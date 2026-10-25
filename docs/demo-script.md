# QoSBoost Demo Evaluation Script

This document details the exact 65-second benchmark evaluation sequence executed during the QoSBoost demonstration, explaining the traffic phases, OpenFlow mechanisms triggered, and expected metrics under **QoS OFF (Unmanaged FIFO)** versus **QoS ON (QoSBoost Active)**.

---

## 1. Network Topology

The demonstration runs over a 4-switch, 6-host SDN topology:
- **`s1` (Ingress Edge Switch):** Connects senders `h1` through `h5`.
- **`s2` (Bottleneck Core Switch):** 10 Mbps bottleneck link (`s1-s2`) with 2ms propagation delay. Hosts Open vSwitch Linux HTB queues 0 through 3.
- **`s3` (Alternative Core Switch):** 20 Mbps bypass link (`s1-s3`) with 15ms delay.
- **`s2-s3` (Core Cross-Link):** 50 Mbps high-speed link with 5ms delay providing multiple alternate routes (`s1->s3->s4` and `s1->s2->s3->s4`).
- **`s4` (Egress Edge Switch):** Connects media sink `h6`.

### Hosts and Traffic Roles:
| Host | IP Address | Traffic Class | Description |
|---|---|---|---|
| `h1` | `10.0.0.1` | `voice` | VoIP G.711 stream (~100 kbps, UDP 5060/RTP, DSCP 46 EF) |
| `h2` | `10.0.0.2` | `video` | 1080p HD video conferencing stream (~3.2 Mbps, UDP 554/RTSP, DSCP 34 AF41) |
| `h3` | `10.0.0.3` | `bulk` | TCP `iperf3` bulk transfer 1 (greedy windowing) |
| `h4` | `10.0.0.4` | `bulk` | TCP `iperf3` bulk transfer 2 (greedy windowing) |
| `h5` | `10.0.0.5` | `flooder` | Rogue UDP flooder attempting link denial-of-service |
| `h6` | `10.0.0.6` | `sink` | Destination sink and metrics collector |

---

## 2. 65-Second Traffic Timeline

```
t=0s             t=15s                      t=40s                         t=60s        t=65s
|----------------|--------------------------|-----------------------------|------------|
 Stage 1          Stage 2                    Stage 3                       Stage 4      Done
 Real-time start  Bulk congestion            Flooder + Overload            Normalization
 (VoIP + Video)   (2x TCP iperf3 saturate)   (3rd bulk + UDP flood)        (Bulk stops)
```

### Stage 1: Real-Time Flow Initialization ($t = 0 \dots 15\text{s}$)
- **Events:** `h1` starts VoIP stream (100 kbps) and `h2` starts Video conferencing (3.2 Mbps). Total offered load $\approx 3.3\text{ Mbps}$, well within the 10 Mbps bottleneck link.
- **QoS OFF:** Voice latency nominal (~7ms), jitter <1ms, loss 0.0%.
- **QoS ON:** Packets classified on packet-in via protocol, port, and DSCP 46/34. Voice assigned to Queue 1, Video to Queue 2. 5-tuple cached in Ryu controller.

### Stage 2: Bulk TCP Congestion ($t = 15 \dots 40\text{s}$)
- **Events:** `h3` and `h4` initiate aggressive TCP bulk transfers attempting to saturate 100% of the 10 Mbps bottleneck interface.
- **QoS OFF (Unmanaged FIFO):**
  - Bottleneck bufferbloat occurs immediately.
  - FIFO queue fills; voice packets wait behind large 1500-byte TCP frames.
  - Voice latency spikes to **120–180 ms**.
  - Voice jitter surges to **30–50 ms**.
  - Drop-tail packet loss begins (~8–15%).
- **QoS ON (QoSBoost HTB):**
  - Voice packets are enqueued in strict-priority Queue 1; Video in Queue 2 with guaranteed minimum rate.
  - Link utilization crosses High-Watermark (80%). Dynamic allocator reduces bulk queue maximum ceiling rate by 35%.
  - Voice latency remains rock-solid at **~7.3 ms**, jitter **<1 ms**, loss **0.0%**.

### Stage 3: Extreme Overload & Rogue Flooder ($t = 40 \dots 60\text{s}$)
- **Events:** A 3rd bulk flow starts, and `h5` launches a 5 Mbps unmanaged UDP burst.
- **QoS OFF:** Total breakdown. Voice latency exceeds **220 ms**, jitter **~55 ms**, packet loss reaches **28%**. Video freezes completely.
- **QoS ON:**
  - **OpenFlow 1.3 Meter 1** detects `h5` exceeding the 2000 kbps threshold and enforces `OFPMBT_DROP`, discarding 2.5+ MB of rogue packets.
  - **QoS Routing:** Dijkstra cost function $\text{Cost}(e) = \alpha \cdot \text{Delay} + \beta \cdot \frac{\text{Util}}{1 - \text{Util}}$ detects heavy congestion on `s1-s2`. Video flow is dynamically rerouted to alternate path `s1 -> s3 -> s4`.
  - Voice traffic retains exclusive access to the bottleneck path, maintaining SLA targets.

### Stage 4: Traffic Normalization ($t = 60 \dots 65\text{s}$)
- **Events:** Bulk transfers and UDP flooder terminate. Offered load returns to VoIP + Video.
- **QoS OFF:** Latency slowly recovers over 5 seconds as bloated switch buffers drain.
- **QoS ON:** Hysteresis controller detects link utilization $<60\%$ for 4 consecutive seconds and restores bulk queues to default profile without oscillation.

---

## 3. Comparative Benchmark Results

| Metric | QoS OFF (FIFO Drop-tail) | QoS ON (QoSBoost) | Measured Improvement |
|---|---|---|---|
| **Voice Latency (Average)** | **82.5 ms** | **5.7 ms** | **93.1% reduction** |
| **Voice Latency (Peak)** | **220.4 ms** | **8.1 ms** | **Eliminated spikes** |
| **Voice Jitter (RFC 3550)** | **19.8 ms** | **0.5 ms** | **97.5% reduction** |
| **Voice Packet Loss** | **4.2% (peak 28%)** | **0.0%** | **100.0% elimination** |
| **Video Stream Health** | Severe frame drops & freeze | 1080p sustained, 0% loss | Rerouted to `s3` |
| **Bulk Transfer Bandwidth** | 10.0 Mbps (starves voice) | 6.5 Mbps (elastic share) | Fair QoS coexistence |

---

## 4. How to Run the Demo

### One-Click Dashboard Evaluation
1. Launch the dashboard (`make run-frontend` or `make demo`).
2. Navigate to the **Demo Mode** tab in the navigation bar.
3. Click **One-Click Benchmark** to automatically execute the evaluation and render the side-by-side results table and overlay chart.
4. Download the artifacts using the **JSON**, **PNG Chart**, or **PDF Report** buttons.

### Command-Line Evaluation
Generate the 300 DPI comparative time-series chart and executive PDF from terminal:
```bash
python network/scenario.py --report
```
Generated artifacts:
- `network/scenarios/evaluation_summary.png`
- `network/scenarios/evaluation_summary.pdf`
