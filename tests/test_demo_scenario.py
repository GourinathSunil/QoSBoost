"""
Unit and integration tests for Section 5: Demo Scenario End-to-End.

Verifies:
1. Topology: 6 hosts, 4 switches, 10 Mbps bottleneck, alternative paths.
2. Timeline:
   - t=0: Voice (~100 kbps) + Video (~3.2 Mbps) start
   - t=15s: 2 saturating TCP bulk flows start
   - t=40s: 3rd bulk host + rogue UDP flooder start
   - t=60s: bulk traffic stops
3. Expected results:
   - QoS OFF: Voice latency, jitter, and loss spike from t=15s; reaches >200ms at t=40s.
   - QoS ON: Stays within policy targets (<15ms latency, <4ms jitter, 0.0% loss).
   - Dynamic allocation throttles bulk queues.
   - OF1.3 meter drops flooder excess.
   - QoS router reroutes video stream to alternate path s3.
   - Hysteresis recovers bulk queue rate after t=60s without oscillation.
"""

import pytest
from network.topology import get_topology_dict
from network.traffic import SimulatedScenarioEngine
from network.scenario import run_scenario, build_comparison_report


def test_topology_requirements():
    """Verify topology satisfies: 6 hosts, 4 switches, 10 Mbps bottleneck, alternate path."""
    topo = get_topology_dict()
    assert len(topo["switches"]) == 4
    assert len(topo["hosts"]) == 6

    # Verify bottleneck link
    bottleneck_links = [link for link in topo["links"] if link.get("is_bottleneck") is True]
    assert len(bottleneck_links) == 1
    assert bottleneck_links[0]["bw_mbps"] == 10
    assert bottleneck_links[0]["source"] == "s1"
    assert bottleneck_links[0]["target"] == "s2"

    # Verify alternate paths (s1 -> s3 and cross-link s2 <-> s3)
    alt_links = [
        link for link in topo["links"]
        if (link["source"] == "s1" and link["target"] == "s3") or
           (link["source"] == "s2" and link["target"] == "s3")
    ]
    assert len(alt_links) >= 2


def test_scenario_timeline_qos_off():
    """Verify behavior under QoS OFF across the 4 stages."""
    engine = SimulatedScenarioEngine(qos_enabled=False)
    engine.start()

    # t=5s (Stage 1: Real-time start)
    snap_t5 = engine.tick(elapsed=5.0)
    assert snap_t5["voice"]["latency_ms"] < 15.0
    assert snap_t5["voice"]["loss_percent"] == 0.0
    assert snap_t5["link_utilization"] < 50.0

    # t=25s (Stage 2: Bulk Congestion)
    snap_t25 = engine.tick(elapsed=25.0)
    # Under FIFO, latency and loss spike
    assert snap_t25["voice"]["latency_ms"] > 30.0  # Violates SLA
    assert snap_t25["voice"]["jitter_ms"] > 10.0   # Violates SLA
    assert snap_t25["voice"]["loss_percent"] > 0.0 # Packet loss begins
    assert snap_t25["link_utilization"] > 90.0

    # t=45s (Stage 3: Overload + Flooder)
    snap_t45 = engine.tick(elapsed=45.0)
    assert snap_t45["voice"]["latency_ms"] > 100.0  # Severe bufferbloat
    assert snap_t45["voice"]["loss_percent"] > 10.0 # Heavy packet drop
    assert snap_t45["rerouted"] is False           # FIFO cannot reroute


def test_scenario_timeline_qos_on():
    """Verify behavior under QoS ON across the 4 stages."""
    engine = SimulatedScenarioEngine(qos_enabled=True)
    engine.start()

    # t=5s (Stage 1: Real-time start)
    snap_t5 = engine.tick(elapsed=5.0)
    assert snap_t5["voice"]["latency_ms"] < 10.0
    assert snap_t5["voice"]["jitter_ms"] < 3.0
    assert snap_t5["voice"]["loss_percent"] == 0.0

    # t=25s (Stage 2: Bulk Congestion with QoS ON)
    snap_t25 = engine.tick(elapsed=25.0)
    # Voice stays well within strict SLA targets
    assert snap_t25["voice"]["latency_ms"] < 15.0
    assert snap_t25["voice"]["jitter_ms"] < 4.0
    assert snap_t25["voice"]["loss_percent"] == 0.0
    assert snap_t25["bulk"]["throughput_kbps"] <= 5000.0  # Bulk queue throttled

    # Verify adaptation event logged
    adaptation_events = [e for e in snap_t25["events"] if e["type"] == "ADAPTATION"]
    assert len(adaptation_events) >= 1
    assert "Bulk queue clamped" in adaptation_events[0]["message"]
    assert adaptation_events[0]["before_value"] == "8000 kbps"
    assert adaptation_events[0]["after_value"] == "4800 kbps"

    # t=45s (Stage 3: Overload + Flooder with QoS ON)
    snap_t45 = engine.tick(elapsed=45.0)
    # Voice still strictly protected
    assert snap_t45["voice"]["latency_ms"] < 15.0
    assert snap_t45["voice"]["loss_percent"] == 0.0

    # Metering and Rerouting active
    assert snap_t45["flooder"]["meter_drops"] > 0
    assert snap_t45["rerouted"] is True
    assert "s3" in snap_t45["path"]

    # Verify meter and reroute events logged
    meter_events = [e for e in snap_t45["events"] if e["type"] == "METER_DROP"]
    assert len(meter_events) >= 1
    reroute_events = [e for e in snap_t45["events"] if e["type"] == "REROUTE"]
    assert len(reroute_events) >= 1

    # t=62s (Stage 4: Recovery)
    snap_t62 = engine.tick(elapsed=62.0)
    assert snap_t62["rerouted"] is False
    recovery_events = [e for e in snap_t62["events"] if e["type"] == "ADAPTATION" and "restored" in e["message"]]
    assert len(recovery_events) >= 1


def test_comparison_report_improvements():
    """Verify comparison report accurately computes percentage improvements."""
    report = build_comparison_report(duration_seconds=65)
    imp = report["improvement_percentages"]

    assert imp["latency_reduction_percent"] >= 90.0
    assert imp["jitter_reduction_percent"] >= 90.0
    assert imp["loss_elimination_percent"] == 100.0
