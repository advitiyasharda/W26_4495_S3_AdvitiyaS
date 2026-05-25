# Database Schema

The system uses a single SQLite database at `Implementation/data/doorface.db`. The `Database` class (`Implementation/data/database.py`) manages all SQL operations — no ORM is used.

---

## Connection

```python
from data.database import Database
db = Database()               # default: data/doorface.db
db = Database("custom.db")   # custom path
```

The connection uses `check_same_thread=False` and `row_factory = sqlite3.Row` (rows accessible as dicts).

---

## Tables

### `users`

Registered residents and caregivers.

| Column | Type | Notes |
|--------|------|-------|
| `user_id` | TEXT PK | Folder name from `data/samples/` (e.g. `"Reubin"`) |
| `name` | TEXT NOT NULL | Display name |
| `role` | TEXT | `"resident"` or `"caregiver"` (default: `"resident"`) |
| `display_id` | TEXT | Human-readable ID auto-assigned as `RES-001`, `RES-002`, … |
| `created_at` | TIMESTAMP | UTC, default `CURRENT_TIMESTAMP` |
| `updated_at` | TIMESTAMP | UTC |

**System rows that always exist:**
- `user_id = "Unknown"` — placeholder for unrecognised faces
- `user_id = "fall_detection"` — placeholder for fall events

**Exclusions in API:** `get_users()` filters out `Unknown`, `fall_detection`, `caregiver_001`, `resident_001` (demo IDs).

---

### `access_logs`

Every door access attempt (granted or denied).

| Column | Type | Notes |
|--------|------|-------|
| `log_id` | INTEGER PK AUTOINCREMENT | |
| `user_id` | TEXT FK → users | |
| `access_type` | TEXT | `"entry"` or `"exit"` |
| `confidence` | REAL | Face match confidence 0.0–1.0 |
| `status` | TEXT | `"success"` or `"failed"` |
| `timestamp` | TIMESTAMP | UTC ISO string |

**Index:** `idx_access_logs_user_timestamp` on `(user_id, timestamp)`

**Current row count:** ~886

---

### `anomalies`

AI-detected anomalies (fall events and behavioural anomalies).

| Column | Type | Notes |
|--------|------|-------|
| `anomaly_id` | INTEGER PK AUTOINCREMENT | |
| `user_id` | TEXT FK → users | `"fall_detection"` for fall events |
| `anomaly_type` | TEXT | `"fall_detected"` or `"BEHAVIOURAL_ANOMALY"` |
| `anomaly_score` | REAL | Confidence/score 0.0–1.0 |
| `description` | TEXT | Human-readable reason |
| `timestamp` | TIMESTAMP | UTC ISO string |

**Current row count:** 67 (23 fall_detected, 44 BEHAVIOURAL_ANOMALY)

**Fall event description format:**
```
Fall detected: hips low (1.37); torso tilted 60° | source=rules confidence=0.73 hip_y=1.369 angle=59.9deg vel=0.0000
```

---

### `threats`

All security alerts and threat events.

| Column | Type | Notes |
|--------|------|-------|
| `threat_id` | INTEGER PK AUTOINCREMENT | |
| `user_id` | TEXT | May be `"Unknown"`, `"fall_detection"`, or a real user |
| `threat_type` | TEXT NOT NULL | See threat type list below |
| `severity` | TEXT | `LOW`, `MEDIUM`, `HIGH`, or `CRITICAL` |
| `message` | TEXT | Human-readable description |
| `resolved` | BOOLEAN | Default `0` (false). Not currently updated via UI |
| `timestamp` | TIMESTAMP | UTC ISO string |
| `resolved_at` | TIMESTAMP | Null unless resolved |

**Current row count:** ~2837

**Note:** Threats are never auto-resolved by the system. The `resolved` flag exists for future use.

**Known threat types:**

| `threat_type` | Severity | Source |
|---------------|----------|--------|
| `Unrecognised Face Detected` | HIGH | `/api/recognize` |
| `Repeated Failed Access Attempts` | HIGH | `/api/recognize` |
| `Unusual Access Time` | MEDIUM | `/api/recognize` |
| `Tailgating Detected` | HIGH | `/api/recognize` |
| `Behavioural Anomaly Detected` | MEDIUM | `/api/recognize` |
| `FALL_DETECTED` | CRITICAL | `/api/fall/log` or `/api/fall/detect` |
| `Repeated Falls` | HIGH / CRITICAL | fall detection routes |
| `CAMERA_VISIBILITY_WARNING` | LOW | `/api/fall/log` |
| `OBJECT_WEAPON` | CRITICAL | `/api/objects/detect` |
| `OBJECT_SECURITY_THREAT` | HIGH | `/api/objects/detect` |
| `OBJECT_PARCEL` | MEDIUM | `/api/objects/detect` |

---

### `audit_logs`

PIPEDA-aligned audit trail for every significant action.

| Column | Type | Notes |
|--------|------|-------|
| `audit_id` | INTEGER PK AUTOINCREMENT | |
| `action` | TEXT NOT NULL | See action list below |
| `user_id` | TEXT | User involved |
| `resource` | TEXT | e.g. `"door/main-entrance"` |
| `result` | TEXT | `"success"` or `"failed"` |
| `details` | TEXT | e.g. `"confidence=0.87"` |
| `timestamp` | TIMESTAMP | UTC ISO string |

**Current row count:** ~886

**Known actions:**

| Action | Trigger |
|--------|---------|
| `ACCESS_GRANTED` | Recognised face, entry allowed |
| `ACCESS_DENIED` | Unknown face, entry refused |

---

### `behavioral_profiles`

Optional behavioral baseline per user (not currently populated).

| Column | Type | Notes |
|--------|------|-------|
| `profile_id` | INTEGER PK AUTOINCREMENT | |
| `user_id` | TEXT UNIQUE FK | |
| `preferred_hours` | TEXT | JSON array of typical hours |
| `preferred_days` | TEXT | JSON array of typical weekdays |
| `avg_daily_accesses` | REAL | Average events per day |
| `created_at` | TIMESTAMP | |
| `updated_at` | TIMESTAMP | |

**Current row count:** 0

---

## Key Database Methods

### `add_user(user_id, name, role, display_id)`
Inserts or updates a user. Auto-assigns `RES-xxx` display ID if not provided.

### `log_access(user_id, access_type, confidence, status)`
Inserts a row in `access_logs`. Timestamps stored as UTC.

### `log_anomaly(user_id, anomaly_type, anomaly_score, description)`
Inserts a row in `anomalies`.

### `log_threat(threat_type, severity, user_id, message)`
Inserts a row in `threats`.

### `log_audit(action, user_id, resource, result, details)`
Inserts a row in `audit_logs`.

### `get_access_logs(user_id=None, limit=100)`
Returns logs excluding demo user IDs (`caregiver_001`, `resident_001`). Ordered by timestamp DESC.

### `get_anomalies(limit=20, anomaly_type=None)`
Returns anomalies, optionally filtered by type.

### `get_active_threats(severity=None)`
Returns all unresolved threats (`resolved = 0`), newest first.

### `get_users()`
Returns all users excluding `Unknown`, `fall_detection`, `caregiver_001`, `resident_001`.

### `delete_user(user_id)`
Deletes user row; returns False if user not found.

### `get_audit_logs(limit=100, offset=0)`
Returns audit logs, newest first.

### `get_database_stats()`
Returns counts: `total_users`, `total_access_events`, `active_threats`.

---

## Database Maintenance

### Reset / Clear

**WARNING — destructive.** Wipes all tables and re-creates schema:

```bash
cd Implementation
python scripts/clear_database.py
```

Use only in development. Backs up nothing.

### Backup

Simply copy `data/doorface.db` — it is a self-contained file:

```bash
cp Implementation/data/doorface.db Implementation/data/doorface_backup_$(date +%Y%m%d).db
```

### Inspect directly

```bash
sqlite3 Implementation/data/doorface.db

.tables
.schema users
SELECT COUNT(*) FROM threats WHERE severity = 'CRITICAL';
SELECT * FROM anomalies WHERE anomaly_type = 'fall_detected' ORDER BY timestamp DESC LIMIT 5;
```

---

## Migrating to PostgreSQL

The entire SQL surface is in `data/database.py`. To migrate:

1. Replace `sqlite3` with `psycopg2` (or `asyncpg`)
2. Change `?` placeholders to `%s`
3. Replace `AUTOINCREMENT` with `SERIAL` / `GENERATED ALWAYS AS IDENTITY`
4. Replace `CURRENT_TIMESTAMP` with `NOW()`
5. Update `db_path` connection logic with a DSN string

The rest of the codebase calls only methods on the `Database` class, so no other files need changing.
