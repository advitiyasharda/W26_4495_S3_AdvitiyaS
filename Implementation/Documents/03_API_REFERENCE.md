# API Reference

**Base URL:** `http://localhost:5001/api`

All requests and responses use JSON (`Content-Type: application/json`) unless noted. Timestamps are ISO 8601 strings with UTC `Z` suffix.

---

## General

### GET /api/health

Health check.

**Response 200**
```json
{
  "status": "healthy",
  "timestamp": "2026-05-25T08:00:00.000000",
  "version": "0.1.0"
}
```

### GET /api/stats

Aggregated system statistics.

**Response 200**
```json
{
  "facial_recognition": {
    "total_persons": 4,
    "recognition_accuracy": 0.92
  },
  "access_events": {
    "total_entries": 886,
    "total_exits": 0,
    "today": 0
  },
  "threats": {
    "active_alerts": 45
  },
  "falls": {
    "today": 0
  },
  "system": {
    "uptime_hours": 0,
    "avg_inference_latency_ms": 75
  },
  "timestamp": "2026-05-25T08:00:00"
}
```

---

## Face Recognition

### POST /api/recognize

Analyse a single camera frame and identify all faces. Logs access, threats, and anomalies.

**Request**
```json
{
  "frame": "<base64-encoded JPEG or PNG>"
}
```

The `frame` field may optionally include a data-URL prefix: `data:image/jpeg;base64,...`

**Response 200 — face(s) detected**
```json
{
  "person_id": "reubin_001",
  "name": "Reubin",
  "confidence": 0.87,
  "access_granted": true,
  "face_count": 1,
  "timestamp": "2026-05-25T08:00:00",
  "faces": [
    {
      "person_id": "reubin_001",
      "name": "Reubin",
      "confidence": 0.87,
      "access_granted": true,
      "face_location": [120, 40, 80, 80]
    }
  ]
}
```

`face_location` is `[x, y, width, height]` in pixels.

**Response 200 — no face detected**
```json
{
  "person_id": null,
  "name": "Unknown",
  "confidence": 0.0,
  "access_granted": false,
  "face_count": 0,
  "faces": [],
  "timestamp": "2026-05-25T08:00:00"
}
```

**Side effects on access granted:**
- Upserts user in `users` table
- Inserts row in `access_logs` (status: "success")
- Inserts row in `audit_logs` (action: "ACCESS_GRANTED")
- Runs tailgating, unusual-time, and anomaly checks
- May insert rows in `threats` and `anomalies`

**Side effects on access denied:**
- Inserts row in `access_logs` (status: "failed", user_id: "Unknown")
- Inserts row in `audit_logs` (action: "ACCESS_DENIED")
- Checks for repeated failed attempts → may log threat

### GET /api/recognition/status

Current state of the face recognition engine.

**Response 200**
```json
{
  "engine_mode": "opencv",
  "dlib_version": null,
  "registered_persons": 4,
  "total_encodings": 163,
  "current_threshold": 0.55,
  "confidence_threshold": 0.6,
  "timestamp": "2026-05-25T08:00:00"
}
```

`engine_mode`: `"dlib"` if `face_recognition` package is installed, `"opencv"` otherwise.

### POST /api/recognition/reload

Reload face encodings from `data/samples/` without restarting Flask. Use after enrolling new people.

**Response 200**
```json
{
  "status": "reloaded",
  "loaded_encodings": 163,
  "registered_persons": 4,
  "total_face_encodings": 163,
  "timestamp": "2026-05-25T08:00:00"
}
```

---

## Users

### GET /api/users

All registered users. Excludes `Unknown`, `fall_detection`, and demo placeholder IDs.

**Response 200**
```json
{
  "users": [
    {
      "user_id": "Reubin",
      "name": "Reubin",
      "display_id": "RES-001",
      "role": "resident"
    }
  ]
}
```

### DELETE /api/users/{user_id}

Remove a user from the database and from the live face engine.

**Response 200**
```json
{ "status": "deleted", "user_id": "Reubin" }
```

**Response 404**
```json
{ "error": "User not found or cannot be deleted" }
```

---

## Access Logs

### GET /api/logs

Access log entries.

**Query parameters**

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `limit` | int | 100 | Max rows returned |
| `offset` | int | 0 | Pagination offset |
| `person_id` | string | — | Filter by user |

**Response 200**
```json
{
  "logs": [
    {
      "person_id": "Reubin",
      "name": "Reubin",
      "type": "entry",
      "status": "success",
      "confidence": 0.87,
      "timestamp": "2026-05-25T08:00:00Z"
    }
  ],
  "total": 886,
  "limit": 100,
  "offset": 0,
  "timestamp": "2026-05-25T08:00:00"
}
```

### POST /api/log-access

⚠️ **Stub — does not persist to database yet.** Only logs to console. See known issues.

---

## Threats & Alerts

### GET /api/threats

Active (unresolved) threats.

**Query parameters**

| Param | Type | Description |
|-------|------|-------------|
| `severity` | string | Filter: `LOW`, `MEDIUM`, `HIGH`, `CRITICAL` |
| `person_id` | string | Filter by user |

**Response 200**
```json
{
  "threats": [
    {
      "threat_id": 1,
      "user_id": "Unknown",
      "threat_type": "Unrecognised Face Detected",
      "severity": "HIGH",
      "message": "Face at main entrance, no match. Confidence: 0.12.",
      "resolved": false,
      "timestamp": "2026-05-25T08:00:00Z"
    }
  ],
  "total": 2837,
  "timestamp": "2026-05-25T08:00:00"
}
```

**Known threat types**

| `threat_type` | Severity | Trigger |
|---------------|----------|---------|
| `Unrecognised Face Detected` | HIGH | Unknown face at door |
| `Repeated Failed Access Attempts` | HIGH | ≥ 3 failures in 10 min |
| `Unusual Access Time` | MEDIUM | Access between 22:00–05:00 |
| `Tailgating Detected` | HIGH | 2+ persons enter within 15s |
| `Behavioural Anomaly Detected` | MEDIUM | IsolationForest flag |
| `FALL_DETECTED` | CRITICAL | Fall confirmed |
| `Repeated Falls` | HIGH/CRITICAL | 2+ or 3+ falls in 24h |
| `OBJECT_WEAPON` | CRITICAL | Weapon detected |
| `OBJECT_SECURITY_THREAT` | HIGH | Security-threat object |
| `OBJECT_PARCEL` | MEDIUM | Unattended parcel |
| `CAMERA_VISIBILITY_WARNING` | LOW | Body not fully in frame |

---

## Compliance / Audit

### GET /api/compliance/audit

PIPEDA audit trail.

**Query parameters**

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `limit` | int | 100 | Max rows |
| `offset` | int | 0 | Pagination |
| `format` | string | json | `"csv"` triggers file download |

**Response 200 (JSON)**
```json
{
  "audit_log": [
    {
      "action": "ACCESS_GRANTED",
      "user": "Reubin",
      "resource": "door/main-entrance",
      "result": "success",
      "details": "confidence=0.87",
      "timestamp": "2026-05-25T08:00:00Z"
    }
  ],
  "count": 886,
  "timestamp": "2026-05-25T08:00:00"
}
```

**Response 200 (CSV)** — when `?format=csv`

Returns `Content-Type: text/csv` with `Content-Disposition: attachment; filename=audit_log_YYYYMMDD_HHMMSS.csv`.

---

## Fall Detection

Base prefix: `/api/fall`

### POST /api/fall/detect

Analyse a frame on the server's fall detector instance. Not recommended for continuous streams (use `/api/fall/log` instead — see Architecture doc).

**Request**
```json
{ "frame": "<base64>" }
```

**Response 200**
```json
{
  "is_fall": true,
  "confidence": 0.73,
  "reason": "hips low (1.37); torso tilted 60°",
  "hip_height": 1.369,
  "torso_angle_deg": 59.9,
  "hip_velocity": 0.0,
  "landmarks_visible": true,
  "timestamp": "2026-05-25T08:00:00"
}
```

### POST /api/fall/log

Log a fall event detected externally (e.g. by `fall_detection_camera.py`).

**Request**
```json
{
  "confidence": 0.73,
  "reason": "hips low; rapid drop",
  "hip_height": 1.2,
  "torso_angle_deg": 55.0,
  "hip_velocity": 0.18,
  "detector_source": "rules"
}
```

All fields except `confidence` are optional.

**Response 200**
```json
{
  "status": "logged",
  "detector_source": "rules",
  "timestamp": "2026-05-25T08:00:00"
}
```

### GET /api/fall/events

Recent fall events from the database.

**Query parameters:** `limit` (default 20)

**Response 200**
```json
{
  "events": [
    {
      "anomaly_id": 200,
      "user_id": "fall_detection",
      "anomaly_type": "fall_detected",
      "anomaly_score": 0.661,
      "description": "Fall detected: hips low (1.04); ...",
      "timestamp": "2026-04-14T06:44:54Z"
    }
  ],
  "count": 23
}
```

### GET /api/fall/status

Current state of the fall detector.

**Response 200**
```json
{
  "detector_ready": true,
  "active_mode": "rules",
  "requested_mode": "rules",
  "fall_threshold": 0.55,
  "velocity_window": 8,
  "sequence_length": 0,
  "cooldown_frames": 0,
  "history_length": 5,
  "artifacts": {
    "pose_model_exists": true,
    "lstm_model_exists": false,
    "lstm_scaler_exists": false
  }
}
```

### POST /api/fall/reset

Clear the detector's velocity history and cooldown. Use after repositioning the camera.

**Response 200**
```json
{ "status": "reset", "timestamp": "2026-05-25T08:00:00" }
```

---

## Object Detection

Base prefix: `/api/objects`

### POST /api/objects/detect

Analyse a frame for objects.

**Request**
```json
{ "frame": "<base64>" }
```

**Response 200**
```json
{
  "detections": [
    {
      "object_class": "knife",
      "category": "WEAPON",
      "severity": "CRITICAL",
      "confidence": 0.82,
      "bbox": [100, 200, 50, 60],
      "timestamp": "2026-05-25T08:00:00"
    }
  ],
  "count": 1,
  "timestamp": "2026-05-25T08:00:00"
}
```

### GET /api/objects/events

In-memory recent detection events (not persisted to DB directly).

**Query parameters**

| Param | Type | Description |
|-------|------|-------------|
| `limit` | int | Max events (default 50) |
| `category` | string | Filter: WEAPON, PARCEL, etc. |
| `severity` | string | Filter: CRITICAL, HIGH, etc. |

**Response 200**
```json
{
  "events": [
    {
      "object_class": "knife",
      "category": "WEAPON",
      "severity": "CRITICAL",
      "confidence": 0.82,
      "unattended_seconds": 0,
      "frame_count": 5,
      "timestamp": "2026-05-25T08:00:00"
    }
  ],
  "count": 1
}
```

### GET /api/objects/status

Detector readiness and event counts.

**Response 200**
```json
{
  "detector_ready": true,
  "weapon_model_ready": false,
  "confidence": 0.20,
  "frame_threshold": 3,
  "unattended_minutes": 2.0,
  "events_logged": 12,
  "category_counts": {
    "WEAPON": 0,
    "PARCEL": 3,
    "MOBILITY_AID": 9
  }
}
```

---

## Demo Tools

Manage live camera scripts launched from the Demo Center page.

### GET /api/demo/tools

List all available demo tools and their current process status.

**Response 200**
```json
{
  "tools": [
    {
      "id": "face-register",
      "label": "Face registration capture",
      "kind": "camera",
      "command": "python scripts/capture_faces.py ...",
      "running": false,
      "pid": null
    },
    {
      "id": "face-test",
      "label": "Face recognition test interface",
      "kind": "camera",
      "running": false,
      "pid": null
    },
    {
      "id": "fall-test",
      "label": "Fall detection interface",
      "kind": "camera",
      "running": false,
      "pid": null
    },
    {
      "id": "object-test",
      "label": "Object detection interface",
      "kind": "camera",
      "running": false,
      "pid": null
    }
  ],
  "timestamp": "2026-05-25T08:00:00"
}
```

### POST /api/demo/tools/{tool_id}/start

Start a demo tool subprocess. Only one camera tool can run at a time; starting another stops the current one.

**Tool IDs:** `face-register`, `face-test`, `fall-test`, `object-test`

**Request (for `face-register` only)**
```json
{
  "person_id": "john_001",
  "name": "John Smith",
  "role": "resident",
  "photos": 40
}
```

Other tools take no request body (or empty `{}`).

**Response 200**
```json
{
  "status": "started",
  "tool_id": "fall-test",
  "pid": 12345,
  "command": "python scripts/fall_detection_camera.py",
  "timestamp": "2026-05-25T08:00:00"
}
```

### POST /api/demo/tools/{tool_id}/stop

Stop a running demo tool.

**Response 200**
```json
{
  "status": "stopped",
  "tool_id": "fall-test",
  "timestamp": "2026-05-25T08:00:00"
}
```

If not running:
```json
{ "status": "not_running", "tool_id": "fall-test", "timestamp": "..." }
```

---

## Error Responses

All endpoints return a consistent error shape on 4xx/5xx:

```json
{ "error": "Descriptive message" }
```

Common codes:
| Code | Meaning |
|------|---------|
| 400 | Missing or invalid request body / parameter |
| 404 | Resource not found (user, tool) |
| 500 | Internal server error (check `server.log`) |
