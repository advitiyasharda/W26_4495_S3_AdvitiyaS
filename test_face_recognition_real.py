"""
Test Face Recognition with Real Detection and Matching
"""
import cv2
from pathlib import Path
from api.facial_recognition import FacialRecognitionEngine
from data.database import Database

def test_recognition_with_webcam():
    """Test face recognition in real-time with webcam"""
    print("\n" + "=" * 70)
    print("FACE RECOGNITION TEST - LIVE WEBCAM")
    print("=" * 70)
    
    engine = FacialRecognitionEngine()
    db = Database()
    
    # Load registered faces from database
    print("\nLoading registered people...")
    users = db.get_database_stats()
    print(f"  Registered persons: {users['total_persons']}")
    
    # Load face encodings from registered people
    # In a real system, we'd query the database
    sample_dir = Path('data/samples')
    registered_people = []
    
    if sample_dir.exists():
        for person_dir in sample_dir.iterdir():
            if person_dir.is_dir():
                person_name = person_dir.name
                photos = list(person_dir.glob('*.jpg')) + list(person_dir.glob('*.png'))
                
                if photos:
                    print(f"\n  Loading {person_name} ({len(photos)} photos)...")
                    
                    for photo_path in photos:
                        try:
                            frame = cv2.imread(str(photo_path))
                            if frame is None:
                                continue
                            
                            faces = engine.detect_faces(frame)
                            if len(faces) > 0:
                                (x, y, w, h) = faces[0]
                                face_roi = frame[y:y+h, x:x+w]
                                encoding = engine._extract_face_features(face_roi)
                                
                                if encoding is not None:
                                    engine.register_face(person_name, person_name, encoding)
                                    registered_people.append(person_name)
                                    print(f"    ✓ Loaded {photo_path.name}")
                        except Exception as e:
                            print(f"    ✗ Error: {e}")
    
    print(f"\n✓ Loaded {len(engine.known_faces)} registered people")
    
    # Test with webcam
    print("\n" + "=" * 70)
    print("Opening webcam for recognition test...")
    print("Press Q to exit")
    print("=" * 70 + "\n")
    
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("ERROR: Webcam not found!")
        return
    
    frame_count = 0
    recognized_count = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        frame_count += 1
        
        # Detect faces
        faces = engine.detect_faces(frame)
        
        # Process each detected face
        for (x, y, w, h) in faces:
            # Recognize face
            result = engine.recognize_face(frame, (x, y, w, h))
            
            # Draw rectangle
            if result['person_id']:
                # Known person
                color = (0, 255, 0)  # Green
                recognized_count += 1
                label = f"{result['name']} ({result['confidence']:.2f})"
            else:
                # Unknown person
                color = (0, 0, 255)  # Red
                label = f"Unknown ({result['confidence']:.2f})"
            
            cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
            cv2.putText(frame, label, (x, y-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        
        # Show statistics
        cv2.putText(frame, f'Frames: {frame_count} | Recognized: {recognized_count}',
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Show registered people
        cv2.putText(frame, f'Registered: {len(engine.known_faces)}',
                   (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        cv2.imshow('Face Recognition Test', frame)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()
    
    # Summary
    print("\n" + "=" * 70)
    print("RECOGNITION TEST SUMMARY")
    print("=" * 70)
    print(f"Total frames processed: {frame_count}")
    print(f"Faces recognized: {recognized_count}")
    if frame_count > 0:
        print(f"Recognition rate: {100*recognized_count/frame_count:.1f}%")
    print(f"Registered people: {len(engine.known_faces)}")

def test_recognition_with_photos():
    """Test recognition on stored sample photos"""
    print("\n" + "=" * 70)
    print("FACE RECOGNITION TEST - STORED PHOTOS")
    print("=" * 70)
    
    engine = FacialRecognitionEngine()
    sample_dir = Path('data/samples')
    
    if not sample_dir.exists():
        print("No sample photos found")
        print("Run: python capture_faces.py")
        return
    
    # Load registered people
    print("\nLoading registered people...")
    all_encodings = {}
    
    for person_dir in sample_dir.iterdir():
        if person_dir.is_dir():
            person_name = person_dir.name
            photos = list(person_dir.glob('*.jpg')) + list(person_dir.glob('*.png'))
            
            if photos:
                all_encodings[person_name] = []
                
                for photo_path in photos:
                    try:
                        frame = cv2.imread(str(photo_path))
                        if frame is None:
                            continue
                        
                        faces = engine.detect_faces(frame)
                        if len(faces) > 0:
                            (x, y, w, h) = faces[0]
                            face_roi = frame[y:y+h, x:x+w]
                            encoding = engine._extract_face_features(face_roi)
                            
                            if encoding is not None:
                                all_encodings[person_name].append(encoding)
                                engine.register_face(person_name, person_name, encoding)
                    except Exception as e:
                        print(f"Error: {e}")
    
    print(f"✓ Loaded {len(engine.known_faces)} registered people\n")
    
    # Test recognition on photos
    print("Testing recognition on sample photos...\n")
    
    total_tests = 0
    correct = 0
    
    for person_dir in sample_dir.iterdir():
        if not person_dir.is_dir():
            continue
        
        person_name = person_dir.name
        photos = list(person_dir.glob('*.jpg')) + list(person_dir.glob('*.png'))
        
        if not photos:
            continue
        
        print(f"{person_name}:")
        
        for photo_path in photos:
            try:
                frame = cv2.imread(str(photo_path))
                if frame is None:
                    continue
                
                faces = engine.detect_faces(frame)
                if len(faces) > 0:
                    (x, y, w, h) = faces[0]
                    result = engine.recognize_face(frame, (x, y, w, h))
                    
                    total_tests += 1
                    is_correct = result['person_id'] == person_name
                    
                    if is_correct:
                        correct += 1
                        status = "✓"
                    else:
                        status = "✗"
                    
                    print(f"  {status} {photo_path.name}: {result['name']} ({result['confidence']:.2f})")
            except Exception as e:
                print(f"  Error: {e}")
    
    # Summary
    print("\n" + "=" * 70)
    print("RECOGNITION RESULTS")
    print("=" * 70)
    print(f"Total tests: {total_tests}")
    print(f"Correct: {correct}")
    if total_tests > 0:
        accuracy = 100 * correct / total_tests
        print(f"Accuracy: {accuracy:.1f}%")

if __name__ == '__main__':
    print("\nFace Recognition Testing Options:")
    print("1. Test with live webcam")
    print("2. Test with stored sample photos")
    
    choice = input("\nSelect option (1-2): ").strip()
    
    if choice == '1':
        test_recognition_with_webcam()
    elif choice == '2':
        test_recognition_with_photos()
    else:
        print("Invalid option")
