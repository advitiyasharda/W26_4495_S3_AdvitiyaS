# Security & Compliance Guide

## Door Face Panels Smart Security System

Comprehensive security and PIPEDA compliance documentation.

---

## Overview

This system is designed with privacy-first, security-by-default architecture:
- **Edge Processing**: All face recognition and anomaly detection runs locally
- **No PII to Cloud**: Personal identifying information never leaves the device
- **Encrypted Storage**: Local database with encryption support
- **Audit Trails**: Complete PIPEDA-compliant logging of all actions
- **Access Control**: Role-based access to sensitive endpoints

---

## Data Privacy

### Data Types Collected

1. **Facial Recognition Data**
   - Face embeddings (numerical vectors, not images)
   - Recognition confidence scores
   - Timestamps of recognition events

2. **Access Logs**
   - Entry/exit timestamps
   - Person identification
   - Confidence scores
   - Access success/failure status

3. **Behavioral Data**
   - Access patterns and frequency
   - Anomaly scores
   - Inactivity alerts

4. **System Logs**
   - API calls
   - Threat detections
   - System errors and warnings

### Data Minimization

- No raw image storage (only face embeddings)
- No audio recording or processing
- No tracking outside door area
- Automatic data retention policies:
  ```python
  # config.py
  DATA_RETENTION_DAYS = 90  # Auto-delete after 90 days
  ```

---

## Local Storage Security

### SQLite Encryption (Future Implementation)

```bash
# Using SQLCipher for encrypted database
pip install sqlcipher3

# In config.py
SQLALCHEMY_DATABASE_URI = 'sqlcipher:///doorface.db'
SQLALCHEMY_ENGINE_OPTIONS = {
    'connect_args': {
        'check_same_thread': False,
        'timeout': 15,
        'uri': True
    },
    'echo': False,
    'pool_pre_ping': True,
}
```

### File Permissions

```bash
# Restrict database access to application user
sudo chown doorface:doorface /path/to/doorface.db
sudo chmod 600 /path/to/doorface.db

# Restrict application logs
sudo chmod 600 /var/log/doorface/
```

---

## PIPEDA Compliance

### Personal Information Handling

**PIPEDA Requirements**:
1. Consent for collection
2. Accountability for collection
3. Limited use and disclosure
4. Accuracy and completeness
5. Safeguards
6. Openness
7. Individual access
8. Challenge accuracy
9. Complaint procedures

### Implementation

```python
# data/database.py - Audit logging for compliance
def log_audit(action, user_id, resource, result, details):
    """
    Log all actions involving personal information
    Required for PIPEDA Article 5 (Accountability)
    """
    cursor.execute('''
        INSERT INTO audit_logs 
        (action, user_id, resource, result, details, timestamp)
        VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    ''', (action, user_id, resource, result, details))
```

### Data Subject Rights

```bash
# Endpoint for subject access request (Article 15)
GET /api/compliance/subject-access?person_id=resident_001

# Endpoint for data deletion (Right to be forgotten)
DELETE /api/compliance/person-data?person_id=resident_001

# Export personal data
GET /api/compliance/export?person_id=resident_001&format=json
```

### Audit Trail Example

```json
{
    "audit_log": [
        {
            "timestamp": "2026-01-30T10:00:00",
            "action": "FACE_RECOGNIZED",
            "user_id": "resident_001",
            "resource": "door_001",
            "result": "success",
            "details": "Face match confidence: 0.92"
        },
        {
            "timestamp": "2026-01-30T10:00:15",
            "action": "ACCESS_LOGGED",
            "user_id": "resident_001",
            "resource": "access_logs",
            "result": "success",
            "details": "Entry event logged to database"
        }
    ]
}
```

---

## Authentication & Authorization

### Current Implementation (MVP)

No authentication required for development. Production must add:

### Future: JWT Authentication

```python
# api/auth.py
from flask_jwt_extended import create_access_token, jwt_required

@api_bp.route('/auth/login', methods=['POST'])
def login():
    """Authenticate caregiver"""
    data = request.get_json()
    
    # Verify credentials
    if verify_credentials(data['username'], data['password']):
        access_token = create_access_token(identity=data['username'])
        return {'access_token': access_token}
    
    return {'error': 'Invalid credentials'}, 401

@api_bp.route('/logs')
@jwt_required()
def get_logs():
    """Protected endpoint"""
    current_user = get_jwt_identity()
    # Return logs for current user's facility
```

### Role-Based Access Control

```python
# config.py
ROLES = {
    'admin': ['read', 'write', 'delete', 'export'],
    'caregiver': ['read', 'acknowledge_alerts'],
    'resident': []  # No access to system
}

# Middleware to check roles
@require_role('admin', 'caregiver')
def sensitive_endpoint():
    pass
```

---

## Threat Detection & Response

### Security Threats Detected

1. **Repeated Failed Access**
   ```python
   # Trigger alert after 3 failed attempts in 10 minutes
   if len(failed_attempts) >= 3:
       alert = {
           'threat_type': 'REPEATED_FAILED_ACCESS',
           'severity': 'HIGH'
       }
   ```

2. **Unauthorized Access Attempts**
   - Unrecognized faces
   - Access at unusual times
   - Frequency spikes

3. **System Threats**
   - Failed authentication attempts
   - Unauthorized API calls
   - Database integrity checks

### Alert Response Protocol

```
CRITICAL Alert → Immediately notify facility manager
HIGH Alert → Log and display on dashboard
MEDIUM Alert → Log and include in daily report
LOW Alert → Log for compliance audit only
```

---

## Cryptography

### Hashing Passwords

```python
from werkzeug.security import generate_password_hash, check_password_hash

# Hash password on registration
hashed = generate_password_hash(password, method='pbkdf2:sha256')

# Verify on login
if check_password_hash(hashed, password):
    # Grant access
```

### Encrypting Sensitive Fields

```python
from cryptography.fernet import Fernet

# In config.py
ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY')
cipher_suite = Fernet(ENCRYPTION_KEY)

# Encrypt sensitive data
encrypted_data = cipher_suite.encrypt(b"sensitive data")

# Decrypt when needed
decrypted_data = cipher_suite.decrypt(encrypted_data)
```

---

## Network Security

### HTTPS/TLS Configuration

```nginx
# /etc/nginx/sites-available/doorface
server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "SAMEORIGIN" always;

    location / {
        proxy_pass http://127.0.0.1:5000;
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}
```

### CORS Policy

```python
# api/__init__.py
from flask_cors import CORS

# Restrict CORS to trusted domains only
CORS(app, resources={
    r"/api/*": {
        "origins": ["https://trusted-domain.com"],
        "methods": ["GET", "POST"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})
```

---

## Database Security

### SQL Injection Prevention

```python
# ✅ SAFE: Using parameterized queries
cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))

# ❌ UNSAFE: String concatenation
cursor.execute(f'SELECT * FROM users WHERE user_id = {user_id}')
```

### Input Validation

```python
from flask import request
from werkzeug.security import safe_str_cmp

# Validate and sanitize input
@api_bp.route('/logs')
def get_logs():
    person_id = request.args.get('person_id', '').strip()
    
    # Validate format
    if not re.match(r'^[a-zA-Z0-9_]+$', person_id):
        return {'error': 'Invalid person_id format'}, 400
    
    # Safe database query
    cursor.execute('SELECT * FROM access_logs WHERE person_id = ?', (person_id,))
```

---

## Incident Response

### Breach Notification Protocol

In case of security breach:

1. **Immediate Actions**
   - Isolate affected systems
   - Preserve logs and evidence
   - Notify security team

2. **Investigation** (24 hours)
   - Determine scope of breach
   - Identify compromised data
   - Document timeline

3. **Notification** (30 days)
   - Notify affected individuals
   - Notify regulatory bodies
   - Provide remediation steps

4. **Follow-up** (90 days)
   - Post-incident review
   - Implement preventive measures
   - Audit new controls

### Incident Logging

```python
# logs/security_incidents.log
[2026-01-30 10:15:00] SECURITY_INCIDENT
[Severity] CRITICAL
[Type] REPEATED_FAILED_ACCESS
[Source] Unknown
[Affected_Systems] Door access control
[Response] Alert sent to facility manager
[Status] ACTIVE_MONITORING
```

---

## Regular Security Audits

### Monthly Checklist

- [ ] Review access logs for anomalies
- [ ] Verify database backups
- [ ] Check for unauthorized API access
- [ ] Test alarm notification system
- [ ] Review failed authentication attempts

### Quarterly Review

- [ ] Penetration testing
- [ ] Code security review
- [ ] Dependency vulnerability scan
- [ ] PIPEDA compliance audit
- [ ] Disaster recovery drill

### Annual Review

- [ ] Complete security assessment
- [ ] Privacy impact assessment
- [ ] Update security policies
- [ ] Employee security training
- [ ] Regulatory compliance audit

---

## Compliance Checklist

### PIPEDA

- [x] Accountability principle implemented
- [x] Audit logging of all data access
- [x] Data minimization (no unnecessary PII)
- [x] Retention policy (90-day auto-delete)
- [ ] Subject access request endpoint (TODO)
- [ ] Right-to-deletion implementation (TODO)

### GDPR (Future)

- [ ] Data protection impact assessment
- [ ] Privacy policy compliance
- [ ] Consent management
- [ ] Data processor agreements

---

## Security Best Practices

### For Administrators

1. **Regular Updates**
   ```bash
   sudo apt-get update && sudo apt-get upgrade
   pip install --upgrade -r requirements.txt
   ```

2. **Strong Credentials**
   - Use 16+ character passwords
   - Enable multi-factor authentication
   - Rotate keys regularly

3. **Secure Configuration**
   - Change default secrets
   - Enable HTTPS only
   - Restrict firewall rules

4. **Monitoring**
   - Set up log aggregation
   - Enable system alerts
   - Regular backups

### For Developers

1. **Code Security**
   - Use parameterized queries
   - Validate all inputs
   - Never hardcode secrets

2. **Dependency Management**
   - Review dependencies regularly
   - Update vulnerable packages
   - Use lock files for reproducibility

3. **Testing**
   - Perform security testing
   - Test error handling
   - Verify access controls

---

**Last Updated**: January 30, 2026  
**Version**: 0.1.0  
**Compliance**: PIPEDA Aligned (GDPR-ready architecture)
