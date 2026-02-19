"""
Anomaly Detection Training Script
Train and test the Isolation Forest model with synthetic data
"""
import numpy as np
import pandas as pd
from datetime import datetime
from models.anomaly_detection import AnomalyDetector, BehavioralProfiler
from data.data_generator import SyntheticDataGenerator
from data.database import Database
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AnomalyTrainer:
    """Train and evaluate anomaly detection models"""
    
    def __init__(self):
        self.generator = SyntheticDataGenerator()
        self.detector = AnomalyDetector(model_type='isolation_forest')
        self.profiler = BehavioralProfiler()
        self.db = Database()
    
    def generate_training_data(self, output_path='data/synthetic_dataset.csv',
                             num_residents=3, num_days=30):
        """Generate synthetic training dataset"""
        print("\n" + "=" * 60)
        print("GENERATING SYNTHETIC TRAINING DATA")
        print("=" * 60)
        
        print(f"\nGenerating {num_days}-day dataset with {num_residents} residents...")
        dataset_path = self.generator.generate_dataset(
            output_path=output_path,
            num_residents=num_residents,
            num_caregivers=2,
            num_days=num_days,
            anomaly_rate=0.15
        )
        
        print(f"✓ Dataset generated: {dataset_path}")
        
        # Load and show stats
        events = self.generator.load_dataset(dataset_path)
        print(f"\nDataset Statistics:")
        print(f"   Total events: {len(events)}")
        
        # Count by type
        normal = sum(1 for e in events if e['is_normal'] == 'yes')
        anomalous = sum(1 for e in events if e['is_normal'] == 'no')
        print(f"   Normal events: {normal} ({100*normal/len(events):.1f}%)")
        print(f"   Anomalous events: {anomalous} ({100*anomalous/len(events):.1f}%)")
        
        return dataset_path
    
    def train_model(self, dataset_path='data/synthetic_dataset.csv'):
        """Train Isolation Forest on synthetic data"""
        print("\n" + "=" * 60)
        print("TRAINING ISOLATION FOREST MODEL")
        print("=" * 60)
        
        # Load data
        print(f"\nLoading dataset: {dataset_path}")
        events = self.generator.load_dataset(dataset_path)
        
        # Extract features
        print("Extracting features from access events...")
        X = self.detector.extract_features(events)
        print(f"   Feature matrix shape: {X.shape}")
        print(f"   Features: hour, day_of_week, access_type, confidence, time_interval")
        
        # Train model
        print("\nTraining Isolation Forest...")
        success = self.detector.train_isolation_forest(X)
        
        if success:
            print("✓ Model training successful!")
            
            # Save model
            model_path = 'models/isolation_forest.pkl'
            self.detector.save_model(model_path)
            print(f"✓ Model saved: {model_path}")
        else:
            print("✗ Model training failed")
            return False
        
        return True
    
    def evaluate_model(self, dataset_path='data/synthetic_dataset.csv'):
        """Evaluate model performance"""
        print("\n" + "=" * 60)
        print("EVALUATING MODEL PERFORMANCE")
        print("=" * 60)
        
        # Load data
        events = self.generator.load_dataset(dataset_path)
        
        # Predict
        print("\nMaking predictions on full dataset...")
        predictions = self.detector.batch_predict(events)
        
        # Compare to ground truth
        print("\nComputing accuracy metrics...")
        tp = sum(1 for i, p in enumerate(predictions) 
                if p['is_anomaly'] and events[i]['is_normal'] == 'no')
        fp = sum(1 for i, p in enumerate(predictions) 
                if p['is_anomaly'] and events[i]['is_normal'] == 'yes')
        tn = sum(1 for i, p in enumerate(predictions) 
                if not p['is_anomaly'] and events[i]['is_normal'] == 'yes')
        fn = sum(1 for i, p in enumerate(predictions) 
                if not p['is_anomaly'] and events[i]['is_normal'] == 'no')
        
        # Calculate metrics
        accuracy = (tp + tn) / len(events)
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        print(f"\nPerformance Metrics:")
        print(f"   Accuracy:  {accuracy:.3f}")
        print(f"   Precision: {precision:.3f}")
        print(f"   Recall:    {recall:.3f}")
        print(f"   F1-Score:  {f1:.3f}")
        
        print(f"\nConfusion Matrix:")
        print(f"   True Positives:  {tp}")
        print(f"   False Positives: {fp}")
        print(f"   True Negatives:  {tn}")
        print(f"   False Negatives: {fn}")
    
    def build_behavioral_profiles(self, dataset_path='data/synthetic_dataset.csv'):
        """Build behavioral profiles for residents"""
        print("\n" + "=" * 60)
        print("BUILDING BEHAVIORAL PROFILES")
        print("=" * 60)
        
        events = self.generator.load_dataset(dataset_path)
        
        # Group by person
        by_person = {}
        for event in events:
            person_id = event['person_id']
            if person_id not in by_person:
                by_person[person_id] = []
            by_person[person_id].append(event)
        
        print(f"\nBuilding profiles for {len(by_person)} residents/caregivers...")
        
        for person_id, person_events in by_person.items():
            profile = self.profiler.build_profile(person_id, person_events)
            self.db.save_behavioral_profile(person_id, profile)
            
            print(f"\n   {person_id}:")
            print(f"      Total accesses: {profile['total_accesses']}")
            print(f"      Avg daily: {profile['avg_accesses_per_day']:.1f}")
            print(f"      Preferred hours: {profile['preferred_hours']}")
            print(f"      Preferred days: {profile['preferred_days']}")
    
    def test_realtime_detection(self):
        """Test real-time anomaly detection"""
        print("\n" + "=" * 60)
        print("REAL-TIME ANOMALY DETECTION TEST")
        print("=" * 60)
        
        # Test samples
        test_events = [
            {
                'timestamp': datetime.now().isoformat(),
                'person_id': 'resident_001',
                'type': 'entry',
                'confidence': 0.95,
                'is_normal': 'yes'
            },
            {
                'timestamp': datetime.now().isoformat(),
                'person_id': 'resident_001',
                'type': 'entry',
                'confidence': 0.50,  # Low confidence - anomalous
                'is_normal': 'no'
            },
            {
                'timestamp': datetime.now().isoformat(),
                'person_id': 'resident_001',
                'type': 'exit',
                'confidence': 0.92,
                'is_normal': 'yes'
            }
        ]
        
        print("\nTesting real-time predictions...")
        for event in test_events:
            result = self.detector.predict_anomaly(event)
            
            status = "🔴 ANOMALY" if result['is_anomaly'] else "🟢 NORMAL"
            print(f"\n   {status}")
            print(f"      Anomaly Score: {result['anomaly_score']:.3f}")
            print(f"      Confidence: {result['confidence']:.3f}")
            print(f"      Event: {event['type']} at {event['timestamp']}")

def run_full_pipeline():
    """Run complete training pipeline"""
    trainer = AnomalyTrainer()
    
    print("\n" + "=" * 70)
    print(" " * 15 + "ANOMALY DETECTION TRAINING PIPELINE")
    print("=" * 70)
    
    # Step 1: Generate data
    dataset_path = trainer.generate_training_data(
        num_residents=3,
        num_days=30
    )
    
    # Step 2: Train model
    if trainer.train_model(dataset_path):
        # Step 3: Evaluate
        trainer.evaluate_model(dataset_path)
        
        # Step 4: Build profiles
        trainer.build_behavioral_profiles(dataset_path)
        
        # Step 5: Test real-time
        trainer.test_realtime_detection()
        
        print("\n" + "=" * 70)
        print("✓ TRAINING PIPELINE COMPLETE")
        print("=" * 70)
        print("\nNext steps:")
        print("1. Review model performance metrics above")
        print("2. Check saved model: models/isolation_forest.pkl")
        print("3. Integration with Flask API: api/routes.py")
        print("4. Deploy to Raspberry Pi for edge inference")

if __name__ == '__main__':
    import sys
    
    print("\nAnomaly Detection Training Options:")
    print("1. Full training pipeline (recommended)")
    print("2. Generate data only")
    print("3. Train model only")
    print("4. Evaluate model")
    print("5. Build behavioral profiles")
    print("6. Real-time detection test")
    
    choice = input("\nSelect option (1-6): ").strip()
    
    trainer = AnomalyTrainer()
    
    if choice == '1':
        run_full_pipeline()
    elif choice == '2':
        trainer.generate_training_data()
    elif choice == '3':
        trainer.train_model()
    elif choice == '4':
        trainer.evaluate_model()
    elif choice == '5':
        trainer.build_behavioral_profiles()
    elif choice == '6':
        trainer.test_realtime_detection()
    else:
        print("Invalid option")
