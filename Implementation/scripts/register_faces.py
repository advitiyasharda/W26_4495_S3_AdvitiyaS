"""
Face Registration Utility - Register captured faces in the system
Adds people to database and facial recognition engine.
Saves encodings to models/face_encodings.npz so the Flask server
and live tests load instantly without reprocessing photos.

Run from anywhere:
  python scripts/register_faces.py             # interactive menu
  python scripts/register_faces.py --all       # auto-register every folder in data/samples/
"""
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from data.database import Database
from api.facial_recognition import FacialRecognitionEngine
import cv2

ENCODINGS_PATH = str(BASE_DIR / 'models' / 'face_encodings.npz')


class FaceRegistration:
    """Register faces in the Door Face Panels system"""
    
    def __init__(self):
        self.db = Database()
        self.engine = FacialRecognitionEngine()

    def save_encodings(self):
        """Persist all in-memory encodings to disk so other tools load instantly."""
        ok = self.engine.save_encodings(ENCODINGS_PATH)
        if ok:
            print(f"\n  [OK] Encodings saved to {ENCODINGS_PATH}")
        else:
            print(f"\n  [WARN] Could not save encodings to {ENCODINGS_PATH}")
        return ok
    
    def register_person(self, person_id, name, role='resident'):
        """
        Register a person in the system.
        Looks for captured photos in data/samples/{name}/ to extract real
        face encodings. If no photos are found, adds to the DB only and
        reminds the user to capture photos first.
        
        Args:
            person_id: Unique identifier (e.g., 'resident_001')
            name: Full name
            role: 'resident' or 'caregiver'
            
        Returns:
            True if successful
        """
        try:
            # Resolve photo directory before touching the DB (avoids ghost users)
            folder_name = name.replace(' ', '_').lower()
            photo_dir = BASE_DIR / 'data' / 'samples' / folder_name
            if not photo_dir.exists():
                photo_dir = BASE_DIR / 'data' / 'samples' / name

            encodings_to_register = []
            quality_skipped = 0

            if photo_dir.exists():
                photos = list(photo_dir.glob('*.jpg')) + list(photo_dir.glob('*.png'))
                for photo_path in photos:
                    frame = cv2.imread(str(photo_path))
                    if frame is None:
                        continue
                    faces = self.engine.detect_faces(frame)
                    if len(faces) == 0:
                        continue
                    x, y, w, h = (int(v) for v in faces[0])
                    face_roi = frame[y:y+h, x:x+w]

                    quality = self.engine._score_face_quality(face_roi)
                    if not quality["passed"]:
                        print(f"  [SKIP] {photo_path.name} — {quality['reason']}")
                        quality_skipped += 1
                        continue

                    encoding = self.engine._extract_face_features(face_roi)
                    if encoding is not None:
                        encodings_to_register.append(encoding)

                if quality_skipped:
                    print(f"  [!] {quality_skipped} photo(s) skipped (poor quality)")

                if not encodings_to_register:
                    print(f"  [FAIL] Could not extract any face encodings from {photo_dir}/")
                    print(f"     Check photo quality or recapture: python scripts/capture_faces.py")
                    return False
            else:
                print(f"  [!] No photo folder found at {photo_dir}")
                print(f"     Capture photos first: python scripts/capture_faces.py --name {folder_name}")
                print(f"     Then run this registration again.")
                return False

            # Now add to database — only after we know encoding extraction succeeded
            if not self.db.add_user(person_id, name, role):
                print(f"  [FAIL] Could not add to database (may be locked — stop the Flask server).")
                return False

            print(f"  [OK] Added to database: {person_id}")

            for encoding in encodings_to_register:
                self.engine.register_face(person_id, name, encoding)

            if encodings_to_register:
                print(f"  [OK] Registered {len(encodings_to_register)} face encoding(s) from {photo_dir}/")
                self.save_encodings()

            return True
        except Exception as e:
            print(f"  [FAIL] Error: {e}")
            return False
    
    def register_from_photos(self, person_name, person_id, role='resident'):
        """
        Register a person using captured photos
        
        Args:
            person_name: Name used for photo directory (e.g., 'john_doe')
            person_id: Unique identifier (e.g., 'resident_001')
            role: 'resident' or 'caregiver'
        """
        photo_dir = BASE_DIR / 'data' / 'samples' / person_name

        # Check if photos exist
        if not photo_dir.exists():
            print(f"[FAIL] No photos found at: {photo_dir}")
            print(f"  Run: python scripts/capture_faces.py")
            return False

        # Count photos
        photos = [f for f in photo_dir.iterdir() if f.suffix.lower() in ['.jpg', '.jpeg', '.png']]
        if not photos:
            print(f"[FAIL] No image files found in: {photo_dir}")
            return False
        
        print(f"\nFound {len(photos)} photos for {person_name}")
        print(f"Extracting face encodings from photos...")
        
        # Extract face encodings from all photos (quality-checked)
        encodings = []
        quality_skipped = 0
        for i, photo_path in enumerate(photos, 1):
            try:
                frame = cv2.imread(str(photo_path))
                if frame is None:
                    print(f"  [FAIL] Could not read {photo_path.name}")
                    continue

                faces = self.engine.detect_faces(frame)
                if len(faces) == 0:
                    print(f"  [FAIL] No face detected in {photo_path.name}")
                    continue

                (x, y, w, h) = faces[0]
                face_roi = frame[y:y+h, x:x+w]

                quality = self.engine._score_face_quality(face_roi)
                if not quality["passed"]:
                    print(f"  [SKIP] {photo_path.name} — {quality['reason']}")
                    quality_skipped += 1
                    continue

                encoding = self.engine._extract_face_features(face_roi)
                if encoding is not None:
                    encodings.append(encoding)
                    print(f"  [OK]   {photo_path.name} (quality score {quality['score']:.2f})")
                else:
                    print(f"  [FAIL] Failed to extract encoding from {photo_path.name}")
            except Exception as e:
                print(f"  [FAIL] Error processing {photo_path.name}: {e}")

        if quality_skipped:
            print(f"\n  [!] {quality_skipped}/{len(photos)} photos skipped — poor quality"
                  f" (blurry, too small, or bad lighting). Recapture for better accuracy.")
        
        if not encodings:
            print(f"\n[FAIL] Could not extract face encodings from any photos")
            print(f"  Tips:")
            print(f"    - Make sure photos have clear, frontal faces")
            print(f"    - Check image lighting and clarity")
            print(f"    - Re-capture photos and try again")
            return False
        
        print(f"\n[OK] Successfully extracted {len(encodings)} face encodings")
        
        # Register person with extracted encodings
        try:
            if not self.db.add_user(person_id, person_name.replace('_', ' ').title(), role):
                print(f"  [FAIL] Could not add to database (database may be locked).")
                print(f"     Stop the Flask server and try again.")
                return False
            
            print(f"  [OK] Added to database")
            
            for encoding in encodings:
                self.engine.register_face(person_id, person_name, encoding)
            
            print(f"  [OK] Registered {len(encodings)} face encodings in engine")
            self.save_encodings()
            
            print(f"\n[OK] Successfully registered {person_name}")
            return True
            
        except Exception as e:
            print(f"[FAIL] Error during registration: {e}")
            return False
    
    def register_all(self):
        """Auto-register every folder in data/samples/ using folder name as both
        person_id and display name. Skips folders already in the DB."""
        samples_dir = BASE_DIR / 'data' / 'samples'
        if not samples_dir.exists():
            print(f"  [FAIL] No samples directory at {samples_dir}")
            return False

        folders = sorted([d for d in samples_dir.iterdir() if d.is_dir()])
        if not folders:
            print(f"  [FAIL] No person folders found in {samples_dir}")
            return False

        print(f"\nFound {len(folders)} person folder(s): {[f.name for f in folders]}\n")

        registered = 0
        for folder in folders:
            person_name = folder.name
            display_name = person_name.replace('_', ' ').title()
            person_id = person_name  # use folder name as person_id

            photos = list(folder.glob('*.jpg')) + list(folder.glob('*.png'))
            if not photos:
                print(f"  [{person_name}] No photos — skipping")
                continue

            print(f"  [{person_name}] {len(photos)} photos ...")

            encodings = []
            for photo_path in sorted(photos):
                frame = cv2.imread(str(photo_path))
                if frame is None:
                    continue
                faces = self.engine.detect_faces(frame)
                if not faces:
                    continue
                x, y, w, h = (int(v) for v in faces[0])
                face_roi = frame[y:y+h, x:x+w]

                quality = self.engine._score_face_quality(face_roi)
                if not quality["passed"]:
                    continue

                encoding = self.engine._extract_face_features(face_roi)
                if encoding is not None:
                    encodings.append(encoding)

            if not encodings:
                print(f"  [{person_name}] Could not extract any encodings — skipping")
                continue

            self.db.add_user(person_id, display_name, 'resident')
            for enc in encodings:
                self.engine.register_face(person_id, display_name, enc)

            print(f"  [{person_name}] Registered {len(encodings)} encodings, added to DB")
            registered += 1

        if registered:
            self.save_encodings()
            print(f"\n[OK] {registered} person(s) registered and saved.")
        else:
            print("\n[FAIL] No persons could be registered.")
        return registered > 0

    def list_registered_people(self):
        """List all registered people from the database"""
        try:
            users = self.db.get_users()
            stats = self.db.get_database_stats()

            print("\n" + "=" * 60)
            print("REGISTERED PEOPLE")
            print("=" * 60)

            if not users:
                print("  No users registered yet.")
                print("  Run: python scripts/register_faces.py --all")
            else:
                print(f"  {'ID':<20} {'Name':<25} {'Role':<12}")
                print("  " + "-" * 55)
                for u in users:
                    uid = u.get('user_id', '?')
                    name = u.get('name', '?')
                    role = u.get('role', '?')
                    print(f"  {uid:<20} {name:<25} {role:<12}")

            print(f"\n  Total users: {stats['total_users']}")
            print(f"  Total access events: {stats['total_access_events']}")

        except Exception as e:
            print(f"Error: {e}")
    
    def show_facial_recognition_stats(self):
        """Show facial recognition statistics"""
        stats = self.engine.get_recognition_stats()
        
        print("\n" + "=" * 60)
        print("FACIAL RECOGNITION STATS")
        print("=" * 60)
        print(f"Total registered persons: {stats['total_persons']}")
        print(f"Total face encodings: {stats['total_face_encodings']}")
        print(f"Confidence threshold: {stats['confidence_threshold']}")

def main():
    """Main interactive registration menu"""
    import argparse
    parser = argparse.ArgumentParser(description="Register faces in the system")
    parser.add_argument("--all", action="store_true",
                        help="Auto-register every folder in data/samples/ (no prompts)")
    args = parser.parse_args()

    print("\n" + "=" * 70)
    print("DOOR FACE PANELS - FACE REGISTRATION SYSTEM")
    print("=" * 70)

    reg = FaceRegistration()

    if args.all:
        reg.register_all()
        return

    while True:
        print("\nOptions:")
        print("  1. Register all people in data/samples/ (recommended)")
        print("  2. Register one person from photos")
        print("  3. Register new person (manual ID + name)")
        print("  4. View registered people")
        print("  5. View facial recognition stats")
        print("  6. Exit")

        choice = input("\nSelect option (1-6): ").strip()

        if choice == '1':
            reg.register_all()

        elif choice == '2':
            print("\n" + "=" * 60)
            print("REGISTER FROM PHOTOS")
            print("=" * 60)

            person_name = input("Enter folder name in data/samples/ (e.g. 'Advitiya'): ").strip()
            if not person_name:
                print("Error: Name required")
                continue

            person_id = input(f"Enter person ID [{person_name}]: ").strip() or person_name

            role = input("Enter role (resident/caregiver) [resident]: ").strip().lower()
            if role not in ['resident', 'caregiver']:
                role = 'resident'

            print(f"\nRegistering: {person_name} ({person_id}) from photos...")
            if reg.register_from_photos(person_name, person_id, role):
                print(f"\n[OK] Successfully registered {person_name} from photos")
            else:
                print(f"\n[FAIL] Failed to register from photos")

        elif choice == '3':
            print("\n" + "=" * 60)
            print("MANUAL REGISTRATION")
            print("=" * 60)

            person_id = input("Enter person ID (e.g., 'resident_001'): ").strip()
            if not person_id:
                print("Error: Person ID required")
                continue

            name = input("Enter full name: ").strip()
            if not name:
                print("Error: Name required")
                continue

            role = input("Enter role (resident/caregiver) [resident]: ").strip().lower()
            if role not in ['resident', 'caregiver']:
                role = 'resident'

            print(f"\nRegistering: {name} ({person_id}) as {role}...")
            if reg.register_person(person_id, name, role):
                print(f"\n[OK] Successfully registered {name}")
            else:
                print(f"\n[FAIL] Failed to register {name}")

        elif choice == '4':
            reg.list_registered_people()

        elif choice == '5':
            reg.show_facial_recognition_stats()

        elif choice == '6':
            print("\nExiting registration system...")
            break

        else:
            print("Invalid option")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nExiting...")
    except Exception as e:
        print(f"\nError: {e}")
