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
        
        logger.info("Facial Recognition Engine initialized")
    
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
        
        # Compare to registered faces
        best_match = None
        best_distance = float('inf')
        
        for person_id, encodings in self.known_faces.items():
            for known_encoding in encodings:
                # Calculate distance (euclidean)
                distance = np.linalg.norm(test_encoding - known_encoding)
                
                if distance < best_distance:
                    best_distance = distance
                    best_match = person_id
        
        # Determine if match is valid based on distance threshold
        # Lower distance = better match. Threshold typically 0.6-0.7
        confidence = max(0, 1 - (best_distance / 1.0))  # Normalize distance to confidence
        is_match = best_distance < 0.7  # Distance threshold
        
        if is_match and best_match:
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
    
    def _extract_face_features(self, face_roi: np.ndarray) -> Optional[np.ndarray]:
        """
        Extract feature vector from face image.
        Uses gradient and color histogram features for face encoding.
        
        Args:
            face_roi: Face region of interest (image)
            
        Returns:
            Feature vector (128-dim) or None
        """
        try:
            if face_roi is None or face_roi.size == 0:
                return None
            
            # Resize to standard size for consistent feature extraction
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
