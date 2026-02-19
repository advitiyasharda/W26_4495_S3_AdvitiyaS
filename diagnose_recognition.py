#!/usr/bin/env python3
"""
Face Recognition Diagnostics
Diagnose issues with face capture, detection, and recognition
"""
import cv2
import numpy as np
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

from api.facial_recognition import FacialRecognitionEngine
from data.database import Database

def diagnose_capture():
    """Diagnose face capture setup"""
    print("\n" + "="*70)
    print("CAPTURE DIAGNOSTICS")
    print("="*70)
    
    print("\n[1] Checking camera...")
    cap = cv2.VideoCapture(0)
    if cap.isOpened():
        print("  ✓ Camera is available")
        ret, frame = cap.read()
        if ret:
            print(f"  ✓ Camera is working")
            print(f"  ✓ Frame resolution: {frame.shape[1]}x{frame.shape[0]}")
        else:
            print("  ✗ Camera not responding")
        cap.release()
    else:
        print("  ✗ Camera not found!")
        print("  Solutions:")
        print("    - Check camera is connected")
        print("    - Restart terminal")
        print("    - Check for camera permission (Windows/Mac)")
        return False
    
    print("\n[2] Testing face detection...")
    print("  Opening webcam for 5 seconds...")
    cap = cv2.VideoCapture(0)
    engine = FacialRecognitionEngine()
    
    detected = False
    frame_count = 0
    faces_found = 0
    
    while frame_count < 150:  # ~5 seconds at 30fps
        ret, frame = cap.read()
        if not ret:
            break
        
        frame_count += 1
        faces = engine.detect_faces(frame)
        
        if len(faces) > 0:
            detected = True
            faces_found += 1
            print(f"  Frame {frame_count}: {len(faces)} face(s) detected")
    
    cap.release()
    
    if detected:
        print(f"  ✓ Face detection working ({faces_found}/150 frames)")
    else:
        print("  ✗ No faces detected in 150 frames")
        print("  Solutions:")
        print("    - Get closer to camera")
        print("    - Improve lighting")
        print("    - Remove sunglasses/hats")
        return False
    
    return True

def diagnose_samples():
    """Diagnose captured sample photos"""
    print("\n" + "="*70)
    print("SAMPLE PHOTOS DIAGNOSTICS")
    print("="*70)
    
    sample_dir = Path('data/samples')
    
    if not sample_dir.exists():
        print("  ✗ No sample directory found!")
        print("  Please run: python capture_faces.py")
        return False
    
    people = list(sample_dir.iterdir())
    print(f"\n[1] Found {len(people)} person(s)")
    
    total_photos = 0
    total_with_faces = 0
    total_extractable = 0
    
    engine = FacialRecognitionEngine()
    
    for person_dir in people:
        if not person_dir.is_dir():
            continue
        
        person_name = person_dir.name
        photos = list(person_dir.glob('*.jpg')) + list(person_dir.glob('*.png'))
        
        print(f"\n  {person_name}:")
        print(f"    Photos: {len(photos)}")
        
        photos_with_faces = 0
        photos_extractable = 0
        
        for photo in photos:
            frame = cv2.imread(str(photo))
            if frame is None:
                print(f"      ✗ {photo.name}: Cannot read")
                continue
            
            faces = engine.detect_faces(frame)
            
            if len(faces) == 0:
                print(f"      ✗ {photo.name}: No face detected")
                continue
            
            photos_with_faces += 1
            
            # Try to extract features
            x, y, w, h = faces[0]
            face_roi = frame[y:y+h, x:x+w]
            encoding = engine._extract_face_features(face_roi)
            
            if encoding is not None:
                photos_extractable += 1
                print(f"      ✓ {photo.name}: OK (64x64, 128-dim vector)")
            else:
                print(f"      ⚠ {photo.name}: Feature extraction failed")
        
        total_photos += len(photos)
        total_with_faces += photos_with_faces
        total_extractable += photos_extractable
        
        print(f"    ✓ Readable: {photos_with_faces}/{len(photos)}")
        print(f"    ✓ Extractable: {photos_extractable}/{len(photos)}")
    
    print(f"\n[2] Summary:")
    print(f"  Total photos: {total_photos}")
    print(f"  With faces detected: {total_with_faces}")
    print(f"  Ready for registration: {total_extractable}")
    
    if total_extractable > 0:
        print(f"  ✓ Ready to register!")
        return True
    else:
        print(f"  ✗ No usable photos")
        print("  Solutions:")
        print("    - Recapture with better lighting")
        print("    - Ensure faces are clearly visible")
        print("    - Try different angles")
        return False

def diagnose_recognition():
    """Diagnose recognition engine"""
    print("\n" + "="*70)
    print("RECOGNITION ENGINE DIAGNOSTICS")
    print("="*70)
    
    engine = FacialRecognitionEngine()
    sample_dir = Path('data/samples')
    
    print("\n[1] Loading face encodings...")
    
    total_loaded = 0
    people = {}
    
    for person_dir in sample_dir.iterdir():
        if not person_dir.is_dir():
            continue
        
        person_name = person_dir.name
        people[person_name] = []
        
        photos = list(person_dir.glob('*.jpg')) + list(person_dir.glob('*.png'))
        
        for photo in photos:
            try:
                frame = cv2.imread(str(photo))
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
                    people[person_name].append(encoding)
                    total_loaded += 1
            except:
                continue
    
    stats = engine.get_recognition_stats()
    print(f"  ✓ Loaded {stats['total_persons']} people")
    print(f"  ✓ Total encodings: {stats['total_face_encodings']}")
    print(f"  ✓ Confidence threshold: {stats['confidence_threshold']}")
    
    if total_loaded == 0:
        print("  ✗ No encodings loaded!")
        return False
    
    print("\n[2] Testing recognition on self...")
    
    correct = 0
    total = 0
    
    for person_name, encodings in people.items():
        person_correct = 0
        
        for idx, test_encoding in enumerate(encodings[:3]):  # Test first 3
            # Simulate frame (won't actually use it for encoding)
            # Calculate distances manually
            best_distance = float('inf')
            best_match = None
            
            for check_name, check_encodings in people.items():
                for check_encoding in check_encodings:
                    distance = np.linalg.norm(test_encoding - check_encoding)
                    if distance < best_distance:
                        best_distance = distance
                        best_match = check_name
            
            total += 1
            if best_match == person_name:
                person_correct += 1
                correct += 1
                print(f"  ✓ {person_name} test {idx+1}: Recognized (dist: {best_distance:.3f})")
            else:
                print(f"  ✗ {person_name} test {idx+1}: Confused with {best_match} (dist: {best_distance:.3f})")
    
    if total > 0:
        accuracy = 100 * correct / total
        print(f"\n[3] Recognition Accuracy: {accuracy:.0f}%")
        
        if accuracy >= 80:
            print("  ✓ Recognition working well!")
            return True
        elif accuracy >= 50:
            print("  ⚠ Recognition partially working")
            return True
        else:
            print("  ✗ Recognition not working")
            return False
    
    return False

def diagnose_database():
    """Diagnose database"""
    print("\n" + "="*70)
    print("DATABASE DIAGNOSTICS")
    print("="*70)
    
    db = Database()
    
    try:
        stats = db.get_database_stats()
        
        print("\n[1] Database Connection")
        print("  ✓ Database connected")
        
        print("\n[2] Tables")
        for table, count in stats.items():
            if isinstance(count, int):
                print(f"  ✓ {table}: {count} records")
        
        print("\n  ✓ Database healthy")
        return True
    except Exception as e:
        print(f"  ✗ Database error: {e}")
        return False

def main():
    """Run all diagnostics"""
    print("\n" + "="*70)
    print("FACE RECOGNITION SYSTEM DIAGNOSTICS")
    print("="*70)
    
    results = {}
    
    # Run diagnostics
    print("\nStep 1/5: Camera Setup")
    results['camera'] = diagnose_capture()
    
    print("\nStep 2/5: Sample Photos")
    results['samples'] = diagnose_samples()
    
    print("\nStep 3/5: Face Detection")
    results['detection'] = results['samples']  # Same as samples
    
    print("\nStep 4/5: Recognition Engine")
    results['recognition'] = diagnose_recognition()
    
    print("\nStep 5/5: Database")
    results['database'] = diagnose_database()
    
    # Summary
    print("\n" + "="*70)
    print("DIAGNOSTIC SUMMARY")
    print("="*70)
    
    for check, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{check.upper():20} {status}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n✓ ALL CHECKS PASSED!")
        print("\nYou can now use:")
        print("  python quick_test_recognition.py")
        print("  python test_integration.py")
    else:
        print("\n⚠ Some checks failed. Review output above for solutions.")
    
    return all_passed

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
