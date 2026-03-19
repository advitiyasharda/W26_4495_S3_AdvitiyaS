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
import json
from datetime import datetime, timedelta
from pathlib import Path

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


def _build_fall_description(reason: str, confidence: float, hip_height: float,
                            torso_angle: float, hip_velocity: float,
                            source: str) -> str:
    return (
        f"Fall detected: {reason} | "
        f"source={source} "
        f"confidence={confidence:.2f} "
        f"hip_y={hip_height:.3f} "
        f"angle={torso_angle:.1f}deg "
        f"vel={hip_velocity:.4f}"
    )


def _log_repeated_falls_if_needed(db) -> None:
    """Raise repeated-falls threat if threshold met, with basic dedupe window."""
    try:
        detector = current_app.threat_detector
        alert = detector.check_repeated_falls(db)
        if not alert:
            return

        existing = db.get_active_threats(severity=alert["severity"])
        cutoff = datetime.utcnow() - timedelta(hours=1)
        for row in existing or []:
            if row.get("threat_type") != alert["threat_type"]:
                continue
            ts_raw = str(row.get("timestamp", ""))
            try:
                ts = datetime.fromisoformat(ts_raw.replace("Z", ""))
            except Exception:
                continue
            if ts >= cutoff:
                return

        db.log_threat(
            threat_type=alert["threat_type"],
            severity=alert["severity"],
            user_id=alert.get("person_id", "fall_detection"),
            message=alert.get("message", "Repeated falls detected"),
        )
    except Exception as e:
        logger.warning("Could not evaluate repeated-falls threat: %s", e)


def _log_fall_to_db(result, source: str = "backend_rules") -> None:
    """
    Write a fall event to the anomalies table and escalate to the
    threats table as a CRITICAL security alert so it surfaces on the
    main alerts dashboard alongside other threat rules.
    """
    description = _build_fall_description(
        result.reason,
        result.confidence,
        result.hip_height,
        result.torso_angle_deg,
        result.hip_velocity,
        source,
    )
    try:
        db = _get_db()
        db.log_anomaly(
            user_id="fall_detection",
            anomaly_type="fall_detected",
            anomaly_score=result.confidence,
            description=description,
        )
        _log_repeated_falls_if_needed(db)
    except Exception as e:
        logger.warning("Could not log fall anomaly to DB: %s", e)

    try:
        db = _get_db()
        db.log_threat(
            threat_type="FALL_DETECTED",
            severity="CRITICAL",
            user_id="fall_detection",
            message=(
                f"Fall detected via {source} (confidence {result.confidence:.0%}): "
                f"{result.reason}"
            ),
        )
        logger.warning("Fall escalated to CRITICAL threat — conf=%.2f", result.confidence)
    except Exception as e:
        logger.warning("Could not escalate fall to threats table: %s", e)


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
        _log_fall_to_db(result, source=f"api_{getattr(current_app, 'fall_detector_mode', 'rules')}")
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
    artifacts = getattr(current_app, "fall_model_artifacts", {})
    model_info = getattr(current_app, "fall_model_info", {})
    model_info_path = Path("models/model_info.json")
    if not model_info and model_info_path.exists():
        try:
            model_info = json.loads(model_info_path.read_text())
        except Exception:
            model_info = {}

    if detector is None:
        return jsonify({
            "detector_ready": False,
            "active_mode": getattr(current_app, "fall_detector_mode", "unavailable"),
            "requested_mode": getattr(current_app, "fall_detector_mode_requested", "rules"),
            "artifacts": artifacts,
            "model_info": model_info,
        }), 200

    is_rules = hasattr(detector, "_hip_y_history")
    cooldown_frames = (
        detector._fall_cooldown_frames if hasattr(detector, "_fall_cooldown_frames")
        else getattr(detector, "_cooldown", 0)
    )
    history_length = (
        len(detector._hip_y_history) if hasattr(detector, "_hip_y_history")
        else len(getattr(detector, "_buffer", []))
    )

    return jsonify({
        "detector_ready":  True,
        "active_mode": getattr(current_app, "fall_detector_mode", "rules"),
        "requested_mode": getattr(current_app, "fall_detector_mode_requested", "rules"),
        "fall_threshold": getattr(detector, "fall_threshold", getattr(detector, "threshold", 0.55)),
        "velocity_window": getattr(detector, "velocity_window", 0),
        "sequence_length": getattr(detector, "sequence_len", 0),
        "cooldown_frames": cooldown_frames,
        "history_length": history_length,
        "artifacts": artifacts,
        "model_info": model_info,
        "implementation": "rules" if is_rules else "lstm",
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
        # Normalize timestamps to UTC ISO with Z so frontend renders local time consistently
        for item in falls:
            ts = item.get("timestamp") or ""
            if isinstance(ts, str) and "Z" not in ts and "+" not in ts:
                item["timestamp"] = ts.replace(" ", "T", 1).strip() + "Z"
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

    if hasattr(detector, "_hip_y_history"):
        detector._hip_y_history.clear()
    if hasattr(detector, "_fall_cooldown_frames"):
        detector._fall_cooldown_frames = 0
    if hasattr(detector, "_buffer"):
        detector._buffer.clear()
    if hasattr(detector, "_cooldown"):
        detector._cooldown = 0
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
          "hip_velocity":    float,   // optional
          "detector_source": "rules|lstm|external" // optional
        }

    Response JSON (200):
        { "status": "logged|logged_warning", "timestamp": str }
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
    detector_source = str(data.get("detector_source", "camera_external")).strip().lower()

    reason_lower = str(reason).lower()
    is_visibility_warning = "body not fully visible" in reason_lower

    description = _build_fall_description(
        reason,
        confidence,
        float(hip_height),
        float(torso_angle),
        float(hip_velocity),
        detector_source,
    )

    try:
        db = _get_db()
        if is_visibility_warning:
            db.log_threat(
                threat_type="CAMERA_VISIBILITY_WARNING",
                severity="LOW",
                user_id="fall_detection",
                message=(
                    f"Camera visibility warning via {detector_source}: {reason}"
                ),
            )
            logger.info(
                "Visibility warning via /log  source=%s  | %s",
                detector_source, reason
            )
            return jsonify({
                "status": "logged_warning",
                "detector_source": detector_source,
                "timestamp": datetime.now().isoformat(timespec="seconds"),
            }), 200

        db.log_anomaly(
            user_id="fall_detection",
            anomaly_type="fall_detected",
            anomaly_score=confidence,
            description=description,
        )
        db.log_threat(
            threat_type="FALL_DETECTED",
            severity="CRITICAL",
            user_id="fall_detection",
            message=(
                f"Fall detected via {detector_source} "
                f"(confidence {confidence:.0%}): {reason}"
            ),
        )
        _log_repeated_falls_if_needed(db)
        logger.warning(
            "Fall logged via /log  conf=%.2f  source=%s  | %s",
            confidence, detector_source, reason
        )
        return jsonify({
            "status":    "logged",
            "detector_source": detector_source,
            "timestamp": datetime.now().isoformat(timespec="seconds"),
        }), 200
    except Exception as e:
        logger.exception("Error logging fall via /log")
        return jsonify({"error": str(e)}), 500

