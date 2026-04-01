"""
Face Registration Utility - Register captured faces in the system
Adds people to database and facial recognition engine.

Run from anywhere:
  python scripts/register_faces.py
"""
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from data.database import Database
from api.facial_recognition import FacialRecognitionEngine
import cv2

class FaceRegistration:
    """Register faces in the Door Face Panels system"""
    
    def __init__(self):
        self.db = Database()
        self.engine = FacialRecognitionEngine()
    
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
                print(f"     Capture photos first: python scripts/capture_faces.py")
                print(f"     Then use Option 2 to register from photos.")
                # Still add to DB so the person exists; encodings can be added later
                # via Option 2 once photos are captured.

            # Now add to database — only after we know encoding extraction succeeded
            if not self.db.add_user(person_id, name, role):
                print(f"  [FAIL] Could not add to database (may be locked — stop the Flask server).")
                return False

            print(f"  [OK] Added to database: {person_id}")

            for encoding in encodings_to_register:
                self.engine.register_face(person_id, name, encoding)

            if encodings_to_register:
                print(f"  [OK] Registered {len(encodings_to_register)} face encoding(s) from {photo_dir}/")

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
            
            # Register all encodings
            for encoding in encodings:
                self.engine.register_face(person_id, person_name, encoding)
            
            print(f"  [OK] Registered {len(encodings)} face encodings in engine")
            
            print(f"\n[OK] Successfully registered {person_name}")
            return True
            
        except Exception as e:
            print(f"[FAIL] Error during registration: {e}")
            return False
    
    def list_registered_people(self):
        """List all registered people"""
        try:
            stats = self.db.get_database_stats()
            
            print("\n" + "=" * 60)
            print("REGISTERED PEOPLE")
            print("=" * 60)
            print(f"Total users: {stats['total_users']}")
            print(f"Total accesses logged: {stats['total_access_events']}")
            
            # In a real system, would query the users table
            print("\n(To see details, run: SELECT * FROM users in database)")
            
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
    print("\n" + "=" * 70)
    print("DOOR FACE PANELS - FACE REGISTRATION SYSTEM")
    print("=" * 70)
    
    reg = FaceRegistration()
    
    while True:
        print("\nOptions:")
        print("  1. Register new person (manual)")
        print("  2. Register from captured photos")
        print("  3. View registered people")
        print("  4. View facial recognition stats")
        print("  5. Exit")
        
        choice = input("\nSelect option (1-5): ").strip()
        
        if choice == '1':
            # Manual registration
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
            
            role = input("Enter role (resident/caregiver, default: resident): ").strip().lower()
            if role not in ['resident', 'caregiver']:
                role = 'resident'
            
            print(f"\nRegistering: {name} ({person_id}) as {role}...")
            if reg.register_person(person_id, name, role):
                print(f"\n[OK] Successfully registered {name}")
            else:
                print(f"\n[FAIL] Failed to register {name}")
        
        elif choice == '2':
            # Register from photos
            print("\n" + "=" * 60)
            print("REGISTER FROM PHOTOS")
            print("=" * 60)
            
            person_name = input("Enter person name from photos (e.g., 'john_doe'): ").strip()
            if not person_name:
                print("Error: Name required")
                continue
            
            person_id = input("Enter person ID (e.g., 'resident_001'): ").strip()
            if not person_id:
                print("Error: Person ID required")
                continue
            
            role = input("Enter role (resident/caregiver, default: resident): ").strip().lower()
            if role not in ['resident', 'caregiver']:
                role = 'resident'
            
            print(f"\nRegistering: {person_name} ({person_id}) from photos...")
            if reg.register_from_photos(person_name, person_id, role):
                print(f"\n[OK] Successfully registered {person_name} from photos")
            else:
                print(f"\n[FAIL] Failed to register from photos")
        
        elif choice == '3':
            reg.list_registered_people()
        
        elif choice == '4':
            reg.show_facial_recognition_stats()
        
        elif choice == '5':
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
