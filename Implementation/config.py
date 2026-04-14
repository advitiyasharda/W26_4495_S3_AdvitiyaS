"""
Configuration file for Door Face Panels Smart Security System
"""
import os
from datetime import timedelta

# Flask Configuration
DEBUG = True
SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
FLASK_ENV = 'development'

# Database Configuration
DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'data', 'doorface.db')
SQLALCHEMY_DATABASE_URI = f'sqlite:///{DATABASE_PATH}'
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Facial Recognition Configuration
FACE_CONFIDENCE_THRESHOLD = 0.6
FACE_DETECTION_SCALE_FACTOR = 1.05
FACE_DETECTION_MIN_NEIGHBORS = 5
MAX_INFERENCE_LATENCY_MS = 500

# Threat Detection Configuration
FAILED_ATTEMPT_THRESHOLD = 3  # Failed attempts to trigger alert
FAILED_ATTEMPT_WINDOW_MINUTES = 10
INACTIVITY_THRESHOLD_HOURS = 24
UNUSUAL_TIME_HOURS = [22, 23, 0, 1, 2, 3, 4, 5]  # 10 PM - 5 AM

# Anomaly Detection Configuration
ANOMALY_SCORE_THRESHOLD = 0.7
ISOLATION_FOREST_CONTAMINATION = 0.1
ISOLATION_FOREST_N_ESTIMATORS = 100

# API Configuration
API_TIMEOUT_SECONDS = 30
MAX_UPLOAD_SIZE_MB = 10

# Logging Configuration
LOG_LEVEL = 'INFO'
LOG_FILE = os.path.join(os.path.dirname(__file__), 'logs', 'doorface.log')

# Security
ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY', 'default-encryption-key')
ENABLE_AUDIT_LOGGING = True
ENABLE_ACCESS_CONTROL = True

# Hardware Configuration
TARGET_DEVICE = 'raspberry_pi'  # 'raspberry_pi' or 'jetson_nano'
ENABLE_GPU = False  # Set to True if using Jetson with GPU

# Fall Detection Configuration
# Mode options: "rules" (default) or "lstm"
FALL_DETECTOR_MODE = os.environ.get("FALL_DETECTOR_MODE", "rules").strip().lower()
# Shared confidence threshold used by both rules and LSTM implementations
FALL_CONFIDENCE_THRESHOLD = float(os.environ.get("FALL_CONFIDENCE_THRESHOLD", "0.55"))
# Rules-specific setting
FALL_VELOCITY_WINDOW = int(os.environ.get("FALL_VELOCITY_WINDOW", "8"))
# Cooldown used by LSTM detector (rules detector has built-in cooldown)
FALL_COOLDOWN_FRAMES = int(os.environ.get("FALL_COOLDOWN_FRAMES", "30"))

# Object Detection Configuration (Phase 3 — YOLO26)
# Floor confidence sent to YOLO; per-category thresholds in the detector raise
# the effective bar for noisy categories while keeping it low for weapons.
OBJECT_DETECTION_CONFIDENCE = float(os.environ.get("OBJECT_DETECTION_CONFIDENCE", "0.20"))
# Consecutive frames an object must appear before triggering an alert
OBJECT_DETECTION_FRAME_THRESHOLD = int(os.environ.get("OBJECT_DETECTION_FRAME_THRESHOLD", "3"))
# Minutes an item must remain unattended before raising a MEDIUM threat
OBJECT_UNATTENDED_MINUTES = float(os.environ.get("OBJECT_UNATTENDED_MINUTES", "2.0"))
# Path to a custom fine-tuned weapon model; falls back gracefully if missing
OBJECT_WEAPON_MODEL_PATH = os.environ.get(
    "OBJECT_WEAPON_MODEL_PATH",
    os.path.join(os.path.dirname(__file__), "models", "weapon_detector.pt"),
)
# Base model — YOLO26 Large (higher mAP than medium; heavier). Override with OBJECT_BASE_MODEL.
OBJECT_BASE_MODEL = os.environ.get("OBJECT_BASE_MODEL", "yolo26l.pt")
# Inference image size (px); 640 is the sweet spot for real-time + accuracy
OBJECT_IMGSZ = int(os.environ.get("OBJECT_IMGSZ", "640"))
# CLAHE preprocessing for backlit / shadowed doorway scenes
OBJECT_ENABLE_PREPROCESSING = os.environ.get("OBJECT_ENABLE_PREPROCESSING", "1") == "1"
