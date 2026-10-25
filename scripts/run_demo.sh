#!/usr/bin/env bash
# QoSBoost One-Command Demonstration Launcher
set -e

echo "======================================================================"
echo " QoSBoost: SDN-Based QoS Management for Real-Time Applications"
echo "======================================================================"

# Determine root / sudo capability for Mininet
IS_ROOT=false
if [ "$EUID" -eq 0 ]; then
    IS_ROOT=true
fi

PIDS=()

cleanup() {
    echo ""
    echo "Terminating QoSBoost processes..."
    for pid in "${PIDS[@]}"; do
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid" 2>/dev/null || true
        fi
    done
    if [ "$IS_ROOT" = true ]; then
        mn -c >/dev/null 2>&1 || true
    fi
    echo "QoSBoost cleanup complete."
}

trap cleanup INT TERM EXIT

# 1. Start Ryu SDN Controller
echo "[1/4] Starting Ryu OpenFlow 1.3 Controller (Port 6653, WSGI 8080)..."
if command -v ryu-manager >/dev/null 2>&1; then
    ryu-manager --verbose controller/controller.py > controller.log 2>&1 &
    PIDS+=($!)
else
    echo "ryu-manager not found in PATH; running controller fallback..."
    python3 -m controller.main > controller.log 2>&1 &
    PIDS+=($!)
fi

# 2. Start FastAPI Backend
echo "[2/4] Starting FastAPI Telemetry & Policy Backend (Port 8000)..."
python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 > backend.log 2>&1 &
PIDS+=($!)

# 3. Start Frontend Dashboard
echo "[3/4] Starting React Dashboard (Port 5173)..."
(cd frontend && npm run dev > ../frontend.log 2>&1) &
PIDS+=($!)

sleep 2

# 4. Launch Mininet Topology or Simulated Emulation
if [ "$IS_ROOT" = true ] && command -v mn >/dev/null 2>&1; then
    echo "[4/4] Starting Mininet Topology with OVS HTB Queues..."
    echo "Access the QoSBoost Dashboard at: http://localhost:5173"
    python3 network/topology.py
else
    echo "[4/4] Running in Dashboard Standalone & Emulation Mode"
    echo ""
    echo "======================================================================"
    echo " QoSBoost Dashboard is active at: http://localhost:5173"
    echo " Backend API is active at:       http://localhost:8000/docs"
    echo " To run with root Mininet data plane, execute with sudo:"
    echo "   sudo make demo"
    echo "======================================================================"
    echo "Press Ctrl+C to stop all services."
    wait
fi
