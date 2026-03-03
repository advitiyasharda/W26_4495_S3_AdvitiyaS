"""
Flask API Routes for Door Face Panels Smart Security System
"""
import base64
import logging
from datetime import datetime

import cv2
import numpy as np
from flask import Blueprint, request, jsonify, current_app

logger = logging.getLogger(__name__)

api_bp = Blueprint("api", __name__)


def get_db():
    """Get database instance from Flask app"""
    return current_app.db


@api_bp.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "0.1.0",
    }), 200


@api_bp.route("/recognize", methods=["POST"])
def recognize_face():
    """
    Recognize a face from camera frame.

    Expected JSON:
    {
        "frame": "base64_encoded_image"  (optional: "data:image/jpeg;base64,...")
    }

    Returns:
    {
        "person_id": "string" | null,
        "name": "string",
        "confidence": 0.0-1.0,
        "access_granted": bool,
        "timestamp": "ISO format"
    }
    """
    try:
        data = request.get_json()
        if not data or "frame" not in data:
            return jsonify({"error": "Missing frame data"}), 400

        raw = data["frame"].strip()
        if raw.startswith("data:"):
            raw = raw.split(",", 1)[-1]
        try:
            img_bytes = base64.b64decode(raw)
        except Exception as e:
            return jsonify({"error": f"Invalid base64: {e}"}), 400

        arr = np.frombuffer(img_bytes, dtype=np.uint8)
        frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if frame is None:
            return jsonify({"error": "Could not decode image"}), 400

        engine = current_app.face_engine
        faces = engine.detect_faces(frame)
        if len(faces) == 0:
            return jsonify({
                "person_id": None,
                "name": "Unknown",
                "confidence": 0.0,
                "access_granted": False,
                "timestamp": str(datetime.now().isoformat()),
            }), 200

        x, y, w, h = (int(v) for v in faces[0])
        rec = engine.recognize_face(frame, (x, y, w, h))
        conf = rec.get("confidence", 0.0)
        access_granted = (
            rec.get("person_id") is not None
            and float(conf) >= engine.confidence_threshold
        )
        # Coerce to native Python types for JSON (avoid numpy float/int)
        result = {
            "person_id": rec.get("person_id"),
            "name": str(rec.get("name", "Unknown")),
            "confidence": float(conf),
            "access_granted": bool(access_granted),
            "timestamp": str(rec.get("timestamp", datetime.now().isoformat())),
        }
        logger.info("Face recognized: %s (confidence: %.2f)", result["name"], result["confidence"])
        db = get_db()
        if access_granted and result["person_id"]:
            # Map recognition result to an existing user if possible to avoid duplicates.
            # Prefer an existing DB user with the same name; otherwise, create a new user
            # with the engine's person_id as the primary key.
            db_user_id = result["person_id"]
            existing = db.get_user_by_name(result["name"])
            if existing:
                db_user_id = existing.get("user_id", db_user_id)
            else:
                db.add_user(db_user_id, result["name"], "resident")

            db.log_access(
                db_user_id,
                "entry",
                confidence=float(conf),
                status="success",
            )
            db.log_audit(
                "ACCESS_GRANTED",
                user_id=db_user_id,
                resource="door/main-entrance",
                result="success",
                details=f"confidence={conf:.2f}",
            )

            # --- Anomaly Detection ---
            # Score this access event through the Isolation Forest model.
            # If flagged as anomalous, log it to the anomalies table and
            # raise a threat alert so caregivers are notified on the dashboard.
            try:
                anomaly_event = {
                    "timestamp": result["timestamp"],
                    "person_id": db_user_id,
                    "access_type": "entry",
                    "confidence": float(conf),
                }
                anomaly_detector = current_app.anomaly_detector
                anomaly_result = anomaly_detector.predict_anomaly(anomaly_event)
                result["anomaly_score"] = anomaly_result.get("anomaly_score", 0.0)
                result["is_anomaly"] = anomaly_result.get("is_anomaly", False)

                if anomaly_result.get("is_anomaly"):
                    score = anomaly_result.get("anomaly_score", 0.0)
                    db.log_anomaly(
                        db_user_id,
                        "BEHAVIOURAL_ANOMALY",
                        score,
                        f"Isolation Forest flagged unusual access pattern (score={score:.3f})",
                    )
                    db.log_threat(
                        threat_type="Behavioural Anomaly Detected",
                        severity="MEDIUM",
                        user_id=db_user_id,
                        message=(
                            f"Unusual access pattern detected for {result['name']}. "
                            f"Anomaly score: {score:.3f}."
                        ),
                    )
                    logger.warning(
                        "Anomaly flagged for %s — score=%.3f", result["name"], score
                    )
            except Exception as e:
                logger.warning("Anomaly detection skipped: %s", e)
            # --- End Anomaly Detection ---

        else:
            # Face detected but not recognized or below threshold
            unknown_id = result["name"] or "Unknown"
            db.add_user("Unknown", "Unknown", "resident")  # ensure FK exists
            db.log_access("Unknown", "entry", confidence=float(conf), status="failed")
            db.log_audit(
                "ACCESS_DENIED",
                user_id=unknown_id,
                resource="door/main-entrance",
                result="failed",
                details=f"confidence={conf:.2f}",
            )
            db.log_threat(
                threat_type="Unrecognised Face Detected",
                severity="HIGH",
                user_id=unknown_id,
                message=(
                    f"Face detected at main entrance but no match in database. "
                    f"Confidence: {float(conf):.2f}."
                ),
            )
        return jsonify(result), 200

    except Exception as e:
        logger.exception("Error in face recognition")
        return jsonify({"error": str(e)}), 500

@api_bp.route('/log-access', methods=['POST'])
def log_access():
    """
    Log an access event.
    
    Expected JSON:
    {
        "person_id": "string",
        "access_type": "entry|exit",
        "confidence": 0.0-1.0,
        "timestamp": "ISO format"
    }
    """
    try:
        data = request.get_json()
        
        required_fields = ['person_id', 'access_type', 'confidence']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # TODO: Store in database
        logger.info(f"Access logged: {data['person_id']} - {data['access_type']}")
        
        return jsonify({
            'status': 'logged',
            'timestamp': datetime.now().isoformat()
        }), 201
        
    except Exception as e:
        logger.error(f"Error logging access: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/threats', methods=['GET'])
def get_threats():
    """
    Retrieve active threats and alerts.
    
    Query parameters:
    - person_id (optional): Filter by specific person
    - severity (optional): Filter by severity level
    """
    try:
        person_id = request.args.get('person_id')
        severity = request.args.get('severity')
        
        # Query database for threats
        threats = get_db().get_active_threats(severity=severity)
        # Normalize timestamps: ensure UTC with Z so frontend displays in local time
        for t in threats:
            ts = t.get("timestamp") or ""
            if isinstance(ts, str) and "Z" not in ts and "+" not in ts:
                t["timestamp"] = ts.replace(" ", "T", 1).strip() + "Z"
        # Filter by person_id (user_id in DB) if provided
        if person_id:
            threats = [t for t in threats if t.get("user_id") == person_id]
        
        return jsonify({
            'threats': threats,
            'total': len(threats),
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error retrieving threats: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api_bp.route("/users", methods=["GET"])
def get_users():
    """Return all registered users (for Unique People modal)."""
    try:
        users = get_db().get_users()
        return jsonify({"users": users}), 200
    except Exception as e:
        logger.error("Error retrieving users: %s", e)
        return jsonify({"error": str(e)}), 500


@api_bp.route("/users/<user_id>", methods=["DELETE"])
def delete_user(user_id):
    """Remove a registered user (DB + face engine)."""
    try:
        if not user_id:
            return jsonify({"error": "user_id required"}), 400
        db = get_db()
        if not db.delete_user(user_id):
            return jsonify({"error": "User not found or cannot be deleted"}), 404
        current_app.face_engine.remove_face(user_id)
        return jsonify({"status": "deleted", "user_id": user_id}), 200
    except Exception as e:
        logger.exception("Error deleting user")
        return jsonify({"error": str(e)}), 500


@api_bp.route('/logs', methods=['GET'])
def get_access_logs():
    """
    Retrieve access logs with optional filtering.
    
    Query parameters:
    - person_id (optional): Filter by specific person
    - limit (optional, default=100): Number of records to return
    - offset (optional, default=0): Pagination offset
    """
    try:
        person_id = request.args.get('person_id')
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        # Query database for access logs
        logs = get_db().get_access_logs(user_id=person_id)
        # Normalize timestamps: ensure UTC with Z so frontend displays in local time
        for log in logs:
            ts = log.get("timestamp") or ""
            if isinstance(ts, str) and "Z" not in ts and "+" not in ts:
                log["timestamp"] = ts.replace(" ", "T", 1).strip() + "Z"
        # Apply pagination
        paginated_logs = logs[offset:offset+limit]
        
        return jsonify({
            'logs': paginated_logs,
            'total': len(logs),
            'limit': limit,
            'offset': offset,
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error retrieving logs: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/stats', methods=['GET'])
def get_statistics():
    """Get system statistics and analytics"""
    try:
        db_stats = get_db().get_database_stats()
        
        stats = {
            'facial_recognition': {
                'total_persons': db_stats.get('total_users', 0),
                'recognition_accuracy': 0.92  # From our testing
            },
            'access_events': {
                'total_entries': db_stats.get('total_access_events', 0),
                'total_exits': 0,
                'today': 0
            },
            'threats': {
                'active_alerts': db_stats.get('active_threats', 0),
                'total_threats': 0
            },
            'system': {
                'uptime_hours': 0,
                'avg_inference_latency_ms': 75
            },
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(stats), 200
        
    except Exception as e:
        logger.error(f"Error retrieving statistics: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/compliance/audit', methods=['GET'])
def get_audit_log():
    """
    Retrieve compliance audit log (PIPEDA).
    All system actions logged for regulatory compliance.
    """
    try:
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        # Query audit log database; map user_id -> user for frontend
        raw = get_db().get_audit_logs(limit=limit, offset=offset)
        audit_log = []
        for row in raw:
            entry = {**row, "user": row.get("user_id")}
            ts = entry.get("timestamp") or ""
            if isinstance(ts, str) and "Z" not in ts and "+" not in ts:
                entry["timestamp"] = ts.replace(" ", "T", 1).strip() + "Z"
            audit_log.append(entry)
        return jsonify({
            "audit_log": audit_log,
            "count": len(audit_log),
            "timestamp": datetime.now().isoformat(),
        }), 200
        
    except Exception as e:
        logger.error(f"Error retrieving audit log: {str(e)}")
        return jsonify({'error': str(e)}), 500
