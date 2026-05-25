# Configuration Reference

All backend configuration lives in `Implementation/config.py`. Most settings can be overridden with environment variables without editing the file.

---

## How Configuration Works

1. `config.py` defines all defaults
2. `create_app()` reads `config.py` via `app.config.from_object("config")`
3. Many values also read environment variables at module load time, e.g. `os.environ.get("FALL_DETECTOR_MODE", "rules")`
4. To override a setting, set the environment variable before running Flask

**Recommended approach for persistent overrides:** Create a `.env` file in `Implementation/` and load it with:

```python
# In main.py or before create_app()
from dotenv import load_dotenv
load_dotenv()
```

Or export variables in your shell:

```bash
export FALL_DETECTOR_MODE=lstm
export FACE_CONFIDENCE_THRESHOLD=0.65
python main.py
```

---

## Flask / General

| Config key | Default | Environment var | Notes |
|------------|---------|-----------------|-------|
| `DEBUG` | `True` | — | Set `False` in production |
| `SECRET_KEY` | `"dev-secret-key-change-in-production"` | `SECRET_KEY` | **Change before production** |
| `ENCRYPTION_KEY` | `"default-encryption-key"` | `ENCRYPTION_KEY` | Used for data encryption |
| `FLASK_ENV` | `"development"` | `FLASK_ENV` | Set `"production"` to disable debug |
| `FLASK_HOST` | `"0.0.0.0"` | `FLASK_HOST` | Bind address |
| `FLASK_PORT` | `5001` | `FLASK_PORT` | Port for Flask; must match Next.js proxy |

> **Security note:** Never commit real `SECRET_KEY` or `ENCRYPTION_KEY` values. Use environment variables or a `.env` file (which is `.gitignore`d).

---

## Database

| Config key | Default | Notes |
|------------|---------|-------|
| `DATABASE_PATH` | `data/doorface.db` | Auto-resolved relative to `config.py` |

To use a different database file:

```bash
# Not currently exposed as an env var; edit config.py or pass to Database():
from data.database import Database
db = Database("/path/to/custom.db")
```

---

## Face Recognition

| Config key | Default | Env var | Effect |
|------------|---------|---------|--------|
| `FACE_CONFIDENCE_THRESHOLD` | `0.6` | — | Minimum confidence to grant access |
| `FACE_DETECTION_SCALE_FACTOR` | `1.05` | — | OpenCV Haar cascade scale factor |
| `FACE_DETECTION_MIN_NEIGHBORS` | `5` | — | OpenCV Haar cascade min neighbors |
| `MAX_INFERENCE_LATENCY_MS` | `500` | — | Latency warning threshold |

**Tuning confidence threshold:**
- Lower (e.g. 0.5): more permissive, fewer false denials, more false accepts
- Higher (e.g. 0.75): stricter, fewer false accepts, more false denials
- Calibrate using `python scripts/calibrate_recognition.py`

---

## Threat Detection

| Config key | Default | Effect |
|------------|---------|--------|
| `FAILED_ATTEMPT_THRESHOLD` | `3` | Failures in window before HIGH threat |
| `FAILED_ATTEMPT_WINDOW_MINUTES` | `10` | Time window for failed-attempt count |
| `INACTIVITY_THRESHOLD_HOURS` | `24` | Hours with no access before alert |
| `UNUSUAL_TIME_HOURS` | `[22,23,0,1,2,3,4,5]` | Hours considered unusual (10 PM–5 AM) |

---

## Anomaly Detection

| Config key | Default | Env var | Effect |
|------------|---------|---------|--------|
| `ANOMALY_SCORE_THRESHOLD` | `0.7` | — | Score ≥ this triggers a MEDIUM threat |
| `ISOLATION_FOREST_CONTAMINATION` | `0.1` | — | Expected % of anomalies in training data |
| `ISOLATION_FOREST_N_ESTIMATORS` | `100` | — | Number of trees in the forest |

Changing `CONTAMINATION` or `N_ESTIMATORS` requires retraining the model:

```bash
python scripts/train_anomaly_detection.py
```

---

## Fall Detection

| Config key | Default | Env var | Effect |
|------------|---------|---------|--------|
| `FALL_DETECTOR_MODE` | `"rules"` | `FALL_DETECTOR_MODE` | `"rules"` or `"lstm"` |
| `FALL_CONFIDENCE_THRESHOLD` | `0.55` | `FALL_CONFIDENCE_THRESHOLD` | Fall score ≥ this fires alert |
| `FALL_VELOCITY_WINDOW` | `8` | `FALL_VELOCITY_WINDOW` | Frames for velocity averaging (rules only) |
| `FALL_COOLDOWN_FRAMES` | `30` | `FALL_COOLDOWN_FRAMES` | Frames between alerts |

**Quick sensitivity test:**
```bash
# More sensitive (lower threshold)
export FALL_CONFIDENCE_THRESHOLD=0.45

# Less sensitive (fewer false positives)
export FALL_CONFIDENCE_THRESHOLD=0.65
```

---

## Object Detection

| Config key | Default | Env var | Effect |
|------------|---------|---------|--------|
| `OBJECT_DETECTION_CONFIDENCE` | `0.20` | `OBJECT_DETECTION_CONFIDENCE` | YOLO base confidence floor |
| `OBJECT_DETECTION_FRAME_THRESHOLD` | `3` | `OBJECT_DETECTION_FRAME_THRESHOLD` | Frames before alert fires |
| `OBJECT_UNATTENDED_MINUTES` | `2.0` | `OBJECT_UNATTENDED_MINUTES` | Minutes before unattended parcel alert |
| `OBJECT_WEAPON_MODEL_PATH` | `models/weapon_detector.pt` | `OBJECT_WEAPON_MODEL_PATH` | Custom weapon model; ignored if file missing |
| `OBJECT_BASE_MODEL` | `"yolo26l.pt"` | `OBJECT_BASE_MODEL` | YOLO base model filename |
| `OBJECT_IMGSZ` | `640` | `OBJECT_IMGSZ` | Inference image size in pixels |
| `OBJECT_ENABLE_PREPROCESSING` | `True` | `OBJECT_ENABLE_PREPROCESSING` | CLAHE preprocessing for doorway lighting |

**Performance vs accuracy trade-off:**
- `OBJECT_IMGSZ=320` — faster, less accurate (suitable for Raspberry Pi)
- `OBJECT_IMGSZ=640` — balanced (default)
- `OBJECT_IMGSZ=1280` — most accurate, slow on CPU

---

## Frontend Environment Variables

Create `Implementation/frontend/.env.local` (not committed to git):

```bash
# Always fall back to demo when API returns empty (default: true)
NEXT_PUBLIC_USE_DEMO_DATA=true

# Force demo data always (ignores toggle and API — useful for screenshots)
NEXT_PUBLIC_FORCE_DEMO_DATA=false

# Skip MediaPipe pose model download on npm install (set "1" to skip)
SKIP_POSE_MODEL_DOWNLOAD=
```

---

## Hardware Configuration

| Config key | Default | Notes |
|------------|---------|-------|
| `TARGET_DEVICE` | `"raspberry_pi"` | Informational; not currently used in code |
| `ENABLE_GPU` | `False` | Jetson Nano GPU acceleration (future use) |

---

## Logging

| Config key | Default | Notes |
|------------|---------|-------|
| `LOG_LEVEL` | `"INFO"` | Python logging level |
| `LOG_FILE` | `logs/doorface.log` | File logging path (not created by default) |

Backend logs are written to `Implementation/server.log` in the current directory when running via `main.py`. The Demo Center page shows no terminal output — check `server.log` if tools appear to misbehave.

---

## Full Example: Production-Like Override

```bash
export SECRET_KEY="your-random-secret-here"
export ENCRYPTION_KEY="your-encryption-key-here"
export FLASK_ENV="production"
export FALL_DETECTOR_MODE="lstm"
export FACE_CONFIDENCE_THRESHOLD="0.70"
export OBJECT_DETECTION_CONFIDENCE="0.25"
export OBJECT_DETECTION_FRAME_THRESHOLD="5"

python main.py
```
