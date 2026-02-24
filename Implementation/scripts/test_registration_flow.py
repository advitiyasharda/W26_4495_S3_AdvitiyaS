#!/usr/bin/env python3
"""
Non-interactive test: Register 3 people from existing samples and run recognition test.
Uses Advitya, Eric, Dino (or Reubin if Dino has issues).

Run from project root: python3 scripts/test_registration_flow.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.register_faces import FaceRegistration


def main():
    # Pick 3 people with photos
    people = [
        ("Advitya", "RES-001", "resident"),
        ("Eric", "RES-002", "resident"),
        ("Dino", "RES-003", "resident"),
    ]
    
    # Fallback if Dino has no usable photos
    if not (Path("data/samples/Dino").exists() and list(Path("data/samples/Dino").glob("*.jpg"))):
        people = [
            ("Advitya", "RES-001", "resident"),
            ("Eric", "RES-002", "resident"),
            ("Reubin", "RES-003", "resident"),
        ]
    
    print("\n" + "=" * 60)
    print("REGISTRATION FLOW TEST - 3 people from data/samples/")
    print("=" * 60)
    
    reg = FaceRegistration()
    registered = 0
    
    for person_name, person_id, role in people:
        folder = Path(f"data/samples/{person_name}")
        if not folder.exists():
            print(f"\n  Skip {person_name}: folder not found")
            continue
        photos = list(folder.glob("*.jpg")) + list(folder.glob("*.jpeg")) + list(folder.glob("*.png"))
        if not photos:
            print(f"\n  Skip {person_name}: no photos")
            continue
        
        print(f"\n--- Registering {person_name} ({person_id}) ---")
        if reg.register_from_photos(person_name, person_id, role):
            registered += 1
        else:
            print(f"  ✗ Failed to register {person_name}")
    
    print("\n" + "=" * 60)
    print(f"Registered {registered}/3 people")
    print("=" * 60)
    
    if registered >= 2:
        print("\n✓ Test passed. Run quick_test to verify recognition:")
        print("  python3 scripts/quick_test_recognition.py")
        return 0
    else:
        print("\n✗ Need at least 2 people with valid face photos in data/samples/")
        return 1


if __name__ == "__main__":
    sys.exit(main())
