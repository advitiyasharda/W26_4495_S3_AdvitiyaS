"""
API Module for Door Face Panels Smart Security System
"""
import logging
from pathlib import Path
import json
import sys
import types
from importlib.machinery import ModuleSpec

from flask import Flask
from flask_cors import CORS

logger = logging.getLogger(__name__)


def _norm_name(value: str) -> str:
    return "".join(ch.lower() if ch.isalnum() else "" for ch in (value or ""))


def _load_face_encodings_from_samples(engine, db, samples_dir="data/samples"):
    """Load registered faces from data/samples/ into the engine using DB IDs."""
    path = Path(samples_dir)
    if not path.exists():
        return 0

    users = db.get_users() or []
    by_user_id = {str(u.get("user_id", "")).strip(): u for u in users}
    by_name = {_norm_name(str(u.get("name", ""))): u for u in users if u.get("name")}

    total = 0
    for person_dir in path.iterdir():
        if not person_dir.is_dir():
            continue
        folder = person_dir.name
        person = by_user_id.get(folder) or by_name.get(_norm_name(folder))
        if not person:
            logger.warning("Skipping sample folder '%s' (no matching DB user)", folder)
            continue

        person_id = str(person.get("user_id", folder))
        person_name = str(person.get("name", folder))
        photos = list(person_dir.glob("*.jpg")) + list(person_dir.glob("*.png"))
        for photo_path in photos:
            try:
                import cv2
                frame = cv2.imread(str(photo_path))
                if frame is None:
                    continue
                faces = engine.detect_faces(frame)
                if len(faces) > 0:
                    x, y, w, h = faces[0]
                    face_roi = frame[y : y + h, x : x + w]
                    encoding = engine._extract_face_features(face_roi)
                    if encoding is not None:
                        engine.register_face(person_id, person_name, encoding)
                        total += 1
            except Exception as e:
                logger.warning("Failed to load %s: %s", photo_path.name, e)
    return total


def create_app(config_name="config"):
    """Create and configure Flask application"""
    app = Flask(__name__)
    app.config.from_object(config_name)

    # Enable CORS — allow requests from the Next.js dev server and production build
    CORS(app, origins=["http://localhost:3000", "http://127.0.0.1:3000"])

    # Initialize database before registering routes
    from data.database import Database
    app.db = Database()

    # Initialize face recognition engine and load encodings from data/samples/
    from api.facial_recognition import FacialRecognitionEngine
    app.face_engine = FacialRecognitionEngine()
    n = _load_face_encodings_from_samples(app.face_engine, app.db)
    if n > 0:
        logger.info("Loaded %d face encodings from data/samples/", n)

    # Load anomaly detection model
    from models.anomaly_detection import AnomalyDetector
    app.anomaly_detector = AnomalyDetector()
    model_path = Path("models/isolation_forest.pkl")
    if model_path.exists():
        app.anomaly_detector.load_model(str(model_path))
        logger.info("Anomaly detection model loaded from %s", model_path)
    else:
        logger.warning("No trained anomaly model found at %s — run scripts/train_anomaly_detection.py", model_path)

    # Initialise threat detector (rules-based)
    from api.threat_detection import ThreatDetector
    app.threat_detector = ThreatDetector()
    logger.info("ThreatDetector initialised")

    # Initialise fall detector (stateful — one instance per server process)
    # MediaPipe imports tensorflow.tools.docs.doc_controls if tensorflow is present.
    # On some local envs (protobuf/tensorflow mismatch), this crashes startup.
    # Provide a tiny stub so backend can still boot and face APIs stay available.
    if "tensorflow" not in sys.modules:
        tf_mod = types.ModuleType("tensorflow")
        tf_tools_mod = types.ModuleType("tensorflow.tools")
        tf_docs_mod = types.ModuleType("tensorflow.tools.docs")
        # Some libraries inspect __spec__; keep it non-None.
        tf_mod.__spec__ = ModuleSpec("tensorflow", loader=None)
        tf_tools_mod.__spec__ = ModuleSpec("tensorflow.tools", loader=None)
        tf_docs_mod.__spec__ = ModuleSpec("tensorflow.tools.docs", loader=None)
        sys.modules["tensorflow"] = tf_mod
        sys.modules["tensorflow.tools"] = tf_tools_mod
        sys.modules["tensorflow.tools.docs"] = tf_docs_mod
        _no_op = lambda x: x
        sys.modules["tensorflow.tools.docs"].doc_controls = types.SimpleNamespace(
            do_not_generate_docs=_no_op,
        )

    from models.fall_detection import FallDetector
    from models.fall_detection_trained import LSTM_MODEL_PATH, LSTM_SCALER_PATH

    app.fall_detector_mode_requested = str(
        app.config.get("FALL_DETECTOR_MODE", "rules")
    ).strip().lower()
    app.fall_detector_mode = "rules"
    app.fall_model_artifacts = {
        "pose_model_exists": Path("models/pose_landmarker.task").exists(),
        "lstm_model_exists": Path(LSTM_MODEL_PATH).exists(),
        "lstm_scaler_exists": Path(LSTM_SCALER_PATH).exists(),
    }
    model_info_path = Path("models/model_info.json")
    app.fall_model_info = {}
    if model_info_path.exists():
        try:
            app.fall_model_info = json.loads(model_info_path.read_text())
        except Exception as e:
            logger.warning("Could not parse %s: %s", model_info_path, e)

    threshold = app.config.get("FALL_CONFIDENCE_THRESHOLD", 0.55)
    velocity_window = app.config.get("FALL_VELOCITY_WINDOW", 8)
    cooldown_frames = app.config.get("FALL_COOLDOWN_FRAMES", 30)

    try:
        if app.fall_detector_mode_requested == "lstm":
            from models.fall_detection_trained import LSTMFallDetector
            app.fall_detector = LSTMFallDetector(
                threshold=threshold,
                cooldown_frames=cooldown_frames,
            )
            app.fall_detector_mode = "lstm"
            logger.info("FallDetector initialised (Phase 2 — LSTM)")
        else:
            app.fall_detector = FallDetector(
                fall_threshold=threshold,
                velocity_window=velocity_window,
            )
            app.fall_detector_mode = "rules"
            logger.info("FallDetector initialised (Phase 1 — rules-based)")
    except Exception as e:
        if app.fall_detector_mode_requested == "lstm":
            logger.warning("LSTM detector init failed, falling back to rules: %s", e)
            try:
                app.fall_detector = FallDetector(
                    fall_threshold=threshold,
                    velocity_window=velocity_window,
                )
                app.fall_detector_mode = "rules"
                logger.info("FallDetector fallback initialised (Phase 1 — rules-based)")
            except Exception as fallback_err:
                app.fall_detector = None
                app.fall_detector_mode = "unavailable"
                logger.warning("FallDetector fallback failed: %s", fallback_err)
        else:
            app.fall_detector = None
            app.fall_detector_mode = "unavailable"
            logger.warning("FallDetector could not be initialised: %s", e)

    # Initialise object detector (Phase 3 — YOLO26)
    try:
        from models.object_detection import ObjectDetector
        weapon_model_path = app.config.get(
            "OBJECT_WEAPON_MODEL_PATH", "models/weapon_detector.pt"
        )
        base_model = app.config.get("OBJECT_BASE_MODEL", "yolo26l.pt")
        obj_confidence = app.config.get("OBJECT_DETECTION_CONFIDENCE", 0.20)
        obj_frame_threshold = app.config.get("OBJECT_DETECTION_FRAME_THRESHOLD", 3)
        obj_unattended_minutes = app.config.get("OBJECT_UNATTENDED_MINUTES", 2.0)
        obj_imgsz = app.config.get("OBJECT_IMGSZ", 640)
        obj_preprocessing = app.config.get("OBJECT_ENABLE_PREPROCESSING", True)

        app.object_detector = ObjectDetector(
            weapon_model_path=weapon_model_path,
            base_model=base_model,
            confidence=obj_confidence,
            frame_threshold=obj_frame_threshold,
            unattended_minutes=obj_unattended_minutes,
            imgsz=obj_imgsz,
            enable_preprocessing=obj_preprocessing,
        )
        logger.info(
            "ObjectDetector initialised (ready=%s, weapon_model=%s, model=%s, imgsz=%s)",
            app.object_detector.is_ready,
            app.object_detector.weapon_model_ready,
            base_model,
            obj_imgsz,
        )
    except Exception as e:
        app.object_detector = None
        logger.warning("ObjectDetector could not be initialised: %s", e)

    # Register blueprints
    from api.routes import api_bp
    app.register_blueprint(api_bp, url_prefix="/api")

    from api.fall_detection_routes import fall_bp
    app.register_blueprint(fall_bp, url_prefix="/api/fall")

    from api.object_detection_routes import objects_bp
    app.register_blueprint(objects_bp, url_prefix="/api/objects")

    return app
