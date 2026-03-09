"""
Fall Detection API Routes (Phase 1 — Rules-Based)

Endpoints:
  POST /api/fall/detect    — analyse a single base64 frame for falls
  GET  /api/fall/status    — detector health / session stats
  GET  /api/fall/events    — list recent fall events stored in DB

No dashboard connection here.
Dashboard integration (showing CRITICAL alerts) is Reubin's responsibility.

The FallDetector instance lives on `current_app.fall_detector` so it keeps
its hip-velocity history across successive frames from a streaming client.
"""

import base64
import logging
from datetime import datetime

import cv2
import numpy as np
from flask import Blueprint, request, jsonify, current_app

logger = logging.getLogger(__name__)

fall_bp = Blueprint("fall", __name__)


# ── Helpers ──────────────────────────────────────────────────────────────────

def _decode_frame(b64_data: str) -> np.ndarray:
    """Decode a base64 image string into a BGR numpy array."""
    if b64_data.startswith("data:"):
        b64_data = b64_data.split(",", 1)[1]
    img_bytes = base64.b64decode(b64_data)
    arr = np.frombuffer(img_bytes, dtype=np.uint8)
    frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if frame is None:
        raise ValueError("Could not decode image from base64 data")
    return frame


def _get_db():
    return current_app.db


def _log_fall_to_db(result) -> None:
    """Write a fall event to the anomalies table (no dashboard side-effects)."""
    try:
        db = _get_db()
        db.log_anomaly(
            user_id="fall_detection",
            anomaly_type="fall_detected",
            anomaly_score=result.confidence,
            description=(
                f"Fall detected: {result.reason} | "
                f"hip_y={result.hip_height:.3f} "
                f"angle={result.torso_angle_deg:.1f}° "
                f"vel={result.hip_velocity:.4f}"
            ),
        )
    except Exception as e:
        logger.warning("Could not log fall to DB: %s", e)


# ── Routes ────────────────────────────────────────────────────────────────────

@fall_bp.route("/detect", methods=["POST"])
def detect_fall():
    """
    Analyse one camera frame for a fall.

    Request JSON:
        { "frame": "<base64-encoded JPEG/PNG>" }

    Response JSON (200):
        {
          "is_fall":           bool,
          "confidence":        float,   // 0.0 – 1.0
          "reason":            str,
          "hip_height":        float,
          "torso_angle_deg":   float,
          "hip_velocity":      float,
          "landmarks_visible": bool,
          "timestamp":         str      // ISO 8601
        }

    Error (400/500):
        { "error": "message" }
    """
    data = request.get_json(silent=True)
    if not data or "frame" not in data:
        return jsonify({"error": "Missing 'frame' field in JSON body"}), 400

    try:
        frame = _decode_frame(data["frame"])
    except Exception as e:
        return jsonify({"error": f"Invalid frame data: {e}"}), 400

    detector = current_app.fall_detector
    if detector is None:
        return jsonify({"error": "FallDetector not initialised on this server"}), 500

    try:
        result = detector.process_frame(frame)
    except Exception as e:
        logger.exception("FallDetector error on frame")
        return jsonify({"error": f"Detection failed: {e}"}), 500

    if result is None:
        return jsonify({"error": "Detector returned no result"}), 500

    # Persist fall events to the DB (async-safe, swallows errors internally)
    if result.is_fall:
        _log_fall_to_db(result)
        logger.warning(
            "FALL via API  conf=%.2f  hip_y=%.2f  angle=%.0f°  | %s",
            result.confidence, result.hip_height,
            result.torso_angle_deg, result.reason,
        )

    return jsonify({
        "is_fall":           result.is_fall,
        "confidence":        result.confidence,
        "reason":            result.reason,
        "hip_height":        result.hip_height,
        "torso_angle_deg":   result.torso_angle_deg,
        "hip_velocity":      result.hip_velocity,
        "landmarks_visible": result.landmarks_visible,
        "timestamp":         datetime.now().isoformat(timespec="seconds"),
    }), 200


@fall_bp.route("/status", methods=["GET"])
def fall_detector_status():
    """
    Returns the current state of the FallDetector instance.

    Response JSON:
        {
          "detector_ready":  bool,
          "fall_threshold":  float,
          "velocity_window": int,
          "cooldown_frames": int,   // frames left in cooldown (0 = ready)
          "history_length":  int    // how many hip-y samples are buffered
        }
    """
    detector = current_app.fall_detector
    if detector is None:
        return jsonify({"detector_ready": False}), 200

    return jsonify({
        "detector_ready":  True,
        "fall_threshold":  detector.fall_threshold,
        "velocity_window": detector.velocity_window,
        "cooldown_frames": detector._fall_cooldown_frames,
        "history_length":  len(detector._hip_y_history),
    }), 200


@fall_bp.route("/events", methods=["GET"])
def fall_events():
    """
    Return recent fall events stored in the DB.

    Query params:
        limit  (int, default 20)

    Response JSON:
        { "events": [ { anomaly_id, user_id, anomaly_score, description, timestamp }, … ] }
    """
    limit = request.args.get("limit", 20, type=int)

    try:
        db = _get_db()
        rows = db.get_anomalies(limit=limit)
        # Filter to only fall_detected events
        falls = [r for r in rows if r.get("anomaly_type") == "fall_detected"]
        return jsonify({"events": falls, "count": len(falls)}), 200
    except Exception as e:
        logger.exception("Error fetching fall events")
        return jsonify({"error": str(e)}), 500


@fall_bp.route("/reset", methods=["POST"])
def reset_detector():
    """
    Clear the FallDetector's velocity history and cooldown.
    Useful when changing scenes or re-positioning the camera.
    """
    detector = current_app.fall_detector
    if detector is None:
        return jsonify({"error": "FallDetector not initialised"}), 500

    detector._hip_y_history.clear()
    detector._fall_cooldown_frames = 0
    logger.info("FallDetector state reset via API")
    return jsonify({"status": "reset", "timestamp": datetime.now().isoformat()}), 200


@fall_bp.route("/log", methods=["POST"])
def log_fall():
    """
    Directly log a fall event that was already detected externally
    (e.g. by fall_detection_camera.py running its own FallDetector).

    This avoids the re-detection problem: the camera script has full
    velocity history; Flask's detector instance does not.

    Request JSON:
        {
          "confidence":      float,   // 0.0 – 1.0  (required)
          "reason":          str,     // optional
          "hip_height":      float,   // optional
          "torso_angle_deg": float,   // optional
          "hip_velocity":    float    // optional
        }

    Response JSON (200):
        { "status": "logged", "timestamp": str }
    """
    data = request.get_json(silent=True) or {}

    confidence = data.get("confidence")
    if confidence is None:
        return jsonify({"error": "Missing required field: confidence"}), 400

    try:
        confidence = float(confidence)
    except (TypeError, ValueError):
        return jsonify({"error": "confidence must be a number"}), 400

    reason        = data.get("reason", "Fall detected by camera script")
    hip_height    = data.get("hip_height", 0.0)
    torso_angle   = data.get("torso_angle_deg", 0.0)
    hip_velocity  = data.get("hip_velocity", 0.0)

    description = (
        f"Fall detected: {reason} | "
        f"hip_y={hip_height:.3f} "
        f"angle={torso_angle:.1f}° "
        f"vel={hip_velocity:.4f}"
    )

    try:
        db = _get_db()
        db.log_anomaly(
            user_id="fall_detection",
            anomaly_type="fall_detected",
            anomaly_score=confidence,
            description=description,
        )
        logger.warning(
            "Fall logged via /log  conf=%.2f  | %s", confidence, reason
        )
        return jsonify({
            "status":    "logged",
            "timestamp": datetime.now().isoformat(timespec="seconds"),
        }), 200
    except Exception as e:
        logger.exception("Error logging fall via /log")
        return jsonify({"error": str(e)}), 500

