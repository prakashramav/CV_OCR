"""One-Click System Launcher for AI-Powered ANPR & Traffic Monitoring.

Spawns the FastAPI backend (Uvicorn on port 8000) and Next.js frontend (Node on port 3000).
"""

import os
import sys
import time
import subprocess
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))


def main():
    print("=" * 70)
    print("  AI-POWERED AUTOMATIC NUMBER PLATE RECOGNITION (ANPR) SYSTEM")
    print("  Industry-Standard B.Tech Project Launcher")
    print("=" * 70)

    # 1. Check or initialize database
    from backend.app.database.init_db import init_db
    print("\n[1/3] Initializing SQLite database schema (WAL Mode)...")
    init_db()

    # 2. Start FastAPI Backend
    print("[2/3] Launching FastAPI Backend on http://127.0.0.1:8000 ...")
    backend_cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "backend.app.main:app",
        "--host",
        "127.0.0.1",
        "--port",
        "8000",
    ]
    backend_proc = subprocess.Popen(backend_cmd, cwd=str(ROOT_DIR))

    # Give backend a moment to bind socket
    time.sleep(2)

    # 3. Start Next.js Frontend
    print("[3/3] Launching Next.js Frontend on http://localhost:3000 ...")
    frontend_dir = ROOT_DIR / "frontend"
    frontend_cmd = ["npm", "start"]

    frontend_proc = subprocess.Popen(frontend_cmd, cwd=str(frontend_dir), shell=True)

    print("\n" + "=" * 70)
    print("  SYSTEM RUNNING SUCCESSFULLY!")
    print("  - Frontend Dashboard: http://localhost:3000")
    print("  - Backend REST API:   http://127.0.0.1:8000")
    print("  - Interactive Docs:   http://127.0.0.1:8000/docs")
    print("  Press Ctrl+C in this terminal to gracefully terminate both services.")
    print("=" * 70 + "\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nTerminating ANPR system services...")
        backend_proc.terminate()
        frontend_proc.terminate()
        print("Shutdown complete.")


if __name__ == "__main__":
    main()
