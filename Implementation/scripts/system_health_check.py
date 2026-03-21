"""
System health check for demo readiness.

Usage:
  python scripts/system_health_check.py
"""

from pathlib import Path
import sqlite3
import json
from urllib import request, error

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "doorface.db"
POSE_MODEL = BASE_DIR / "models" / "pose_landmarker.task"
LSTM_MODEL = BASE_DIR / "models" / "fall_lstm.keras"
LSTM_SCALER = BASE_DIR / "models" / "fall_lstm_scaler.pkl"
MODEL_INFO = BASE_DIR / "models" / "model_info.json"
API_BASE = "http://localhost:5001/api"


def check_db():
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.fetchone()
        conn.close()
        return True, f"DB OK ({DB_PATH})"
    except Exception as exc:
        return False, f"DB FAIL: {exc}"


def check_file(path: Path, required: bool = True):
    exists = path.exists()
    if exists:
        return True, f"FOUND: {path}"
    if required:
        return False, f"MISSING: {path}"
    return True, f"OPTIONAL MISSING: {path}"


def fetch_json(url: str):
    try:
        with request.urlopen(url, timeout=5) as resp:
            body = resp.read().decode("utf-8")
            return True, json.loads(body)
    except error.URLError as exc:
        return False, f"HTTP FAIL: {exc}"
    except Exception as exc:
        return False, f"PARSE FAIL: {exc}"


def main():
    checks = []
    checks.append(("Database", *check_db()))
    checks.append(("Pose model", *check_file(POSE_MODEL, required=True)))
    checks.append(("LSTM model", *check_file(LSTM_MODEL, required=False)))
    checks.append(("LSTM scaler", *check_file(LSTM_SCALER, required=False)))
    checks.append(("Model info", *check_file(MODEL_INFO, required=False)))

    ok_api, health = fetch_json(f"{API_BASE}/health")
    checks.append(("API /health", ok_api, health if ok_api else str(health)))
    ok_status, status = fetch_json(f"{API_BASE}/fall/status")
    checks.append(("API /fall/status", ok_status, status if ok_status else str(status)))

    failures = 0
    print("System Health Check")
    print("=" * 60)
    for name, passed, info in checks:
        marker = "PASS" if passed else "FAIL"
        if not passed:
            failures += 1
        print(f"[{marker}] {name}: {info}")

    print("=" * 60)
    if failures:
        print(f"Completed with {failures} failing check(s).")
    else:
        print("All checks passed.")


if __name__ == "__main__":
    main()
