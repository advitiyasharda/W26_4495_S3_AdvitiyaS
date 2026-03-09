"""
API Module for Door Face Panels Smart Security System
"""
import logging
from pathlib import Path

from flask import Flask
from flask_cors import CORS

logger = logging.getLogger(__name__)


def _load_face_encodings_from_samples(engine, samples_dir="data/samples"):
    """Load registered faces from data/samples/ into the engine."""
    path = Path(samples_dir)
    if not path.exists():
        return 0
    total = 0
    for person_dir in path.iterdir():
        if not person_dir.is_dir():
            continue
        person_name = person_dir.name
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
                        engine.register_face(person_name, person_name, encoding)
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
    n = _load_face_encodings_from_samples(app.face_engine)
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

    # Initialise fall detector (stateful — one instance per server process)
    from models.fall_detection import FallDetector
    try:
        app.fall_detector = FallDetector()
        logger.info("FallDetector initialised (Phase 1 — rules-based)")
    except Exception as e:
        app.fall_detector = None
        logger.warning("FallDetector could not be initialised: %s", e)

    # Register blueprints
    from api.routes import api_bp
    app.register_blueprint(api_bp, url_prefix="/api")

    from api.fall_detection_routes import fall_bp
    app.register_blueprint(fall_bp, url_prefix="/api/fall")

    return app
