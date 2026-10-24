# QoSBoost — SDN-Based QoS Management for Real-Time Applications

[![Design Compliance](https://img.shields.io/badge/Design-Linear--Compliant-5e6ad2)](docs/design-compliance.md)
[![OpenFlow](https://img.shields.io/badge/OpenFlow-1.3-blue)](controller/)
[![Backend](https://img.shields.io/badge/Backend-FastAPI-009688)](backend/)
[![Frontend](https://img.shields.io/badge/Frontend-React_18_%2B_Vite-61dafb)](frontend/)

QoSBoost is a demonstrable Software-Defined Networking (SDN) QoS control framework designed to guarantee ultra-low latency, jitter, and zero packet loss for real-time traffic (VoIP, video conferencing) in the presence of heavy bulk transfers and rogue network floods.

---

## Architecture Overview

```
 React Dashboard  <--REST + WebSocket-->  FastAPI Backend  <--REST/IPC-->  Ryu Controller
 (Linear Design)                               |                               |
                                          SQLite (metrics,                OpenFlow 1.3
                                          policies, runs)                       |
                                                                 Open vSwitch in Mininet
                                                                  (6 hosts + 4 switches)
```

QoSBoost consists of four coordinated components:
1. **Ryu Controller (`controller/`)**: OpenFlow 1.3 application executing dynamic classification, HTB queue assignments, meter enforcement, stats polling, admission control, and Dijkstra-based QoS routing.
2. **FastAPI Backend (`backend/`)**: REST and WebSocket server managing active policy profiles, telemetry persistence in SQLite, WebSocket live broadcasting, and scripted experiment runs.
3. **Mininet Network Topology (`network/`)**: 6-host, 4-switch mesh topology featuring a calibrated 10 Mbps bottleneck and an alternative routed path.
4. **React Dashboard (`frontend/`)**: High-fidelity dark mode dashboard strictly compliant with `DESIGN.md` (#010102 canvas, surface ladder, single #5e6ad2 lavender accent, React Flow topology, Recharts telemetry).

---

## Quick Start

### 1. Prerequisites Check
Verify your environment prerequisites:
```bash
make check-prereqs
# or: python scripts/check_prereqs.py
```

### 2. Setup
Install Python backend packages and frontend dependencies:
```bash
make setup
```

### 3. One-Command Demo
Launch the full demonstration:
```bash
make demo
```
*Note: On Linux systems with Mininet installed, this runs with kernel Open vSwitch; on non-Linux or non-root environments, QoSBoost automatically activates high-fidelity simulated network emulation so the demo works anywhere!*

---

## Repo Structure

```
qosboost/
├── DESIGN.md                 # Source of truth for frontend UI design
├── Makefile                  # Build, test, and demo orchestration
├── requirements.txt          # Pinned Python dependencies
├── config/                   # YAML configuration for policies, queues, and meters
│   └── policies.yaml
├── docs/                     # Specifications and architectural docs
│   ├── design-compliance.md  # Detailed compliance matrix against DESIGN.md
│   ├── architecture.md       # Deep-dive architecture and OpenFlow message flow
│   └── demo-script.md        # Scripted evaluation timeline
├── network/                  # Mininet topology, traffic generators, and scenario runner
│   ├── topology.py
│   ├── traffic.py
│   └── scenario.py
├── controller/               # OpenFlow 1.3 Ryu controller
│   ├── classifier.py         # Rule-based (and ML) traffic classifier
│   ├── queue_manager.py      # OVS HTB queue configuration (ovs-vsctl)
│   ├── policy_engine.py      # Dynamic bandwidth allocator & hysteresis
│   ├── admission.py          # Bandwidth-aware admission control
│   ├── qos_router.py         # Delay/utilization-weighted QoS routing
│   └── controller.py         # Main OpenFlow 1.3 event loop & REST interface
├── backend/                  # FastAPI web services & SQLite persistence
│   ├── main.py               # Application entrypoint & lifespan
│   ├── database.py           # SQLite connection and session management
│   ├── models/               # Pydantic v2 & SQLModel schemas
│   ├── api/                  # REST routes (policies, flows, metrics, scenarios)
│   └── ws/                   # WebSocket telemetry broadcaster
├── frontend/                 # React 18 + TypeScript + Vite UI
└── scripts/                  # Helper scripts (setup, run_demo, cleanup)
```

---

## Modules Explanation

- **Classifier (`controller/classifier.py`)**: Classifies traffic into `voice`, `video`, `web`, and `bulk` based on 5-tuple, protocol, port ranges, and DSCP tags on the first packet-in. Results are cached and programmed into OpenFlow flow rules.
- **Queue Manager (`controller/queue_manager.py`)**: Configures Hierarchical Token Bucket (HTB) queues on Open vSwitch interfaces with guaranteed minimum rates and burst ceilings.
- **Dynamic Allocator (`controller/policy_engine.py`)**: Monitors link saturation. When the high watermark (80%) is exceeded, it dynamically shrinks bulk queues and raises real-time allocations with hysteresis to avoid oscillation.
- **Admission Controller (`controller/admission.py`)**: Evaluates real-time flow requests against residual link headroom, making deterministic `admit`, `downgrade`, or `reject` decisions.
- **QoS Router (`controller/qos_router.py`)**: Maintains a NetworkX graph with link costs derived from latency and utilization, redirecting latency-critical flows away from congested paths.
