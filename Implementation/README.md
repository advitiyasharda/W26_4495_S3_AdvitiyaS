# FaceDoor — Smart Door Security System

A facial recognition-based access control and monitoring system designed for elderly care facilities. It identifies residents and staff at entry points, logs every access event, detects behavioural anomalies, monitors for falls, and surfaces everything through a modern web dashboard.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [1. Backend (Flask API)](#1-backend-flask-api)
  - [2. Frontend (Next.js)](#2-frontend-nextjs)
- [Usage](#usage)
  - [Registering Faces](#registering-faces)
  - [Running the System](#running-the-system)
  - [Fall Detection (Live Camera)](#fall-detection-live-camera)
  - [Diagnostics](#diagnostics)
- [API Reference](#api-reference)
- [Dashboard Pages](#dashboard-pages)
- [Screenshots](#screenshots)
- [Configuration](#configuration)
- [Compliance](#compliance)
- [Scripts](#scripts)

---

## Overview

FaceDoor provides:

- **Facial Recognition** — detects and identifies people at the door using HOG feature extraction and Euclidean distance matching (85–95% accuracy, runs on Raspberry Pi)
- **Threat Detection** — rules-based alerts for failed access attempts, unusual hours, unrecognised faces, and frequency spikes
- **Anomaly Detection** — Isolation Forest ML model flags unusual behavioural patterns (e.g. inactivity, off-hours access, failed access bursts)
- **Fall Detection** — real-time rules-based fall detector using MediaPipe Pose skeleton tracking; detects falls via hip height, torso angle, and drop velocity
- **Audit Logging** — every system action is logged for PIPEDA / GDPR compliance
- **Live Dashboard** — real-time monitoring of entries/exits, alerts, falls, and audit trail via a Next.js web app

---

## Architecture

```
┌─────────────────────────────┐        ┌──────────────────────────────────┐
│   Next.js Frontend          │        │   Flask REST API                 │
│   localhost:3000            │◄──────►│   localhost:5001                 │
│                             │  HTTP  │                                  │
│  Dashboard  /               │        │  /api/recognize                  │
│  Alerts     /alerts         │        │  /api/logs                       │
│  Logs       /logs           │        │  /api/threats                    │
│  Falls      /falls          │        │  /api/stats                      │
│  Audit      /compliance     │        │  /api/compliance/audit           │
└─────────────────────────────┘        │  /api/fall/detect                │
                                       │  /api/fall/log  (new)            │
                                       │  /api/fall/events                │
                                       │  /api/fall/status                │
                                       └──────────────┬───────────────────┘
                                                      │
                              ┌───────────────────────▼───────────────────┐
                              │   SQLite Database  (data/doorface.db)     │
                              │   Tables: users, access_logs,             │
                              │           threats, anomalies,             │
                              │           audit_logs,                     │
                              │           behavioral_profiles             │
                              └───────────────────────────────────────────┘
```

The Next.js dev server proxies all `/api/*` requests to Flask automatically — no CORS issues during development.

---

## Tech Stack

| Layer              | Technology                                          |
|--------------------|-----------------------------------------------------|
| Backend            | Python 3.9+, Flask 3.x                             |
| Computer Vision    | OpenCV 4.x (Haar Cascade, HOG)                     |
| Pose Estimation    | MediaPipe 0.10 (PoseLandmarker — Tasks API)        |
| Machine Learning   | scikit-learn (Isolation Forest), StandardScaler    |
| Database           | SQLite via `sqlite3`                               |
| Frontend           | Next.js 15 (App Router), React 19, TypeScript      |
| Styling            | Tailwind CSS                                        |
| Charts             | Recharts                                            |
| Target Hardware    | Raspberry Pi 4 / Jetson Nano                       |

---

## Project Structure

```text
Implementation/
│
├── main.py                          # Flask app entry point
├── config.py                        # Configuration constants
├── requirements.txt                 # Python dependencies
│
├── api/                             # REST API layer
│   ├── __init__.py                  # Flask app factory — loads all models at startup
│   ├── routes.py                    # Core endpoints (recognize, logs, threats, stats)
│   ├── facial_recognition.py        # HOG face detection & matching engine
│   ├── fall_detection_routes.py     # Fall detection endpoints (/api/fall/...)
│   └── threat_detection.py          # Rules-based threat scoring
│
├── models/                          # ML models
│   ├── anomaly_detection.py         # Isolation Forest anomaly detector
│   ├── isolation_forest.pkl         # Trained Isolation Forest model artifact
│   ├── fall_detection.py            # FallDetector (Phase 1 rules-based)
│   ├── fall_detection_trained.py    # LSTMFallDetector (Phase 2 trained model)
│   ├── pose_landmarker.task         # MediaPipe pre-trained pose skeleton model (download separately)
│   ├── fall_lstm.keras              # Trained LSTM fall detection model (93% accuracy)
│   └── fall_lstm_scaler.pkl         # Feature scaler for LSTM model
│
├── data/                            # Data layer
│   ├── database.py                  # SQLite manager (all DB read/write operations)
│   ├── data_generator.py            # Synthetic training data generator
│   ├── doorface.db                  # SQLite database (auto-created, gitignored)
│   ├── synthetic_dataset.csv        # Generated training data for anomaly model
│   ├── keypoints/                   # Extracted MediaPipe keypoints from URFD videos (CSVs)
│   ├── urfd/                        # URFD dataset videos — download separately, gitignored
│   │   ├── Fall/                    # 30 fall videos (fall-01-cam0.mp4 ... fall-30-cam0.mp4)
│   │   └── Activities of Daily Living/  # 40 ADL videos
│   └── samples/                     # Captured face photos per person
│       └── {person_name}/
│           └── *.jpg / *.png
│
├── frontend/                        # Next.js dashboard (App Router)
│   ├── app/
│   │   ├── layout.tsx               # Root layout with sidebar
│   │   ├── page.tsx                 # Main dashboard (stats + charts)
│   │   ├── alerts/page.tsx          # Security alerts feed
│   │   ├── falls/page.tsx           # Fall detection history & live status
│   │   ├── logs/page.tsx            # Access logs + registered people
│   │   └── compliance/page.tsx      # Audit trail (PIPEDA compliance)
│   ├── components/
│   │   ├── Sidebar.tsx              # Collapsible nav sidebar
│   │   ├── StatCard.tsx             # KPI stat cards
│   │   ├── AccessChart.tsx          # Bar chart (entries/exits by hour)
│   │   ├── StatusDonut.tsx          # Donut chart (access breakdown)
│   │   ├── AccessLogsTable.tsx      # Paginated access log table
│   │   ├── AlertList.tsx            # Threat alert cards list
│   │   ├── AuditTable.tsx           # Compliance audit table
│   │   └── StatusBadge.tsx          # Small status pill component
│   ├── lib/
│   │   ├── api.ts                   # Typed API client (all fetch wrappers)
│   │   └── demoData.ts              # Demo data when DB is empty
│   ├── next.config.ts               # API proxy (frontend → Flask :5001)
│   ├── tailwind.config.ts           # Tailwind design tokens
│   └── package.json
│
├── scripts/                         # Utility scripts (run from project root)
│   ├── fall_detection_camera.py     # Live webcam fall detection (Phase 1 rules or Phase 2 LSTM)
│   ├── extract_keypoints.py         # Extract MediaPipe keypoints from URFD videos → CSVs
│   ├── capture_faces.py             # Capture face photos from webcam
│   ├── register_faces.py            # Register faces into DB + extract encodings
│   ├── clear_database.py            # Reset the SQLite DB (preserves samples/)
│   ├── diagnose_recognition.py      # Full system diagnostics tool
│   ├── quick_test_recognition.py    # Quick recognition sanity check
│   └── train_anomaly_detection.py   # Generate data and train Isolation Forest
│
├── tests/                           # Test scripts (run from project root)
│   ├── test_api_recognize.py        # API-level tests for /api/recognize
│   ├── test_face_recognition_real.py
│   ├── test_facial_recognition.py
│   └── test_integration.py          # End-to-end integration tests
│
├── docs/                            # Architecture, API, deployment, guides
│   ├── ARCHITECTURE.md
│   ├── API_DOCS.md
│   ├── DEPLOYMENT.md
│   ├── FACIAL_RECOGNITION_GUIDE.md
│   ├── GET_STARTED.md
│   ├── SECURITY.md
│   ├── TRAINING_GUIDE.md
│   └── images/
│
└── screenshots/                     # UI screenshots for reports / README
    ├── dashboard.png
    ├── access-logs.png
    ├── alerts.png
    └── audit-trail.png
```

---

## Getting Started

> **Important:** Always run commands from the **`Implementation/`** directory. Scripts and the Flask app expect to find `data/`, `api/`, and `models/` relative to the current working directory.

### Prerequisites

| Tool    | Version | Download                |
|---------|---------|-------------------------|
| Python  | 3.11+   | https://www.python.org  |
| Node.js | 18+ LTS | https://nodejs.org      |
| npm     | 9+      | Included with Node.js   |

> **Mac users:** Install Python 3.11 via Homebrew for best results: `brew install python@3.11`

### 1. Backend (Flask API)

```bash
# Install Python dependencies
pip install -r requirements.txt

# Download the MediaPipe pose model (one-time, ~9 MB)
curl -L -o models/pose_landmarker.task \
  https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_full/float16/1/pose_landmarker_full.task

# Start the API server (use python3 on macOS/Linux)
python main.py
```

Flask API will be available at **http://localhost:5001**

### 2. Frontend (Next.js)

Open a **second terminal**:

```bash
cd frontend

# Install Node dependencies (first time only)
npm install

# Start the dev server
npm run dev
```

Dashboard will be available at **http://localhost:3000**

> Both servers must be running at the same time. The frontend proxies all `/api/*` calls to Flask automatically.

---

## Usage

### Registering Faces

Before the system can recognise anyone, register faces:

```bash
# Step 1 — capture face photos from your webcam
python scripts/capture_faces.py

# Step 2 — register the captured photos into the database
python scripts/register_faces.py
```

The system will prompt for a name, capture several photos, extract HOG features, and store them in `data/samples/` and the SQLite database.

### Running the System

Once faces are registered:

1. Start Flask: `python main.py`
2. Start Next.js: `cd frontend && npm run dev`
3. Open **http://localhost:3000**
4. Point a camera feed at the door — the `/api/recognize` endpoint accepts base64-encoded frames

### Fall Detection (Live Camera + Dashboard)

Run Flask first, then the fall detection script in a second terminal:

```bash
# Terminal 1 — Flask must be running
python main.py

# Terminal 2 — live camera fall detector
python scripts/fall_detection_camera.py
```

A window opens showing your webcam with a skeleton overlay. When a fall is detected:
- The banner turns **red** with "FALL DETECTED"
- The fall is automatically posted to the Flask API (`/api/fall/log`)
- It appears immediately on the **Falls** dashboard page (`/falls`)
- The **"Falls Detected Today"** stat card on the main dashboard updates

> **Any person is monitored** — registered or unregistered/unknown. Fall detection uses pose estimation only, not face recognition.

**Options:**
```bash
python scripts/fall_detection_camera.py --camera 1       # use a different camera
python scripts/fall_detection_camera.py --threshold 0.6  # adjust sensitivity (default 0.55)
python scripts/fall_detection_camera.py --log falls.csv  # also save events to CSV
python scripts/fall_detection_camera.py --no-display     # headless / no window
python scripts/fall_detection_camera.py --no-api         # skip dashboard posting
python scripts/fall_detection_camera.py --api-url http://localhost:5001  # custom server
```

**Controls while running:**
- `Q` — quit
- `S` — save screenshot to `screenshots/`
- `R` — reset fall history

**How it works (Phase 1 — Rules-Based):**

MediaPipe extracts 33 body skeleton landmarks per frame. Three rules are scored and combined:

| Rule | Weight | Trigger |
|------|--------|---------|
| Hip height | 35% | Hips near bottom of frame (person on floor) |
| Torso angle | 30% | Spine tilted > 50° from vertical |
| Drop velocity | 35% | Hips dropped rapidly across recent frames |

When combined confidence ≥ 0.55 → fall is declared and sent to the dashboard.

A **cooldown** of ~30 frames (~1 second at 30 fps) prevents the same fall from triggering multiple alerts.

### Fall Detection Phase 2 — LSTM Model

Phase 2 uses a trained LSTM (Long Short-Term Memory) neural network for higher-accuracy fall detection. Instead of hand-tuned rules, the LSTM learns fall patterns from labelled video sequences.

**How it works:**

```
Video frame → MediaPipe Pose (33 landmarks × 2 = 66 features)
    → rolling window of 30 frames → StandardScaler normalisation
    → LSTM model (fall_lstm.keras) → fall probability (0–1)
    → threshold → FALL / NO FALL
```

The LSTM does **not** process raw pixels. It processes **pose-landmark sequences** extracted by the same MediaPipe model used in Phase 1.

#### Full LSTM Workflow (videos → trained model → live detection)

**Step 1 — Prepare video dataset**

You need two classes of `.mp4` videos:
- **Fall videos** (people falling)
- **ADL / normal videos** (walking, sitting, bending, standing)

Place them into (create these folders if they don't exist):

```
data/urfd/Fall/                          ← fall videos (.mp4)
data/urfd/Activities of Daily Living/    ← normal activity videos (.mp4)
```

> The original UR Fall Detection Dataset is available at [https://fenix.ur.edu.pl/mkepski/ds/uf.html](https://fenix.ur.edu.pl/mkepski/ds/uf.html) (30 fall + 40 ADL cam0 videos). You can also use your own videos.

**Step 2 — Extract keypoints from videos**

```bash
python3 scripts/extract_keypoints.py
```

This reads every `.mp4` from both folders, runs MediaPipe Pose on each frame, and saves one CSV per video to `data/keypoints/`. Each CSV has 66 columns (x,y for 33 keypoints) plus a `label` column (1 = fall, 0 = normal).

> Takes ~5–15 minutes depending on video count and hardware. If you already have CSVs in `data/keypoints/` from a previous extraction, new CSVs are added alongside them.

**Step 3 — Train the LSTM model**

```bash
python3 scripts/train_lstm.py
```

This:
1. Loads all keypoint CSVs from `data/keypoints/`
2. Creates fixed-length sequences of 30 frames (sliding window with 50% overlap)
3. Fits a StandardScaler on all features and saves it to `models/fall_lstm_scaler.pkl`
4. Splits data 80/20 for training/testing
5. Trains a 2-layer LSTM (64 → 32 units, dropout, batch normalisation) for up to 50 epochs with early stopping
6. Saves the best model to `models/fall_lstm.keras`
7. Prints accuracy, confusion matrix, and classification report

**Step 4 — Evaluate the model (optional but recommended)**

```bash
python3 scripts/evaluate_lstm.py
```

Loads the trained model + scaler, runs predictions on all keypoint sequences, and saves a detailed report to `models/lstm_eval_report.txt`.

**Step 5 — Run live fall detection with LSTM**

```bash
# Terminal 1 — Flask backend must be running
python3 main.py

# Terminal 2 — live camera with LSTM mode
python3 scripts/fall_detection_camera.py --lstm
```

The camera script extracts pose landmarks per frame, builds a rolling 30-frame sequence, runs the LSTM model, and posts detected falls to the backend. Falls appear on the `/falls` dashboard page and as CRITICAL alerts on `/alerts`.

> You can also set `FALL_DETECTOR_MODE=lstm` in `config.py` to use LSTM mode when the backend itself processes frames via `POST /api/fall/detect`.

#### Summary of files involved

| Step | Script | Reads | Creates |
|------|--------|-------|---------|
| 1 | *(manual)* | — | `.mp4` videos in `data/urfd/` |
| 2 | `scripts/extract_keypoints.py` | Videos + `models/pose_landmarker.task` | `data/keypoints/*.csv` |
| 3 | `scripts/train_lstm.py` | `data/keypoints/*.csv` | `models/fall_lstm.keras` + `models/fall_lstm_scaler.pkl` |
| 4 | `scripts/evaluate_lstm.py` | Model + scaler + keypoints | `models/lstm_eval_report.txt` |
| 5 | `scripts/fall_detection_camera.py --lstm` | Model + scaler + webcam | Posts to `POST /api/fall/log` |

### Fall Alerting and Escalation

When a fall is detected (by either Phase 1 or Phase 2), the backend:

1. Stores an **anomaly** row in SQLite (`anomaly_type = "fall_detected"`, `anomaly_score = confidence`)
2. Stores a **threat** row (`threat_type = "FALL_DETECTED"`, `severity = "CRITICAL"`)
3. Checks for **repeated falls in the last 24 hours**:
   - 2 falls → additional `REPEATED_FALLS_WARNING` threat (HIGH severity)
   - 3+ falls → additional `REPEATED_FALLS_CRITICAL` threat (CRITICAL severity)

If the LSTM detector cannot see enough of the body, it returns a visibility warning instead — this is logged as a LOW severity `CAMERA_VISIBILITY_WARNING` (not a fall event).

---

### Diagnostics

If recognition is not working:

```bash
python scripts/diagnose_recognition.py
```

Checks camera connectivity, face detection, stored samples, recognition accuracy, and database health.

---

## API Reference

All endpoints are prefixed with `/api`.

### Core Endpoints

| Method | Endpoint            | Description                          |
|--------|---------------------|--------------------------------------|
| GET    | `/health`           | Health check                         |
| POST   | `/recognize`        | Recognize a face from a camera frame |
| POST   | `/log-access`       | Log an access event manually         |
| GET    | `/logs`             | Get access logs (paginated)          |
| GET    | `/threats`          | Get active security threats          |
| GET    | `/stats`            | System statistics                    |
| GET    | `/compliance/audit` | PIPEDA audit log                     |

### Fall Detection Endpoints

| Method | Endpoint         | Description                                                        |
|--------|------------------|--------------------------------------------------------------------|
| POST   | `/fall/detect`   | Analyse a base64 frame for falls (re-runs detection on server)     |
| POST   | `/fall/log`      | Log a pre-detected fall directly to DB (used by camera script)     |
| GET    | `/fall/events`   | List recent fall events from DB                                    |
| GET    | `/fall/status`   | Detector health and config                                         |
| POST   | `/fall/reset`    | Clear velocity history and cooldown                                |

### Example — Recognize a face

```bash
curl -X POST http://localhost:5001/api/recognize \
  -H "Content-Type: application/json" \
  -d '{"frame": "<base64_encoded_image>"}'
```

Response:
```json
{
  "person_id": "resident_001",
  "name": "Margaret T.",
  "confidence": 0.94,
  "access_granted": true,
  "timestamp": "2026-03-08T14:30:00"
}
```

### Example — Get fall events

```bash
curl "http://localhost:5001/api/fall/events?limit=10"
```

Response:
```json
{
  "events": [
    {
      "anomaly_id": 12,
      "anomaly_type": "fall_detected",
      "anomaly_score": 0.78,
      "description": "Fall detected: hips low (0.81); torso tilted 67°",
      "timestamp": "2026-03-08T21:30:00"
    }
  ],
  "count": 1
}
```

---

## Dashboard Pages

| Page        | URL           | Description                                                       |
|-------------|---------------|-------------------------------------------------------------------|
| Dashboard   | `/`           | KPI cards (including falls today), hourly chart, recent logs      |
| Alerts      | `/alerts`     | Active threats filtered by ALL / HIGH / CRITICAL severity         |
| Falls       | `/falls`      | Fall detection history, confidence scores, detector live status   |
| Access Logs | `/logs`       | Full paginated access log with entry/exit badges                  |
| Audit Trail | `/compliance` | PIPEDA-compliant audit log with CSV export                        |

> **Demo mode:** When the database has no registered faces, pages automatically show realistic demo data. A yellow `Demo data` badge appears in the page header.

---

## Screenshots

### Dashboard
![Dashboard](screenshots/dashboard.png)

### Alerts
![Alerts](screenshots/alerts.png)

### Access Logs
![Access Logs](screenshots/access-logs.png)

### Audit Trail
![Audit Trail](screenshots/audit-trail.png)

---

## Configuration

All system settings live in `config.py`:

| Setting                       | Default            | Description                                   |
|-------------------------------|--------------------|-----------------------------------------------|
| `CONFIDENCE_THRESHOLD`        | `0.6`              | Minimum face match confidence to grant access |
| `FAILED_ATTEMPTS_THRESHOLD`   | `3`                | Failed attempts before threat alert           |
| `INACTIVITY_THRESHOLD_HOURS`  | `24`               | Hours without access before alert             |
| `UNUSUAL_HOURS`               | `22:00 – 06:00`    | Hours flagged as unusual access               |
| `ANOMALY_SCORE_THRESHOLD`     | `0.7`              | Isolation Forest score cutoff                 |
| `DATABASE_PATH`               | `data/doorface.db` | SQLite file location                          |
| `TARGET_DEVICE`               | `raspberry_pi`     | Hardware target for optimisation              |
| `FALL_DETECTOR_MODE`          | `rules`            | Fall runtime mode (`rules` or `lstm`)         |
| `FALL_CONFIDENCE_THRESHOLD`   | `0.55`             | Shared threshold for fall declaration         |
| `FALL_COOLDOWN_FRAMES`        | `30`               | LSTM event cooldown window                    |

Fall detection thresholds are tunable at the top of `models/fall_detection.py`:

| Setting                  | Default | Description                              |
|--------------------------|---------|------------------------------------------|
| `FALL_THRESHOLD`         | `0.52`  | Weighted confidence to declare a fall    |
| `HIP_HEIGHT_THRESHOLD`   | `0.72`  | Normalised y position considered "floor" |
| `TORSO_ANGLE_THRESHOLD`  | `50°`   | Degrees from vertical = lying down       |
| `VELOCITY_THRESHOLD`     | `0.05`  | Normalised drop per frame = fast fall    |
| `VELOCITY_WINDOW`        | `5`     | Frames tracked for velocity calculation  |

---

## Compliance

FaceDoor is designed with **PIPEDA** (Canada) and **GDPR** compliance in mind:

- All face data is processed and stored **locally** — no cloud uploads
- Every system action is written to the `audit_logs` table with actor, resource, and result
- Audit logs are exportable as CSV from the Compliance page
- Face images are stored only in `data/samples/` and can be deleted on request
- Recognition confidence scores are logged for accountability

---

## Scripts

| Script                                | Purpose                                                    |
|---------------------------------------|------------------------------------------------------------|
| `scripts/fall_detection_camera.py`    | Live webcam fall detection — Phase 1 rules or Phase 2 LSTM (`--lstm` flag) |
| `scripts/extract_keypoints.py`        | Extract MediaPipe pose keypoints from URFD videos → CSVs in `data/keypoints/` |
| `scripts/train_lstm.py`              | Train LSTM fall detection model from keypoint CSVs → `models/fall_lstm.keras` + scaler |
| `scripts/evaluate_lstm.py`            | Evaluate trained LSTM model and write report to `models/lstm_eval_report.txt` |
| `scripts/system_health_check.py`      | Check DB, model artifacts, API health, and fall detector status |
| `scripts/capture_faces.py`            | Capture face photos from webcam for registration           |
| `scripts/register_faces.py`           | Register captured photos, extract HOG features             |
| `scripts/clear_database.py`           | Reset the SQLite DB (preserves `data/samples/`)            |
| `scripts/diagnose_recognition.py`     | Full system diagnostics (camera, DB, recognition)          |
| `scripts/quick_test_recognition.py`   | Quick test: photo + live webcam recognition                |
| `scripts/train_anomaly_detection.py`  | Generate synthetic data and retrain Isolation Forest       |
| `tests/test_facial_recognition.py`    | Component-level recognition unit tests                     |
| `tests/test_face_recognition_real.py` | Extended webcam + photo recognition tests                  |
| `tests/test_integration.py`           | End-to-end pipeline integration tests                      |
| `tests/test_api_recognize.py`         | API-level tests for `/api/recognize`                       |
| `tests/test_fall_detection.py`        | Fall route and repeated-falls unit tests                   |

---

## Douglas College CSIS 4495 — Applied Research Project

© 2026 Douglas College. Built for elderly care facilities.
