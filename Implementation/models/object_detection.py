"""
Object Detection Module — Phase 3 (YOLO26)

Detects security-relevant objects at the door and classifies them into
five categories with associated threat levels for an elderly-care
smart-door system:

  Category          Default sev.   Door-security context
  ─────────────────────────────────────────────────────────────────────
  WEAPON            CRITICAL       knife, scissors, bat; custom model guns
  SECURITY_THREAT   HIGH           unusual / policy-flagged items at ingress
  PARCEL            INFO→MEDIUM    bags, deliveries — escalates when unattended
  MOBILITY_AID      INFO           wheelchair, walker, umbrella (elderly care)
  OPERATIONAL       LOW→MEDIUM     person, pet, bottles — routine but tracked

Accuracy pipeline (improvements over Phase 3 v1):
  • YOLO26l base model (Large — stronger than YOLO26m; heavier inference)
  • NMS-free end-to-end design (no separate post-processing step)
  • Padded weapon verification: reflected-border re-inference when any
    weapon-class hint is found — restores context for close-up weapons
  • CLAHE contrast-enhancement for backlit / shadowed doorways
  • Per-category confidence thresholds (lower for weapons, higher for noise)
  • Cross-model IoU-based NMS when weapon model is active
  • Exponential-moving-average confidence smoothing per class
  • Person-at-door awareness: bbox position → standing vs low-position alert
"""

from __future__ import annotations

import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np

logger = logging.getLogger(__name__)

# ── COCO class → category / severity mapping ─────────────────────────────────
# IDs match the 80-class COCO set used by YOLOv8.

_WEAPON_CLASSES: Dict[int, str] = {
    43: "knife",
    76: "scissors",
    34: "baseball_bat",
}

_PARCEL_CLASSES: Dict[int, str] = {
    24: "backpack",
    26: "handbag",
    28: "suitcase",
}

_SECURITY_THREAT_CLASSES: Dict[int, str] = {
    36: "skateboard",
    38: "tennis_racket",
}

_MOBILITY_AID_CLASSES: Dict[int, str] = {
    56: "chair",        # wheelchair proxy
    25: "umbrella",     # walking-aid / cane proxy, also commonly left at doors
}

_OPERATIONAL_CLASSES: Dict[int, str] = {
    0:  "person",
    39: "bottle",
    41: "cup",
    42: "fork",
    44: "spoon",
    45: "bowl",
    17: "cat",
    16: "dog",
    67: "cell_phone",
    73: "book",
    58: "potted_plant",
}

_CUSTOM_WEAPON_NAMES = {"gun", "pistol", "rifle", "handgun", "firearm", "weapon"}

_CATEGORY_SEVERITY: Dict[str, str] = {
    "WEAPON":          "CRITICAL",
    "SECURITY_THREAT": "HIGH",
    "PARCEL":          "INFO",
    "MOBILITY_AID":    "INFO",
    "OPERATIONAL":     "LOW",
}

_CATEGORY_CONFIDENCE: Dict[str, float] = {
    "WEAPON":          0.20,
    "SECURITY_THREAT": 0.35,
    "PARCEL":          0.35,
    "MOBILITY_AID":    0.40,
    "OPERATIONAL":     0.45,
}

_CONFIDENCE_EMA_ALPHA = 0.6

_ALL_WEAPON_IDS = set(_WEAPON_CLASSES.keys())

_WEAPON_VERIFY_FLOOR = 0.12
_WEAPON_PAD_RATIO = 0.25


@dataclass
class DetectionEvent:
    """A single object detection result."""
    object_class: str
    category: str
    severity: str
    confidence: float
    bbox: Tuple[float, float, float, float]  # x1, y1, x2, y2 (normalised 0–1)
    timestamp: float = field(default_factory=time.time)
    unattended_seconds: float = 0.0
    frame_count: int = 1


class ObjectDetector:
    """
    YOLO26-based object detector for elderly-care door security.

    v2 improvements over the original:
      – YOLO26l default (Large variant — higher accuracy than YOLO26m, more compute)
      – NMS-free end-to-end inference (built into YOLO26)
      – Padded weapon verification (reflected-border re-inference on weapon hints)
      – CLAHE preprocessing for mixed doorway lighting
      – Per-category confidence floors
      – Cross-model NMS to deduplicate weapon / COCO overlaps
      – EMA confidence smoothing for temporal stability
      – Person-at-door position awareness
    """

    def __init__(
        self,
        weapon_model_path: str = "models/weapon_detector.pt",
        base_model: str = "yolo26l.pt",
        confidence: float = 0.20,
        frame_threshold: int = 3,
        unattended_minutes: float = 2.0,
        imgsz: int = 640,
        enable_preprocessing: bool = True,
    ) -> None:
        self.confidence = confidence
        self.frame_threshold = frame_threshold
        self.unattended_seconds = unattended_minutes * 60.0
        self.imgsz = imgsz
        self.enable_preprocessing = enable_preprocessing

        self._model = None
        self._weapon_model = None
        self._model_ready = False
        self._weapon_model_ready = False

        self._frame_counts: Dict[str, int] = defaultdict(int)
        self._first_seen: Dict[str, float] = {}

        self._ema_confidence: Dict[str, float] = {}

        self._event_log: List[Dict] = []

        self._clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))

        self._load_models(weapon_model_path, base_model)

    # ── Model loading ─────────────────────────────────────────────────────────

    def _load_models(self, weapon_model_path: str, base_model: str) -> None:
        try:
            from ultralytics import YOLO  # type: ignore
        except ImportError:
            logger.error(
                "ultralytics not installed — run: pip install ultralytics"
            )
            return

        wp = Path(weapon_model_path)
        if wp.exists():
            try:
                self._weapon_model = YOLO(str(wp))
                self._weapon_model_ready = True
                logger.info("Custom weapon model loaded from %s", wp)
            except Exception as e:
                logger.warning("Could not load weapon model %s: %s", wp, e)

        try:
            self._model = YOLO(base_model)
            self._model_ready = True
            logger.info("Base YOLO model loaded: %s", base_model)
        except Exception as e:
            logger.error("Could not load base YOLO model %s: %s", base_model, e)

    # ── Preprocessing ─────────────────────────────────────────────────────────

    def _preprocess(self, frame: np.ndarray) -> np.ndarray:
        """Adaptive CLAHE: only enhance contrast on dark doorway frames."""
        if not self.enable_preprocessing:
            return frame

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        mean_brightness = float(gray.mean())

        if mean_brightness < 85:
            lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
            l_ch, a_ch, b_ch = cv2.split(lab)
            l_ch = self._clahe.apply(l_ch)
            enhanced = cv2.merge([l_ch, a_ch, b_ch])
            return cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)

        return frame

    # ── Cross-model NMS ───────────────────────────────────────────────────────

    @staticmethod
    def _iou(box_a: Tuple, box_b: Tuple) -> float:
        """Intersection-over-Union for two normalised (x1,y1,x2,y2) boxes."""
        x1 = max(box_a[0], box_b[0])
        y1 = max(box_a[1], box_b[1])
        x2 = min(box_a[2], box_b[2])
        y2 = min(box_a[3], box_b[3])
        inter = max(0.0, x2 - x1) * max(0.0, y2 - y1)
        area_a = (box_a[2] - box_a[0]) * (box_a[3] - box_a[1])
        area_b = (box_b[2] - box_b[0]) * (box_b[3] - box_b[1])
        union = area_a + area_b - inter
        return inter / union if union > 0 else 0.0

    def _cross_model_nms(
        self, detections: List[Tuple], iou_threshold: float = 0.45
    ) -> List[Tuple]:
        """Remove overlapping boxes across models, keeping higher confidence."""
        if len(detections) <= 1:
            return detections

        sorted_dets = sorted(detections, key=lambda d: d[1], reverse=True)
        keep: List[Tuple] = []

        for det in sorted_dets:
            suppressed = False
            for kept in keep:
                if self._iou(det[2], kept[2]) > iou_threshold:
                    suppressed = True
                    break
            if not suppressed:
                keep.append(det)

        return keep

    # ── Weapon verification via padded re-inference ─────────────────────────

    def _run_inference(
        self, frame: np.ndarray, conf: float, imgsz: int,
    ) -> List[Tuple[str, float, Tuple, int]]:
        """Run the base model and return raw (name, conf, bbox, cls_id) tuples."""
        detections: List[Tuple[str, float, Tuple, int]] = []
        try:
            results = self._model(
                frame, conf=conf, imgsz=imgsz, verbose=False,
            )
            for result in results:
                for box in result.boxes:
                    cls_id = int(box.cls[0])
                    c = float(box.conf[0])
                    xyxyn = tuple(float(v) for v in box.xyxyn[0])
                    cls_name = self._model.names.get(cls_id, str(cls_id))
                    detections.append((cls_name, c, xyxyn, cls_id))
        except Exception as e:
            logger.warning("Inference error (imgsz=%d): %s", imgsz, e)
        return detections

    def _weapon_verify(
        self, frame: np.ndarray, base_dets: List[Tuple],
    ) -> List[Tuple]:
        """
        When a weapon hint is found in the base pass (even at very low
        confidence), re-run on a padded copy of the frame.  YOLO models are
        trained on images where objects have surrounding context; padding with
        reflected borders restores that context for close-up weapon images and
        significantly boosts detection confidence.

        Only triggers when a potential weapon exists — normal non-weapon frames
        stay at the fast single-pass speed.
        """
        has_weapon_hint = any(
            d[3] in _ALL_WEAPON_IDS or d[0].lower() in _CUSTOM_WEAPON_NAMES
            for d in base_dets
        )
        if not has_weapon_hint:
            return base_dets

        h, w = frame.shape[:2]
        pad_y = int(h * _WEAPON_PAD_RATIO)
        pad_x = int(w * _WEAPON_PAD_RATIO)
        padded = cv2.copyMakeBorder(
            frame, pad_y, pad_y, pad_x, pad_x, cv2.BORDER_REFLECT_101,
        )

        padded_dets = self._run_inference(padded, conf=_WEAPON_VERIFY_FLOOR, imgsz=self.imgsz)

        ph, pw = padded.shape[:2]
        weapon_padded: Dict[int, Tuple] = {}
        for d in padded_dets:
            cid = d[3]
            is_weapon = cid in _ALL_WEAPON_IDS or d[0].lower() in _CUSTOM_WEAPON_NAMES
            if not is_weapon:
                continue
            ox1 = (d[2][0] * pw - pad_x) / w
            oy1 = (d[2][1] * ph - pad_y) / h
            ox2 = (d[2][2] * pw - pad_x) / w
            oy2 = (d[2][3] * ph - pad_y) / h
            remapped = (d[0], d[1], (ox1, oy1, ox2, oy2), cid)
            existing = weapon_padded.get(cid)
            if existing is None or d[1] > existing[1]:
                weapon_padded[cid] = remapped

        merged: List[Tuple] = []
        seen_weapon_ids: set = set()
        for d in base_dets:
            cid = d[3]
            is_weapon = cid in _ALL_WEAPON_IDS or d[0].lower() in _CUSTOM_WEAPON_NAMES
            if is_weapon and cid in weapon_padded and weapon_padded[cid][1] > d[1]:
                merged.append(weapon_padded[cid])
                seen_weapon_ids.add(cid)
            else:
                merged.append(d)
                if is_weapon:
                    seen_weapon_ids.add(cid)

        for cid, d in weapon_padded.items():
            if cid not in seen_weapon_ids:
                merged.append(d)

        return merged

    # ── Frame processing ──────────────────────────────────────────────────────

    def process_frame(self, frame: np.ndarray) -> List[DetectionEvent]:
        """
        Run detection on one BGR frame.

        Returns a (possibly empty) list of DetectionEvent objects that
        passed the frame-count filter.
        """
        if not self._model_ready:
            return []

        enhanced = self._preprocess(frame)

        raw_detections = self._run_inference(
            enhanced, conf=_WEAPON_VERIFY_FLOOR, imgsz=self.imgsz,
        )

        if self._weapon_model_ready:
            try:
                w_results = self._weapon_model(
                    enhanced,
                    conf=_WEAPON_VERIFY_FLOOR,
                    imgsz=self.imgsz,
                    verbose=False,
                )
                for result in w_results:
                    for box in result.boxes:
                        cls_id = int(box.cls[0])
                        conf = float(box.conf[0])
                        xyxyn = tuple(float(v) for v in box.xyxyn[0])
                        cls_name = self._weapon_model.names.get(cls_id, str(cls_id))
                        raw_detections.append((cls_name, conf, xyxyn, cls_id))
            except Exception as e:
                logger.warning("Weapon model inference error: %s", e)

        raw_detections = self._weapon_verify(enhanced, raw_detections)

        if self._weapon_model_ready and len(raw_detections) > 1:
            raw_detections = self._cross_model_nms(raw_detections)

        fired_events: List[DetectionEvent] = []
        detected_classes: set = set()

        for item in raw_detections:
            cls_name, conf, bbox, cls_id = item
            category, severity = self._classify(cls_name, cls_id, bbox)
            if category is None:
                continue

            min_conf = _CATEGORY_CONFIDENCE.get(category, self.confidence)
            if conf < min_conf:
                continue

            conf = self._smooth_confidence(cls_name, conf)

            detected_classes.add(cls_name)
            self._frame_counts[cls_name] += 1

            if cls_name not in self._first_seen:
                self._first_seen[cls_name] = time.time()

            unattended_sec = time.time() - self._first_seen[cls_name]

            if unattended_sec >= self.unattended_seconds:
                if category in ("PARCEL", "OPERATIONAL", "SECURITY_THREAT") and severity in ("INFO", "LOW"):
                    severity = "MEDIUM"

            if self._frame_counts[cls_name] >= self.frame_threshold:
                evt = DetectionEvent(
                    object_class=cls_name,
                    category=category,
                    severity=severity,
                    confidence=conf,
                    bbox=bbox,
                    unattended_seconds=unattended_sec,
                    frame_count=self._frame_counts[cls_name],
                )
                fired_events.append(evt)

        gone = set(self._frame_counts.keys()) - detected_classes
        for cls_name in gone:
            self._frame_counts[cls_name] = 0
            self._first_seen.pop(cls_name, None)
            self._ema_confidence.pop(cls_name, None)

        for evt in fired_events:
            self._append_log(evt)

        return fired_events

    # ── Confidence smoothing ──────────────────────────────────────────────────

    def _smooth_confidence(self, cls_name: str, raw_conf: float) -> float:
        """EMA smoothing to reduce single-frame confidence spikes / dips."""
        prev = self._ema_confidence.get(cls_name)
        if prev is None:
            smoothed = raw_conf
        else:
            smoothed = _CONFIDENCE_EMA_ALPHA * raw_conf + (1 - _CONFIDENCE_EMA_ALPHA) * prev
        self._ema_confidence[cls_name] = smoothed
        return round(smoothed, 4)

    # ── Classification ────────────────────────────────────────────────────────

    def _classify(
        self,
        cls_name: str,
        cls_id: int,
        bbox: Tuple[float, ...] = (),
    ) -> Tuple[Optional[str], Optional[str]]:
        """Return (category, severity) or (None, None) if not relevant."""
        name_lower = cls_name.lower()

        if name_lower in _CUSTOM_WEAPON_NAMES:
            return "WEAPON", "CRITICAL"

        if cls_id in _WEAPON_CLASSES:
            if cls_id == 34:
                return "WEAPON", "HIGH"
            return "WEAPON", "CRITICAL"

        if cls_id in _PARCEL_CLASSES:
            return "PARCEL", _CATEGORY_SEVERITY["PARCEL"]

        if cls_id in _SECURITY_THREAT_CLASSES:
            return "SECURITY_THREAT", _CATEGORY_SEVERITY["SECURITY_THREAT"]

        if cls_id in _MOBILITY_AID_CLASSES:
            return "MOBILITY_AID", _CATEGORY_SEVERITY["MOBILITY_AID"]

        if cls_id in _OPERATIONAL_CLASSES:
            severity = _CATEGORY_SEVERITY["OPERATIONAL"]

            if cls_id == 0 and len(bbox) == 4:
                _, y1, _, y2 = bbox
                box_height = y2 - y1
                box_bottom = y2
                if box_height < 0.35 and box_bottom > 0.7:
                    severity = "MEDIUM"

            if cls_id in (16, 17):
                severity = "INFO"

            return "OPERATIONAL", severity

        return None, None

    # ── Event log helpers ─────────────────────────────────────────────────────

    def _append_log(self, evt: DetectionEvent) -> None:
        import datetime as _dt
        record = {
            "object_class": evt.object_class,
            "category": evt.category,
            "severity": evt.severity,
            "confidence": round(evt.confidence, 3),
            "unattended_seconds": round(evt.unattended_seconds, 1),
            "frame_count": evt.frame_count,
            "timestamp": _dt.datetime.now(_dt.timezone.utc).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            ),
        }
        self._event_log.append(record)
        if len(self._event_log) > 500:
            self._event_log = self._event_log[-500:]

    def get_recent_events(self, limit: int = 50) -> List[Dict]:
        """Return the most recent detection events (newest first)."""
        return list(reversed(self._event_log[-limit:]))

    def get_category_counts(self) -> Dict[str, int]:
        """Return total detection counts per category from the rolling log."""
        counts: Dict[str, int] = defaultdict(int)
        for rec in self._event_log:
            counts[rec["category"]] += 1
        return dict(counts)

    @property
    def is_ready(self) -> bool:
        return self._model_ready

    @property
    def weapon_model_ready(self) -> bool:
        return self._weapon_model_ready
