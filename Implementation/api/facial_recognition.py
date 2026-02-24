"""
Facial Recognition Module for Access Control
Uses OpenCV for face detection and recognition
"""
import cv2
import numpy as np
import logging
from datetime import datetime
from typing import Tuple, List, Optional

logger = logging.getLogger(__name__)

# Match when distance is below this. Live webcam needs higher (0.55); stored photos work with lower.
DISTANCE_MATCH_THRESHOLD = 0.55
# When second-best is a *different* person, best must be this much closer (avoids wrong match).
MIN_DISTANCE_MARGIN_DIFFERENT_PERSON = 0.05

# Optional: use face_recognition (dlib) library for much better accuracy. Fallback to OpenCV if not installed.
try:
    import face_recognition as fr_lib
    USE_FACE_RECOGNITION_LIB = True
except ImportError:
    fr_lib = None
    USE_FACE_RECOGNITION_LIB = False

class FacialRecognitionEngine:
    """
    Handles face detection and recognition for access control.
    Uses OpenCV cascade classifiers for detection.
    """
    
    def __init__(self, confidence_threshold=0.6):
        """
        Initialize facial recognition engine.
        
        Args:
            confidence_threshold: Minimum confidence score for face match
        """
        self.confidence_threshold = confidence_threshold
        
        # Load pre-trained cascade classifier
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        self.face_cascade = cv2.CascadeClassifier(cascade_path)
        
        # Known faces database (to be populated during setup)
        self.known_faces = {}  # {person_id: [face_encodings]}
        self.person_names = {}  # {person_id: name}
        
        if USE_FACE_RECOGNITION_LIB:
            logger.info("Facial Recognition Engine initialized (using face_recognition/dlib for best accuracy)")
        else:
            logger.info("Facial Recognition Engine initialized (OpenCV fallback; install 'face_recognition' for better results)")
    
    def detect_faces(self, frame: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """
        Detect faces in a given frame.
        
        Args:
            frame: Input image frame (BGR format)
            
        Returns:
            List of face rectangles (x, y, w, h)
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.05,
            minNeighbors=5,
            minSize=(30, 30)
        )
        return faces
    
    def recognize_face(self, frame: np.ndarray, face_location: Tuple) -> Optional[dict]:
        """
        Recognize a detected face by comparing to registered faces.
        
        Args:
            frame: Input image frame
            face_location: Face bounding box (x, y, w, h)
            
        Returns:
            Dictionary with recognition result or None
        """
        x, y, w, h = face_location
        face_roi = frame[y:y+h, x:x+w]
        
        # Extract features from detected face
        test_encoding = self._extract_face_features(face_roi)
        
        if test_encoding is None:
            return {
                'person_id': None,
                'name': 'Unknown',
                'confidence': 0.0,
                'timestamp': datetime.now().isoformat()
            }
        
        # Compare to registered faces: find best and second-best (by distance), and who they belong to
        best_match = None
        best_distance = float('inf')
        second_best_distance = float('inf')
        second_best_match = None
        
        for person_id, encodings in self.known_faces.items():
            for known_encoding in encodings:
                distance = float(np.linalg.norm(test_encoding - known_encoding))
                if distance < best_distance:
                    second_best_distance = best_distance
                    second_best_match = best_match
                    best_distance = distance
                    best_match = person_id
                elif distance < second_best_distance:
                    second_best_distance = distance
                    second_best_match = person_id
        
        # Only require margin when second-best is a *different* person (fixes "Unknown" when you have multiple photos per person)
        if second_best_match is None or second_best_match == best_match:
            margin_ok = True
        else:
            margin_ok = bool((second_best_distance - best_distance) >= MIN_DISTANCE_MARGIN_DIFFERENT_PERSON)
        
        distance_threshold = 0.6 if USE_FACE_RECOGNITION_LIB else DISTANCE_MATCH_THRESHOLD
        within_threshold = bool(best_distance < distance_threshold)
        confidence = float(max(0.0, min(1.0, 1.0 - (best_distance / 0.6))))
        is_match = (
            best_match is not None
            and within_threshold
            and margin_ok
            and confidence >= self.confidence_threshold
        )
        
        if is_match:
            result = {
                'person_id': best_match,
                'name': self.person_names.get(best_match, 'Unknown'),
                'confidence': float(confidence),
                'timestamp': datetime.now().isoformat()
            }
            logger.info(f"Face recognized: {result['name']} (confidence: {confidence:.2f})")
        else:
            result = {
                'person_id': None,
                'name': 'Unknown',
                'confidence': float(confidence),
                'timestamp': datetime.now().isoformat()
            }
            logger.info(f"Unknown face detected (confidence: {confidence:.2f})")
        
        return result
    
    def register_face(self, person_id: str, name: str, face_encoding: np.ndarray) -> bool:
        """
        Register a new face in the system.
        
        Args:
            person_id: Unique identifier for person
            name: Person's name
            face_encoding: Face encoding vector
            
        Returns:
            True if registration successful
        """
        try:
            if person_id not in self.known_faces:
                self.known_faces[person_id] = []
            
            self.known_faces[person_id].append(face_encoding)
            self.person_names[person_id] = name
            
            logger.info(f"Face registered for {name} (ID: {person_id})")
            return True
        except Exception as e:
            logger.error(f"Error registering face: {e}")
            return False

    def remove_face(self, person_id: str) -> bool:
        """Remove a person from the recognition engine (they will no longer be recognized)."""
        try:
            if person_id in self.known_faces:
                del self.known_faces[person_id]
            if person_id in self.person_names:
                del self.person_names[person_id]
            logger.info(f"Face removed for person_id: {person_id}")
            return True
        except Exception as e:
            logger.error(f"Error removing face: {e}")
            return False

    def _extract_face_features(self, face_roi: np.ndarray) -> Optional[np.ndarray]:
        """
        Extract feature vector from face image.
        Uses face_recognition (dlib) when available, else OpenCV gradient+histogram.
        
        Args:
            face_roi: Face region of interest (image, BGR)
            
        Returns:
            Feature vector (128-dim) or None
        """
        try:
            if face_roi is None or face_roi.size == 0:
                return None
            
            # Prefer face_recognition (dlib) - much better accuracy for live webcam
            if USE_FACE_RECOGNITION_LIB and fr_lib is not None:
                rgb = cv2.cvtColor(face_roi, cv2.COLOR_BGR2RGB)
                h, w = rgb.shape[:2]
                # Treat whole ROI as one face (top, right, bottom, left)
                encodings = fr_lib.face_encodings(rgb, known_face_locations=[(0, w, h, 0)])
                if encodings:
                    return encodings[0].astype(np.float32)
                return None
            
            # OpenCV fallback
            resized = cv2.resize(face_roi, (64, 64))
            gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
            
            # Apply histogram equalization for better contrast
            gray = cv2.equalizeHist(gray)
            
            # Compute gradient features (Sobel)
            # This works reliably across OpenCV versions
            sobelx = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
            sobely = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
            
            # Compute magnitude and direction
            magnitude = np.sqrt(sobelx**2 + sobely**2)
            direction = np.arctan2(sobely, sobelx)
            
            # Create histogram of gradients (8 bins for direction)
            hist_edges = np.linspace(-np.pi, np.pi, 9)
            hist_grad, _ = np.histogram(direction.flatten(), bins=hist_edges, weights=magnitude.flatten())
            
            # Also get color histogram for robustness
            hist_gray = cv2.calcHist([gray], [0], None, [64], [0, 256]).flatten()
            
            # Combine both histograms
            combined_features = np.concatenate([hist_grad, hist_gray])
            
            # Ensure exactly 128-dimensional output
            if len(combined_features) > 128:
                combined_features = combined_features[:128]
            elif len(combined_features) < 128:
                padding = np.zeros(128 - len(combined_features))
                combined_features = np.concatenate([combined_features, padding])
            
            # Normalize vector to unit length for better distance comparison
            norm = np.linalg.norm(combined_features)
            if norm > 0:
                combined_features = combined_features / norm
            
            return combined_features.astype(np.float32)
        except Exception as e:
            logger.error(f"Error extracting face features: {e}")
            return None
    
    def get_recognition_stats(self) -> dict:
        """Get statistics about recognized faces"""
        return {
            'total_persons': len(self.known_faces),
            'total_face_encodings': sum(len(faces) for faces in self.known_faces.values()),
            'confidence_threshold': self.confidence_threshold
        }
