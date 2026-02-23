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
