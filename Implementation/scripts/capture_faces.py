"""
Face Capture Utility — capture registration photos from webcam.

Features:
  - Live quality score overlay (size / blur / brightness) so you only
    save frames that will actually pass the quality gate at registration.
  - Auto-capture mode: takes a photo every N seconds automatically so
    you can move your head naturally instead of pressing SPACE repeatedly.
  - Angle prompts guide you through frontal, left, right, up, down poses
    to give the recognition engine varied coverage.
  - All paths are absolute so the script works from any working directory.

Usage:
  python scripts/capture_faces.py --name john_doe
  python scripts/capture_faces.py --name john_doe --count 20 --auto 2.0
  python scripts/capture_faces.py --name john_doe --count 20  # manual SPACE
"""
import sys
import argparse
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import cv2
import os
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

# Pose prompts shown sequentially so captures cover varied head angles
POSE_PROMPTS = [
    "Look straight at camera",
    "Turn slightly LEFT",
    "Turn slightly RIGHT",
    "Tilt head slightly UP",
    "Tilt head slightly DOWN",
    "Look straight — neutral expression",
    "Look straight — slight smile",
]


def _quality_color(passed: bool) -> tuple:
    return (0, 220, 0) if passed else (0, 60, 220)


def capture_face_images(person_name: str, num_photos: int = 20,
                        auto_interval: float = 0.0,
                        camera_index: int = 0) -> bool:
    """
    Capture face images from webcam with live quality feedback.

    Args:
        person_name:   Folder name under data/samples/ (e.g. 'john_doe')
        num_photos:    Target number of good-quality photos to capture
        auto_interval: If > 0, auto-capture every this many seconds.
                       If 0, manual SPACE-bar capture.

    Returns:
        True if at least one photo was saved.
    """
    save_dir = BASE_DIR / 'data' / 'samples' / person_name
    save_dir.mkdir(parents=True, exist_ok=True)

    # Determine next available index so we never overwrite existing photos
    existing = list(save_dir.glob('*.jpg'))
    next_idx = max((int(p.stem.split('_')[-1]) for p in existing
                    if p.stem.split('_')[-1].isdigit()), default=0) + 1

    print("Loading face detection engine...", end=" ", flush=True)
    engine = FacialRecognitionEngine()
    print("OK")

    print(f"Opening camera {camera_index}...", end=" ", flush=True)
    cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
    if not cap.isOpened():
        cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        print(f"\n[ERROR] Camera {camera_index} not found. Make sure it is connected and not in use.")
        return False
    print("OK")

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    mode = f"AUTO every {auto_interval}s" if auto_interval > 0 else "MANUAL (SPACE)"
    print(f"\n{'='*65}")
    print(f"CAPTURING FACES FOR: {person_name}")
    print(f"  Target : {num_photos} photos    Mode: {mode}")
    print(f"  Save to: {save_dir}")
    print(f"  Controls: SPACE = capture  |  Q / ESC = quit")
    print(f"{'='*65}\n")

    captured = 0
    last_auto_time = time.time()

    while captured < num_photos:
        ret, frame = cap.read()
        if not ret:
            print("[ERROR] Failed to read from webcam.")
            break

        display = frame.copy()
        fh, fw = display.shape[:2]

        faces = engine.detect_faces(frame)
        face_present = len(faces) > 0
        quality = {"passed": False, "reason": "No face detected",
                   "size_ok": False, "blur_ok": False, "brightness_ok": False}
        face_rect = None

        if face_present:
            x, y, w, h = (int(v) for v in faces[0])
            face_rect = (x, y, w, h)
            face_roi = frame[y:y+h, x:x+w]
            quality = engine._score_face_quality(face_roi)

            box_color = _quality_color(quality["passed"])
            cv2.rectangle(display, (x, y), (x+w, y+h), box_color, 2)

            # Quality sub-scores under the face box
            checks = [
                ("Size",       quality["size_ok"]),
                ("Sharp",      quality["blur_ok"]),
                ("Lighting",   quality["brightness_ok"]),
            ]
            for i, (label, ok) in enumerate(checks):
                sym = "OK" if ok else "--"
                col = _quality_color(ok)
                cv2.putText(display, f"{label}: {sym}", (x, y + h + 18 + i * 18),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.48, col, 1)

        # ── Header bar ────────────────────────────────────────────────────────
        cv2.rectangle(display, (0, 0), (fw, 44), (30, 30, 30), -1)
        cv2.putText(display, f"Captured: {captured}/{num_photos}",
                    (10, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 255, 255), 2)

        status_text = "READY — press SPACE" if quality["passed"] else quality["reason"]
        status_col = _quality_color(quality["passed"])
        cv2.putText(display, status_text, (220, 28),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, status_col, 1)

        # ── Pose prompt ───────────────────────────────────────────────────────
        prompt = POSE_PROMPTS[captured % len(POSE_PROMPTS)]
        cv2.rectangle(display, (0, fh - 36), (fw, fh), (30, 30, 30), -1)
        cv2.putText(display, f"Pose: {prompt}", (10, fh - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.58, (200, 200, 255), 1)

        # ── Auto-capture countdown ────────────────────────────────────────────
        if auto_interval > 0 and quality["passed"]:
            elapsed = time.time() - last_auto_time
            remaining = max(0.0, auto_interval - elapsed)
            cv2.putText(display, f"Auto in {remaining:.1f}s",
                        (fw - 170, 28), cv2.FONT_HERSHEY_SIMPLEX,
                        0.6, (100, 220, 255), 1)

        cv2.imshow(f"Face Capture — {person_name}", display)

        # ── Capture logic ─────────────────────────────────────────────────────
        do_capture = False
        key = cv2.waitKey(1) & 0xFF

        if key in (ord('q'), ord('Q'), 27):
            break

        if key == ord(' ') and quality["passed"]:
            do_capture = True

        if auto_interval > 0 and quality["passed"]:
            if (time.time() - last_auto_time) >= auto_interval:
                do_capture = True

        if do_capture and face_rect is not None:
            filename = save_dir / f"{person_name}_{next_idx}.jpg"
            # Save the full frame, not the face crop.
            # register_faces.py re-runs detect_faces() on the saved image, and
            # Haar cascade needs context (forehead, chin) around the face to work —
            # it fails on tight face crops.
            cv2.imwrite(str(filename), frame)
            print(f"  [OK] {filename.name}  (pose: {prompt})")
            captured += 1
            next_idx += 1
            last_auto_time = time.time()

            # Flash green border to confirm capture
            flash = display.copy()
            cv2.rectangle(flash, (0, 0), (fw, fh), (0, 255, 0), 6)
            cv2.imshow(f"Face Capture — {person_name}", flash)
            cv2.waitKey(120)

    cap.release()
    cv2.destroyAllWindows()

    print(f"\n{'='*65}")
    if captured > 0:
        print(f"[OK] Saved {captured} photo(s) to {save_dir}/")
        print(f"\nNext step — register in the system:")
        print(f"  python scripts/register_faces.py")
    else:
        print(f"[FAIL] No photos captured.")
    print(f"{'='*65}")
    return captured > 0


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
        
        # Extract real face encodings from captured photos
        photo_dir = Path(f'data/samples/{person_name}')
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
            print(f"     Check photo quality and try recapturing.")
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
