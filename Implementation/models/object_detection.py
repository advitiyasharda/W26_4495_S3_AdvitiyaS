"""
Object Detection Module — Phase 3 (YOLOv8)

Detects security-relevant objects at the door and classifies them into
four categories with associated threat levels:

  Category          Base level  Unattended (>2 min)   Examples
  ─────────────────────────────────────────────────────────────────────
  WEAPON            CRITICAL    CRITICAL              knife, scissors, gun
  SECURITY_THREAT   HIGH        CRITICAL              suitcase, baseball bat
  PARCEL            INFO        MEDIUM                backpack, handbag left at door
  MOBILITY_AID      INFO        INFO                  wheelchair (chair proxy)

Design decisions
─────────────────
- Person is intentionally NOT classified — face recognition handles persons.
- Only objects realistic at a door entry are included; household items
  (TV, fridge, couch, sports ball, clock…) are ignored to avoid noise.
- Parcel starts as INFO: a delivery for the resident is not a threat.
  After UNATTENDED_MINUTES it escalates to MEDIUM (still waiting).
- Suitcase starts as HIGH: unattended luggage is inherently suspicious.
  After UNATTENDED_MINUTES it escalates to CRITICAL.

Frame-filtering:
  An object must appear in FRAME_THRESHOLD consecutive frames before an
  alert fires — prevents single-frame false positives.
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

# ── COCO class → category mapping ────────────────────────────────────────────
# Only objects that are realistic at a door entry point are listed.
# Person (class 0) is intentionally excluded — face recognition handles persons.

# WEAPON (CRITICAL): actual weapons visible at a door
_WEAPON_CLASSES: Dict[int, str] = {
    43: "knife",        # COCO 43
    76: "scissors",     # COCO 76 — usable as weapon
    34: "baseball_bat", # COCO 34 — blunt weapon
}

# SECURITY_THREAT (HIGH → CRITICAL when unattended):
# Luggage/large bags are suspicious at a care facility entrance.
# An unattended suitcase is a serious concern.
_SECURITY_THREAT_CLASSES: Dict[int, str] = {
    28: "suitcase",     # COCO 28 — unattended luggage
}

# PARCEL (INFO → MEDIUM when unattended):
# A package or bag left at the door for the resident is a delivery, not a threat.
# Severity only escalates if it sits there unattended for too long.
_PARCEL_CLASSES: Dict[int, str] = {
    24: "backpack",     # COCO 24 — delivery pack / courier bag
    26: "handbag",      # COCO 26 — bag left at door
}

# MOBILITY_AID (INFO): accessibility objects near the entrance
_MOBILITY_AID_CLASSES: Dict[int, str] = {
    56: "chair",        # COCO 56 — wheelchair proxy
}

# Custom class names output by the fine-tuned weapon model
_CUSTOM_WEAPON_NAMES = {"gun", "pistol", "rifle", "handgun", "firearm", "weapon"}

# Base severity for each category
_CATEGORY_SEVERITY = {
    "WEAPON":          "CRITICAL",
    "SECURITY_THREAT": "HIGH",
    "PARCEL":          "INFO",
    "MOBILITY_AID":    "INFO",
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

    def detect_all(self, frame: np.ndarray) -> List[dict]:
        """
        Return every YOLO detection on this frame (no category filter, no frame-
        threshold filter).  Used by the camera debug view so the operator can see
        what the model is seeing even for objects not in our tracked set.
        """
        if not self._model_ready:
            return []
        results = []
        try:
            for r in self._model(frame, conf=self.confidence, verbose=False):
                for box in r.boxes:
                    cls_id  = int(box.cls[0])
                    cls_name = self._model.names.get(cls_id, str(cls_id))
                    cat, sev = self._classify(cls_name, cls_id)
                    results.append({
                        "object_class": cls_name,
                        "confidence":   float(box.conf[0]),
                        "bbox":         tuple(float(v) for v in box.xyxyn[0]),
                        "category":     cat,   # None if not in our tracked set
                        "severity":     sev,
                    })
        except Exception as e:
            logger.warning("detect_all error: %s", e)
        return results

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

            # Unattended escalation rules:
            #   PARCEL   INFO  → MEDIUM  after timer (delivery still sitting there)
            #   SECURITY HIGH  → CRITICAL after timer (unattended suitcase = serious)
            if unattended_sec >= self.unattended_seconds:
                if category == "PARCEL" and severity == "INFO":
                    severity = "MEDIUM"
                elif category == "SECURITY_THREAT" and severity == "HIGH":
                    severity = "CRITICAL"

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
        """
        Return (category, severity) or (None, None) if not security-relevant.

        Lookup order matters — weapons are checked first so a baseball bat
        is always WEAPON rather than falling through to another category.
        Parcels are checked after security threats so suitcase (SECURITY_THREAT)
        is never accidentally downgraded to PARCEL (INFO).
        """
        name_lower = cls_name.lower()

        # 1. Custom fine-tuned weapon model outputs (e.g. gun, pistol)
        if name_lower in _CUSTOM_WEAPON_NAMES:
            return "WEAPON", "CRITICAL"

        # 2. COCO weapon classes (knife, scissors, baseball bat)
        if cls_id in _WEAPON_CLASSES:
            return "WEAPON", "CRITICAL"

        # 3. Security threats — suspicious unattended items (suitcase)
        if cls_id in _SECURITY_THREAT_CLASSES:
            return "SECURITY_THREAT", _CATEGORY_SEVERITY["SECURITY_THREAT"]

        # 4. Parcels — deliveries for the resident, NOT a threat by default
        if cls_id in _PARCEL_CLASSES:
            return "PARCEL", _CATEGORY_SEVERITY["PARCEL"]

        # 5. Mobility aids near the entrance
        if cls_id in _MOBILITY_AID_CLASSES:
            return "MOBILITY_AID", _CATEGORY_SEVERITY["MOBILITY_AID"]

        # Everything else (person, bottle, cup, TV, etc.) is ignored
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
