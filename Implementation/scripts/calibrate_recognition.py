"""
Recognition Threshold Calibration Tool

Tests DISTANCE_MATCH_THRESHOLD values from 0.30 to 0.80 against your
registered sample photos and reports accuracy at each step.

The best threshold (highest F1 score) is written back to config.py so
the live system immediately benefits from the result.

Run from project root:
    python scripts/calibrate_recognition.py

Optional flags:
    --dry-run   Print results but do NOT update config.py
    --verbose   Show per-image detail during testing
"""

import sys
import os
import re
import cv2
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from api.facial_recognition import FacialRecognitionEngine, USE_FACE_RECOGNITION_LIB

# ── Config ───────────────────────────────────────────────────────────────────

SAMPLES_DIR    = Path(__file__).resolve().parent.parent / "data" / "samples"
CONFIG_PATH    = Path(__file__).resolve().parent.parent / "config.py"
THRESHOLD_STEPS = [round(v, 2) for v in np.arange(0.30, 0.81, 0.05)]

DRY_RUN = "--dry-run" in sys.argv
VERBOSE = "--verbose" in sys.argv


# ── Helpers ──────────────────────────────────────────────────────────────────

def load_samples(engine: FacialRecognitionEngine):
    """
    Load every image in data/samples/<person_id>/*.jpg|png,
    register the person in the engine, and return a list of
    (person_id, face_roi_bgr) tuples for testing.
    """
    samples = []

    if not SAMPLES_DIR.exists():
        print(f"[WARN] Samples directory not found: {SAMPLES_DIR}")
        print("       Register some faces first with: python scripts/register_faces.py")
        return samples

    for person_dir in sorted(SAMPLES_DIR.iterdir()):
        if not person_dir.is_dir():
            continue

        person_id = person_dir.name
        encodings_loaded = 0

        for img_path in sorted(person_dir.glob("*.jpg")) or sorted(person_dir.glob("*.png")):
            img = cv2.imread(str(img_path))
            if img is None:
                continue

            faces = engine.detect_faces(img)
            if len(faces) == 0:
                if VERBOSE:
                    print(f"  [skip] {img_path.name} — no face detected")
                continue

            x, y, w, h = faces[0]
            face_roi = img[y:y+h, x:x+w]
            encoding = engine._extract_face_features(face_roi)

            if encoding is not None:
                engine.register_face(person_id, person_id, encoding)
                samples.append((person_id, face_roi))
                encodings_loaded += 1

        if encodings_loaded:
            print(f"  Loaded {encodings_loaded:2d} photos  →  {person_id}")

    return samples


def evaluate_threshold(engine: FacialRecognitionEngine,
                        samples: list,
                        threshold: float) -> dict:
    """
    Run every sample through recognize_face() at the given threshold
    and return precision / recall / F1 metrics.
    """
    tp = fp = fn = 0

    for true_id, face_roi in samples:
        h, w = face_roi.shape[:2]
        # Build a minimal frame that contains only this face ROI
        frame  = face_roi.copy()
        result = engine.recognize_face(frame, (0, 0, w, h))

        predicted_id = result.get("person_id")

        if predicted_id == true_id:
            tp += 1
        elif predicted_id is None:
            fn += 1
        else:
            fp += 1

    total     = len(samples)
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall    = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1        = (2 * precision * recall / (precision + recall)
                 if (precision + recall) > 0 else 0.0)
    accuracy  = tp / total if total > 0 else 0.0

    return {
        "threshold": threshold,
        "tp": tp, "fp": fp, "fn": fn,
        "accuracy": round(accuracy, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
    }


def update_config(optimal_threshold: float) -> None:
    """Rewrite FACE_DISTANCE_MATCH_THRESHOLD in config.py."""
    text = CONFIG_PATH.read_text(encoding="utf-8")

    # Update the facial recognition distance threshold constant
    # (used by facial_recognition.py at module load via config import)
    new_line = f"FACE_RECOGNITION_DISTANCE_THRESHOLD = {optimal_threshold}"

    if "FACE_RECOGNITION_DISTANCE_THRESHOLD" in text:
        text = re.sub(
            r"FACE_RECOGNITION_DISTANCE_THRESHOLD\s*=\s*[\d.]+",
            new_line,
            text,
        )
    else:
        # Append after the existing FACE_CONFIDENCE_THRESHOLD line
        text = text.replace(
            "FACE_CONFIDENCE_THRESHOLD",
            "FACE_CONFIDENCE_THRESHOLD",
        )
        insert_after = "FACE_CONFIDENCE_THRESHOLD = 0.6"
        text = text.replace(
            insert_after,
            f"{insert_after}\n{new_line}  # auto-calibrated",
        )

    CONFIG_PATH.write_text(text, encoding="utf-8")
    print(f"\n[config.py] FACE_RECOGNITION_DISTANCE_THRESHOLD updated → {optimal_threshold}")


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("=" * 65)
    print("FACIAL RECOGNITION — THRESHOLD CALIBRATION")
    mode = "dlib (face_recognition)" if USE_FACE_RECOGNITION_LIB else "OpenCV HOG fallback"
    print(f"Engine : {mode}")
    print(f"Samples: {SAMPLES_DIR}")
    print(f"Dry run: {DRY_RUN}")
    print("=" * 65)

    engine = FacialRecognitionEngine(confidence_threshold=0.0)

    print("\nLoading sample photos...")
    samples = load_samples(engine)

    if not samples:
        print("\n[ERROR] No usable samples found. Cannot calibrate.")
        print("        Run  python scripts/register_faces.py  first.")
        sys.exit(1)

    print(f"\n{len(samples)} face samples loaded across "
          f"{len(engine.known_faces)} registered person(s).\n")

    # Header
    col = "{:<10} {:>9} {:>10} {:>8} {:>8}"
    print(col.format("Threshold", "Accuracy", "Precision", "Recall", "F1"))
    print("-" * 50)

    results = []
    for t in THRESHOLD_STEPS:
        # Temporarily patch the engine's internal threshold
        import api.facial_recognition as fr_mod
        original = fr_mod.DISTANCE_MATCH_THRESHOLD
        fr_mod.DISTANCE_MATCH_THRESHOLD = t

        metrics = evaluate_threshold(engine, samples, t)
        results.append(metrics)

        marker = ""
        print(col.format(
            f"  {t:.2f}",
            f"{metrics['accuracy']*100:.1f}%",
            f"{metrics['precision']*100:.1f}%",
            f"{metrics['recall']*100:.1f}%",
            f"{metrics['f1']:.3f} {marker}",
        ))

        fr_mod.DISTANCE_MATCH_THRESHOLD = original

    # Pick best by F1
    best = max(results, key=lambda r: (r["f1"], r["accuracy"]))

    print("\n" + "=" * 65)
    print(f"OPTIMAL THRESHOLD : {best['threshold']:.2f}  "
          f"(F1={best['f1']:.3f}  accuracy={best['accuracy']*100:.1f}%)")
    print("=" * 65)

    if DRY_RUN:
        print("\n[--dry-run] config.py NOT updated.")
    else:
        update_config(best["threshold"])
        print("\nRe-run  python scripts/diagnose_recognition.py  to verify the improvement.")


if __name__ == "__main__":
    main()
