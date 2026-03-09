"""
Face Registration Utility - Register captured faces in the system
Adds people to database and facial recognition engine.

Run from project root:
  python3 scripts/register_faces.py
"""
import sys
from pathlib import Path

# Ensure project root is on sys.path so 'data' and 'api' can be imported
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

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
            # Add to database
            if not self.db.add_user(person_id, name, role):
                print(f"  [FAIL] Could not add to database (database may be locked).")
                print(f"     Stop the Flask server and try again.")
                return False
            
            print(f"  [OK] Added to database: {person_id}")
            
            # Try to extract real face encodings from data/samples/{name}/
            # Use the folder name derived from the display name (spaces → underscores, lower)
            folder_name = name.replace(' ', '_').lower()
            photo_dir = Path(f'data/samples/{folder_name}')
            
            # Also try exact name as typed in case the folder matches it directly
            if not photo_dir.exists():
                photo_dir = Path(f'data/samples/{name}')
            
            if photo_dir.exists():
                photos = list(photo_dir.glob('*.jpg')) + list(photo_dir.glob('*.png'))
                encodings_registered = 0
                
                for photo_path in photos:
                    frame = cv2.imread(str(photo_path))
                    if frame is None:
                        continue
                    faces = self.engine.detect_faces(frame)
                    if len(faces) == 0:
                        continue
                    x, y, w, h = faces[0]
                    face_roi = frame[y:y+h, x:x+w]
                    encoding = self.engine._extract_face_features(face_roi)
                    if encoding is not None:
                        self.engine.register_face(person_id, name, encoding)
                        encodings_registered += 1
                
                if encodings_registered > 0:
                    print(f"  [OK] Registered {encodings_registered} face encoding(s) from {photo_dir}/")
                else:
                    print(f"  [!] Found photo folder but could not extract any face encodings.")
                    print(f"     Check photo quality, or recapture with: python scripts/capture_faces.py")
            else:
                print(f"  [!] No photo folder found at data/samples/{folder_name}/")
                print(f"     Person added to DB only. Capture photos first, then use Option 2")
                print(f"     to register face encodings: python scripts/capture_faces.py")
            
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
        photo_dir = f'data/samples/{person_name}'
        
        # Check if photos exist
        if not Path(photo_dir).exists():
            print(f"[FAIL] No photos found at: {photo_dir}")
            print(f"  Run: python scripts/capture_faces.py")
            return False
        
        # Count photos
        photos = [f for f in Path(photo_dir).iterdir() if f.suffix.lower() in ['.jpg', '.jpeg', '.png']]
        if not photos:
            print(f"[FAIL] No image files found in: {photo_dir}")
            return False
        
        print(f"\nFound {len(photos)} photos for {person_name}")
        print(f"Extracting face encodings from photos...")
        
        # Extract face encodings from all photos
        encodings = []
        for i, photo_path in enumerate(photos, 1):
            try:
                frame = cv2.imread(str(photo_path))
                if frame is None:
                    print(f"  [FAIL] Could not read {photo_path.name}")
                    continue
                
                # Detect faces in photo
                faces = self.engine.detect_faces(frame)
                if len(faces) > 0:
                    # Extract encoding from detected face
                    (x, y, w, h) = faces[0]
                    face_roi = frame[y:y+h, x:x+w]
                    encoding = self.engine._extract_face_features(face_roi)
                    
                    if encoding is not None:
                        encodings.append(encoding)
                        print(f"  [OK] Extracted encoding from {photo_path.name}")
                    else:
                        print(f"  [FAIL] Failed to extract encoding from {photo_path.name}")
                else:
                    print(f"  [FAIL] No face detected in {photo_path.name}")
            except Exception as e:
                print(f"  [FAIL] Error processing {photo_path.name}: {e}")
        
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
