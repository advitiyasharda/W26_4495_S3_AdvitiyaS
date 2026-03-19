"""
Object Detection Module — Phase 3 (YOLOv8)

Detects security-relevant objects at the door and classifies them into
five categories with associated threat levels:

  Category          Threat level   Examples
  ─────────────────────────────────────────────────────────────────────
  WEAPON            CRITICAL       knife, scissors (COCO); gun (custom)
  SECURITY_THREAT   HIGH/MEDIUM    backpack (odd-hour), sports equipment
  PARCEL            INFO           handbag, suitcase, backpack (daytime)
  MOBILITY_AID      INFO           wheelchair proxy objects
  OPERATIONAL       LOW            bottle, cup, chair near entrance

Frame-filtering:
  An object must be detected in FRAME_THRESHOLD consecutive frames before
  an alert fires — this prevents one-frame false positives.

Unattended-item timer:
  If a PARCEL or SECURITY_THREAT object remains in frame for longer than
  UNATTENDED_MINUTES the severity is escalated to MEDIUM.
"""

from __future__ import annotations

import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)

# ── COCO class → category / severity mapping ─────────────────────────────────
# Numbers are COCO class IDs used by YOLOv8n.

# Classes that are always weapons regardless of context
_WEAPON_CLASSES: Dict[int, str] = {
    43: "knife",       # COCO 43 — knife
    76: "scissors",    # COCO 76 — scissors (can be used as weapon)
}

# Classes that are potential security threats (context-dependent)
_SECURITY_THREAT_CLASSES: Dict[int, str] = {
    24: "backpack",    # COCO 24 — suspicious if at odd hours
    26: "handbag",     # COCO 26 — left unattended
    28: "suitcase",    # COCO 28 — unauthorized moving attempt
    33: "sports_ball", # COCO 33 — proxy for thrown object
    34: "baseball_bat",# COCO 34 — blunt weapon
    35: "baseball_glove",
    36: "skateboard",
    38: "tennis_racket",
    74: "clock",       # standalone — unusual
}

# Classes that indicate a delivery / parcel
_PARCEL_CLASSES: Dict[int, str] = {
    26: "handbag",     # also parcel if left at door
    28: "suitcase",    # luggage / overnight visitor
    24: "backpack",    # delivery pack
}

# Classes that indicate mobility / medical aid
_MOBILITY_AID_CLASSES: Dict[int, str] = {
    56: "chair",       # proxy for wheelchair
    57: "couch",       # gurney-like
    62: "tv",          # medical monitor (loose proxy)
    72: "refrigerator",# O2 / medical equipment (loose)
}

# Operational / facility-management hazards
_OPERATIONAL_CLASSES: Dict[int, str] = {
    39: "bottle",      # spilled liquid / slip hazard
    41: "cup",
    42: "fork",
    44: "spoon",
    45: "bowl",
    17: "cat",         # escaped pet
    16: "dog",
    0:  "person",      # fallen person near door (complement to fall detection)
}

# Custom class names added by the fine-tuned weapon model
_CUSTOM_WEAPON_NAMES = {"gun", "pistol", "rifle", "handgun", "firearm", "weapon"}

# Severity for each category
_CATEGORY_SEVERITY = {
    "WEAPON":          "CRITICAL",
    "SECURITY_THREAT": "HIGH",
    "PARCEL":          "INFO",
    "MOBILITY_AID":    "INFO",
    "OPERATIONAL":     "LOW",
}


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
    YOLOv8-based object detector for door security.

    Usage
    -----
    detector = ObjectDetector(
        weapon_model_path="models/weapon_detector.pt",   # optional
        base_model="yolov8n.pt",
        confidence=0.45,
        frame_threshold=3,
        unattended_minutes=2.0,
    )
    events = detector.process_frame(bgr_frame)
    """

    def __init__(
        self,
        weapon_model_path: str = "models/weapon_detector.pt",
        base_model: str = "yolov8n.pt",
        confidence: float = 0.45,
        frame_threshold: int = 3,
        unattended_minutes: float = 2.0,
    ) -> None:
        self.confidence = confidence
        self.frame_threshold = frame_threshold
        self.unattended_seconds = unattended_minutes * 60.0

        self._model = None          # base YOLOv8 model (COCO)
        self._weapon_model = None   # optional fine-tuned weapon model
        self._model_ready = False
        self._weapon_model_ready = False

        # Per-class consecutive-frame counters for false-positive filtering
        self._frame_counts: Dict[str, int] = defaultdict(int)

        # Unattended-item tracking: class_name → first-seen timestamp
        self._first_seen: Dict[str, float] = {}

        # Rolling event log (capped at 500 events)
        self._event_log: List[Dict] = []

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

        # 1. Try to load the fine-tuned weapon model
        wp = Path(weapon_model_path)
        if wp.exists():
            try:
                self._weapon_model = YOLO(str(wp))
                self._weapon_model_ready = True
                logger.info("Custom weapon model loaded from %s", wp)
            except Exception as e:
                logger.warning("Could not load weapon model %s: %s", wp, e)

        # 2. Load the base COCO model (always)
        try:
            self._model = YOLO(base_model)
            self._model_ready = True
            logger.info("Base YOLOv8 model loaded: %s", base_model)
        except Exception as e:
            logger.error("Could not load base YOLO model %s: %s", base_model, e)

    # ── Frame processing ──────────────────────────────────────────────────────

    def process_frame(self, frame: np.ndarray) -> List[DetectionEvent]:
        """
        Run detection on one BGR frame.

        Returns a (possibly empty) list of DetectionEvent objects that
        passed the frame-count filter.  Call this for every camera frame.
        """
        if not self._model_ready:
            return []

        raw_detections: List[Tuple[str, float, Tuple]] = []

        # Run base COCO model
        try:
            results = self._model(frame, conf=self.confidence, verbose=False)
            for result in results:
                for box in result.boxes:
                    cls_id = int(box.cls[0])
                    conf = float(box.conf[0])
                    xyxyn = tuple(float(v) for v in box.xyxyn[0])
                    cls_name = self._model.names.get(cls_id, str(cls_id))
                    raw_detections.append((cls_name, conf, xyxyn, cls_id))
        except Exception as e:
            logger.warning("Base model inference error: %s", e)

        # Run custom weapon model if available
        if self._weapon_model_ready:
            try:
                w_results = self._weapon_model(
                    frame, conf=self.confidence, verbose=False
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

        # Classify and filter
        fired_events: List[DetectionEvent] = []
        detected_classes = set()

        for item in raw_detections:
            cls_name, conf, bbox, cls_id = item
            category, severity = self._classify(cls_name, cls_id)
            if category is None:
                continue

            detected_classes.add(cls_name)
            self._frame_counts[cls_name] += 1

            # Track first-seen for unattended-item detection
            if cls_name not in self._first_seen:
                self._first_seen[cls_name] = time.time()

            unattended_sec = time.time() - self._first_seen[cls_name]

            # Escalate unattended parcel/threat after timer
            if unattended_sec >= self.unattended_seconds:
                if category in ("PARCEL", "OPERATIONAL") and severity in ("INFO", "LOW"):
                    severity = "MEDIUM"

            # Only fire once the object has been seen for enough consecutive frames
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

        # Reset counters for classes not seen this frame
        gone = set(self._frame_counts.keys()) - detected_classes
        for cls_name in gone:
            self._frame_counts[cls_name] = 0
            self._first_seen.pop(cls_name, None)

        # Append to rolling log
        for evt in fired_events:
            self._append_log(evt)

        return fired_events

    # ── Classification ────────────────────────────────────────────────────────

    def _classify(
        self, cls_name: str, cls_id: int
    ) -> Tuple[Optional[str], Optional[str]]:
        """Return (category, severity) or (None, None) if not security-relevant."""
        name_lower = cls_name.lower()

        # Custom weapon model outputs
        if name_lower in _CUSTOM_WEAPON_NAMES:
            return "WEAPON", "CRITICAL"

        # COCO weapons
        if cls_id in _WEAPON_CLASSES:
            return "WEAPON", "CRITICAL"

        # Security threats (backpack / bat / etc.)
        if cls_id in _SECURITY_THREAT_CLASSES:
            return "SECURITY_THREAT", _CATEGORY_SEVERITY["SECURITY_THREAT"]

        # Parcels / deliveries — subset of security-threat classes
        if cls_id in _PARCEL_CLASSES:
            return "PARCEL", _CATEGORY_SEVERITY["PARCEL"]

        # Mobility aids
        if cls_id in _MOBILITY_AID_CLASSES:
            return "MOBILITY_AID", _CATEGORY_SEVERITY["MOBILITY_AID"]

        # Operational hazards
        if cls_id in _OPERATIONAL_CLASSES:
            return "OPERATIONAL", _CATEGORY_SEVERITY["OPERATIONAL"]

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
