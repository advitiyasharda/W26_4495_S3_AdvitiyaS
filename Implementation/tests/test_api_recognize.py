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

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        cv2.imshow("Face Recognition API Test", frame)
        key = cv2.waitKey(100 if args.continuous else 1) & 0xFF

        if key == ord("q") or key == 27:
            break
        if key == ord(" ") or args.continuous:
            if args.continuous:
                time.sleep(2)
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
                print(f"  → {name}  confidence={confidence:.2f}  access_granted={granted}")
            except urllib.error.HTTPError as e:
                body = e.read().decode() if e.fp else ""
                try:
                    err = json.loads(body).get("error", body) if body else str(e)
                except Exception:
                    err = body or str(e)
                print(f"  → ERROR: {e.code} - {err}")
            except urllib.error.URLError as e:
                if "Connection refused" in str(e) or "nodename nor servname" in str(e):
                    print("  → ERROR: Cannot reach API. Is the backend running? (FLASK_PORT=5001 python3 main.py)")
                else:
                    print(f"  → ERROR: {e}")
            except Exception as e:
                print(f"  → ERROR: {e}")
            if not args.continuous:
                continue

    cap.release()
    cv2.destroyAllWindows()
    print("Done.")


if __name__ == "__main__":
    main()
