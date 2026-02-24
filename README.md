# FaceDoor — Smart Door Security System

**Douglas College CSIS 4495 — Applied Research Project (Section 003)**  
Team: Advitiya Sharda, Eric Sanjo, Reubin Chatta  
Industry Partner: Door Face Panels — Armin Ghauforian

---

## What This Project Does

FaceDoor is a smart door security system designed for elderly care facilities. A camera at the door recognises residents and staff by face, logs every entry and exit event, and shows caregivers everything on a live web dashboard. When an unknown person appears or something unusual happens, the system generates a security alert.

The project has two main parts that run together:

- **Backend (Flask + Python)** — handles face recognition, stores access logs in a local SQLite database, and exposes a REST API
- **Frontend (Next.js)** — a caregiver dashboard that reads from the API and refreshes automatically every 30 seconds

Everything runs locally. No data is sent to the cloud.

---

## What the Dashboard Shows

| Page | URL | What you see |
|---|---|---|
| Dashboard | `http://localhost:3000/` | KPI cards (total entries, denials, active alerts), hourly bar chart, access outcome donut chart, recent access log |
| Alerts | `http://localhost:3000/alerts` | Security alert cards, filterable by severity (High / Critical) |
| Access Logs | `http://localhost:3000/logs` | Full paginated access log with entry/exit and status badges; registered people list |
| Audit Trail | `http://localhost:3000/compliance` | System audit log for compliance; CSV export |

If no one has been registered yet, the dashboard shows realistic demo data with a visible "Demo data" label so the UI is always presentable.

---

## System Requirements

| Tool | Version | Where to get it |
|---|---|---|
| Python | 3.10 or newer | https://www.python.org/downloads |
| Node.js | 18 LTS or newer | https://nodejs.org/en/download |
| npm | comes with Node.js | — |
| Webcam | any USB or built-in | required for face capture |

A webcam is only needed if you want to register real faces or run the live recognition test. The dashboard and API work without one.

---

## Installation

Clone the repository if you have not already:

```bash
git clone https://github.com/advitiyasharda/W26_4495_S3_AdvitiyaS.git
cd W26_4495_S3_AdvitiyaS
```

### Step 1 — Install Python dependencies

Run this from the **project root** (the folder that contains `main.py`):

```bash
pip install -r requirements.txt
```

On some machines you may need `pip3` instead of `pip`. If you are on Windows, use Command Prompt or PowerShell (not Git Bash) for best results.

### Step 2 — Install frontend dependencies

This only needs to be done once:

```bash
cd frontend
npm install
cd ..
```

---

## Running the Project

You need **two terminals open at the same time** — one for the backend and one for the frontend.

### Terminal 1 — Start the backend

Run from the **project root**:

```bash
FLASK_PORT=5001 python3 main.py
```

On Windows (Command Prompt):

```cmd
set FLASK_PORT=5001 && python main.py
```

On Windows (PowerShell):

```powershell
$env:FLASK_PORT=5001; python main.py
```

The API will be available at `http://localhost:5001`. You should see output like:

```
* Running on http://127.0.0.1:5001
```

### Terminal 2 — Start the frontend

Run from the **frontend folder**:

```bash
cd frontend
npm run dev
```

The dashboard will be available at `http://localhost:3000`.

Open that URL in a browser. If the backend is running, the dashboard will show live data. If not, it will show demo data automatically.

---

## Registering Faces (to use real recognition)

To see the system recognise a real person, you need to register them first. Run both of the following from the **project root**:

```bash
# Step 1: capture photos from your webcam
python3 scripts/capture_faces.py

# Step 2: load those photos into the database
python3 scripts/register_faces.py
```

You will be prompted to enter a name. The system takes several photos, extracts facial features, and saves them under `data/samples/<name>/`. Once registered, that person will be recognised when their face appears in a frame sent to `/api/recognize`.

---

## Seeing a Live Demo

The quickest way to see the full system in action:

1. Start the backend in Terminal 1 (`FLASK_PORT=5001 python3 main.py`)
2. Start the frontend in Terminal 2 (`cd frontend && npm run dev`)
3. Open `http://localhost:3000` in a browser
4. If no faces are registered, the dashboard shows demo data — you can explore all four pages
5. To see real recognition, register a face (steps above) then run the webcam test:

```bash
python3 tests/test_face_recognition_real.py
```

This opens a webcam window, detects faces in real time, and prints recognition results to the terminal. A summary of total frames, detected faces, and recognition rate is shown when you press `q` to quit.

---

## Port Configuration

The backend is set to run on port **5001** (not Flask's default 5000) to avoid conflicts. The frontend is already configured to proxy all API calls to port 5001 via `frontend/next.config.ts`.

If you need to change the port:

1. Set the environment variable to your chosen port when starting the backend:  
   `FLASK_PORT=5002 python3 main.py`

2. Update the destination in `frontend/next.config.ts`:

```ts
destination: 'http://localhost:5002/api/:path*',
```

Both must match, otherwise the frontend will not be able to reach the backend.

---

## API Endpoints

The backend exposes the following REST endpoints. All are prefixed with `/api`.

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Check if the server is running |
| POST | `/recognize` | Submit a base64 image frame for face recognition |
| GET | `/logs` | Retrieve access logs (supports `limit` and `offset` query params) |
| GET | `/threats` | Retrieve active security alerts |
| GET | `/stats` | System statistics (total events, active threats, registered users) |
| GET | `/users` | List registered users |
| DELETE | `/users/<id>` | Remove a registered user |
| GET | `/compliance/audit` | Full system audit log |

Example — check the server is up:

```bash
curl http://localhost:5001/api/health
```

Example — get the 10 most recent access logs:

```bash
curl "http://localhost:5001/api/logs?limit=10"
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
|   |-- routes.py                  # All REST API route handlers
|   |-- facial_recognition.py      # Face detection and matching engine (OpenCV)
|   `-- threat_detection.py        # Rules-based threat detection class
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
|   `-- isolation_forest.pkl       # Trained model file (generated by training script)
|
|-- frontend/                      # Next.js web application
|   |-- app/
|   |   |-- page.tsx               # Main dashboard page
|   |   |-- alerts/page.tsx        # Alerts page
|   |   |-- logs/page.tsx          # Access logs page
|   |   `-- compliance/page.tsx    # Audit trail page
|   |-- components/
|   |   |-- Sidebar.tsx
|   |   |-- StatCard.tsx
|   |   |-- AccessChart.tsx
|   |   |-- StatusDonut.tsx
|   |   |-- AccessLogsTable.tsx
|   |   |-- AlertList.tsx
|   |   |-- AuditTable.tsx
|   |   `-- StatusBadge.tsx
|   |-- lib/
|   |   |-- api.ts                 # Typed API client (all fetch calls go here)
|   |   `-- demoData.ts            # Fallback demo data when DB is empty
|   |-- next.config.ts             # API proxy configuration (port 5001)
|   `-- package.json
|
|-- scripts/
|   |-- capture_faces.py           # Capture face photos from webcam
|   |-- register_faces.py          # Load photos into the recognition engine and DB
|   |-- clear_database.py          # Wipe the database without deleting sample photos
|   |-- diagnose_recognition.py    # Diagnostic tool — checks camera, samples, DB, recognition
|   |-- quick_test_recognition.py  # Quick photo-based recognition test
|   `-- train_anomaly_detection.py # Train the Isolation Forest model on synthetic data
|
|-- tests/
|   |-- test_api_recognize.py         # API-level recognition test using live webcam
|   |-- test_face_recognition_real.py # Extended webcam test with per-frame statistics
|   |-- test_facial_recognition.py    # Unit tests for the recognition engine
|   `-- test_integration.py           # End-to-end pipeline test
|
`-- dashboard/                     # Original HTML/CSS prototype (kept for reference)
```

---

## Troubleshooting

**The dashboard shows "Demo data" even though I registered faces**  
Make sure the backend is running before opening the dashboard. The frontend falls back to demo data when it cannot reach `localhost:5001`.

**Recognition is not working or always returns "Unknown"**  
Run the diagnostics script from the project root:

```bash
python3 scripts/diagnose_recognition.py
```

This checks whether the camera is accessible, whether sample photos were loaded correctly, whether samples from different people are visually distinct enough, and whether the database is reachable.

**Backend fails to start with "Address already in use"**  
Another process is using port 5001. Either stop that process or change the port as described in the Port Configuration section above.

**"Module not found" errors when starting the backend**  
Make sure you ran `pip install -r requirements.txt` from the project root and that you are using the same Python environment where you installed the packages.

**Frontend fails with "npm: command not found"**  
Node.js is not installed or is not on your PATH. Download it from https://nodejs.org and restart your terminal after installing.

---

## Compliance Notes

All face data is processed and stored on the local machine. No images or personal data are uploaded to any external server. The audit log records every system action (access granted, access denied, user registered, user deleted) with a timestamp and actor identifier. This supports accountability requirements under PIPEDA (Canada) and similar privacy frameworks.

---

*CSIS 4495 Applied Research Project — Douglas College, Winter 2026*
