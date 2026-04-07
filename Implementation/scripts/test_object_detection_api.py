#!/usr/bin/env python3
"""
Quick test for POST /api/objects/detect.

The server requires the same class to appear in FRAME_THRESHOLD consecutive
frames (default 3) before it returns a detection — so this script sends the
same image 3 times in a row.

Usage (from Implementation/ with Flask on 5001):

  python3 scripts/test_object_detection_api.py /path/to/photo.jpg

  # Or use a remote URL (downloads to memory):
  python3 scripts/test_object_detection_api.py --url https://example.com/photo.jpg
"""
from __future__ import annotations

import argparse
import base64
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path


def encode_image_jpeg(path: Path) -> str:
    import cv2

    img = cv2.imread(str(path))
    if img is None:
        raise SystemExit(f"Could not read image: {path}")
    ok, buf = cv2.imencode(".jpg", img, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
    if not ok:
        raise SystemExit("cv2.imencode failed")
    return base64.b64encode(buf).decode("ascii")


def decode_frame_from_url(url: str) -> str:
    import cv2
    import numpy as np

    req = urllib.request.Request(url, headers={"User-Agent": "FaceDoor-test/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = np.frombuffer(resp.read(), dtype=np.uint8)
    img = cv2.imdecode(data, cv2.IMREAD_COLOR)
    if img is None:
        raise SystemExit("Could not decode image from URL")
    ok, buf = cv2.imencode(".jpg", img, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
    if not ok:
        raise SystemExit("cv2.imencode failed")
    return base64.b64encode(buf).decode("ascii")


def post_detect(api_base: str, frame_b64: str) -> dict:
    import urllib.request

    url = api_base.rstrip("/") + "/api/objects/detect"
    body = json.dumps({"frame": frame_b64}).encode()
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode())


def main() -> None:
    p = argparse.ArgumentParser(description="Test /api/objects/detect")
    p.add_argument(
        "image",
        nargs="?",
        help="Path to a JPEG/PNG file (or use --url)",
    )
    p.add_argument(
        "--url",
        dest="remote_url",
        help="Download image from URL instead of reading a local file",
    )
    p.add_argument(
        "--api",
        default="http://127.0.0.1:5001",
        help="Flask API base URL (default: http://127.0.0.1:5001)",
    )
    p.add_argument(
        "--frames",
        type=int,
        default=3,
        help="Number of identical POSTs (default: 3, matches default frame threshold)",
    )
    args = p.parse_args()

    if args.remote_url:
        b64 = decode_frame_from_url(args.remote_url)
    elif args.image:
        b64 = encode_image_jpeg(Path(args.image))
    else:
        p.error("Provide a local image path or --url")

    for i in range(1, args.frames + 1):
        try:
            out = post_detect(args.api, b64)
        except urllib.error.HTTPError as e:
            print(f"HTTP {e.code}: {e.read().decode()}", file=sys.stderr)
            raise SystemExit(1)
        except urllib.error.URLError as e:
            print(f"Connection failed: {e}", file=sys.stderr)
            print("Is the Flask server running? (python main.py from Implementation/)", file=sys.stderr)
            raise SystemExit(1)
        print(f"POST {i}/{args.frames}: count={out.get('count', 0)}")
        if out.get("detections"):
            print(json.dumps(out, indent=2))
            return

    print(json.dumps(out, indent=2))
    print(
        "\n(No detections after all frames — try a clearer photo with people, bags, "
        "bottles, etc., or lower OBJECT_DETECTION_CONFIDENCE in config.)",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
