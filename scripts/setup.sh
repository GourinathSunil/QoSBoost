#!/usr/bin/env bash
# QoSBoost Setup Script (Ubuntu/Debian Linux & WSL2)
set -e

echo "=== QoSBoost Setup: Installing Dependencies ==="

# Check Linux distribution
if [ -f /etc/debian_version ]; then
    echo "Updating apt repositories and installing system tools..."
    sudo apt-get update -y
    sudo apt-get install -y \
        python3 \
        python3-pip \
        python3-dev \
        mininet \
        openvswitch-switch \
        openvswitch-testcontroller \
        iperf3 \
        iproute2 \
        net-tools \
        curl \
        git \
        make
fi

# Verify Python requirements
echo "Installing Python dependencies from requirements.txt..."
pip3 install -r requirements.txt

# Setup Frontend
echo "Setting up Frontend (React + TypeScript + Vite)..."
if command -v node > /dev/null 2>&1; then
    cd frontend && npm install && cd ..
else
    echo "WARNING: Node.js is not installed. Please install Node.js v18+ to build the dashboard."
fi

# Verify OVS service status on Linux
if command -v systemctl > /dev/null 2>&1; then
    echo "Ensuring Open vSwitch service is active..."
    sudo systemctl start openvswitch-switch || true
fi

echo "=== QoSBoost Setup Complete! ==="
echo "You can now run:"
echo "  make demo     # Starts the full demonstration"
