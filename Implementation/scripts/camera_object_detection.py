"""
Live Camera Object Detection — Phase 3

Opens the webcam and shows every object YOLO detects with its name
drawn directly on the bounding box.

Usage (from Implementation/ with venv active):
    python scripts/camera_object_detection.py

Controls:
    Q / ESC — quit
"""

import base64
import sys
import os
import time

import cv2
import numpy as np
import requests

API_BASE    = "http://localhost:5001"
DETECT_URL  = f"{API_BASE}/api/objects/detect"
STATUS_URL  = f"{API_BASE}/api/objects/status"
CAMERA_INDEX = 0
TARGET_FPS   = 3          # API calls per second

# Colour per severity (BGR)
SEVERITY_COL = {
    "CRITICAL": (0,   0,  220),
    "HIGH":     (0,  100, 255),
    "MEDIUM":   (0,  200, 255),
    "INFO":     (220, 150,  0),
    "LOW":      (160, 160, 160),
}
UNTRACKED_COL = (100, 100, 100)   # grey for non-security objects


def encode(frame):
    _, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
    return base64.b64encode(buf).decode()


def get_all_detections(frame):
    """Run the local ObjectDetector to get every YOLO detection."""
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
        from models.object_detection import ObjectDetector
        if not hasattr(get_all_detections, "_det"):
            get_all_detections._det = ObjectDetector()
        return get_all_detections._det.detect_all(frame)
    except Exception as e:
        print("Detector error:", e)
        return []


def get_tracked_detections(frame):
    """Send frame to Flask API and return only security-relevant detections."""
    try:
        r = requests.post(DETECT_URL, json={"frame": encode(frame)}, timeout=5)
        if r.status_code == 200:
            return r.json().get("detections", [])
    except Exception:
        pass
    return []


def draw_label(frame, x1, y1, x2, y2, name, colour):
    """Draw a bounding box with just the object name as the label."""
    h, w = frame.shape[:2]
    x1, y1 = max(0, x1), max(0, y1)
    x2, y2 = min(w, x2), min(h, y2)

    cv2.rectangle(frame, (x1, y1), (x2, y2), colour, 2)

    (tw, th), baseline = cv2.getTextSize(name, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 1)
    label_y = y1 - 6 if y1 - 6 > th else y1 + th + 6

    cv2.rectangle(frame, (x1, label_y - th - 4), (x1 + tw + 6, label_y + baseline), colour, -1)
    cv2.putText(frame, name, (x1 + 3, label_y - 2),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)


def main():
    print("\n🎥  Object Detection — Live Camera")

    # Check server
    try:
        requests.get(STATUS_URL, timeout=3)
    except Exception:
        print(f"   ⚠  Cannot reach {API_BASE} — start Flask first.")
        return

    cap = cv2.VideoCapture(CAMERA_INDEX)
    if not cap.isOpened():
        print("   ❌ Could not open camera.")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    print("   Camera open. Press Q to quit.\n")

    all_dets     = []
    tracked_set  = set()
    last_send    = 0.0
    interval     = 1.0 / TARGET_FPS

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        now = time.time()
        if now - last_send >= interval:
            all_dets    = get_all_detections(frame)
            tracked_dets = get_tracked_detections(frame)
            tracked_set  = {d["object_class"] for d in tracked_dets}
            last_send    = now

        h, w = frame.shape[:2]
        for det in all_dets:
            bbox = det.get("bbox")
            if not bbox or len(bbox) != 4:
                continue

            x1 = int(bbox[0] * w)
            y1 = int(bbox[1] * h)
            x2 = int(bbox[2] * w)
            y2 = int(bbox[3] * h)

            name    = det["object_class"].replace("_", " ")
            sev     = det.get("severity")
            tracked = det["object_class"] in tracked_set

            colour = SEVERITY_COL.get(sev, UNTRACKED_COL) if tracked else UNTRACKED_COL
            draw_label(frame, x1, y1, x2, y2, name, colour)

        cv2.putText(frame, "Q to quit", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1, cv2.LINE_AA)

        cv2.imshow("Object Detection", frame)

        if cv2.waitKey(1) & 0xFF in (ord("q"), ord("Q"), 27):
            break

    cap.release()
    cv2.destroyAllWindows()
    print("   Closed.")


if __name__ == "__main__":
    main()
