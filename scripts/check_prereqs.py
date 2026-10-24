#!/usr/bin/env python3
"""
Prerequisite Checker for QoSBoost.
Inspects system environment for required dependencies:
- Python 3.10+
- Root privileges (required for Mininet and OVS kernel spaces)
- Mininet (mn binary)
- Open vSwitch (ovs-vsctl, ovs-ofctl)
- Node.js & npm (for React Dashboard)
- Traffic tools (iperf3, ping)
"""

import os
import shutil
import sys
import platform

def check_prereqs() -> bool:
    print("=" * 65)
    print(" QoSBoost: System Prerequisites Inspection")
    print("=" * 65)
    
    all_passed = True
    warnings = []
    
    # 1. Python version
    py_major, py_minor = sys.version_info[:2]
    py_ok = (py_major == 3 and py_minor >= 10) or py_major > 3
    status = "OK" if py_ok else "FAIL"
    print(f"[{status:^4}] Python 3.10+: Detected Python {platform.python_version()}")
    if not py_ok:
        all_passed = False
        print("       ERROR: Python 3.10 or higher is required.")

    # 2. Node.js & NPM
    node_path = shutil.which("node")
    npm_path = shutil.which("npm") or shutil.which("npm.cmd")
    node_ok = node_path is not None and npm_path is not None
    status = "OK" if node_ok else "FAIL"
    print(f"[{status:^4}] Node.js & NPM: Node={'Found' if node_path else 'Missing'}, NPM={'Found' if npm_path else 'Missing'}")
    if not node_ok:
        all_passed = False
        print("       ERROR: Node.js (v18+) and npm are required to run the frontend.")

    # 3. Operating System & Root
    is_linux = platform.system().lower() == "linux"
    is_root = False
    if hasattr(os, "geteuid"):
        is_root = (os.geteuid() == 0)

    # 4. Mininet & OVS binaries
    mn_path = shutil.which("mn")
    ovs_vsctl = shutil.which("ovs-vsctl")
    ovs_ofctl = shutil.which("ovs-ofctl")
    iperf3_path = shutil.which("iperf3")

    if is_linux:
        status_root = "OK" if is_root else "WARN"
        print(f"[{status_root:^4}] Root Privileges: {'Active (UID 0)' if is_root else 'Non-root user'}")
        if not is_root:
            warnings.append("Mininet and OVS queue configuration require root (sudo) privileges on Linux.")

        status_mn = "OK" if mn_path else "WARN"
        print(f"[{status_mn:^4}] Mininet binary (mn): {'Found at ' + mn_path if mn_path else 'Not found'}")
        if not mn_path:
            warnings.append("Install Mininet on Ubuntu/Debian: 'sudo apt-get install -y mininet'")

        status_ovs = "OK" if (ovs_vsctl and ovs_ofctl) else "WARN"
        print(f"[{status_ovs:^4}] Open vSwitch (OVS): {'Found' if status_ovs == 'OK' else 'Not found'}")
        if not (ovs_vsctl and ovs_ofctl):
            warnings.append("Install OVS on Ubuntu/Debian: 'sudo apt-get install -y openvswitch-switch'")

        status_iperf = "OK" if iperf3_path else "WARN"
        print(f"[{status_iperf:^4}] iperf3: {'Found' if iperf3_path else 'Not found'}")
        if not iperf3_path:
            warnings.append("Install iperf3: 'sudo apt-get install -y iperf3'")
    else:
        print(f"[INFO] Host OS: {platform.system()} (Non-Linux detected)")
        print("       NOTE: Native Mininet and Open vSwitch kernel modules require Linux or WSL2.")
        print("       QoSBoost includes an intelligent dual-mode architecture:")
        print("         1) Linux / WSL2 mode: Full real Mininet + OVS + Ryu kernel emulation.")
        print("         2) Simulated / Mock mode: High-fidelity mathematical network simulation")
        print("            running the exact 6-host 4-switch topology with dynamic congestion,")
        print("            jitter spikes, HTB queue behavior, and live WebSocket telemetry.")

    print("=" * 65)
    if warnings:
        print("System Notices:")
        for w in warnings:
            print(f"  * {w}")
        print("=" * 65)

    if not all_passed:
        print("FAIL: Core prerequisites are missing. Please address the errors above.")
        return False
    else:
        print("SUCCESS: Environment is ready to run QoSBoost!")
        return True

if __name__ == "__main__":
    success = check_prereqs()
    sys.exit(0 if success else 1)
