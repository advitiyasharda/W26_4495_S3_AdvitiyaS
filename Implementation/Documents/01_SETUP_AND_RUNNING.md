# Setup & Running Guide

## Prerequisites

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| Python | 3.10 | 3.11 |
| Node.js | 18 LTS | 20 LTS |
| npm | 9+ | bundled with Node |
| OS | Windows 10 / macOS 12+ / Ubuntu 20+ | macOS or Ubuntu |
| Camera | Any USB/built-in webcam | 720p+ |
| RAM | 4 GB | 8 GB (LSTM needs ~2 GB) |
| Disk | 3 GB free | 5 GB (includes YOLO weights) |

---

## Option A — One-Click Start (Recommended)

The `start.py` script handles everything: creates a virtual environment, installs Python and Node packages, then lets you choose what to launch.

```bash
# From the project root
python Implementation/start.py
```

On first run it will:
1. Create `Implementation/venv/`
2. Install all Python packages from `requirements.txt`
3. Install all npm packages (and download the MediaPipe pose model)
4. Ask you: Backend only / Frontend only / Both / Exit

**Subsequent runs** skip the install steps if dependencies are already present and go straight to the launch menu.

> **Windows note:** Run from a terminal that supports ANSI colour (Windows Terminal or VS Code terminal). PowerShell and cmd work but look plain.

---

## Option B — Manual Setup

### 1. Python virtual environment

```bash
cd Implementation

# Create venv
python -m venv venv

# Activate
# macOS / Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Frontend dependencies

```bash
cd Implementation/frontend
npm install
```

This also runs a `postinstall` script (`scripts/download-pose-model.mjs`) that downloads `pose_landmarker.task` (~25 MB) into `public/models/`. Requires internet on first run.

### 3. Start the backend

```bash
# From Implementation/ with venv active
python main.py
```

Flask starts on **http://localhost:5001**

### 4. Start the frontend

```bash
# From Implementation/frontend/
npm run dev
```

Next.js starts on **http://localhost:3000**

---

## Port Reference

| Service | URL | Notes |
|---------|-----|-------|
| Flask API | http://localhost:5001 | Backend; do not change without updating `next.config.ts` |
| Next.js dashboard | http://localhost:3000 | Frontend; proxies `/api/*` → Flask |

The frontend proxy is defined in `Implementation/frontend/next.config.ts`:

```typescript
rewrites: async () => [
  { source: "/api/:path*", destination: "http://localhost:5001/api/:path*" }
]
```

If you change the Flask port, update **both** `main.py` and `next.config.ts`.

---

## Face Enrollment

Faces must be enrolled before recognition works.

### Quick enrollment via Demo Center (UI)

1. Start both backend and frontend
2. Navigate to http://localhost:3000/demo
3. Enter the person's ID, name, and role
4. Click **Start** next to "Face registration capture"
5. The webcam opens — look at the camera; 40 photos are captured automatically
6. Registration reloads automatically when done

### Manual enrollment

```bash
cd Implementation
# Capture 40 photos for "John" with ID "john_001"
python scripts/capture_faces.py \
  --person john \
  --photos 40 \
  --register-now \
  --person-id john_001 \
  --display-name "John Smith" \
  --role resident \
  --reload-api-url http://localhost:5001
```

Captured photos are saved to `data/samples/john/`.

### How the engine loads faces

At startup, `create_app()` scans `data/samples/` and matches each folder name to a database user by `user_id` or normalised name. Any folder that does not match a DB user is skipped with a warning. After adding new photos you can force a live reload without restarting Flask:

```bash
curl -X POST http://localhost:5001/api/recognition/reload
```

---

## Running the Detection Scripts (Live Camera)

These are standalone scripts that send frames or results to the Flask API.

### Fall detection

```bash
cd Implementation
python scripts/fall_detection_camera.py
```

Opens a webcam window. Falls are displayed in red overlay and POSTed to `/api/fall/log`. Press **q** to quit.

### Object detection

```bash
cd Implementation
python scripts/test_object_detection_camera_live.py \
  --base-model yolo26l.pt \
  --post-api-url http://127.0.0.1:5001 \
  --api-every 3
```

Press **q** to quit.

### Face recognition test

```bash
cd Implementation
python tests/test_api_recognize.py --continuous
```

---

## Optional: LSTM Fall Detector (Phase 2)

By default the system uses the rules-based Phase 1 fall detector. To enable the trained LSTM model:

```bash
# Set in your shell before starting Flask
export FALL_DETECTOR_MODE=lstm
python main.py
```

Or on Windows:
```cmd
set FALL_DETECTOR_MODE=lstm
python main.py
```

Required model files (must exist in `models/`):
- `fall_lstm.keras`
- `fall_lstm_scaler.pkl`

To train from scratch:
```bash
# First extract keypoints from UR Fall Detection dataset CSVs
python scripts/extract_keypoints.py

# Then train
python scripts/train_lstm.py
```

---

## Optional: dlib / face_recognition (Better Face Accuracy)

The default engine uses OpenCV Haar cascades. For significantly better accuracy install the `face_recognition` package (requires dlib):

```bash
# macOS (with Xcode command-line tools)
pip install face_recognition

# Ubuntu
sudo apt install cmake libopenblas-dev
pip install face_recognition

# Windows — see dlib docs for pre-built wheels
```

The engine auto-detects `face_recognition` at startup and switches to dlib mode. Check the mode:

```bash
curl http://localhost:5001/api/recognition/status
```

---

## Demo Mode (No Camera Needed)

Demo mode fills all dashboard visualisations with synthetic data, useful for presentations or testing the UI without a running backend.

- **Toggle:** Click the purple/grey toggle next to the admin name in the sidebar
- **Default:** ON (purple) on first visit
- **Behaviour when ON:** All pages show synthetic demo data, even if the backend is running with real data
- **Behaviour when OFF:** Shows real API data; shows empty states if backend is not running

Demo state is stored in `localStorage["facedoor_demo_mode"]`.

---

## Health Check

```bash
curl http://localhost:5001/api/health
# → {"status": "healthy", "timestamp": "...", "version": "0.1.0"}
```

Full system health (models, DB, camera):
```bash
cd Implementation
python scripts/system_health_check.py
```
