# FaceDoor — Project Overview

## What Is FaceDoor?

FaceDoor is a smart door security system designed for elderly care facilities. It uses a single door-mounted camera to perform three real-time detection tasks:

1. **Face Recognition** — identifies residents and caregivers, grants or denies entry, and logs every access event.
2. **Fall Detection** — monitors the doorway zone for sudden posture changes using AI pose estimation.
3. **Object Detection** — identifies security-relevant objects (weapons, unattended parcels, mobility aids) at the entrance.

All events are logged to a local SQLite database and surfaced through a real-time web dashboard. The system also generates compliance-ready audit trails (PIPEDA aligned).

---

## Project Context

| Item | Detail |
|------|--------|
| **Course** | CSIS 4495 — Applied Research Project, Douglas College |
| **Team** | Reubin, Advitiya, Armin, Eric |
| **Semester** | Winter/Spring 2026 |
| **Repo** | `W26_4495_S3_AdvitiyaS` |

---

## High-Level System Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                       DOOR CAMERA                            │
└─────────────┬───────────────┬──────────────┬────────────────┘
              │               │              │
              ▼               ▼              ▼
     Face Recognition    Fall Detection  Object Detection
     (OpenCV + dlib)    (MediaPipe +    (YOLO26 + optional
                         LSTM option)    weapon model)
              │               │              │
              └───────────────┴──────────────┘
                              │
                              ▼
                   ┌──────────────────┐
                   │  Flask API :5001  │
                   │  (Python backend) │
                   └────────┬─────────┘
                            │
                    ┌───────▼──────┐
                    │  SQLite DB   │
                    │  doorface.db │
                    └───────┬──────┘
                            │
                   ┌────────▼─────────┐
                   │  Next.js :3000   │
                   │  Web Dashboard   │
                   └──────────────────┘
```

---

## Technology Stack

### Backend
| Layer | Technology |
|-------|-----------|
| Web framework | Python / Flask |
| Face detection | OpenCV (Haar cascade) + optional `face_recognition` (dlib) |
| Pose estimation | Google MediaPipe `PoseLandmarker` |
| LSTM model | TensorFlow/Keras (`fall_lstm.keras`) |
| Object detection | Ultralytics YOLO26 (`yolo26l.pt`) |
| Anomaly detection | scikit-learn `IsolationForest` |
| Database | SQLite via `data/database.py` |

### Frontend
| Layer | Technology |
|-------|-----------|
| Framework | Next.js 16 (App Router) |
| UI | React 19 + Tailwind CSS |
| Charts | Recharts |
| Language | TypeScript |

---

## Capabilities at a Glance

### Face Recognition
- Recognises registered residents and caregivers in real time
- Logs every access attempt (granted / denied) with confidence score
- Triggers threat alerts for unrecognised faces, repeated failures, tailgating, and unusual access times
- Supports enrolling new people via a Demo Center webcam capture

### Fall Detection
- Rules-based Phase 1: hip height + torso angle + hip velocity (MediaPipe pose)
- LSTM Phase 2: 30-frame sequence through a trained Keras model
- Logs every fall event with confidence score; escalates to CRITICAL threat
- Detects repeated falls over 24 hours

### Object Detection
- YOLO26-based detection across 5 categories:
  - `WEAPON` — firearms, bladed objects
  - `SECURITY_THREAT` — suspicious items
  - `PARCEL` — unattended packages
  - `MOBILITY_AID` — walkers, wheelchairs (informational)
  - `OPERATIONAL` — normal objects
- High/Critical events logged as threats with severity routing

### Threat & Anomaly Detection
- Isolation Forest model on access patterns (time, frequency, confidence)
- Rules-based checks: failed attempts, unusual hours, tailgating, wandering, inactivity
- All threats surfaced on the Alerts dashboard with severity levels (LOW → CRITICAL)

### Compliance & Audit
- PIPEDA-aligned audit log for every system action
- CSV export from the Compliance page
- Access log export from the Alerts page

---

## Dashboard Pages

| Page | URL | What it shows |
|------|-----|--------------|
| Dashboard | `/` | KPIs, recent activity, charts for falls/objects/threats |
| Alerts | `/alerts` | All security threats with severity filter |
| Access Logs | `/logs` | Door access history + enrolled people modal |
| Fall Detection | `/falls` | Fall events, confidence chart, per-day area chart |
| Object Detection | `/objects` | Detection events, category/severity breakdown |
| Compliance | `/compliance` | Full audit trail, CSV export |
| Demo Center | `/demo` | Start/stop live detection scripts |

---

## Repository Structure (Top Level)

```
W26_4495_S3_AdvitiyaS/
├── Documents/                  ← This folder: all handover docs
├── Implementation/             ← All application code
│   ├── api/                    ← Flask blueprints & engine modules
│   ├── models/                 ← Detection models & ML code
│   ├── scripts/                ← Utility & training scripts
│   ├── data/                   ← SQLite DB, face samples, training data
│   ├── frontend/               ← Next.js dashboard
│   ├── docs/                   ← Technical docs (pre-existing)
│   ├── tests/                  ← pytest tests
│   ├── main.py                 ← Flask app entry point
│   ├── start.py                ← One-click installer + launcher
│   ├── config.py               ← All thresholds & config
│   └── requirements.txt        ← Python dependencies
├── ReportsAndDocuments/        ← Academic reports and presentations
└── FaceDoor_Quick_Start_Guide.pdf
```
