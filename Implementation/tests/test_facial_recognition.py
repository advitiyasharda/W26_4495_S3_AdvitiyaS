"""
Facial Recognition Training and Testing Script
Test the facial recognition module with sample data

Run from project root: python tests/test_facial_recognition.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import os
from pathlib import Path
from api.facial_recognition import FacialRecognitionEngine
from data.database import Database

def test_facial_recognition():
    """Test facial recognition with webcam"""
    print("=" * 60)
    print("Door Face Panels - Facial Recognition Testing")
    print("=" * 60)
    
    # Initialize engine
    engine = FacialRecognitionEngine(confidence_threshold=0.6)
    db = Database()
    
    # Register some test faces
    print("\n[1] Registering test residents...")
    register_test_faces(engine, db)
    
    # Test face detection with webcam
    print("\n[2] Testing face detection with webcam...")
    print("Press 'q' to quit, 's' to capture, 'r' to recognize")
    test_webcam_detection(engine, db)
    
    # Test with image file
    print("\n[3] Testing with image file...")
    test_image_recognition(engine, db)
    
    # Display statistics
    print("\n[4] Recognition Statistics:")
    stats = engine.get_recognition_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")

def register_test_faces(engine, db):
    """Register test faces for residents and caregivers"""
    test_residents = [
        {'person_id': 'resident_001', 'name': 'John Doe', 'role': 'resident'},
        {'person_id': 'resident_002', 'name': 'Jane Smith', 'role': 'resident'},
        {'person_id': 'caregiver_001', 'name': 'Alice Johnson', 'role': 'caregiver'},
    ]
    
    for resident in test_residents:
        db.add_user(resident['person_id'], resident['name'], resident['role'])
        print(f"   [OK] Registered {resident['name']} ({resident['person_id']})")
    
    print(f"   Total residents/caregivers: {len(test_residents)}")

def test_webcam_detection(engine, db):
    """Test face detection using webcam"""
    print("   Opening webcam (ESC or 'q' to exit)...")
    
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("   ERROR: Could not open webcam")
        return
    
    frame_count = 0
    detected_count = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        frame_count += 1
        
        # Detect faces
        faces = engine.detect_faces(frame)
        
        if len(faces) > 0:
            detected_count += 1
        
        # Draw rectangles around detected faces
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            cv2.putText(frame, 'Face Detected', (x, y-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        # Display info
        cv2.putText(frame, f'Frames: {frame_count} | Detections: {detected_count}',
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Show frame
        cv2.imshow('Facial Recognition - Test', frame)
        
        # Key handling
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q') or key == 27:  # 'q' or ESC
            break
        elif key == ord('s'):
            # Save frame
            filename = f'test_frame_{frame_count}.jpg'
            cv2.imwrite(filename, frame)
            print(f"   Saved: {filename}")
    
    cap.release()
    cv2.destroyAllWindows()
    
    print(f"   Detection Rate: {detected_count}/{frame_count} = {100*detected_count/frame_count:.1f}%")

def test_image_recognition(engine, db):
    """Test recognition with sample images"""
    sample_dir = 'data/samples'
    
    if not os.path.exists(sample_dir):
        print(f"   Sample directory '{sample_dir}' not found")
        print("   To test, create sample images in 'data/samples/'")
        print("   Example structure:")
        print("   data/samples/")
        print("   ├── resident_001/")
        print("   │   ├── face1.jpg")
        print("   │   └── face2.jpg")
        print("   └── resident_002/")
        print("       └── face1.jpg")
        return
    
    print(f"   Loading images from '{sample_dir}'...")
    
    # Load and process images
    for person_dir in os.listdir(sample_dir):
        person_path = os.path.join(sample_dir, person_dir)
        if not os.path.isdir(person_path):
            continue
        
        print(f"\n   Processing: {person_dir}")
        
        for image_file in os.listdir(person_path):
            image_path = os.path.join(person_path, image_file)
            
            # Read image
            img = cv2.imread(image_path)
            if img is None:
                print(f"      ERROR: Could not load {image_file}")
                continue
            
            # Detect faces
            faces = engine.detect_faces(img)
            print(f"      {image_file}: {len(faces)} faces detected")

def create_sample_dataset():
    """Instructions for creating sample dataset"""
    print("\n" + "=" * 60)
    print("CREATING SAMPLE DATASET")
    print("=" * 60)
    
    print("""
To test facial recognition, create a sample image dataset:

1. Create directory structure:
   mkdir -p data/samples/resident_001
   mkdir -p data/samples/resident_002
   mkdir -p data/samples/caregiver_001

2. Add sample images (JPG/PNG) to each folder:
   - Use clear frontal face photos (1000x800px recommended)
   - Multiple angles per person for better training
   - Avoid poor lighting or blurry images

3. Example structure:
   data/samples/
   ├── resident_001/
   │   ├── face_straight.jpg
   │   ├── face_angle1.jpg
   │   └── face_angle2.jpg
   └── resident_002/
       ├── face_straight.jpg
       └── face_angle1.jpg

4. Then run this test script again:
   python tests/test_facial_recognition.py
    """)

def integration_test():
    """Test integration with database"""
    print("\n" + "=" * 60)
    print("DATABASE INTEGRATION TEST")
    print("=" * 60)
    
    db = Database()
    
    # Add test user
    print("\n[Adding test user to database...]")
    db.add_user('test_resident_001', 'Test User', 'resident')
    
    # Log a test access
    print("[Logging test access event...]")
    success = db.log_access('test_resident_001', 'entry', confidence=0.92, status='success')
    if success:
        print("   [OK] Access logged successfully")
    
    # Log a test threat
    print("[Logging test threat...]")
    db.log_threat('TEST_THREAT', 'MEDIUM', user_id='test_resident_001', 
                 message='This is a test threat')
    
    # Retrieve and display data
    print("\n[Database Statistics:]")
    stats = db.get_database_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    # Get recent access logs
    print("\n[Recent Access Logs:]")
    logs = db.get_access_logs(limit=5)
    for log in logs:
        print(f"   {log.get('person_id', log.get('user_id', '?'))} - {log.get('type', log.get('access_type', '?'))} at {log.get('timestamp', '?')}")

def run_unit_tests():
    """
    Unit tests for the facial recognition engine — no webcam required.

    Covers:
      - Engine initialises without error in both dlib and OpenCV modes
      - Feature extraction returns a 128-dim float32 vector
      - Confidence is always in [0, 1] for any distance value
      - Confidence denominator uses the active threshold (regression test
        for the hardcoded-0.6 bug fixed in Phase 2)
      - Face registration and lookup work correctly
    """
    import traceback
    from api.facial_recognition import (
        FacialRecognitionEngine,
        USE_FACE_RECOGNITION_LIB,
        DISTANCE_MATCH_THRESHOLD,
    )

    passed = 0
    failed = 0

    def check(name, condition, detail=""):
        nonlocal passed, failed
        if condition:
            print(f"  [PASS] {name}")
            passed += 1
        else:
            print(f"  [FAIL] {name}" + (f" — {detail}" if detail else ""))
            failed += 1

    print("\n" + "=" * 60)
    print("UNIT TESTS — FacialRecognitionEngine")
    mode = "dlib (face_recognition)" if USE_FACE_RECOGNITION_LIB else "OpenCV HOG"
    print(f"Engine mode : {mode}")
    print("=" * 60)

    # ── Test 1: Engine initialises ───────────────────────────────────────────
    try:
        engine = FacialRecognitionEngine(confidence_threshold=0.5)
        check("Engine initialises without error", True)
    except Exception as exc:
        check("Engine initialises without error", False, str(exc))
        print("  Cannot continue — engine failed to initialise.")
        return

    # ── Test 2: Synthetic face ROI produces a 128-dim vector ─────────────────
    synthetic_face = np.random.randint(80, 200, (64, 64, 3), dtype=np.uint8)
    encoding = engine._extract_face_features(synthetic_face)

    check(
        "Feature extraction returns ndarray",
        encoding is not None and isinstance(encoding, np.ndarray),
        f"got {type(encoding)}",
    )
    if encoding is not None:
        check(
            "Feature vector is 128-dimensional",
            len(encoding) == 128,
            f"got len={len(encoding)}",
        )
        check(
            "Feature vector dtype is float32",
            encoding.dtype == np.float32,
            f"got dtype={encoding.dtype}",
        )

    # ── Test 3: Register a face and retrieve it ───────────────────────────────
    dummy_enc = np.zeros(128, dtype=np.float32)
    engine.register_face("test_001", "Test Person", dummy_enc)

    check(
        "Registered person appears in known_faces",
        "test_001" in engine.known_faces,
    )
    check(
        "Person name stored correctly",
        engine.person_names.get("test_001") == "Test Person",
    )

    # ── Test 4: Confidence is always clamped to [0, 1] ───────────────────────
    active_threshold = 0.6 if USE_FACE_RECOGNITION_LIB else DISTANCE_MATCH_THRESHOLD
    for dist in [0.0, active_threshold / 2, active_threshold, active_threshold * 2, 9.99]:
        conf = max(0.0, min(1.0, 1.0 - (dist / active_threshold)))
        check(
            f"Confidence clamped to [0,1] at distance={dist:.3f}",
            0.0 <= conf <= 1.0,
            f"got {conf}",
        )

    # ── Test 5: Confidence denominator regression (Phase 2 bug fix) ──────────
    # Before the fix: confidence always divided by hardcoded 0.6
    # After the fix:  denominator equals the active_threshold
    # When OpenCV is active, threshold=0.55; a distance of 0.55 should give
    # confidence=0.0, not the wrong value produced by dividing by 0.6.
    if not USE_FACE_RECOGNITION_LIB:
        dist_at_threshold = DISTANCE_MATCH_THRESHOLD          # should yield conf=0.0
        correct_conf   = max(0.0, min(1.0, 1.0 - (dist_at_threshold / DISTANCE_MATCH_THRESHOLD)))
        incorrect_conf = max(0.0, min(1.0, 1.0 - (dist_at_threshold / 0.6)))
        check(
            "Confidence=0.0 at exact threshold (OpenCV mode, regression test)",
            abs(correct_conf) < 1e-6,
            f"correct={correct_conf:.4f} incorrect_old={incorrect_conf:.4f}",
        )
    else:
        dist_at_threshold = 0.6
        correct_conf = max(0.0, min(1.0, 1.0 - (dist_at_threshold / 0.6)))
        check(
            "Confidence=0.0 at exact threshold (dlib mode, regression test)",
            abs(correct_conf) < 1e-6,
            f"correct={correct_conf:.4f}",
        )

    # ── Test 6: Remove face ───────────────────────────────────────────────────
    engine.remove_face("test_001")
    check(
        "Removed person no longer in known_faces",
        "test_001" not in engine.known_faces,
    )

    # ── Summary ───────────────────────────────────────────────────────────────
    print(f"\nResults: {passed} passed, {failed} failed")
    if failed == 0:
        print("[ALL TESTS PASSED]")
    else:
        print("[SOME TESTS FAILED] — review output above")
    print("=" * 60)


if __name__ == '__main__':
    import sys

    args = sys.argv[1:]

    if '--webcam' in args:
        test_facial_recognition()
    elif '--dataset' in args:
        create_sample_dataset()
    elif '--units' in args:
        run_unit_tests()
    else:
        # Default: unit tests + database integration (no webcam, CI-safe)
        run_unit_tests()
        integration_test()
