#!/usr/bin/env python3
"""
Download a real weapon dataset and fine-tune YOLO26 (default Large) for weapon detection.

Pulls the WeaponDetection_Grouped dataset from HuggingFace (7,600 images,
3 classes: GUN / KNIFE / PERSON), converts to YOLO format, then trains.
The resulting model is saved to models/weapon_detector.pt and auto-loaded
by Flask on next startup.

Usage (from Implementation/):
  python3 scripts/download_and_train_weapon_model.py
  python3 scripts/download_and_train_weapon_model.py --epochs 30 --batch 16
  python3 scripts/download_and_train_weapon_model.py --skip-download   # reuse already-downloaded data
"""

from __future__ import annotations

import argparse
import logging
import shutil
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

DATASET_DIR = Path("data/weapon_dataset")
YAML_PATH = DATASET_DIR / "data.yaml"
BASE_MODEL = "yolo26l.pt"
OUTPUT_MODEL = Path("models/weapon_detector.pt")
RUNS_DIR = Path("runs/detect/weapon_finetune")

CLASS_NAMES = {0: "gun", 1: "knife", 2: "person"}


def download_and_convert() -> None:
    """Download from HuggingFace and convert to YOLO txt format."""
    try:
        from datasets import load_dataset  # type: ignore
    except ImportError:
        logger.error("Install the datasets library: pip install datasets")
        sys.exit(1)

    logger.info("Downloading WeaponDetection_Grouped from HuggingFace...")
    ds = load_dataset("Subh775/WeaponDetection_Grouped")

    splits = {"train": "train", "validation": "val", "test": "test"}

    for hf_split, yolo_split in splits.items():
        if hf_split not in ds:
            logger.warning("Split '%s' not in dataset, skipping", hf_split)
            continue

        img_dir = DATASET_DIR / "images" / yolo_split
        lbl_dir = DATASET_DIR / "labels" / yolo_split
        img_dir.mkdir(parents=True, exist_ok=True)
        lbl_dir.mkdir(parents=True, exist_ok=True)

        split_data = ds[hf_split]
        total = len(split_data)
        logger.info("Converting %s: %d images...", hf_split, total)

        for i, sample in enumerate(split_data):
            img = sample["image"]
            w_img, h_img = img.size
            img_id = sample.get("image_id", i)
            fname = f"{img_id:06d}"

            img_path = img_dir / f"{fname}.jpg"
            if not img_path.exists():
                img.save(str(img_path), "JPEG", quality=95)

            objects = sample.get("objects", {})
            bboxes = objects.get("bbox", [])
            categories = objects.get("category", [])

            lines = []
            for bbox, cat in zip(bboxes, categories):
                x, y, bw, bh = bbox
                cx = (x + bw / 2) / w_img
                cy = (y + bh / 2) / h_img
                nw = bw / w_img
                nh = bh / h_img
                cx = max(0, min(1, cx))
                cy = max(0, min(1, cy))
                nw = max(0, min(1, nw))
                nh = max(0, min(1, nh))
                lines.append(f"{cat} {cx:.6f} {cy:.6f} {nw:.6f} {nh:.6f}")

            lbl_path = lbl_dir / f"{fname}.txt"
            lbl_path.write_text("\n".join(lines) + "\n" if lines else "")

            if (i + 1) % 500 == 0 or i == total - 1:
                logger.info("  %s: %d/%d", hf_split, i + 1, total)

    yaml_content = f"""\
path: {DATASET_DIR.resolve()}
train: images/train
val: images/val
test: images/test

names:
  0: gun
  1: knife
  2: person

nc: 3
"""
    YAML_PATH.write_text(yaml_content)
    logger.info("Dataset ready at %s", DATASET_DIR)


def train(epochs: int, batch: int, imgsz: int, device: str) -> Path | None:
    try:
        from ultralytics import YOLO  # type: ignore
    except ImportError:
        logger.error("ultralytics not installed: pip install ultralytics")
        return None

    if not YAML_PATH.exists():
        logger.error("data.yaml not found at %s — run download first", YAML_PATH)
        return None

    logger.info(
        "Training: model=%s  epochs=%d  batch=%d  imgsz=%d  device=%s",
        BASE_MODEL, epochs, batch, imgsz, device,
    )

    model = YOLO(BASE_MODEL)

    use_amp = device not in ("mps",)

    model.train(
        data=str(YAML_PATH),
        epochs=epochs,
        imgsz=imgsz,
        batch=batch,
        name="weapon_finetune",
        project="runs/detect",
        exist_ok=True,
        device=device,
        workers=0 if device == "mps" else 4,
        verbose=True,
        patience=8,
        save=True,
        save_period=3,
        amp=use_amp,
        lr0=0.002,
        lrf=0.01,
        warmup_epochs=2,
        mosaic=0.8,
        fliplr=0.5,
        fraction=0.4,
    )

    best = RUNS_DIR / "weights" / "best.pt"
    if not best.exists():
        logger.error("best.pt not found after training")
        return None

    return best


def detect_device() -> str:
    try:
        import torch
        if torch.backends.mps.is_available():
            return "mps"
        if torch.cuda.is_available():
            return "0"
    except Exception:
        pass
    return "cpu"


def main():
    p = argparse.ArgumentParser(description="Download weapon dataset & fine-tune YOLO26l")
    p.add_argument("--epochs", type=int, default=30, help="Training epochs (default 30)")
    p.add_argument("--batch", type=int, default=16, help="Batch size (default 16)")
    p.add_argument("--imgsz", type=int, default=640, help="Image size (default 640)")
    p.add_argument("--device", default=None, help="Device: mps / cpu / 0 (auto-detect)")
    p.add_argument("--skip-download", action="store_true", help="Skip dataset download")
    args = p.parse_args()

    device = args.device or detect_device()
    logger.info("Using device: %s", device)

    if not args.skip_download:
        download_and_convert()
    else:
        if not YAML_PATH.exists():
            logger.error("No dataset found. Run without --skip-download first.")
            sys.exit(1)
        logger.info("Skipping download — using existing dataset at %s", DATASET_DIR)

    best = train(args.epochs, args.batch, args.imgsz, device)
    if best is None:
        logger.error("Training failed.")
        sys.exit(1)

    OUTPUT_MODEL.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(best, OUTPUT_MODEL)
    logger.info("Weapon model saved to %s", OUTPUT_MODEL)
    logger.info("Restart Flask to auto-load the new weapon model.")


if __name__ == "__main__":
    main()
