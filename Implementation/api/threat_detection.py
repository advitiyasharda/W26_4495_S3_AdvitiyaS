"""
Threat Detection Module for Cybersecurity
Detects anomalous access patterns and security threats
"""
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from enum import Enum

logger = logging.getLogger(__name__)

class ThreatLevel(Enum):
    """Threat severity levels"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

class ThreatDetector:
    """
    Detects security and behavioral threats.
    Rules-based approach for real-time detection on edge devices.
    """
    
    def __init__(self, 
                 failed_attempt_threshold=3,
                 failed_attempt_window_minutes=10,
                 inactivity_threshold_hours=24):
        """
        Initialize threat detector with configurable thresholds.
        
        Args:
            failed_attempt_threshold: Failed attempts to trigger alert
            failed_attempt_window_minutes: Time window for failed attempts
            inactivity_threshold_hours: Hours without activity to trigger alert
        """
        self.failed_attempt_threshold = failed_attempt_threshold
        self.failed_attempt_window_minutes = failed_attempt_window_minutes
        self.inactivity_threshold_hours = inactivity_threshold_hours
        
        # Threat history tracking
        self.failed_attempts = []  # [(timestamp, person_id)]
        self.access_log = []  # [(timestamp, person_id, status)]
        
        logger.info("Threat Detector initialized")
    
    def check_failed_access_attempts(self, person_id: str) -> Optional[Dict]:
        """
        Check for repeated failed access attempts.
        
        Args:
            person_id: Identifier for person attempting access
            
        Returns:
            Threat alert if threshold exceeded, None otherwise
        """
        now = datetime.now()
        window_start = now - timedelta(minutes=self.failed_attempt_window_minutes)
        
        # Count recent failed attempts
        recent_failures = [
            attempt for attempt in self.failed_attempts
            if attempt[0] > window_start and attempt[1] == person_id
        ]
        
        if len(recent_failures) >= self.failed_attempt_threshold:
            alert = {
                'threat_type': 'REPEATED_FAILED_ACCESS',
                'severity': ThreatLevel.HIGH.name,
                'person_id': person_id,
                'failed_count': len(recent_failures),
                'timestamp': now.isoformat(),
                'message': f'Multiple failed access attempts ({len(recent_failures)}) detected'
            }
            logger.warning(alert['message'])
            return alert
        
        return None
    
    def check_inactivity(self, person_id: str, last_activity: datetime) -> Optional[Dict]:
        """
        Check for prolonged inactivity (potential health emergency).
        
        Args:
            person_id: Identifier for resident
            last_activity: Timestamp of last door activity
            
        Returns:
            Health alert if inactivity threshold exceeded, None otherwise
        """
        now = datetime.now()
        inactivity_duration = now - last_activity
        threshold = timedelta(hours=self.inactivity_threshold_hours)
        
        if inactivity_duration > threshold:
            alert = {
                'threat_type': 'PROLONGED_INACTIVITY',
                'severity': ThreatLevel.CRITICAL.name,
                'person_id': person_id,
                'inactivity_hours': inactivity_duration.total_seconds() / 3600,
                'last_activity': last_activity.isoformat(),
                'timestamp': now.isoformat(),
                'message': f'No door activity for {inactivity_duration.total_seconds() / 3600:.1f} hours'
            }
            logger.critical(alert['message'])
            return alert
        
        return None
    
    def check_unusual_access_time(self, person_id: str, 
                                  unusual_hours: List[int] = None) -> Optional[Dict]:
        """
        Check for access at unusual times (e.g., late night).
        
        Args:
            person_id: Identifier for person
            unusual_hours: List of unusual hours (24-hour format)
            
        Returns:
            Alert if access at unusual time, None otherwise
        """
        if unusual_hours is None:
            unusual_hours = [22, 23, 0, 1, 2, 3, 4, 5]  # 10 PM - 5 AM
        
        now = datetime.now()
        if now.hour in unusual_hours:
            alert = {
                'threat_type': 'UNUSUAL_ACCESS_TIME',
                'severity': ThreatLevel.MEDIUM.name,
                'person_id': person_id,
                'access_hour': now.hour,
                'timestamp': now.isoformat(),
                'message': f'Access at unusual time: {now.strftime("%H:%M")}'
            }
            logger.warning(alert['message'])
            return alert
        
        return None
    
    def check_frequency_spike(self, person_id: str, 
                            window_minutes: int = 60,
                            spike_threshold: int = 10) -> Optional[Dict]:
        """
        Check for unusual spike in access frequency.
        
        Args:
            person_id: Identifier for person
            window_minutes: Time window to check
            spike_threshold: Maximum expected accesses in window
            
        Returns:
            Alert if frequency spike detected, None otherwise
        """
        now = datetime.now()
        window_start = now - timedelta(minutes=window_minutes)
        
        recent_accesses = [
            access for access in self.access_log
            if access[0] > window_start and access[1] == person_id and access[2] == 'success'
        ]
        
        if len(recent_accesses) > spike_threshold:
            alert = {
                'threat_type': 'ACCESS_FREQUENCY_SPIKE',
                'severity': ThreatLevel.MEDIUM.name,
                'person_id': person_id,
                'access_count': len(recent_accesses),
                'window_minutes': window_minutes,
                'timestamp': now.isoformat(),
                'message': f'High access frequency: {len(recent_accesses)} accesses in {window_minutes} minutes'
            }
            logger.warning(alert['message'])
            return alert
        
        return None
    
    def log_access_attempt(self, person_id: str, success: bool):
        """Log an access attempt"""
        status = 'success' if success else 'failed'
        self.access_log.append((datetime.now(), person_id, status))
        
        if not success:
            self.failed_attempts.append((datetime.now(), person_id))
    
    def get_threat_stats(self) -> Dict:
        """Get threat detection statistics"""
        return {
            'total_failed_attempts': len(self.failed_attempts),
            'total_logged_accesses': len(self.access_log),
            'active_threats': 'N/A'  # TODO: Count active threats
        }
