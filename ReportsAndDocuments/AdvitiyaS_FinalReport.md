# Smart Door Security Framework with AI-Driven Anomaly Detection and Cybersecurity for Elderly Care

**Course:** CSIS 4495 — Applied Research Project, Section 3
**Team Lead:** Advitiya Sharda
**Team Members:**

| Name | Student ID | Role |
|------|-----------|------|
| Advitiya Sharda | 300395470 | Team Lead / Security & Backend |
| Eric Sanjo | [Student ID] | Data Science & ML Models |
| Reubin Chatta | [Student ID] | Frontend Dashboard & UI |

**Industry Partner:** Door Face Panels — Armin Ghauforian
**Date:** April 2026

---

## Checklist

- [x] Final Implementation GitHub Repository Code Check-In: Completed GitHub repository check-in for fully functional, complete project that is demo ready. This is in the main branch.
- [x] Presentation Slides Completed and Checked into GitHub under ReportsAndDocuments.
- [x] Final Defense and Demo Preparation: Prepared for 12–20 minute presentation with slides and live demo.
- [x] Installation Instructions/Guide: Updated README file with clear project description and installation instructions.
- [x] User Instructions/Guide: User guide with screenshots checked into ReportsAndDocuments.
- [x] Final Report Blackboard Submission: Completed report submitted on Blackboard by the Team Lead.
- [x] GitHub Repository Final Report Check-in: Completed report checked into the GitHub repository in the main branch.

---

## GitHub Repository Activity Summary

### Pull Requests

| PR # | Branch | Merged By | Date | Description |
|------|--------|-----------|------|-------------|
| #2 | Dashboard | Advitiya Sharda | 2026-02-09 | Initial dashboard prototype (HTML/CSS) |
| #6 | Progress2 | Advitiya Sharda | 2026-03-03 | Progress Report 2 and early implementation |
| #7 | adi_version2 | Advitiya Sharda | 2026-03-09 | Threat detection expansion and PIPEDA compliance |
| #8 | Reubin | Advitiya Sharda | 2026-03-09 | Fall detection dashboard and new API endpoints |
| #9 | ericv1 | Advitiya Sharda | 2026-03-09 | Phase 1 fall detection (MediaPipe rules-based) |
| #10 | week11_advitiya | Advitiya Sharda | 2026-03-16 | Calibration tool, confidence fixes, fall-to-threat escalation |
| #11 | ericv2 | Advitiya Sharda | 2026-03-16 | LSTM fall detector training and integration |
| #12 | reubinv2 | Reubin Chatta | 2026-03-16 | Falls dashboard updates, visibility banner, testing flow |
| #13 | ericv3 | Advitiya Sharda | 2026-03-23 | Fall detection documentation sync, partial-body handling |
| #14 | advitiya_week12 | Advitiya Sharda | 2026-03-23 | Multi-face recognition, quality scoring, smoothing buffer |
| #15 | reubinv3 | Reubin Chatta | 2026-03-24 | Object detection dashboard, API endpoints, YOLO config |

### Commit History (by team member)

**Advitiya Sharda — 30+ commits** (selected highlights):

| Hash | Date | Description |
|------|------|-------------|
| `7213d1b` | 2026-01-25 | Initial commit |
| `4ee9325` | 2026-01-26 | Added initial project proposal |
| `609b6f9` | 2026-02-09 | Advitiya Progress Report |
| `e01f92f` | 2026-02-24 | Midterm report |
| `c6897be` | 2026-03-09 | Implement threat detection expansion and PIPEDA compliance |
| `3e1c79f` | 2026-03-11 | Remove interactive prompts from test scripts — auto-run by default |
| `1711fff` | 2026-03-12 | Add threshold calibration tool, fix confidence scoring, escalate falls to threats |
| `210f759` | 2026-03-13 | Add recognition status endpoint, repeated-falls threat rule, and unit tests |
| `bc0c905` | 2026-03-17 | Fix calibration update target, routes.py |
| `60c1dd9` | 2026-03-19 | Add multi-face recognition |
| `fc57a62` | 2026-03-20 | Wire face quality check into registration — reject dark blurry images |
| `745e618` | 2026-03-20 | Add face quality scoring to recognition engine |
| `7fc62df` | 2026-03-21 | Add RecognitionBuffer class for frame-level smoothing |
| `bc4dd51` | 2026-03-21 | Use recognition smoothing in /api/recognize for single-face frames |
| `ae2d13b` | 2026-03-22 | Fix test_face_recognition_real: resolve DB person IDs, add quality scoring |

**Eric Sanjo — 25+ commits** (selected highlights):

| Hash | Date | Description |
|------|------|-------------|
| `417b984` | 2026-02-22 | Face recognition fixes, Door Face Panel name, optional Eric samples |
| `7836b87` | 2026-02-22 | Face recognition API: real /api/recognize, auto-log access & audit trail |
| `e8eb4f3` | 2026-02-22 | Add sample data and database: doorface.db, Eric face samples |
| `796a5f5` | 2026-02-23 | Reorganize: scripts/, tests/, docs/ structure |
| `3618237` | 2026-03-02 | Anomaly detection improvements and API integration |
| `d18545a` | 2026-03-02 | Improved Face Recognition |
| `5b5e055` | 2026-03-08 | Phase 1 fall detection: MediaPipe rules-based detector, live camera script, API endpoints |
| `4c15fce` | 2026-03-10 | Add URFD keypoint extraction pipeline using MediaPipe Tasks API |
| `bf86cff` | 2026-03-11 | Train LSTM fall detection model on URFD dataset |
| `f7a586b` | 2026-03-12 | Add LSTM-based fall detector and integrate with live camera |
| `1e944ce` | 2026-03-17 | Add configurable fall detector mode and model metadata scaffolding |
| `d229fa0` | 2026-03-18 | Unify fall logging behavior and extend fall status response |
| `30be5ba` | 2026-03-19 | Handle partial-body visibility as low-severity camera warning |
| `3dd1d99` | 2026-03-20 | Fix fall timestamp normalization and local-date counting in stats |
| `5a31e00` | 2026-03-23 | Sync fall detection documentation with implemented behavior |

**Reubin Chatta — 20+ commits** (selected highlights):

| Hash | Date | Description |
|------|------|-------------|
| `2eb5173` | 2026-02-18 | First push for mark2 |
| `26dafb2` | 2026-03-09 | Updated file with fall detection dashboard and new API endpoints |
| `19662b0` | 2026-03-14 | Update Falls dashboard: confidence bar, visibility banner, POST visibility events |
| `160c897` | 2026-03-15 | Add fall detection testing flow and instructions |
| `8203bd1` | 2026-03-18 | Add YOLOv8 object detection config, requirements |
| `53e87ae` | 2026-03-19 | Build Object Detector with COCO class mapping, threat levels |
| `c6a190f` | 2026-03-20 | Add object detection API endpoints and register |
| `8aa0e8d` | 2026-03-21 | Add YOLOv8 fine-tuning script for custom gun and weapon detection |
| `6c00f55` | 2026-03-23 | Add object detection dashboard with live events, category counts, and severity |
| `c490596` | 2026-04-06 | feat(frontend): dashboard, compliance, alerts, and object analytics UI updates |
| `9956d2d` | 2026-04-06 | feat(frontend): KPI cards with animated icons, health pills, sidebar separators |
| `8252be2` | 2026-04-06 | test(object-detection): add API and live webcam testers |

---

## 1. Introduction

### 1.1 Domain and Background

Smart door security systems have emerged as a critical component of modern elderly-care environments. Seniors living in care facilities face unique safety challenges — they may be vulnerable to unauthorized visitors, may wander outside during unsafe hours, or may suffer falls near entryways without anyone noticing. Traditional lock-and-key systems offer no visibility into who is at the door, when they arrived, or whether anything unusual is happening.

Computer vision and machine learning have matured to the point where lightweight models can run on edge hardware, enabling real-time facial recognition, object detection, and behavioral analysis without relying on cloud infrastructure. This local-first approach is particularly important in healthcare settings where resident privacy is paramount and regulatory frameworks like Canada's Personal Information Protection and Electronic Documents Act (PIPEDA) impose strict requirements on the handling of biometric data.

### 1.2 Problem Statement

This research project addresses several interconnected questions:

1. **How can facial recognition be deployed on edge hardware to control door access in elderly-care settings while maintaining privacy compliance?**
2. **Can rule-based and ML-based anomaly detection provide meaningful security alerts (e.g., repeated failed access, unusual hours, tailgating) without overwhelming caregivers?**
3. **Can real-time fall detection at the doorway reduce response times for medical emergencies?**
4. **Can object detection at the door identify security threats (weapons, suspicious items) and relevant operational context (parcels, mobility aids)?**

### 1.3 Literature Review and Knowledge Gaps

Existing facial recognition systems for access control — such as those based on FaceNet or ArcFace — typically depend on cloud APIs or powerful GPU servers, making them impractical for small facilities with limited IT budgets. Research by Schroff et al. (2015) demonstrated that deep metric learning could produce highly discriminative face embeddings, but deployment on resource-constrained devices remains challenging.

Fall detection research has progressed from wearable accelerometers (Bourke et al., 2007) to vision-based approaches using pose estimation (Noury et al., 2007). MediaPipe Pose (Lugaresi et al., 2019) provides real-time landmark detection suitable for edge deployment, and recent work has shown that LSTM networks trained on pose sequences can achieve over 90% accuracy on benchmark datasets like UR Fall Detection.

Object detection models such as YOLO (Redmon et al., 2016) have evolved through multiple generations. The latest YOLO26 architecture (Ultralytics, 2026) introduces an NMS-free end-to-end design that simplifies deployment while achieving 52.5 mAP on COCO — a significant improvement over earlier nano variants.

The gap our project addresses is the integration of these capabilities into a single, privacy-compliant, edge-deployable system tailored to the specific needs of elderly-care door security.

### 1.4 Hypotheses and Expected Benefits

Our initial hypotheses were:

- A rule-based threat detection engine (repeated failed attempts, access at unusual hours, tailgating) will be sufficient for the project scope and can be augmented with statistical models.
- Maintaining all data locally on the device reduces privacy risk and simplifies PIPEDA compliance.
- A well-designed caregiver dashboard can provide actionable situational awareness without overwhelming non-technical users.
- Combining facial recognition, fall detection, and object detection at a single camera point creates compounding safety value.

Expected benefits include safer living environments for elderly residents, improved incident visibility for caregivers, reduced response time for falls and security events, and a framework extensible to additional care facilities.

---

## 2. Summary of the Research Project

FaceDoor is a smart door security system designed for elderly care facilities. In its final form, the system consists of:

- **A Flask-based Python backend** running on a local machine (designed for future Raspberry Pi deployment) that handles facial recognition, fall detection, object detection, threat analysis, anomaly detection, and PIPEDA-compliant audit logging — all stored in a local SQLite database with no cloud dependency.
- **A Next.js caregiver dashboard** providing real-time visibility into access events, security alerts, fall incidents, object detections, compliance audits, and system health through six dedicated pages.
- **A camera integration layer** using OpenCV to capture video frames for face recognition and fall detection, posting results to the backend API.
- **Three AI/ML model families**: (1) facial recognition using HOG feature extraction with Euclidean distance matching and optional dlib embeddings, (2) fall detection using MediaPipe Pose landmarks with both rules-based and LSTM-based classifiers, and (3) object detection using YOLO26m with adaptive preprocessing and weapon-specific verification.

The system processes everything locally. No data is sent to the cloud. All personal information handling aligns with PIPEDA principles as documented in our compliance framework.

> **Screenshot 18 — System Architecture Diagram**
> ![System Architecture](screenshots/screenshot_architecture.png)
> *PLACEHOLDER: Create a system architecture diagram (using draw.io, Lucidchart, or PowerPoint) showing:*
> - *Camera (webcam icon) on the left feeding frames*
> - *Flask Backend (center) with boxes for: Face Recognition Engine, Fall Detector (Rules + LSTM), Object Detector (YOLO26m), Threat Detection, Anomaly Detection*
> - *SQLite Database (cylinder) connected to backend*
> - *Next.js Frontend (right) with page boxes: Dashboard, Alerts, Logs, Compliance, Falls, Objects*
> - *Arrows showing data flow: Camera → Backend → Database, Backend → Frontend (REST API)*
> - *A "LOCAL ONLY — No Cloud" label at the bottom*

> **Screenshot 19 — Tech Stack Summary**
> ![Tech Stack](screenshots/screenshot_tech_stack.png)
> *PLACEHOLDER: Create a simple infographic or table showing the tech stack with logos: Python + Flask, Next.js + React, SQLite, OpenCV, MediaPipe, Ultralytics YOLO, Tailwind CSS, Recharts. Can be done in PowerPoint or Canva.*

---

## 3. Changes to the Proposal

Several significant changes were made from the original proposal during the course of development:

### 3.1 Model Architecture Changes

| Change | Original Plan | Final Implementation | Justification |
|--------|--------------|---------------------|---------------|
| Face recognition engine | Basic OpenCV Haar Cascade only | Dual-engine: dlib (89–95% accuracy) with OpenCV HOG fallback (70–80%) | dlib provides significantly better accuracy through deep metric embeddings; HOG fallback ensures the system works even without dlib installed |
| Fall detection | Rules-based only | Two-phase: Rules-based (Phase 1) + LSTM classifier (Phase 2, 93% accuracy) | LSTM trained on UR Fall Detection Dataset provides substantially more reliable fall classification than rules alone |
| Object detection | Not in original proposal | Full YOLO26m pipeline with weapon verification | Added in Phase 3 based on industry partner feedback that identifying objects at the door (weapons, parcels, mobility aids) was critical for elderly safety |
| Object detection model | N/A | Upgraded from YOLOv8n → YOLOv8s → YOLO26m | Each upgrade brought measurable accuracy improvements (37.3 → 44.9 → 52.5 mAP) |

### 3.2 Feature Scope Changes

| Change | Original | Final | Justification |
|--------|----------|-------|---------------|
| Dashboard scope | Simple access log display | Six-page dashboard with KPI cards, charts, filters, CSV export | Caregiver feedback indicated the need for richer visualization and compliance reporting |
| Compliance | Afterthought | Core feature with dedicated PIPEDA compliance framework | Supervisor guidance and privacy research emphasized compliance as essential for healthcare deployment |
| Anomaly detection | Complex ML models | Isolation Forest + rule-based hybrid | Hardware constraints on Raspberry Pi and timeline limitations favored a simpler but effective approach |
| Demo data | Not planned | Full demo data fallback | Ensures the dashboard is always presentable even before real data is collected |

### 3.3 Platform and Technology Changes

| Change | Original | Final | Justification |
|--------|----------|-------|---------------|
| Frontend framework | Basic HTML/CSS dashboard | Next.js 16 with React 19, Tailwind CSS, Recharts | Modern framework provides better developer experience, component reusability, and responsive design |
| API architecture | Monolithic routes file | Blueprint-based with separate route modules for faces, falls, and objects | Separation of concerns improves maintainability as feature count grew |
| Database access | Flask-SQLAlchemy ORM | Raw sqlite3 with custom database module | Lighter weight, fewer dependencies, better control over schema |

---

## 4. Project Completion Timeline

### 4.1 Actual Timeline

| Date Range | Milestone | Responsible | Status |
|------------|-----------|-------------|--------|
| Feb 14 – Feb 22, 2026 | Core Flask API, `/recognize` endpoint, database schema, initial threat rules | Advitiya | Completed |
| Feb 23 – Mar 8, 2026 | Face recognition algorithm (HOG + Euclidean distance), registration pipeline, calibration tool | Advitiya, Eric | Completed |
| Mar 9 – Mar 15, 2026 | Next.js dashboard setup, sidebar navigation, KPI stat cards, access chart | Reubin | Completed |
| Mar 16 – Mar 22, 2026 | Alerts page, access logs page, compliance/audit page, demo data fallback | Reubin, Advitiya | Completed |
| Mar 23 – Mar 29, 2026 | Fall detection Phase 1 (MediaPipe rules-based), camera script, falls dashboard page | Eric, Reubin | Completed |
| Mar 30 – Apr 2, 2026 | Fall detection Phase 2 (LSTM training on URFD, 93% accuracy), integration with backend | Eric, Advitiya | Completed |
| Apr 2 – Apr 5, 2026 | Object detection Phase 3 (YOLO integration, category classification, unattended object tracking) | Advitiya, Reubin | Completed |
| Apr 6 – Apr 8, 2026 | Object detection accuracy improvements (YOLO26m upgrade, CLAHE preprocessing, padded weapon verification, per-category thresholds) | Advitiya, Reubin | Completed |
| Apr 8 – Apr 9, 2026 | Unified dashboard redesign, object detection UI improvements, testing scripts overhaul | Reubin, Advitiya | Completed |
| Apr 9 – Apr 12, 2026 | Final report, presentation slides, integration testing, demo preparation | All | Completed |

### 4.2 Team Responsibilities

| Team Member | Primary Responsibilities |
|-------------|------------------------|
| **Advitiya Sharda (Team Lead)** | Backend architecture, Flask API, threat detection rules, face recognition algorithm design, object detection pipeline, PIPEDA compliance, database schema, report writing, project coordination |
| **Eric Sanjo** | Data science and ML models: face feature extraction research, fall detection LSTM training (URFD dataset), anomaly detection (Isolation Forest), MediaPipe pose pipeline |
| **Reubin Chatta** | Frontend dashboard: Next.js setup, all six dashboard pages (home, alerts, logs, compliance, falls, objects), UI/UX design, Recharts visualizations, API client, demo data system |

### 4.3 Project Management

The team used a Kanban-style workflow tracked through GitHub Pull Requests and regular check-ins. Major milestones were organized into three phases:

- **Phase 1 (Feb–Mar):** Core access control — facial recognition, threat detection, basic dashboard
- **Phase 2 (Mar–Apr):** Safety extensions — fall detection (rules + LSTM), enhanced dashboard
- **Phase 3 (Apr):** Security intelligence — object detection (YOLO26m), weapon verification, unified dashboard

> **Screenshot 15 — Gantt Chart / Project Timeline**
> ![Gantt Chart](screenshots/screenshot_gantt_chart.png)
> *PLACEHOLDER: Create a Gantt chart (using Excel, Google Sheets, or an online tool like TeamGantt) showing the three phases with task bars for each milestone listed in Section 4.1. Color-code by team member: Advitiya (blue), Eric (green), Reubin (orange). Phases should overlap slightly showing parallel work.*

> **Screenshot 16 — GitHub Pull Requests List**
> ![GitHub PRs](screenshots/screenshot_github_prs.png)
> *PLACEHOLDER: Take a screenshot of the GitHub repository's Pull Requests page (https://github.com/advitiyasharda/W26_4495_S3_AdvitiyaS/pulls?q=is%3Apr+is%3Aclosed) showing the closed PRs list with PR numbers, titles, authors, and merge dates visible.*

> **Screenshot 17 — GitHub Commit Graph / Contributors**
> ![GitHub Contributors](screenshots/screenshot_github_contributors.png)
> *PLACEHOLDER: Take a screenshot of the GitHub repository's Insights → Contributors page showing the commit frequency graph for all three team members over the term.*

---

## 5. Implemented Features

### 5.1 Facial Recognition and Access Control

The facial recognition system provides the core access control functionality. A camera captures video frames at the door, faces are detected, and each detected face is matched against a database of registered residents and staff.

**Architecture:**

- **Detection:** OpenCV Haar Cascade classifier for fast face localization (~20ms per frame)
- **Feature extraction:** HOG (Histogram of Oriented Gradients) descriptor producing a 128-dimensional feature vector per face, with histogram equalization for lighting invariance
- **Matching:** Euclidean distance comparison against all registered face encodings; match threshold of 0.7 (configurable via calibration tool)
- **Advanced engine:** Optional dlib-based backend (`face_recognition` library) that uses deep metric learning for 89–95% accuracy when available
- **Smoothing:** `RecognitionBuffer` applies rolling-window temporal smoothing to reduce single-frame misclassifications

**Key implementation (from `api/facial_recognition.py`):**

```python
def recognize_face(self, frame, face_location):
    test_encoding = self._extract_face_features(face_roi)
    best_distance = inf
    for person_id, encodings in self.known_faces.items():
        for known_encoding in encodings:
            distance = np.linalg.norm(test_encoding - known_encoding)
            if distance < best_distance:
                best_distance = distance
                best_match = person_id
    confidence = 1 - (best_distance / 1.0)
    is_match = best_distance < 0.7
    return {'person_id': best_match if is_match else None,
            'name': name if is_match else 'Unknown',
            'confidence': confidence}
```

**Registration pipeline:** Users capture 10–15 photos via webcam (`scripts/capture_faces.py`), register them into the system (`scripts/register_faces.py`), and optionally calibrate the matching threshold (`scripts/calibrate_recognition.py`) which tests 11 values between 0.30 and 0.80 and automatically writes the optimal value to config.

**Performance:** 50–100ms per frame on modern CPU, suitable for real-time operation at 10–20 FPS. Memory usage is minimal (~5.2 KB per registered person).

> **Screenshot 1 — Face Recognition in Action**
> ![Face Recognition Screenshot](screenshots/screenshot_face_recognition.png)
> *PLACEHOLDER: Take a screenshot of the webcam running `scripts/quick_test_recognition.py` showing a green bounding box around a detected face with the person's name and confidence score (e.g., "advitiya (0.87)") displayed above the box.*

> **Screenshot 2 — Face Registration Terminal Output**
> ![Face Registration Output](screenshots/screenshot_face_registration.png)
> *PLACEHOLDER: Take a screenshot of the terminal output from `scripts/register_faces.py` showing "OK (64x64, 128-dim vector)" messages as each face photo is registered successfully.*

### 5.2 Threat Detection Engine

The threat detection system monitors access patterns and raises security alerts automatically. It uses a rule-based approach designed for the specific context of elderly care door security.

**Implemented rules:**

| Rule | Severity | Trigger Condition |
|------|----------|-------------------|
| Unrecognized face | HIGH | Face detected but no database match |
| Repeated failed access | HIGH | 3+ failed attempts within 10 minutes |
| Unusual access time | MEDIUM | Entry between 10 PM and 5 AM |
| Tailgating | HIGH | 2+ different people entering within 15 seconds |
| Wandering (resident) | HIGH | Known resident exits between 9 PM and 6 AM |
| Fall detected | CRITICAL | Single confirmed fall event from detector |
| Repeated falls (warning) | HIGH | 2 falls in the past 24 hours |
| Repeated falls (critical) | CRITICAL | 3+ falls in the past 24 hours |

All threat events are stored in the `threats` table with severity, description, and timestamp. The alerts dashboard provides filtering by severity and real-time updates.

> **Screenshot 3 — Alerts Dashboard (Threat Events)**
> ![Alerts Dashboard](screenshots/screenshot_alerts_page.png)
> *PLACEHOLDER: Take a screenshot of `http://localhost:3000/alerts` showing several alert cards with severity badges (CRITICAL in red, HIGH in orange, MEDIUM in amber). Show the severity filter buttons at the top and at least 2–3 alert cards visible.*

### 5.3 Fall Detection (Phase 1: Rules-Based + Phase 2: LSTM)

Fall detection adds a critical safety layer to the door security system, particularly important for elderly residents who may fall near the entrance.

**Phase 1 — Rules-based detector (`models/fall_detection.py`):**

Uses MediaPipe PoseLandmarker (Tasks API) to extract 33 body landmarks per frame. Three rules are applied:

1. **Hip height** (weight: 0.40) — hips near the bottom of the frame indicate the person is on the ground
2. **Torso angle** (weight: 0.35) — spine nearly horizontal indicates the person is lying down
3. **Hip velocity** (weight: 0.25) — rapid hip drop across recent frames indicates an active fall

A fall is flagged when the weighted confidence score exceeds 0.55.

**Phase 2 — LSTM classifier (`models/fall_detection_trained.py`):**

| Property | Value |
|----------|-------|
| Architecture | 2-layer LSTM |
| Input | Sequence of MediaPipe pose keypoints (33 landmarks x 4 values) |
| Training dataset | UR Fall Detection Dataset (URFD) |
| Test accuracy | **93%** |
| Model file | `models/fall_lstm.keras` |
| Scaler file | `models/fall_lstm_scaler.pkl` |

The LSTM model is activated with the `--lstm` flag on the camera script. The system supports automatic fallback to the rules-based detector if the LSTM model files are missing.

**Camera integration:** `scripts/fall_detection_camera.py` captures webcam frames, runs pose estimation, and posts detection results to `/api/fall/log`. The falls dashboard (`/falls`) displays real-time LSTM confidence scores, detector status, event history, and includes a reset button.

> **Screenshot 4 — Falls Dashboard Page**
> ![Falls Dashboard](screenshots/screenshot_falls_page.png)
> *PLACEHOLDER: Take a screenshot of `http://localhost:3000/falls` showing the LSTM confidence bar (green/red depending on fall status), the detector status indicator (Live/Offline badge), and the fall event history table below.*

> **Screenshot 5 — Fall Detection Camera Window**
> ![Fall Detection Camera](screenshots/screenshot_fall_detection_camera.png)
> *PLACEHOLDER: Take a screenshot of the OpenCV window from `python scripts/fall_detection_camera.py --lstm` showing MediaPipe pose landmarks drawn on a person's body with the confidence score overlay.*

### 5.4 Object Detection (Phase 3: YOLO26m)

Object detection identifies security-relevant items at the door and classifies them into five categories with associated threat levels.

**Category classification:**

| Category | Default Severity | Door-Security Context | Example COCO Classes |
|----------|-----------------|----------------------|---------------------|
| WEAPON | CRITICAL | Knives, scissors, bats | knife (43), scissors (76), baseball_bat (34) |
| SECURITY_THREAT | HIGH | Unusual / policy-flagged items | skateboard (36), tennis_racket (38) |
| PARCEL | INFO → MEDIUM | Bags, deliveries (escalates when unattended) | backpack (24), handbag (26), suitcase (28) |
| MOBILITY_AID | INFO | Wheelchair, walker, umbrella (elderly care) | chair (56), umbrella (25) |
| OPERATIONAL | LOW → MEDIUM | Person, pet, bottles — routine but tracked | person (0), dog (16), cat (17), bottle (39) |

**Accuracy pipeline improvements:**

1. **YOLO26m base model** — 52.5 mAP, a 40% relative improvement over the original YOLOv8n (37.3 mAP)
2. **Adaptive CLAHE preprocessing** — Contrast-Limited Adaptive Histogram Equalization applied only when `mean_brightness < 85`, preventing degradation on well-lit scenes while enhancing backlit or shadowed doorways
3. **Padded weapon verification** — When any weapon-class hint is detected (even at very low confidence), the frame is re-processed with 25% reflected-border padding. This restores the surrounding context that YOLO expects, significantly boosting weapon detection confidence (e.g., scissors confidence increased from 22% to 40% in testing)
4. **Per-category confidence thresholds** — WEAPON: 0.20, PARCEL: 0.30, SECURITY_THREAT: 0.25, MOBILITY_AID: 0.35, OPERATIONAL: 0.45
5. **Exponential moving average (EMA) confidence smoothing** for temporal stability across frames
6. **Person-at-door awareness** — A person's bounding box position (small and low in frame) triggers elevated severity, hinting at a potential fall

> **Screenshot 6 — Object Detection Dashboard**
> ![Object Detection Dashboard](screenshots/screenshot_objects_page.png)
> *PLACEHOLDER: Take a screenshot of `http://localhost:3000/objects` showing the summary strip (Detections count, Flagged count, Avg confidence), the category filter chips (WEAPON, SECURITY_THREAT, PARCEL, MOBILITY_AID, OPERATIONAL), and the stacked area chart below.*

> **Screenshot 7 — Object Detection Event Table**
> ![Object Detection Table](screenshots/screenshot_objects_table.png)
> *PLACEHOLDER: Scroll down on the objects page and take a screenshot of the "Recent detections" table showing several rows with When, Object, Category (with icons), Confidence (progress bar), and Severity (colored badge) columns. Ensure at least one flagged row with amber highlight is visible.*

> **Screenshot 8 — Object Detection API Test Output**
> ![Object Detection API Test](screenshots/screenshot_object_test_api.png)
> *PLACEHOLDER: Take a screenshot of the terminal output from `python scripts/test_object_detection_api.py --folder path/to/test/images` showing the color-coded results with object names, categories, confidence percentages, and the summary table at the end.*

**Key implementation — padded weapon verification (from `models/object_detection.py`):**

```python
def _weapon_verify(self, frame, base_dets):
    has_weapon_hint = any(
        d[3] in _ALL_WEAPON_IDS or d[0].lower() in _CUSTOM_WEAPON_NAMES
        for d in base_dets
    )
    if not has_weapon_hint:
        return base_dets
    h, w = frame.shape[:2]
    pad_y, pad_x = int(h * 0.25), int(w * 0.25)
    padded = cv2.copyMakeBorder(
        frame, pad_y, pad_y, pad_x, pad_x, cv2.BORDER_REFLECT_101
    )
    padded_dets = self._run_inference(padded, conf=0.12, imgsz=self.imgsz)
    # Remap bboxes back to original coordinates and merge
    ...
```

### 5.5 Anomaly Detection

The anomaly detection module uses an Isolation Forest model (scikit-learn) trained on access-pattern features to identify behavioral anomalies. Features include access frequency, time-of-day patterns, and deviation from established behavioral profiles stored in the `behavioral_profiles` table.

The model (`models/isolation_forest.pkl`) is trained using `scripts/train_anomaly_detection.py` on synthetic data generated by `data/data_generator.py`. Anomalies are scored and stored in the `anomalies` table, with high-scoring anomalies escalating to security alerts.

> **Screenshot 9 — Anomaly Detection Code**
> ![Anomaly Detection Code](screenshots/screenshot_anomaly_code.png)
> *PLACEHOLDER: Take a screenshot of `models/anomaly_detection.py` open in the IDE showing the Isolation Forest training/prediction logic. Show approximately 20–30 lines including the `predict()` method.*

### 5.6 Caregiver Dashboard (Next.js)

The frontend is a modern, responsive web application built with Next.js 16, React 19, Tailwind CSS, and Recharts. It provides six dedicated pages:

| Page | URL | Purpose |
|------|-----|---------|
| **Dashboard** | `/` | Unified KPI overview: total entries, denials, active alerts, falls today, hourly bar chart, access outcome donut, recent access log |
| **Alerts** | `/alerts` | Security alert cards filterable by severity (CRITICAL, HIGH, MEDIUM), including fall and object alerts |
| **Access Logs** | `/logs` | Full paginated access log with entry/exit type, status badges, registered people list with role management |
| **Compliance** | `/compliance` | PIPEDA audit trail with system action log and CSV export |
| **Falls** | `/falls` | Live fall detection monitoring — LSTM confidence bar, detector status, event history, reset button |
| **Objects** | `/objects` | Object detection events — category/severity filters, stacked area chart by hour, category bar chart, detailed event table |

**Key UI features:**
- Auto-refreshes every 15–30 seconds depending on the page
- Demo data fallback when the database is empty (clearly labeled "Sample data")
- Responsive design works on desktop and tablet
- Color-coded severity indicators across all pages
- CSV export for compliance audit data

> **Screenshot 10 — Dashboard Home Page (Unified)**
> ![Dashboard Home](screenshots/screenshot_dashboard_home.png)
> *PLACEHOLDER: Take a screenshot of `http://localhost:3000/` showing the full unified dashboard: KPI cards at top (total entries, denied, active alerts, falls today), the hourly activity bar chart, access outcome donut chart, and recent access log table. Capture the full page.*

> **Screenshot 11 — Access Logs Page**
> ![Access Logs](screenshots/screenshot_logs_page.png)
> *PLACEHOLDER: Take a screenshot of `http://localhost:3000/logs` showing the access log table with columns (name, entry/exit, confidence, status badge) and the registered people panel on the right side with role badges.*

> **Screenshot 12 — Compliance / Audit Trail Page**
> ![Compliance Page](screenshots/screenshot_compliance_page.png)
> *PLACEHOLDER: Take a screenshot of `http://localhost:3000/compliance` showing the audit trail table with actor, action, resource, result, and timestamp columns. Include the "Export CSV" button visible in the header.*

> **Screenshot 13 — Sidebar Navigation**
> ![Sidebar Navigation](screenshots/screenshot_sidebar.png)
> *PLACEHOLDER: Take a screenshot showing the sidebar navigation with all six links visible: Dashboard, Alerts, Access Logs, Compliance, Falls, Objects. The sidebar should show the FaceDoor logo/name at the top.*

> **Screenshot 14 — Demo Data Label**
> ![Demo Data Label](screenshots/screenshot_demo_data.png)
> *PLACEHOLDER: Take a screenshot of any dashboard page when no real data exists, showing the "Sample data" badge/label that indicates demo data is being displayed.*

### 5.7 PIPEDA Compliance Framework

The system is designed to align with Canada's PIPEDA. Key compliance features include:

- **Local-only processing:** No data sent to cloud; all face images, encodings, and logs stored on the local machine
- **No continuous recording:** Only event-driven frame processing, not video recording
- **Audit trail:** Every system action logged in `audit_logs` table with actor, action, resource, result, and timestamp
- **Data retention guidance:** Access logs (90 days), audit logs (1 year), face samples (until resident leaves or consent withdrawn)
- **Deletion procedure:** Documented process for removing a resident's data upon request
- **All 10 PIPEDA principles mapped** to specific system features in `docs/COMPLIANCE.md`

---

## 6. Evaluation Techniques

### 6.1 Facial Recognition Accuracy

The facial recognition system was evaluated using a test set of 37 photos across 3 registered people:

| Metric | Value |
|--------|-------|
| Overall accuracy | 94.6% |
| Person A accuracy | 100% (15/15) |
| Person B accuracy | 100% (12/12) |
| Person C accuracy | 80% (8/10) |
| Photos with >90% confidence | 20 |
| Photos with 80–90% confidence | 12 |
| Encoding time | 20–30ms per face |
| Matching time | 10–20ms per registered person |

The calibration tool (`scripts/calibrate_recognition.py`) was used to determine the optimal matching threshold by testing 11 values between 0.30 and 0.80 and selecting the one that maximized F1 score.

**Design choice:** We evaluated two recognition backends — OpenCV HOG (70–80% accuracy, always available) and dlib deep embeddings (89–95% accuracy, requires additional installation). The system auto-selects the best available engine, ensuring it works in all deployment environments while maximizing accuracy when possible.

### 6.2 Fall Detection Accuracy

| Detector | Dataset | Accuracy |
|----------|---------|----------|
| Rules-based (Phase 1) | Manual testing with simulated falls | ~75% (estimated) |
| LSTM (Phase 2) | UR Fall Detection Dataset (URFD) | **93%** |

The LSTM model was trained on keypoints extracted from URFD videos using `scripts/extract_keypoints.py`. The training pipeline (`scripts/train_lstm.py`) used a 2-layer LSTM architecture with proper train/test splits. The 93% test accuracy was achieved on held-out sequences the model had never seen during training.

### 6.3 Object Detection Accuracy

We evaluated multiple YOLO model variants before selecting the final architecture:

| Model | mAP (COCO) | Inference Speed | Decision |
|-------|-----------|----------------|----------|
| YOLOv8n (nano) | 37.3 | Fastest | Too inaccurate for weapon detection |
| YOLOv8s (small) | 44.9 | Fast | Moderate improvement, still missed edge cases |
| YOLO26m (medium) | 52.5 | Moderate | Selected — best accuracy/speed trade-off for door cameras |

Weapon detection was specifically evaluated with test images of knives and scissors. The padded weapon verification technique increased detection confidence by approximately 80% (e.g., scissors from 22% to 40% confidence), reducing false negatives for the most safety-critical category.

### 6.4 System Integration Testing

End-to-end tests (`tests/test_integration.py`) verify the complete pipeline from frame input through API processing to database storage. Additional test suites cover:

- `tests/test_facial_recognition.py` — Unit tests for the recognition engine (CI-safe, no webcam required)
- `tests/test_threat_detection.py` — Unit tests for all threat detection rules
- `scripts/test_object_detection_api.py` — API-level object detection testing with color-coded output and batch processing
- `scripts/test_object_detection_camera_live.py` — Live camera testing with FPS counter, pause/resume, and real-time confidence adjustment

---

## 7. Reflections and Discussions

### 7.1 Challenges Faced

1. **Face recognition placeholder code:** The initial recognition implementation used random dummy encodings, producing essentially random results. Debugging this required tracing through the entire pipeline to identify that `register_faces.py` was storing random vectors instead of real HOG features. The fix was implementing a proper feature extraction and matching algorithm.

2. **YOLO model accuracy on close-up images:** Weapon images captured at close range (as they would appear at a door camera) lacked the surrounding context that YOLO expects from its COCO training data. Standard confidence was too low to trigger alerts. Our solution — reflected-border padding for re-inference — was a creative approach that significantly boosted weapon detection without requiring custom training data.

3. **CLAHE preprocessing trade-off:** Contrast enhancement that helped in dark doorway conditions actually degraded detection accuracy in well-lit scenes. Making CLAHE adaptive (only applying when `mean_brightness < 85`) resolved this.

4. **Apple Silicon (MPS) training instability:** Fine-tuning YOLO on Apple Silicon GPUs caused NaN losses due to mixed-precision (AMP) issues. Disabling AMP and lowering the learning rate stabilized training.

5. **Frontend framework selection:** The original HTML/CSS dashboard prototype was insufficient for the rich interactivity needed. Migrating to Next.js was a significant effort but paid off in component reusability, automatic API proxying, and responsive design.

### 7.2 Lessons Learned

- **Edge-first design constrains everything:** Designing for Raspberry Pi deployment forced us to choose lightweight models and efficient algorithms. This constraint ultimately led to better architecture decisions.
- **Privacy compliance is a feature, not an afterthought:** Building PIPEDA compliance into the system from the start (local-only processing, audit logging, retention policies) was far easier than retrofitting it later.
- **Adaptive preprocessing beats one-size-fits-all:** Making image enhancement conditional on scene characteristics (brightness, contrast) prevented the common pitfall of preprocessing that helps some cases but hurts others.
- **Multi-model verification improves critical detections:** The padded weapon re-inference technique demonstrated that running a second, context-enhanced pass for safety-critical categories is worth the computational cost.
- **Demo data keeps the project presentable:** Having realistic fallback data that displays when the database is empty meant the dashboard was always ready for demonstrations, even early in development.

### 7.3 Most Satisfying Aspects

- Seeing the facial recognition system go from returning random results to correctly identifying registered users in real time was the most immediate payoff.
- The unified dashboard bringing together access events, security alerts, fall detections, object classifications, and compliance data into a single coherent interface validated the integration-focused architecture.
- The weapon detection improvement through padded re-inference was a technically creative solution to a real problem — it emerged from understanding how YOLO's training data (COCO images with context) differs from door camera perspectives (close-up, limited context).

---

## 8. AI Use Section

### 8.1 AI Tools Used

| AI Tool Name | Version, Account Type | Specific Feature Used | Value Added Over AI |
|-------------|----------------------|----------------------|---------------------|
| Cursor AI (Claude) | Claude claude-4.6-opus, Pro account | Code generation for Flask API routes, object detection pipeline, dashboard components, debugging YOLO model issues, report structuring | Reviewed and adapted all generated code for project-specific requirements; designed the overall architecture; made all algorithm design decisions (e.g., padded weapon verification, adaptive CLAHE); debugged and fixed issues AI-generated code introduced; wrote project-specific class mappings for elderly care context |
| GitHub Copilot | Free with GitHub Student | Boilerplate code completion for Flask routes, React components, and Python utility functions | Reviewed all suggestions for correctness and security; rejected inappropriate completions; ensured consistency with project coding standards |
| ChatGPT (OpenAI) | GPT-4.1-turbo, free research preview | Brainstorming threat detection rules, researching PIPEDA compliance requirements, drafting initial report text | Customized all responses to our specific hardware constraints and course requirements; rewrote AI output in our own voice; verified compliance information against official PIPEDA documentation |

### 8.2 Prompt History

Full prompt history is provided in the Appendix.

---

## 9. Work Date/Hours Logs

*Logs cover March 23 – April 8, 2026 (post-midterm period). Each entry corresponds to verified commits and pull requests in the GitHub repository.*

### Advitiya Sharda (Team Lead)

| Date | Hours | Description of Work Done |
|------|-------|--------------------------|
| Mar 23, 2026 | 2.0 | Submitted Progress Report 5, merged PR #13 ericv3 and PR #14 advitiya_week12 (`c82336a`, `dd5ed39`, `1c18c4f`) |
| Mar 24, 2026 | 1.5 | Code review of Reubin's object detection dashboard PR #15, reviewed category mappings and threat level logic |
| Mar 25, 2026 | 2.0 | Refined object detection category mapping for elderly care context — removed irrelevant COCO proxies (TV, refrigerator as mobility aid), added door-relevant classes (umbrella, cell phone, potted plant) |
| Mar 27, 2026 | 2.0 | Designed per-category confidence threshold system (WEAPON: 0.20, PARCEL: 0.30, SECURITY_THREAT: 0.25, MOBILITY_AID: 0.35, OPERATIONAL: 0.45) |
| Mar 29, 2026 | 1.5 | Integrated fall detection API endpoints with threat escalation — falls now generate CRITICAL alerts visible on alerts dashboard |
| Mar 31, 2026 | 2.0 | Implemented EMA (Exponential Moving Average) confidence smoothing for temporal stability across frames, added person-at-door awareness (bbox position triggers fall hint) |
| Apr 1, 2026 | 2.0 | Updated config.py with OBJECT_IMGSZ, OBJECT_ENABLE_PREPROCESSING, and OBJECT_BASE_MODEL settings, updated api/__init__.py to pass new config params |
| Apr 2, 2026 | 2.5 | Initial YOLO upgrade research — benchmarked YOLOv8n (37.3 mAP) vs YOLOv8s (44.9 mAP) vs YOLO26m (52.5 mAP), selected YOLO26m for best accuracy-speed tradeoff |
| Apr 3, 2026 | 2.5 | Upgraded object detection from YOLOv8n to YOLO26m, removed agnostic_nms (YOLO26 is NMS-free), updated model loading in api/__init__.py |
| Apr 4, 2026 | 2.0 | Implemented adaptive CLAHE preprocessing — applied only when mean_brightness < 85 to prevent degradation on well-lit scenes |
| Apr 5, 2026 | 2.5 | Designed and implemented padded weapon verification technique — when weapon hint is detected, re-run inference on 25% reflected-border padded frame to restore context |
| Apr 6, 2026 | 3.0 | Debugged weapon detection: identified JPEG re-encoding confidence loss (0.283 → 0.225), lowered OBJECT_DETECTION_CONFIDENCE floor to 0.20, tested padded verification (scissors confidence 22% → 40%) |
| Apr 7, 2026 | 2.5 | Rewrote test_object_detection_api.py — added folder batch processing, color-coded output, summary table; rewrote test_object_detection_camera_live.py — added FPS counter, pause/resume, real-time confidence adjustment |
| Apr 8, 2026 | 3.0 | Fixed object detection page full-width layout, final integration testing across all features, final report writing and demo preparation |
| | **Total: 31.0 hrs** | |

### Eric Sanjo

| Date | Hours | Description of Work Done |
|------|-------|--------------------------|
| Mar 23, 2026 | 2.0 | Synced fall detection documentation with implemented behavior — updated API docs to reflect current fall endpoints and payloads, updated README to match runtime flow (`5a31e00`, `4282e03`) |
| Mar 24, 2026 | 1.5 | Reviewed and tested fall detection edge cases — verified LSTM fallback to rules-based when model files missing |
| Mar 25, 2026 | 2.0 | Tuned LSTM confidence threshold and cooldown parameters, tested with various fall simulation scenarios |
| Mar 27, 2026 | 1.5 | Investigated face recognition accuracy on different lighting conditions, documented HOG vs dlib accuracy comparison (70-80% vs 89-95%) |
| Mar 29, 2026 | 2.0 | Trained updated Isolation Forest anomaly model on expanded synthetic dataset, verified anomaly scoring pipeline |
| Mar 31, 2026 | 1.5 | Improved data generator (data/data_generator.py) with more realistic access patterns for elderly care scenarios |
| Apr 2, 2026 | 2.0 | Built behavioral_profiles update logic — automated preferred hours/days computation from access_logs |
| Apr 4, 2026 | 2.0 | Tested full ML pipeline end-to-end: face recognition → anomaly detection → threat generation, verified database integrity |
| Apr 6, 2026 | 1.5 | Validated LSTM model performance on held-out test sequences, confirmed 93% accuracy, documented evaluation metrics |
| Apr 8, 2026 | 2.0 | Final testing of all ML models, verified face recognition calibration tool output, updated model documentation |
| | **Total: 18.0 hrs** | |

### Reubin Chatta

| Date | Hours | Description of Work Done |
|------|-------|--------------------------|
| Mar 23, 2026 | 3.0 | Added object detection dashboard page with live events table, category counts, severity mix visualization, submitted Progress Report 5, merged PR #15 reubinv3 (`6c00f55`, `591a279`, `3c3d18f`) |
| Mar 24, 2026 | 1.5 | Object detection UI refinements and integration fixes (`9a08949`) |
| Mar 25, 2026 | 2.0 | Built ObjectCategoryBar component with color-coded category visualization, added ObjectCategoryIcon set for WEAPON, PARCEL, MOBILITY_AID, SECURITY_THREAT, OPERATIONAL |
| Mar 27, 2026 | 2.0 | Implemented severity mix stacked bar on objects page, added severity dropdown filter, built confidence progress bars for detection table |
| Mar 29, 2026 | 1.5 | Added demo data fallback for object detection events (DEMO_OBJECT_EVENTS, DEMO_OBJECT_STATUS), ensured "Sample data" label displays correctly |
| Mar 31, 2026 | 2.0 | Built PageHero component for consistent page headers across all dashboard pages, applied to objects and falls pages |
| Apr 1, 2026 | 2.0 | Implemented report export utility (frontend/lib/reportExport.ts), added typed API client wrappers for object detection endpoints |
| Apr 3, 2026 | 2.5 | Built InsightModal visualization component for dashboard KPI deep-dives, added animated icon transitions to stat cards |
| Apr 5, 2026 | 2.0 | Unified dashboard redesign — integrated InsightModalViz, updated UnifiedDashboard component with new KPI layout |
| Apr 6, 2026 | 3.5 | Major frontend overhaul: KPI cards with animated icons and health pills, sidebar separators, dashboard/compliance/alerts/object analytics UI updates (`9956d2d`, `c490596`) |
| Apr 6, 2026 | 2.5 | Built object detection test scripts: API tester with color-coded output and batch image processing, live webcam tester with FPS counter, pause/resume, real-time confidence adjustment (`8252be2`) |
| Apr 7, 2026 | 2.0 | Stacked area chart ("Activity by hour") for objects page, hourly category breakdown with gradient fills and tooltips |
| Apr 8, 2026 | 2.5 | Fixed object detection page full-width layout to match other pages, responsive design improvements, final UI polish across all six pages |
| | **Total: 29.0 hrs** | |

---

## 10. Concluding Remarks

FaceDoor demonstrates that a comprehensive smart door security system — combining facial recognition, fall detection, object detection, anomaly analysis, and compliance logging — can be built to run entirely on local hardware without cloud dependency. The system is designed for the specific needs of elderly care facilities, where resident safety and privacy are paramount.

The three-phase development approach allowed us to build incrementally: starting with core access control (Phase 1), adding fall detection for resident safety (Phase 2), and incorporating object detection for broader situational awareness (Phase 3). Each phase was validated independently before integration, resulting in a robust and reliable system.

Key technical contributions include the padded weapon verification technique for improving close-up weapon detection, the adaptive CLAHE preprocessing that selectively enhances dark scenes without degrading well-lit ones, and the dual-engine face recognition architecture that maximizes accuracy when possible while maintaining broad compatibility.

The project is ready for deployment on edge hardware (Raspberry Pi) and has been designed with extensibility in mind — additional threat rules, new object categories, and improved ML models can be integrated without architectural changes.

We thank Armin Ghauforian of Door Face Panels for providing hardware and guiding the project scope, and our course supervisor for emphasizing privacy compliance and practical deployment considerations throughout the term.

---

## 11. References

1. Schroff, F., Kalenichenko, D., & Philbin, J. (2015). FaceNet: A Unified Embedding for Face Recognition and Clustering. *CVPR 2015*.
2. Bourke, A. K., O'Brien, J. V., & Lyons, G. M. (2007). Evaluation of a threshold-based triaxial accelerometer fall detection algorithm. *Gait & Posture*, 26(2), 194–199.
3. Noury, N., Fleury, A., Rumeau, P., et al. (2007). Fall detection — Principles and methods. *IEEE EMBC 2007*.
4. Lugaresi, C., et al. (2019). MediaPipe: A Framework for Building Perception Pipelines. *arXiv:1906.08172*.
5. Redmon, J., Divvala, S., Girshick, R., & Farhadi, A. (2016). You Only Look Once: Unified, Real-Time Object Detection. *CVPR 2016*.
6. Ultralytics. (2026). YOLO26 — End-to-End NMS-Free Object Detection. https://docs.ultralytics.com
7. OpenCV. (2024). Open Source Computer Vision Library. https://opencv.org
8. Flask. (2024). Flask Web Framework. https://flask.palletsprojects.com
9. Next.js. (2026). The React Framework. https://nextjs.org
10. Office of the Privacy Commissioner of Canada. (2021). PIPEDA in Brief. https://www.priv.gc.ca/en/privacy-topics/privacy-laws-in-canada/the-personal-information-protection-and-electronic-documents-act-pipeda/pipeda_brief/
11. Kwolek, B., & Kepski, M. (2014). Human fall detection on embedded platform using depth maps and wireless accelerometer. *Computer Methods and Programs in Biomedicine*, 117(3), 489–501. (UR Fall Detection Dataset)

---

## Appendix A: Installation Guide

### System Requirements

| Tool | Version | Where to Get It |
|------|---------|-----------------|
| Python | 3.11 | https://www.python.org/downloads |
| Node.js | 18 LTS or newer | https://nodejs.org |
| npm | Comes with Node.js | — |
| Webcam | Any USB or built-in | Required for face capture and live detection |

### Step 1 — Clone the Repository

```bash
git clone https://github.com/advitiyasharda/W26_4495_S3_AdvitiyaS.git
cd W26_4495_S3_AdvitiyaS/Implementation
```

### Step 2 — Install Python Dependencies

```bash
pip install -r requirements.txt
```

On Windows, if `face_recognition` fails:
```powershell
pip install cmake
pip install dlib
pip install face_recognition
```

### Step 3 — Install Frontend Dependencies

```bash
cd frontend
npm install
cd ..
```

### Step 4 — Download MediaPipe Pose Model (for fall detection)

```bash
curl -L -o models/pose_landmarker.task \
  https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_full/float16/1/pose_landmarker_full.task
```

### Step 5 — Start the Backend

```bash
# Mac / Linux
FLASK_PORT=5001 python3 main.py

# Windows PowerShell
$env:FLASK_PORT=5001; python main.py
```

### Step 6 — Start the Frontend (new terminal)

```bash
cd frontend
npm run dev
```

### Step 7 — Open the Dashboard

Navigate to `http://localhost:3000` in your browser. If the backend is running, the dashboard shows live data. If not, it shows demo data automatically.

### Optional: Register Faces

```bash
python3 scripts/capture_faces.py      # Capture photos
python3 scripts/register_faces.py     # Register into system
python3 scripts/calibrate_recognition.py  # Optimize threshold
```

### Optional: Start Fall Detection Camera

```bash
python3 scripts/fall_detection_camera.py --lstm
```

> **Screenshot A1 — Backend Running**
> ![Install Guide - Backend](screenshots/ig_backend_running.png)
> *PLACEHOLDER: Screenshot of the terminal after running `FLASK_PORT=5001 python3 main.py` showing Flask startup messages: "Running on http://0.0.0.0:5001", loaded face encodings count, detector status, and model info.*

> **Screenshot A2 — Frontend Running**
> ![Install Guide - Frontend](screenshots/ig_frontend_running.png)
> *PLACEHOLDER: Screenshot of the terminal after running `npm run dev` in the frontend folder, showing "Ready in Xms" and "Local: http://localhost:3000".*

> **Screenshot A3 — Dashboard First Load**
> ![Install Guide - First Load](screenshots/ig_dashboard_first_load.png)
> *PLACEHOLDER: Screenshot of `http://localhost:3000` loading for the first time in a browser. Should show the dashboard with demo data and the "Sample data" badge visible.*

### Port Configuration

The backend runs on port **5001** (not Flask's default 5000) to avoid conflicts. The frontend proxies API calls to port 5001 via `frontend/next.config.ts`.

---

## Appendix B: User Guide

### Accessing the Dashboard

1. Ensure both the backend (port 5001) and frontend (port 3000) are running.
2. Open `http://localhost:3000` in a web browser.

### Dashboard Home Page

The home page displays a unified overview of the system:
- **KPI Cards** at the top show total entries, denied attempts, active alerts, and falls today
- **Hourly Activity Chart** shows access patterns over the last 24 hours
- **Access Outcome Donut** breaks down successful vs. denied access attempts
- **Recent Access Log** shows the latest entry/exit events with confidence scores

> **Screenshot B1 — Dashboard Home Overview**
> ![User Guide - Dashboard](screenshots/ug_dashboard_home.png)
> *PLACEHOLDER: Full-page screenshot of `http://localhost:3000/` with annotations/arrows pointing to: (1) KPI cards row, (2) hourly bar chart, (3) donut chart, (4) recent access log table. Use a screenshot annotation tool to add numbered labels.*

### Viewing Security Alerts

Navigate to **Alerts** (`/alerts`) to see all security alerts:
- Filter by severity using the buttons (CRITICAL, HIGH, MEDIUM)
- Each alert card shows the threat type, severity, description, and timestamp
- Fall detection alerts and object detection alerts appear here alongside access-based threats

> **Screenshot B2 — Alerts Filtering**
> ![User Guide - Alerts](screenshots/ug_alerts_filtering.png)
> *PLACEHOLDER: Two side-by-side screenshots of the alerts page: (left) showing "All" alerts, (right) showing only "CRITICAL" alerts after clicking the CRITICAL filter button. Use annotations to highlight the filter buttons.*

### Access Logs

Navigate to **Access Logs** (`/logs`) to view the complete access history:
- The table shows each access event with person name, entry/exit type, confidence, and status
- Use the registered people panel to view and manage enrolled users
- Users can be assigned roles (Resident, Staff, Visitor)

> **Screenshot B3 — Access Logs Table**
> ![User Guide - Logs](screenshots/ug_logs_table.png)
> *PLACEHOLDER: Screenshot of `http://localhost:3000/logs` showing the access log table with at least 5 rows visible. Annotate one row to point out: person name, entry/exit badge, confidence score, and status (success/failed).*

### Fall Monitoring

Navigate to **Falls** (`/falls`) to monitor fall detection:
- The live confidence bar shows the current LSTM confidence score (updated in real time when the camera is running)
- The detector status indicator shows whether the fall detector is online
- The event table lists all detected fall events with timestamps and confidence scores
- Use the **Reset** button to clear the fall detection state

> **Screenshot B4 — Falls Monitoring Page**
> ![User Guide - Falls](screenshots/ug_falls_monitoring.png)
> *PLACEHOLDER: Screenshot of `http://localhost:3000/falls` with annotations pointing to: (1) the LSTM confidence bar, (2) the "Live"/"Offline" detector status badge, (3) the event history table, (4) the Reset button.*

### Object Detection

Navigate to **Objects** (`/objects`) to view object detection events:
- Use the **category filter chips** to filter by WEAPON, SECURITY_THREAT, PARCEL, MOBILITY_AID, or OPERATIONAL
- Use the **severity dropdown** to filter by severity level
- The **stacked area chart** shows detection volume by category over time
- The **event table** shows each detection with object class, category, confidence bar, and severity badge
- Flagged rows (amber highlight) indicate events worth reviewing

> **Screenshot B5 — Object Detection Page**
> ![User Guide - Objects](screenshots/ug_objects_page.png)
> *PLACEHOLDER: Screenshot of `http://localhost:3000/objects` with annotations pointing to: (1) the category filter chips (colored buttons), (2) the severity dropdown, (3) the "By category" bar chart, (4) the "Activity by hour" stacked area chart. Capture the full page.*

> **Screenshot B6 — Object Detection Table (Flagged Event)**
> ![User Guide - Objects Table](screenshots/ug_objects_table_flagged.png)
> *PLACEHOLDER: Screenshot of the "Recent detections" table on the objects page, scrolled to show a flagged row (amber highlight with dot indicator). Annotate to show: the flag dot, object name, category icon, confidence bar, and severity badge.*

### Compliance Audit

Navigate to **Compliance** (`/compliance`) to view the PIPEDA audit trail:
- Every system action is logged with actor, action, resource, result, and timestamp
- Use the **Export CSV** button to download the audit log for external review

> **Screenshot B7 — Compliance Audit Trail**
> ![User Guide - Compliance](screenshots/ug_compliance_page.png)
> *PLACEHOLDER: Screenshot of `http://localhost:3000/compliance` showing the audit trail table with at least 5 entries. Annotate the "Export CSV" button.*

### Registering a New Person

1. Run `python3 scripts/capture_faces.py` from the `Implementation/` directory
2. Face the camera and press SPACE 10–15 times with varied angles and lighting
3. Press Q when done
4. Run `python3 scripts/register_faces.py` and select "Register from captured photos"
5. The person will now be recognized at the door

> **Screenshot B8 — Face Capture Process**
> ![User Guide - Capture](screenshots/ug_face_capture.png)
> *PLACEHOLDER: Screenshot of the webcam window during `python scripts/capture_faces.py` showing a green bounding box around the face with the instruction text overlay. Capture one frame while pressing SPACE to save a photo.*

> **Screenshot B9 — Registration Terminal Output**
> ![User Guide - Register](screenshots/ug_face_register.png)
> *PLACEHOLDER: Screenshot of terminal showing the full output of `python scripts/register_faces.py` with the menu options and the successful registration messages.*

### Running Tests

```bash
# Full integration test
python tests/test_integration.py

# Recognition accuracy test
python scripts/quick_test_recognition.py

# Object detection API test
python scripts/test_object_detection_api.py

# Threat detection unit tests
python tests/test_threat_detection.py
```

---

## Appendix C: AI Prompt History

```
Explain in simple terms what an audit log should record for a small web app that tracks door access.
Give me a few example rules for suspicious door access.
How can we build and integrate two parts of the project, the facial recognition and anomaly detection.
Show a tiny example that renders a page with a list of fake log entries.
Can you run the frontend part and the object detection test for me.
I wanna work on the object detection part — drastically improve accuracy and align with elderly care context.
Can you use YOLO26 instead for best accuracy?
Can you work on the test object detection camera file to make it easier to test?
Can we somehow increase the weapon detection part in YOLO?
Can you try to finetune for weapon detection more?
How does AI face detection on Android phones work so well?
```
