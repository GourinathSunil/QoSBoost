# QoSBoost System Architecture Specification

This document defines the 4-tier architecture of **QoSBoost**, detailing the communication interfaces, protocols, and data models connecting the React Dashboard, FastAPI Backend, Ryu OpenFlow Controller, and Mininet Open vSwitch environment.

---

## 1. High-Level Architecture Diagram

```
+-----------------------------------------------------------------------------------------+
|                                    React Dashboard                                      |
|            (React 18 + TypeScript + Vite, strictly compliant with DESIGN.md)            |
+-----------------------------------------------------------------------------------------+
                    ▲                                                   ▲
                    │ REST API (CRUD, Profiles, Scenarios)              │ WebSocket (/ws/telemetry)
                    ▼                                                   │ 1 Hz live JSON snapshots
+-----------------------------------------------------------------------------------------+
|                                    FastAPI Backend                                      |
|                       (Port 8000, Uvicorn, Pydantic v2 Schemas)                         |
|                                                                                         |
|   ┌───────────────────────────┐   ┌─────────────────────────┐   ┌───────────────────┐   |
|   │     SQLite Persistence    │   │  Experiment Orchestrator│   │ Controller Client │   |
|   │ (Metrics, Policies, Logs) │   │ (Mininet Lifecycle/Runs)│   │  (Ryu REST / IPC) │   |
|   └───────────────────────────┘   └─────────────────────────┘   └───────────────────┘   |
+-----------------------------------------------------------------------------------------+
                                                                        ▲
                                                                        │ REST / IPC
                                                                        │ (ofctl_rest & wsgi)
                                                                        ▼
+-----------------------------------------------------------------------------------------+
|                                     Ryu Controller                                      |
|                        (OpenFlow 1.3 Controller, Port 6653 & 8080)                      |
|                                                                                         |
|   ┌───────────────────────────┐   ┌─────────────────────────┐   ┌───────────────────┐   |
|   │   5-Tuple Classifier      │   │   Queue & Meter Engine  │   │ Admission Control │   |
|   │  (Rule-based / DSCP / ML) │   │   (HTB & OF1.3 Meters)  │   │  & QoS Routing    │   |
|   └───────────────────────────┘   └─────────────────────────┘   └───────────────────┘   |
+-----------------------------------------------------------------------------------------+
                                                                        ▲
                                                                        │ OpenFlow 1.3
                                                                        │ (TCP port 6653)
                                                                        ▼
+-----------------------------------------------------------------------------------------+
|                               Mininet + Open vSwitch (OVS)                              |
|                                                                                         |
|     h1 (VoIP)  ----\                                                                    |
|     h2 (Video) ----- s1 (Ingress) ==== [10M Bottleneck, HTB] ====> s2 ====> s4 ===> h6  |
|     h3 (Bulk1) ----/   │                                           ▲                    |
|     h4 (Bulk2) ---/    +========= [20M Alternate Path] ======> s3 -+                    |
|     h5 (Flood) --/                                                                      |
+-----------------------------------------------------------------------------------------+
```

---

## 2. Component Specifications

### 2.1 Ryu Controller (OpenFlow 1.3)
- **Role:** Centralized SDN brain governing the data plane via OpenFlow 1.3 protocol.
- **Port:** OpenFlow listening port `6653`, WSGI REST server listening on port `8080`.
- **Sub-modules:**
  1. `TrafficClassifier`: Inspects first packet of each flow (`OFPPacketIn`). Matches 5-tuple, port lists, and DiffServ DSCP bits (Voice: DSCP 46 EF, Video: DSCP 34 AF41). Caches matches in an in-memory hash table for $O(1)$ lookup.
  2. `QueueManager`: Manages Hierarchical Token Bucket (HTB) queues across the bottleneck switch ports (`s1-eth6`). Queues 0 (Web), 1 (Voice), 2 (Video), 3 (Bulk). Flow entries apply `OFPActionSetQueue(queue_id=X)`.
  3. `MeterManager`: Implements OpenFlow 1.3 meter tables (`OFPMeterMod`) to police rogue UDP traffic (Host `h5`) at 1000 kbps, dropping excess packets.
  4. `DynamicBandwidthAllocator`: Control loop evaluating link utilization against high-watermark (80%) and low-watermark (60%) thresholds with hysteresis (4.0s cooldown) to throttle bulk traffic during congestion.
  5. `AdmissionController`: Evaluates residual bandwidth headroom for incoming real-time calls. Produces `admit`, `downgrade`, or `reject` decisions.
  6. `QoSRouter`: Models network topology in NetworkX. Dynamically reroutes real-time traffic to alternate switch `s3` when bottleneck `s1-s2` experiences queuing delay.

### 2.2 FastAPI Backend
- **Role:** Single unified API surface for the React Dashboard.
- **Port:** Port `8000`.
- **Responsibilities:**
  - **Policy Store:** Validates and persists policy profiles (`Balanced`, `Voice-First`, `Video-Conference`) in YAML and SQLite.
  - **Metrics Ingestion & Broadcaster:** Collects 1-second telemetry snapshots, maintains a 120-second circular buffer, persists downsampled history to SQLite, and broadcasts compact JSON to all connected WebSockets (`/ws/telemetry`).
  - **Ryu REST Client:** Communicates with Ryu via standard `ryu.app.ofctl_rest` endpoints (`/stats/flow/<dpid>`, `/stats/port/<dpid>`) and custom QoSBoost WSGI routes (`/qosboost/policy`, `/qosboost/queues`).
  - **Experiment Runner:** Orchestrates reproducible demo evaluation scenarios (t=0..65s timeline).

### 2.3 Mininet + Open vSwitch (OVS)
- **Role:** Emulated virtual network environment executing Linux network namespaces.
- **Topology:**
  - 6 Hosts: `h1` (VoIP: 10.0.0.1), `h2` (Video: 10.0.0.2), `h3` (Bulk 1: 10.0.0.3), `h4` (Bulk 2: 10.0.0.4), `h5` (Flooder: 10.0.0.5), `h6` (Receiver Sink: 10.0.0.6).
  - 4 Switches: `s1` (Ingress), `s2` (Core Bottleneck), `s3` (Core Alternate), `s4` (Egress).
  - Primary Bottleneck Link: `s1 <-> s2` (10 Mbps, 2ms delay, HTB Queues).
  - Alternate Path: `s1 <-> s3` (20 Mbps, 15ms delay).

### 2.4 React Dashboard
- **Role:** Visual command and control center.
- **Design System:** Strictly compliant with `DESIGN.md` (#010102 canvas, surface ladder, single lavender `#5e6ad2` accent, Inter/JetBrains Mono typography).
- **Features:** KPI telemetry, live React Flow/SVG topology graph, live active flows table, policy profile editor, event timeline, and one-click demo comparison mode.

---

## 3. Communication Protocols & APIs

| Channel | Source | Destination | Protocol | Description |
|---|---|---|---|---|
| **Control Plane** | Ryu Controller | Open vSwitch | OpenFlow 1.3 (TCP 6653) | Switch features, FlowMod, PacketIn/PacketOut, MeterMod, PortStats |
| **Controller REST** | FastAPI Backend | Ryu Controller | HTTP REST (Port 8080) | `ofctl_rest` flow/port stats, `/qosboost/` WSGI endpoints |
| **Client REST** | React Dashboard | FastAPI Backend | HTTP REST (Port 8000) | Policy CRUD, flow inspect, scenario runner controls |
| **Telemetry Stream**| FastAPI Backend | React Dashboard | WebSocket (`/ws/telemetry`) | 1-second compact JSON telemetry snapshots |
| **Data Plane** | Host Senders (`h1`-`h5`) | Host Receiver (`h6`) | UDP / TCP over OVS | VoIP RTP streams (5004), Video (5002), iperf3 (5201) |
