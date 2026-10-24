#!/usr/bin/env bash
# QoSBoost Cleanup Script
# Tears down Mininet, OVS bridges, and terminates background backend/controller processes

echo "=== Cleaning up QoSBoost Environment ==="

# 1. Clean Mininet if available
if command -v mn > /dev/null 2>&1; then
    echo "Running sudo mn -c..."
    sudo mn -c 2>/dev/null || true
fi

# 2. Clean OVS bridges created by QoSBoost (s1, s2, s3, s4)
if command -v ovs-vsctl > /dev/null 2>&1; then
    echo "Tearing down OVS bridges and QoS queues..."
    for sw in s1 s2 s3 s4; do
        sudo ovs-vsctl del-br $sw 2>/dev/null || true
    done
    # Clear all QoS records
    sudo ovs-vsctl --all destroy qos 2>/dev/null || true
    sudo ovs-vsctl --all destroy queue 2>/dev/null || true
fi

# 3. Kill running iperf3 and controller processes
echo "Stopping any lingering controller, backend, or traffic generator processes..."
sudo pkill -f "ryu-manager" 2>/dev/null || true
sudo pkill -f "controller.main" 2>/dev/null || true
sudo pkill -f "backend.main" 2>/dev/null || true
sudo pkill -f "iperf3" 2>/dev/null || true
sudo pkill -f "network.traffic" 2>/dev/null || true

echo "=== Cleanup Complete ==="
