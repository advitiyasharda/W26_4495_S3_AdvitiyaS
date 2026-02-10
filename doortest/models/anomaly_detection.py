"""
Anomaly Detection Module using Machine Learning
Implements Isolation Forest and optional LSTM autoencoder for behavioral anomaly detection
"""
import numpy as np
import logging
from typing import Tuple, Optional, Dict, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class AnomalyDetector:
    """
    Detects anomalous door access patterns using unsupervised learning.
    Designed for edge deployment on Raspberry Pi/Jetson.
    """
    
    def __init__(self, model_type='isolation_forest', contamination=0.1):
        """
        Initialize anomaly detector.
        
        Args:
            model_type: 'isolation_forest' or 'lstm_autoencoder'
            contamination: Expected proportion of anomalies in dataset
        """
        self.model_type = model_type
        self.contamination = contamination
        self.model = None
        self.is_trained = False
        self.feature_scaler = None
        
        logger.info(f"Anomaly Detector initialized with model_type={model_type}")
    
    def extract_features(self, access_sequence: List[Dict]) -> np.ndarray:
        """
        Extract statistical features from access sequence.
        
        Features:
        - Time between accesses
        - Access frequency (per hour/day)
        - Day of week
        - Hour of day
        - Access type (entry/exit)
        
        Args:
            access_sequence: List of access events with timestamps
            
        Returns:
            Feature matrix (n_events, n_features)
        """
        features = []
        
        for i, access in enumerate(access_sequence):
            timestamp = datetime.fromisoformat(access['timestamp'])
            
            # Time-based features
            hour = timestamp.hour
            day_of_week = timestamp.weekday()
            
            # Access pattern features
            access_type = 1 if access['type'] == 'entry' else 0
            confidence = access.get('confidence', 0.0)
            
            # Time interval from previous access
            if i > 0:
                prev_timestamp = datetime.fromisoformat(access_sequence[i-1]['timestamp'])
                time_diff = (timestamp - prev_timestamp).total_seconds() / 3600  # hours
            else:
                time_diff = 0.0
            
            feature_vector = [
                hour,
                day_of_week,
                access_type,
                confidence,
                time_diff
            ]
            
            features.append(feature_vector)
        
        return np.array(features)
    
    def train_isolation_forest(self, training_data: np.ndarray) -> bool:
        """
        Train Isolation Forest model.
        
        Args:
            training_data: Feature matrix (n_samples, n_features)
            
        Returns:
            True if training successful
        """
        try:
            # Import here to avoid dependency if not using this model
            from sklearn.ensemble import IsolationForest
            
            self.model = IsolationForest(
                contamination=self.contamination,
                n_estimators=100,
                random_state=42,
                n_jobs=-1
            )
            
            self.model.fit(training_data)
            self.is_trained = True
            
            logger.info(f"Isolation Forest trained on {len(training_data)} samples")
            return True
            
        except ImportError:
            logger.error("scikit-learn not installed. Install with: pip install scikit-learn")
            return False
        except Exception as e:
            logger.error(f"Error training Isolation Forest: {e}")
            return False
    
    def train_lstm_autoencoder(self, training_data: np.ndarray, 
                              sequence_length: int = 10) -> bool:
        """
        Train LSTM Autoencoder model (optional, if time permits).
        
        Args:
            training_data: Feature matrix
            sequence_length: Number of time steps for LSTM
            
        Returns:
            True if training successful
        """
        try:
            logger.info("LSTM Autoencoder training - TODO: Implement TensorFlow Lite version")
            return False
            
        except Exception as e:
            logger.error(f"Error training LSTM: {e}")
            return False
    
    def predict_anomaly(self, access_event: Dict) -> Dict:
        """
        Predict if an access event is anomalous.
        
        Args:
            access_event: Single access event
            
        Returns:
            Dictionary with anomaly score and prediction
        """
        if not self.is_trained:
            logger.warning("Model not trained. Returning neutral prediction.")
            return {
                'is_anomaly': False,
                'anomaly_score': 0.0,
                'confidence': 0.0,
                'reason': 'Model not trained'
            }
        
        try:
            # Extract features for single event
            features = self.extract_features([access_event])
            
            # Get anomaly score (-1 for anomaly, 1 for normal)
            prediction = self.model.predict(features)[0]
            score = self.model.score_samples(features)[0]
            
            # Normalize score to 0-1 range
            normalized_score = 1 / (1 + np.exp(score))  # Sigmoid normalization
            
            is_anomaly = prediction == -1
            
            result = {
                'is_anomaly': is_anomaly,
                'anomaly_score': float(normalized_score),
                'confidence': float(abs(score)),
                'timestamp': datetime.now().isoformat()
            }
            
            if is_anomaly:
                logger.warning(f"Anomaly detected: {result}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in anomaly prediction: {e}")
            return {
                'is_anomaly': False,
                'anomaly_score': 0.0,
                'error': str(e)
            }
    
    def batch_predict(self, access_events: List[Dict]) -> List[Dict]:
        """
        Predict anomalies for multiple events.
        
        Args:
            access_events: List of access events
            
        Returns:
            List of prediction results
        """
        results = []
        for event in access_events:
            results.append(self.predict_anomaly(event))
        
        return results
    
    def get_model_stats(self) -> Dict:
        """Get model statistics"""
        return {
            'model_type': self.model_type,
            'is_trained': self.is_trained,
            'contamination': self.contamination,
            'model': str(self.model) if self.model else None
        }
    
    def save_model(self, filepath: str) -> bool:
        """Save trained model to disk"""
        try:
            import pickle
            with open(filepath, 'wb') as f:
                pickle.dump(self.model, f)
            logger.info(f"Model saved to {filepath}")
            return True
        except Exception as e:
            logger.error(f"Error saving model: {e}")
            return False
    
    def load_model(self, filepath: str) -> bool:
        """Load trained model from disk"""
        try:
            import pickle
            with open(filepath, 'rb') as f:
                self.model = pickle.load(f)
            self.is_trained = True
            logger.info(f"Model loaded from {filepath}")
            return True
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            return False


class BehavioralProfiler:
    """
    Builds and monitors behavioral profiles for elderly residents.
    Detects deviations from normal patterns (wandering, inactivity, etc.)
    """
    
    def __init__(self):
        """Initialize behavioral profiler"""
        self.profiles = {}  # {person_id: profile_data}
    
    def build_profile(self, person_id: str, access_history: List[Dict]) -> Dict:
        """
        Build behavioral profile from access history.
        
        Args:
            person_id: Identifier for person
            access_history: List of past access events
            
        Returns:
            Profile dictionary with statistics
        """
        if not access_history:
            return {}
        
        timestamps = [datetime.fromisoformat(e['timestamp']) for e in access_history]
        hours = [ts.hour for ts in timestamps]
        days = [ts.weekday() for ts in timestamps]
        
        profile = {
            'person_id': person_id,
            'total_accesses': len(access_history),
            'avg_accesses_per_day': len(access_history) / 30,  # Assuming 30-day history
            'preferred_hours': self._get_most_common(hours),
            'preferred_days': self._get_most_common(days),
            'inactivity_threshold': 24,  # hours
            'created_at': datetime.now().isoformat()
        }
        
        self.profiles[person_id] = profile
        return profile
    
    def _get_most_common(self, values: List[int], top_k: int = 3) -> List[int]:
        """Get most common values"""
        from collections import Counter
        return [val for val, _ in Counter(values).most_common(top_k)]
    
    def detect_behavioral_anomaly(self, person_id: str, 
                                 access_event: Dict) -> Optional[Dict]:
        """
        Detect anomaly compared to behavioral profile.
        
        Args:
            person_id: Identifier for person
            access_event: New access event
            
        Returns:
            Anomaly alert or None
        """
        if person_id not in self.profiles:
            return None
        
        profile = self.profiles[person_id]
        event_time = datetime.fromisoformat(access_event['timestamp'])
        
        # Check if access at unusual hour
        if event_time.hour not in profile['preferred_hours']:
            return {
                'type': 'UNUSUAL_HOUR',
                'person_id': person_id,
                'hour': event_time.hour,
                'preferred_hours': profile['preferred_hours'],
                'severity': 'LOW'
            }
        
        return None
