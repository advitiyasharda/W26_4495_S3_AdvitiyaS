"""
Facial Recognition Module for Access Control
Uses OpenCV for face detection and recognition
"""
import cv2
import numpy as np
import logging
import json
from collections import deque, Counter
from datetime import datetime
from pathlib import Path
from typing import Tuple, List, Optional

logger = logging.getLogger(__name__)

# Match when distance is below this. Live webcam needs higher (0.55); stored photos work with lower.
DISTANCE_MATCH_THRESHOLD = 0.3
# When second-best is a *different* person, best must be this much closer (avoids wrong match).
MIN_DISTANCE_MARGIN_DIFFERENT_PERSON = 0.05

# Optional: use face_recognition (dlib) library for much better accuracy. Fallback to OpenCV if not installed.
try:
    import face_recognition as fr_lib
    USE_FACE_RECOGNITION_LIB = True
except ImportError:
    fr_lib = None
    USE_FACE_RECOGNITION_LIB = False

class RecognitionBuffer:
    """
    Smooths face recognition over a rolling window of recent frames.

    On a door camera, a single bad frame (dark, partially occluded, motion
    blur) can deny access to a registered resident.  This buffer keeps the
    last N results and returns the majority-vote identity with averaged
    confidence so one bad frame cannot flip the decision on its own.

    Usage:
        buf = RecognitionBuffer(maxlen=5, min_samples=3)
        buf.update(person_id, confidence)
        result = buf.get_smoothed()   # stable after min_samples frames
    """

    def __init__(self, maxlen: int = 5, min_samples: int = 3):
        self.maxlen      = maxlen
        self.min_samples = min_samples
        self._history: deque = deque(maxlen=maxlen)  # (person_id | None, confidence)

    def update(self, person_id: Optional[str], confidence: float) -> None:
        """Add the latest raw recognition result to the rolling window."""
        self._history.append((person_id, float(confidence)))

    def get_smoothed(self) -> dict:
        """
        Return the smoothed result from recent history.

        Returns:
            {
              "person_id":    str | None,  # majority-vote identity
              "confidence":   float,       # mean confidence for that identity
              "is_stable":    bool,        # True once min_samples frames seen
              "sample_count": int
            }
        """
        if not self._history:
            return {"person_id": None, "confidence": 0.0,
                    "is_stable": False, "sample_count": 0}

        sample_count = len(self._history)
        is_stable    = sample_count >= self.min_samples

        ids         = [entry[0] for entry in self._history]
        majority_id = Counter(ids).most_common(1)[0][0]

        matching  = [conf for pid, conf in self._history if pid == majority_id]
        avg_conf  = round(sum(matching) / len(matching), 4)

        return {
            "person_id":    majority_id,
            "confidence":   avg_conf,
            "is_stable":    is_stable,
            "sample_count": sample_count,
        }

    def reset(self) -> None:
        """Clear the buffer — call between sessions or on scene change."""
        self._history.clear()

    def __len__(self) -> int:
        return len(self._history)


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
        
        # Per-engine smoothing buffer — keeps last 5 single-face results
        # so one bad frame cannot deny access to a registered resident.
        self.buffer = RecognitionBuffer(maxlen=5, min_samples=3)

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
        # Use the active threshold as the denominator so confidence is always
        # relative to whichever engine (dlib or OpenCV) is actually running.
        confidence = float(max(0.0, min(1.0, 1.0 - (best_distance / distance_threshold))))
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

    def _score_face_quality(self, face_roi: np.ndarray) -> dict:
        """
        Score a face ROI on three quality dimensions before registration.

        Checks:
          size       — ROI must be at least 60×60 px (smaller = unreliable features)
          blur       — Laplacian variance must be ≥ 40 (low = blurry / out of focus)
          brightness — mean pixel value must be 30–220 (avoid pitch-black or washed-out)

        Returns a dict:
          {
            "passed":       bool,
            "score":        float,   # 0.0 – 1.0 composite
            "size_ok":      bool,
            "blur_ok":      bool,
            "brightness_ok": bool,
            "reason":       str      # human-readable summary
          }
        """
        if face_roi is None or face_roi.size == 0:
            return {"passed": False, "score": 0.0, "size_ok": False,
                    "blur_ok": False, "brightness_ok": False,
                    "reason": "Empty or missing face ROI"}

        h, w = face_roi.shape[:2]
        gray = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY)

        # ── Size ────────────────────────────────────────────────────────────
        MIN_DIM = 60
        size_ok = (h >= MIN_DIM and w >= MIN_DIM)

        # ── Blur (Laplacian variance) ────────────────────────────────────────
        BLUR_THRESHOLD = 40.0
        lap_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        blur_ok = lap_var >= BLUR_THRESHOLD

        # ── Brightness (mean pixel value) ────────────────────────────────────
        BRIGHT_MIN, BRIGHT_MAX = 30.0, 220.0
        mean_brightness = float(gray.mean())
        brightness_ok = BRIGHT_MIN <= mean_brightness <= BRIGHT_MAX

        # ── Composite score (equal weight) ───────────────────────────────────
        score = round(sum([size_ok, blur_ok, brightness_ok]) / 3.0, 3)
        passed = size_ok and blur_ok and brightness_ok

        reasons = []
        if not size_ok:
            reasons.append(f"too small ({w}×{h}px, need {MIN_DIM}×{MIN_DIM})")
        if not blur_ok:
            reasons.append(f"blurry (variance={lap_var:.1f}, need ≥{BLUR_THRESHOLD})")
        if not brightness_ok:
            reasons.append(f"bad lighting (mean={mean_brightness:.0f}, need {BRIGHT_MIN}–{BRIGHT_MAX})")
        reason = "; ".join(reasons) if reasons else "OK"

        return {
            "passed":        passed,
            "score":         score,
            "size_ok":       size_ok,
            "blur_ok":       blur_ok,
            "brightness_ok": brightness_ok,
            "reason":        reason,
        }

    def _align_face(self, face_roi: np.ndarray,
                    output_size: int = 112) -> np.ndarray:
        """
        Align a face ROI to a canonical pose before encoding.

        When dlib (face_recognition) is available the eye positions come from
        dlib's 68-point landmark model and we apply an affine warp to place
        both eyes at fixed target coordinates.  This corrects in-plane
        rotation so a 15° head tilt doesn't produce a completely different
        encoding vector.

        When dlib is not available we fall back to OpenCV's Haar eye
        detector.  If eye detection fails for any reason we skip alignment
        and return the resized ROI so the caller always gets a usable image.

        Args:
            face_roi:    BGR face crop (any size)
            output_size: Side length of the square output image (default 112)

        Returns:
            Aligned (or plain-resized) BGR face image of shape
            (output_size, output_size, 3).
        """
        try:
            if USE_FACE_RECOGNITION_LIB and fr_lib is not None:
                rgb = cv2.cvtColor(face_roi, cv2.COLOR_BGR2RGB)
                h, w = rgb.shape[:2]
                landmarks_list = fr_lib.face_landmarks(
                    rgb, face_locations=[(0, w, h, 0)]
                )
                if landmarks_list:
                    lm = landmarks_list[0]
                    # Mean of the inner eye corner points
                    left_eye  = np.mean(lm.get("left_eye",  []), axis=0)
                    right_eye = np.mean(lm.get("right_eye", []), axis=0)

                    if left_eye.size and right_eye.size:
                        # Canonical eye positions inside output_size square
                        # (roughly 30 % from each side, 35 % from top)
                        desired_left  = np.array([output_size * 0.30, output_size * 0.35])
                        desired_right = np.array([output_size * 0.70, output_size * 0.35])

                        dx = right_eye[0] - left_eye[0]
                        dy = right_eye[1] - left_eye[1]
                        angle  = np.degrees(np.arctan2(dy, dx))
                        scale  = (np.linalg.norm(desired_right - desired_left)
                                  / (np.linalg.norm(right_eye - left_eye) + 1e-6))
                        center = tuple(((left_eye + right_eye) / 2).astype(int))

                        M = cv2.getRotationMatrix2D(center, angle, scale)
                        # Shift so the eye midpoint lands in the right spot
                        M[0, 2] += (output_size / 2) - center[0]
                        M[1, 2] += (output_size * 0.35) - center[1]

                        aligned = cv2.warpAffine(
                            face_roi, M, (output_size, output_size),
                            flags=cv2.INTER_LINEAR,
                            borderMode=cv2.BORDER_REPLICATE,
                        )
                        return aligned

            # OpenCV Haar eye detector fallback
            gray = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY)
            eye_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_eye.xml'
            )
            eyes = eye_cascade.detectMultiScale(gray, 1.1, 5, minSize=(15, 15))

            if len(eyes) >= 2:
                # Sort left-to-right
                eyes = sorted(eyes, key=lambda e: e[0])
                lx, ly, lw, lh = eyes[0]
                rx, ry, rw, rh = eyes[1]
                left_eye  = np.array([lx + lw / 2, ly + lh / 2])
                right_eye = np.array([rx + rw / 2, ry + rh / 2])

                desired_left  = np.array([output_size * 0.30, output_size * 0.35])
                desired_right = np.array([output_size * 0.70, output_size * 0.35])

                dx = right_eye[0] - left_eye[0]
                dy = right_eye[1] - left_eye[1]
                angle  = np.degrees(np.arctan2(dy, dx))
                scale  = (np.linalg.norm(desired_right - desired_left)
                          / (np.linalg.norm(right_eye - left_eye) + 1e-6))
                center = tuple(((left_eye + right_eye) / 2).astype(int))

                M = cv2.getRotationMatrix2D(center, angle, scale)
                M[0, 2] += (output_size / 2) - center[0]
                M[1, 2] += (output_size * 0.35) - center[1]

                aligned = cv2.warpAffine(
                    face_roi, M, (output_size, output_size),
                    flags=cv2.INTER_LINEAR,
                    borderMode=cv2.BORDER_REPLICATE,
                )
                return aligned

        except Exception as e:
            logger.debug(f"Face alignment skipped: {e}")

        # No landmarks / eye detection failed — plain resize as fallback
        return cv2.resize(face_roi, (output_size, output_size))

    # ── Encoding persistence ──────────────────────────────────────────────────

    def save_encodings(self, path: str) -> bool:
        """
        Persist all registered face encodings to a .npz file on disk.

        Call this after a registration session so the engine can be
        restored at next startup without re-processing every photo.

        Args:
            path: File path to write, e.g. 'models/face_encodings.npz'

        Returns:
            True on success.
        """
        try:
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            arrays = {}
            meta   = {}
            for person_id, encodings in self.known_faces.items():
                key = f"enc_{person_id}"
                arrays[key] = np.array(encodings, dtype=np.float32)
                meta[person_id] = self.person_names.get(person_id, person_id)

            np.savez_compressed(path, **arrays)
            # Store name mapping alongside the .npz
            meta_path = str(path).replace('.npz', '_meta.json')
            with open(meta_path, 'w') as f:
                json.dump(meta, f, indent=2)

            logger.info(f"Saved {len(self.known_faces)} person(s) to {path}")
            return True
        except Exception as e:
            logger.error(f"Could not save encodings: {e}")
            return False

    def load_encodings(self, path: str) -> int:
        """
        Load face encodings previously saved with save_encodings().

        Merges loaded persons into the current known_faces dict so you
        can call this multiple times (e.g. load base set then add guests).

        Args:
            path: Path to the .npz file written by save_encodings()

        Returns:
            Number of persons loaded (0 on failure).
        """
        try:
            npz_path  = Path(path)
            meta_path = Path(str(path).replace('.npz', '_meta.json'))

            if not npz_path.exists():
                logger.warning(f"Encodings file not found: {path}")
                return 0

            data = np.load(str(npz_path))
            meta: dict = {}
            if meta_path.exists():
                with open(meta_path) as f:
                    meta = json.load(f)

            loaded = 0
            for key in data.files:
                person_id = key.replace('enc_', '', 1)
                encodings = [data[key][i] for i in range(len(data[key]))]
                self.known_faces[person_id]  = encodings
                self.person_names[person_id] = meta.get(person_id, person_id)
                loaded += 1

            logger.info(f"Loaded {loaded} person(s) from {path}")
            return loaded
        except Exception as e:
            logger.error(f"Could not load encodings: {e}")
            return 0

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

            # Align face to canonical pose before encoding
            face_roi = self._align_face(face_roi)

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
    
    def recognize_with_smoothing(self, frame: np.ndarray,
                                 face_location: Tuple) -> Optional[dict]:
        """
        Recognize one face and apply RecognitionBuffer smoothing.

        Calls recognize_face() for the current frame, feeds the raw result
        into the internal buffer, then returns the majority-vote result
        instead of the single-frame result.  Use this for live video streams
        where one dark or blurry frame should not flip the access decision.

        Returns the same dict shape as recognize_face(), with two extra fields:
          "is_stable":    bool  — False until min_samples frames are buffered
          "sample_count": int   — frames seen so far in the rolling window
        """
        raw = self.recognize_face(frame, face_location)
        if raw is None:
            return None

        self.buffer.update(raw.get("person_id"), raw.get("confidence", 0.0))
        smoothed = self.buffer.get_smoothed()

        person_id = smoothed["person_id"]
        return {
            "person_id":    person_id,
            "name":         self.person_names.get(person_id, "Unknown") if person_id else "Unknown",
            "confidence":   smoothed["confidence"],
            "timestamp":    raw.get("timestamp"),
            "is_stable":    smoothed["is_stable"],
            "sample_count": smoothed["sample_count"],
        }

    def recognize_all_faces(self, frame: np.ndarray) -> List[dict]:
        """
        Detect and recognize every face present in a single frame.

        Returns a list of recognition result dicts (same shape as
        recognize_face()) each extended with a 'face_location' key
        containing [x, y, w, h].  Returns an empty list when no
        faces are detected.
        """
        faces = self.detect_faces(frame)
        if len(faces) == 0:
            return []

        results = []
        for face_coords in faces:
            x, y, w, h = (int(v) for v in face_coords)
            result = self.recognize_face(frame, (x, y, w, h))
            if result is not None:
                result["face_location"] = [x, y, w, h]
                results.append(result)
        return results

    def get_recognition_stats(self) -> dict:
        """Get statistics about recognized faces"""
        return {
            'total_persons': len(self.known_faces),
            'total_face_encodings': sum(len(faces) for faces in self.known_faces.values()),
            'confidence_threshold': self.confidence_threshold
        }
