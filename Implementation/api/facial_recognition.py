"""
Facial Recognition Module for Access Control

Default   : OpenCV Haar Cascade (detection) + OpenCV LBPH (encoding)
Optional  : pass use_dlib=True to FacialRecognitionEngine to use dlib for
            both detection (HOG) and encoding (ResNet-128).

Biometric data is encrypted at rest using Fernet (AES-128-CBC) before writing
to disk, and decrypted on load.  The key is derived from config.ENCRYPTION_KEY.
"""
import cv2
import numpy as np
import logging
import json
import io
import base64
import hashlib
from collections import deque, Counter
from datetime import datetime
from pathlib import Path
from typing import Tuple, List, Optional

from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)

# Match when distance is below this.
# dlib uses its own threshold of 0.6 (set inline below).
# OpenCV LBPH fallback: 0.55 is the right balance.
DISTANCE_MATCH_THRESHOLD = 0.55
# When second-best is a *different* person, best must be this much closer (avoids wrong match).
MIN_DISTANCE_MARGIN_DIFFERENT_PERSON = 0.05

# ── dlib / face_recognition (only used when use_dlib=True) ───────────────────
try:
    import face_recognition as fr_lib
    _DLIB_AVAILABLE = True
except ImportError:
    fr_lib = None
    _DLIB_AVAILABLE = False

# Backward-compat alias — other files import this to check if dlib is installed
USE_FACE_RECOGNITION_LIB = _DLIB_AVAILABLE


def _get_fernet() -> Fernet:
    """Derive a Fernet key from config.ENCRYPTION_KEY (any-length passphrase).

    Fernet requires a 32-byte URL-safe base64 key.  We SHA-256 hash the
    passphrase to get exactly 32 bytes, then base64-encode it.
    """
    try:
        from config import ENCRYPTION_KEY
    except ImportError:
        ENCRYPTION_KEY = "default-encryption-key"
    raw = hashlib.sha256(ENCRYPTION_KEY.encode()).digest()
    return Fernet(base64.urlsafe_b64encode(raw))

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

    Detection : OpenCV Haar Cascade (fast, no extra deps)
    Encoding  : dlib ResNet-128 (preferred) or OpenCV LBPH fallback
    """

    def __init__(self, confidence_threshold=0.6, use_dlib=False):
        self.confidence_threshold = confidence_threshold
        self.use_dlib = use_dlib and _DLIB_AVAILABLE

        if use_dlib and not _DLIB_AVAILABLE:
            logger.warning("use_dlib=True but face_recognition is not installed — falling back to OpenCV")

        # ── Haar cascade (always loaded as fallback) ──────────────────────
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        self.face_cascade = cv2.CascadeClassifier(cascade_path)

        # ── CLAHE for low-light preprocessing ─────────────────────────────
        self._clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))

        self.known_faces = {}   # {person_id: [face_encodings]}
        self.person_names = {}  # {person_id: name}

        self.buffer = RecognitionBuffer(maxlen=5, min_samples=3)

        det_name = "dlib HOG" if self.use_dlib else "OpenCV Haar Cascade"
        enc_name = "dlib ResNet-128" if self.use_dlib else "OpenCV LBPH"
        logger.info(f"Facial Recognition Engine initialized  "
                     f"(detect={det_name}, encode={enc_name})")

    # ── Detection ─────────────────────────────────────────────────────────────

    def detect_faces(self, frame: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """
        Detect faces in *frame* (BGR).

        Returns a list of (x, y, w, h) bounding boxes.
        Uses dlib HOG when use_dlib=True, otherwise OpenCV Haar Cascade.
        """
        if self.use_dlib:
            return self._detect_faces_dlib(frame)
        return self._detect_faces_haar(frame)

    def _detect_faces_dlib(self, frame: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """dlib HOG face detector — much more accurate than Haar cascade.

        face_recognition.face_locations() returns (top, right, bottom, left)
        tuples.  We convert to (x, y, w, h) to match the rest of our API.
        """
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        locations = fr_lib.face_locations(rgb, model="hog")
        faces: List[Tuple[int, int, int, int]] = []
        for (top, right, bottom, left) in locations:
            x = left
            y = top
            w = right - left
            h = bottom - top
            if w >= 40 and h >= 40:
                faces.append((x, y, w, h))
        return faces

    def _detect_faces_haar(self, frame: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """Haar Cascade detector with CLAHE for better low-light detection."""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = self._clahe.apply(gray)
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=4,
            minSize=(50, 50)
        )
        return [(int(x), int(y), int(w_), int(h_)) for x, y, w_, h_ in faces]
    
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
        
        distance_threshold = 0.6 if self.use_dlib else DISTANCE_MATCH_THRESHOLD
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

    # ── Preprocessing helpers ───────────────────────────────────────────────

    def _apply_clahe(self, face_roi: np.ndarray) -> np.ndarray:
        """Apply CLAHE contrast normalisation to the face ROI (BGR in, BGR out).

        This dramatically improves encoding quality in uneven or low
        lighting — the single biggest environmental factor in accuracy loss.
        """
        lab = cv2.cvtColor(face_roi, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        l = self._clahe.apply(l)
        return cv2.cvtColor(cv2.merge([l, a, b]), cv2.COLOR_LAB2BGR)

    @staticmethod
    def _compute_lbp(gray: np.ndarray, radius: int = 1) -> np.ndarray:
        """Compute a simple circular LBP (Local Binary Pattern) image.

        LBP encodes the micro-texture around every pixel into an 8-bit code
        by comparing the center pixel to its *radius*-distant neighbours.
        This is far more discriminative for faces than raw gradient histograms.
        """
        h, w = gray.shape
        lbp = np.zeros_like(gray)
        offsets = [
            (-radius,  0),      (-radius,  radius),
            (0,        radius), ( radius,  radius),
            ( radius,  0),      ( radius, -radius),
            (0,       -radius), (-radius, -radius),
        ]
        for i, (dy, dx) in enumerate(offsets):
            ny = np.clip(np.arange(h) + dy, 0, h - 1)
            nx = np.clip(np.arange(w) + dx, 0, w - 1)
            neighbor = gray[np.ix_(ny, nx)]
            lbp |= ((neighbor >= gray).astype(np.uint8) << i)
        return lbp

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
            if self.use_dlib and fr_lib is not None:
                rgb = cv2.cvtColor(face_roi, cv2.COLOR_BGR2RGB)
                h, w = rgb.shape[:2]
                landmarks_list = fr_lib.face_landmarks(
                    rgb, face_locations=[(0, w, h, 0)]
                )
                if landmarks_list:
                    lm = landmarks_list[0]
                    left_pts  = lm.get("left_eye",  [])
                    right_pts = lm.get("right_eye", [])
                    # Guard: np.mean([], axis=0) returns nan with size==1, which is
                    # truthy and produces garbage alignment. Check the source lists.
                    if left_pts and right_pts:
                        left_eye  = np.mean(left_pts,  axis=0)
                        right_eye = np.mean(right_pts, axis=0)
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
        Persist all registered face encodings to an encrypted file on disk.

        The encodings are serialised as a compressed .npz in memory, then
        encrypted with Fernet (AES-128-CBC) using the key from config.py
        before being written to *path*.  A separate encrypted JSON sidecar
        stores the person-name mapping.

        Args:
            path: File path to write, e.g. 'models/face_encodings.npz'

        Returns:
            True on success.
        """
        try:
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            fernet = _get_fernet()

            # Serialise arrays to an in-memory buffer, then encrypt
            arrays = {}
            meta   = {}
            for person_id, encodings in self.known_faces.items():
                key = f"enc_{person_id}"
                arrays[key] = np.array(encodings, dtype=np.float32)
                meta[person_id] = self.person_names.get(person_id, person_id)

            buf = io.BytesIO()
            np.savez_compressed(buf, **arrays)
            encrypted_data = fernet.encrypt(buf.getvalue())

            with open(path, 'wb') as f:
                f.write(encrypted_data)

            meta_path = str(path).replace('.npz', '_meta.json')
            encrypted_meta = fernet.encrypt(json.dumps(meta).encode())
            with open(meta_path, 'wb') as f:
                f.write(encrypted_meta)

            logger.info(f"Saved {len(self.known_faces)} person(s) to {path} (encrypted)")
            return True
        except Exception as e:
            logger.error(f"Could not save encodings: {e}")
            return False

    def load_encodings(self, path: str) -> int:
        """
        Load face encodings previously saved with save_encodings().

        Decrypts the file with Fernet, then loads the .npz arrays.
        Merges loaded persons into the current known_faces dict.

        Args:
            path: Path to the encrypted file written by save_encodings()

        Returns:
            Number of persons loaded (0 on failure).
        """
        try:
            enc_path  = Path(path)
            meta_path = Path(str(path).replace('.npz', '_meta.json'))

            if not enc_path.exists():
                logger.warning(f"Encodings file not found: {path}")
                return 0

            fernet = _get_fernet()

            with open(enc_path, 'rb') as f:
                decrypted = fernet.decrypt(f.read())
            data = np.load(io.BytesIO(decrypted))

            meta: dict = {}
            if meta_path.exists():
                with open(meta_path, 'rb') as f:
                    meta = json.loads(fernet.decrypt(f.read()).decode())

            loaded = 0
            for key in data.files:
                person_id = key.replace('enc_', '', 1)
                encodings = [data[key][i] for i in range(len(data[key]))]
                self.known_faces[person_id]  = encodings
                self.person_names[person_id] = meta.get(person_id, person_id)
                loaded += 1

            logger.info(f"Loaded {loaded} person(s) from {path} (decrypted)")
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

            # CLAHE contrast normalization — dramatically improves low-light and
            # uneven-lighting conditions before any encoding step.
            face_roi = self._apply_clahe(face_roi)

            # Align face to canonical pose before encoding
            face_roi = self._align_face(face_roi)

            # ── dlib ResNet encoder (only when use_dlib=True) ─────────────
            if self.use_dlib and fr_lib is not None:
                rgb = cv2.cvtColor(face_roi, cv2.COLOR_BGR2RGB)
                h, w = rgb.shape[:2]
                encodings = fr_lib.face_encodings(rgb, known_face_locations=[(0, w, h, 0)])
                if encodings:
                    return encodings[0].astype(np.float32)
                return None

            # ── OpenCV LBPH + gradient fallback ───────────────────────────
            resized = cv2.resize(face_roi, (96, 96))
            gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
            gray = cv2.equalizeHist(gray)

            # LBP (Local Binary Pattern) — encodes micro-texture around each pixel.
            # Far more discriminative for faces than raw gradient histograms.
            lbp = self._compute_lbp(gray)
            hist_lbp, _ = np.histogram(lbp.ravel(), bins=64, range=(0, 256))
            hist_lbp = hist_lbp.astype(np.float32)

            # HOG-lite: oriented gradient magnitudes in an 8-bin histogram
            sobelx = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
            sobely = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
            magnitude = np.sqrt(sobelx**2 + sobely**2)
            direction = np.arctan2(sobely, sobelx)
            hist_edges = np.linspace(-np.pi, np.pi, 9)
            hist_grad, _ = np.histogram(direction.ravel(), bins=hist_edges,
                                        weights=magnitude.ravel())
            hist_grad = hist_grad.astype(np.float32)

            # Spatial intensity histogram (captures overall brightness distribution)
            hist_gray = cv2.calcHist([gray], [0], None, [56], [0, 256]).flatten()

            combined = np.concatenate([hist_lbp, hist_grad, hist_gray])   # 64+8+56 = 128

            norm = np.linalg.norm(combined)
            if norm > 0:
                combined = combined / norm

            return combined.astype(np.float32)
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
