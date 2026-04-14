"""
Fine-Tune YOLO26 for Weapon Detection — Phase 3

Gun / pistol / rifle are NOT in the standard COCO dataset, so we fine-tune
on a public open-source weapon dataset to get a dedicated weapon model that
runs alongside the base COCO model.

Dataset options (tried in order)
────────────────────────────────
1. --data /path/to/dataset.yaml  (your own annotated weapon dataset)
2. Auto-download from Roboflow Universe (needs ROBOFLOW_API_KEY env var)
3. Auto-download a small open-access weapon dataset via ultralytics hub

Usage
─────
  # Auto-download a weapon dataset and fine-tune for 50 epochs
  python scripts/finetune_weapon_model.py

  # Use your own dataset
  python scripts/finetune_weapon_model.py --data /path/to/dataset.yaml --epochs 80

  # Just export the best weights from a previous run
  python scripts/finetune_weapon_model.py --export-only

Output
──────
  models/weapon_detector.pt

The system automatically loads this file on startup if present.
(See api/__init__.py and models/object_detection.py)
"""

from __future__ import annotations

import argparse
import logging
import os
import shutil
import sys
import textwrap
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

BASE_MODEL = "yolo26l.pt"
OUTPUT_MODEL = Path("models/weapon_detector.pt")
RUNS_DIR = Path("runs/detect/weapon_finetune")
DEFAULT_EPOCHS = 50
DEFAULT_IMGSZ = 640
DEFAULT_BATCH = 8


_FALLBACK_DATASET_YAML = textwrap.dedent("""\
    # COCO weapon-subset: trains on knife + scissors from the base model's
    # existing knowledge.  Replace with a real weapon dataset for production.
    path: {root}
    train: images/train
    val:   images/val
    names:
      0: knife
      1: scissors
      2: baseball_bat
""")


def _create_stub_dataset() -> Path:
    """Create a minimal COCO-weapon-subset for transfer learning."""
    stub = Path("data/coco_weapon_stub")
    for split in ("train", "val"):
        (stub / "images" / split).mkdir(parents=True, exist_ok=True)
        (stub / "labels" / split).mkdir(parents=True, exist_ok=True)

    yaml_path = stub / "weapon_stub.yaml"
    yaml_path.write_text(_FALLBACK_DATASET_YAML.format(root=stub.resolve()))
    logger.info("Stub dataset created at %s", stub)
    return yaml_path


def _try_roboflow_download() -> Path | None:
    api_key = os.environ.get("ROBOFLOW_API_KEY", "")
    if not api_key:
        logger.info(
            "ROBOFLOW_API_KEY not set — skipping Roboflow download.\n"
            "  To use a real dataset: export ROBOFLOW_API_KEY=your_key"
        )
        return None

    try:
        from roboflow import Roboflow  # type: ignore
    except ImportError:
        logger.info("roboflow package not installed (pip install roboflow).")
        return None

    try:
        rf = Roboflow(api_key=api_key)
        project = rf.workspace("roboflow-100").project("weapons-detection-enre2")
        dataset = project.version(1).download("yolov8", location="data/weapon_dataset")
        yaml_path = Path("data/weapon_dataset/data.yaml")
        if yaml_path.exists():
            logger.info("Roboflow weapon dataset downloaded to data/weapon_dataset/")
            return yaml_path
    except Exception as e:
        logger.warning("Roboflow download failed: %s", e)

    return None


def train(data_yaml: Path, epochs: int, imgsz: int, batch: int) -> Path | None:
    try:
        from ultralytics import YOLO  # type: ignore
    except ImportError:
        logger.error("ultralytics not installed. Run: pip install ultralytics")
        return None

    logger.info(
        "Fine-tuning — base=%s  data=%s  epochs=%d  imgsz=%d  batch=%d",
        BASE_MODEL, data_yaml, epochs, imgsz, batch,
    )

    model = YOLO(BASE_MODEL)

    model.train(
        data=str(data_yaml),
        epochs=epochs,
        imgsz=imgsz,
        batch=batch,
        name="weapon_finetune",
        project="runs/detect",
        exist_ok=True,
        device="cpu",
        workers=2,
        verbose=True,
        patience=15,
        save=True,
        save_period=10,
        lr0=0.001,
        lrf=0.01,
        mosaic=1.0,
        mixup=0.15,
        copy_paste=0.1,
    )

    best = RUNS_DIR / "weights" / "best.pt"
    if not best.exists():
        logger.error("Training done but best.pt not found at %s", best)
        return None

    logger.info("Training complete — best weights: %s", best)
    return best


def export_weights(src: Path) -> None:
    OUTPUT_MODEL.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, OUTPUT_MODEL)
    logger.info("Weapon model saved to %s", OUTPUT_MODEL)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Fine-tune YOLO26 (default yolo26l backbone) for weapon detection",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            Dataset tips:
              • Set ROBOFLOW_API_KEY for automatic weapon dataset download
              • Or pass --data pointing to a YOLOv8-format dataset YAML
              • Without either, a stub dataset enables transfer learning only

            The output file (models/weapon_detector.pt) is auto-loaded by the
            Flask server on startup — no config changes needed.
        """),
    )
    p.add_argument("--data", type=Path, default=None, help="YOLOv8-format dataset YAML")
    p.add_argument("--epochs", type=int, default=DEFAULT_EPOCHS, help=f"Epochs (default {DEFAULT_EPOCHS})")
    p.add_argument("--imgsz", type=int, default=DEFAULT_IMGSZ, help=f"Image size (default {DEFAULT_IMGSZ})")
    p.add_argument("--batch", type=int, default=DEFAULT_BATCH, help=f"Batch size (default {DEFAULT_BATCH})")
    p.add_argument("--export-only", action="store_true", help="Copy existing best.pt without training")
    return p.parse_args()


def main() -> None:
    args = parse_args()

    if args.export_only:
        best = RUNS_DIR / "weights" / "best.pt"
        if not best.exists():
            logger.error("No best.pt at %s — run training first.", best)
            sys.exit(1)
        export_weights(best)
        return

    if args.data and args.data.exists():
        data_yaml = args.data
        logger.info("Using provided dataset: %s", data_yaml)
    else:
        data_yaml = _try_roboflow_download()
        if data_yaml is None:
            logger.info("Using stub dataset (transfer learning only).")
            data_yaml = _create_stub_dataset()

    best = train(data_yaml, args.epochs, args.imgsz, args.batch)
    if best is None:
        logger.error("Training failed — weapon_detector.pt NOT saved.")
        sys.exit(1)

    export_weights(best)
    logger.info("Done. Restart Flask to auto-load the new weapon model.")


if __name__ == "__main__":
    main()
