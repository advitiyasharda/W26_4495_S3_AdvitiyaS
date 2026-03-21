"""
Object Detection API Routes — Phase 3 (YOLOv8)

Endpoints registered under the prefix /api/objects:
  POST /api/objects/detect   — analyse a base64 camera frame for objects
  GET  /api/objects/status   — detector health & model info
  GET  /api/objects/events   — recent detection events (from DB + in-memory log)

The ObjectDetector instance is stored on current_app.object_detector so it
retains frame-count / unattended-item state across successive API calls from
a streaming client.

If the model is not yet available (first run, missing weights) the endpoints
return graceful error responses rather than crashing the app.
"""

import base64
import logging
from datetime import datetime, timezone

import cv2
import numpy as np
from flask import Blueprint, current_app, jsonify, request

logger = logging.getLogger(__name__)

objects_bp = Blueprint("objects", __name__)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _decode_frame(b64_data: str) -> np.ndarray:
    """Decode a base64 image string (with or without data-URI prefix) to BGR."""
    if b64_data.startswith("data:"):
        b64_data = b64_data.split(",", 1)[1]
    img_bytes = base64.b64decode(b64_data)
    arr = np.frombuffer(img_bytes, dtype=np.uint8)
    frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if frame is None:
        raise ValueError("Could not decode image from base64 data")
    return frame


def _get_detector():
    return getattr(current_app, "object_detector", None)


def _get_db():
    return current_app.db


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ── Routes ────────────────────────────────────────────────────────────────────

@objects_bp.route("/detect", methods=["POST"])
def detect_objects():
    """
    Analyse one camera frame for security-relevant objects.

    Request JSON:
        { "frame": "<base64-encoded JPEG/PNG>" }

    Response JSON (200):
        {
          "detections": [
            {
              "object_class":       str,
              "category":           str,   // WEAPON | SECURITY_THREAT | PARCEL | MOBILITY_AID | OPERATIONAL
              "severity":           str,   // CRITICAL | HIGH | MEDIUM | INFO | LOW
              "confidence":         float,
              "unattended_seconds": float,
              "frame_count":        int
            },
            ...
          ],
          "count":     int,
          "timestamp": str   // ISO 8601 UTC
        }

    Error (400 / 503):
        { "error": "message" }
    """
    detector = _get_detector()
    if detector is None or not detector.is_ready:
        return jsonify({
            "error": "ObjectDetector not ready — model weights may be missing",
            "hint": "Run: pip install ultralytics && python main.py",
        }), 503

    data = request.get_json(silent=True)
    if not data or "frame" not in data:
        return jsonify({"error": "Missing 'frame' field in JSON body"}), 400

    try:
        frame = _decode_frame(data["frame"])
    except Exception as e:
        return jsonify({"error": f"Invalid frame data: {e}"}), 400

    try:
        events = detector.process_frame(frame)
    except Exception as e:
        logger.exception("ObjectDetector error on frame")
        return jsonify({"error": f"Detection failed: {e}"}), 500

    # Persist high-severity detections to the threats table
    db = _get_db()
    for evt in events:
        if evt.severity in ("CRITICAL", "HIGH"):
            _log_object_threat(db, evt)
        elif evt.severity == "MEDIUM" and evt.unattended_seconds > 0:
            _log_object_threat(db, evt)

    detections = [
        {
            "object_class":       evt.object_class,
            "category":           evt.category,
            "severity":           evt.severity,
            "confidence":         round(evt.confidence, 3),
            "unattended_seconds": round(evt.unattended_seconds, 1),
            "frame_count":        evt.frame_count,
        }
        for evt in events
    ]

    return jsonify({
        "detections": detections,
        "count":      len(detections),
        "timestamp":  _now_iso(),
    }), 200


@objects_bp.route("/status", methods=["GET"])
def object_detector_status():
    """
    Returns the current health of the ObjectDetector.

    Response JSON (200):
        {
          "detector_ready":      bool,
          "weapon_model_ready":  bool,
          "confidence":          float,
          "frame_threshold":     int,
          "unattended_minutes":  float,
          "events_logged":       int
        }
    """
    detector = _get_detector()

    if detector is None:
        return jsonify({
            "detector_ready":     False,
            "weapon_model_ready": False,
            "message": "ObjectDetector was not initialised (ultralytics may be missing)",
        }), 200

    return jsonify({
        "detector_ready":     detector.is_ready,
        "weapon_model_ready": detector.weapon_model_ready,
        "confidence":         detector.confidence,
        "frame_threshold":    detector.frame_threshold,
        "unattended_minutes": round(detector.unattended_seconds / 60.0, 2),
        "events_logged":      len(detector._event_log),
        "category_counts":    detector.get_category_counts(),
    }), 200


@objects_bp.route("/events", methods=["GET"])
def object_events():
    """
    Return recent object detection events.

    Query params:
        limit     (int, default 50)
        category  (str, optional) — filter by category name
        severity  (str, optional) — filter by severity level

    Response JSON (200):
        {
          "events": [ { object_class, category, severity, confidence,
                        unattended_seconds, frame_count, timestamp }, … ],
          "count": int
        }
    """
    limit = request.args.get("limit", 50, type=int)
    category_filter = request.args.get("category", "").strip().upper() or None
    severity_filter = request.args.get("severity", "").strip().upper() or None

    detector = _get_detector()
    if detector is None:
        return jsonify({"events": [], "count": 0}), 200

    events = detector.get_recent_events(limit=limit * 3)  # over-fetch then filter

    if category_filter:
        events = [e for e in events if e.get("category") == category_filter]
    if severity_filter:
        events = [e for e in events if e.get("severity") == severity_filter]

    events = events[:limit]

    return jsonify({"events": events, "count": len(events)}), 200


# ── Internal helpers ──────────────────────────────────────────────────────────

def _log_object_threat(db, evt) -> None:
    """Write a DetectionEvent to the threats table so it surfaces on the alerts dashboard."""
    try:
        if evt.unattended_seconds > 0:
            unattended_note = f" (unattended {evt.unattended_seconds:.0f}s)"
        else:
            unattended_note = ""

        db.log_threat(
            threat_type=f"OBJECT_{evt.category}",
            severity=evt.severity,
            user_id="object_detection",
            message=(
                f"{evt.object_class.replace('_', ' ').title()} detected at door"
                f"{unattended_note} — confidence {evt.confidence:.0%}"
            ),
        )
    except Exception as e:
        logger.warning("Could not log object threat to DB: %s", e)
