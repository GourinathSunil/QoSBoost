# Project: QoSBoost — SDN-Based QoS Management for Real-Time Applications

You are a senior engineer building **QoSBoost**, a complete, demonstrable SDN project that prioritizes latency-sensitive traffic (VoIP, video calls) over bulk traffic using traffic classification, queue-based prioritization, and dynamic bandwidth allocation. Build the full project in this repo.

## 0. Non-negotiable rules

1. **Read `design.md` in the repo root first, before writing any UI code.** Strictly follow every design and UI principle in it: colors, typography, spacing, components, layout, motion, accessibility, and tone. If anything in this prompt conflicts with `design.md` on visual or UX matters, `design.md` wins. Do not invent a visual style of your own. Before building the frontend, write a short `docs/design-compliance.md` mapping each principle in `design.md` to where and how it is applied.
2. **No Docker.** Provide plain setup scripts and a Makefile instead.
3. **Comprehensible:** clear folder structure, typed code, docstrings, short README sections explaining each module, and inline comments for any non-obvious OpenFlow/OVS logic.
4. **Demonstrable:** one command to launch the whole demo, plus a "Demo Mode" in the UI that runs a scripted before/after scenario with live results.
5. Build in the phases listed in section 6. After each phase, ensure it runs and is tested before moving on. Keep commits small and meaningful.
6. Pin dependency versions. Fail fast with helpful error messages when prerequisites (Mininet, OVS, root privileges) are missing.

## 1. System architecture

```
 React Dashboard  <--REST + WebSocket-->  FastAPI Backend  <--REST/IPC-->  Ryu Controller
                                               |                               |
                                          SQLite (metrics,                OpenFlow 1.3
                                          policies, runs)                       |
                                                                 Open vSwitch in Mininet
                                                                  (hosts + traffic gens)
```

- **Ryu controller** (OpenFlow 1.3): classification, flow rules, queues, meters, stats polling, admission control, QoS routing.
- **FastAPI backend**: the single API surface for the UI. It owns policy storage, metrics ingestion, experiment orchestration, and the WebSocket stream. It talks to Ryu through Ryu's `ryu.app.ofctl_rest`-style REST endpoints and a small custom REST app (`ryu.app.wsgi`) for QoSBoost-specific actions.
- **Mininet + OVS**: emulated network and traffic hosts. The topology script is launched and controlled by the backend's experiment runner.
- **React dashboard**: real-time visualization and control.

## 2. Tech stack (use exactly these unless a hard blocker appears, and document any deviation)

**Network and controller**
- Python 3.10+, Mininet, Open vSwitch, **Ryu** (OpenFlow 1.3), `ovs-vsctl`/`ovs-ofctl` for queue config
- Traffic generation: `iperf3` (TCP bulk, UDP), `D-ITG` or scripted UDP generators with RTP-like packet sizes/intervals for VoIP, `ffmpeg` or a scripted constant-bitrate UDP stream for video
- Latency/jitter/loss measurement: `ping`, `iperf3 --json` UDP jitter reports, plus controller probe packets

**Backend**
- **FastAPI** + Uvicorn, Pydantic v2 for schemas, `SQLModel` or SQLAlchemy + SQLite for persistence, `websockets` support via FastAPI, `pydantic-settings` for config, `PyYAML` for policies
- Classification ML (stretch): scikit-learn (Random Forest), joblib for model persistence
- Testing: pytest, httpx; lint/format: ruff + black; type checks: mypy (reasonable strictness)

**Frontend**
- **React 18 + TypeScript + Vite**
- Styling: follow `design.md`; use Tailwind CSS only if `design.md` is compatible with it, otherwise CSS Modules or the approach `design.md` prescribes
- Charts: **Recharts** (time series, bars) or **uPlot** if high-frequency rendering is needed
- Topology graph: **React Flow** (`@xyflow/react`) with custom nodes and animated edges showing utilization
- Server state: **TanStack Query**; live data: native WebSocket hook with reconnect; client state: **Zustand**
- Routing: React Router; icons: lucide-react; accessible primitives: Radix UI (or whatever `design.md` mandates)
- Testing: Vitest + React Testing Library; one Playwright smoke test for the main flow

## 3. Features to implement

### 3.1 Traffic classification
- Rule-based classifier (default): protocol + port ranges + DSCP marking → classes `voice`, `video`, `web`, `bulk`. Rules are defined in YAML and hot-reloadable.
- Classification happens on first packet of a flow (packet-in). The result is cached per 5-tuple and installed as a flow rule.
- **Stretch:** ML classifier (Random Forest on packet size, inter-arrival time, flow duration, bytes/sec) for unknown/encrypted flows, with a toggle in the UI to switch between rule-based and ML mode. Include a training script and a generated dataset from Mininet runs. Report accuracy and a confusion matrix.

### 3.2 Policy engine
- Policy per class: priority, min guaranteed bandwidth, max rate, target latency, target jitter, max loss.
- Stored in YAML + SQLite, validated with Pydantic, editable live from the UI. Changes are pushed to Ryu and re-applied to queues/meters without restarting.
- Provide 3 preset profiles: `Balanced`, `Voice-First`, `Video-Conference`.

### 3.3 Queue-based prioritization
- Configure HTB queues on the bottleneck switch ports via `ovs-vsctl` (one queue per class).
- Flow rules use `set_queue`. Provide a queue-setup module that is idempotent and cleans up on exit.

### 3.4 Real-time monitoring
- Controller polls port and flow stats every 1s. Compute per-class and per-link throughput, utilization, drops, active-flow counts.
- Latency/jitter measured by controller probe packets (or an equivalent documented method).
- Backend stores a rolling window in memory and persists downsampled history to SQLite.
- WebSocket pushes a compact JSON snapshot every second.

### 3.5 Dynamic bandwidth allocation
- Control loop: if link utilization > high-water threshold (e.g., 80%) or a real-time class violates its latency/jitter/loss target, shrink bulk/best-effort queue max rates and raise real-time guarantees; release gradually when utilization stays below a low-water mark (hysteresis to avoid flapping).
- Every adjustment is logged as an event with timestamp, reason, and before/after values, and shown in the UI event log.

### 3.3b Metering
- OpenFlow 1.3 meters rate-limit bulk flows and misbehaving hosts (drop or DSCP remark on exceed). Expose per-meter hit counters.

### 3.6 Admission control
- On a new voice/video flow, compute available bandwidth along its path versus the class's required bandwidth. Decision: **admit**, **downgrade** (to a lower class), or **reject**, with the reason. Show decisions in a live table in the UI.

### 3.7 QoS-aware routing
- Build the topology graph with NetworkX. Link cost = weighted function of delay and utilization. Real-time flows are rerouted to the best path under congestion; bulk keeps the default path. Include a topology with at least two alternative paths so rerouting is visible.

### 3.8 Evaluation module
- Scenario runner: executes a defined scenario (see section 5) twice, once with QoS disabled and once enabled, collecting latency, jitter, loss, and throughput per class.
- Produces a comparison report: summary table, time-series overlay charts, percentage improvement, and an exportable JSON + PNG/PDF summary.

## 4. Dashboard (React) — all visuals governed by `design.md`

Pages:
1. **Overview / Live:** KPI cards (voice latency, voice jitter, packet loss, link utilization, active flows), live topology with edge color/width by utilization and flow paths highlighted, per-class bandwidth stacked chart, latency/jitter chart with target lines from policy.
2. **Flows:** live table of active flows (5-tuple, class, queue, path, rate, decision) with filters and search.
3. **Policies:** editable per-class policy forms with validation, preset switcher, "Apply" with visible success/failure state, and a QoS on/off master toggle.
4. **Events:** timeline of dynamic adjustments, admission decisions, reroutes, and meter hits.
5. **Demo / Evaluation:** one-click scenario launcher, step-by-step progress, side-by-side "QoS OFF vs QoS ON" charts and results table, and an exportable report.
6. **About / How it works:** a concise architecture diagram and plain-language explanation of each mechanism, so the project is self-explanatory to an evaluator.

UX requirements (in addition to `design.md`): loading, empty, and error states for every data view; connection-status indicator for backend/controller/Mininet; responsive layout; keyboard accessible; no layout shift on live updates; a mock-data mode (`VITE_USE_MOCK=true`) so the UI can be developed and demoed without the network emulation running.

## 5. Demo scenario (must work end-to-end)

Topology: 6 hosts, 4 switches, a 10 Mbps bottleneck, and one alternate path.
Traffic timeline (60-90s):
- t=0: 1 VoIP-like UDP stream (~100 kbps) and 1 video stream (~2-4 Mbps) start
- t=15s: 2 hosts begin saturating `iperf3` TCP bulk transfers
- t=40s: a third bulk host and a misbehaving UDP flooder start
- t=60s: bulk traffic stops

Expected result: with QoS OFF, voice jitter/latency/loss spike from t=15s; with QoS ON they stay within policy targets, the controller visibly adjusts queues, meters the flooder, and reroutes if needed. The UI must show this live and in the final comparison.

## 6. Build phases (complete and verify each before the next)

1. **Scaffold:** monorepo layout, tooling, Makefile, README skeleton, config system, `docs/design-compliance.md` after reading `design.md`.
2. **Topology + learning switch:** Mininet topology script, Ryu L2 learning switch, connectivity test.
3. **Traffic + baseline:** traffic generators and measurement collectors; baseline run saved with no QoS.
4. **Classification + queues:** rule-based classifier, queue setup, `set_queue` flow rules; verify voice is prioritized in a simple test.
5. **Monitoring:** stats poller, metrics model, backend ingestion, WebSocket stream.
6. **Dynamic allocation + meters:** control loop with hysteresis, event log, meters.
7. **Admission control + QoS routing.**
8. **Frontend:** build all pages per `design.md`, wire to the backend, include mock mode.
9. **Evaluation + Demo Mode:** scenario runner, comparison report, one-click demo.
10. **Polish:** tests, docs, `make demo`, final README with screenshots/GIF placeholders and a troubleshooting section.
11. **Stretch (only if time):** ML classifier with UI toggle.

## 7. Repo layout (adapt if justified)

```
qosboost/
├── design.md                 # existing, source of truth for UI
├── README.md
├── Makefile
├── docs/                     # architecture.md, design-compliance.md, demo-script.md
├── network/                  # topology.py, traffic/, scenarios/
├── controller/               # Ryu app: classifier, policy, queues, meters, monitor, allocator, admission, routing
├── backend/                  # FastAPI app: api/, models/, services/, ws/, experiments/
├── ml/                       # (stretch) dataset gen, training, model
├── frontend/                 # React + TS app
└── scripts/                  # setup.sh, run_demo.sh, cleanup.sh
```

## 8. Deliverables and acceptance criteria

- `make setup` installs everything; `make demo` starts Ryu, backend, Mininet, and frontend (or prints exact steps if root access requires it); `make clean` tears down Mininet/OVS state.
- All phases work; unit tests for the classifier, policy validation, allocator logic, admission control, and routing cost function; API tests for the key endpoints; a frontend smoke test.
- The before/after demo shows a clear, measurable improvement for voice/video under congestion.
- The UI complies with `design.md`, verified by the compliance doc.
- README includes: overview, architecture diagram, setup, how to run the demo, how each feature works (2-3 lines each), configuration reference, and troubleshooting.

When something is ambiguous, choose the simplest option that keeps the demo reliable, note the assumption in the README, and continue. Start by reading `design.md`, then summarize your plan in under 20 lines before writing code.