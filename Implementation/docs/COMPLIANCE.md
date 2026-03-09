# FaceDoor — PIPEDA Compliance Notes (Canada)

## Overview

FaceDoor is a local smart-door security system for elderly care facilities that uses on-device face recognition and rules-based threat detection to support resident safety and controlled entry. Because the system processes identifiable information about residents (e.g., facial images and identity-linked access events) in a private-sector organizational context, it is designed to align with Canada’s **Personal Information Protection and Electronic Documents Act (PIPEDA)**.

## What personal data is collected

- **Face images (reference photos)**
  - Stored locally under `data/samples/` as image files organised per resident.
  - Used to register/refresh recognition profiles.
- **Face encoding vectors**
  - Derived biometric templates used for matching.
  - Stored locally in the system’s SQLite-backed resident records (logical “users” dataset) and/or the on-device recognition store used by the face engine.
- **Access event logs**
  - Stored in SQLite `access_logs`.
  - Includes: who entered/exited (`user_id`), access type (`entry/exit`), recognition confidence score, status (`success/failed`), and timestamp.
- **Threat and anomaly records**
  - Stored in SQLite `threats` and `anomalies`.
  - Includes: alert type, severity, description/message, and timestamp; linked to the relevant `user_id` where applicable.
- **Audit logs (system actions)**
  - Stored in SQLite `audit_logs`.
  - Captures security-relevant actions such as access granted/denied and administrative operations for accountability and compliance reporting.

## What is NOT collected

- **No cloud uploads by default**: FaceDoor stores and processes data locally and does not require an external cloud service for recognition.
- **No continuous video recording**: The system processes frames for recognition events; it does not store continuous video.
- **No audio recording**: Audio is not captured or stored.

## How long data is retained (recommended)

Retention should be set by facility policy and local legal/clinical requirements. The following retention periods are recommended for operational safety and compliance:

- **Access logs**: retain **90 days**
- **Audit logs**: retain **1 year**
- **Face samples**: retain **until a resident leaves the facility** (or consent is withdrawn)

## How a resident can request deletion

Deletion requests should be handled by the facility administrator (or designated privacy officer). Suggested procedure:

1. **Identify the resident’s profile** (their `user_id` / name as stored in the system).
2. **Remove database records**:
   - Run: `python scripts/clear_database.py`
   - If the facility policy requires selective deletion, the administrator should remove the resident’s rows from SQLite (users, access logs, threats, anomalies, and audit entries where appropriate) using an approved administrative process.
3. **Remove face sample images**:
   - Manually delete the resident’s folder under `data/samples/` (e.g., `data/samples/<resident_name>/`).
4. **Verify removal**:
   - Confirm the resident no longer appears in the registered users list and no longer matches during recognition.

## Audit trail (accountability)

FaceDoor maintains an **audit trail** in the `audit_logs` table to support accountability and incident review. Each audit entry records:

- **actor**: the `user_id` associated with the event/action (where available)
- **action**: the operation performed (e.g., `ACCESS_GRANTED`, `ACCESS_DENIED`)
- **resource**: the system component affected (e.g., `door/main-entrance`)
- **result**: success/failure outcome
- **timestamp**: when the action occurred
- **details**: supporting context (e.g., confidence score)

This audit trail supports investigation, internal governance, and evidence of appropriate handling of personal information.

## Data storage location

- **Primary store**: local SQLite database file (default path: `data/doorface.db`)
- **Face samples**: local filesystem under `data/samples/`
- **No cloud storage** is required for normal operation.
- **No external API calls** are required for face recognition and rules-based threat detection.

## PIPEDA principles mapped to system features

| PIPEDA Principle | How FaceDoor addresses it |
|---|---|
| Accountability | Assign the facility administrator responsibility for configuration, access control, and responding to data requests. Use `audit_logs` to demonstrate accountability for key actions. |
| Identifying Purposes | Document the purpose as: (1) controlling door access, (2) resident safety monitoring, (3) incident investigation. Data fields are collected only to support these purposes. |
| Consent | Facility obtains resident/guardian consent for collecting and using biometric identifiers (face samples/encodings) and for logging access events. Consent state should be managed as part of facility intake/offboarding procedures. |
| Limiting Collection | Collect only what is needed: identity match, confidence score, access type, timestamps, and security alerts. No audio and no continuous recording. |
| Limiting Use, Disclosure, and Retention | Use data only for access control, safety, and security monitoring. Do not disclose externally by default. Apply retention limits (e.g., 90 days access logs, 1 year audit logs). |
| Accuracy | Use confidence thresholds and supervised registration to reduce misidentification. Allow updates to resident face samples and profiles as appearance changes. |
| Safeguards | Store data locally, use least-privilege access to the host machine, and rely on audit logging and threat detection to identify misuse. Protect the device/DB with OS-level permissions and physical security controls. |
| Openness | Provide facility-facing documentation describing what is collected, where it is stored, how long it is kept, and how requests are handled (this document + system docs). |
| Individual Access | Residents (or guardians) can request access to their records (access logs, threats, audit entries where applicable) through the facility administrator. |
| Challenging Compliance | Provide a clear escalation path: residents can challenge compliance through the facility administrator, who can review `audit_logs`, system configuration, and retention/deletion actions. |

## Contact

For data access or deletion requests, contact the facility administrator.

