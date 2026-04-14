#!/usr/bin/env python3
"""
Test harness for POST /api/objects/detect.

Sends one or more images to the running Flask API and prints a colour-coded
summary.  Supports single files, URLs, and entire folders.

Usage (from Implementation/ with Flask on 5001):

  # Single image
  python3 scripts/test_object_detection_api.py photo.jpg

  # Remote URL
  python3 scripts/test_object_detection_api.py --url https://example.com/photo.jpg

  # Every image in a folder
  python3 scripts/test_object_detection_api.py --folder test_images/

  # Custom frames & API host
  python3 scripts/test_object_detection_api.py photo.jpg --frames 5 --api http://localhost:5001
"""
from __future__ import annotations

import argparse
import base64
import glob
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import List, Tuple

SEVERITY_COLOR = {
    "CRITICAL": "\033[91m",
    "HIGH":     "\033[93m",
    "MEDIUM":   "\033[33m",
    "INFO":     "\033[96m",
    "LOW":      "\033[90m",
}
BOLD  = "\033[1m"
DIM   = "\033[2m"
RESET = "\033[0m"
GREEN = "\033[92m"
RED   = "\033[91m"


def color_sev(severity: str) -> str:
    c = SEVERITY_COLOR.get(severity, "")
    return f"{c}{BOLD}{severity}{RESET}"


def encode_image(path: Path) -> str:
    import cv2

    img = cv2.imread(str(path))
    if img is None:
        raise SystemExit(f"Could not read image: {path}")
    ok, buf = cv2.imencode(".jpg", img, [int(cv2.IMWRITE_JPEG_QUALITY), 92])
    if not ok:
        raise SystemExit("cv2.imencode failed")
    return base64.b64encode(buf).decode("ascii")


def encode_url(url: str) -> str:
    import cv2
    import numpy as np

    req = urllib.request.Request(url, headers={"User-Agent": "FaceDoor-test/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = np.frombuffer(resp.read(), dtype=np.uint8)
    img = cv2.imdecode(data, cv2.IMREAD_COLOR)
    if img is None:
        raise SystemExit("Could not decode image from URL")
    ok, buf = cv2.imencode(".jpg", img, [int(cv2.IMWRITE_JPEG_QUALITY), 92])
    if not ok:
        raise SystemExit("cv2.imencode failed")
    return base64.b64encode(buf).decode("ascii")


def post_detect(api_base: str, frame_b64: str) -> dict:
    url = api_base.rstrip("/") + "/api/objects/detect"
    body = json.dumps({"frame": frame_b64}).encode()
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode())


def get_status(api_base: str) -> dict | None:
    try:
        url = api_base.rstrip("/") + "/api/objects/status"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode())
    except Exception:
        return None


def collect_images(args) -> List[Tuple[str, str]]:
    """Return list of (label, base64) pairs."""
    pairs: List[Tuple[str, str]] = []

    if args.folder:
        folder = Path(args.folder)
        exts = ("*.jpg", "*.jpeg", "*.png", "*.bmp", "*.webp")
        files = []
        for ext in exts:
            files.extend(glob.glob(str(folder / ext)))
        files.sort()
        if not files:
            raise SystemExit(f"No images found in {args.folder}")
        for f in files:
            pairs.append((Path(f).name, encode_image(Path(f))))

    elif args.remote_url:
        pairs.append((args.remote_url.split("/")[-1] or "url_image", encode_url(args.remote_url)))

    elif args.image:
        pairs.append((Path(args.image).name, encode_image(Path(args.image))))

    else:
        raise SystemExit("Provide an image path, --url, or --folder")

    return pairs


def run_test(label: str, b64: str, api_base: str, num_frames: int) -> dict | None:
    """Send num_frames POSTs for a single image and return the first detection result."""
    print(f"\n{BOLD}--- {label} ---{RESET}")

    for i in range(1, num_frames + 1):
        t0 = time.time()
        try:
            out = post_detect(api_base, b64)
        except urllib.error.HTTPError as e:
            print(f"  {RED}HTTP {e.code}: {e.read().decode()}{RESET}", file=sys.stderr)
            return None
        except urllib.error.URLError as e:
            print(f"  {RED}Connection failed: {e}{RESET}", file=sys.stderr)
            print(f"  {DIM}Is Flask running? (python main.py from Implementation/){RESET}", file=sys.stderr)
            return None
        ms = (time.time() - t0) * 1000

        count = out.get("count", 0)
        dets = out.get("detections", [])

        if dets:
            print(f"  Frame {i}/{num_frames}  {GREEN}{count} detection(s){RESET}  {DIM}({ms:.0f}ms){RESET}")
            for d in dets:
                sev = color_sev(d["severity"])
                cat = d["category"]
                cls = d["object_class"]
                conf = d["confidence"]
                print(f"    {sev:>30s}  {cat:18s}  {cls:16s}  {conf:.0%}")
            return out
        else:
            print(f"  Frame {i}/{num_frames}  {DIM}0 detections  ({ms:.0f}ms){RESET}")

    print(f"  {DIM}No detections after {num_frames} frames.{RESET}")
    return out


def main() -> None:
    p = argparse.ArgumentParser(
        description="Test /api/objects/detect",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("image", nargs="?", help="Path to a JPEG/PNG file")
    p.add_argument("--url", dest="remote_url", help="Download image from URL")
    p.add_argument("--folder", help="Test all images in a folder")
    p.add_argument("--api", default="http://127.0.0.1:5001", help="Flask API base URL")
    p.add_argument("--frames", type=int, default=5, help="POSTs per image (default 5)")
    args = p.parse_args()

    if not args.image and not args.remote_url and not args.folder:
        p.error("Provide an image path, --url, or --folder")

    print(f"{BOLD}FaceDoor Object Detection API Test{RESET}")
    print(f"API: {args.api}")

    status = get_status(args.api)
    if status:
        ready = status.get("detector_ready", False)
        weapon = status.get("weapon_model_ready", False)
        conf = status.get("confidence", "?")
        ft = status.get("frame_threshold", "?")
        tag = f"{GREEN}Ready{RESET}" if ready else f"{RED}Offline{RESET}"
        print(f"Detector: {tag}  |  Weapon model: {'yes' if weapon else 'no'}  |  Conf: {conf}  |  Threshold: {ft} frames")
    else:
        print(f"{RED}Cannot reach API — is Flask running?{RESET}")
        sys.exit(1)

    images = collect_images(args)
    print(f"Images to test: {len(images)}")

    results: List[Tuple[str, dict | None]] = []
    t_total = time.time()

    for label, b64 in images:
        out = run_test(label, b64, args.api, args.frames)
        results.append((label, out))

    elapsed = time.time() - t_total

    print(f"\n{'='*60}")
    print(f"{BOLD}SUMMARY{RESET}  ({len(results)} image(s), {elapsed:.1f}s total)")
    print(f"{'='*60}")

    detected = 0
    missed = 0
    for label, out in results:
        dets = (out or {}).get("detections", [])
        if dets:
            detected += 1
            top = dets[0]
            sev = color_sev(top["severity"])
            print(f"  {GREEN}PASS{RESET}  {label:30s}  {top['object_class']:14s}  {sev}  {top['confidence']:.0%}")
        else:
            missed += 1
            print(f"  {DIM}MISS  {label:30s}  (no detection){RESET}")

    print()
    print(f"  Detected: {detected}/{len(results)}    Missed: {missed}/{len(results)}")

    if missed:
        print(f"\n  {DIM}Tip: try --frames 8 for stubborn images, or lower OBJECT_DETECTION_CONFIDENCE in config.py{RESET}")

    print()


if __name__ == "__main__":
    main()
