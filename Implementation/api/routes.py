"""
Flask API Routes for Door Face Panels Smart Security System
"""
import base64
import logging
from datetime import datetime, timezone

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


@api_bp.route("/recognition/status", methods=["GET"])
def recognition_status():
    """
    Return the current state of the facial recognition engine.

    Response JSON:
        {
          "engine_mode":         "dlib" | "opencv",
          "dlib_version":        str | null,
          "registered_persons":  int,
          "total_encodings":     int,
          "current_threshold":   float,
          "confidence_threshold": float,
          "timestamp":           str
        }
    """
    try:
        from api.facial_recognition import USE_FACE_RECOGNITION_LIB, DISTANCE_MATCH_THRESHOLD

        engine = current_app.face_engine
        stats  = engine.get_recognition_stats()

        dlib_version = None
        if USE_FACE_RECOGNITION_LIB:
            try:
                import face_recognition
                dlib_version = getattr(face_recognition, "__version__", "installed")
            except Exception:
                dlib_version = "installed"

        threshold = 0.6 if USE_FACE_RECOGNITION_LIB else DISTANCE_MATCH_THRESHOLD

        return jsonify({
            "engine_mode":          "dlib" if USE_FACE_RECOGNITION_LIB else "opencv",
            "dlib_version":         dlib_version,
            "registered_persons":   stats.get("total_persons", 0),
            "total_encodings":      stats.get("total_face_encodings", 0),
            "current_threshold":    threshold,
            "confidence_threshold": engine.confidence_threshold,
            "timestamp":            datetime.now().isoformat(),
        }), 200

    except Exception as e:
        logger.exception("Error retrieving recognition status")
        return jsonify({"error": str(e)}), 500


@api_bp.route("/recognize", methods=["POST"])
def recognize_face():
    """
    Recognize ALL faces present in a single camera frame.

    Expected JSON:
        { "frame": "<base64-encoded JPEG/PNG>" }

    Response JSON (200):
        {
          "person_id":     str | null,   // primary result (first granted, or first face)
          "name":          str,
          "confidence":    float,
          "access_granted": bool,
          "timestamp":     str,
          "face_count":    int,          // total faces detected
          "faces": [                     // one entry per detected face
            {
              "person_id":     str | null,
              "name":          str,
              "confidence":    float,
              "access_granted": bool,
              "face_location": [x, y, w, h]
            }, ...
          ]
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

        # For a single face use the smoothing buffer (majority vote over last
        # 5 frames) so one bad frame cannot deny access to a known resident.
        # For multiple faces fall back to raw per-face results — smoothing a
        # crowd is unreliable without face-tracking across frames.
        raw_faces = engine.recognize_all_faces(frame)

        if len(raw_faces) == 1:
            x, y, w, h = raw_faces[0].get("face_location", [0, 0, 0, 0])
            smoothed = engine.recognize_with_smoothing(frame, (x, y, w, h))
            if smoothed:
                smoothed["face_location"] = [x, y, w, h]
                all_recs = [smoothed]
            else:
                all_recs = raw_faces
        else:
            engine.buffer.reset()   # multi-face scene — clear single-face history
            all_recs = raw_faces

        if not all_recs:
            return jsonify({
                "person_id": None,
                "name": "Unknown",
                "confidence": 0.0,
                "access_granted": False,
                "face_count": 0,
                "faces": [],
                "timestamp": datetime.now().isoformat(),
            }), 200

        db = get_db()
        timestamp = datetime.now().isoformat()
        processed_faces = []

        for rec in all_recs:
            conf = rec.get("confidence", 0.0)
            access_granted = (
                rec.get("person_id") is not None
                and float(conf) >= engine.confidence_threshold
            )
            face_result = {
                "person_id":      rec.get("person_id"),
                "name":           str(rec.get("name", "Unknown")),
                "confidence":     float(conf),
                "access_granted": bool(access_granted),
                "face_location":  rec.get("face_location", []),
                "timestamp":      timestamp,
            }

            if access_granted and face_result["person_id"]:
                db_user_id = face_result["person_id"]
                existing = db.get_user_by_name(face_result["name"])
                if existing:
                    db_user_id = existing.get("user_id", db_user_id)
                else:
                    db.add_user(db_user_id, face_result["name"], "resident")

                db.log_access(db_user_id, "entry", confidence=float(conf), status="success")

                try:
                    threat_detector = current_app.threat_detector
                    threat_detector.log_access_attempt(db_user_id, success=True)
                    tailgating = threat_detector.check_tailgating(db_user_id, db)
                    if tailgating:
                        db.log_threat(tailgating["threat_type"], tailgating["severity"],
                                      user_id=db_user_id, message=tailgating["message"])
                    unusual = threat_detector.check_unusual_access_time(db_user_id)
                    if unusual:
                        db.log_threat(unusual["threat_type"], unusual["severity"],
                                      user_id=db_user_id, message=unusual["message"])
                except Exception as e:
                    logger.warning("Threat detection skipped: %s", e)

                db.log_audit("ACCESS_GRANTED", user_id=db_user_id,
                             resource="door/main-entrance", result="success",
                             details=f"confidence={conf:.2f}")

                try:
                    anomaly_event = {"timestamp": timestamp, "person_id": db_user_id,
                                     "access_type": "entry", "confidence": float(conf)}
                    anomaly_result = current_app.anomaly_detector.predict_anomaly(anomaly_event)
                    face_result["anomaly_score"] = anomaly_result.get("anomaly_score", 0.0)
                    face_result["is_anomaly"]    = anomaly_result.get("is_anomaly", False)
                    if anomaly_result.get("is_anomaly"):
                        score = anomaly_result.get("anomaly_score", 0.0)
                        db.log_anomaly(db_user_id, "BEHAVIOURAL_ANOMALY", score,
                                       f"Unusual access pattern (score={score:.3f})")
                        db.log_threat(threat_type="Behavioural Anomaly Detected",
                                      severity="MEDIUM", user_id=db_user_id,
                                      message=(f"Unusual access pattern for {face_result['name']}. "
                                               f"Score: {score:.3f}."))
                except Exception as e:
                    logger.warning("Anomaly detection skipped: %s", e)

                logger.info("Access granted: %s (conf=%.2f)", face_result["name"], conf)

            else:
                unknown_id = "Unknown"
                db.add_user("Unknown", "Unknown", "resident")
                db.log_access("Unknown", "entry", confidence=float(conf), status="failed")
                db.log_audit("ACCESS_DENIED", user_id=unknown_id,
                             resource="door/main-entrance", result="failed",
                             details=f"confidence={conf:.2f}")
                db.log_threat(threat_type="Unrecognised Face Detected", severity="HIGH",
                              user_id=unknown_id,
                              message=(f"Face at main entrance, no match. "
                                       f"Confidence: {float(conf):.2f}."))
                try:
                    threat_detector = current_app.threat_detector
                    threat_detector.log_access_attempt(unknown_id, success=False)
                    repeated = threat_detector.check_failed_access_attempts(unknown_id)
                    if repeated:
                        db.log_threat(repeated["threat_type"], repeated["severity"],
                                      user_id=unknown_id, message=repeated["message"])
                except Exception as e:
                    logger.warning("Failed-attempt check skipped: %s", e)

                logger.info("Access denied: unknown face (conf=%.2f)", conf)

            processed_faces.append(face_result)

        # Primary result = first person granted access, else first face detected
        granted = [f for f in processed_faces if f.get("access_granted")]
        primary = (granted[0] if granted else processed_faces[0]).copy()
        primary["face_count"] = len(processed_faces)
        primary["faces"]      = processed_faces
        return jsonify(primary), 200

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
        db = get_db()
        db_stats = db.get_database_stats()

        fall_count_today = 0
        try:
            rows = db.get_anomalies(limit=200, anomaly_type="fall_detected")
            local_tz = datetime.now().astimezone().tzinfo
            today_local = datetime.now(local_tz).date()

            def _parse_to_local_date(ts_raw):
                ts = str(ts_raw or "").strip()
                if not ts:
                    return None

                # Handle common stored forms:
                # - "YYYY-MM-DD HH:MM:SS" (SQLite CURRENT_TIMESTAMP, UTC)
                # - ISO strings with/without timezone suffix
                try:
                    if "T" not in ts and " " in ts:
                        dt = datetime.strptime(ts[:19], "%Y-%m-%d %H:%M:%S")
                        dt = dt.replace(tzinfo=timezone.utc)
                    else:
                        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                        if dt.tzinfo is None:
                            dt = dt.replace(tzinfo=timezone.utc)
                    return dt.astimezone(local_tz).date()
                except Exception:
                    return None

            fall_count_today = sum(
                1 for r in rows
                if _parse_to_local_date(r.get("timestamp")) == today_local
            )
        except Exception:
            pass

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
            'falls': {
                'today': fall_count_today
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
