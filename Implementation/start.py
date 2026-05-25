#!/usr/bin/env python3
"""
FaceDoor — One-click installer and launcher
Works on Windows and macOS/Linux.

Usage:
    python start.py          # from anywhere — paths are resolved automatically
"""

import os
import platform
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────────────────
IMPL     = Path(__file__).resolve().parent   # Implementation/
FRONTEND = IMPL / "frontend"
VENV     = IMPL / "venv"
REQS     = IMPL / "requirements.txt"

IS_WIN  = platform.system() == "Windows"
VENV_PY = VENV / ("Scripts" / Path("python.exe") if IS_WIN else Path("bin/python3"))

# ── Colour helpers (gracefully disabled on plain Windows terminals) ────────────
_ANSI = not IS_WIN or bool(os.environ.get("WT_SESSION") or os.environ.get("TERM"))

def _c(code: str, text: str) -> str:
    return f"\033[{code}m{text}\033[0m" if _ANSI else text

ok   = lambda t: _c("32;1", t)
warn = lambda t: _c("33;1", t)
err  = lambda t: _c("31;1", t)
info = lambda t: _c("36", t)
bold = lambda t: _c("1", t)
dim  = lambda t: _c("2", t)


# ── UI helpers ────────────────────────────────────────────────────────────────
def header() -> None:
    print()
    print(bold("═" * 60))
    print(bold("DoorFace  —  Smart Door Security System"))
    print(bold("═" * 60))
    print()

def step(msg: str) -> None:
    print(f"\n{info('▶')} {bold(msg)}")

def done(msg: str) -> None:
    print(f"  {ok('✓')} {msg}")

def skip(msg: str) -> None:
    print(f"  {dim('–')} {msg}")


# ── Pre-flight checks ─────────────────────────────────────────────────────────
def check_python() -> None:
    step("Checking Python version")
    v = sys.version_info
    label = f"Python {v.major}.{v.minor}.{v.micro}"
    if v.major < 3 or (v.major == 3 and v.minor < 10):
        print(f"  {warn(label + '  ← 3.10+ recommended (3.11 ideal)')}")
    else:
        done(label)


def check_node() -> bool:
    step("Checking Node.js / npm")
    if not shutil.which("node"):
        print(f"  {err('Node.js not found.')}")
        print(f"  {warn('Install from https://nodejs.org (v18 LTS+) then re-run.')}")
        print(f"  {warn('Frontend will be skipped.')}")
        return False
    try:
        node_v = subprocess.check_output(["node", "--version"], text=True).strip()
        npm_v  = subprocess.check_output(["npm",  "--version"], text=True).strip()
        done(f"Node {node_v}  /  npm v{npm_v}")
        return True
    except Exception:
        done("Node.js found (could not read version)")
        return True


# ── Setup steps ───────────────────────────────────────────────────────────────
def ensure_venv() -> None:
    step("Virtual environment")
    if VENV_PY.exists():
        skip(f"venv already exists at {VENV}")
        return
    print(f"  {info('Creating venv …')}")
    subprocess.check_call([sys.executable, "-m", "venv", str(VENV)])
    done("venv created")


def install_python_deps() -> None:
    step("Python dependencies  (requirements.txt)")
    # Quick probe: if key packages are importable we can skip
    probe = subprocess.run(
        [str(VENV_PY), "-c", "import flask, cv2, mediapipe, ultralytics, requests"],
        capture_output=True,
    )
    if probe.returncode == 0:
        skip("All packages already installed")
        return
    print(f"  {info('Running pip install …  (this may take a few minutes on first run)')}")
    # Upgrade pip silently first
    subprocess.check_call(
        [str(VENV_PY), "-m", "pip", "install", "--upgrade", "pip", "-q"]
    )
    subprocess.check_call(
        [str(VENV_PY), "-m", "pip", "install", "-r", str(REQS)],
        cwd=str(IMPL),
    )
    done("Python packages installed")


def install_npm_deps() -> None:
    step("Frontend dependencies  (npm install)")
    nm = FRONTEND / "node_modules"
    lock = FRONTEND / "package-lock.json"
    if nm.exists() and lock.exists():
        skip("node_modules already present")
        return
    print(f"  {info('Running npm install …  (also downloads the MediaPipe pose model)')}")
    npm_cmd = "npm.cmd" if IS_WIN else "npm"
    subprocess.check_call([npm_cmd, "install"], cwd=str(FRONTEND))
    done("npm packages installed")


# ── Launch helpers ────────────────────────────────────────────────────────────
def _make_env() -> dict:
    env = os.environ.copy()
    env["FLASK_PORT"] = "5001"
    if platform.system() == "darwin":
        env.setdefault("OPENCV_VIDEOIO_PRIORITY_AVFOUNDATION", "1000")
    return env


def start_backend() -> subprocess.Popen:
    print(f"\n  {info('Starting Flask backend')}  →  {bold('http://localhost:5001')}")
    return subprocess.Popen(
        [str(VENV_PY), "main.py"],
        cwd=str(IMPL),
        env=_make_env(),
    )


def start_frontend() -> subprocess.Popen:
    print(f"  {info('Starting Next.js frontend')}  →  {bold('http://localhost:3000')}")
    npm_cmd = "npm.cmd" if IS_WIN else "npm"
    return subprocess.Popen(
        [npm_cmd, "run", "dev"],
        cwd=str(FRONTEND),
    )


def wait_for_processes(procs: list) -> None:
    print()
    print(ok("  All services running.  Press Ctrl+C to stop everything."))
    print()

    def _shutdown(signum=None, frame=None):
        print(warn("\n\n  Shutting down …"))
        for p in procs:
            try:
                p.terminate()
            except Exception:
                pass
        time.sleep(1)
        for p in procs:
            try:
                if p.poll() is None:
                    p.kill()
            except Exception:
                pass
        print(ok("  Stopped cleanly.  Goodbye!"))
        sys.exit(0)

    signal.signal(signal.SIGINT, _shutdown)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, _shutdown)

    while True:
        for p in procs:
            if p.poll() is not None:
                print(err(f"\n  A process exited unexpectedly (code {p.returncode})."))
                _shutdown()
        time.sleep(1)


# ── Main ──────────────────────────────────────────────────────────────────────
def main() -> None:
    header()

    # Sanity check — make sure we're in the right place
    if not REQS.exists():
        print(err(f"  Cannot find requirements.txt at:  {REQS}"))
        print(err("  The start.py file may have been moved incorrectly."))
        sys.exit(1)

    # ── Step 1: checks ───────────────────────────────────────────────────────
    check_python()
    node_ok = check_node()

    # ── Step 2: install ──────────────────────────────────────────────────────
    ensure_venv()
    install_python_deps()
    if node_ok:
        install_npm_deps()
    else:
        skip("Skipping npm install (Node.js not available)")

    # ── Step 3: ask what to run ──────────────────────────────────────────────
    print()
    print(bold("─" * 60))
    print(bold("  What would you like to start?"))
    print(bold("─" * 60))
    print(f"  {bold('1')}  Backend only   {dim('(Flask API  →  http://localhost:5001)')}")
    print(f"  {bold('2')}  Frontend only  {dim('(Next.js    →  http://localhost:3000)')}")
    print(f"  {bold('3')}  Both           {ok('← recommended — full dashboard + API')}")
    print(f"  {bold('4')}  Exit")
    print()

    while True:
        choice = input("  Enter choice [1-4]: ").strip()
        if choice in ("1", "2", "3", "4"):
            break
        print(warn("  Please enter 1, 2, 3, or 4."))

    if choice == "4":
        print(info("\n  Exiting. Run start.py again whenever you want to start."))
        sys.exit(0)

    # ── Step 4: launch ───────────────────────────────────────────────────────
    print()
    print(bold("─" * 60))
    procs = []

    if choice in ("1", "3"):
        procs.append(start_backend())

    if choice in ("2", "3"):
        if not node_ok:
            print(err("  Cannot start frontend: Node.js is not installed."))
            if choice == "2":
                sys.exit(1)
        else:
            if choice == "3":
                time.sleep(1)   # let backend start first
            procs.append(start_frontend())

    wait_for_processes(procs)


if __name__ == "__main__":
    main()
