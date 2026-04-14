# FaceDoor — Smart Door Security System

**Douglas College — CSIS 4495 Applied Research (Section 003)**  
**Team:** Advitiya Sharda, Eric Sanjo, Reubin Chatta  
**Industry partner:** Door Face Panels — Armin Ghauforian

---

## For instructors and markers

| What | Where |
|------|--------|
| **Runnable application** | `Implementation/` — Flask API, Next.js dashboard, ML models, scripts, and automated tests |
| **Slides, progress reports, and written docs** | `ReportsAndDocuments/` — PDFs and supporting markdown (per course check-in expectations) |
| **Extended technical README** | `Implementation/README.md` — architecture diagram, full endpoint list, script catalogue |
| **Compliance write-up** | `Implementation/docs/COMPLIANCE.md` |
| **Ongoing work history** | Git `main` branch history and merged pull requests (see **Team contributions** below). Progress reports are under `ReportsAndDocuments/`. |

**Quick verify (from repo root):**

```powershell
cd Implementation
pip install -r requirements.txt
# Terminal 1
$env:FLASK_PORT=5001; python main.py
# Terminal 2
cd frontend; npm install; npm run dev
```

Open **http://localhost:3000**. The frontend proxies `/api/*` to the Flask port (default **5001**).

---

## What this project does

FaceDoor is a smart door security system for elderly care: a camera identifies people at the door, logs access, raises **threat** alerts (failed attempts, unusual hours, tailgating, and more), supports **behavioural anomaly** scoring (Isolation Forest), **fall detection** (rules-based and LSTM on pose sequences), and **object / weapon-aware** monitoring (YOLO). A **Next.js** dashboard presents KPIs, alerts, falls, access logs, compliance audit export, and object analytics. **All processing is local** (no cloud upload of video or face biometrics in the default design).

---

## Repository layout

```text
W26_4495_S3_AdvitiyaS/
├── README.md                 ← This file (course + team + how to run)
├── Implementation/          ← Application source, tests, and Implementation/README.md
├── ReportsAndDocuments/     ← Slides, progress reports, duplicated docs for submission
└── …
```

All commands in this README assume you start from the **repository root**, then `cd Implementation` unless noted otherwise.

---

## System requirements

| Tool | Notes |
|------|--------|
| Python **3.11+** | Used by Flask, OpenCV, MediaPipe, scikit-learn, optional `face_recognition` |
| Node.js **18+** | For `Implementation/frontend` |
| Webcam | Optional: face capture, live fall script, live object tests |

**Windows:** building `dlib` / `face_recognition` may require **Visual Studio Build Tools**. If install fails: `pip install cmake` then `pip install dlib` then `pip install face_recognition`.

---

## Installation (first time)

```powershell
git clone https://github.com/advitiyasharda/W26_4495_S3_AdvitiyaS.git
cd W26_4495_S3_AdvitiyaS\Implementation
pip install -r requirements.txt
```

**MediaPipe pose model (fall detection):** one-time download — see `Implementation/README.md` for the exact `curl` command into `Implementation/models/pose_landmarker.task`.

```powershell
cd frontend
npm install
```

---

## Running the project

Use **two terminals** for dashboard + API.

**Terminal 1 — backend (from `Implementation/`):**

```powershell
cd W26_4495_S3_AdvitiyaS\Implementation
$env:FLASK_PORT=5001
python main.py
```

**Terminal 2 — frontend:**

```powershell
cd W26_4495_S3_AdvitiyaS\Implementation\frontend
npm run dev
```

Browser: **http://localhost:3000**

**Optional third process — live fall camera** (from `Implementation/`):

```powershell
python scripts/fall_detection_camera.py
# or LSTM mode:
python scripts/fall_detection_camera.py --lstm
```

---

## Dashboard routes

| Page | URL |
|------|-----|
| Dashboard | http://localhost:3000/ |
| Alerts | http://localhost:3000/alerts |
| Access logs | http://localhost:3000/logs |
| Falls | http://localhost:3000/falls |
| Compliance / audit | http://localhost:3000/compliance |
| Objects | http://localhost:3000/objects |

If the database is empty, the UI can show labelled **demo** data (see `Implementation/frontend/lib/demoMode.ts` and env vars documented in `Implementation/README.md`).

---

## Registering faces (real recognition)

From `Implementation/`:

```powershell
python scripts/capture_faces.py
python scripts/register_faces.py
```

Optional threshold tuning:

```powershell
python scripts/calibrate_recognition.py
```

---

## Evaluation and tests

Run from **`Implementation/`** (all paths below are relative to that folder):

```powershell
cd Implementation   # from repository root

# End-to-end integration + benchmark (no prompts)
python tests/test_integration.py

# Unit tests (stdlib unittest)
python -m unittest tests.test_threat_detection
python -m unittest tests.test_fall_detection

# Optional: recognition script tests / webcam (see file docstrings)
python tests/test_facial_recognition.py
python scripts/system_health_check.py
```

Fall LSTM pipeline, metrics, and optional **pytest** invocations are documented in **`Implementation/README.md`**.

---

## Team contributions (from Git history and merged PRs)

The bullets below summarize **authored commits and merged feature branches** on this repository (work may also appear in progress PDFs under `ReportsAndDocuments/`). Approximate **non-merge commit** totals from `git log --all --no-merges`: **Advitiya ~54**, **Eric ~38**, **Reubin ~27** (author names vary slightly by machine, e.g. `Eric` vs `Eric Sanjo`).

### Advitiya Sharda

- **Facial recognition and API:** major work on `Implementation/api/facial_recognition.py`, `routes.py`, and app factory `api/__init__.py` — including multi-face handling, **face quality** scoring, **RecognitionBuffer** smoothing for stable `/api/recognize` results, and registration integration (`register_faces.py`, `capture_faces.py`, `calibrate_recognition.py`).
- **Data and threats:** substantive edits to `Implementation/data/database.py`, `Implementation/api/threat_detection.py`, and related tests (`test_facial_recognition.py`, `test_face_recognition_real.py`).
- **Dashboard and analytics:** unified dashboard wiring (`UnifiedDashboard.tsx`, KPI/chart libs, demo mode utilities), integration of **object-detection** backend pieces in collaboration with teammates, and repository hygiene (e.g. stopping tracking of local biometric artifacts, `.gitignore` updates).
- **Merged PRs (examples):** `week11_advitiya`, `advitiya_week12`, `advitiya_week14` (see merge commits on `main`).

### Eric Sanjo

- **Fall detection (core research track):** Phase 1 **MediaPipe** rules-based detector, live **`fall_detection_camera.py`**, Flask **`/api/fall/*`** routes, logging and **repeated-fall** escalation, partial-body **visibility** handling, fall timestamps and **stats** alignment with the dashboard.
- **Phase 2 LSTM:** URFD **keypoint extraction** pipeline, **LSTM training** and **`fall_lstm.keras`** integration, configurable **`FALL_DETECTOR_MODE`** (rules vs LSTM) with safe fallback in `api/__init__.py`, extended **`/api/fall/status`** metadata.
- **Documentation and earlier ML:** API and facial-recognition documentation updates (`Implementation/docs/`, `ReportsAndDocuments/docs/`), **anomaly detection** training integration, improvements to early **face recognition** and **`routes.py`** / **`database.py`**.
- **Frontend/API touches:** fall-related **`frontend/lib/api.ts`** and dashboard page updates where tied to backend contracts; **CSV export** improvements across dashboard pages where implemented.
- **Merged PRs (examples):** `ericv1` … `ericv5` (see merge commits on `main`).

### Reubin Chatta

- **Object detection (Phase 3):** `Implementation/models/object_detection.py`, **`api/object_detection_routes.py`** registration, **YOLOv8** configuration and requirements, **fine-tuning** script for weapon-oriented classes, **API and live webcam test scripts** under `Implementation/scripts/`.
- **Frontend UX:** large **App Router** updates — **`layout.tsx`**, **`globals.css`**, **`Sidebar.tsx`**, revamps of **alerts**, **compliance**, **logs**, **falls**, **`objects`**, and the **home** dashboard; KPI cards, animated visuals, door summaries, and alert severity summaries; collaboration on shared dashboard components (e.g. `UnifiedDashboard`, modal and traffic cards).
- **Merged PRs (examples):** `Reubin`, `reubinv2`, `reubinv3`, `reubinv4` (see merge commits on `main`).

*To reproduce contributor statistics locally:*

```powershell
cd W26_4495_S3_AdvitiyaS
git shortlog -sne --all
git log --all --merges --oneline
```

---

## Threat rules (summary)

| Pattern | Typical severity |
|---------|------------------|
| Unrecognised face | HIGH |
| Repeated failed access | HIGH |
| Unusual time window | MEDIUM |
| Tailgating / wandering (as implemented) | HIGH |
| Fall detected | CRITICAL |
| Repeated falls (24h window) | HIGH → CRITICAL |

Full tables: **`Implementation/README.md`**.

---

## Ports

- Flask default in this project: **5001** (see `Implementation/main.py` / env `FLASK_PORT`).
- Next.js dev server: **3000**; proxy target in `Implementation/frontend/next.config.ts` must match Flask.

---

## Licence / course context

Course project for **CSIS 4495 — Applied Research**, Douglas College, **Winter 2026**. Not a commercial release; configure secrets and retention appropriately before any real deployment.
