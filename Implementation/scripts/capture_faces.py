"""
Face Capture Utility - Capture face images from webcam
Stores images in data/samples/{person_name}/ for use in training

Run from project root: python scripts/capture_faces.py
"""
import sys
import os
from pathlib import Path

# Keep AVFoundation enabled on macOS for reliable webcam access.
if sys.platform == "darwin":
    os.environ.setdefault("OPENCV_VIDEOIO_PRIORITY_AVFOUNDATION", "1000")

SCRIPT_DIR = Path(__file__).resolve().parent        # .../Implementation/scripts
PROJECT_DIR = SCRIPT_DIR.parent                     # .../Implementation
SAMPLES_DIR = PROJECT_DIR / "data" / "samples"

sys.path.insert(0, str(PROJECT_DIR))

import cv2
import argparse


def _reload_backend_recognizer(api_url: str) -> bool:
    """Reload backend in-memory face encodings after registration."""
    base = (api_url or "").strip().rstrip("/")
    if not base:
        return False
    try:
        import requests
    except Exception:
        print("  [WARN] requests not installed; skipping backend recognizer reload")
        return False

    try:
        resp = requests.post(f"{base}/api/recognition/reload", timeout=10)
        if not resp.ok:
            print(f"  [WARN] Backend reload failed ({resp.status_code}): {resp.text[:160]}")
            return False
        payload = resp.json() if resp.content else {}
        print(f"  [OK] Backend recognizer reloaded ({payload.get('loaded_encodings', 'unknown')} encodings)")
        return True
    except Exception as e:
        print(f"  [WARN] Could not reload backend recognizer: {e}")
        return False

def capture_face_images(person_name, num_photos=10):
    """
    Capture face images from webcam for a specific person
    
    Args:
        person_name: Name of the person to capture photos for
        num_photos: Number of photos to capture
    """
    # Create directory (use absolute path so script works from any CWD)
    save_dir = SAMPLES_DIR / person_name
    save_dir.mkdir(parents=True, exist_ok=True)
    
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
                
                filename = save_dir / f'{person_name}_{captured+1}.jpg'
                cv2.imwrite(str(filename), face_roi)
                print(f"  [OK] Photo {captured+1}/{num_photos} saved: {filename}")
                captured += 1
            else:
                print("  [FAIL] No face detected! Please position your face in the frame.")
        elif key == ord('q') or key == ord('Q'):  # Q
            break
    
    cap.release()
    cv2.destroyAllWindows()
    
    print("\n" + "=" * 60)
    if captured > 0:
        print(f"[OK] SUCCESS: Captured {captured}/{num_photos} photos")
        print(f"[OK] Saved to: {save_dir}")
        print("\nNext steps:")
        print("  1. python scripts/register_faces.py  (Register in system)")
        print("  2. python scripts/test_facial_recognition.py  (Test detection)")
        print("=" * 60)
        return True
    else:
        print("[FAIL] FAILED: No photos captured")
        print("=" * 60)
        return False

def main():
    """Main function"""
    print("\n" + "=" * 60)
    print("DOOR FACE PANELS - FACE CAPTURE UTILITY")
    print("=" * 60)

    parser = argparse.ArgumentParser(description="Capture face photos from webcam")
    parser.add_argument("--person", type=str, default=None, help="Person folder name (e.g. john_doe)")
    parser.add_argument("--photos", type=int, default=None, help="Number of photos to capture")
    parser.add_argument("--register-now", action="store_true", help="Register captured photos in DB immediately")
    parser.add_argument("--person-id", type=str, default=None, help="Person ID for DB registration")
    parser.add_argument("--display-name", type=str, default=None, help="Display name for DB registration")
    parser.add_argument("--role", type=str, default=None, help="Role for DB registration (resident/caregiver)")
    parser.add_argument("--reload-api-url", type=str, default=None, help="Backend API base URL for face reload")
    args = parser.parse_args()

    # Get input from user (or CLI args for non-interactive launchers)
    try:
        person_name = (args.person or "").strip()
        if not person_name:
            person_name = input("\nEnter person name (e.g., 'john_doe'): ").strip()
        if not person_name:
            print("ERROR: Name cannot be empty")
            return

        if args.photos is not None:
            num_photos = int(args.photos)
            print(f"Using --photos={num_photos}")
        else:
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
            if args.register_now:
                register_now = "y"
            elif args.person is not None:
                # Non-interactive run from launcher defaults to no immediate DB registration.
                register_now = "n"
            else:
                register_now = input("\nRegister these photos in the system now? (y/n): ").strip().lower()
            if register_now == 'y':
                register_captured_person(
                    person_name,
                    person_id=args.person_id,
                    role=args.role,
                    display_name=args.display_name,
                    reload_api_url=args.reload_api_url,
                )
    
    except ValueError:
        print("ERROR: Invalid number entered")
    except KeyboardInterrupt:
        print("\n\nCapture cancelled by user")
    except Exception as e:
        print(f"ERROR: {e}")

def register_captured_person(person_name, person_id=None, role=None, display_name=None, reload_api_url=None):
    """Register the captured person in the system"""
    from data.database import Database
    from api.facial_recognition import FacialRecognitionEngine

    print("\n" + "=" * 60)
    print("REGISTERING IN SYSTEM")
    print("=" * 60)
    
    try:
        # Get person details
        if not person_id:
            person_id = input(f"\nEnter person ID (e.g., 'resident_001'): ").strip()
        role = (role or "").strip().lower()
        if not role:
            role = input("Enter role (resident/caregiver): ").strip().lower()
        display_name = (display_name or "").strip() or person_name.replace('_', ' ').title()
        
        if role not in ['resident', 'caregiver']:
            role = 'resident'
        
        # Register in database
        db = Database()
        engine = FacialRecognitionEngine()
        
        if not db.add_user(person_id, display_name, role, display_id=person_id):
            print(f"  [FAIL] Could not add to database (database may be locked).")
            print(f"     Stop the Flask server (Ctrl+C in its terminal) and run:")
            print(f"     python3 scripts/register_faces.py  → option 2 to register from photos")
            return
        
        print(f"  [OK] Added to database")
        
        # Extract real face encodings from captured photos (absolute path)
        photo_dir = SAMPLES_DIR / person_name
        photos = list(photo_dir.glob('*.jpg')) + list(photo_dir.glob('*.png'))
        encodings_registered = 0
        
        for photo_path in photos:
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
                engine.register_face(person_id, display_name, encoding)
                encodings_registered += 1
        
        if encodings_registered == 0:
            print(f"  [FAIL] Could not extract face encodings from photos in {photo_dir}")
            print("     Check photo quality and try recapturing.")
            return
        
        print(f"  [OK] Registered {encodings_registered} face encoding(s) in engine")
        
        print("\n" + "=" * 60)
        print("[OK] REGISTRATION COMPLETE")
        print("=" * 60)
        print(f"  Person ID: {person_id}")
        print(f"  Name: {display_name}")
        print(f"  Role: {role}")
        print(f"  Encodings: {encodings_registered}/{len(photos)} photos")
        _reload_backend_recognizer(reload_api_url)
        
    except Exception as e:
        print(f"ERROR during registration: {e}")

if __name__ == '__main__':
    main()
