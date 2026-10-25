#!/usr/bin/env python3
"""
QoSBoost One-Command Demo Launcher (Cross-Platform: Windows, Linux, macOS).
Orchestrates the Ryu controller, FastAPI backend, and React dashboard.
"""

import os
import sys
import time
import signal
import subprocess
import webbrowser

processes = []

def cleanup(sig=None, frame=None):
    print("\nStopping QoSBoost services...")
    for p in processes:
        try:
            p.terminate()
            p.wait(timeout=2)
        except Exception:
            try:
                p.kill()
            except Exception:
                pass
    print("QoSBoost cleanup complete.")
    sys.exit(0)

signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)

def main():
    print("======================================================================")
    print(" QoSBoost: SDN-Based QoS Management for Real-Time Applications")
    print("======================================================================")

    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    frontend_dir = os.path.join(root_dir, "frontend")

    # 1. Start Backend (FastAPI on Port 8000)
    print("[1/3] Starting FastAPI Backend on http://localhost:8000 ...")
    backend_cmd = [sys.executable, "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
    backend_proc = subprocess.Popen(backend_cmd, cwd=root_dir)
    processes.append(backend_proc)

    # 2. Start Frontend (Vite on Port 5173)
    print("[2/3] Starting React Dashboard on http://localhost:5173 ...")
    npm_cmd = "npm.cmd" if os.name == "nt" else "npm"
    frontend_proc = subprocess.Popen([npm_cmd, "run", "dev"], cwd=frontend_dir)
    processes.append(frontend_proc)

    # 3. Optional Ryu / Mininet notice
    print("[3/3] Checking Mininet / OpenFlow Controller availability...")
    is_linux = sys.platform.startswith("linux")
    is_root = os.geteuid() == 0 if hasattr(os, "geteuid") else False

    if is_linux and is_root:
        print("Root Linux environment detected; starting Mininet topology...")
        try:
            mininet_proc = subprocess.Popen([sys.executable, "network/topology.py"], cwd=root_dir)
            processes.append(mininet_proc)
        except Exception as e:
            print(f"Could not launch Mininet: {e}")
    else:
        print("Note: Running in standalone / mock emulation mode (works on all operating systems).")

    time.sleep(2)
    print("\n======================================================================")
    print("  QoSBoost Dashboard: http://localhost:5173")
    print("  FastAPI Swagger UI: http://localhost:8000/docs")
    print("======================================================================")
    print("Press Ctrl+C to terminate all services.\n")

    try:
        webbrowser.open("http://localhost:5173")
    except Exception:
        pass

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        cleanup()

if __name__ == "__main__":
    main()
