"""
Fall Detection — Live Camera Script (Phase 1: Rules-Based)

Run this script to start real-time fall detection using your webcam.
Falls are detected for ANY person in view — registered or unknown.

Usage:
    python scripts/fall_detection_camera.py
    python scripts/fall_detection_camera.py --camera 1          # use camera index 1
    python scripts/fall_detection_camera.py --no-display        # headless, logs only
    python scripts/fall_detection_camera.py --log falls.csv     # save fall events to CSV
    python scripts/fall_detection_camera.py --no-api            # skip dashboard logging
    python scripts/fall_detection_camera.py --api-url http://localhost:5001

Controls (when window is open):
    Q  — quit
    S  — save a screenshot of the current frame
    R  — reset fall history / cooldown

What it does:
    Opens your webcam, runs MediaPipe Pose on every frame, applies
    three rules (hip height, torso angle, drop velocity) to detect falls.
    Works for ANY person — no face recognition required.

    When a fall is detected:
      - A red "FALL DETECTED" banner appears on screen
      - The event is logged in the terminal
      - The fall metadata is POSTed to /api/fall/log on the Flask server
        so it immediately appears on the dashboard
"""

import sys
import os
import time
import argparse
import logging
import csv
import threading
from datetime import datetime
from pathlib import Path

try:
    import requests as _requests
    _HAS_REQUESTS = True
except ImportError:
    _HAS_REQUESTS = False

# Make sure the Implementation root is on the path regardless of where
# the script is launched from
SCRIPT_DIR  = Path(__file__).resolve().parent          # .../Implementation/scripts
PROJECT_DIR = SCRIPT_DIR.parent                        # .../Implementation
sys.path.insert(0, str(PROJECT_DIR))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("fall_detection_camera")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Real-time fall detection via webcam (rules-based, Phase 1)"
    )
    parser.add_argument(
        "--camera", type=int, default=0,
        help="Camera device index (default: 0)"
    )
    parser.add_argument(
        "--no-display", action="store_true",
        help="Run headless — no OpenCV window, just terminal output"
    )
    parser.add_argument(
        "--log", type=str, default=None, metavar="FILE",
        help="CSV file to append fall events to (e.g. falls.csv)"
    )
    parser.add_argument(
        "--threshold", type=float, default=0.55,
        help="Fall confidence threshold 0–1 (default: 0.55)"
    )
    parser.add_argument(
        "--no-api", action="store_true",
        help="Disable posting falls to the Flask dashboard API"
    )
    parser.add_argument(
        "--api-url", type=str, default="http://localhost:5001",
        help="Base URL of the Flask server (default: http://localhost:5001)"
    )
    return parser.parse_args()


def post_fall_to_api(result, api_url: str) -> None:
    """Fire-and-forget: POST already-detected fall metadata to /api/fall/log.

    Uses /api/fall/log (not /api/fall/detect) so Flask logs the result
    directly — no re-detection needed. Flask's FallDetector would have no
    velocity history and could miss the fall from a single cold frame.

    Works for ANY person — registered or unknown — pose-based detection only.
    """
    if not _HAS_REQUESTS:
        logger.warning(
            "'requests' not installed — cannot post to dashboard. "
            "Run: pip install requests"
        )
        return

    def _post():
        try:
            resp = _requests.post(
                f"{api_url}/api/fall/log",
                json={
                    "confidence":      result.confidence,
                    "reason":          result.reason,
                    "hip_height":      result.hip_height,
                    "torso_angle_deg": result.torso_angle_deg,
                    "hip_velocity":    result.hip_velocity,
                },
                timeout=5,
            )
            if resp.ok:
                logger.info("Fall logged to dashboard (status %d)", resp.status_code)
            else:
                logger.warning(
                    "Dashboard POST returned %d: %s",
                    resp.status_code, resp.text[:200]
                )
        except Exception as exc:
            logger.warning("Could not post fall to dashboard: %s", exc)

    threading.Thread(target=_post, daemon=True).start()


def init_csv_log(filepath: str):
    """Create or append to a CSV log file; write header if new."""
    path = Path(filepath)
    write_header = not path.exists()
    f = open(path, "a", newline="")
    writer = csv.writer(f)
    if write_header:
        writer.writerow([
            "timestamp", "confidence", "hip_height",
            "torso_angle_deg", "hip_velocity", "reason"
        ])
        f.flush()
    logger.info("Logging fall events to %s", path.resolve())
    return writer, f


def log_fall_event(writer, result):
    """Append one row to the CSV log."""
    writer.writerow([
        datetime.now().isoformat(timespec="seconds"),
        result.confidence,
        result.hip_height,
        result.torso_angle_deg,
        result.hip_velocity,
        result.reason,
    ])


def run(args):
    import cv2
    from models.fall_detection import FallDetector

    detector = FallDetector(fall_threshold=args.threshold)

    cap = cv2.VideoCapture(args.camera)
    if not cap.isOpened():
        logger.error("Cannot open camera %d. Try a different --camera index.", args.camera)
        sys.exit(1)

    # Try to set a decent resolution
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    cap.set(cv2.CAP_PROP_FPS, 30)

    actual_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    actual_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    actual_fps = cap.get(cv2.CAP_PROP_FPS)
    logger.info("Camera opened: %dx%d @ %.0f fps", actual_w, actual_h, actual_fps)
    logger.info("Fall threshold set to %.2f", args.threshold)
    if not args.no_display:
        logger.info("Press Q to quit | S to screenshot | R to reset")

    if not args.no_api:
        logger.info("Dashboard logging enabled — falls will POST to %s/api/fall/log", args.api_url)
    else:
        logger.info("Dashboard logging disabled (--no-api)")

    # CSV log setup
    csv_writer = None
    csv_file   = None
    if args.log:
        csv_writer, csv_file = init_csv_log(args.log)

    # Screenshot directory
    screenshots_dir = PROJECT_DIR / "screenshots"
    screenshots_dir.mkdir(exist_ok=True)

    # ── Stats counters ─────────────────────────────────────────────────────
    frame_count  = 0
    fall_count   = 0
    start_time   = time.time()
    last_fall_ts = None

    # ── Main loop ──────────────────────────────────────────────────────────
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                logger.warning("Failed to read frame from camera — retrying…")
                time.sleep(0.1)
                continue

            frame_count += 1
            result = detector.process_frame(frame)

            # ── Handle fall event ──────────────────────────────────────────
            if result and result.is_fall:
                fall_count += 1
                last_fall_ts = datetime.now()
                logger.warning(
                    "[!] FALL DETECTED  conf=%.2f  hip_y=%.2f  angle=%.0f°  vel=%.3f  | %s",
                    result.confidence, result.hip_height,
                    result.torso_angle_deg, result.hip_velocity,
                    result.reason,
                )
                # Post to Flask API → logged to DB → visible on dashboard
                # Works for ANY person (unknown or registered) — pose-based only
                if not args.no_api:
                    post_fall_to_api(result, args.api_url)
                if csv_writer:
                    log_fall_event(csv_writer, result)
                    csv_file.flush()

            # ── Draw overlay ───────────────────────────────────────────────
            if not args.no_display:
                annotated = detector.draw_overlay(frame, result) if result else frame

                # Show running stats in top-right corner
                elapsed = time.time() - start_time
                fps_actual = frame_count / elapsed if elapsed > 0 else 0
                stats = f"FPS:{fps_actual:.1f}  Falls:{fall_count}"
                cv2.putText(annotated, stats,
                            (actual_w - 220, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 0), 2)

                cv2.imshow("Fall Detection (Phase 1 — Rules)", annotated)

                key = cv2.waitKey(1) & 0xFF
                if key == ord("q"):
                    logger.info("Q pressed — stopping.")
                    break
                elif key == ord("s"):
                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                    fname = screenshots_dir / f"fall_screenshot_{ts}.jpg"
                    cv2.imwrite(str(fname), annotated)
                    logger.info("Screenshot saved: %s", fname)
                elif key == ord("r"):
                    detector._hip_y_history.clear()
                    detector._fall_cooldown_frames = 0
                    logger.info("Fall history reset.")
            else:
                # Headless — just log periodically
                if frame_count % 300 == 0:
                    elapsed = time.time() - start_time
                    fps_actual = frame_count / elapsed if elapsed > 0 else 0
                    logger.info(
                        "Running %.0fs | frames=%d fps=%.1f falls=%d",
                        elapsed, frame_count, fps_actual, fall_count
                    )

    except KeyboardInterrupt:
        logger.info("Interrupted by user (Ctrl+C)")
    finally:
        cap.release()
        if not args.no_display:
            cv2.destroyAllWindows()
        if csv_file:
            csv_file.close()
        detector.close()

        elapsed = time.time() - start_time
        logger.info(
            "Session ended — %.0fs, %d frames, %d falls detected",
            elapsed, frame_count, fall_count
        )


if __name__ == "__main__":
    args = parse_args()
    run(args)
