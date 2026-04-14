# FaceDoor — Presentation Speaking Script
**CSIS 4495 Applied Research · Final Presentation**

> **Duration target:** 12–16 minutes total  
> **Format:** A = Advitiya speaks · E = Eric speaks · R = Reubin speaks  
> **When demoing:** switch to the live app immediately — do not linger on slides

---

## SLIDE 1 — TITLE

**[A – Advitiya]** *(standing, facing the panel)*

> "Good morning. Our project is called **FaceDoor** — a smart door security system built specifically for elderly care facilities. My name is Advitiya, I was the team lead and handled the backend, security engine, and compliance framework."

**[E – Eric]**

> "I'm Eric, I worked on the machine learning side — fall detection, LSTM model training, and the anomaly detection pipeline."

**[R – Reubin]**

> "And I'm Reubin, I built the full frontend dashboard in Next.js and handled the object detection integration on the UI side."

**[A – Advitiya]**

> "The core idea is simple: elderly care facilities need to know *who* is at the door, detect if a resident has *fallen*, and flag *threats* — all without sending a single byte of data to the cloud. Everything runs on-premises."

---

## SLIDE 2 — THE PROBLEM

**[A – Advitiya]**

> "The problem has three layers. First — access control. Traditional door systems are badge-based or manual. They have no way to recognize a face, so an unauthorized visitor looks identical to a registered nurse. In a care facility, that's a serious safety risk.

> Second — falls. One in four elderly adults falls every year in care settings. Standard CCTV records video but does nothing in real-time. A resident can be on the floor for minutes before anyone notices.

> Third — privacy. These facilities deal with sensitive patient data. Any system that sends face images or logs to a cloud server immediately becomes a PIPEDA liability. So the constraint was: everything stays local."

---

## SLIDE 3 — OUR SOLUTION

**[A – Advitiya]**

> "FaceDoor addresses all three. We built three integrated modules. I'll give a quick overview and then each of us will walk through what we specifically built."

> "First — face recognition. **94.6% measured accuracy** on our test set using dlib's deep embedding pipeline."

**[E – Eric]**

> "Second — fall detection. We built a dual-mode system. A rules-based detector using MediaPipe pose estimation, and an LSTM neural network trained on the UR Fall Detection Dataset that achieved **93% accuracy** on held-out test sequences."

**[R – Reubin]**

> "Third — threat monitoring with YOLO26 object detection, which scored **52.5 mAP** on our evaluation. I'll show all of this live in the demo."

---

## SLIDE 4 — TECH STACK

**[A – Advitiya]** *(keep this brief — 45 seconds max)*

> "On the backend — Flask in Python 3.11, running single-threaded intentionally, because dlib and OpenCV both have thread-safety issues. SQLite as our database — four tables: users, access logs, audit logs, fall history.

> For ML — dlib for face encoding, MediaPipe for pose keypoints, a custom LSTM trained on URFD, and YOLO26 for object detection."

**[R – Reubin]**

> "Frontend is Next.js 16 with React 19, TypeScript, Tailwind CSS for styling, Recharts for all the data visualizations. The dashboard proxies API requests through Next.js to the Flask server on port 5001."

**[A – Advitiya]** *(transition)*

> "Let me show you the architecture before we get into individual features."

---

## SLIDE 5 — SYSTEM ARCHITECTURE

**[A – Advitiya]**

> "The flow is straightforward. A camera frame hits the Flask API. Flask routes it through the ML engines — face engine, fall detector, threat detector, and YOLO26 for objects — all running in the same process. Results go into SQLite. The Next.js dashboard reads from those same endpoints and displays everything in real-time.

> The critical point: nothing leaves this pipeline. No external calls. The architecture was designed so that a Raspberry Pi running on the facility's local network is the entire system."

---

## SLIDE 6 — FEATURE 1: FACE RECOGNITION

**[A – Advitiya]** *(this is your section — own it)*

> "I built the face recognition engine. The pipeline has four steps.

> Detection — dlib's HOG-based frontal face detector locates faces in the frame. Encoding — we extract a 128-dimensional embedding using dlib's ResNet model. That embedding is a numerical vector that represents the geometry of the face. Matching — we compute the Euclidean distance between the new embedding and every registered embedding in the database. If the distance is below our threshold, it's a match. Decision — known person gets access granted, unknown face triggers a HIGH alert and gets logged immediately.

> The measured accuracy on our test set was **94.6%**. We tested on 37 photos across three people. We also built a fallback — if dlib fails to initialize, the system automatically switches to OpenCV's HOG detector which gives 70 to 80 percent accuracy. The full pipeline runs in **45 milliseconds** on a modern CPU.

> One thing I'm particularly proud of is the **RecognitionBuffer** — a temporal smoothing class I built that buffers frame-level predictions to avoid false positives from a single bad frame. If you wave your hand in front of the camera, it won't trigger an alert."

> *(transition to demo if needed)*  
> **[DEMO CUE]** *Open the registration page → register a face → step to the camera → show access granted log in real time.*

---

## SLIDE 7 — FEATURE 2: FALL DETECTION

**[E – Eric]** *(this is your section — own it)*

> "I built both phases of the fall detection system.

> Phase 1 is rules-based. We use MediaPipe to extract 33 body keypoints — specific joint positions — from each camera frame. The rules then check three things: whether the hip landmark has dropped below a floor-proximity threshold, whether the torso angle has exceeded the upright angle limit, and whether there's been a sudden downward velocity spike across keypoints. If two or more of those fire together, it's classified as a fall and triggers a CRITICAL alert. There's also a cooldown timer I implemented to prevent duplicate alerts from the same incident.

> Phase 2 is the LSTM. I trained this on the UR Fall Detection Dataset — a real academic dataset with diverse fall scenarios. The input is a 30-frame sliding window of 33 keypoint coordinates, so each input tensor is 30×33. The LSTM achieved **93% accuracy** on the held-out test sequences. The detector is stateful — it maintains its frame buffer across API calls, which was an interesting engineering challenge because HTTP is stateless by design. I solved it using a singleton pattern for the detector instance.

> The two phases are configurable — you can switch between rules-based and LSTM mode in config.py."

> **[DEMO CUE]** *Open the Falls Monitor page → show the LSTM confidence bar → simulate a fall gesture in front of the camera → show the CRITICAL alert appear.*

---

## SLIDE 8 — FEATURE 3: THREAT DETECTION

**[A – Advitiya]**

> "The threat detection engine is a rule set I built on top of all three modules. Seven rules, three severity levels.

> Unrecognized face — HIGH. Repeated failed access — HIGH — if the same unknown person attempts entry more than a threshold number of times. Unusual access times — MEDIUM — configurable operating hours, anything outside flags. Tailgating — HIGH — if more than one person enters within 15 seconds of a single authorization. Wandering — MEDIUM — a resident detected at the door after 9 PM. Repeated falls — CRITICAL — multiple fall events for the same person within a time window. And object detection — CRITICAL — if YOLO26 flags a weapon or security threat.

> All these rules are evaluated in the same API call as recognition, so there's no separate polling. One request to `/api/recognize` runs the full stack — face recognition, threat evaluation, and alert generation — in that 45 millisecond window."

---

## SLIDE 9 — LIVE DASHBOARD

**[R – Reubin]** *(this is your section — own it, and go to the live demo)*

> "I built the entire frontend in Next.js 16. There are five pages.

> **[SWITCH TO LIVE DEMO NOW]**

> The main dashboard shows four real-time KPI cards — entries today, active alerts, falls today, access denials — plus a Recharts bar chart for hourly access patterns and a donut chart for access outcomes. These refresh automatically every 15 seconds.

> The Alerts page shows a severity-filtered feed — you can filter by CRITICAL, HIGH, or MEDIUM. Each alert has the person, timestamp, rule triggered, and a colour-coded badge.

> The Logs page is the full event history — every access granted, denied, and every system action, with the person name, confidence score, and timestamp.

> The Compliance page is the audit trail — every action the system itself has taken, not just door events. This feeds directly from the `audit_logs` table that Advitiya designed.

> And the Falls Monitor shows the LSTM confidence score over time, fall event history, and the current detector state.

> Everything has a CSV export button because care facilities need to produce paper trails for regulatory inspections."

---

## SLIDE 10 — PIPEDA & PRIVACY COMPLIANCE

**[A – Advitiya]**

> "This was a requirement we took seriously from the proposal stage. PIPEDA — the Personal Information Protection and Electronic Documents Act — applies to any Canadian organization handling personal information, which includes biometric data like face encodings.

> Here's what we actually implemented — not what we planned, what's running.

> **On-premises only.** Not a marketing claim — the Flask server has no outbound network calls. Face encodings, access logs, everything stays on the local machine. I verified this in the architecture.

> **Data minimization.** We store 128-dimensional numerical vectors — not images. If someone walks away with our database, they have a list of floating point numbers, not photos of residents.

> **Event-driven processing.** The camera processes frames only when a door event occurs. There is no continuous recording or surveillance stream.

> **Data retention.** Configured in config.py — 90 days for access logs, one year for audit logs, and face data is deleted when a resident leaves or withdraws consent. These aren't hardcoded — a facility admin can adjust them.

> **Audit trail.** Every action the system takes — access granted, access denied, user registered, user deleted, alert triggered — is written to the `audit_logs` table with the actor, action, resource, result, and timestamp. The compliance dashboard exposes this with CSV export.

> And on the security side — all SQL uses parameterized queries, inputs are validated before processing, and CORS is locked to trusted origins only.

> All ten PIPEDA principles are mapped to specific system features in `docs/COMPLIANCE.md` in our repository."

---

## SLIDE 11 — EVALUATION & RESULTS

**[E – Eric]**

> "Let me walk through the key numbers.

> Face recognition — **94.6% accuracy** on our test set of 37 photos. Person A hit 100%, Person B 100%, Person C 80% — the lower score was due to significant lighting variation in their sample photos. The full pipeline runs in **45 milliseconds**.

> Fall detection LSTM — **93%** on held-out sequences from the UR Fall Detection Dataset. The rules-based phase is harder to give a clean number for because it depends on environment, but in our testing it caught falls reliably under normal lighting.

> YOLO26 for object detection — **52.5 mAP**. We compared against YOLOv8n at 37.3 and YOLOv8s at 44.9. YOLO26 outperformed both on our evaluation set. The CLAHE preprocessing step improved low-light weapon detection meaningfully.

> Threat detection — all seven rules are operational. We tested each rule manually and verified alerts appeared in the dashboard within the same API response cycle.

> On privacy — 100% on-premises, verified by network traffic inspection during testing."

---

## SLIDE 12 — CHALLENGES & LESSONS LEARNED

**[A – Advitiya]**

> "The biggest technical surprise was dlib's threading behaviour. Flask defaults to multi-threaded mode, but dlib's face detector is not thread-safe — we were getting segmentation faults in testing. The fix was forcing single-threaded mode in Flask, which is actually fine for this use case since the facility won't have hundreds of concurrent requests."

**[E – Eric]**

> "For me it was the LSTM state problem. The fall detector needs 30 frames of history to make a prediction, but HTTP is stateless — each request is independent. I solved it with a module-level singleton that persists the frame buffer between API calls, but it means the fall detector state is tied to the server process lifecycle. That's actually acceptable for this use case, but it was a non-obvious design decision."

**[R – Reubin]**

> "On the frontend, the challenge was making the dashboard feel live without hammering the API. I settled on 15-second polling intervals with optimistic UI updates — the chart animates immediately and confirms on the next refresh cycle. Also, the demo data fallback was critical. When the database is empty, the dashboard auto-populates with realistic synthetic data so it doesn't look broken during a demo."

---

## SLIDE 13 — THANK YOU

**[A – Advitiya]** *(wrap up, invite questions)*

> "To summarize — FaceDoor is a complete, working, on-premises security system. Face recognition at 94.6%. Fall detection at 93% LSTM accuracy. Seven active threat rules. Five dashboard pages with audit trail and CSV export. And full PIPEDA compliance by design, not as an afterthought.

> We're happy to demo any specific component you'd like to see, and we're ready for questions. Thank you."

---

## DEMO FLOW QUICK REFERENCE

| Moment | What to show |
|---|---|
| After Slide 6 (Face Recognition) | Register a face → step to camera → show access granted in logs |
| After Slide 7 (Fall Detection) | Falls Monitor page → LSTM confidence → simulate fall → CRITICAL alert |
| During Slide 9 (Dashboard) | Live walk through all 5 pages with real data |
| If asked about compliance | Open Compliance page → show audit trail → hit Export CSV |
| If asked about threat rules | Trigger an unknown face → show HIGH alert appear in Alerts page |

---

## TIMING GUIDE

| Section | Speaker | Target time |
|---|---|---|
| Title + Intro | All | 45 sec |
| Problem | Advitiya | 1.5 min |
| Solution overview | All | 45 sec |
| Tech Stack + Architecture | Advitiya + Reubin | 1.5 min |
| Face Recognition | Advitiya + demo | 2 min |
| Fall Detection | Eric + demo | 2 min |
| Threat Detection | Advitiya | 1 min |
| Dashboard | Reubin + demo | 2 min |
| PIPEDA | Advitiya | 1 min |
| Evaluation | Eric | 1 min |
| Challenges | All | 1 min |
| Close | Advitiya | 30 sec |
| **Total** | | **~15 min** |
