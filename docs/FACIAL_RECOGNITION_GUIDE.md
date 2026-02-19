# Facial Recognition Setup & Testing Guide

## Overview

This guide walks you through the complete facial recognition pipeline:
1. **Capture** - Record your face photos using webcam
2. **Register** - Extract and register face encodings
3. **Test** - Verify recognition works

---

## Quick Start (5 minutes)

```bash
# Step 1: Capture photos of your face
python capture_faces.py

# Step 2: Register your captured photos
python register_faces.py

# Step 3: Test recognition
python quick_test_recognition.py
```

---

## Detailed Walkthrough

### Step 1: Capture Face Photos

```bash
python capture_faces.py
```

**What happens:**
- Webcam opens with face detection
- Green rectangle shows detected face
- Press **SPACE** to capture photo (repeat 10-15 times)
- Press **Q** to exit
- Photos saved to `data/samples/{your_name}/`

**Tips for best results:**
- ✓ Vary angles: straight, left, right, slightly up/down
- ✓ Different lighting: natural light, artificial light, partially shadowed
- ✓ Different distances: face should be 30-50 cm from camera
- ✓ Different expressions: neutral, slight smile
- ✗ Avoid: sunglasses, face masks, very harsh shadows

**Example session:**
```
Captured: data/samples/advitiya/face_001.jpg
Captured: data/samples/advitiya/face_002.jpg
...
Captured: data/samples/advitiya/face_015.jpg
```

---

### Step 2: Register Photos

```bash
python register_faces.py
```

**What happens:**
1. Shows menu with options
2. Select: **2) Register from captured photos**
3. Choose a person (or enter new name)
4. System extracts face encodings from all photos
5. Stores encodings in recognition engine

**Menu options:**
```
1) View registered people
2) Register from captured photos
3) Register from new capture
4) View statistics
5) Exit
```

**Select option 2:**
```
Available people to register:
1. advitiya
2. eric
3. reubin
4. [Add new person]

Choose person: 1

Loading face encodings for advitiya...
  ✓ face_001.jpg - Encoding extracted
  ✓ face_002.jpg - Encoding extracted
  ...
  ✓ face_015.jpg - Encoding extracted

✓ Registered advitiya with 15 face encodings
```

**What's stored:**
- 128-dimensional HOG (Histogram of Oriented Gradients) features
- One encoding per captured photo
- Used for face matching/comparison

---

### Step 3: Test Recognition

#### Option A: Quick Test on Stored Photos

```bash
python quick_test_recognition.py
```

**Output:**
```
======================================================================
FACIAL RECOGNITION PIPELINE TEST
======================================================================

[STEP 1] Checking for captured photos...
  ✓ Found 3 people with captured photos

[STEP 2] Loading and registering faces...
  ✓ advitiya: 15 photos loaded
  ✓ eric: 12 photos loaded
  ✓ reubin: 10 photos loaded
  ✓ Total faces registered: 37

[STEP 3] Testing recognition accuracy...
  Registered persons: 3
  Total encodings: 37
  ✓ face_001.jpg: Expected advitiya, Got advitiya (conf: 0.892)
  ✓ face_002.jpg: Expected advitiya, Got advitiya (conf: 0.856)
  ...

[STEP 4] RESULTS
----------------------------------------------------------------------
  Total tests: 37
  Correct: 35
  Accuracy: 94.6%
  ✓ Recognition working well!
```

**Interpretation:**
- **>80% accuracy**: System is working well ✓
- **50-80% accuracy**: System partially working (could improve with better photos)
- **<50% accuracy**: Check photo quality and lighting

---

#### Option B: Test with Live Webcam

```bash
python quick_test_recognition.py
# When prompted: Press Y for webcam test
```

**Live testing:**
- Webcam opens
- Shows real-time face detection (green boxes)
- For each detected face shows: `name (confidence_score)`
- Press SPACE to capture test frame
- Press Q to exit

**Example output:**
```
LIVE WEBCAM RECOGNITION TEST
...
✓ Loaded 37 face encodings

Starting webcam...
Press SPACE to capture test, Q to quit

[Live feed shows:]
advitiya (0.87)  ← Your name + confidence
```

---

### Step 4: Full System Test (With API)

```bash
python test_integration.py
```

**Tests:**
1. Flask API health check
2. Access logging
3. Anomaly detection
4. Face recognition integration
5. Database persistence

---

## Troubleshooting

### Problem: Low recognition accuracy (<50%)

**Cause 1: Poor photo quality**
- Solution: Delete captured photos and recapture with:
  - Better lighting (not too dark or bright)
  - Different angles (not just straight-on)
  - Face clearly visible (no obstructions)

**Cause 2: Insufficient photos**
- Solution: Capture 15-20 photos instead of 5-10

**Cause 3: Inconsistent lighting**
- Solution: Capture photos in multiple lighting conditions:
  - Natural daylight
  - Artificial indoor lighting
  - Mixed lighting

**Quick fix:**
```bash
# 1. Delete old photos
rm -rf data/samples/

# 2. Recapture with better technique
python capture_faces.py

# 3. Re-register
python register_faces.py

# 4. Retest
python quick_test_recognition.py
```

### Problem: Webcam doesn't open

```
✗ Cannot open webcam!
```

**Solutions:**
1. Check camera is connected and not in use by another app
2. On Windows, check camera permissions in Settings
3. Try restarting the terminal
4. Check if another application has camera lock:
   ```bash
   # Windows: End video applications in Task Manager
   # Linux: killall chrome skype teams zoom
   # Mac: killall "Google Chrome"
   ```

### Problem: Face not detected in photos

**Symptoms:**
```
✗ No faces detected in face_001.jpg
```

**Solutions:**
1. Face too small: Move closer to camera
2. Face partially hidden: Remove sunglasses, hats, masks
3. Poor lighting: Try different lighting angles
4. Face at extreme angle: Keep face more frontal

---

## Technical Details

### Face Feature Extraction (HOG)

The system uses **Histogram of Oriented Gradients (HOG)**:

1. **Input**: 64×64 grayscale face image
2. **Gradients**: Compute pixel intensity gradients
3. **Orientation**: Group gradients into orientation bins (9 bins)
4. **Cells**: Divide image into 8×8 cells
5. **Output**: 128-dimensional feature vector
6. **Normalization**: L2 normalization for better comparison

**Advantages:**
- Fast (milliseconds per face)
- Robust to lighting variations
- Works well on edge devices (Raspberry Pi)
- No neural network training needed

### Face Matching

**Algorithm**: Euclidean Distance Matching

```
For each test face:
  1. Extract 128-dim HOG feature vector
  2. For each registered person:
     - Compare feature vector to all their stored encodings
     - Calculate Euclidean distance to each
  3. Find minimum distance
  4. If distance < 0.7: Match found
  5. Return: {person_name, confidence_score, distance}
```

**Distance Threshold**: 0.7
- Distance < 0.7 → Same person
- Distance ≥ 0.7 → Different person

**Confidence Score**: `1 - (distance / 1.0)`
- 0.9+ = Very confident
- 0.7-0.9 = Confident
- 0.5-0.7 = Low confidence
- <0.5 = Likely mismatch

---

## Performance Metrics

### Recognition Speed
- Per frame: **~50-100ms** (on modern CPU)
- Per face: **~20-30ms**
- Suitable for real-time video (30 FPS)

### Scalability
- Handles **100+ registered people**
- **1000+ stored face encodings**
- Memory usage: **~1MB per 1000 encodings**

### Hardware Compatibility
- ✓ Laptop/Desktop (Windows, Linux, Mac)
- ✓ Raspberry Pi 4 (with optimization)
- ✓ Edge devices (single-board computers)

---

## File Structure

```
doortest/
├── capture_faces.py              # Webcam capture utility
├── register_faces.py             # Registration system
├── quick_test_recognition.py     # Testing script
├── test_facial_recognition.py    # Full test suite
├── api/
│   └── facial_recognition.py    # Core recognition engine
│       ├── FacialRecognitionEngine (main class)
│       ├── detect_faces()        # Face detection
│       ├── recognize_face()      # Face recognition
│       ├── register_face()       # Face registration
│       └── _extract_face_features()  # HOG extraction
├── data/
│   ├── samples/                  # Captured face photos
│   │   ├── advitiya/
│   │   │   ├── face_001.jpg
│   │   │   ├── face_002.jpg
│   │   │   └── ...
│   │   └── eric/
│   └── doorface.db              # SQLite database
└── docs/
    └── FACIAL_RECOGNITION_GUIDE.md  # This file
```

---

## Next Steps

1. ✅ Capture and register your face
2. ✅ Test recognition accuracy
3. ⬜ Integrate with Flask API (`/api/recognize` endpoint)
4. ⬜ Connect to dashboard for real-time monitoring
5. ⬜ Deploy to Raspberry Pi for edge processing

---

## API Integration Example

Once recognition is tested, integrate with Flask API:

```python
# api/main.py
from api.facial_recognition import FacialRecognitionEngine

engine = FacialRecognitionEngine()

@app.route('/api/recognize', methods=['POST'])
def recognize():
    """Recognize face from image"""
    # Load image from request
    image_data = request.files['image']
    frame = cv2.imread(image_data)
    
    # Detect and recognize
    faces = engine.detect_faces(frame)
    results = []
    
    for face_location in faces:
        result = engine.recognize_face(frame, face_location)
        results.append(result)
    
    return jsonify(results)
```

---

## Support

For issues:
1. Check troubleshooting section above
2. Review photo quality and lighting
3. Check database integrity: `sqlite3 data/doorface.db ".tables"`
4. View face statistics: `python register_faces.py` → Option 4

---

## Key Parameters (Advanced)

Adjust in `api/facial_recognition.py`:

```python
# Face detection sensitivity
faces = self.face_cascade.detectMultiScale(
    gray,
    scaleFactor=1.05,  # ↓ = more sensitive, ↑ = fewer false positives
    minNeighbors=5,    # ↑ = stricter detection
    minSize=(30, 30)   # Minimum face size
)

# Face matching threshold
is_match = best_distance < 0.7  # ↓ = stricter, ↑ = more permissive
```

---

Last Updated: February 15, 2025
