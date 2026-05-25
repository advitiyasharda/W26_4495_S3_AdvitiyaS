# Detection Models

This document covers all four AI/ML components: face recognition, fall detection (Phase 1 & 2), object detection, and anomaly detection.

---

## 1. Face Recognition

**File:** `Implementation/api/facial_recognition.py`

### Engine modes

The system supports two detection engines, auto-selected at startup:

| Mode | Package | Accuracy | Notes |
|------|---------|----------|-------|
| **dlib** | `face_recognition` | High | Requires dlib compilation; recommended |
| **OpenCV** | Built-in | Moderate | Haar cascade; works without extra install |

Check current mode: `GET /api/recognition/status` → `engine_mode`

### How it works

**Face detection** (finding face locations in a frame):
- OpenCV mode: Haar cascade classifier on grayscale frame
- dlib mode: `face_recognition.face_locations()`

**Feature extraction** (encoding a face into a vector):
- OpenCV mode: Histogram of Oriented Gradients (HOG) → 36-dim vector
- dlib mode: 128-dim face descriptor via ResNet model

**Matching** (comparing a new face to enrolled ones):
```
distance = euclidean(new_encoding, known_encoding)
match if distance < threshold (0.55 for dlib, 0.6 for OpenCV)
```

For multiple enrollments per person, the best (lowest) distance across all their encodings is used. A secondary check ensures the best match is significantly closer than the second-best person.

### Smoothing buffer (`RecognitionBuffer`)

For single-face scenes, the last 5 recognition results are buffered. The person with the majority vote is returned. This prevents one bad frame (blink, partial occlusion) from causing incorrect denial.

Multi-face scenes bypass the buffer (crowd matching with history is unreliable).

### Enrollment

Each person needs a folder in `data/samples/{person_id}/` containing 30–50 face photos in varied lighting/angles. At startup and on `/api/recognition/reload`, all photos are loaded into memory as encoding arrays.

**Tip:** More photos (40+) and varied angles (slight left/right/up) significantly improve recognition accuracy.

---

## 2. Fall Detection — Phase 1 (Rules-Based)

**File:** `Implementation/models/fall_detection.py`  
**Model file:** `models/pose_landmarker.task` (MediaPipe, ~29 MB, auto-downloaded on `npm install`)

### Algorithm

1. **Pose estimation** — MediaPipe `PoseLandmarker` (Lite model) extracts 33 body landmarks (x, y, z, visibility) from the BGR frame.

2. **Three signals computed:**

   | Signal | How computed | Weight |
   |--------|-------------|--------|
   | Hip height | Normalised y-coordinate of hip midpoint (low y → person is on the ground) | 0.40 |
   | Torso angle | Angle between shoulder midpoint and hip midpoint from vertical | 0.35 |
   | Hip velocity | Mean downward displacement of hips over last N frames (velocity window) | 0.25 |

3. **Fall score** = weighted sum of signals (each normalised to 0–1)

4. **Fall decision:** score ≥ `fall_threshold` (default 0.55) AND not in cooldown

5. **Post-fall cooldown:** After a fall is detected, no new fall is reported for `cooldown_frames` frames (default 30). This prevents one fall event producing a flood of alerts.

### FallResult dataclass

```python
@dataclass
class FallResult:
    is_fall: bool
    confidence: float       # 0.0 – 1.0
    reason: str             # human-readable description
    hip_height: float       # normalised hip y
    torso_angle_deg: float  # degrees from vertical
    hip_velocity: float     # frames per normalised unit
    landmarks_visible: bool
```

### Tuning parameters

| Parameter | Default | Effect |
|-----------|---------|--------|
| `fall_threshold` | 0.55 | Lower → more sensitive (more false positives) |
| `velocity_window` | 8 | Frames over which velocity is averaged |
| `cooldown_frames` | 30 | Min frames between fall alerts |

---

## 3. Fall Detection — Phase 2 (LSTM)

**File:** `Implementation/models/fall_detection_trained.py`  
**Model files:** `models/fall_lstm.keras`, `models/fall_lstm_scaler.pkl`

### Architecture

```
Input: 30 consecutive frames × 66 features
        (33 pose landmarks × x + y coordinates each)
         │
         ▼
StandardScaler (fit on training data, saved as .pkl)
         │
         ▼
LSTM layer(s) (Keras sequential model)
         │
         ▼
Dense(1, activation='sigmoid')
         │
         ▼
Fall probability 0.0 – 1.0
```

### Inference

1. MediaPipe extracts landmarks (same as Phase 1)
2. x/y coordinates of all 33 landmarks → 66-element feature vector
3. Appended to a rolling buffer of 30 frames
4. When buffer is full: normalize with `StandardScaler` → feed to LSTM
5. Output probability ≥ `threshold` (default 0.55) → fall detected

### Training

Training data comes from the **UR Fall Detection Dataset** (preprocessed CSVs in `data/keypoints/`).

```bash
# Extract keypoints from CSVs
python scripts/extract_keypoints.py

# Train the LSTM (saves fall_lstm.keras + fall_lstm_scaler.pkl)
python scripts/train_lstm.py

# Evaluate
python scripts/evaluate_lstm.py
```

### Enabling LSTM mode

```bash
export FALL_DETECTOR_MODE=lstm
python main.py
```

Both model files must exist in `models/`. If loading fails, the system auto-falls-back to rules mode.

---

## 4. Object Detection

**File:** `Implementation/models/object_detection.py`  
**Model file:** `models/yolo26l.pt` (also `Implementation/yolo26l.pt` for scripts CWD)

### Categories

YOLO detects COCO-class objects (80 classes) which are mapped to 5 security categories:

| Category | Severity | Example classes |
|----------|----------|-----------------|
| `WEAPON` | CRITICAL | knife, scissors (weapons list in config) |
| `SECURITY_THREAT` | HIGH | cell phone, laptop, backpack |
| `PARCEL` | MEDIUM (unattended) | suitcase, handbag, backpack |
| `MOBILITY_AID` | INFO | person (context), chair |
| `OPERATIONAL` | LOW | cup, bottle, clock |

The exact mapping is in `models/object_detection.py` (`CATEGORY_MAP` dict).

### Algorithm

1. Optional **CLAHE preprocessing** (Contrast Limited Adaptive Histogram Equalization) improves detection in low-light or overexposed doorway scenes
2. YOLO26l runs on the frame → raw detections with class + confidence
3. Per-category **confidence floors** (WEAPON requires higher confidence than OPERATIONAL)
4. **Frame persistence:** an object must be detected in `frame_threshold` consecutive frames before an alert fires (reduces false positives from motion blur)
5. **Unattended parcel tracking:** if a PARCEL is detected for `unattended_minutes` without a person nearby, severity escalates
6. HIGH/CRITICAL events are written to `threats` table via `/api/objects/detect`

### Optional weapon model

A custom YOLO head (`weapon_detector.pt`) can be trained specifically on the weapon dataset in `data/weapon_dataset/`. If the file exists at `models/weapon_detector.pt`, it is used for WEAPON-category detection instead of the base model.

Training:
```bash
python scripts/download_and_train_weapon_model.py
python scripts/finetune_weapon_model.py
```

---

## 5. Anomaly Detection (Behavioural)

**File:** `Implementation/models/anomaly_detection.py`  
**Model file:** `models/isolation_forest.pkl`

### What it detects

Unusual access patterns for a known resident — based on when they typically access the door. This is not about *who* is at the door (face recognition handles that), but whether a recognised person is accessing at an unusual time or frequency.

### Features (per access event)

| Feature | Description |
|---------|-------------|
| `hour_sin` | Cyclical encoding of hour (sin) |
| `hour_cos` | Cyclical encoding of hour (cos) |
| `day_sin` | Cyclical encoding of day-of-week (sin) |
| `day_cos` | Cyclical encoding of day-of-week (cos) |
| `access_type` | 1 = entry, 0 = exit |
| `confidence` | Face match confidence |
| `time_since_last` | Hours since this person's previous access |

Cyclical encoding prevents Monday (0) and Sunday (6) from appearing far apart to the model.

### Training

```bash
cd Implementation
python scripts/train_anomaly_detection.py
```

This generates synthetic access data (`data/synthetic_dataset.csv`), fits a `StandardScaler` + `IsolationForest`, and saves `models/isolation_forest.pkl`.

Contamination fraction (% of training data treated as anomalies) is set in `config.py` (`ANOMALY_CONTAMINATION`, default 0.1).

### Inference

```python
result = anomaly_detector.predict_anomaly({
    "timestamp": "2026-05-25T03:00:00",   # 3 AM unusual
    "person_id": "Reubin",
    "access_type": "entry",
    "confidence": 0.88
})
# → { "is_anomaly": True, "anomaly_score": 0.74 }
```

Score is sigmoid-normalised from Isolation Forest's raw score. Scores ≥ `ANOMALY_SCORE_THRESHOLD` (0.7) trigger a `Behavioural Anomaly Detected` threat (MEDIUM severity).

### BehavioralProfiler

An optional secondary check (`BehavioralProfiler`) in the same file computes a per-user baseline of preferred hours and flags deviations. Currently not wired into the main access path but available for future use.

---

## Model Files Summary

| File | Purpose | Size | Required |
|------|---------|------|---------|
| `models/pose_landmarker.task` | MediaPipe pose estimation | ~29 MB | Yes (downloaded on npm install) |
| `models/fall_lstm.keras` | LSTM fall detector | ~500 KB | Only for LSTM mode |
| `models/fall_lstm_scaler.pkl` | Input normalizer for LSTM | ~1 KB | Only for LSTM mode |
| `models/isolation_forest.pkl` | Anomaly detector | ~100 KB | No (system boots without it) |
| `models/weapon_detector.pt` | Custom weapon YOLO | variable | No (falls back to base model) |
| `yolo26l.pt` | YOLO26 base model (at root of Implementation/) | ~50 MB | Yes for object detection |

---

## Retraining Guide

| Model | Script | Inputs |
|-------|--------|--------|
| LSTM fall detector | `scripts/train_lstm.py` | CSVs in `data/keypoints/` |
| Anomaly detector | `scripts/train_anomaly_detection.py` | Synthetic or real access CSV |
| Weapon YOLO head | `scripts/finetune_weapon_model.py` | `data/weapon_dataset/` |

After retraining, restart Flask to load the new models.
