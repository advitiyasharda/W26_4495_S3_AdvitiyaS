# FaceDoor — Slide-by-Slide Explanation & Professor Q&A Prep
**CSIS 4495 Applied Research · Final Presentation**

> Use this document to understand what each slide claims and be ready to defend it.  
> ⚠️ = High-probability professor question · ✅ = Confirmed implemented · 🔧 = Partial / documented only

---

## SLIDE 1 — TITLE

**Status:** ✅ Project is complete and running.

**What it covers:** Project identity, team, the three pillars (Face Recognition, Fall Detection, Threat Monitoring), and the privacy-first positioning.

**Key claim to be ready to defend:** "100% on-premises, zero cloud" — you must be able to explain architecturally *why* this is true (no outbound HTTP calls from Flask, SQLite is local, no cloud SDK imports).

---

## SLIDE 2 — THE PROBLEM

**Status:** ✅ Problem is real and well-documented in proposal.

### What Each Point Means

**"Unauthorized access risk"**
Traditional care facilities use badge/PIN systems. They have no way to identify *who* is physically present — a lost badge or shared PIN creates a gap. FaceDoor uses biometric identity (face) instead.

**"Falls go undetected"**
Standard CCTV is passive recording. No system analyzes the video in real-time to detect a person falling. Care staff cannot monitor every camera continuously. FaceDoor actively analyzes each frame.

**"Manual logs are error-prone"**
Paper sign-in sheets or manual visitor logs have no integrity guarantees — anyone can write anything. FaceDoor's audit trail is written programmatically with timestamps, actor, and cryptographic ordering.

**"Privacy/PIPEDA constraint"**
Canadian law (PIPEDA) requires that personal data be protected. Sending face images to a cloud API (e.g., AWS Rekognition) would require data processing agreements, cross-border data transfer disclosures, etc. On-premises eliminates this compliance burden.

### ⚠️ Professor Questions

- **"What specific PIPEDA articles apply here?"** → PIPEDA Principle 4 (Limiting Collection), Principle 7 (Safeguards), Principle 5 (Limiting Use). Our system maps all 10 principles in docs/COMPLIANCE.md.
- **"Why is biometric data sensitive under PIPEDA?"** → Biometric data is considered a subset of personal information under PIPEDA. It's immutable (you can't change your face like a password), so breach consequences are permanent.
- **"Couldn't you just use a cloud API and sign a BAA?"** → Yes, but that introduces vendor dependency, latency, ongoing cost, and requires the facility to negotiate data processing agreements with every resident and their family. On-premises avoids all of this.

---

## SLIDE 3 — OUR SOLUTION

**Status:** ✅ All three modules implemented and tested.

### What Each Number Means

**94.6% face recognition accuracy**
Measured on a 37-photo test set across three people. Not a benchmark from a paper — our own test on our own system with our own registered faces.

**93% LSTM fall detection accuracy**
Measured on held-out sequences from the UR Fall Detection Dataset (URFD) — an academic dataset of real fall scenarios filmed in a lab setting. The model was trained on the remaining sequences.

**52.5 mAP YOLO26**
Mean Average Precision at IoU threshold 0.5 on our evaluation set. mAP is the standard metric for object detection — it measures both accuracy (did it find the right class) and localization (did it draw the right box). YOLO26 outperformed YOLOv8n (37.3) and YOLOv8s (44.9).

### ⚠️ Professor Questions

- **"How did you get 94.6%? What's the test methodology?"** → 37 photos, 3 people, split into train/test. Person A 15/15 (100%), Person B 12/12 (100%), Person C 8/10 (80% — lighting variation). Euclidean distance matching with a calibrated threshold.
- **"Is 94.6% good enough for a security system?"** → It's good for a proof-of-concept. Real deployment would require more training samples per person. The system is designed to fail safe — false negatives (unknown person misclassified as known) trigger a HIGH alert anyway because they appear in the access log with a low confidence score.
- **"What does 93% accuracy mean for fall detection?"** → On the UR Fall Detection Dataset test split, the LSTM correctly classified 93 of 100 sequences as either "fall" or "non-fall." The 7% errors are mostly ambiguous slow-descent movements (sitting down quickly).

---

## SLIDE 4 — TECH STACK

**Status:** ✅ Fully implemented. Every item on this slide is running code.

### Backend Explanation

**Flask (Python 3.11) — single-threaded**
Flask by default runs a multi-threaded development server. We force single-threaded mode (`threaded=False`) because dlib's HOG face detector is not thread-safe — concurrent calls cause segmentation faults. In production, a single-threaded Flask process is acceptable because the facility's door doesn't handle hundreds of simultaneous requests.

**SQLite**
Four tables: `users` (registered persons), `access_logs` (every entry/denial event), `audit_logs` (every system action), `fall_history` (fall events with timestamps and confidence). SQLite was chosen over PostgreSQL because it requires zero server setup and runs entirely in-process.

**dlib + OpenCV**
dlib provides the ResNet-based face encoder (128-D embedding). OpenCV provides the HOG face detector as a fallback. Both libraries are C++ under the hood with Python bindings.

**MediaPipe**
Google's ML framework for real-time body landmark detection. Gives 33 body keypoints (nose, shoulders, elbows, wrists, hips, knees, ankles, etc.) per frame. Used by both the fall detector and the visibility checker.

**LSTM Neural Network**
A sequence model built in TensorFlow/Keras. Input: 30 frames × 33 keypoints = 30×33 tensor. Output: binary classification (fall / not fall) with a confidence score.

**YOLO26**
Object detection model used for weapon and hazard detection. Outperforms YOLOv8n and YOLOv8s on our evaluation. CLAHE (Contrast Limited Adaptive Histogram Equalization) preprocessing is applied to frames before inference to improve low-light performance.

### Frontend Explanation

**Next.js 16 App Router**
Server-side rendering for the initial page load, then client-side navigation. The `/api/*` routes are proxied by Next.js's built-in rewrite rules to the Flask server on port 5001.

**Tailwind CSS**
Utility-first CSS framework. Every class directly applies a CSS property (e.g., `bg-teal-500` = `background-color: #14b8a8`). No custom CSS files needed.

**Recharts**
React charting library. Used for: bar chart (hourly access), donut chart (access outcomes), line chart (LSTM confidence over time), stacked area chart (object detection events).

### ⚠️ Professor Questions

- **"Why SQLite instead of a proper database?"** → SQLite is sufficient for a single-facility deployment. It's file-based, zero-configuration, and the data volumes (hundreds of access events per day) are well within SQLite's performance envelope. For a multi-facility chain, we'd migrate to PostgreSQL.
- **"Why Flask instead of FastAPI?"** → Flask was chosen for familiarity and the ecosystem (Flask-CORS is well-tested). FastAPI would give async support, but we're running single-threaded anyway, so async wouldn't help here.
- **"Why not use a proper ORM like SQLAlchemy?"** → We used raw parameterized queries intentionally — it makes the SQL injection protection explicit and visible in code review, rather than hidden behind an ORM abstraction.
- **"How does the Next.js proxy work?"** → `next.config.js` has a `rewrites` rule: any request to `/api/*` from the browser gets transparently forwarded to `localhost:5001/api/*` on the server side. The browser never knows the Flask port exists.

---

## SLIDE 5 — SYSTEM ARCHITECTURE

**Status:** ✅ This diagram reflects the actual running system.

### How The Pipeline Works

1. **Camera Feed → Flask API:** A camera script (`scripts/camera.py`) captures frames and POSTs them as multipart form data to `/api/recognize`. On Raspberry Pi, this script runs as a systemd service.

2. **Flask API routing:** `api/routes.py` receives the request. It calls: face engine (dlib), threat detector, fall detector (if enabled), and optionally the object detector. All in one synchronous call stack.

3. **ML Engines:** Each engine is a Python class instantiated once at server startup (module-level singletons). They share the same SQLite connection pool.

4. **SQLite:** All events — access logs, alerts, fall events, audit entries — are written in the same transaction. Atomic writes ensure no partial records.

5. **Next.js Dashboard:** Polls Flask API endpoints every 15 seconds. The dashboard pages read from: `/api/logs`, `/api/alerts`, `/api/stats`, `/api/fall/stats`, `/api/objects/recent`.

### ⚠️ Professor Questions

- **"What happens if Flask crashes?"** → SQLite data is preserved (it's a file). The camera script would retry connections. In production, Flask would be managed by a process supervisor (gunicorn or systemd).
- **"How does the dashboard get real-time data?"** → Polling every 15 seconds. Not WebSockets — we evaluated them but polling is simpler and sufficient for this use case (alert response times of seconds, not milliseconds, are acceptable at the dashboard level).
- **"What's the latency end-to-end?"** → Camera capture (~33ms at 30fps) + Flask processing (45ms for face pipeline) + dashboard refresh (up to 15s). For the alert system, the alert is written to SQLite in the same 45ms window as recognition — it's immediate.

---

## SLIDE 6 — FACE RECOGNITION

**Status:** ✅ Fully implemented. Measured accuracy: 94.6%.

### Mechanism

**HOG Detection (dlib)**
Histogram of Oriented Gradients — a classical CV technique that finds edges and their directions in the image, then looks for a face-shaped pattern of edges. Very fast (~20ms). Works well in good lighting.

**128-D Face Encoding (dlib ResNet)**
dlib's `face_recognition_model_v1` is a ResNet-based neural network pretrained on a large face dataset. It maps any face crop to a 128-dimensional vector where similar faces are close in Euclidean space. This is the same technique used in FaceNet.

**Euclidean Distance Matching**
Given a new encoding `e_new`, compute distance to every stored encoding `e_i`. If `min(distance) < threshold`, it's a match. The threshold is calibrated per-environment using the auto-calibration tool.

**RecognitionBuffer**
A sliding window of the last N frame predictions. The system only commits to a recognition decision (and triggers an alert) when the buffer shows a consistent result. Prevents single-frame noise from triggering false alerts.

**Fallback to OpenCV HOG**
If dlib fails to initialize (missing model files, memory error), the system catches the exception and falls back to OpenCV's built-in HOG face detector with a simpler matching strategy. Accuracy drops to 70–80%.

### Key Code Files
- `facial_recognition.py` — main engine, RecognitionBuffer class
- `api/routes.py` — `/api/recognize` endpoint
- `scripts/calibrate.py` — threshold calibration tool
- `data/database.py` — `users` and `access_logs` table management

### ⚠️ Professor Questions

- **"What is a 128-D embedding?"** → A vector of 128 floating point numbers that represents the geometric structure of a face. Two photos of the same person will produce embeddings that are close together in 128-dimensional space. Two different people will produce embeddings far apart.
- **"How did you calibrate the threshold?"** → We built an auto-calibration script that runs over a sample of registered faces and computes the optimal threshold that maximizes the gap between same-person distances and different-person distances.
- **"What happens with glasses, masks, or lighting changes?"** → Accuracy degrades. HOG is sensitive to occlusion. In our test, Person C's 80% accuracy was due to lighting variation. The system is designed to fail to "unknown" (safer) rather than fail to "wrong person" (dangerous).
- **"Could someone fool the system with a photo?"** → Yes — this is a liveness detection gap. We documented it as a known limitation. Production systems would add liveness checks (blink detection, depth sensor). Out of scope for this research prototype.
- **"Why dlib over DeepFace or FaceNet directly?"** → dlib ships as a self-contained Python package with pre-trained weights included. No cloud dependency, no API key. The ResNet model it uses is equivalent quality to FaceNet for a small-scale deployment.

---

## SLIDE 7 — FALL DETECTION

**Status:** ✅ Both phases fully implemented. LSTM: 93% accuracy.

### Phase 1 Mechanism (Rules-Based)

**MediaPipe Pose Landmarks**
MediaPipe provides 33 landmarks, each with x, y, z coordinates normalized to frame dimensions. Key landmarks for fall detection: left/right hip (indices 23, 24), left/right shoulder (11, 12), nose (0).

**Rules Applied:**
1. **Hip height** — if `(hip_y / frame_height) > HIP_THRESHOLD` (i.e., hip is in the lower portion of the frame), score += 1
2. **Torso angle** — angle between shoulder midpoint and hip midpoint relative to vertical. If angle > `ANGLE_THRESHOLD`, score += 1
3. **Velocity** — `delta_hip_y / delta_time` — if downward velocity exceeds `VELOCITY_THRESHOLD`, score += 1
4. If `score >= 2`, classify as fall → CRITICAL alert → logged to `fall_history`
5. Cooldown timer: 10 seconds after a fall event before the detector can fire again

**Phase 2 Mechanism (LSTM)**

**Input Preparation**
Each frame contributes a 33-keypoint row to a buffer. After 30 frames, the buffer forms a 30×33 matrix. This matrix is the LSTM input.

**LSTM Architecture**
- Input layer: (30, 33)
- LSTM layer: 64 hidden units
- Dropout: 0.3
- Dense output: sigmoid activation → probability of fall

**Training**
Trained on UR Fall Detection Dataset (URFD). The dataset contains accelerometer and video data from real fall scenarios. We extracted MediaPipe keypoints from the video sequences as training data. Train/test split: 80/20. Optimizer: Adam. Loss: binary crossentropy.

**Stateful Implementation**
The `FallDetector` class is instantiated once at Flask startup. It holds the frame buffer as an instance variable. Each API call appends to the buffer and runs inference when the buffer is full.

### Key Code Files
- `models/fall_detection.py` — FallDetector class, both phases
- `api/routes.py` — `/api/fall/log`, `/api/fall/stats`
- `scripts/train_lstm.py` — LSTM training script
- `scripts/extract_keypoints.py` — URFD keypoint extraction

### ⚠️ Professor Questions

- **"What is an LSTM and why is it appropriate for fall detection?"** → LSTM (Long Short-Term Memory) is a recurrent neural network designed for sequential data. Fall detection is inherently temporal — a fall is a movement over time (standing → falling → on floor). A single-frame classifier can't see the motion; an LSTM can.
- **"Why 30 frames for the window?"** → At 30fps, 30 frames = 1 second of data. A typical fall takes 0.5–1 second. 30 frames captures the full event.
- **"How do you handle someone sitting down quickly? Wouldn't that trigger a fall?"** → This is the 7% error case. Slow deliberate sitting changes the velocity profile and torso angle differently than a fall. The LSTM learns these differences from the training data. The rules-based phase is more susceptible to this; the LSTM is more robust.
- **"What's the latency of the LSTM inference?"** → Under 10ms per 30-frame window on a modern CPU. The bottleneck is MediaPipe keypoint extraction (~15ms per frame).
- **"Did you train the LSTM yourself or use a pretrained model?"** → We trained it ourselves on URFD using TensorFlow/Keras. The training script is in `scripts/train_lstm.py`.

---

## SLIDE 8 — THREAT DETECTION

**Status:** ✅ All 7 rules operational.

### Mechanism For Each Rule

| Rule | Trigger Condition | Alert Level |
|---|---|---|
| Unrecognized Face | `min_distance > threshold` → no match found | HIGH |
| Repeated Failed Access | Same unknown encoding appears `N` times within session | HIGH |
| Unusual Access Times | `current_hour` outside `[OPEN_HOUR, CLOSE_HOUR]` from config | MEDIUM |
| Tailgating | More than 1 access event within 15 seconds of same door | HIGH |
| Wandering | Resident detected at door between 21:00 and 06:00 | MEDIUM |
| Repeated Falls | Same person_id has `fall_count >= REPEATED_FALL_THRESHOLD` in rolling window | CRITICAL |
| Object Detection | YOLO26 returns a class in `[WEAPON, SECURITY_THREAT]` with `confidence > threshold` | CRITICAL |

**All rules evaluated in `/api/recognize`** — no separate polling or background job. Rules are applied after face matching, using the recognized person's history from the database.

### YOLO26 Threat Categories
- `WEAPON`: gun, knife, scissors (confidence threshold 0.20)
- `SECURITY_THREAT`: threatening posture patterns
- `PARCEL`: package detection (lower threat, MEDIUM)
- `MOBILITY_AID`: wheelchair, walker (informational only)
- `OPERATIONAL`: staff equipment (not flagged)

CLAHE preprocessing: applied as `cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))` before YOLO26 inference. Significantly improves detection in uneven or low lighting.

### Key Code Files
- `models/threat_detection.py` — ThreatDetector class, all 7 rules
- `models/object_detection.py` — YOLO26 pipeline, CLAHE, category mapping
- `api/routes.py` — threat evaluation in `/api/recognize`

### ⚠️ Professor Questions

- **"How do you define 'tailgating' technically?"** → We check if the previous access event for the same door occurred within 15 seconds and was for a different person (or unknown). If both people appear in the same frame, that's a stronger signal — but the 15-second time window catches it even if they appear sequentially.
- **"What's the false positive rate for your threat rules?"** → We don't have a rigorous false positive rate measurement — that would require an extended deployment with labeled ground truth. We tested each rule manually and verified correct behavior. Real-world false positive tuning would require production data.
- **"What does CLAHE do exactly?"** → Contrast Limited Adaptive Histogram Equalization. It divides the image into tiles, equalizes each tile's histogram independently, then merges them with bilinear interpolation. The "contrast limited" part caps the amplification factor to prevent noise amplification. The result is better local contrast — dark corners of a frame become more visible.
- **"Why is the WEAPON threshold 0.20 rather than a higher value?"** → We chose a lower threshold because false negatives (missing a weapon) are more dangerous than false positives (flagging scissors). An alert at 0.20 confidence still goes to the dashboard for a human to review — it doesn't lock the door.

---

## SLIDE 9 — LIVE DASHBOARD

**Status:** ✅ All 5 pages implemented and running.

### How Each Page Works

**Main Dashboard**
- Polls `/api/stats` every 15 seconds for KPI numbers
- Polls `/api/logs?limit=10` for the recent events table
- Recharts `BarChart` visualizes hourly access data from `/api/stats/hourly`
- `PieChart`/`RadialBarChart` shows access outcomes (granted vs denied) from `/api/stats/outcomes`

**Alerts Page**
- Polls `/api/alerts` with severity filter params
- Each alert has: `person_id`, `alert_type` (maps to rule name), `severity`, `timestamp`, `details`
- Colour-coded badges: red (CRITICAL), amber (HIGH), blue (MEDIUM)

**Logs Page**
- Full paginated table from `/api/logs`
- Columns: person name, outcome, confidence score, timestamp, event type
- Sortable by column

**Compliance (Audit) Page**
- Reads from `/api/audit` — the `audit_logs` table
- Columns: actor, action, resource, result, timestamp
- CSV export button hits `/api/audit/export` which streams a CSV file

**Falls Monitor**
- LSTM confidence bar from `/api/fall/stats`
- Timeline of fall events with timestamps
- Detector state (rules-based or LSTM mode, cooldown status)

### ⚠️ Professor Questions

- **"Why polling instead of WebSockets?"** → Polling is simpler, stateless, and sufficient. WebSockets would require maintaining a persistent connection from the Next.js server to Flask, which adds complexity. For a 15-second alert display lag at the dashboard level, polling is fine.
- **"How does the CSV export work?"** → The Flask endpoint reads all audit_log rows for the requested date range, builds a CSV string using Python's `csv` module, and returns it with `Content-Disposition: attachment; filename=audit_export.csv`. The browser downloads it directly.
- **"What is the audit trail for?"** → Compliance auditors (health authority inspectors) can request a full record of who accessed what and when. The audit_logs table records every action the *system* takes, not just door events — including user registrations, deletions, and system restarts.
- **"What happens if the database is empty?"** → The dashboard uses synthetic demo data for all charts and KPIs. This is implemented in the frontend — if the API returns empty arrays, the Recharts components render with pre-built sample data rather than showing empty charts.

---

## SLIDE 10 — PIPEDA & PRIVACY COMPLIANCE

**Status:** ✅ Core privacy architecture implemented. ⚠️ Some items documented but not coded (JWT, encryption).

### What's Actually Implemented vs Documented Only

| Feature | Status |
|---|---|
| On-premises only — no outbound calls | ✅ Implemented |
| Data minimization — embeddings, not images | ✅ Implemented |
| Event-driven processing only | ✅ Implemented |
| Data retention policy (90d/1yr) — config.py | ✅ Implemented |
| Audit trail — audit_logs table | ✅ Implemented |
| Parameterized SQL queries | ✅ Implemented |
| Input validation | ✅ Implemented |
| CORS restriction | ✅ Implemented |
| Compliance dashboard + CSV export | ✅ Implemented |
| docs/COMPLIANCE.md — 10-principle mapping | ✅ Documented |
| SQLCipher database encryption | 🔧 Documented, not yet coded |
| JWT authentication | 🔧 Documented, not yet coded |
| Subject access request endpoint | 🔧 Documented as TODO |

### The 10 PIPEDA Principles — How We Map To Them

1. **Accountability** → Audit trail logs every action with actor
2. **Identifying Purposes** → Only face recognition and safety monitoring; stated in docs/COMPLIANCE.md
3. **Consent** → Resident registration is an explicit consent action; deletion available on request
4. **Limiting Collection** → Only embeddings collected, not images or audio
5. **Limiting Use, Disclosure, Retention** → Retention policy in config.py; data never disclosed externally
6. **Accuracy** → Confidence scores exposed; access logs allow review
7. **Safeguards** → Parameterized queries, input validation, CORS, on-premises
8. **Openness** → docs/COMPLIANCE.md is the transparency document
9. **Individual Access** → System supports face data deletion; export available via audit CSV
10. **Challenging Compliance** → docs/COMPLIANCE.md identifies the data steward

### ⚠️ Professor Questions

- **"If you don't have encryption, is the data actually secure?"** → The data is protected by file system permissions on the local machine. SQLCipher encryption is the next implementation step — it's fully documented in SECURITY.md with code examples, but we prioritized core features within scope. The on-premises model is the primary privacy protection.
- **"PIPEDA requires consent — how do you get consent from residents with cognitive impairment?"** → Consent is obtained from the legal guardian or power of attorney, not the resident directly. This is standard practice in elderly care. The registration workflow requires an admin action, not self-registration.
- **"What happens when a resident leaves the facility?"** → Their face data can be deleted via the API (`DELETE /api/persons/{person_id}`). This action is logged in audit_logs. The data retention policy also auto-expires records.
- **"What's the difference between audit_logs and access_logs?"** → `access_logs` records door events — who arrived, what the system decided, confidence score. `audit_logs` records system actions — who was registered, who was deleted, what data was exported. Audit logs are for compliance; access logs are for security review.

---

## SLIDE 11 — EVALUATION & RESULTS

**Status:** ✅ All metrics are from actual testing, not theoretical.

### How Each Number Was Measured

**94.6% face recognition**
- Test set: 37 photos across 3 people (not seen during threshold calibration)
- Person A: 15/15 = 100%
- Person B: 12/12 = 100%
- Person C: 8/10 = 80% (2 failures due to heavy lighting variation)
- Overall: 35/37 = 94.6%

**93% LSTM fall detection**
- Dataset: UR Fall Detection Dataset (URFD) — academic benchmark
- Split: 80% train, 20% test
- Metric: binary classification accuracy on held-out test sequences
- 93 correct out of 100 test sequences

**52.5 mAP YOLO26**
- Evaluation: compared YOLO26 against YOLOv8n (37.3 mAP) and YOLOv8s (44.9 mAP)
- mAP = mean Average Precision = area under Precision-Recall curve, averaged across object categories
- Measured on our evaluation set of door-scenario images

**45ms pipeline latency**
- Measured with Python `time.perf_counter()` around the full face pipeline
- Breakdown: ~20ms detection, ~15ms encoding, ~10ms matching

### ⚠️ Professor Questions

- **"Your test set for face recognition is only 37 photos — is that statistically significant?"** → No, not for a production system. This is a proof-of-concept. A production deployment would require hundreds of photos per person across varied conditions (lighting, angle, glasses, time of day). We acknowledge this in the limitations section of our report.
- **"How does your fall detection compare to state-of-the-art?"** → URFD benchmark papers report 90–96% accuracy. Our 93% LSTM is within that range, which validates our approach, though we're using a simpler architecture than the best published models.
- **"What's 52.5 mAP in plain English?"** → If you ask the model to find all weapons in 100 images, on average it finds them with about 52.5% precision-recall trade-off balance. It's imperfect but meaningful — good enough to flag events for human review.
- **"Did you test the system under real conditions — low light, crowded frames, etc.?"** → We tested with lighting variation (which caused the 80% for Person C) and CLAHE preprocessing helps with low light. We didn't test with crowded multi-person frames systematically — another limitation we'd address in production.

---

## SLIDE 12 — CHALLENGES & LESSONS LEARNED

**Status:** ✅ These are real engineering problems we solved (or consciously decided not to).

### Challenge Details

**OpenCV + Threading**
The segfault was reproducible — any concurrent call to `dlib.get_frontal_face_detector()` in two threads caused a memory access violation. Fix: `app.run(threaded=False)` in Flask. The tradeoff is no concurrent requests, but that's acceptable.

**LSTM State Management**
The core problem: HTTP is stateless, but the LSTM needs 30 frames of sequential data. If we stored state in the request, we'd need the client to maintain a buffer (impossible for a camera script). Solution: server-side singleton. The `FallDetector` instance lives at module level, not in the request context. This means restarting Flask resets the buffer — acceptable.

**Low-light Detection**
YOLO26 inference on dark frames returned low-confidence results for everything. CLAHE preprocessing (applied as a numpy array transformation before inference) significantly improved contrast and confidence scores on weapon categories in dark conditions.

**Threshold Calibration**
The default Euclidean distance threshold (0.6) works for many faces but not all — some people with similar facial geometry score below 0.6 for different people. We built `scripts/calibrate.py` which sweeps threshold values and finds the optimal separation for the specific registered face set.

### ⚠️ Professor Questions

- **"How did you find the threading bug?"** → By reading the dlib documentation and the Flask documentation for production deployment. dlib explicitly warns against multi-threaded use of the detector objects.
- **"Is a singleton pattern safe in a web server?"** → In our single-threaded Flask, yes. In a multi-threaded server, the singleton would need a mutex/lock around the frame buffer operations. We document this in the architecture notes.
- **"What would you do differently with more time?"** → SQLCipher for database encryption, JWT for proper authentication, WebSockets for real-time dashboard updates, and a larger test set for face recognition validation.

---

## SLIDE 13 — THANK YOU

**Status:** Summary slide.

**Be ready for:** The professor will likely use this moment to ask specific follow-up questions. The most common areas:

1. **"Walk me through the code for [specific feature]"** — be ready to open the actual file
2. **"Who wrote this specific part?"** — each person must know their own code cold
3. **"What would happen if [edge case]?"** — think: no face detected, camera disconnected, database full
4. **"How does this compare to existing commercial solutions?"** — FaceDoor is privacy-first, on-premises, and purpose-built for elderly care. Commercial equivalents (Verkada, Avigilon) require cloud connectivity and per-seat licensing.
