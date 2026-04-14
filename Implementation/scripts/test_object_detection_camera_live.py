#!/usr/bin/env python3
"""
Live object-detection tester for the FaceDoor smart-door system.

Supports webcam, video file, or image folder as input.  Runs YOLO26 (default Large)
locally (no Flask required) and overlays bounding boxes, severity badges,
an FPS counter, and a detection log panel in real time.

Usage (run from Implementation/):

  # Webcam (default camera 0)
  python3 scripts/test_object_detection_camera_live.py

  # Specific camera
  python3 scripts/test_object_detection_camera_live.py --camera 1

  # Video file
  python3 scripts/test_object_detection_camera_live.py --video path/to/clip.mp4

  # Folder of images (cycles through them)
  python3 scripts/test_object_detection_camera_live.py --images path/to/folder/

  # Tweak detection params
  python3 scripts/test_object_detection_camera_live.py --confidence 0.20 --frame-threshold 2

Keys while running:
  Q / Esc   Quit
  SPACE     Pause / resume
  S         Save screenshot
  R         Reset detection counters & event log
  H         Toggle help overlay
  +/-       Adjust confidence threshold live (±0.05)
"""

from __future__ import annotations

import argparse
import datetime as dt
import glob
import sys
import time
from pathlib import Path
from typing import List, Tuple

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from models.object_detection import DetectionEvent, ObjectDetector  # noqa: E402

SEVERITY_COLOR = {
    "CRITICAL": (40, 40, 220),
    "HIGH":     (0, 135, 255),
    "MEDIUM":   (0, 200, 255),
    "INFO":     (220, 160, 70),
    "LOW":      (160, 160, 160),
}

CATEGORY_EMOJI = {
    "WEAPON":          "!!",
    "SECURITY_THREAT": "!?",
    "PARCEL":          ">>",
    "MOBILITY_AID":    "++",
    "OPERATIONAL":     "..",
}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Live FaceDoor object detection tester",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Keys: Q=quit  SPACE=pause  S=screenshot  R=reset  H=help  +/-=confidence",
    )
    src = p.add_mutually_exclusive_group()
    src.add_argument("--camera", type=int, default=0, help="Webcam index (default 0)")
    src.add_argument("--video", type=str, help="Path to a video file")
    src.add_argument("--images", type=str, help="Path to a folder of images")

    p.add_argument("--confidence", type=float, default=0.20, help="YOLO floor confidence (default 0.20)")
    p.add_argument("--frame-threshold", type=int, default=3, help="Consecutive frames to confirm")
    p.add_argument("--unattended-minutes", type=float, default=2.0, help="Unattended escalation timer")
    p.add_argument("--base-model", default="yolo26l.pt", help="Base YOLO model (default yolo26l.pt)")
    p.add_argument("--weapon-model", default="models/weapon_detector.pt", help="Weapon model path")
    p.add_argument("--width", type=int, default=1100, help="Window width")
    p.add_argument("--height", type=int, default=640, help="Window height")
    return p.parse_args()


class FrameSource:
    """Unified source: webcam, video file, or image folder."""

    def __init__(self, args: argparse.Namespace):
        self._mode = "camera"
        self._images: List[str] = []
        self._img_idx = 0
        self._cap = None

        if args.video:
            self._mode = "video"
            self._cap = cv2.VideoCapture(args.video)
            if not self._cap.isOpened():
                raise SystemExit(f"Cannot open video: {args.video}")
            self.label = f"Video: {Path(args.video).name}"
        elif args.images:
            self._mode = "images"
            exts = ("*.jpg", "*.jpeg", "*.png", "*.bmp", "*.webp")
            for ext in exts:
                self._images.extend(glob.glob(str(Path(args.images) / ext)))
            self._images.sort()
            if not self._images:
                raise SystemExit(f"No images found in {args.images}")
            self.label = f"Images: {Path(args.images).name} ({len(self._images)} files)"
        else:
            self._mode = "camera"
            self._cap = cv2.VideoCapture(args.camera)
            if not self._cap.isOpened():
                raise SystemExit(f"Cannot open camera {args.camera}")
            self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, args.width)
            self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, args.height)
            self.label = f"Camera {args.camera}"

    def read(self) -> Tuple[bool, np.ndarray | None]:
        if self._mode == "images":
            if self._img_idx >= len(self._images):
                self._img_idx = 0
            path = self._images[self._img_idx]
            self._img_idx += 1
            img = cv2.imread(path)
            return (img is not None), img
        else:
            return self._cap.read()

    def release(self):
        if self._cap:
            self._cap.release()

    @property
    def is_images(self) -> bool:
        return self._mode == "images"

    @property
    def total_images(self) -> int:
        return len(self._images)

    @property
    def current_image_name(self) -> str:
        if self._images and self._img_idx > 0:
            return Path(self._images[self._img_idx - 1]).name
        return ""


class HUD:
    """Heads-up display overlay manager."""

    @staticmethod
    def banner(frame: np.ndarray, text: str, color: Tuple[int, int, int]):
        h, w = frame.shape[:2]
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, 44), color, -1)
        cv2.addWeighted(overlay, 0.85, frame, 0.15, 0, frame)
        cv2.putText(frame, text, (14, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2, cv2.LINE_AA)

    @staticmethod
    def fps(frame: np.ndarray, fps_val: float):
        text = f"FPS: {fps_val:.1f}"
        cv2.putText(frame, text, (14, frame.shape[0] - 16), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(frame, text, (14, frame.shape[0] - 16), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 200, 0), 1, cv2.LINE_AA)

    @staticmethod
    def boxes(frame: np.ndarray, events: List[DetectionEvent]):
        fh, fw = frame.shape[:2]
        for evt in events:
            x1n, y1n, x2n, y2n = evt.bbox
            x1, y1 = int(x1n * fw), int(y1n * fh)
            x2, y2 = int(x2n * fw), int(y2n * fh)
            color = SEVERITY_COLOR.get(evt.severity, (170, 170, 170))

            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

            label = f"{evt.object_class}  {evt.severity}  {int(evt.confidence * 100)}%"
            (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.48, 1)
            cv2.rectangle(frame, (x1, max(0, y1 - th - 10)), (x1 + tw + 8, y1), color, -1)
            cv2.putText(frame, label, (x1 + 4, max(th + 2, y1 - 4)), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (255, 255, 255), 1, cv2.LINE_AA)

    @staticmethod
    def sidebar(frame: np.ndarray, detector: ObjectDetector, conf_threshold: float, source_label: str):
        fh, fw = frame.shape[:2]
        pw = 310
        x0 = max(0, fw - pw)

        overlay = frame.copy()
        cv2.rectangle(overlay, (x0, 44), (fw, fh), (30, 30, 30), -1)
        cv2.addWeighted(overlay, 0.88, frame, 0.12, 0, frame)

        y = 68
        gap = 22

        cv2.putText(frame, "FaceDoor Object Detection", (x0 + 10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (130, 220, 130), 1, cv2.LINE_AA)
        y += gap

        cv2.putText(frame, f"Source: {source_label}", (x0 + 10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (180, 180, 180), 1, cv2.LINE_AA)
        y += gap

        cv2.putText(frame, f"Conf floor: {conf_threshold:.0%}  (+/- to adjust)", (x0 + 10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (180, 180, 180), 1, cv2.LINE_AA)
        y += gap

        cv2.line(frame, (x0 + 10, y - 6), (fw - 10, y - 6), (80, 80, 80), 1)
        y += 8

        cv2.putText(frame, "RECENT EVENTS", (x0 + 10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)
        y += gap + 2

        recent = detector.get_recent_events(limit=12)
        if not recent:
            cv2.putText(frame, "Waiting for detections...", (x0 + 10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (120, 120, 120), 1, cv2.LINE_AA)
            return

        for rec in recent:
            if y > fh - 30:
                break
            sev = rec.get("severity", "LOW")
            cat = rec.get("category", "?")
            cls = rec.get("object_class", "?")
            conf = rec.get("confidence", 0)
            color = SEVERITY_COLOR.get(sev, (150, 150, 150))

            tag = CATEGORY_EMOJI.get(cat, "  ")
            text = f"{tag} {cls:14s} {sev:8s} {int(conf * 100):>3d}%"
            cv2.putText(frame, text, (x0 + 10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.38, color, 1, cv2.LINE_AA)
            y += gap - 2

        y += 10
        if y < fh - 30:
            counts = detector.get_category_counts()
            if counts:
                cv2.line(frame, (x0 + 10, y - 6), (fw - 10, y - 6), (80, 80, 80), 1)
                y += 8
                cv2.putText(frame, "TOTALS", (x0 + 10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (255, 255, 255), 1, cv2.LINE_AA)
                y += gap
                for cat, cnt in sorted(counts.items(), key=lambda x: x[1], reverse=True):
                    if y > fh - 20:
                        break
                    cv2.putText(frame, f"{cat}: {cnt}", (x0 + 10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (180, 180, 180), 1, cv2.LINE_AA)
                    y += gap - 4

    @staticmethod
    def help_overlay(frame: np.ndarray):
        fh, fw = frame.shape[:2]
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (fw, fh), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)

        lines = [
            "KEYBOARD SHORTCUTS",
            "",
            "Q / Esc     Quit",
            "SPACE       Pause / resume",
            "S           Save screenshot",
            "R           Reset event log & counters",
            "H           Toggle this help",
            "+           Raise confidence +5%",
            "-           Lower confidence -5%",
            "",
            "Detection categories:",
            "  !! WEAPON          (CRITICAL / HIGH)",
            "  !? SECURITY_THREAT (HIGH)",
            "  >> PARCEL          (INFO -> MEDIUM)",
            "  ++ MOBILITY_AID    (INFO)",
            "  .. OPERATIONAL     (LOW)",
        ]

        y = fh // 2 - len(lines) * 12
        for line in lines:
            bold = line and not line.startswith(" ") and line == line.upper()
            color = (130, 220, 130) if bold else (220, 220, 220)
            scale = 0.55 if bold else 0.45
            thick = 2 if bold else 1
            cv2.putText(frame, line, (fw // 2 - 180, y), cv2.FONT_HERSHEY_SIMPLEX, scale, color, thick, cv2.LINE_AA)
            y += 24

    @staticmethod
    def paused(frame: np.ndarray):
        fh, fw = frame.shape[:2]
        cv2.putText(frame, "PAUSED", (fw // 2 - 60, fh // 2), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 3, cv2.LINE_AA)


def main() -> None:
    args = parse_args()

    print(f"\nLoading {args.base_model}...")
    detector = ObjectDetector(
        weapon_model_path=args.weapon_model,
        base_model=args.base_model,
        confidence=args.confidence,
        frame_threshold=args.frame_threshold,
        unattended_minutes=args.unattended_minutes,
    )
    if not detector.is_ready:
        raise SystemExit("ObjectDetector not ready. Check ultralytics install and model weights.")

    source = FrameSource(args)
    print(f"Source: {source.label}")
    print("Press H for keyboard shortcuts\n")

    show_help = False
    paused = False
    frame_count = 0
    t_start = time.time()

    WINDOW = "FaceDoor Object Detection"
    cv2.namedWindow(WINDOW, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(WINDOW, args.width, args.height)

    last_frame = None

    while True:
        if not paused:
            ok, frame = source.read()
            if not ok or frame is None:
                if source.is_images:
                    break
                print("Frame read failed; stopping.")
                break
            last_frame = frame.copy()

            events = detector.process_frame(frame)
            frame_count += 1

            elapsed = time.time() - t_start
            fps_val = frame_count / elapsed if elapsed > 0 else 0.0

            if any(e.severity == "CRITICAL" for e in events):
                HUD.banner(frame, "CRITICAL DETECTION", (40, 40, 220))
            elif events:
                HUD.banner(frame, f"{len(events)} event(s) confirmed", (0, 140, 220))
            else:
                HUD.banner(frame, "Monitoring...", (60, 110, 60))

            HUD.boxes(frame, events)
            HUD.sidebar(frame, detector, detector.confidence, source.label)
            HUD.fps(frame, fps_val)

            if events:
                for e in events:
                    print(f"  [{e.severity:8s}] {e.category:18s} {e.object_class:16s} {e.confidence:.0%}")
        else:
            frame = last_frame.copy() if last_frame is not None else np.zeros((args.height, args.width, 3), dtype=np.uint8)
            HUD.paused(frame)
            HUD.sidebar(frame, detector, detector.confidence, source.label)

        if show_help:
            HUD.help_overlay(frame)

        cv2.imshow(WINDOW, frame)

        wait_ms = 500 if (source.is_images and not paused) else 1
        key = cv2.waitKey(wait_ms) & 0xFF

        if key in (ord("q"), 27):
            break
        elif key == ord(" "):
            paused = not paused
            print("Paused." if paused else "Resumed.")
        elif key == ord("h"):
            show_help = not show_help
        elif key == ord("r"):
            detector._frame_counts.clear()
            detector._first_seen.clear()
            detector._ema_confidence.clear()
            detector._event_log.clear()
            frame_count = 0
            t_start = time.time()
            print("Reset: counters, event log, and EMA cleared.")
        elif key == ord("s"):
            ss_dir = ROOT / "screenshots"
            ss_dir.mkdir(exist_ok=True)
            ts = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
            out = str(ss_dir / f"detect_{ts}.jpg")
            cv2.imwrite(out, frame)
            print(f"Screenshot saved: {out}")
        elif key in (ord("+"), ord("=")):
            detector.confidence = min(0.90, detector.confidence + 0.05)
            print(f"Confidence floor: {detector.confidence:.0%}")
        elif key in (ord("-"), ord("_")):
            detector.confidence = max(0.05, detector.confidence - 0.05)
            print(f"Confidence floor: {detector.confidence:.0%}")

    source.release()
    cv2.destroyAllWindows()

    elapsed = time.time() - t_start
    counts = detector.get_category_counts()
    total = sum(counts.values())

    print(f"\n{'='*50}")
    print(f"Session summary  ({elapsed:.1f}s, {frame_count} frames)")
    print(f"{'='*50}")
    if counts:
        for cat, cnt in sorted(counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  {cat:20s}  {cnt}")
        print(f"  {'TOTAL':20s}  {total}")
    else:
        print("  No objects detected.")
    print()


if __name__ == "__main__":
    main()
