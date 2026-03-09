"""
Fall Detection Module — Phase 1: Rules-Based (MediaPipe Pose)

How it works:
  MediaPipe PoseLandmarker (Tasks API, mediapipe >= 0.10) extracts 33 body
  landmarks per frame.  Three rules are applied to decide if a fall occurred:

    1. Hip height   — hips near bottom of frame → person is on the ground
    2. Torso angle  — spine nearly horizontal   → person is lying down
    3. Hip velocity — hips dropped fast across recent frames → active fall

  All three signals are combined into a weighted confidence score (0–1).
  A fall is flagged when confidence ≥ FALL_THRESHOLD.

Model file (required):
  models/pose_landmarker.task — download once with:
    curl -L -o models/pose_landmarker.task \
      https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_full/float16/1/pose_landmarker_full.task

Phase 2 plan:
  Replace/augment these rules with an LSTM that takes a sequence of
  (33 × 4) landmark vectors over N frames and classifies fall/no-fall.
  Training data: UR Fall Detection Dataset (RGB + depth videos).
"""

import math
import logging
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)

# Default model path (relative to project root, i.e. Implementation/)
DEFAULT_MODEL_PATH = Path(__file__).parent / "pose_landmarker.task"

# ── MediaPipe landmark indices ──────────────────────────────────────────────
NOSE           = 0
LEFT_SHOULDER  = 11
RIGHT_SHOULDER = 12
LEFT_HIP       = 23
RIGHT_HIP      = 24
LEFT_KNEE      = 25
RIGHT_KNEE     = 26

# ── Tunable thresholds ──────────────────────────────────────────────────────
FALL_THRESHOLD        = 0.55   # weighted confidence to declare a fall
HIP_HEIGHT_THRESHOLD  = 0.72   # normalised y; >this means hips are near floor
                                # (MediaPipe y=0 at top, y=1 at bottom)
TORSO_ANGLE_THRESHOLD = 50.0   # degrees from vertical; >this = torso tilted
VELOCITY_THRESHOLD    = 0.07   # normalised-y drop per frame; >this = fast drop
VELOCITY_WINDOW       = 8      # frames to track for velocity
MIN_VISIBILITY        = 0.4    # ignore landmarks below this visibility score

# Rule weights (must sum to 1.0)
W_HIP_HEIGHT  = 0.40
W_TORSO_ANGLE = 0.35
W_VELOCITY    = 0.25


@dataclass
class FallResult:
    is_fall: bool
    confidence: float           # 0.0 – 1.0
    reason: str                 # human-readable explanation
    hip_height: float           # normalised y of mid-hip (0=top, 1=bottom)
    torso_angle_deg: float      # degrees from vertical
    hip_velocity: float         # normalised-y drop in last window
    landmarks_visible: bool     # were enough landmarks detected?


class FallDetector:
    """
    Rules-based fall detector using MediaPipe Pose (Tasks API).

    Usage:
        detector = FallDetector()
        # inside your frame loop (frame is a BGR numpy array):
        result = detector.process_frame(frame)
        if result and result.is_fall:
            print("FALL DETECTED:", result.reason)

    Call detector.close() when done to release MediaPipe resources.
    """

    def __init__(self,
                 model_path: str = None,
                 fall_threshold: float = FALL_THRESHOLD,
                 velocity_window: int  = VELOCITY_WINDOW):

        model_path = model_path or str(DEFAULT_MODEL_PATH)

        if not Path(model_path).exists():
            raise FileNotFoundError(
                f"MediaPipe pose model not found at '{model_path}'.\n"
                "Download it once with:\n"
                "  curl -L -o models/pose_landmarker.task \\\n"
                "    https://storage.googleapis.com/mediapipe-models/"
                "pose_landmarker/pose_landmarker_full/float16/1/pose_landmarker_full.task"
            )

        try:
            import mediapipe as mp
            self._mp   = mp
            self._vis  = mp.tasks.vision
            self._draw = mp.tasks.vision.drawing_utils

            BaseOptions        = mp.tasks.BaseOptions
            PoseLandmarker     = mp.tasks.vision.PoseLandmarker
            PoseLandmarkerOpts = mp.tasks.vision.PoseLandmarkerOptions
            RunningMode        = mp.tasks.vision.RunningMode

            options = PoseLandmarkerOpts(
                base_options=BaseOptions(model_asset_path=model_path),
                running_mode=RunningMode.IMAGE,   # frame-by-frame (no callback)
                num_poses=1,
                min_pose_detection_confidence=0.5,
                min_pose_presence_confidence=0.5,
                min_tracking_confidence=0.5,
            )
            self._landmarker = PoseLandmarker.create_from_options(options)
            logger.info("MediaPipe PoseLandmarker initialised from %s", model_path)
        except ImportError:
            raise ImportError(
                "mediapipe is required. Install it with: pip install mediapipe"
            )

        self.fall_threshold  = fall_threshold
        self.velocity_window = velocity_window

        self._hip_y_history: deque = deque(maxlen=velocity_window)
        self._fall_cooldown_frames = 0
        self._cooldown_duration    = 30   # ~1 s at 30 fps

    # ── Public API ──────────────────────────────────────────────────────────

    def process_frame(self, frame: np.ndarray) -> Optional[FallResult]:
        """
        Run pose estimation + fall rules on one BGR frame.
        Returns a FallResult, or None on hard failure.
        """
        import cv2
        import mediapipe as mp

        rgb   = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w  = frame.shape[:2]
        mp_img = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=np.ascontiguousarray(rgb),
        )

        detection = self._landmarker.detect(mp_img)

        if not detection.pose_landmarks or len(detection.pose_landmarks) == 0:
            self._hip_y_history.clear()
            return FallResult(
                is_fall=False, confidence=0.0,
                reason="No person detected",
                hip_height=0.0, torso_angle_deg=0.0, hip_velocity=0.0,
                landmarks_visible=False,
            )

        lm = detection.pose_landmarks[0]   # first (and only) pose

        def get(idx):
            p = lm[idx]
            if p.visibility < MIN_VISIBILITY:
                return None
            return p.x, p.y

        l_sh = get(LEFT_SHOULDER)
        r_sh = get(RIGHT_SHOULDER)
        l_hp = get(LEFT_HIP)
        r_hp = get(RIGHT_HIP)

        if not all(p is not None for p in [l_sh, r_sh, l_hp, r_hp]):
            return FallResult(
                is_fall=False, confidence=0.0,
                reason="Key landmarks not visible",
                hip_height=0.0, torso_angle_deg=0.0, hip_velocity=0.0,
                landmarks_visible=False,
            )

        mid_sx = (l_sh[0] + r_sh[0]) / 2
        mid_sy = (l_sh[1] + r_sh[1]) / 2
        mid_hx = (l_hp[0] + r_hp[0]) / 2
        mid_hy = (l_hp[1] + r_hp[1]) / 2

        # ── Rule 1: Hip height ───────────────────────────────────────────
        hip_score  = self._hip_height_score(mid_hy)

        # ── Rule 2: Torso angle ──────────────────────────────────────────
        torso_angle = self._torso_angle_degrees(mid_sx, mid_sy, mid_hx, mid_hy)
        angle_score = self._torso_angle_score(torso_angle)

        # ── Rule 3: Hip downward velocity ───────────────────────────────
        self._hip_y_history.append(mid_hy)
        hip_velocity   = self._hip_velocity()
        velocity_score = self._velocity_score(hip_velocity)

        # ── Combine ──────────────────────────────────────────────────────
        confidence = float(np.clip(
            W_HIP_HEIGHT * hip_score +
            W_TORSO_ANGLE * angle_score +
            W_VELOCITY * velocity_score,
            0.0, 1.0,
        ))
        confidence = round(confidence, 3)

        if self._fall_cooldown_frames > 0:
            self._fall_cooldown_frames -= 1
            is_fall = False
        else:
            is_fall = confidence >= self.fall_threshold
            if is_fall:
                self._fall_cooldown_frames = self._cooldown_duration

        reasons = []
        if hip_score > 0.5:
            reasons.append(f"hips low ({mid_hy:.2f})")
        if angle_score > 0.5:
            reasons.append(f"torso tilted {torso_angle:.0f}°")
        if velocity_score > 0.5:
            reasons.append(f"rapid drop ({hip_velocity:.3f}/frame)")
        reason = "; ".join(reasons) if reasons else "standing normally"

        return FallResult(
            is_fall=is_fall,
            confidence=confidence,
            reason=reason,
            hip_height=round(mid_hy, 3),
            torso_angle_deg=round(torso_angle, 1),
            hip_velocity=round(hip_velocity, 4),
            landmarks_visible=True,
        )

    def draw_overlay(self, frame: np.ndarray, result: FallResult) -> np.ndarray:
        """Draw pose skeleton + fall status banner onto the frame."""
        import cv2
        import mediapipe as mp

        rgb    = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_img = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=np.ascontiguousarray(rgb),
        )
        detection = self._landmarker.detect(mp_img)

        if detection.pose_landmarks:
            PoseLandmarksConnections = mp.tasks.vision.PoseLandmarksConnections
            drawing_utils  = mp.tasks.vision.drawing_utils
            drawing_styles = mp.tasks.vision.drawing_styles

            annotated = np.copy(frame)   # draw directly on BGR copy
            for pose_lm in detection.pose_landmarks:
                drawing_utils.draw_landmarks(
                    annotated,
                    pose_lm,
                    PoseLandmarksConnections.POSE_LANDMARKS,
                    landmark_drawing_spec=drawing_styles.get_default_pose_landmarks_style(),
                )
            frame = annotated

        h, w = frame.shape[:2]

        if result.is_fall:
            cv2.rectangle(frame, (0, 0), (w, 60), (0, 0, 200), -1)
            cv2.putText(frame, "  FALL DETECTED", (10, 42),
                        cv2.FONT_HERSHEY_DUPLEX, 1.3, (255, 255, 255), 2)
        else:
            cv2.rectangle(frame, (0, 0), (w, 60), (0, 150, 0), -1)
            cv2.putText(frame, "  Monitoring...", (10, 42),
                        cv2.FONT_HERSHEY_DUPLEX, 1.0, (255, 255, 255), 2)

        info = (f"conf={result.confidence:.2f}  "
                f"hip_y={result.hip_height:.2f}  "
                f"angle={result.torso_angle_deg:.0f}deg  "
                f"vel={result.hip_velocity:.3f}")
        cv2.rectangle(frame, (0, h - 35), (w, h), (30, 30, 30), -1)
        cv2.putText(frame, info, (8, h - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200, 200, 200), 1)

        if result.reason and result.reason != "standing normally":
            cv2.putText(frame, result.reason, (8, h - 45),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100, 200, 255), 1)

        return frame

    def close(self):
        self._landmarker.close()
        logger.info("FallDetector closed")

    # ── Private helpers ─────────────────────────────────────────────────────

    @staticmethod
    def _torso_angle_degrees(sx, sy, hx, hy) -> float:
        dx = hx - sx
        dy = hy - sy
        if abs(dx) < 1e-6 and abs(dy) < 1e-6:
            return 0.0
        return math.degrees(math.atan2(abs(dx), abs(dy)))

    @staticmethod
    def _hip_height_score(mid_hip_y: float) -> float:
        lo = HIP_HEIGHT_THRESHOLD - 0.10
        hi = HIP_HEIGHT_THRESHOLD + 0.10
        if mid_hip_y <= lo:
            return 0.0
        if mid_hip_y >= hi:
            return 1.0
        return (mid_hip_y - lo) / (hi - lo)

    @staticmethod
    def _torso_angle_score(angle_deg: float) -> float:
        lo = TORSO_ANGLE_THRESHOLD - 15.0
        hi = TORSO_ANGLE_THRESHOLD + 15.0
        if angle_deg <= lo:
            return 0.0
        if angle_deg >= hi:
            return 1.0
        return (angle_deg - lo) / (hi - lo)

    def _hip_velocity(self) -> float:
        if len(self._hip_y_history) < 3:
            return 0.0
        hist = list(self._hip_y_history)
        half    = len(hist) // 2
        old_avg = sum(hist[:half]) / half
        new_avg = sum(hist[half:]) / max(len(hist[half:]), 1)
        drop    = new_avg - old_avg
        frames  = len(hist) - half
        return max(drop / max(frames, 1), 0.0)

    @staticmethod
    def _velocity_score(velocity: float) -> float:
        lo = VELOCITY_THRESHOLD
        hi = VELOCITY_THRESHOLD * 2.0
        if velocity <= lo:
            return 0.0
        if velocity >= hi:
            return 1.0
        return (velocity - lo) / (hi - lo)
