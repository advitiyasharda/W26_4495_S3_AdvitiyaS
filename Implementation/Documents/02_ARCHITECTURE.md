# System Architecture

## Overview

FaceDoor is a two-process application: a **Python Flask backend** (port 5001) and a **Next.js frontend** (port 3000). The frontend proxies all `/api/*` requests to Flask, so the browser only ever talks to one origin.

---

## Process Architecture

```
                        ┌─────────────────────────────┐
                        │    Browser / Dashboard       │
                        │    http://localhost:3000     │
                        └──────────────┬───────────────┘
                                       │ /api/* (proxied)
                        ┌──────────────▼───────────────┐
                        │    Next.js Server            │
                        │    npm run dev / npm start   │
                        │    Implementation/frontend/  │
                        └──────────────┬───────────────┘
                                       │ http://localhost:5001/api/*
                        ┌──────────────▼───────────────┐
                        │    Flask API                 │
                        │    python main.py            │
                        │    Implementation/           │
                        │    • routes.py               │
                        │    • fall_detection_routes   │
                        │    • object_detection_routes │
                        └──────────────┬───────────────┘
                                       │
                     ┌─────────────────┼──────────────────┐
                     │                 │                  │
           ┌─────────▼──────┐ ┌───────▼──────┐ ┌────────▼───────┐
           │  FaceEngine    │ │ FallDetector │ │ ObjectDetector │
           │ (OpenCV/dlib)  │ │ (MediaPipe + │ │ (YOLO26l +     │
           │                │ │  LSTM opt.)  │ │  weapon model) │
           └────────────────┘ └──────────────┘ └────────────────┘
                     │                 │                  │
                     └─────────────────┼──────────────────┘
                                       │
                        ┌──────────────▼───────────────┐
                        │    SQLite Database           │
                        │    data/doorface.db          │
                        └──────────────────────────────┘
```

---

## Directory Layout

```
Implementation/
├── main.py                         Flask entry point (create_app, port 5001)
├── start.py                        One-click launcher
├── config.py                       All thresholds and env overrides
├── requirements.txt
│
├── api/
│   ├── __init__.py                 create_app(): wires all components
│   ├── routes.py                   Main blueprint: /api/*
│   ├── fall_detection_routes.py    /api/fall/*
│   ├── object_detection_routes.py  /api/objects/*
│   ├── facial_recognition.py       FacialRecognitionEngine + RecognitionBuffer
│   └── threat_detection.py         Rules-based ThreatDetector
│
├── models/
│   ├── fall_detection.py           Phase 1: rules-based FallDetector
│   ├── fall_detection_trained.py   Phase 2: LSTMFallDetector
│   ├── anomaly_detection.py        IsolationForest + BehavioralProfiler
│   ├── object_detection.py         ObjectDetector wrapping YOLO26
│   ├── pose_landmarker.task        MediaPipe model file (~29 MB)
│   ├── fall_lstm.keras             Trained LSTM weights
│   ├── fall_lstm_scaler.pkl        StandardScaler for LSTM input
│   ├── isolation_forest.pkl        Trained anomaly model
│   └── model_info.json             LSTM training metadata
│
├── data/
│   ├── database.py                 Database class, all SQL
│   ├── data_generator.py           Synthetic training data
│   ├── doorface.db                 SQLite database (live)
│   ├── samples/                    Face enrollment photos
│   │   ├── Eric/
│   │   ├── Reubin/
│   │   ├── advitiya/
│   │   ├── armin/
│   │   └── person_test/
│   ├── keypoints/                  URFD dataset CSVs for LSTM training
│   └── weapon_dataset/             YOLO weapon training data
│
├── scripts/                        Utility + training scripts (see doc 07)
├── tests/                          pytest tests + API test scripts
│
└── frontend/
    ├── app/                        Next.js App Router pages
    ├── components/                 React components
    ├── lib/                        API client, data helpers, demo data
    ├── public/                     Static assets + pose model download
    ├── next.config.ts              API proxy rewrite
    ├── tailwind.config.ts
    └── package.json
```

---

## Application Startup Sequence

When `python main.py` runs, `create_app()` in `api/__init__.py` does the following in order:

1. Create Flask app and configure from `config.py`
2. Enable CORS for `localhost:3000`
3. Initialise `Database` (creates tables if they don't exist)
4. Initialise `FacialRecognitionEngine`; load all face encodings from `data/samples/`
5. Load `AnomalyDetector` from `models/isolation_forest.pkl` (or warn if missing)
6. Initialise `ThreatDetector` (in-memory, stateless rules)
7. Inject a stub TensorFlow module (prevents import crashes from protobuf mismatch)
8. Attempt to load `FallDetector` (rules) or `LSTMFallDetector` (if `FALL_DETECTOR_MODE=lstm`); falls back to rules on error
9. Attempt to load `ObjectDetector` (`yolo26l.pt`); continues without it if model missing
10. Register all three Flask blueprints (`api_bp`, `fall_bp`, `objects_bp`)
11. Start serving on `0.0.0.0:5001`

> Flask is started with `threaded=False` to prevent OpenCV segfaults from concurrent frame decoding.

---

## Request Flow — Face Recognition

```
Browser streams webcam frame
        │
        ▼ base64 JPEG in JSON body
POST /api/recognize
        │
        ├─ FacialRecognitionEngine.recognize_all_faces(frame)
        │   ├─ detect_faces() → bounding boxes
        │   └─ per face: _extract_face_features() → distance matching
        │
        ├─ Single face? → RecognitionBuffer majority vote (last 5 frames)
        │
        ├─ Access GRANTED:
        │   ├─ db.add_user() / upsert
        │   ├─ db.log_access() → access_logs
        │   ├─ db.log_audit() → audit_logs
        │   ├─ ThreatDetector.check_tailgating()
        │   ├─ ThreatDetector.check_unusual_access_time()
        │   └─ AnomalyDetector.predict_anomaly() → db.log_anomaly() if anomaly
        │
        └─ Access DENIED:
            ├─ db.log_access() → access_logs
            ├─ db.log_audit() → audit_logs
            └─ ThreatDetector.check_failed_access_attempts()
```

---

## Request Flow — Fall Detection (Camera Script Path)

```
fall_detection_camera.py
  │
  ├─ Local FallDetector.process_frame(bgr_frame)
  │   ├─ MediaPipe → 33 body landmarks
  │   ├─ Compute hip_height, torso_angle, hip_velocity
  │   └─ Return FallResult(is_fall, confidence, reason, …)
  │
  └─ If is_fall:
      POST /api/fall/log { confidence, reason, hip_height, … }
              │
              ├─ db.log_anomaly(anomaly_type="fall_detected")
              ├─ db.log_threat(severity="CRITICAL")
              └─ ThreatDetector.check_repeated_falls()
```

---

## Request Flow — Object Detection (Camera Script Path)

```
test_object_detection_camera_live.py
  │
  ├─ Every N frames: POST /api/objects/detect { frame: base64 }
              │
              ├─ ObjectDetector.process_frame(frame)
              │   ├─ Optional CLAHE preprocessing
              │   ├─ YOLO26l → raw detections
              │   ├─ Map COCO class → category
              │   └─ Persistence: only alert after frame_threshold hits
              │
              └─ If HIGH/CRITICAL:
                  db.log_threat(threat_type="OBJECT_{category}")
```

---

## Frontend Data Flow

```
Next.js page mounts
        │
        ├─ useDemoMode() → reads localStorage["facedoor_demo_mode"]
        │
        ├─ If demoEnabled === true:
        │   └─ Returns DEMO_* fixtures from lib/demoData.ts
        │       (bypasses API entirely for that data type)
        │
        └─ If demoEnabled === false:
            ├─ fetch("/api/…") → proxied to Flask :5001
            ├─ Response mapped to typed interfaces (lib/api.ts)
            └─ Rendered in charts / tables
```

### Polling intervals

| Component | Interval |
|-----------|----------|
| UnifiedDashboard (home) | 10 seconds |
| Falls page | 15 seconds |
| Objects page | 15 seconds |
| Demo Center page | 2.5 seconds (tool status only) |

All pages also re-fetch when the browser tab gains focus.

---

## Key Design Decisions

### Why `threaded=False` in Flask?

OpenCV and MediaPipe are not thread-safe. Running Flask in multi-threaded mode causes intermittent segfaults when two requests try to decode frames simultaneously. Single-threaded Flask is safe for a single-camera, single-user system like this.

### Why camera scripts post results rather than frames?

The `FallDetector` maintains a rolling history of hip positions across frames. If each frame is sent to Flask and processed by the server's detector instance, different client sessions would share (and corrupt) that history. The camera scripts run their own local detector and only POST confirmed fall events to `/api/fall/log`.

### Why SQLite?

Care home scale: a few residents, a few hundred events per day. SQLite has zero administration overhead, runs embedded, and stores in a single file (`doorface.db`). It can be replaced by PostgreSQL by swapping `data/database.py` — the rest of the code uses the `Database` abstraction class.

### Why Next.js API proxy?

The frontend only ever communicates with its own origin (`:3000`). The proxy rewrite in `next.config.ts` forwards `/api/*` to Flask. This avoids CORS issues in the browser and means you only need to open one port externally.

### Why demo mode overrides real data?

With `demoEnabled = true`, `emptyOrDemo()` returns demo fixtures before even checking the API response. This lets the UI look populated for a presentation without requiring a live backend or real enrolled users. When evaluating or deploying, turn demo OFF via the sidebar toggle.
