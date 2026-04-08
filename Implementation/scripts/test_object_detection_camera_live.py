#!/usr/bin/env python3
"""
Live webcam tester for the ObjectDetector model.

Runs detection locally (no Flask required) and shows:
1) Live candidate detections from base YOLO model
2) Confirmed security events from ObjectDetector.process_frame()

Usage (run from Implementation/):
  python3 scripts/test_object_detection_camera_live.py
  python3 scripts/test_object_detection_camera_live.py --camera 1
  python3 scripts/test_object_detection_camera_live.py --confidence 0.35 --frame-threshold 2
"""

from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path
from typing import List, Tuple

import cv2
import numpy as np

# Ensure project root (Implementation/) is importable when running this file directly.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from models.object_detection import DetectionEvent, ObjectDetector


COLOR_BY_SEVERITY = {
    "CRITICAL": (40, 40, 220),   # red-ish (BGR)
    "HIGH": (0, 135, 255),       # orange
    "MEDIUM": (0, 200, 255),     # amber
    "INFO": (220, 160, 70),      # blue
    "LOW": (160, 160, 160),      # gray
}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Live object detection camera test")
    p.add_argument("--camera", type=int, default=0, help="OpenCV camera index (default: 0)")
    p.add_argument("--confidence", type=float, default=0.45, help="YOLO confidence threshold (default: 0.45)")
    p.add_argument("--frame-threshold", type=int, default=3, help="Consecutive frames to confirm an event")
    p.add_argument("--unattended-minutes", type=float, default=2.0, help="Escalation timer for unattended items")
    p.add_argument("--base-model", default="yolov8n.pt", help="Base YOLO model path")
    p.add_argument("--weapon-model", default="models/weapon_detector.pt", help="Optional weapon model path")
    p.add_argument("--max-candidates", type=int, default=5, help="Max raw YOLO labels shown in the side panel")
    p.add_argument("--width", type=int, default=960, help="Display width")
    p.add_argument("--height", type=int, default=540, help="Display height")
    return p.parse_args()


def draw_banner(frame: np.ndarray, text: str, color: Tuple[int, int, int]) -> None:
    h, w = frame.shape[:2]
    cv2.rectangle(frame, (0, 0), (w, 42), color, -1)
    cv2.putText(frame, text, (14, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.68, (255, 255, 255), 2, cv2.LINE_AA)


def draw_event_boxes(frame: np.ndarray, events: List[DetectionEvent]) -> None:
    h, w = frame.shape[:2]
    for evt in events:
        x1n, y1n, x2n, y2n = evt.bbox
        x1 = max(0, min(w - 1, int(x1n * w)))
        y1 = max(0, min(h - 1, int(y1n * h)))
        x2 = max(0, min(w - 1, int(x2n * w)))
        y2 = max(0, min(h - 1, int(y2n * h)))
        color = COLOR_BY_SEVERITY.get(evt.severity, (170, 170, 170))

        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        label = f"{evt.object_class} | {evt.category} | {evt.severity} | {int(evt.confidence * 100)}%"
        cv2.putText(
            frame,
            label,
            (x1, max(18, y1 - 8)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.48,
            color,
            2,
            cv2.LINE_AA,
        )


def draw_candidates_panel(
    frame: np.ndarray,
    detector: ObjectDetector,
    candidates: List[Tuple[str, float]],
    max_rows: int,
) -> None:
    h, w = frame.shape[:2]
    panel_w = 320
    x0 = max(0, w - panel_w)
    cv2.rectangle(frame, (x0, 42), (w, h), (245, 245, 245), -1)
    cv2.rectangle(frame, (x0, 42), (w, h), (220, 220, 220), 1)

    y = 66
    line_h = 24
    cv2.putText(frame, "Live candidates (YOLO)", (x0 + 12, y), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (35, 35, 35), 2, cv2.LINE_AA)
    y += line_h + 2

    if not candidates:
        cv2.putText(frame, "No detections this frame", (x0 + 12, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (120, 120, 120), 1, cv2.LINE_AA)
        y += line_h
    else:
        for cls_name, conf in candidates[:max_rows]:
            # Reuse model classifier to show mapped category/severity readability
            # cls_id is unknown here from this tuple path, so fallback classify by class name only.
            category, severity = detector._classify(cls_name, -1)  # pylint: disable=protected-access
            cat = category or "IGNORE"
            sev = severity or "-"
            text = f"{cls_name:16s} {int(conf * 100):>2d}%  {cat}/{sev}"
            cv2.putText(frame, text, (x0 + 12, y), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (55, 55, 55), 1, cv2.LINE_AA)
            y += line_h

    y += 8
    cv2.putText(frame, "Confirmed events", (x0 + 12, y), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (35, 35, 35), 2, cv2.LINE_AA)
    y += line_h
    recent = detector.get_recent_events(limit=4)
    if not recent:
        cv2.putText(frame, "None yet", (x0 + 12, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (120, 120, 120), 1, cv2.LINE_AA)
        return

    for rec in recent:
        sev = rec.get("severity", "LOW")
        color = COLOR_BY_SEVERITY.get(sev, (150, 150, 150))
        text = f"{rec.get('object_class','?')}  {sev}  {int(float(rec.get('confidence', 0))*100)}%"
        cv2.putText(frame, text, (x0 + 12, y), cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1, cv2.LINE_AA)
        y += line_h


def extract_candidates(detector: ObjectDetector, frame: np.ndarray) -> List[Tuple[str, float]]:
    out: List[Tuple[str, float]] = []
    if not detector.is_ready:
        return out
    model = detector._model  # pylint: disable=protected-access
    if model is None:
        return out
    results = model(frame, conf=detector.confidence, verbose=False)
    for result in results:
        for box in result.boxes:
            cls_id = int(box.cls[0])
            conf = float(box.conf[0])
            cls_name = model.names.get(cls_id, str(cls_id))
            out.append((cls_name, conf))
    out.sort(key=lambda x: x[1], reverse=True)
    return out


def main() -> None:
    args = parse_args()

    detector = ObjectDetector(
        weapon_model_path=args.weapon_model,
        base_model=args.base_model,
        confidence=args.confidence,
        frame_threshold=args.frame_threshold,
        unattended_minutes=args.unattended_minutes,
    )
    if not detector.is_ready:
        raise SystemExit("ObjectDetector is not ready. Ensure ultralytics and YOLO weights are available.")

    cap = cv2.VideoCapture(args.camera)
    if not cap.isOpened():
        raise SystemExit(f"Could not open camera index {args.camera}")

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, args.width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, args.height)

    print("\nLive object detection started.")
    print("Keys: Q = quit, S = screenshot, R = reset event history\n")

    while True:
        ok, frame = cap.read()
        if not ok:
            print("Camera frame read failed; stopping.")
            break

        events = detector.process_frame(frame)
        candidates = extract_candidates(detector, frame)

        if any(e.severity == "CRITICAL" for e in events):
            draw_banner(frame, "CRITICAL OBJECT DETECTED", (40, 40, 220))
        elif events:
            draw_banner(frame, f"{len(events)} object event(s) detected", (0, 160, 255))
        else:
            draw_banner(frame, "Monitoring... no confirmed events", (75, 130, 75))

        draw_event_boxes(frame, events)
        draw_candidates_panel(frame, detector, candidates, args.max_candidates)

        cv2.imshow("FaceDoor Object Detection Test", frame)
        key = cv2.waitKey(1) & 0xFF

        if key in (ord("q"), 27):
            break
        if key == ord("r"):
            # Reset rolling history counters
            detector._frame_counts.clear()  # pylint: disable=protected-access
            detector._first_seen.clear()    # pylint: disable=protected-access
            detector._event_log.clear()     # pylint: disable=protected-access
            print("Detector counters and event log reset.")
        if key == ord("s"):
            ts = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
            out = f"screenshots/object_detect_{ts}.jpg"
            cv2.imwrite(out, frame)
            print(f"Saved screenshot: {out}")

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()

