# Handover Checklist

This document is the starting point for anyone inheriting or continuing work on FaceDoor. Work through each section before making changes.

---

## Day 1: Get the System Running

- [ ] **Install prerequisites:** Python 3.10+ and Node.js 18+
- [ ] **Run the launcher:**
  ```bash
  python Implementation/start.py
  ```
  Choose option **3 (Both)** on first run to install all dependencies.

- [ ] **Verify backend health:**
  ```bash
  curl http://localhost:5001/api/health
  # Expected: {"status": "healthy", ...}
  ```

- [ ] **Open the dashboard:** http://localhost:3000
  - Demo toggle should be ON (purple) by default
  - All pages should show populated charts and tables (demo data)

- [ ] **Turn demo OFF** and confirm empty state (no backend data in DB for today)

- [ ] **Run the system health check:**
  ```bash
  cd Implementation && python scripts/system_health_check.py
  ```

---

## Day 2: Understand the Current State

### Database state
```bash
sqlite3 Implementation/data/doorface.db
.tables
SELECT COUNT(*) FROM threats;
SELECT COUNT(*) FROM anomalies;
SELECT user_id, name, role FROM users;
```

### Enrolled faces
```bash
ls Implementation/data/samples/
# Currently enrolled: Eric, Reubin, advitiya, armin, person_test
```

### Model files present
```bash
ls Implementation/models/
# Required: pose_landmarker.task
# Optional LSTM: fall_lstm.keras, fall_lstm_scaler.pkl
# Optional anomaly: isolation_forest.pkl
# Optional weapon: weapon_detector.pt
```

### Recognition engine
```bash
curl http://localhost:5001/api/recognition/status
# Check engine_mode (dlib vs opencv) and registered_persons count
```

---

## Known Issues / Incomplete Work

The following items were identified during development and not yet completed:

| # | Issue | File | Severity |
|---|-------|------|----------|
| 1 | `POST /api/log-access` is a **stub** — does not write to database | `api/routes.py` → `log_access()` | Medium |
| 2 | `threats.resolved` flag is never updated by any code path — resolved threats pile up in the DB | `data/database.py`, `api/routes.py` | Low |
| 3 | `behavioral_profiles` table exists but is never populated — `check_inactivity` and `check_wandering` checks are defined but not fully wired | `api/threat_detection.py` | Low |
| 4 | Object detection events are stored **in memory only** (`ObjectDetector._events` list) — they are lost on Flask restart and are not persisted to SQLite | `models/object_detection.py`, `api/object_detection_routes.py` | Medium |
| 5 | `TARGET_DEVICE` and `ENABLE_GPU` config values exist but no code uses them — GPU acceleration for Jetson Nano was planned but not implemented | `config.py` | Low |
| 6 | `POST /api/fall/detect` shares Flask's stateful `FallDetector` instance — multiple concurrent clients corrupt velocity history. Use `/api/fall/log` instead | `api/fall_detection_routes.py` | Design note |
| 7 | Flask runs `threaded=False` to avoid OpenCV segfaults — this limits throughput to one request at a time | `main.py` | Design note |

---

## Feature Roadmap (from team planning)

These features were planned but not implemented in the current release:

- **Exit detection:** The `access_type` column supports `"exit"` but nothing currently logs exits — `total_exits` is always 0 in stats
- **Multi-camera support:** All code assumes a single camera; extending would require session/camera ID routing
- **Threat resolution UI:** The `resolved` flag exists in the DB but there is no UI button to mark a threat resolved
- **Real-time WebSocket push:** Currently all pages poll on intervals; a WebSocket feed would reduce latency for critical alerts
- **User activity timeline:** The `behavioral_profiles` table was intended to power a per-resident activity view
- **Mobile-responsive layout:** Dashboard is desktop-first; works on tablet but not mobile

---

## Codebase Quick Reference

| If you want to… | Look in… |
|-----------------|----------|
| Add a new API endpoint | `api/routes.py` or create a new blueprint file |
| Change face recognition logic | `api/facial_recognition.py` |
| Change fall detection algorithm | `models/fall_detection.py` (rules) or `models/fall_detection_trained.py` (LSTM) |
| Change threat rules | `api/threat_detection.py` |
| Add a new dashboard page | `frontend/app/{page}/page.tsx` + `components/Sidebar.tsx` nav links |
| Add new demo data | `frontend/lib/demoData.ts` |
| Change chart colours | `frontend/lib/theme.ts` |
| Change thresholds | `Implementation/config.py` |
| Change the database schema | `data/database.py` → `init_db()` |
| Add a new script | `Implementation/scripts/` |

---

## Architecture Decisions to Preserve

These decisions were intentional and should not be changed without understanding the reasons:

1. **`threaded=False` in Flask** — prevents OpenCV/MediaPipe segfaults. Do not change to `threaded=True` unless you refactor to process images in a separate thread pool.

2. **Camera scripts post results, not frames** — `fall_detection_camera.py` runs a local `FallDetector` and posts confirmed events. This preserves the stateful velocity history. Do not refactor to send raw frames.

3. **Demo mode overrides real data when ON** — `emptyOrDemo()` returns demo fixtures when `demoEnabled === true`, even if the API returns real data. This is intentional so presentations work without a live camera.

4. **SQLite single-file database** — adequate for care home scale. If multi-user concurrency becomes an issue (multiple admins hitting the API simultaneously), migrate to PostgreSQL. The `Database` class is the only thing to change.

5. **Next.js API proxy** — the frontend never calls Flask directly from the browser (avoids CORS). All `/api/*` goes through Next.js. Do not break this by adding direct `fetch("http://localhost:5001")` calls in frontend components.

---

## Security Checklist Before Production

- [ ] Change `SECRET_KEY` in `config.py` (or env var) to a random 32+ character string
- [ ] Change `ENCRYPTION_KEY` to a secure value
- [ ] Set `DEBUG = False` in `config.py` or `FLASK_ENV=production`
- [ ] Restrict CORS origins in `api/__init__.py` to the actual production frontend URL
- [ ] Remove `data/doorface.db` and replace with a fresh database (current DB has test data)
- [ ] Remove `data/samples/person_test/` (test enrollment folder)
- [ ] Replace demo face enrollments with real resident/caregiver photos if deploying
- [ ] Ensure `server.log` rotation is configured (can grow indefinitely)
- [ ] Set up HTTPS if the dashboard is accessible outside localhost

---

## Document Index

| Document | Contents |
|----------|----------|
| `00_PROJECT_OVERVIEW.md` | What the system does, team, tech stack |
| `01_SETUP_AND_RUNNING.md` | Complete setup guide, enrollment, running scripts |
| `02_ARCHITECTURE.md` | System architecture, request flows, design decisions |
| `03_API_REFERENCE.md` | All API endpoints with request/response examples |
| `04_DATABASE_SCHEMA.md` | Table schemas, method reference, migration notes |
| `05_DETECTION_MODELS.md` | Face recognition, fall detection, object detection, anomaly detection |
| `06_FRONTEND_GUIDE.md` | Pages, components, demo mode, API client |
| `07_SCRIPTS_REFERENCE.md` | All scripts with arguments and usage |
| `08_CONFIGURATION.md` | All config keys and environment variables |
| `09_TROUBLESHOOTING.md` | Common issues and fixes |
| `10_HANDOVER_CHECKLIST.md` | This document |

---

## Contacts (at time of project)

| Name | Role | Contribution |
|------|------|--------------|
| Reubin | Team Lead / Full-stack | Dashboard, API integration, face registration flow |
| Advitiya | ML / Backend | Fall detection (Phase 1 + 2), anomaly detection |
| Armin | Backend / Camera | Object detection, camera scripts |
| Eric | Backend | Facial recognition engine, threat detection |
