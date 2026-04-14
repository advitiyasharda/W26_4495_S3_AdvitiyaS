# FaceDoor — Implementation folder

This directory is the **complete runnable FaceDoor system**: Flask API, SQLite data layer, computer-vision and ML models, CLI scripts, automated tests, Next.js dashboard, and technical documentation.

**Important:** Run all Python commands and tests with your **current working directory set to `Implementation/`** (so paths like `data/`, `models/`, and `api/` resolve correctly). The repository root `README.md` gives a shorter course-oriented overview; this file is the **detailed reference for everything inside `Implementation/`**.

---

## Table of contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Technology stack](#technology-stack)
4. [Top-level layout](#top-level-layout)
5. [What each major area does](#what-each-major-area-does)
   - [Root files](#root-files)
   - [`api/` — HTTP layer](#api--http-layer)
   - [`models/` — ML and CV logic](#models--ml-and-cv-logic)
   - [`data/` — persistence and datasets](#data--persistence-and-datasets)
   - [`scripts/` — CLI utilities](#scripts--cli-utilities)
   - [`tests/` — quality assurance](#tests--quality-assurance)
   - [`frontend/` — Next.js dashboard](#frontend--nextjs-dashboard)
   - [`dashboard/` — legacy HTML prototype](#dashboard--legacy-html-prototype)
   - [`docs/` — technical writing](#docs--technical-writing)
   - [`screenshots/`](#screenshots)
6. [Installation and first run](#installation-and-first-run)
7. [Environment variables](#environment-variables)
8. [Operational workflows](#operational-workflows)
9. [REST API reference](#rest-api-reference)
10. [Dashboard routes](#dashboard-routes)
11. [Configuration (`config.py`)](#configuration-configpy)
12. [Compliance and privacy](#compliance-and-privacy)
13. [Evaluation and testing](#evaluation-and-testing)
14. [Troubleshooting](#troubleshooting)

---

## Overview

FaceDoor supports:

| Capability | Description |
|------------|-------------|
| **Access control** | Detect faces in a frame, match to registered identities, log entry/exit, drive **grant/deny** decisions. |
| **Threat detection** | Rule-based alerts (failed attempts, unusual hours, unrecognised faces, tailgating-style patterns, wandering, **falls**, repeated falls, object-related threats where wired). |
| **Behavioural anomaly** | **Isolation Forest** on synthetic / access-derived features; scores feed into monitoring. |
| **Fall detection** | **Phase 1:** MediaPipe pose + heuristic rules (hip height, torso angle, velocity). **Phase 2:** sequence classifier (**LSTM** / Keras) on pose keypoint windows; optional on camera and/or server-side mode. |
| **Object detection** | **YOLOv8** (Ultralytics): general COCO objects plus optional **weapon-specialised** weights; events exposed via REST for the Objects dashboard. |
| **Audit trail** | SQLite-backed **audit_logs** for accountability (PIPEDA-oriented design). |
| **Dashboard** | Next.js app (App Router) with KPIs, charts, alerts, falls, logs, compliance export, objects. |

---

## Architecture

```
┌─────────────────────────────┐        ┌──────────────────────────────────────────┐
│  Next.js (frontend/)        │        │  Flask (main.py → api/__init__.py)       │
│  http://localhost:3000      │  HTTP  │  http://localhost:5001                   │
│                             │◄──────►│  Proxied: /api/* → Flask (next.config)   │
│  /  /alerts /logs /falls    │        │  Blueprints: /api, /api/fall, /api/objects│
│  /compliance /objects       │        └──────────────────┬───────────────────────┘
└─────────────────────────────┘                         │
                                                        ▼
                              ┌─────────────────────────────────────────────┐
                              │  SQLite — data/doorface.db                  │
                              │  users, access_logs, threats, anomalies,    │
                              │  audit_logs, behavioral_profiles, …         │
                              └─────────────────────────────────────────────┘
```

At startup, `create_app()` wires: **Database**, **FacialRecognitionEngine** (+ optional `models/face_encodings.npz`), **AnomalyDetector** (+ `models/isolation_forest.pkl` if present), **ThreatDetector**, **FallDetector** or **LSTMFallDetector** (per `FALL_DETECTOR_MODE`), **ObjectDetector** (YOLO — may degrade gracefully if weights missing).

---

## Technology stack

| Layer | Technologies |
|-------|----------------|
| API | Python **3.11+**, **Flask 3.x**, **flask-cors** |
| Vision | **OpenCV** (Haar cascade face detection; LBPH-style encoding path in code), optional **face_recognition** / dlib for higher-accuracy path when installed |
| Pose | **MediaPipe** Tasks API — `models/pose_landmarker.task` |
| ML | **scikit-learn** (Isolation Forest, scalers), **TensorFlow/Keras** (LSTM fall model) |
| Objects | **Ultralytics YOLOv8** (`ultralytics` package) |
| Crypto / privacy helpers | **cryptography** (Fernet) for at-rest encoding payload handling in recognition module |
| DB | **sqlite3** via `data/database.py` |
| Frontend | **Next.js 15** (App Router), **React 19**, **TypeScript**, **Tailwind CSS**, **Recharts** |

---

## Top-level layout

```text
Implementation/
├── main.py                 # Starts Flask (see FLASK_HOST / FLASK_PORT)
├── config.py               # All tunable constants (imported as config object)
├── requirements.txt        # Pinned minimum Python dependencies
├── .gitignore              # Ignores DB, venv, large artifacts, local secrets
│
├── api/                    # Flask blueprints and domain logic entrypoints
├── models/                 # Fall, anomaly, object detectors + serialized weights
├── data/                   # database.py, generator, samples, keypoints, optional urfd/
├── scripts/                # One-off and operational CLI tools
├── tests/                  # unittest + runnable integration scripts
├── frontend/               # Next.js application
├── dashboard/              # Legacy static HTML/JS prototype (reference)
├── docs/                   # Markdown guides (API, architecture, compliance, …)
└── screenshots/            # PNGs referenced by README figures
```

Large or generated artifacts (e.g. `doorface.db`, `__pycache__`, `.pt` / `.keras` files) may be **gitignored**; clone instructions often include downloading pose weights or placing URFD videos locally.

---

## What each major area does

### Root files

| File | Purpose |
|------|---------|
| **`main.py`** | Configures logging, calls `create_app('config')`, runs `app.run()` with **`threaded=False`** to reduce OpenCV/native multithreading issues. Host/port from **`FLASK_HOST`** / **`FLASK_PORT`** (default port **5001**). |
| **`config.py`** | Single source of truth for thresholds, DB path, fall mode, object-detection paths, retention days, device flags. Flask loads this module by name. |
| **`requirements.txt`** | Production-style list: Flask, OpenCV, scikit-learn, numpy, pandas, Pillow, dotenv, cryptography, mediapipe, tensorflow, ultralytics. Optional: **`face_recognition`** (requires **dlib** — often harder on Windows). |

---

### `api/` — HTTP layer

| File | Purpose |
|------|---------|
| **`__init__.py`** | **`create_app()`**: constructs Flask app, enables CORS for local Next origins, attaches **`app.db`**, loads face engine + **`models/face_encodings.npz`** fast path or rescans **`data/samples/`**, loads anomaly + threat + fall + object detectors, registers blueprints **`api_bp`**, **`fall_bp`**, **`objects_bp`**. |
| **`routes.py`** | Core REST: **`GET /api/health`**, **`GET /api/recognition/status`**, **`POST /api/recognize`**, **`POST /api/log-access`**, **`GET /api/threats`**, **`GET /api/users`**, **`DELETE /api/users/<id>`**, **`GET /api/logs`**, **`GET /api/stats`**, **`GET /api/compliance/audit`**, CSV/export helpers as implemented. |
| **`facial_recognition.py`** | **`FacialRecognitionEngine`**: face detection, encoding (OpenCV LBPH path or **dlib**/**face_recognition** when available), matching thresholds, optional **multi-face**, **quality** scoring, **RecognitionBuffer** smoothing, encrypted encoding storage helpers, **`/recognition/status`** support. |
| **`threat_detection.py`** | **`ThreatDetector`**: evaluates rules against DB state (failed access, unusual hours, inactivity, tailgating, wandering, unrecognised faces, fall-related escalation, object-related hooks where integrated). |
| **`fall_detection_routes.py`** | Blueprint **`/api/fall/*`**: **`POST /detect`**, **`GET /status`**, **`GET /events`**, **`POST /reset`**, **`POST /log`**. Bridges HTTP JSON (e.g. base64 frames) to **`app.fall_detector`**. |
| **`object_detection_routes.py`** | Blueprint **`/api/objects/*`**: **`POST /detect`**, **`GET /status`**, **`GET /events`** — uses **`app.object_detector`** when initialised. |

---

### `models/` — ML and CV logic

| File / artifact | Purpose |
|-----------------|---------|
| **`anomaly_detection.py`** | **`AnomalyDetector`** wrapper around sklearn **Isolation Forest**; train/load/predict for access-pattern scores. |
| **`fall_detection.py`** | **`FallDetector`** — Phase **rules** pipeline using MediaPipe landmarks (hip height, torso angle, velocity window). |
| **`fall_detection_trained.py`** | **`LSTMFallDetector`** — loads **`fall_lstm.keras`** + **`fall_lstm_scaler.pkl`**, sequences frames, handles partial visibility warnings. |
| **`object_detection.py`** | **`ObjectDetector`** — Ultralytics YOLO, COCO mapping, weapon fine-tuned weights path, confidence / frame thresholds, unattended timing; feeds threats/events. |
| **`__init__.py`** | Package marker / light exports if any. |
| **`isolation_forest.pkl`** | Trained anomaly model (from **`scripts/train_anomaly_detection.py`**). Optional until trained. |
| **`fall_lstm.keras`** | Trained LSTM weights for fall Phase 2. |
| **`fall_lstm_scaler.pkl`** | StandardScaler state for LSTM input. |
| **`pose_landmarker.task`** | **Download** from Google Storage (URL in [Installation](#installation-and-first-run)); save under this name even though the upstream file is named `pose_landmarker_full.task`. Required for pose-based fall pipeline and keypoint extraction. |
| **`weapon_detector.pt`** | Optional fine-tuned YOLO weights (see **`scripts/finetune_weapon_model.py`**). |
| **`yolov8n.pt`** | Base COCO weights (may download on first use). |
| **`face_encodings.npz`** | Fast startup cache of encodings (written by registration flow). |
| **`face_encodings_meta.json`** | Metadata sidecar for encodings when present. |
| **`model_info.json`** | Optional JSON with LSTM / model provenance for **`/api/fall/status`**. |
| **`lstm_eval_report.txt`** | Output from **`scripts/evaluate_lstm.py`**. |

---

### `data/` — persistence and datasets

| Path | Purpose |
|------|---------|
| **`database.py`** | All SQLite access: users, access_logs, threats, anomalies, audit_logs, behavioral_profiles, fall/object-related tables as schema evolves. Includes retention purge hooks used at startup. |
| **`data_generator.py`** | **`SyntheticDataGenerator`** — builds synthetic behavioural rows for anomaly training / demos. |
| **`__init__.py`** | Package marker. |
| **`doorface.db`** | Main SQLite file (created at runtime; typically **gitignored**). |
| **`synthetic_dataset.csv`** | Generated / committed sample data for isolation forest training. |
| **`samples/<PersonName>/`** | Registered face images (`*.jpg` / `*.png`) used by registration and fallback encoding load. |
| **`keypoints/*.csv`** | Per-video pose sequences for LSTM training (from **`scripts/extract_keypoints.py`**). |
| **`urfd/`** | Optional local folder tree for UR Fall Detection **videos** (`Fall/`, `Activities of Daily Living/`) — large; usually **not** committed. |

---

### `scripts/` — CLI utilities

| Script | Purpose |
|--------|---------|
| **`capture_faces.py`** | Interactive webcam capture into **`data/samples/<name>/`**. |
| **`register_faces.py`** | Register samples into DB + face engine; refresh **`face_encodings.npz`**; menu-driven options. |
| **`calibrate_recognition.py`** | Sweep distance thresholds on stored photos; optionally write best threshold into **`config.py`**. |
| **`quick_test_recognition.py`** | Quick accuracy / live check after registration. |
| **`diagnose_recognition.py`** | Camera, disk samples, DB, and recognition sanity diagnostics. |
| **`clear_database.py`** | Wipe DB tables while keeping **`data/samples/`** (reset demo state). |
| **`train_anomaly_detection.py`** | Regenerate synthetic data and fit **`isolation_forest.pkl`**. |
| **`extract_keypoints.py`** | Walk **`data/urfd/`** videos → MediaPipe → **`data/keypoints/*.csv`**. |
| **`train_lstm.py`** | Train **`fall_lstm.keras`** + scaler from keypoint CSVs. |
| **`evaluate_lstm.py`** | Offline evaluation → **`lstm_eval_report.txt`**. |
| **`fall_detection_camera.py`** | Live webcam: rules and/or **`--lstm`**; posts to **`POST /api/fall/log`**; CLI flags for camera index, threshold, no-display, no-api, API URL, CSV log. |
| **`finetune_weapon_model.py`** | YOLO fine-tuning for weapon-oriented classes → **`weapon_detector.pt`**. |
| **`system_health_check.py`** | Smoke-check DB paths, artifacts, and API reachability. |
| **`test_object_detection_api.py`** | Script-style tester hitting object HTTP API. |
| **`test_object_detection_camera_live.py`** | Live webcam object-detection exercise. |
| **`test_registration_flow.py`** | Registration pipeline smoke test. |
| **`__init__.py`** | Makes `scripts` a package (optional imports). |

---

### `tests/` — quality assurance

| File | Purpose |
|------|---------|
| **`test_integration.py`** | Runnable **integration + benchmark** script (`python tests/test_integration.py`). No pytest required; exercises face + anomaly + threat + DB flow. |
| **`test_facial_recognition.py`** | Recognition exercises and optional webcam modes (see file header). |
| **`test_face_recognition_real.py`** | Extended recognition scenarios (image quality, multi-face, DB alignment — see docstring). |
| **`test_api_recognize.py`** | HTTP-level tests against **`/api/recognize`** (may need server or mocks per implementation). |
| **`test_threat_detection.py`** | **`unittest`** suite: **`python -m unittest tests.test_threat_detection`**. |
| **`test_fall_detection.py`** | **`unittest`** for fall routes, descriptions, repeated-fall logic. |
| **`__init__.py`** | Package marker. |

---

### `frontend/` — Next.js dashboard

| Path | Purpose |
|------|---------|
| **`app/layout.tsx`** | Root shell: sidebar, fonts, global providers. |
| **`app/page.tsx`** | Main dashboard (KPIs, unified dashboard widgets). |
| **`app/globals.css`** | Tailwind + global styles. |
| **`app/alerts/page.tsx`** | Threat list and severity filters / summaries. |
| **`app/logs/page.tsx`** | Access logs, door summaries, registered users. |
| **`app/falls/page.tsx`** | Fall events, detector status, LSTM / visibility UI. |
| **`app/compliance/page.tsx`** | Audit table and export. |
| **`app/objects/page.tsx`** | Object detection analytics and live-style event UI. |
| **`components/`** | Reusable UI: **`Sidebar`**, **`StatCard`**, **`AccessChart`**, **`StatusDonut`**, **`AccessLogsTable`**, **`AlertList`**, **`AuditTable`**, **`PageHero`**, **`SparkMicroChart`**, **`ObjectCategoryBar`**, dashboard cards (**`UnifiedDashboard`**, **`DoorTrafficCard`**, **`CameraPipelineCard`**, **`KpiInsightModal`**, …), **`alerts/`**, **`compliance/`**, **`dashboard/`**, **`logs/`**, **`icons/`** subfolders. |
| **`lib/api.ts`** | Typed **`fetch`** wrappers for all backend routes used by pages. |
| **`lib/demoData.ts`** | Static fallback datasets for empty API responses. |
| **`lib/demoMode.ts`** | **`NEXT_PUBLIC_USE_DEMO_DATA`**, **`NEXT_PUBLIC_FORCE_DEMO_DATA`** — controls demo injection. |
| **`lib/theme.ts`** | Colours / tokens for charts and UI. |
| **`lib/timeRange.ts`** | Time-range filter for dashboard analytics. |
| **`lib/chartPrep.ts`**, **`insightChartData.ts`**, **`dashboardInsights.ts`**, **`dashboardCardSpark.ts`**, **`dashboardKpiHealth.ts`** | Data shaping for KPIs and charts. |
| **`lib/objectAnalytics.ts`** | Object-category and severity aggregations for Objects page. |
| **`lib/reportExport.ts`** | Client-side CSV / report export helpers. |
| **`next.config.ts`** | Rewrites **`/api/*`** → **`http://localhost:5001/api/*`**. |
| **`package.json`** / **`tailwind.config.ts`** / **`postcss.config.js`** | Tooling and design system. |

---

### `dashboard/` — legacy HTML prototype

Static **`templates/index.html`** plus **`static/css`**, **`static/js`** — early or alternate UI. The **primary** operator UI is **`frontend/`** (Next.js). Keep this folder for reference or screenshots unless you remove it deliberately.

---

### `docs/` — technical writing

| Document | Typical contents |
|----------|------------------|
| **`API_DOCS.md`** | REST contract details and examples. |
| **`ARCHITECTURE.md`** | System design narrative. |
| **`COMPLIANCE.md`** | Privacy / audit / retention discussion. |
| **`DEPLOYMENT.md`** | Deployment notes. |
| **`SECURITY.md`** | Security considerations. |
| **`TRAINING_GUIDE.md`** | ML training procedures. |
| **`GET_STARTED.md`**, **`START_HERE.md`** | Onboarding. |
| **`FACIAL_RECOGNITION_*.md`**, **`README_FACIAL_RECOGNITION.md`**, **`SOLUTION_SUMMARY.md`**, **`FACIAL_RECOGNITION_STATUS.md`** | Face pipeline history and how-tos. |

---

### `screenshots/`

PNG captures used in README figures (`dashboard.png`, `alerts.png`, etc.). Update when UI changes significantly.

---

## Installation and first run

### Prerequisites

- **Python 3.11+**
- **Node.js 18+** and npm
- Webcam optional (capture, fall camera, live object tests)

### Python dependencies

```bash
cd Implementation
pip install -r requirements.txt
```

Optional higher-accuracy face path (requires **CMake** + **dlib** build chain; on Windows use **Visual Studio Build Tools**):

```bash
pip install face_recognition
```

### MediaPipe pose model (fall detection)

Download into **`models/`** (one-time):

```bash
# macOS / Linux
curl -L -o models/pose_landmarker.task \
  "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_full/float16/1/pose_landmarker_full.task"
```

```powershell
# Windows PowerShell
Invoke-WebRequest -Uri "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_full/float16/1/pose_landmarker_full.task" -OutFile "models\pose_landmarker.task"
```

If a script expects a slightly different filename, rename to match the path in **`fall_detection.py`** / **`extract_keypoints.py`** or set the constant there.

### Run Flask

```bash
# Default: http://127.0.0.1:5001
python main.py
```

```powershell
$env:FLASK_PORT = "5001"
python main.py
```

### Run Next.js (second terminal)

```bash
cd frontend
npm install   # first time only
npm run dev
```

Open **http://localhost:3000**. All browser calls to **`/api/...`** are proxied to Flask on **5001** per **`frontend/next.config.ts`**.

---

## Environment variables

| Variable | Effect |
|----------|--------|
| **`FLASK_HOST`** | Bind address (default from code, often `0.0.0.0`). |
| **`FLASK_PORT`** | Listen port (default **5001** in `main.py`). |
| **`FLASK_ENV`** | If `development`, enables Flask debug flag path in `main.py`. |
| **`SECRET_KEY`** | Flask secret (override in production). |
| **`ENCRYPTION_KEY`** | Passphrase used to derive Fernet key for stored encodings. |
| **`DATA_RETENTION_DAYS`** | Retention for purged rows at startup. |
| **`FALL_DETECTOR_MODE`** | `rules` or `lstm` (also settable in **`config.py`**). |
| **`FALL_CONFIDENCE_THRESHOLD`**, **`FALL_VELOCITY_WINDOW`**, **`FALL_COOLDOWN_FRAMES`** | Override fall tuning without editing files. |
| **`OBJECT_*`** | See **`config.py`** — confidence, frame threshold, unattended minutes, model paths. |
| **`NEXT_PUBLIC_USE_DEMO_DATA`** | If `false`, disables demo fill for empty lists (frontend). |
| **`NEXT_PUBLIC_FORCE_DEMO_DATA`** | If `true`, forces demo datasets in UI. |

---

## Operational workflows

### Register faces

```bash
python scripts/capture_faces.py
python scripts/register_faces.py
```

Then call **`POST /api/recognize`** with a base64 JPEG/PNG from your door client, or use test scripts.

### Live fall detection (camera → API → dashboard)

1. Start **`python main.py`**
2. **`python scripts/fall_detection_camera.py`** (rules) or **`python scripts/fall_detection_camera.py --lstm`**
3. Open **`/falls`** on the dashboard

Rules mode uses weighted hip / torso / velocity scores; LSTM mode uses a rolling window of normalised landmarks.

### LSTM retraining (advanced)

1. Place URFD (or custom) videos under **`data/urfd/Fall/`** and **`data/urfd/Activities of Daily Living/`**
2. **`python scripts/extract_keypoints.py`**
3. **`python scripts/train_lstm.py`**
4. **`python scripts/evaluate_lstm.py`**
5. Deploy new **`fall_lstm.keras`** / scaler; set **`FALL_DETECTOR_MODE=lstm`** if the server should use LSTM in **`POST /api/fall/detect`**

### Object detection

- Ensure **`ultralytics`** installed and weights available (**`yolov8n.pt`** and/or **`weapon_detector.pt`**).
- Use **`POST /api/objects/detect`** with frame payload per **`docs/API_DOCS.md`**.
- **`scripts/finetune_weapon_model.py`** for custom weapon-class fine-tuning.

### Anomaly model

```bash
python scripts/train_anomaly_detection.py
```

Produces / refreshes **`models/isolation_forest.pkl`** using synthetic and/or stored patterns.

---

## REST API reference

Base URL: **`http://localhost:5001`** (or your `FLASK_PORT`).  
JSON unless noted. **`/api/recognize`** expects a **`frame`** field (base64 image).

### Core (`routes.py` — prefix `/api`)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Liveness payload. |
| GET | `/api/recognition/status` | Engine mode (dlib vs OpenCV), counts, thresholds. |
| POST | `/api/recognize` | Detect and identify all faces; log access; run threat/anomaly hooks. |
| POST | `/api/log-access` | Manually log an access row. |
| GET | `/api/threats` | Active / recent threats. |
| GET | `/api/users` | Registered users list. |
| DELETE | `/api/users/<user_id>` | Remove a user (audited). |
| GET | `/api/logs` | Paginated access log. |
| GET | `/api/stats` | Aggregate KPIs for dashboard. |
| GET | `/api/compliance/audit` | Audit log entries (+ export patterns if implemented). |

### Fall (`fall_detection_routes.py` — prefix `/api/fall`)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/fall/detect` | Run detector on base64 frame on server. |
| GET | `/api/fall/status` | Mode, artifact presence, cooldown / model metadata. |
| GET | `/api/fall/events` | Recent fall-related anomaly rows. |
| POST | `/api/fall/reset` | Reset internal detector state. |
| POST | `/api/fall/log` | Idempotent log of client-side detection (used by camera script). |

### Objects (`object_detection_routes.py` — prefix `/api/objects`)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/objects/detect` | Run YOLO on frame; update threats / events. |
| GET | `/api/objects/status` | Detector readiness and config. |
| GET | `/api/objects/events` | Recent object events for dashboard. |

For request/response schemas and edge cases, see **`docs/API_DOCS.md`**.

---

## Dashboard routes

| URL | Page |
|-----|------|
| `/` | Main KPI dashboard |
| `/alerts` | Threat feed |
| `/logs` | Access log + door summary |
| `/falls` | Fall history + detector status |
| `/compliance` | Audit trail + CSV export |
| `/objects` | Object detections and analytics |

**Demo behaviour:** When APIs return empty lists or null aggregates, **`lib/demoMode.ts`** may inject realistic placeholder data so the UI stays demonstrable, unless disabled via **`NEXT_PUBLIC_USE_DEMO_DATA=false`**.

---

## Configuration (`config.py`)

Key symbols (see file for full list and defaults):

| Symbol | Role |
|--------|------|
| **`DATABASE_PATH`** | SQLite file path under `data/`. |
| **`FACE_CONFIDENCE_THRESHOLD`**, **`FACE_DETECTION_*`** | Face pipeline tuning. |
| **`FAILED_ATTEMPT_THRESHOLD`**, **`FAILED_ATTEMPT_WINDOW_MINUTES`**, **`INACTIVITY_THRESHOLD_HOURS`**, **`UNUSUAL_TIME_HOURS`** | Threat rules. |
| **`ANOMALY_SCORE_THRESHOLD`**, **`ISOLATION_FOREST_*`** | Anomaly detector. |
| **`DATA_RETENTION_DAYS`**, **`ENABLE_AUDIT_LOGGING`** | Compliance / retention. |
| **`FALL_DETECTOR_MODE`**, **`FALL_CONFIDENCE_THRESHOLD`**, **`FALL_VELOCITY_WINDOW`**, **`FALL_COOLDOWN_FRAMES`** | Fall stack. |
| **`OBJECT_DETECTION_CONFIDENCE`**, **`OBJECT_DETECTION_FRAME_THRESHOLD`**, **`OBJECT_UNATTENDED_MINUTES`**, **`OBJECT_WEAPON_MODEL_PATH`**, **`OBJECT_BASE_MODEL`** | Object stack. |

Rule-specific numeric thresholds for the **rules** fall detector (hip height, torso angle, velocity) live at the top of **`models/fall_detection.py`** — adjust there for fine physics tuning.

---

## Compliance and privacy

- Processing is designed for **on-prem / local** deployment: no cloud requirement in the default code path.
- **`audit_logs`** captures security-relevant actions for review on **`/compliance`**.
- Face images remain under **`data/samples/`**; biometric encodings may be cached in **`models/face_encodings.npz`** with encryption helpers in **`facial_recognition.py`** — treat these as sensitive.
- Read **`docs/COMPLIANCE.md`** for narrative suitable for reports and instructors.

---

## Evaluation and testing

From **`Implementation/`**:

```bash
# Integration + latency-style checks (prints to stdout)
python tests/test_integration.py

# Unittest modules
python -m unittest tests.test_threat_detection
python -m unittest tests.test_fall_detection

# Recognition suites (see each file for webcam / API requirements)
python tests/test_facial_recognition.py
python scripts/quick_test_recognition.py
python scripts/diagnose_recognition.py
python scripts/system_health_check.py
```

If you adopt **pytest** project-wide, you can additionally run `pytest tests/ -q` once tests are standardised on pytest conventions.

---

## Troubleshooting

| Symptom | Things to check |
|---------|-------------------|
| **502 / failed fetch from Next** | Flask not running; wrong **`FLASK_PORT`**; **`next.config.ts`** destination must match. |
| **OpenCV errors under load** | `main.py` uses **`threaded=False`** intentionally — avoid hammering the API with parallel heavy requests during demos. |
| **Fall script cannot start** | Missing **`pose_landmarker.task`**; wrong working directory. |
| **LSTM mode fails** | Missing **`fall_lstm.keras`** / **`fall_lstm_scaler.pkl`**; check **`/api/fall/status`** for artifact flags. |
| **`face_recognition` install fails on Windows** | Install **Visual Studio Build Tools (C++)**, then `pip install cmake dlib` before `face_recognition`. System works without it using OpenCV path. |
| **Empty dashboard** | Seed DB or enable demo env vars; register faces with scripts. |
| **YOLO download slow** | First run downloads **`yolov8n.pt`**; ensure disk space and network. |

---

## Course context

**Douglas College — CSIS 4495 Applied Research.**  
Winter 2026 — FaceDoor / Door Face Panels industry collaboration.

For repository-wide submission paths (slides, reports), see the parent **`README.md`** at the repo root and the **`ReportsAndDocuments/`** folder.
