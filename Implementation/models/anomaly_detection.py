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
    
    def __init__(self, model_type='isolation_forest', contamination=0.15):
        """
        Initialize anomaly detector.
        contamination=0.15 matches the 15% anomaly rate in the synthetic dataset.

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
        Extract features from access sequence using cyclical encoding for
        time-based fields so that the model understands hour and day wrap
        around (e.g. 23:00 is close to 00:00, not far away).

        Features (7 total):
        - hour_sin, hour_cos   : cyclical encoding of hour (0-23)
        - day_sin,  day_cos    : cyclical encoding of day-of-week (0-6)
        - access_type          : 1=entry, 0=exit
        - confidence           : recognition confidence score
        - time_delta           : hours since previous access event

        Args:
            access_sequence: List of access events with timestamps

        Returns:
            Feature matrix (n_events, 7)
        """
        features = []

        for i, access in enumerate(access_sequence):
            timestamp = datetime.fromisoformat(access['timestamp'])

            hour = timestamp.hour
            day_of_week = timestamp.weekday()

            # Cyclical encoding — maps time onto a unit circle so the model
            # understands that 23:00 and 00:00 are 1 hour apart, not 23 apart
            hour_sin = np.sin(2 * np.pi * hour / 24)
            hour_cos = np.cos(2 * np.pi * hour / 24)
            day_sin  = np.sin(2 * np.pi * day_of_week / 7)
            day_cos  = np.cos(2 * np.pi * day_of_week / 7)

            access_type_key = 'access_type' if 'access_type' in access else 'type'
            access_type = 1 if access[access_type_key] == 'entry' else 0
            confidence = float(access.get('confidence', 0.0))

            if i > 0:
                prev_timestamp = datetime.fromisoformat(access_sequence[i-1]['timestamp'])
                time_diff = (timestamp - prev_timestamp).total_seconds() / 3600
            else:
                time_diff = 0.0

            features.append([
                hour_sin, hour_cos,
                day_sin,  day_cos,
                access_type,
                confidence,
                time_diff,
            ])

        return np.array(features)
    
    def train_isolation_forest(self, training_data: np.ndarray) -> bool:
        """
        Train Isolation Forest model with StandardScaler normalisation.
        Scaling ensures all 7 features contribute equally regardless of
        their raw numeric range (e.g. time_delta can be hundreds of hours
        while confidence is 0-1).

        Args:
            training_data: Feature matrix (n_samples, n_features)

        Returns:
            True if training successful
        """
        try:
            from sklearn.ensemble import IsolationForest
            from sklearn.preprocessing import StandardScaler

            # Fit scaler on training data and transform
            self.feature_scaler = StandardScaler()
            scaled_data = self.feature_scaler.fit_transform(training_data)

            self.model = IsolationForest(
                contamination=self.contamination,
                n_estimators=100,
                random_state=42,
                n_jobs=-1
            )

            self.model.fit(scaled_data)
            self.is_trained = True

            logger.info(f"Isolation Forest trained on {len(training_data)} samples "
                        f"(contamination={self.contamination}, scaled=True)")
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
            features = self.extract_features([access_event])

            # Apply the same scaler used during training
            if self.feature_scaler is not None:
                features = self.feature_scaler.transform(features)

            prediction = self.model.predict(features)[0]
            score = self.model.score_samples(features)[0]

            # Sigmoid normalisation → 0-1 range (higher = more anomalous)
            normalized_score = 1 / (1 + np.exp(score))

            is_anomaly = prediction == -1

            result = {
                'is_anomaly': bool(is_anomaly),
                'anomaly_score': float(normalized_score),
                'confidence': float(abs(score)),
                'timestamp': datetime.now().isoformat()
            }

            if is_anomaly:
                logger.warning(f"Anomaly detected: score={normalized_score:.3f}")

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
        """Save trained model and scaler to disk as a single bundle."""
        try:
            import pickle
            bundle = {'model': self.model, 'scaler': self.feature_scaler}
            with open(filepath, 'wb') as f:
                pickle.dump(bundle, f)
            logger.info(f"Model + scaler saved to {filepath}")
            return True
        except Exception as e:
            logger.error(f"Error saving model: {e}")
            return False

    def load_model(self, filepath: str) -> bool:
        """Load trained model and scaler from disk."""
        try:
            import pickle
            with open(filepath, 'rb') as f:
                bundle = pickle.load(f)
            # Support both old format (bare model) and new bundle format
            if isinstance(bundle, dict):
                self.model = bundle['model']
                self.feature_scaler = bundle.get('scaler')
            else:
                self.model = bundle
                self.feature_scaler = None
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
