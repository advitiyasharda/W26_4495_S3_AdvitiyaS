# Smart Door Security Framework with Anomaly Detection & Cybersecurity for Elderly Care

**Student Name:** Advitiya Sharda  
**Student ID:** 300395470  
**Course:** CSIS 4495 – Applied Research Project, Section 3  
**Team Lead:** Advitiya Sharda  

**Midterm Video Demonstration:** [https://YOUR_VIDEO_LINK_HERE](https://YOUR_VIDEO_LINK_HERE)  
*(publicly viewable, clickable link)*

---

## 1. Introduction

Door face panels and smart door security are critical components of modern elderly-care environments. This project combines facial recognition, anomaly detection, and cybersecurity to protect seniors’ residences. The system is designed to run entirely on edge hardware (a Raspberry Pi) with no cloud dependency, ensuring privacy and reliability.

The core problem is to detect and log authorized and unauthorized access attempts, identify abnormal behavior patterns, and maintain audit-compliant logs while minimizing sensitive data retention. Existing literature shows numerous facial-recognition systems, but many either rely on cloud services or neglect compliance and anomaly detection. Our research addresses these gaps by implementing a lightweight, rule-based threat detector on edge devices and by designing a privacy-aware logging schema.

Initial hypotheses include:

- A rule-based threat-detection engine (e.g., repeated failed attempts, access at unusual hours) will be sufficient for the term’s scope.
- Maintaining all data locally on the Pi reduces privacy risk.
- A simple UI dashboard can provide useful situational awareness without overwhelming users.

Potential benefits include safer living environments for elderly residents, improved incident visibility for caregivers, and a framework that can be extended with add-on anomaly models in later phases.

## 2. Summary of the Initially Proposed Research Project

The original proposal outlined a smart door security framework with facial recognition at the entrance, an anomaly detection layer to catch suspicious patterns, and cybersecurity features to protect data and logs. Key components were:

- A Raspberry Pi acting as the main controller and database.
- A lock and camera interface for capturing video frames.
- Flask-based REST API exposing endpoints for recognition, access logging, and threat retrieval.
- A simple Next.js dashboard to visualize access events and alerts.

The project aimed to integrate basic ML (e.g., Isolation Forest) for anomaly detection while keeping core functionality rule-based for performance on edge hardware.

## 3. Changes to the Proposal

Several adjustments were made after early research and a hardware meeting:

- **Edge-first requirement reinforced:** The Pi’s hardware limitations mean no cloud or heavy ML can be used; all processing stays local.
- **Simplified anomaly approach:** Rather than complex models, we are implementing rule-based detectors (e.g., too many failed attempts, access after long inactivity) with the option to add basic statistical models later.
- **Dashboard scope reduced:** Only access events, alerts, and status information are shown; no comprehensive analytics UI yet.
- **Compliance as a core feature:** Logging and data retention policies were incorporated from the start rather than as an afterthought, based on privacy research and supervisor guidance.

Each change was justified by: hardware constraints observed during the Raspberry Pi/lock/camera briefing; project timeline limitations; and advice from our supervisor emphasizing privacy and simplicity.

## 4. Project Planning and Timeline

### Updated Timeline (Feb 24 – End of Term)

| Date Range | Milestone | Responsible |
|------------|-----------|-------------|
| Feb 24–Mar 8 | Implement rule-based threat detector & log schema | Advitiya |
| Mar 9–Mar 22 | Build Flask API endpoints, storage mechanisms | Advitiya |
| Mar 23–Apr 5 | Develop Next.js dashboard to display events/alerts | Advitiya |
| Apr 6–Apr 19 | Integrate all components, perform testing | Advitiya |
| Apr 20–end term | Prepare final report, polish UI, in-class demo | Advitiya |

*(Since I am working alone, all tasks are my responsibility; if part of a team, individual assignments would be noted here.)*

### Project Management Diagram

![Gantt chart placeholder](docs/gantt_example.png)

*(Include screenshot of a simple Gantt chart or Kanban board here.)*

## 5. Implemented Features

### 5.1 Facial Recognition and Access Logging

I implemented the Flask `/recognize` endpoint which accepts a base64-encoded frame, decodes it, runs face detection/recognition via an `engine` abstraction, and returns a JSON response containing `person_id`, `name`, `confidence`, and access decision. Successful recognitions are logged to the SQLite database; failures generate threat records.

**Key code snippet:**

```python
@app.route("/recognize", methods=["POST"])
def recognize_face():
    # ... decode image, detect faces ...
    rec = engine.recognize_face(frame, (x, y, w, h))
    # ... build result and log into DB ...
```

**Screenshot of API call (example):**

![API response](screenshots/recognize_response.png)

### 5.2 Threat Detection Rules

Basic rules implemented include:

- More than 3 consecutive failed recognitions within 1 minute triggers a HIGH-severity threat.
- Access attempts outside of defined hours generate alerts.
- Unknown faces are logged and flagged.

These rules run inside the same endpoint and record threats via a new `log_threat` database method.

**My contribution:** I designed and coded the threat‑detection logic, wrote unit tests, and ensured all log entries include timestamps and severity levels appropriate for compliance.

## 6. AI Use Section

| AI Tool | Version / Account Type | Specific Feature Used | Value Added by Me |
|---------|------------------------|----------------------|-------------------|
| ChatGPT (OpenAI) | GPT-4.1‑turbo, research preview | Rewriting report text, brainstorming rules | Customized answers to our hardware and course constraints; rewrote all AI output in my own words. |
| GitHub Copilot | Free with GitHub | Provided boilerplate for Flask routes and small dashboard templates | Reviewed and corrected all generated code to ensure security and correctness. |

### Appendix: Prompt History

*(See end of this document for the full prompt history used with chat-based tools.)*

## 7. Work Date / Hours Logs

**Advitiya Sharda**

| Date | Hours | Description |
|------|-------|-------------|
| Feb 14, 2026 | 1.5 | Implemented `/recognize` endpoint and database logging |
| Feb 18, 2026 | 2.0 | Added unit tests and adjusted CV handling |
| Feb 20, 2026 | 1.0 | Wrote initial threat-detection rules |
| Feb 22, 2026 | 2.5 | Updated README with installation instructions |

*(Continue adding entries as work progresses.)*

## 8. Closing & References

Thanks to Armin for providing the Raspberry Pi and camera assembly and for guiding our project scope.  

### References

- OpenCV documentation, release 4.8
- NIST Face Recognition Vendor Test reports
- Flask official tutorial
- [Any other cited literature goes here]

---

*Appendix: Full prompt history*  
```
Explain in simple terms what an audit log should record for a small web app that tracks door access.
Give me a few example rules for suspicious door access.
How can we build and integrate two parts of the project, the facial recognition and anomaly detection.
Show a tiny example that renders a page with a list of fake log entries.
```