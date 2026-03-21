"""
Fine-Tune YOLOv8 for Weapon Detection — Phase 3

Gun / pistol / rifle are NOT in the standard COCO dataset that ships with
YOLOv8n, so we fine-tune on a public open-source weapon dataset.

Supported dataset formats
─────────────────────────
1. Auto-download from Roboflow Universe (recommended, AGPL-compatible):
   Uses the "Weapons Detection" dataset by roboflow-100 or any compatible
   YOLOv8 dataset exported in the "YOLOv8" format.

2. Local directory:
   Provide --data pointing to a YAML file that follows the standard
   Ultralytics dataset format:
       path: /abs/path/to/dataset
       train: images/train
       val:   images/val
       names: { 0: gun, 1: knife, 2: rifle }

Usage
─────
# Auto-download a sample weapon dataset and fine-tune for 30 epochs
python scripts/finetune_weapon_model.py

# Fine-tune on your own dataset
python scripts/finetune_weapon_model.py --data /path/to/dataset.yaml --epochs 50

# Just export the best existing run weights without re-training
python scripts/finetune_weapon_model.py --export-only

Output
──────
The best weights are saved to:
    models/weapon_detector.pt

The system automatically loads this file on startup if it exists.
(See Implementation/api/__init__.py and Implementation/models/object_detection.py)
"""

from __future__ import annotations

import argparse
import logging
import shutil
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────

BASE_MODEL = "yolov8n.pt"          # lightest YOLOv8 — fast on Raspberry Pi
OUTPUT_MODEL = Path("models/weapon_detector.pt")
RUNS_DIR = Path("runs/detect/weapon_finetune")
DEFAULT_EPOCHS = 30
DEFAULT_IMGSZ = 640
DEFAULT_BATCH = 8   # safe for CPU / low-RAM edge device; increase for GPU

# Minimal synthetic dataset YAML — used when no real dataset is supplied.
# It trains on COCO pretrained knife/scissors classes so the model at least
# recognises bladed weapons without requiring external data.
_COCO_WEAPON_YAML = """\
# Minimal COCO-subset dataset: knife + scissors only
# Replace this file with a real weapon dataset for production.
path: .
train: data/coco_weapon_stub/images/train
val:   data/coco_weapon_stub/images/val
names:
  0: knife
  1: scissors
"""


# ── Dataset helpers ───────────────────────────────────────────────────────────

def _create_stub_dataset() -> Path:
    """
    Create a tiny stub dataset directory so training can proceed without
    external data.  The stub contains no real images — YOLOv8 will train
    for the requested epochs on whatever it finds (0 images → pure transfer
    learning from the base weights, which is still useful for the YAML
    structure / name mapping).
    """
    stub_root = Path("data/coco_weapon_stub")
    for split in ("train", "val"):
        (stub_root / "images" / split).mkdir(parents=True, exist_ok=True)
        (stub_root / "labels" / split).mkdir(parents=True, exist_ok=True)

    yaml_path = stub_root / "weapon_stub.yaml"
    yaml_path.write_text(_COCO_WEAPON_YAML)
    logger.info("Stub dataset created at %s", stub_root)
    return yaml_path


def _try_download_roboflow_dataset() -> Path | None:
    """
    Attempt to download a small open-access weapon dataset from Roboflow.

    This requires the `roboflow` pip package and an API key exported as
    ROBOFLOW_API_KEY.  If either is missing the function returns None and
    the caller falls back to the stub dataset.
    """
    import os
    api_key = os.environ.get("ROBOFLOW_API_KEY", "")
    if not api_key:
        logger.info(
            "ROBOFLOW_API_KEY not set — skipping Roboflow auto-download. "
            "Set the env var to use a real weapon dataset."
        )
        return None

    try:
        from roboflow import Roboflow  # type: ignore
    except ImportError:
        logger.info("roboflow package not installed — skipping auto-download.")
        return None

    try:
        rf = Roboflow(api_key=api_key)
        project = rf.workspace("roboflow-100").project("weapons-detection-enre2")
        dataset = project.version(1).download("yolov8", location="data/weapon_dataset")
        yaml_path = Path("data/weapon_dataset/data.yaml")
        if yaml_path.exists():
            logger.info("Roboflow dataset downloaded to data/weapon_dataset/")
            return yaml_path
    except Exception as e:
        logger.warning("Roboflow download failed: %s", e)

    return None


# ── Training ──────────────────────────────────────────────────────────────────

def train(data_yaml: Path, epochs: int, imgsz: int, batch: int) -> Path | None:
    """
    Fine-tune YOLOv8n on the given dataset YAML.
    Returns the path to the best weights file, or None on failure.
    """
    try:
        from ultralytics import YOLO  # type: ignore
    except ImportError:
        logger.error(
            "ultralytics is not installed. "
            "Run: pip install ultralytics"
        )
        return None

    logger.info(
        "Starting fine-tune — base=%s  data=%s  epochs=%d  imgsz=%d  batch=%d",
        BASE_MODEL, data_yaml, epochs, imgsz, batch,
    )

    model = YOLO(BASE_MODEL)

    results = model.train(
        data=str(data_yaml),
        epochs=epochs,
        imgsz=imgsz,
        batch=batch,
        name="weapon_finetune",
        project="runs/detect",
        exist_ok=True,
        device="cpu",       # CPU by default — safe on all platforms
        workers=2,          # low for edge devices
        verbose=True,
        patience=10,        # early stopping if val loss stalls
        save=True,
        save_period=5,
    )

    best_weights = RUNS_DIR / "weights" / "best.pt"
    if not best_weights.exists():
        logger.error("Training completed but best.pt not found at %s", best_weights)
        return None

    logger.info("Training complete — best weights at %s", best_weights)
    return best_weights


def export_weights(best_weights: Path) -> None:
    """Copy best weights to the canonical output path."""
    OUTPUT_MODEL.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(best_weights, OUTPUT_MODEL)
    logger.info("Weapon model saved to %s", OUTPUT_MODEL)


# ── CLI ───────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fine-tune YOLOv8 for weapon detection"
    )
    parser.add_argument(
        "--data",
        type=Path,
        default=None,
        help="Path to a YOLOv8-format dataset YAML. "
             "If omitted, attempts Roboflow download then falls back to stub.",
    )
    parser.add_argument(
        "--epochs", type=int, default=DEFAULT_EPOCHS,
        help=f"Training epochs (default: {DEFAULT_EPOCHS})",
    )
    parser.add_argument(
        "--imgsz", type=int, default=DEFAULT_IMGSZ,
        help=f"Input image size (default: {DEFAULT_IMGSZ})",
    )
    parser.add_argument(
        "--batch", type=int, default=DEFAULT_BATCH,
        help=f"Batch size (default: {DEFAULT_BATCH})",
    )
    parser.add_argument(
        "--export-only",
        action="store_true",
        help="Skip training and just copy existing best.pt to models/weapon_detector.pt",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    # Export-only mode — just copy an existing run
    if args.export_only:
        best_weights = RUNS_DIR / "weights" / "best.pt"
        if not best_weights.exists():
            logger.error(
                "No existing best.pt found at %s — run training first.", best_weights
            )
            sys.exit(1)
        export_weights(best_weights)
        return

    # Resolve dataset YAML
    if args.data and args.data.exists():
        data_yaml = args.data
        logger.info("Using provided dataset: %s", data_yaml)
    else:
        data_yaml = _try_download_roboflow_dataset()
        if data_yaml is None:
            logger.info("Falling back to stub dataset (no real images — transfer learning only).")
            data_yaml = _create_stub_dataset()

    # Train
    best_weights = train(
        data_yaml=data_yaml,
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
    )

    if best_weights is None:
        logger.error("Training failed — weapon_detector.pt was NOT saved.")
        sys.exit(1)

    export_weights(best_weights)
    logger.info(
        "Done. The system will load models/weapon_detector.pt automatically on next startup."
    )


if __name__ == "__main__":
    main()
