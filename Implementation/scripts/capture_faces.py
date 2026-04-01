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
import numpy as np
from api.facial_recognition import FacialRecognitionEngine

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
                        auto_interval: float = 0.0) -> bool:
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

    engine = FacialRecognitionEngine()

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[ERROR] Webcam not found. Make sure it is connected and not in use.")
        return False

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
            x, y, w, h = face_rect
            face_roi = frame[y:y+h, x:x+w]
            filename = save_dir / f"{person_name}_{next_idx}.jpg"
            cv2.imwrite(str(filename), face_roi)
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
    parser = argparse.ArgumentParser(
        description="Capture registration photos for face recognition"
    )
    parser.add_argument("--name",  required=True,
                        help="Folder name for this person, e.g. 'john_doe'")
    parser.add_argument("--count", type=int, default=20,
                        help="Number of photos to capture (default: 20)")
    parser.add_argument("--auto",  type=float, default=0.0,
                        help="Auto-capture interval in seconds (0 = manual SPACE, "
                             "e.g. --auto 2.0 captures every 2 seconds)")
    args = parser.parse_args()

    if args.count < 1:
        print("ERROR: --count must be at least 1")
        sys.exit(1)
    if args.count > 100:
        print("WARNING: capping at 100 photos")
        args.count = 100

    capture_face_images(args.name, args.count, args.auto)


if __name__ == '__main__':
    main()
