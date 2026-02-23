#!/usr/bin/env python3
"""
Clear the SQLite database (access logs, users, threats, audit, etc.).
Does NOT delete any pictures or folders in data/samples/.

Stop the Flask backend before running this, then restart it after.
"""
from pathlib import Path

DB_PATH = Path("data/doorface.db")

def main():
    if not DB_PATH.exists():
        print("No database file found. Nothing to clear.")
        return
    DB_PATH.unlink()
    print("Database cleared (data/doorface.db removed).")
    print("Pictures and folders in data/samples/ were NOT touched.")
    print("Restart the backend (FLASK_PORT=5001 python3 main.py) to create a fresh DB and reload faces from data/samples/.")

if __name__ == "__main__":
    main()
