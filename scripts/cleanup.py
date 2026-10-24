#!/usr/bin/env python3
"""
Cross-platform Cleanup Utility for QoSBoost.
Terminates running backend, controller, and emulator processes, and cleans temp state.
"""

import os
import sys
import subprocess
import platform

def cleanup():
    print("Running QoSBoost cleanup...")
    is_linux = platform.system().lower() == "linux"
    
    if is_linux:
        # Run sudo mn -c
        try:
            subprocess.run(["sudo", "mn", "-c"], check=False)
        except Exception:
            pass
        # Kill lingering processes
        for proc in ["ryu-manager", "controller.main", "backend.main", "iperf3"]:
            try:
                subprocess.run(["sudo", "pkill", "-f", proc], check=False)
            except Exception:
                pass
    else:
        # Windows process termination
        for proc_name in ["uvicorn.exe", "iperf3.exe"]:
            try:
                subprocess.run(["taskkill", "/F", "/IM", proc_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                pass

    # Remove temporary database if desired or keep clean
    db_file = os.path.join(os.path.dirname(__file__), "..", "qosboost.db")
    if os.path.exists(db_file):
        try:
            os.remove(db_file)
            print(f"Removed transient database: {db_file}")
        except Exception as e:
            print(f"Note: Could not remove db: {e}")

    print("Cleanup completed successfully.")

if __name__ == "__main__":
    cleanup()
