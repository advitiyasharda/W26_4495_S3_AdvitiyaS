# API Documentation

## Door Face Panels Smart Security System API

Base URL: `http://localhost:5000/api`

## Health Check

### GET /health

Check system health and availability.

**Response**:
```json
{
    "status": "healthy",
    "timestamp": "2026-01-30T10:00:00",
    "version": "0.1.0"
}
```

---

## Facial Recognition

### POST /recognize

Recognize a face from camera frame and determine access permission.

**Request**:
```json
{
    "frame": "base64_encoded_image_data"
}
```

**Response**:
```json
{
    "person_id": "resident_001",
    "name": "John Doe",
    "confidence": 0.92,
    "access_granted": true,
    "timestamp": "2026-01-30T10:00:00"
}
```

**Status Codes**:
- `200`: Face recognized successfully
- `400`: Invalid/missing frame data
- `500`: Processing error

---

## Access Logging

### POST /log-access

Log a door access event (entry/exit).

**Request**:
```json
{
    "person_id": "resident_001",
    "access_type": "entry",
    "confidence": 0.92,
    "timestamp": "2026-01-30T10:00:00"
}
```

**Response**:
```json
{
    "status": "logged",
    "timestamp": "2026-01-30T10:00:00"
}
```

---

## Access Logs

### GET /logs

Retrieve access logs with optional filtering.

**Query Parameters**:
- `person_id` (optional): Filter by person
- `limit` (optional, default=100): Number of records
- `offset` (optional, default=0): Pagination offset

**Response**:
```json
{
    "logs": [
        {
            "log_id": 1,
            "person_id": "resident_001",
            "name": "John Doe",
            "access_type": "entry",
            "confidence": 0.92,
            "status": "success",
            "timestamp": "2026-01-30T10:00:00"
        }
    ],
    "total": 150,
    "limit": 100,
    "offset": 0,
    "timestamp": "2026-01-30T10:00:00"
}
```

---

## Threats & Alerts

### GET /threats

Retrieve active security threats and behavioral alerts.

**Query Parameters**:
- `person_id` (optional): Filter by specific person
- `severity` (optional): Filter by severity (LOW, MEDIUM, HIGH, CRITICAL)

**Response**:
```json
{
    "threats": [
        {
            "threat_id": 1,
            "threat_type": "REPEATED_FAILED_ACCESS",
            "severity": "HIGH",
            "person_id": "unknown_001",
            "message": "Multiple failed access attempts (4) detected",
            "resolved": false,
            "timestamp": "2026-01-30T10:00:00"
        },
        {
            "threat_id": 2,
            "threat_type": "PROLONGED_INACTIVITY",
            "severity": "CRITICAL",
            "person_id": "resident_001",
            "message": "No door activity for 26.5 hours",
            "resolved": false,
            "timestamp": "2026-01-30T10:00:00"
        }
    ],
    "timestamp": "2026-01-30T10:00:00"
}
```

---

## Statistics

### GET /stats

Get system statistics and analytics.

**Response**:
```json
{
    "facial_recognition": {
        "total_persons": 5,
        "recognition_accuracy": 0.92
    },
    "access_events": {
        "total_entries": 245,
        "total_exits": 238,
        "today": 12
    },
    "threats": {
        "active_alerts": 2,
        "total_threats": 45
    },
    "system": {
        "uptime_hours": 72,
        "avg_inference_latency_ms": 380
    },
    "timestamp": "2026-01-30T10:00:00"
}
```

---

## Compliance & Audit

### GET /compliance/audit

Retrieve PIPEDA-compliant audit log for regulatory compliance.

**Query Parameters**:
- `limit` (optional, default=100): Number of records

**Response**:
```json
{
    "audit_log": [
        {
            "audit_id": 1,
            "action": "FACE_RECOGNIZED",
            "user_id": "resident_001",
            "resource": "door_001",
            "result": "success",
            "timestamp": "2026-01-30T10:00:00"
        },
        {
            "audit_id": 2,
            "action": "THREAT_DETECTED",
            "user_id": null,
            "resource": "system",
            "result": "REPEATED_FAILED_ACCESS",
            "timestamp": "2026-01-30T10:00:30"
        }
    ],
    "count": 2,
    "timestamp": "2026-01-30T10:00:00"
}
```

---

## Error Handling

All API endpoints return error responses in the following format:

```json
{
    "error": "Error description",
    "timestamp": "2026-01-30T10:00:00"
}
```

**Common HTTP Status Codes**:
- `200`: Success
- `201`: Created
- `400`: Bad Request
- `401`: Unauthorized
- `403`: Forbidden
- `404`: Not Found
- `500`: Internal Server Error

---

## Rate Limiting

Currently no rate limiting implemented. Production deployment should include:
- 100 requests per minute per IP for public endpoints
- 1000 requests per minute per token for authenticated endpoints

---

## Authentication

Future versions will implement JWT-based authentication:
```bash
Authorization: Bearer <jwt_token>
```

---

## Examples

### Example 1: Full Access Flow

```bash
# 1. Capture frame from camera and recognize face
curl -X POST http://localhost:5000/api/recognize \
  -H "Content-Type: application/json" \
  -d '{"frame": "BASE64_IMAGE_DATA"}'

# 2. Log the access
curl -X POST http://localhost:5000/api/log-access \
  -H "Content-Type: application/json" \
  -d '{
    "person_id": "resident_001",
    "access_type": "entry",
    "confidence": 0.92
  }'

# 3. Check for active threats
curl http://localhost:5000/api/threats
```

### Example 2: Monitoring Dashboard

```bash
# Get all system statistics
curl http://localhost:5000/api/stats

# Get today's access logs
curl http://localhost:5000/api/logs?limit=50

# Get high-severity alerts
curl http://localhost:5000/api/threats?severity=HIGH
```

---

**API Version**: 0.1.0  
**Last Updated**: January 30, 2026
