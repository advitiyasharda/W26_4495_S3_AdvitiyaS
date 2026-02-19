# Quick Start Guide - Training & Testing

## Overview

Three test scripts to train and validate the system:

1. **test_facial_recognition.py** - Face detection with webcam
2. **train_anomaly_detection.py** - Train ML models with synthetic data
3. **test_integration.py** - Full system integration test

---

## Quick Start (5 minutes)

### Option 1: Full System Integration Test (Recommended for beginners)

```bash
# Run complete end-to-end test
python test_integration.py

# Select option "1" for complete flow test
# This simulates:
#   - 20 realistic door access events
#   - Normal patterns + anomalies
#   - Failed attempts and unusual activity
#   - Full alert detection pipeline
```

**Output**: System statistics, threat detection, anomaly scores

---

## Detailed Testing Workflows

### Workflow A: Train Anomaly Detection Model

Perfect for training with synthetic data (no hardware needed)

```bash
# 1. Run full training pipeline
python train_anomaly_detection.py

# Select "1" for complete pipeline:
#   ├─ Generate 30 days of synthetic data (3 residents)
#   ├─ Train Isolation Forest model
#   ├─ Evaluate performance (accuracy, precision, recall, F1)
#   ├─ Build behavioral profiles
#   └─ Test real-time predictions
```

**What happens:**
```
✓ Generates 2,000-3,000 synthetic access events
✓ Trains model on normal vs anomalous patterns
✓ Shows performance metrics:
   - Accuracy, Precision, Recall, F1-Score
✓ Saves trained model: models/isolation_forest.pkl
✓ Tests real-time predictions
```

**Expected Performance:**
- F1-Score: >80%
- Inference time: <200ms
- Data: 30 days, 3 residents

---

### Workflow B: Facial Recognition with Webcam

Test face detection in real-time (requires webcam)

```bash
# 1. Run facial recognition test
python test_facial_recognition.py

# Select "1" for webcam test:
#   - Opens webcam feed
#   - Detects faces in real-time
#   - Draws bounding boxes
#   - Shows detection rate
#   - Press 'q' to exit
```

**Controls:**
- `q` - Quit
- `s` - Capture frame
- `ESC` - Exit

**Performance Target:**
- Detection rate: >90%
- Latency: <500ms per frame

---

### Workflow C: Database Integration Test

Test data persistence and logging

```bash
# 2. Run database test
python test_facial_recognition.py

# Select "2" for database integration test:
#   - Creates test users
#   - Logs access events
#   - Records threats
#   - Shows database statistics
```

---

## Anomaly Detection Training Details

### Generate Different Datasets

```bash
python train_anomaly_detection.py

# Option 1: Full pipeline (default)
# Option 2: Generate data only
python -c "
from train_anomaly_detection import AnomalyTrainer
trainer = AnomalyTrainer()
# 90 days, 5 residents
trainer.generate_training_data(num_days=90, num_residents=5)
"

# Option 3: Train on existing data
python -c "
from train_anomaly_detection import AnomalyTrainer
trainer = AnomalyTrainer()
trainer.train_model('data/synthetic_dataset.csv')
"

# Option 4: Evaluate performance
trainer.evaluate_model('data/synthetic_dataset.csv')
```

### Synthetic Data Patterns Generated

**Normal Patterns:**
- Regular morning entry (7-9 AM)
- Mid-day exits/entries
- Evening exit (5-8 PM)
- Consistent daily routine

**Anomalous Patterns (15% of data):**
- **Wandering**: 5-12 entries/exits in 1-2 hours (dementia behavior)
- **Inactivity**: Single entry, no exits for extended period (potential fall)
- **Unusual Time**: Activity between 2-5 AM
- **Frequency Spike**: 8-15 accesses in single day

---

## Full Integration Test Details

### Test Flow

```
1. Setup
   └─ Register 3 residents + 1 caregiver

2. Process 20 Events
   ├─ Facial Recognition
   ├─ Access Logging
   ├─ Anomaly Detection
   └─ Threat Detection

3. Display Summary
   ├─ Database statistics
   ├─ Active threats
   ├─ Anomalies detected
   └─ Performance metrics
```

### Detected Events

**Normal:**
- Standard entry/exit with high confidence

**Anomalies:**
- Failed access attempts (low confidence)
- Wandering patterns
- Unusual times

**Threats:**
- REPEATED_FAILED_ACCESS
- UNUSUAL_ACCESS_TIME
- FREQUENCY_SPIKE

---

## Production Training Pipeline

### Step 1: Prepare Training Data

```python
from data import SyntheticDataGenerator

gen = SyntheticDataGenerator()
dataset = gen.generate_dataset(
    num_residents=5,
    num_caregivers=3,
    num_days=90,
    anomaly_rate=0.20
)
```

### Step 2: Train Model

```python
from models import AnomalyDetector

detector = AnomalyDetector(model_type='isolation_forest')
features = detector.extract_features(events)
detector.train_isolation_forest(features)
detector.save_model('models/production_model.pkl')
```

### Step 3: Deploy to Flask API

The trained model automatically loads in the API:

```bash
python main.py

# Then make predictions via API:
curl -X POST http://localhost:5000/api/recognize \
  -H "Content-Type: application/json" \
  -d '{"frame": "BASE64_IMAGE_DATA"}'
```

### Step 4: Monitor Performance

```bash
# Check system statistics
curl http://localhost:5000/api/stats

# View active alerts
curl http://localhost:5000/api/threats

# Export audit logs
curl http://localhost:5000/api/compliance/audit > audit.json
```

---

## Performance Benchmarks

### Facial Recognition
- OpenCV Detection: ~50-100ms per frame
- Target latency: <500ms on Raspberry Pi

### Anomaly Detection
- Feature extraction: ~1-5ms per event
- Inference: <200ms on Raspberry Pi
- Training: ~5-15 seconds on synthetic data

### System Overall
- API response time: <100ms average
- Database queries: <50ms
- Threat detection: <10ms per rule

---

## Troubleshooting

### "No module named X"
```bash
pip install -r requirements.txt
```

### Webcam not working
```bash
# Check device access
python -c "import cv2; cap = cv2.VideoCapture(0); print(cap.isOpened())"

# On Linux: grant permissions
sudo usermod -a -G video $USER
```

### Memory issues on Raspberry Pi
```python
# In config.py - reduce model complexity
ISOLATION_FOREST_N_ESTIMATORS = 50  # from 100
ISOLATION_FOREST_CONTAMINATION = 0.2  # from 0.1
```

### Database locked error
```bash
# Reset database
rm data/doorface.db
python -c "from data import Database; db = Database()"
```

---

## Next Steps

1. **Complete Integration Test** → `python test_integration.py`
2. **Train Full Model** → `python train_anomaly_detection.py`
3. **Test on Real Data** → Add images to `data/samples/`
4. **Deploy to Raspberry Pi** → See `docs/DEPLOYMENT.md`
5. **Integrate with Flask API** → Already pre-configured in `api/routes.py`

---

## File Locations

```
doortest/
├── test_facial_recognition.py  # Webcam + database tests
├── train_anomaly_detection.py  # ML training pipeline
├── test_integration.py         # Full system test
├── data/
│   ├── synthetic_dataset.csv   # Generated training data
│   └── doorface.db             # SQLite database
├── models/
│   └── isolation_forest.pkl    # Trained model
└── api/
    └── routes.py               # API integration
```

---

**Start Here**: `python test_integration.py` (select option 1)
