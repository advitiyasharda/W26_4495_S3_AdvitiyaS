# FaceDoor — Smart Door Security System

**Douglas College CSIS 4495 — Applied Research Project (Section 003)**  
Team: Advitiya Sharda, Eric Sanjo, Reubin Chatta  
Industry Partner: Door Face Panels — Armin Ghauforian

---

## What This Project Does

FaceDoor is a smart door security system designed for elderly care facilities. A camera at the door recognises residents and staff by face, logs every entry and exit event, and shows caregivers everything on a live web dashboard. When an unknown person appears or something unusual happens, the system generates a security alert.

Phase 2 adds real-time **fall detection** using a trained LSTM model on top of the door security system, monitored through a dedicated dashboard page.

The project has three main parts that run together:

- **Backend (Flask + Python)** — handles face recognition, fall detection, stores all events in a local SQLite database, and exposes a REST API
- **Frontend (Next.js)** — a caregiver dashboard that reads from the API and refreshes automatically every 30 seconds
- **Camera script** — a standalone process that feeds frames into the fall detector and posts results to the backend API

Everything runs locally. No data is sent to the cloud.

---

## What the Dashboard Shows

| Page | URL | What you see |
|---|---|---|
| Dashboard | `http://localhost:3000/` | KPI cards (total entries, denials, active alerts, falls today), hourly bar chart, access outcome donut chart, recent access log |
| Alerts | `http://localhost:3000/alerts` | Security alert cards, filterable by severity (High / Critical) — includes fall alerts |
| Access Logs | `http://localhost:3000/logs` | Full paginated access log with entry/exit and status badges; registered people list |
| Audit Trail | `http://localhost:3000/compliance` | System audit log for compliance; CSV export |
| Falls | `http://localhost:3000/falls` | Live fall detection page — LSTM confidence bar, detector status, event history, reset button |

If no one has been registered yet, the dashboard shows realistic demo data with a visible "Demo data" label so the UI is always presentable.

---

## System Requirements

| Tool | Version | Where to get it |
|---|---|---|
| Python | **3.11** | https://www.python.org/downloads |
| Node.js | 18 LTS or newer | https://nodejs.org/en/download |
| npm | comes with Node.js | — |
| Webcam | any USB or built-in | required for face capture and fall detection |

A webcam is only needed if you want to register real faces or run the live detection scripts. The dashboard and API work without one.

> **Windows note:** Installing `face_recognition` (dlib) on Windows requires Visual Studio Build Tools. Run `pip install cmake` before `pip install face_recognition`.

---

## Installation

Clone the repository if you have not already:

```bash
git clone https://github.com/advitiyasharda/W26_4495_S3_AdvitiyaS.git
cd W26_4495_S3_AdvitiyaS
```

### Step 1 — Install Python dependencies

Run this from inside the `Implementation/` folder:

```bash
pip install -r requirements.txt
```

On Windows, use PowerShell (not Git Bash) for best results. If `face_recognition` fails to install, run these first:

```powershell
pip install cmake
pip install dlib
pip install face_recognition
```

### Step 2 — Install frontend dependencies

This only needs to be done once:

```bash
cd frontend
npm install
cd ..
```

---

## Running the Project

### Standard mode (face recognition + dashboard)

You need **two terminals open at the same time**.

**Terminal 1 — Backend:**

```bash
# Mac / Linux
FLASK_PORT=5001 python3 main.py

# Windows PowerShell
$env:FLASK_PORT=5001; python main.py
```

**Terminal 2 — Frontend:**

```bash
cd frontend
npm run dev
```

Open `http://localhost:3000` in a browser. If the backend is running, the dashboard shows live data. If not, it shows demo data automatically.

### Phase 2 mode (face recognition + fall detection + dashboard)

You need **three terminals**.

**Terminal 1 — Backend:**

```bash
$env:FLASK_PORT=5001; python main.py
```

**Terminal 2 — Fall detection camera (LSTM model):**

```bash
cd Implementation
python scripts/fall_detection_camera.py --lstm
```

**Terminal 3 — Frontend:**

```bash
cd Implementation/frontend
npm run dev
```

Open `http://localhost:3000/falls` to see live LSTM confidence scores updating in real time.

---

## Registering Faces (to use real recognition)

```bash
# Step 1: capture photos from your webcam
python3 scripts/capture_faces.py

# Step 2: load those photos into the database
python3 scripts/register_faces.py
```

You will be prompted to enter a name. The system takes several photos, extracts facial features, and saves them under `data/samples/<name>/`. Once registered, that person will be recognised when their face appears in a frame sent to `/api/recognize`.

### Calibrating recognition accuracy

After registering faces, run the calibration tool to find the optimal matching threshold for your specific sample photos:

```bash
python3 scripts/calibrate_recognition.py
```

This tests 11 threshold values between 0.30 and 0.80, prints a precision/recall/F1 table, and writes the best value back to `config.py` automatically. Run it with `--dry-run` to see results without changing any files.

---

## Face Recognition Engine

The system uses **two recognition backends** and automatically picks the best one available:

| Backend | How to enable | Accuracy |
|---|---|---|
| **dlib** (via `face_recognition`) | Install `face_recognition` — switches on automatically | ~89–95% |
| **OpenCV HOG** (fallback) | Used if `face_recognition` is not installed | ~70–80% |

To check which engine is active and see the current threshold, call the status endpoint after starting the backend:

```
GET http://localhost:5001/api/recognition/status
```

Returns engine mode, registered persons count, active threshold, and dlib version.

---

## Fall Detection

### Phase 1 — Rules-based (available now)

Three rules applied per frame: hip height, torso angle, and hip drop velocity. Each produces a score weighted into a combined confidence value. A fall is flagged when confidence ≥ 0.55.

```bash
python3 scripts/fall_detection_camera.py
```

### Phase 2 — LSTM model (requires `--lstm` flag)

An LSTM trained on the UR Fall Detection Dataset classifies sequences of 33 MediaPipe body landmarks over N frames as fall or no-fall.

```bash
python3 scripts/fall_detection_camera.py --lstm
```

The `--lstm` flag loads `models/fall_lstm.keras` and the associated scaler. Falls detected by either method are logged to the database and escalate as **CRITICAL** security alerts visible on the alerts dashboard.

Press `q` to quit the camera window. Detections are automatically posted to `/api/fall/log`.

---

## LSTM Model

| Property | Value |
|---|---|
| Architecture | LSTM (2 layers) |
| Input | Sequence of MediaPipe pose keypoints (33 landmarks × 4 values) |
| Training dataset | UR Fall Detection Dataset (URFD) |
| Test accuracy | **93%** |
| Model file | `models/fall_lstm.keras` |
| Scaler file | `models/fall_lstm_scaler.pkl` |

The keypoint extraction pipeline (`scripts/extract_keypoints.py`) uses the MediaPipe Tasks API to process URFD video frames into CSV sequences for training. The model was trained using `scripts/train_lstm.py`.

---

## Threat Detection Rules

The system monitors for the following patterns and raises alerts automatically:

| Rule | Severity | Trigger |
|---|---|---|
| Unrecognised face | HIGH | Face detected but no database match |
| Repeated failed access | HIGH | 3+ failed attempts in 10 minutes |
| Unusual access time | MEDIUM | Entry between 10 PM and 5 AM |
| Tailgating | HIGH | 2+ different people entering within 15 seconds |
| Wandering | HIGH | Known resident exits between 9 PM and 6 AM |
| Fall detected | CRITICAL | Single confirmed fall event |
| Repeated falls (warning) | HIGH | 2 falls in the past 24 hours |
| Repeated falls (critical) | CRITICAL | 3+ falls in the past 24 hours |

---

## Port Configuration

The backend runs on port **5001** (not Flask's default 5000) to avoid conflicts. The frontend proxies all API calls to port 5001 via `frontend/next.config.ts`.

To change the port, update both:

```powershell
$env:FLASK_PORT=5002; python main.py
```

```ts
// frontend/next.config.ts
destination: 'http://localhost:5002/api/:path*',
```

---

## Project Structure

```
project-root/
|
|-- main.py                        # Entry point — starts the Flask API
|-- config.py                      # Configuration values (thresholds, paths)
|-- requirements.txt               # Python package list
|
|-- api/
|   |-- __init__.py                # Flask app factory, loads face encodings at startup
|   |-- routes.py                  # All REST API route handlers (includes /recognition/status)
|   |-- facial_recognition.py      # Face detection and matching engine (dlib + OpenCV fallback)
|   |-- fall_detection_routes.py   # Fall detection REST endpoints (/detect, /status, /events, /log)
|   `-- threat_detection.py        # Rules-based threat detection (6 rules + repeated-falls)
|
|-- data/
|   |-- database.py                # All SQLite read/write operations
|   |-- data_generator.py          # Synthetic data generation (for ML training)
|   |-- doorface.db                # SQLite database file (created automatically)
|   `-- samples/                   # Face photo storage
|       `-- {person_name}/
|           `-- *.jpg / *.png
|
|-- models/
|   |-- anomaly_detection.py       # Isolation Forest model wrapper
|   |-- fall_detection.py          # FallDetector class — rules-based (Phase 1) + LSTM (Phase 2)
|   |-- isolation_forest.pkl       # Trained anomaly model (generated by training script)
|   |-- fall_lstm.keras            # Trained LSTM fall detection model (93% accuracy)
|   |-- fall_lstm_scaler.pkl       # Feature scaler for LSTM input normalisation
|   `-- pose_landmarker.task       # MediaPipe pose model (downloaded separately)
|
|-- frontend/                      # Next.js web application
|   |-- app/
|   |   |-- page.tsx               # Main dashboard page (includes falls-today stat card)
|   |   |-- alerts/page.tsx        # Alerts page
|   |   |-- logs/page.tsx          # Access logs page
|   |   |-- compliance/page.tsx    # Audit trail page
|   |   `-- falls/page.tsx         # Fall monitoring page (LSTM confidence bar, event table)
|   |-- components/
|   |   |-- Sidebar.tsx            # Navigation (includes Falls link)
|   |   |-- StatCard.tsx
|   |   |-- AccessChart.tsx
|   |   |-- StatusDonut.tsx
|   |   |-- AccessLogsTable.tsx
|   |   |-- AlertList.tsx
|   |   |-- AuditTable.tsx
|   |   `-- StatusBadge.tsx
|   |-- lib/
|   |   |-- api.ts                 # Typed API client (includes fall detection types)
|   |   `-- demoData.ts            # Fallback demo data when DB is empty
|   |-- next.config.ts             # API proxy configuration (port 5001)
|   `-- package.json
|
|-- scripts/
|   |-- capture_faces.py           # Capture face photos from webcam
|   |-- register_faces.py          # Load photos into the recognition engine and DB
|   |-- calibrate_recognition.py   # Threshold calibration tool — finds optimal value, updates config.py
|   |-- clear_database.py          # Wipe the database without deleting sample photos
|   |-- diagnose_recognition.py    # Diagnostic tool — checks camera, samples, DB, recognition
|   |-- quick_test_recognition.py  # Quick photo-based recognition test
|   |-- extract_keypoints.py       # Extract MediaPipe keypoints from URFD dataset videos
|   |-- train_lstm.py              # Train LSTM fall detection model on extracted keypoints
|   |-- fall_detection_camera.py   # Live webcam fall detection (--lstm flag for LSTM mode)
|   `-- train_anomaly_detection.py # Train the Isolation Forest model on synthetic data
|
|-- tests/
|   |-- test_api_recognize.py         # API-level recognition test using live webcam
|   |-- test_face_recognition_real.py # Extended webcam test with per-frame statistics
|   |-- test_facial_recognition.py    # Unit tests for the recognition engine (CI-safe, no webcam)
|   |-- test_threat_detection.py      # Unit tests for all threat detection rules
|   `-- test_integration.py           # End-to-end pipeline test (auto-runs, no prompt)
|
`-- dashboard/                     # Original HTML/CSS prototype (kept for reference)
```

---

## Running the Tests

```bash
# Full integration test (no prompts — runs automatically)
python tests/test_integration.py

# Recognition engine unit tests (no webcam required)
python tests/test_facial_recognition.py

# Webcam-based recognition test
python tests/test_facial_recognition.py --webcam

# Threat detection unit tests
python tests/test_threat_detection.py
```

---

## Compliance Notes

All face data is processed and stored on the local machine. No images or personal data are uploaded to any external server. The audit log records every system action (access granted, access denied, user registered, user deleted) with a timestamp and actor identifier. This supports accountability requirements under PIPEDA (Canada) and similar privacy frameworks. Full compliance documentation is in `docs/COMPLIANCE.md`.

---

*CSIS 4495 Applied Research Project — Douglas College, Winter 2026*
