# Scripts Reference

All scripts live in `Implementation/scripts/`. Run them from the `Implementation/` directory with the virtual environment active unless otherwise noted.

```bash
cd Implementation
source venv/bin/activate   # or venv\Scripts\activate on Windows
```

---

## Face Recognition Scripts

### `capture_faces.py`

Captures webcam photos and optionally registers the person in the database.

```bash
# Basic capture only (no registration)
python scripts/capture_faces.py --person john --photos 40

# Full registration (capture + DB entry + reload engine)
python scripts/capture_faces.py \
  --person john \
  --photos 40 \
  --register-now \
  --person-id john_001 \
  --display-name "John Smith" \
  --role resident \
  --reload-api-url http://localhost:5001
```

**Arguments:**

| Argument | Required | Description |
|----------|----------|-------------|
| `--person` | Yes | Folder name in `data/samples/` |
| `--photos` | No (40) | Number of photos to capture |
| `--register-now` | No | Register in DB immediately after capture |
| `--person-id` | If registering | DB primary key for the user |
| `--display-name` | If registering | Full name shown in dashboard |
| `--role` | If registering | `resident` or `caregiver` |
| `--reload-api-url` | If registering | Flask URL to call reload after registration |

**Output:** JPEGs saved to `data/samples/{person}/` named `{person}_1.jpg`, `{person}_2.jpg`, ...

**macOS note:** Sets `OPENCV_VIDEOIO_PRIORITY_AVFOUNDATION=1000` to ensure the correct camera backend is used.

---

### `register_faces.py`

Batch-registers existing `data/samples/` folders into the database without capturing new photos. Useful when migrating the database or after clearing it.

```bash
python scripts/register_faces.py
```

---

### `calibrate_recognition.py`

Tests recognition accuracy against enrolled samples and recommends a distance threshold.

```bash
python scripts/calibrate_recognition.py
```

---

### `diagnose_recognition.py`

Detailed diagnostic that shows per-person accuracy, distance distributions, and potential problem cases.

```bash
python scripts/diagnose_recognition.py
```

---

### `quick_test_recognition.py`

Opens the webcam for a quick live recognition test. Press **q** to quit.

```bash
python scripts/quick_test_recognition.py
```

---

## Fall Detection Scripts

### `fall_detection_camera.py`

Live fall detection from a webcam. Runs the local rules-based `FallDetector` and POSTs confirmed falls to `/api/fall/log`.

```bash
python scripts/fall_detection_camera.py
```

**Keyboard controls in the window:**
- **q** — quit
- **r** — reset detector history

**What it shows:** Live camera feed with pose landmarks, hip height indicator, torso angle, velocity reading, and fall confidence bar. Falls are highlighted in red.

**Why use this instead of `/api/fall/detect`:** The local detector maintains velocity history across frames. The server's detector instance shares history across all clients, making multi-client scenarios unreliable. This script is the recommended integration path.

---

### `extract_keypoints.py`

Pre-processes UR Fall Detection Dataset CSVs (in `data/keypoints/`) into a format suitable for LSTM training.

```bash
python scripts/extract_keypoints.py
```

---

### `train_lstm.py`

Trains the LSTM fall detector model from keypoint data. Saves:
- `models/fall_lstm.keras`
- `models/fall_lstm_scaler.pkl`
- `models/model_info.json`

```bash
python scripts/train_lstm.py
```

Training typically takes 1–5 minutes depending on dataset size.

---

### `evaluate_lstm.py`

Evaluates the trained LSTM model on a held-out test set. Prints accuracy, precision, recall, F1.

```bash
python scripts/evaluate_lstm.py
```

---

## Object Detection Scripts

### `test_object_detection_camera_live.py`

Live YOLO-based object detection from webcam. Optionally posts detections to the Flask API.

```bash
python scripts/test_object_detection_camera_live.py \
  --base-model yolo26l.pt \
  --post-api-url http://127.0.0.1:5001 \
  --api-every 3
```

**Arguments:**

| Argument | Default | Description |
|----------|---------|-------------|
| `--base-model` | `yolo26l.pt` | YOLO model filename |
| `--post-api-url` | None | If set, posts frames to `/api/objects/detect` |
| `--api-every` | 1 | Only post every Nth frame (reduces load) |
| `--confidence` | 0.20 | Detection confidence floor |
| `--no-display` | Off | Run headless (no window) |

Press **q** to quit.

---

### `test_object_detection_api.py`

Sends a test image to `/api/objects/detect` and prints the response. For API smoke testing.

```bash
python scripts/test_object_detection_api.py
```

---

### `download_and_train_weapon_model.py`

Downloads the weapon detection training dataset and trains a custom YOLO head.

```bash
python scripts/download_and_train_weapon_model.py
```

---

### `finetune_weapon_model.py`

Fine-tunes the weapon detection model on local data.

```bash
python scripts/finetune_weapon_model.py
```

---

## Anomaly Detection Scripts

### `train_anomaly_detection.py`

Generates synthetic access data and trains the `IsolationForest` anomaly model.

```bash
python scripts/train_anomaly_detection.py
```

Saves `models/isolation_forest.pkl`. Run this once during setup or after clearing the model.

---

## Database Scripts

### `clear_database.py`

⚠️ **DESTRUCTIVE** — drops all tables and recreates the empty schema.

```bash
python scripts/clear_database.py
```

Use only in development. Creates no backup.

---

## Testing Scripts

### `test_registration_flow.py`

End-to-end test of the face enrollment → recognition flow.

```bash
python scripts/test_registration_flow.py
```

---

### `test_fall_flow.sh`

Shell script that sends a test POST to `/api/fall/log` and verifies the response.

```bash
bash scripts/test_fall_flow.sh
```

---

## System Utilities

### `system_health_check.py`

Checks all dependencies, model files, and database connectivity. Useful to verify the environment before a demo.

```bash
python scripts/system_health_check.py
```

Output example:
```
✓ Flask
✓ OpenCV
✓ MediaPipe
✓ YOLO (ultralytics)
✓ pose_landmarker.task
✓ isolation_forest.pkl
⚠ fall_lstm.keras — not found (LSTM mode unavailable)
✓ database connection
```

---

## Script CWD Note

Most scripts use absolute paths via `Path(__file__).resolve().parent`, so they work from any directory. A few YOLO-related scripts expect `.pt` files in their working directory — copies of `yolo26l.pt` and `yolov8n.pt` are present in both `Implementation/scripts/` and `Implementation/` for this reason.
