"""
Synthetic Data Generator for Training and Testing
Generates realistic door access patterns for elderly care scenarios
"""
import csv
import random
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict

logger = logging.getLogger(__name__)

class SyntheticDataGenerator:
    """
    Generates synthetic door access datasets with:
    - Normal patterns (residents, caregivers)
    - Anomalous patterns (wandering, inactivity, unusual times)
    - Security events (failed attempts, unauthorized access)
    """
    
    def __init__(self, seed: int = 42):
        """Initialize generator with optional random seed"""
        random.seed(seed)
        logger.info("Synthetic Data Generator initialized")
    
    def generate_dataset(self, output_path: str = 'data/synthetic_dataset.csv',
                        num_residents: int = 3,
                        num_caregivers: int = 2,
                        num_days: int = 30,
                        anomaly_rate: float = 0.15) -> str:
        """
        Generate synthetic door access dataset.
        
        Args:
            output_path: Path to save CSV file
            num_residents: Number of residents
            num_caregivers: Number of caregivers
            num_days: Number of days to simulate
            anomaly_rate: Proportion of anomalous events (0.0-1.0)
            
        Returns:
            Path to generated CSV file
        """
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Generate events
        events = []
        
        # Add normal patterns
        for day in range(num_days):
            date = datetime.now() - timedelta(days=num_days - day)
            
            # Resident patterns (normal and anomalous)
            for res_id in range(1, num_residents + 1):
                events.extend(self._generate_resident_day(
                    f"resident_{res_id}", date, anomaly_rate
                ))
            
            # Caregiver patterns
            for cg_id in range(1, num_caregivers + 1):
                events.extend(self._generate_caregiver_day(
                    f"caregiver_{cg_id}", date
                ))
        
        # Write to CSV
        self._write_csv(output_path, events)
        
        logger.info(f"Generated {len(events)} synthetic events -> {output_path}")
        return output_path
    
    def _generate_resident_day(self, resident_id: str, date: datetime, 
                              anomaly_rate: float) -> List[Dict]:
        """Generate a day of resident door activity"""
        events = []
        
        # Determine if this is an anomaly day
        is_anomaly_day = random.random() < anomaly_rate
        
        if is_anomaly_day:
            anomaly_type = random.choice([
                'wandering',      # Excessive entries/exits
                'inactivity',     # No movement for extended period
                'unusual_time',   # Late night activity
                'frequency_spike' # Unusual access pattern
            ])
            
            if anomaly_type == 'wandering':
                # Multiple entries/exits in short time
                for _ in range(random.randint(5, 12)):
                    time = date + timedelta(hours=random.randint(8, 18), minutes=random.randint(0, 59))
                    access_type = random.choice(['entry', 'exit'])
                    events.append(self._create_event(resident_id, access_type, time, is_normal=False))
            
            elif anomaly_type == 'inactivity':
                # Only one entry early in day, no exits
                time = date + timedelta(hours=7, minutes=random.randint(0, 59))
                events.append(self._create_event(resident_id, 'entry', time, is_normal=False))
            
            elif anomaly_type == 'unusual_time':
                # Activity during unusual hours (2-5 AM)
                time = date + timedelta(hours=random.randint(2, 5), minutes=random.randint(0, 59))
                access_type = random.choice(['entry', 'exit'])
                events.append(self._create_event(resident_id, access_type, time, is_normal=False))
            
            elif anomaly_type == 'frequency_spike':
                # More accesses than normal
                num_accesses = random.randint(8, 15)
                for _ in range(num_accesses):
                    time = date + timedelta(hours=random.randint(6, 22), minutes=random.randint(0, 59))
                    access_type = random.choice(['entry', 'exit'])
                    events.append(self._create_event(resident_id, access_type, time, is_normal=False))
        
        else:
            # Normal resident day pattern
            # Morning entry (7-9 AM)
            time = date + timedelta(hours=random.randint(7, 8), minutes=random.randint(0, 59))
            events.append(self._create_event(resident_id, 'entry', time))
            
            # Random mid-day exit/entry
            if random.random() > 0.3:
                time = date + timedelta(hours=random.randint(10, 14), minutes=random.randint(0, 59))
                events.append(self._create_event(resident_id, 'exit', time))
                
                time = date + timedelta(hours=random.randint(14, 17), minutes=random.randint(0, 59))
                events.append(self._create_event(resident_id, 'entry', time))
            
            # Evening exit (5-8 PM)
            time = date + timedelta(hours=random.randint(17, 20), minutes=random.randint(0, 59))
            events.append(self._create_event(resident_id, 'exit', time))
        
        return events
    
    def _generate_caregiver_day(self, caregiver_id: str, date: datetime) -> List[Dict]:
        """Generate a day of caregiver door activity"""
        events = []
        
        # Caregivers typically visit once or twice per day
        num_visits = random.randint(1, 2)
        
        for _ in range(num_visits):
            # Visit time between 9 AM - 5 PM
            visit_hour = random.randint(9, 17)
            
            # Entry
            time = date + timedelta(hours=visit_hour, minutes=random.randint(0, 59))
            events.append(self._create_event(caregiver_id, 'entry', time, role='caregiver'))
            
            # Exit (30-60 minutes later)
            time = time + timedelta(minutes=random.randint(30, 60))
            events.append(self._create_event(caregiver_id, 'exit', time, role='caregiver'))
        
        return events
    
    def _create_event(self, person_id: str, access_type: str, timestamp: datetime,
                     is_normal: bool = True, role: str = 'resident') -> Dict:
        """Create a single access event"""
        return {
            'timestamp': timestamp.isoformat(),
            'person_id': person_id,
            'access_type': access_type,
            'confidence': random.uniform(0.85, 0.99) if is_normal else random.uniform(0.5, 0.85),
            'is_normal': 'yes' if is_normal else 'no',
            'role': role,
            'device_id': 'door_001'
        }
    
    def _write_csv(self, filepath: str, events: List[Dict]):
        """Write events to CSV file"""
        if not events:
            logger.warning("No events to write")
            return
        
        # Sort by timestamp
        events.sort(key=lambda x: x['timestamp'])
        
        with open(filepath, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=events[0].keys())
            writer.writeheader()
            writer.writerows(events)
    
    def load_dataset(self, filepath: str) -> List[Dict]:
        """Load dataset from CSV file"""
        events = []
        try:
            with open(filepath, 'r') as f:
                reader = csv.DictReader(f)
                events = list(reader)
            logger.info(f"Loaded {len(events)} events from {filepath}")
        except Exception as e:
            logger.error(f"Error loading dataset: {e}")
        
        return events

# Utility function to generate default dataset
def generate_default_dataset(output_path: str = 'data/synthetic_dataset.csv',
                           num_residents: int = 3,
                           num_caregivers: int = 2) -> str:
    """Generate and save default synthetic dataset"""
    generator = SyntheticDataGenerator()
    return generator.generate_dataset(
        output_path=output_path,
        num_residents=num_residents,
        num_caregivers=num_caregivers,
        num_days=30,
        anomaly_rate=0.15
    )
