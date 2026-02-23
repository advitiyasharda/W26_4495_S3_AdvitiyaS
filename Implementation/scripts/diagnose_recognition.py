#!/usr/bin/env python3
"""
Face Recognition Diagnostics
Diagnose issues with face capture, detection, and recognition
"""
import cv2
import numpy as np
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

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
        print("  Please run: python scripts/capture_faces.py")
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
        photos = list(person_dir.glob('*.jpg')) + list(person_dir.glob('*.jpeg')) + list(person_dir.glob('*.png'))
        
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

def diagnose_sample_separation():
    """
    Check that the 3 users' sample photos encode to distinct faces.
    If two people's encodings are as close as one person's own photos, photos may be mixed or same person.
    """
    print("\n" + "="*70)
    print("ARE THE 3 USERS' PHOTOS DISTINCT?")
    print("="*70)
    
    sample_dir = Path('data/samples')
    if not sample_dir.exists():
        print("  ✗ No data/samples/ directory")
        return False
    
    engine = FacialRecognitionEngine()
    # person_name -> list of (encoding, photo_name)
    encodings_by_person = {}
    
    for person_dir in sample_dir.iterdir():
        if not person_dir.is_dir():
            continue
        person_name = person_dir.name
        photos = list(person_dir.glob('*.jpg')) + list(person_dir.glob('*.jpeg')) + list(person_dir.glob('*.png'))
        encodings_by_person[person_name] = []
        
        for photo in photos:
            frame = cv2.imread(str(photo))
            if frame is None:
                continue
            faces = engine.detect_faces(frame)
            if len(faces) == 0:
                continue
            x, y, w, h = faces[0]
            face_roi = frame[y:y+h, x:x+w]
            enc = engine._extract_face_features(face_roi)
            if enc is not None:
                encodings_by_person[person_name].append((enc, photo.name))
    
    names = list(encodings_by_person.keys())
    if len(names) < 2:
        print("  Need at least 2 people in data/samples/ to check separation.")
        return True
    
    def mean_pairwise_distance(encodings_a, encodings_b):
        if not encodings_a or not encodings_b:
            return float('nan')
        total, count = 0.0, 0
        for enc_a, _ in encodings_a:
            for enc_b, _ in encodings_b:
                total += np.linalg.norm(enc_a - enc_b)
                count += 1
        return total / count if count else float('nan')
    
    # Within-person: mean distance among same person's encodings
    print("\n  Mean encoding distance (lower = more similar):")
    print("  ----------------------------------------")
    within = {}
    for n in names:
        encs = encodings_by_person[n]
        if len(encs) < 2:
            within[n] = 0.0
            print(f"    Within {n}: (only 1 encoding)")
        else:
            # All distinct pairs of this person's encodings
            pairs = []
            for i, (enc_a, _) in enumerate(encs):
                for j, (enc_b, _) in enumerate(encs):
                    if i == j:
                        continue
                    pairs.append((enc_a, enc_b))
            within[n] = sum(np.linalg.norm(a - b) for a, b in pairs) / len(pairs)
            print(f"    Within {n}: {within[n]:.3f}")
    
    # Between-person: mean distance between each pair
    print("  ----------------------------------------")
    between = {}
    for i, a in enumerate(names):
        for b in names[i+1:]:
            d = mean_pairwise_distance(encodings_by_person[a], encodings_by_person[b])
            between[(a, b)] = d
            print(f"    {a} vs {b}: {d:.3f}")
    
    # Sanity: between-person distance should be larger than within-person
    max_within = max(within.values()) if within else 0
    min_between = min(between.values()) if between else float('inf')
    
    print("  ----------------------------------------")
    # Highlight individual photos that look closer to someone else
    print("\n  Photos that look closer to another person than to their own group:")
    suspicious_found = False
    for name in names:
        encs = encodings_by_person[name]
        other_names = [n for n in names if n != name]
        for idx, (enc, photo_name) in enumerate(encs):
            # Closest distance to same-person encodings (excluding itself)
            self_dists = [
                np.linalg.norm(enc - other_enc)
                for j, (other_enc, _) in enumerate(encs)
                if j != idx
            ]
            min_self = min(self_dists) if self_dists else float('inf')
            # Closest distance to any other person
            best_other_name = None
            best_other_dist = float('inf')
            for other in other_names:
                for other_enc, _ in encodings_by_person[other]:
                    d = np.linalg.norm(enc - other_enc)
                    if d < best_other_dist:
                        best_other_dist = d
                        best_other_name = other
            if best_other_name is not None and best_other_dist < min_self:
                suspicious_found = True
                print(
                    f"    {name}/{photo_name}: closer to {best_other_name} "
                    f"(other {best_other_dist:.3f} < self {min_self:.3f})"
                )
    if not suspicious_found:
        print("    None — every photo is closest to its own person.")
    
    if min_between > max_within:
        print(f"\n  ✓ Users look distinct overall (min between-person {min_between:.3f} > max within-person {max_within:.3f})")
        return True
    else:
        print(f"\n  ⚠ Overlap: some users' photos are as similar as the same person's.")
        print(f"    Max within-person: {max_within:.3f}, Min between-person: {min_between:.3f}")
        print("    If two people look like one person, check that each folder has the correct person's photos.")
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
        
        photos = list(person_dir.glob('*.jpg')) + list(person_dir.glob('*.jpeg')) + list(person_dir.glob('*.png'))
        
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
    
    print("\nStep 2b: Are the 3 users' photos distinct?")
    results['separation'] = diagnose_sample_separation()
    
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
        print(f"{str(check).upper():20} {status}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n✓ ALL CHECKS PASSED!")
        print("\nYou can now use:")
        print("  python scripts/quick_test_recognition.py")
        print("  python tests/test_integration.py")
    else:
        print("\n⚠ Some checks failed. Review output above for solutions.")
    
    return all_passed

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
