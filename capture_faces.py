"""
Face Capture Utility - Capture face images from webcam
Stores images in data/samples/{person_name}/ for use in training
"""
import cv2
import os
from pathlib import Path

def capture_face_images(person_name, num_photos=10):
    """
    Capture face images from webcam for a specific person
    
    Args:
        person_name: Name of the person to capture photos for
        num_photos: Number of photos to capture
    """
    # Create directory
    save_dir = f'data/samples/{person_name}'
    Path(save_dir).mkdir(parents=True, exist_ok=True)
    
    print("\n" + "=" * 60)
    print(f"CAPTURING FACE IMAGES FOR: {person_name}")
    print("=" * 60)
    
    print(f"\nCapturing {num_photos} photos")
    print("Controls:")
    print("  SPACE - Capture current frame")
    print("  Q     - Finish capturing")
    print("\nTips:")
    print("  - Keep face centered and clear")
    print("  - Move head slightly for each photo")
    print("  - Try different angles (frontal, slight left/right)")
    print("  - Good lighting is important\n")
    
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("ERROR: Webcam not found!")
        print("Make sure webcam is connected and not in use")
        return False
    
    # Load face detector
    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
    )
    
    captured = 0
    frame_count = 0
    
    while captured < num_photos:
        ret, frame = cap.read()
        if not ret:
            print("ERROR: Failed to capture frame")
            break
        
        frame_count += 1
        
        # Detect faces
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.05, 5, minSize=(100, 100))
        
        # Draw rectangles around detected faces
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
        
        # Show status
        status_color = (0, 255, 0) if len(faces) > 0 else (0, 0, 255)
        face_status = f"Face Detected: YES ({len(faces)})" if len(faces) > 0 else "Face Detected: NO"
        
        cv2.putText(frame, f'Captured: {captured}/{num_photos}', (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(frame, face_status, (10, 70),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)
        cv2.putText(frame, 'SPACE: Capture | Q: Done', (10, 110),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        cv2.imshow(f'Face Capture - {person_name}', frame)
        
        # Key handling
        key = cv2.waitKey(1) & 0xFF
        if key == ord(' '):  # SPACE
            if len(faces) > 0:
                # Save the first detected face region
                (x, y, w, h) = faces[0]
                face_roi = frame[y:y+h, x:x+w]
                
                filename = f'{save_dir}/{person_name}_{captured+1}.jpg'
                cv2.imwrite(filename, face_roi)
                print(f"  ✓ Photo {captured+1}/{num_photos} saved: {filename}")
                captured += 1
            else:
                print("  ✗ No face detected! Please position your face in the frame.")
        elif key == ord('q') or key == ord('Q'):  # Q
            break
    
    cap.release()
    cv2.destroyAllWindows()
    
    print("\n" + "=" * 60)
    if captured > 0:
        print(f"✓ SUCCESS: Captured {captured}/{num_photos} photos")
        print(f"✓ Saved to: {save_dir}/")
        print("\nNext steps:")
        print("  1. python register_faces.py  (Register in system)")
        print("  2. python test_facial_recognition.py  (Test detection)")
        print("=" * 60)
        return True
    else:
        print("✗ FAILED: No photos captured")
        print("=" * 60)
        return False

def main():
    """Main function"""
    print("\n" + "=" * 60)
    print("DOOR FACE PANELS - FACE CAPTURE UTILITY")
    print("=" * 60)
    
    # Get input from user
    try:
        person_name = input("\nEnter person name (e.g., 'john_doe'): ").strip()
        if not person_name:
            print("ERROR: Name cannot be empty")
            return
        
        num_input = input("How many photos to capture? (10-20 recommended): ").strip()
        num_photos = int(num_input)
        
        if num_photos < 1:
            print("ERROR: Must capture at least 1 photo")
            return
        if num_photos > 100:
            print("WARNING: Capturing more than 100 photos. Using 100.")
            num_photos = 100
        
        # Capture
        success = capture_face_images(person_name, num_photos)
        
        if success:
            # Ask if user wants to register now
            register_now = input("\nRegister these photos in the system now? (y/n): ").strip().lower()
            if register_now == 'y':
                register_captured_person(person_name)
    
    except ValueError:
        print("ERROR: Invalid number entered")
    except KeyboardInterrupt:
        print("\n\nCapture cancelled by user")
    except Exception as e:
        print(f"ERROR: {e}")

def register_captured_person(person_name):
    """Register the captured person in the system"""
    from data.database import Database
    from api.facial_recognition import FacialRecognitionEngine
    import numpy as np
    
    print("\n" + "=" * 60)
    print("REGISTERING IN SYSTEM")
    print("=" * 60)
    
    try:
        # Get person details
        person_id = input(f"\nEnter person ID (e.g., 'resident_001'): ").strip()
        role = input("Enter role (resident/caregiver): ").strip().lower()
        
        if role not in ['resident', 'caregiver']:
            role = 'resident'
        
        # Register in database
        db = Database()
        engine = FacialRecognitionEngine()
        
        db.add_user(person_id, person_name.replace('_', ' ').title(), role)
        print(f"  ✓ Added to database")
        
        # Register face (dummy encoding for now)
        dummy_encoding = np.random.rand(128)
        engine.register_face(person_id, person_name, dummy_encoding)
        print(f"  ✓ Face registered in engine")
        
        print("\n" + "=" * 60)
        print("✓ REGISTRATION COMPLETE")
        print("=" * 60)
        print(f"  Person ID: {person_id}")
        print(f"  Name: {person_name.replace('_', ' ').title()}")
        print(f"  Role: {role}")
        print(f"  Photos: {len([f for f in os.listdir(f'data/samples/{person_name}') if f.endswith(('.jpg', '.jpeg', '.png'))])}")
        
    except Exception as e:
        print(f"ERROR during registration: {e}")

if __name__ == '__main__':
    main()
