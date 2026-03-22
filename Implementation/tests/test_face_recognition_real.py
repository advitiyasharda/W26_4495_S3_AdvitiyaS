"""
Face Recognition — Real Detection and Matching Tests

Loads registered faces from data/samples/, resolves each folder to its
real person_id from the database (so results align with the live system),
and runs either a live webcam test or a photo accuracy test.

Run from project root:
    python tests/test_face_recognition_real.py            # live webcam
    python tests/test_face_recognition_real.py --photos   # photo accuracy
    python tests/test_face_recognition_real.py --both     # both
"""
import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import cv2
from api.facial_recognition import FacialRecognitionEngine
from data.database import Database

SAMPLE_DIR = Path(__file__).resolve().parent.parent / "data" / "samples"


# ── Helpers ──────────────────────────────────────────────────────────────────

def _folder_to_display_name(folder_name: str) -> str:
    """Convert a folder name like 'john_doe' → 'John Doe' for DB lookup."""
    return folder_name.replace("_", " ").title()


def _resolve_person_id(db: Database, folder_name: str) -> tuple:
    """
    Find the DB person_id and display name for a samples folder.

    Tries three strategies in order:
      1. Exact folder name match against DB user_id
      2. Folder name → 'Title Case' match against DB name field
      3. Case-insensitive partial match against DB name field

    Returns (person_id, display_name).  If no DB record is found,
    falls back to (folder_name, folder_name) with a warning so the
    test still runs but results won't align with the live API.
    """
    try:
        all_users = db.get_users() or []
    except Exception:
        all_users = []

    # Strategy 1: folder name == user_id exactly
    for u in all_users:
        if u.get("user_id") == folder_name:
            return u["user_id"], u.get("name", folder_name)

    # Strategy 2: title-cased folder name matches DB name
    display = _folder_to_display_name(folder_name)
    for u in all_users:
        if u.get("name", "").strip().lower() == display.lower():
            return u["user_id"], u.get("name", display)

    # Strategy 3: folder name is a substring of the DB name (or vice versa)
    for u in all_users:
        db_name = u.get("name", "").lower()
        if folder_name.lower() in db_name or db_name in folder_name.lower():
            return u["user_id"], u.get("name", folder_name)

    print(f"  [WARN] No DB record found for folder '{folder_name}'. "
          f"Using folder name as ID — results won't match the live API.")
    return folder_name, display


def _load_encodings(engine: FacialRecognitionEngine, db: Database) -> dict:
    """
    Load face encodings from data/samples/ into the engine.

    Each folder is resolved to its real DB person_id so recognition
    results use the same IDs as the live /api/recognize endpoint.
    Photos that fail quality scoring are skipped with a warning.

    Returns a mapping of {person_id: display_name} for summary display.
    """
    if not SAMPLE_DIR.exists():
        print(f"  [WARN] Samples directory not found: {SAMPLE_DIR}")
        print("         Register faces first: python scripts/capture_faces.py")
        return {}

    loaded = {}

    for person_dir in sorted(SAMPLE_DIR.iterdir()):
        if not person_dir.is_dir():
            continue

        folder_name = person_dir.name
        person_id, display_name = _resolve_person_id(db, folder_name)

        photos = list(person_dir.glob("*.jpg")) + list(person_dir.glob("*.png"))
        if not photos:
            continue

        print(f"\n  Loading '{display_name}'  (id={person_id}, {len(photos)} photos)")

        encodings_ok = 0
        quality_skipped = 0

        for photo_path in sorted(photos):
            frame = cv2.imread(str(photo_path))
            if frame is None:
                print(f"    [SKIP] {photo_path.name} — could not read file")
                continue

            faces = engine.detect_faces(frame)
            if not faces:
                print(f"    [SKIP] {photo_path.name} — no face detected")
                continue

            x, y, w, h = (int(v) for v in faces[0])
            face_roi = frame[y:y+h, x:x+w]

            quality = engine._score_face_quality(face_roi)
            if not quality["passed"]:
                print(f"    [SKIP] {photo_path.name} — {quality['reason']}")
                quality_skipped += 1
                continue

            encoding = engine._extract_face_features(face_roi)
            if encoding is not None:
                engine.register_face(person_id, display_name, encoding)
                encodings_ok += 1

        status = f"{encodings_ok} loaded"
        if quality_skipped:
            status += f", {quality_skipped} skipped (quality)"
        print(f"    → {status}")

        if encodings_ok > 0:
            loaded[person_id] = display_name

    return loaded


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_recognition_with_webcam():
    """Live webcam test — draws recognition result on each frame."""
    print("\n" + "=" * 70)
    print("FACE RECOGNITION TEST — LIVE WEBCAM")
    print("=" * 70)

    engine = FacialRecognitionEngine()
    db     = Database()

    print("\nLoading registered people from data/samples/...")
    loaded = _load_encodings(engine, db)

    if not loaded:
        print("\n[ERROR] No faces loaded. Cannot run webcam test.")
        return

    print(f"\n[OK] {len(loaded)} person(s) loaded: {', '.join(loaded.values())}")

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("\n[ERROR] Webcam not found.")
        return

    print("\nWebcam open. Press Q or ESC to quit (click the window first).\n")

    frame_count  = 0
    granted_count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1
        faces = engine.detect_faces(frame)

        for face_coords in faces:
            x, y, w, h = (int(v) for v in face_coords)
            result = engine.recognize_face(frame, (x, y, w, h))

            if result and result.get("person_id"):
                color = (0, 255, 0)
                label = f"{result['name']} ({result['confidence']:.2f})"
                granted_count += 1
            else:
                color = (0, 0, 255)
                conf  = result.get("confidence", 0.0) if result else 0.0
                label = f"Unknown ({conf:.2f})"

            cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
            cv2.putText(frame, label, (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

        fh, fw = frame.shape[:2]
        cv2.putText(frame, f"Frames: {frame_count}  Granted: {granted_count}",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)
        cv2.putText(frame, f"Registered: {len(loaded)}  |  Q / ESC to quit",
                    (10, fh - 12), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 180, 180), 1)

        cv2.imshow("Face Recognition — Webcam Test", frame)

        key = cv2.waitKey(1) & 0xFF
        if key in (ord("q"), ord("Q"), 27):
            break

    cap.release()
    cv2.destroyAllWindows()

    print("\n" + "=" * 70)
    print("WEBCAM TEST SUMMARY")
    print("=" * 70)
    print(f"  Frames processed : {frame_count}")
    print(f"  Faces granted    : {granted_count}")
    if frame_count:
        print(f"  Grant rate       : {100 * granted_count / frame_count:.1f}%")
    print(f"  Registered people: {len(loaded)}")


def test_recognition_with_photos():
    """
    Photo accuracy test — registers all sample photos then tests each
    photo against the loaded encodings and reports per-person accuracy.
    """
    print("\n" + "=" * 70)
    print("FACE RECOGNITION TEST — PHOTO ACCURACY")
    print("=" * 70)

    engine = FacialRecognitionEngine()
    db     = Database()

    print("\nLoading registered people from data/samples/...")
    loaded = _load_encodings(engine, db)

    if not loaded:
        print("\n[ERROR] No faces loaded. Cannot run photo test.")
        return

    print(f"\n[OK] {len(loaded)} person(s) loaded. Testing accuracy...\n")

    total  = 0
    correct = 0

    for person_dir in sorted(SAMPLE_DIR.iterdir()):
        if not person_dir.is_dir():
            continue

        folder_name = person_dir.name
        person_id, display_name = _resolve_person_id(db, folder_name)

        photos = list(person_dir.glob("*.jpg")) + list(person_dir.glob("*.png"))
        if not photos:
            continue

        print(f"{display_name}  (id={person_id})")

        for photo_path in sorted(photos):
            frame = cv2.imread(str(photo_path))
            if frame is None:
                continue

            faces = engine.detect_faces(frame)
            if not faces:
                print(f"  [SKIP] {photo_path.name} — no face detected")
                continue

            x, y, w, h = (int(v) for v in faces[0])
            result = engine.recognize_face(frame, (x, y, w, h))

            total += 1
            predicted_id = result.get("person_id") if result else None
            is_correct   = predicted_id == person_id
            if is_correct:
                correct += 1

            status = "[OK]  " if is_correct else "[FAIL]"
            name   = result.get("name", "Unknown") if result else "Unknown"
            conf   = result.get("confidence", 0.0) if result else 0.0
            print(f"  {status} {photo_path.name}: predicted='{name}'  conf={conf:.2f}")

        print()

    print("=" * 70)
    print("PHOTO ACCURACY SUMMARY")
    print("=" * 70)
    print(f"  Total tests : {total}")
    print(f"  Correct     : {correct}")
    if total:
        print(f"  Accuracy    : {100 * correct / total:.1f}%")


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Test facial recognition with real webcam or sample photos"
    )
    parser.add_argument("--photos",     action="store_true",
                        help="Run photo accuracy test only")
    parser.add_argument("--both",       action="store_true",
                        help="Run photo accuracy test then webcam test")
    args = parser.parse_args()

    if args.photos:
        test_recognition_with_photos()
    elif args.both:
        test_recognition_with_photos()
        test_recognition_with_webcam()
    else:
        # Default: live webcam
        test_recognition_with_webcam()
