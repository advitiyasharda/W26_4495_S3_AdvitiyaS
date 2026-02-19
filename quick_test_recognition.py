#!/usr/bin/env python3
"""
Quick test to verify facial recognition pipeline works end-to-end
Tests: capture → register → recognize
"""
import cv2
import numpy as np
from pathlib import Path
import sys

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from api.facial_recognition import FacialRecognitionEngine
from data.database import Database

def test_pipeline():
    """Test the complete recognition pipeline"""
    print("\n" + "="*70)
    print("FACIAL RECOGNITION PIPELINE TEST")
    print("="*70)
    
    engine = FacialRecognitionEngine()
    sample_dir = Path('data/samples')
    
    # Step 1: Check for sample photos
    print("\n[STEP 1] Checking for captured photos...")
    if not sample_dir.exists():
        print("  ✗ No sample photos found!")
        print("  Please run: python capture_faces.py")
        return False
    
    person_dirs = [d for d in sample_dir.iterdir() if d.is_dir()]
    print(f"  ✓ Found {len(person_dirs)} people with captured photos")
    
    # Step 2: Register faces from photos
    print("\n[STEP 2] Loading and registering faces...")
    total_loaded = 0
    
    for person_dir in person_dirs:
        person_name = person_dir.name
        photos = list(person_dir.glob('*.jpg')) + list(person_dir.glob('*.png'))
        
        if not photos:
            continue
        
        loaded = 0
        for photo_path in photos:
            try:
                frame = cv2.imread(str(photo_path))
                if frame is None:
                    continue
                
                # Detect face
                faces = engine.detect_faces(frame)
                if len(faces) == 0:
                    continue
                
                # Extract features
                x, y, w, h = faces[0]
                face_roi = frame[y:y+h, x:x+w]
                encoding = engine._extract_face_features(face_roi)
                
                if encoding is not None:
                    engine.register_face(person_name, person_name, encoding)
                    loaded += 1
                    total_loaded += 1
            except Exception as e:
                print(f"    Error with {photo_path.name}: {e}")
                continue
        
        print(f"  ✓ {person_name}: {loaded} photos loaded")
    
    print(f"  ✓ Total faces registered: {total_loaded}")
    
    if total_loaded == 0:
        print("  ✗ No faces could be loaded from photos!")
        return False
    
    # Step 3: Test recognition on stored photos
    print("\n[STEP 3] Testing recognition accuracy...")
    stats = engine.get_recognition_stats()
    print(f"  Registered persons: {stats['total_persons']}")
    print(f"  Total encodings: {stats['total_face_encodings']}")
    
    correct = 0
    total = 0
    
    for person_dir in person_dirs:
        person_name = person_dir.name
        photos = list(person_dir.glob('*.jpg')) + list(person_dir.glob('*.png'))
        
        if not photos:
            continue
        
        person_correct = 0
        person_total = 0
        
        for photo_path in photos:
            try:
                frame = cv2.imread(str(photo_path))
                if frame is None:
                    continue
                
                faces = engine.detect_faces(frame)
                if len(faces) == 0:
                    continue
                
                x, y, w, h = faces[0]
                result = engine.recognize_face(frame, (x, y, w, h))
                
                person_total += 1
                total += 1
                
                if result['person_id'] == person_name:
                    person_correct += 1
                    correct += 1
                    symbol = "✓"
                else:
                    symbol = "✗"
                
                print(f"  {symbol} {photo_path.name}: "
                      f"Expected {person_name}, Got {result['name']} "
                      f"(conf: {result['confidence']:.3f})")
            except Exception as e:
                print(f"  ✗ Error: {e}")
                continue
        
        if person_total > 0:
            acc = 100 * person_correct / person_total
            print(f"    → {person_name} accuracy: {acc:.0f}% ({person_correct}/{person_total})")
    
    # Step 4: Summary
    print("\n[STEP 4] RESULTS")
    print("-" * 70)
    if total > 0:
        accuracy = 100 * correct / total
        print(f"  Total tests: {total}")
        print(f"  Correct: {correct}")
        print(f"  Accuracy: {accuracy:.1f}%")
        
        if accuracy >= 80:
            print("  ✓ Recognition working well!")
            return True
        elif accuracy >= 50:
            print("  ⚠ Recognition partially working (accuracy could be better)")
            print("  Tips:")
            print("    - Capture photos with varied angles/lighting")
            print("    - Ensure good face visibility in photos")
            print("    - Consider capturing 15-20 photos per person")
            return True
        else:
            print("  ✗ Recognition not working well")
            print("  Troubleshooting:")
            print("    - Check photo quality and face visibility")
            print("    - Try different lighting conditions")
            print("    - Delete photos and recapture with better angles")
            return False
    else:
        print("  ✗ No photos could be tested")
        return False

def test_webcam_recognition():
    """Test recognition with live webcam"""
    print("\n" + "="*70)
    print("LIVE WEBCAM RECOGNITION TEST")
    print("="*70)
    
    engine = FacialRecognitionEngine()
    sample_dir = Path('data/samples')
    
    # Load registered faces
    print("\nLoading registered faces...")
    total_loaded = 0
    
    for person_dir in sample_dir.iterdir():
        if not person_dir.is_dir():
            continue
        
        person_name = person_dir.name
        photos = list(person_dir.glob('*.jpg')) + list(person_dir.glob('*.png'))
        
        if not photos:
            continue
        
        for photo_path in photos[:5]:  # Load first 5 photos per person
            try:
                frame = cv2.imread(str(photo_path))
                if frame is None:
                    continue
                
                faces = engine.detect_faces(frame)
                if len(faces) == 0:
                    continue
                
                x, y, w, h = faces[0]
                face_roi = frame[y:y+h, x:x+w]
                encoding = engine._extract_face_features(face_roi)
                
                if encoding is not None:
                    engine.register_face(person_name, person_name, encoding)
                    total_loaded += 1
            except:
                continue
    
    print(f"✓ Loaded {total_loaded} face encodings")
    
    print("\nStarting webcam...")
    print("Press SPACE to capture test, Q to quit")
    
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("✗ Cannot open webcam!")
        return
    
    captured_faces = []
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Flip for mirror effect
            frame = cv2.flip(frame, 1)
            
            # Detect faces
            faces = engine.detect_faces(frame)
            
            for x, y, w, h in faces:
                # Draw rectangle
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                
                # Recognize
                result = engine.recognize_face(frame, (x, y, w, h))
                label = f"{result['name']} ({result['confidence']:.2f})"
                
                cv2.putText(frame, label, (x, y-10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
            # Show instructions
            cv2.putText(frame, "SPACE=capture  Q=quit", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(frame, f"Registered: {engine.get_recognition_stats()['total_persons']} people",
                       (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            cv2.imshow('Face Recognition', frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord(' '):
                if len(faces) > 0:
                    captured_faces.append(frame.copy())
                    print(f"  Captured face {len(captured_faces)}")
            elif key == ord('q'):
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()
    
    print(f"\n✓ Test complete! Captured {len(captured_faces)} frames")

if __name__ == '__main__':
    # First test stored photos
    success = test_pipeline()
    
    if success:
        print("\n" + "="*70)
        choice = input("Test with live webcam? (y/n): ").strip().lower()
        if choice == 'y':
            test_webcam_recognition()
    
    print("\nTest complete!")
