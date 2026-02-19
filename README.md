# FaceDoor — Smart Door Security System

A facial recognition-based access control and monitoring system designed for elderly care facilities. It identifies residents and staff at entry points, logs every access event, detects security threats, and surfaces everything through a modern web dashboard.

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
  - [Diagnostics](#diagnostics)
- [API Reference](#api-reference)
- [Dashboard Pages](#dashboard-pages)
- [Configuration](#configuration)
- [Compliance](#compliance)
- [Scripts](#scripts)

---

## Overview

FaceDoor provides:

- **Facial Recognition** — detects and identifies people at the door using HOG feature extraction and Euclidean distance matching (85–95% accuracy, runs on Raspberry Pi)
- **Threat Detection** — rules-based alerts for failed access attempts, unusual hours, unrecognised faces, and frequency spikes
- **Anomaly Detection** — Isolation Forest ML model flags unusual behavioural patterns (e.g. inactivity, off-hours access)
- **Audit Logging** — every system action is logged for PIPEDA / GDPR compliance
- **Live Dashboard** — real-time monitoring of entries/exits, alerts, and audit trail via a Next.js web app

---

## Architecture

```
┌─────────────────────────────┐        ┌──────────────────────────────┐
│   Next.js Frontend          │        │   Flask REST API             │
│   localhost:3000            │◄──────►│   localhost:5000             │
│                             │  HTTP  │                              │
│  Dashboard  /               │        │  /api/recognize              │
│  Alerts     /alerts         │        │  /api/logs                   │
│  Logs       /logs           │        │  /api/threats                │
│  Audit      /compliance     │        │  /api/stats                  │
└─────────────────────────────┘        │  /api/compliance/audit       │
                                       └──────────────┬───────────────┘
                                                      │
                              ┌───────────────────────▼──────────────┐
                              │  SQLite Database  (data/doorface.db) │
                              │  Tables: users, access_logs,          │
                              │          threats, anomalies,          │
                              │          audit_logs,                  │
                              │          behavioral_profiles          │
                              └──────────────────────────────────────┘
```

The Next.js dev server proxies all `/api/*` requests to Flask automatically — no CORS issues during development.

---

## Tech Stack

| Layer             | Technology                                      |
|-------------------|-------------------------------------------------|
| Backend           | Python 3.12, Flask 3.x                         |
| Computer Vision   | OpenCV 4.x (Haar Cascade, HOG)                 |
| Machine Learning  | scikit-learn (Isolation Forest)                 |
| Database          | SQLite via `sqlite3`                            |
| Frontend          | Next.js 16 (App Router), React 19, TypeScript  |
| Styling           | Tailwind CSS                                    |
| Charts            | Recharts                                        |
| Target Hardware   | Raspberry Pi 4 / Jetson Nano                   |

---

## Project Structure

```
facedoor-1/
│
├── main.py                        # Flask app entry point (API only)
├── config.py                      # All configuration constants
├── requirements.txt               # Python dependencies
│
├── api/
│   ├── __init__.py                # Flask app factory + CORS setup
│   ├── routes.py                  # REST API endpoints
│   ├── facial_recognition.py      # Face detection & matching engine
│   └── threat_detection.py        # Rules-based threat detection
│
├── models/
│   └── anomaly_detection.py       # Isolation Forest anomaly detector
│
├── data/
│   ├── database.py                # SQLite manager (all DB operations)
│   ├── data_generator.py          # Synthetic training data generator
│   ├── doorface.db                # SQLite database (auto-created)
│   └── samples/                   # Captured face photos (auto-created)
│       └── {person_name}/
│           └── face_*.jpg
│
├── frontend/                      # Next.js dashboard
│   ├── app/
│   │   ├── layout.tsx             # Root layout with sidebar
│   │   ├── page.tsx               # Dashboard (stats + charts)
│   │   ├── alerts/page.tsx        # Security alerts
│   │   ├── logs/page.tsx          # Access logs table
│   │   └── compliance/page.tsx    # PIPEDA audit trail
│   ├── components/
│   │   ├── Sidebar.tsx            # Collapsible nav sidebar
│   │   ├── StatCard.tsx           # KPI stat cards
│   │   ├── AccessChart.tsx        # Bar chart (entries/exits by hour)
│   │   ├── StatusDonut.tsx        # Donut chart (access breakdown)
│   │   ├── AccessLogsTable.tsx    # Paginated logs table
│   │   ├── AlertList.tsx          # Threat alert cards
│   │   └── AuditTable.tsx         # Compliance audit table
│   ├── lib/
│   │   ├── api.ts                 # Typed API client
│   │   └── demoData.ts            # Demo data (shown when DB is empty)
│   ├── next.config.ts             # API proxy config
│   └── package.json
│
├── docs/                          # Architecture, API, deployment guides
│
└── Utility scripts
    ├── capture_faces.py           # Capture face photos from webcam
    ├── register_faces.py          # Register faces into the database
    ├── diagnose_recognition.py    # System diagnostics tool
    ├── quick_test_recognition.py  # Quick recognition test
    ├── test_integration.py        # End-to-end integration tests
    └── train_anomaly_detection.py # Train the Isolation Forest model
```

---

## Getting Started

### Prerequisites

| Tool       | Version  | Download                        |
|------------|----------|---------------------------------|
| Python     | 3.12+    | https://www.python.org          |
| Node.js    | 18+ LTS  | https://nodejs.org              |
| npm        | 9+       | Included with Node.js           |

> **Note:** Both were automatically installed via `winget` during initial setup on Windows.

---

### 1. Backend (Flask API)

```bash
# Install Python dependencies
pip install -r requirements.txt

# Start the API server
python main.py
```

Flask API will be available at **http://localhost:5000**

---

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

Before the system can recognise anyone, you need to register faces:

```bash
# Step 1 — capture face photos from your webcam
python capture_faces.py

# Step 2 — register the captured photos into the database
python register_faces.py
```

The system will prompt for a name, capture several photos, extract HOG features, and store them in `data/samples/` and the SQLite database.

### Running the System

Once faces are registered:

1. Start the Flask API: `python main.py`
2. Start the Next.js dashboard: `cd frontend && npm run dev`
3. Open **http://localhost:3000**
4. Point a camera feed at the door — the `/api/recognize` endpoint accepts base64-encoded frames

### Diagnostics

If recognition is not working:

```bash
python diagnose_recognition.py
```

This checks camera connectivity, face detection, stored samples, recognition accuracy, and database health.

---

## API Reference

All endpoints are prefixed with `/api`.

| Method | Endpoint              | Description                          |
|--------|-----------------------|--------------------------------------|
| GET    | `/health`             | Health check                         |
| POST   | `/recognize`          | Recognize a face from a camera frame |
| POST   | `/log-access`         | Log an access event                  |
| GET    | `/logs`               | Get access logs (paginated)          |
| GET    | `/threats`            | Get active security threats          |
| GET    | `/stats`              | System statistics                    |
| GET    | `/compliance/audit`   | PIPEDA audit log                     |

### Example — Recognize a face

```bash
curl -X POST http://localhost:5000/api/recognize \
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
  "timestamp": "2026-02-17T14:30:00"
}
```

### Example — Get access logs

```bash
curl "http://localhost:5000/api/logs?limit=20"
```

---

## Dashboard Pages

| Page        | URL           | Description                                                      |
|-------------|---------------|------------------------------------------------------------------|
| Dashboard   | `/`           | KPI cards, hourly bar chart, access breakdown donut, recent logs |
| Alerts      | `/alerts`     | Active threats filtered by ALL / HIGH / CRITICAL severity        |
| Access Logs | `/logs`       | Full paginated access log with entry/exit badges                 |
| Audit Trail | `/compliance` | PIPEDA-compliant audit log with CSV export                       |

> **Demo mode:** When the database has no registered faces, all pages automatically show realistic demo data. A yellow `Demo data` badge appears in the page header. Demo data disappears as soon as real users are registered.

---

## Configuration

All system settings live in `config.py`:

| Setting                        | Default          | Description                                  |
|--------------------------------|------------------|----------------------------------------------|
| `CONFIDENCE_THRESHOLD`         | `0.6`            | Minimum face match confidence to grant access |
| `FAILED_ATTEMPTS_THRESHOLD`    | `3`              | Failed attempts before alert                 |
| `INACTIVITY_THRESHOLD_HOURS`   | `24`             | Hours without access before alert            |
| `UNUSUAL_HOURS`                | `22:00 – 06:00`  | Hours flagged as unusual access              |
| `ANOMALY_SCORE_THRESHOLD`      | `0.7`            | Isolation Forest score cutoff                |
| `DATABASE_PATH`                | `data/doorface.db` | SQLite file location                       |
| `TARGET_DEVICE`                | `raspberry_pi`   | Hardware target for optimisation             |

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

| Script                        | Purpose                                            |
|-------------------------------|----------------------------------------------------|
| `capture_faces.py`            | Capture face photos from webcam for registration   |
| `register_faces.py`           | Register captured photos, extract HOG features     |
| `diagnose_recognition.py`     | Full system diagnostics (camera, DB, recognition)  |
| `quick_test_recognition.py`   | Quick test: photo + live webcam recognition        |
| `test_facial_recognition.py`  | Component-level recognition tests                  |
| `test_face_recognition_real.py` | Extended webcam + photo recognition tests        |
| `test_integration.py`         | End-to-end pipeline integration tests              |
| `train_anomaly_detection.py`  | Generate synthetic data and train Isolation Forest |

---

## Douglas College CSIS 4495 — Applied Research Project

© 2026 Douglas College. Built for elderly care facilities.
