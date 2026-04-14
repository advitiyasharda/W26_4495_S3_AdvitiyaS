#!/usr/bin/env python3
"""
Test the /api/recognize endpoint with a live webcam frame.
Backend must be running: FLASK_PORT=5001 python3 main.py

Usage (from project root):
  python tests/test_api_recognize.py              # one snapshot when you press SPACE
  python tests/test_api_recognize.py --continuous # send a frame every 2 seconds
"""
import argparse
import base64
import json
import sys
import time
import urllib.request

import cv2

API_BASE = "http://localhost:5001"


def main():
    parser = argparse.ArgumentParser(description="Test POST /api/recognize with webcam")
    parser.add_argument(
        "--continuous",
        action="store_true",
        help="Send a frame every 2 seconds instead of on SPACE",
    )
    parser.add_argument("--api", default=API_BASE, help=f"API base URL (default: {API_BASE})")
    args = parser.parse_args()

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("ERROR: No webcam found.")
        sys.exit(1)

    url = f"{args.api.rstrip('/')}/api/recognize"
    print(f"Testing {url}")
    print("Press SPACE to capture and recognize (or use --continuous)")
    print("Press Q to quit.\n")
    last_faces = []
    last_summary = "Waiting for recognition..."
    last_capture_ts = 0.0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Draw last-known recognition boxes/labels on the live frame
        for face in last_faces:
            try:
                x, y, w, h = face.get("face_location", [0, 0, 0, 0])
                granted = bool(face.get("access_granted", False))
                name = face.get("name", "Unknown")
                conf = float(face.get("confidence", 0.0))
                color = (0, 255, 0) if granted else (0, 80, 255)
                cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
                label = f"{name} ({conf:.2f})"
                cv2.putText(frame, label, (x, max(24, y - 10)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.65, color, 2)
            except Exception:
                continue

        cv2.putText(frame, last_summary, (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(frame, "SPACE=recognize  Q=quit", (10, 62),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (210, 210, 210), 1)

        cv2.imshow("Face Recognition API Test", frame)
        key = cv2.waitKey(100 if args.continuous else 1) & 0xFF

        if key == ord("q") or key == 27:
            break
        if key == ord(" ") or args.continuous:
            if args.continuous:
                now = time.time()
                if (now - last_capture_ts) < 2.0:
                    continue
                last_capture_ts = now
            # Encode frame as high-quality JPEG (reduces loss vs default; helps recognition)
            _, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 98])
            b64 = base64.b64encode(buf.tobytes()).decode("utf-8")
            try:
                req = urllib.request.Request(
                    url,
                    data=json.dumps({"frame": b64}).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=10) as r:
                    data = json.loads(r.read().decode())
                name = data.get("name", "?")
                confidence = data.get("confidence", 0)
                granted = data.get("access_granted", False)
                faces = data.get("faces", [])
                last_faces = faces if isinstance(faces, list) else []
                face_count = data.get("face_count", len(last_faces))
                last_summary = f"Detected: {name} | conf={confidence:.2f} | faces={face_count} | access={granted}"
                print(f"  → {name}  confidence={confidence:.2f}  access_granted={granted}")
            except urllib.error.HTTPError as e:
                body = e.read().decode() if e.fp else ""
                try:
                    err = json.loads(body).get("error", body) if body else str(e)
                except Exception:
                    err = body or str(e)
                last_faces = []
                last_summary = f"API ERROR {e.code}: {err}"
                print(f"  → ERROR: {e.code} - {err}")
            except urllib.error.URLError as e:
                if "Connection refused" in str(e) or "nodename nor servname" in str(e):
                    last_faces = []
                    last_summary = "API offline: start backend on port 5001"
                    print("  → ERROR: Cannot reach API. Is the backend running? (FLASK_PORT=5001 python3 main.py)")
                else:
                    last_faces = []
                    last_summary = f"Network error: {e}"
                    print(f"  → ERROR: {e}")
            except Exception as e:
                last_faces = []
                last_summary = f"Unexpected error: {e}"
                print(f"  → ERROR: {e}")
            if not args.continuous:
                continue

    cap.release()
    cv2.destroyAllWindows()
    print("Done.")


if __name__ == "__main__":
    main()
