"""
Database Module for SQLite Data Persistence
Handles access logs, threats, audit trails, and user data
"""
import sqlite3
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class Database:
    """SQLite database manager for Door Face Panels system"""
    
    def __init__(self, db_path: str = 'data/doorface.db'):
        """
        Initialize database connection.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = None
        self.init_db()
    
    def connect(self):
        """Connect to database"""
        # check_same_thread=False allows SQLite to be used across threads
        # This is needed for Flask which uses threads for requests
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        logger.info(f"Connected to database: {self.db_path}")
    
    def disconnect(self):
        """Disconnect from database"""
        if self.conn:
            self.conn.close()
            logger.info("Disconnected from database")
    
    def init_db(self):
        """Initialize database schema"""
        self.connect()
        cursor = self.conn.cursor()
        
        # Users/Residents table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                role TEXT DEFAULT 'resident',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Access Log table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS access_logs (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                access_type TEXT CHECK(access_type IN ('entry', 'exit')),
                confidence REAL,
                status TEXT DEFAULT 'success',
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(user_id)
            )
        ''')
        
        # Create index on user_id and timestamp for faster queries
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_access_logs_user_timestamp 
            ON access_logs(user_id, timestamp)
        ''')
        
        # Anomaly Detections table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS anomalies (
                anomaly_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                anomaly_type TEXT,
                anomaly_score REAL,
                description TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(user_id)
            )
        ''')
        
        # Threats/Alerts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS threats (
                threat_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                threat_type TEXT NOT NULL,
                severity TEXT CHECK(severity IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
                message TEXT,
                resolved BOOLEAN DEFAULT 0,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                resolved_at TIMESTAMP
            )
        ''')
        
        # Audit Log table (PIPEDA compliance)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS audit_logs (
                audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
                action TEXT NOT NULL,
                user_id TEXT,
                resource TEXT,
                result TEXT,
                details TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Behavioral Profiles table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS behavioral_profiles (
                profile_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT UNIQUE NOT NULL,
                preferred_hours TEXT,
                preferred_days TEXT,
                avg_daily_accesses REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(user_id)
            )
        ''')
        
        self.conn.commit()
        logger.info("Database schema initialized")
    
    def add_user(self, user_id: str, name: str, role: str = 'resident') -> bool:
        """Add a new user"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT OR IGNORE INTO users (user_id, name, role)
                VALUES (?, ?, ?)
            ''', (user_id, name, role))
            self.conn.commit()
            logger.info(f"User added: {name} ({user_id})")
            return True
        except Exception as e:
            logger.error(f"Error adding user: {e}")
            return False
    
    def log_access(self, user_id: str, access_type: str, 
                   confidence: float = 0.0, status: str = 'success') -> bool:
        """Log an access event"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO access_logs (user_id, access_type, confidence, status)
                VALUES (?, ?, ?, ?)
            ''', (user_id, access_type, confidence, status))
            self.conn.commit()
            logger.info(f"Access logged: {user_id} - {access_type}")
            return True
        except Exception as e:
            logger.error(f"Error logging access: {e}")
            return False
    
    def get_access_logs(self, user_id: str = None,
                       limit: int = 100, offset: int = 0) -> List[Dict]:
        """Retrieve access logs joined with user names, mapped to frontend field names."""
        try:
            cursor = self.conn.cursor()

            base_query = '''
                SELECT
                    al.log_id,
                    al.user_id        AS person_id,
                    u.name            AS name,
                    al.access_type    AS type,
                    al.confidence,
                    al.status,
                    al.timestamp
                FROM access_logs al
                LEFT JOIN users u ON al.user_id = u.user_id
            '''

            if user_id:
                cursor.execute(
                    base_query + ' WHERE al.user_id = ? ORDER BY al.timestamp DESC LIMIT ? OFFSET ?',
                    (user_id, limit, offset)
                )
            else:
                cursor.execute(
                    base_query + ' ORDER BY al.timestamp DESC LIMIT ? OFFSET ?',
                    (limit, offset)
                )

            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error retrieving access logs: {e}")
            return []
    
    def log_threat(self, threat_type: str, severity: str, 
                  user_id: str = None, message: str = '') -> bool:
        """Log a security threat or behavioral alert"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO threats (user_id, threat_type, severity, message)
                VALUES (?, ?, ?, ?)
            ''', (user_id, threat_type, severity, message))
            self.conn.commit()
            logger.warning(f"Threat logged: {threat_type} ({severity})")
            return True
        except Exception as e:
            logger.error(f"Error logging threat: {e}")
            return False
    
    def get_active_threats(self, severity: str = None) -> List[Dict]:
        """Get active (unresolved) threats"""
        try:
            cursor = self.conn.cursor()
            
            if severity:
                cursor.execute('''
                    SELECT * FROM threats
                    WHERE resolved = 0 AND severity = ?
                    ORDER BY timestamp DESC
                ''', (severity,))
            else:
                cursor.execute('''
                    SELECT * FROM threats
                    WHERE resolved = 0
                    ORDER BY timestamp DESC
                ''')
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error retrieving threats: {e}")
            return []
    
    def log_audit(self, action: str, user_id: str = None, 
                 resource: str = None, result: str = 'success', details: str = '') -> bool:
        """Log an action for PIPEDA compliance audit trail"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO audit_logs (action, user_id, resource, result, details)
                VALUES (?, ?, ?, ?, ?)
            ''', (action, user_id, resource, result, details))
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error logging audit: {e}")
            return False
    
    def get_audit_logs(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """Retrieve audit logs for compliance reporting"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT * FROM audit_logs
                ORDER BY timestamp DESC
                LIMIT ? OFFSET ?
            ''', (limit, offset))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error retrieving audit logs: {e}")
            return []
    
    def log_anomaly(self, user_id: str, anomaly_type: str, 
                   anomaly_score: float, description: str = '') -> bool:
        """Log detected anomaly"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO anomalies (user_id, anomaly_type, anomaly_score, description)
                VALUES (?, ?, ?, ?)
            ''', (user_id, anomaly_type, anomaly_score, description))
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error logging anomaly: {e}")
            return False
    
    def save_behavioral_profile(self, user_id: str, profile: Dict) -> bool:
        """Save or update behavioral profile"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO behavioral_profiles 
                (user_id, preferred_hours, preferred_days, avg_daily_accesses, updated_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (
                user_id,
                json.dumps(profile.get('preferred_hours', [])),
                json.dumps(profile.get('preferred_days', [])),
                profile.get('avg_daily_accesses', 0.0)
            ))
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error saving behavioral profile: {e}")
            return False
    
    def get_database_stats(self) -> Dict:
        """Get database statistics"""
        try:
            cursor = self.conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM users')
            total_users = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM access_logs')
            total_accesses = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM threats WHERE resolved = 0')
            active_threats = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM anomalies')
            total_anomalies = cursor.fetchone()[0]
            
            return {
                'total_users': total_users,
                'total_access_events': total_accesses,
                'active_threats': active_threats,
                'total_anomalies': total_anomalies
            }
        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            return {}
