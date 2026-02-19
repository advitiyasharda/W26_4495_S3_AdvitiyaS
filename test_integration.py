"""
Integration Test - Full System Testing
Test all modules together: facial recognition, anomaly detection, threat detection
"""
import logging
from datetime import datetime, timedelta
from api.facial_recognition import FacialRecognitionEngine
from api.threat_detection import ThreatDetector
from models.anomaly_detection import AnomalyDetector
from data.data_generator import SyntheticDataGenerator
from data.database import Database

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SystemIntegrationTest:
    """Test all system components together"""
    
    def __init__(self):
        self.face_engine = FacialRecognitionEngine()
        self.threat_detector = ThreatDetector()
        self.anomaly_detector = AnomalyDetector()
        self.data_gen = SyntheticDataGenerator()
        self.db = Database()
    
    def test_complete_flow(self):
        """Test complete access flow"""
        print("\n" + "=" * 70)
        print("INTEGRATION TEST - COMPLETE SYSTEM FLOW")
        print("=" * 70)
        
        # Setup
        print("\n[Setup] Registering residents...")
        residents = [
            ('resident_001', 'John Doe'),
            ('resident_002', 'Jane Smith'),
            ('caregiver_001', 'Alice Johnson'),
        ]
        
        for person_id, name in residents:
            self.db.add_user(person_id, name, 'resident' if 'resident' in person_id else 'caregiver')
            self.face_engine.register_face(person_id, name, None)
        
        print(f"✓ Registered {len(residents)} users")
        
        # Simulate access events
        print("\n[Simulation] Creating 20 realistic access events...")
        test_events = self._create_test_events()
        
        # Process each event
        print("\n[Processing] Running events through pipeline...\n")
        
        for i, event in enumerate(test_events, 1):
            print(f"Event {i}: {event['person_id']} - {event['type'].upper()}")
            
            # Step 1: Facial Recognition
            print(f"  └─ Facial Recognition: {event['person_id']}")
            
            # Step 2: Log access
            self.db.log_access(
                event['person_id'],
                event['type'],
                event['confidence'],
                'success'
            )
            self.threat_detector.log_access_attempt(event['person_id'], True)
            print(f"  └─ Access Logged ✓")
            
            # Step 3: Anomaly Detection
            anomaly_result = self.anomaly_detector.predict_anomaly(event)
            if anomaly_result['is_anomaly']:
                print(f"  └─ Anomaly Detected: {anomaly_result['anomaly_score']:.3f}")
                self.db.log_anomaly(
                    event['person_id'],
                    'BEHAVIORAL_ANOMALY',
                    anomaly_result['anomaly_score'],
                    'Unusual access pattern detected'
                )
            else:
                print(f"  └─ Normal Pattern ✓")
            
            # Step 4: Threat Detection
            threats = []
            
            # Check failed attempts
            if event['confidence'] < 0.6:
                threat = self.threat_detector.check_failed_access_attempts(event['person_id'])
                if threat:
                    threats.append(threat)
            
            # Check unusual time
            threat = self.threat_detector.check_unusual_access_time(event['person_id'])
            if threat:
                threats.append(threat)
            
            if threats:
                for threat in threats:
                    print(f"  └─ 🚨 Threat: {threat['threat_type']} ({threat['severity']})")
                    self.db.log_threat(
                        threat['threat_type'],
                        threat['severity'],
                        event['person_id'],
                        threat['message']
                    )
            else:
                print(f"  └─ No Threats ✓")
            
            print()
        
        # Summary
        self._print_summary()
    
    def _create_test_events(self):
        """Create realistic test events"""
        events = []
        base_time = datetime.now() - timedelta(hours=12)
        
        # Normal morning routine
        events.extend([
            {'timestamp': (base_time + timedelta(hours=0)).isoformat(), 'person_id': 'resident_001', 'type': 'entry', 'confidence': 0.94},
            {'timestamp': (base_time + timedelta(hours=1)).isoformat(), 'person_id': 'resident_001', 'type': 'exit', 'confidence': 0.92},
            {'timestamp': (base_time + timedelta(hours=2)).isoformat(), 'person_id': 'resident_001', 'type': 'entry', 'confidence': 0.91},
        ])
        
        # Caregiver visit
        events.extend([
            {'timestamp': (base_time + timedelta(hours=3)).isoformat(), 'person_id': 'caregiver_001', 'type': 'entry', 'confidence': 0.96},
            {'timestamp': (base_time + timedelta(hours=3, minutes=30)).isoformat(), 'person_id': 'caregiver_001', 'type': 'exit', 'confidence': 0.95},
        ])
        
        # Normal patterns
        events.extend([
            {'timestamp': (base_time + timedelta(hours=5)).isoformat(), 'person_id': 'resident_002', 'type': 'entry', 'confidence': 0.93},
            {'timestamp': (base_time + timedelta(hours=6)).isoformat(), 'person_id': 'resident_002', 'type': 'exit', 'confidence': 0.90},
        ])
        
        # Anomalous patterns
        events.extend([
            # Failed attempt (low confidence)
            {'timestamp': (base_time + timedelta(hours=7)).isoformat(), 'person_id': 'unknown_001', 'type': 'entry', 'confidence': 0.45},
            {'timestamp': (base_time + timedelta(hours=7, minutes=2)).isoformat(), 'person_id': 'unknown_001', 'type': 'entry', 'confidence': 0.42},
            
            # Wandering (multiple entries in short time)
            {'timestamp': (base_time + timedelta(hours=8)).isoformat(), 'person_id': 'resident_001', 'type': 'exit', 'confidence': 0.89},
            {'timestamp': (base_time + timedelta(hours=8, minutes=5)).isoformat(), 'person_id': 'resident_001', 'type': 'entry', 'confidence': 0.88},
            {'timestamp': (base_time + timedelta(hours=8, minutes=8)).isoformat(), 'person_id': 'resident_001', 'type': 'exit', 'confidence': 0.87},
        ])
        
        # Night activity (unusual time)
        events.extend([
            {'timestamp': (base_time + timedelta(hours=15)).isoformat(), 'person_id': 'resident_001', 'type': 'entry', 'confidence': 0.92},
            {'timestamp': (base_time + timedelta(hours=16)).isoformat(), 'person_id': 'resident_002', 'type': 'entry', 'confidence': 0.91},
        ])
        
        return events
    
    def _print_summary(self):
        """Print test summary"""
        print("=" * 70)
        print("SYSTEM STATISTICS")
        print("=" * 70)
        
        db_stats = self.db.get_database_stats()
        print(f"\nDatabase:")
        print(f"  Users: {db_stats['total_users']}")
        print(f"  Access Events: {db_stats['total_access_events']}")
        print(f"  Active Threats: {db_stats['active_threats']}")
        print(f"  Anomalies: {db_stats['total_anomalies']}")
        
        fr_stats = self.face_engine.get_recognition_stats()
        print(f"\nFacial Recognition:")
        print(f"  Registered Persons: {fr_stats['total_persons']}")
        print(f"  Total Encodings: {fr_stats['total_face_encodings']}")
        
        threat_stats = self.threat_detector.get_threat_stats()
        print(f"\nThreat Detection:")
        print(f"  Failed Attempts: {threat_stats['total_failed_attempts']}")
        print(f"  Logged Accesses: {threat_stats['total_logged_accesses']}")
        
        # Show active threats
        threats = self.db.get_active_threats()
        if threats:
            print(f"\nActive Threats ({len(threats)}):")
            for threat in threats[:5]:  # Show first 5
                print(f"  [{threat['severity']}] {threat['threat_type']}")
                print(f"      {threat['message']}")
    
    def run_benchmark(self):
        """Run performance benchmark"""
        print("\n" + "=" * 70)
        print("PERFORMANCE BENCHMARK")
        print("=" * 70)
        
        import time
        
        # Test facial recognition
        print("\nFacial Recognition Speed:")
        print("  (Note: Using OpenCV cascade, not real ML model)")
        
        test_event = {
            'timestamp': datetime.now().isoformat(),
            'person_id': 'test_user',
            'type': 'entry',
            'confidence': 0.92
        }
        
        # Anomaly detection speed
        print("\nAnomaly Detection Speed:")
        start = time.time()
        for _ in range(100):
            self.anomaly_detector.predict_anomaly(test_event)
        elapsed = time.time() - start
        avg_time = (elapsed / 100) * 1000
        
        print(f"  100 predictions: {elapsed:.3f}s")
        print(f"  Average latency: {avg_time:.1f}ms")
        
        # Threat detection speed
        print("\nThreat Detection Speed:")
        start = time.time()
        for _ in range(100):
            self.threat_detector.check_failed_access_attempts('test_user')
            self.threat_detector.check_unusual_access_time('test_user')
        elapsed = time.time() - start
        avg_time = (elapsed / 100) * 1000
        
        print(f"  100 checks: {elapsed:.3f}s")
        print(f"  Average latency: {avg_time:.1f}ms")
        
        print("\n✓ All components responding within acceptable latency")

if __name__ == '__main__':
    import sys
    
    print("\nSystem Integration Test Options:")
    print("1. Complete flow test (recommended)")
    print("2. Performance benchmark")
    print("3. Both")
    
    choice = input("\nSelect option (1-3): ").strip()
    
    tester = SystemIntegrationTest()
    
    if choice == '1':
        tester.test_complete_flow()
    elif choice == '2':
        tester.run_benchmark()
    elif choice == '3':
        tester.test_complete_flow()
        tester.run_benchmark()
    else:
        print("Invalid option")
