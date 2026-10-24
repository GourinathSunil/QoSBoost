"""
Unit tests for Phase 7: Admission Control and QoS Routing.
"""

import pytest
from controller.admission import AdmissionController
from controller.qos_router import QoSRouter


def test_admission_control_decisions():
    # 10 Mbps bottleneck with 10% safety margin -> 9000 kbps allocatable
    ac = AdmissionController(bottleneck_capacity_kbps=10000.0, safety_margin=0.10)

    # 1. Ample capacity: Current in-use = 2000k, new voice flow (100k) -> ADMIT
    d1 = ac.evaluate(flow_id="f1", class_name="voice", requested_kbps=100.0, current_in_use_kbps=2000.0)
    assert d1.decision == "admit"
    assert d1.granted_rate_kbps == 100.0

    # 2. Ample capacity for HD video (3000k) -> ADMIT
    d2 = ac.evaluate(flow_id="f2", class_name="video", requested_kbps=3000.0, current_in_use_kbps=2000.0)
    assert d2.decision == "admit"
    assert d2.granted_rate_kbps == 3000.0

    # 3. Constrained capacity: Current in-use = 7500k (1500k left). Video request -> DOWNGRADE to SD (1200k)
    d3 = ac.evaluate(flow_id="f3", class_name="video", requested_kbps=3000.0, current_in_use_kbps=7500.0)
    assert d3.decision == "downgrade"
    assert d3.granted_rate_kbps == 1200.0

    # 4. Saturated capacity: Current in-use = 8800k (200k left). Video request -> REJECT
    d4 = ac.evaluate(flow_id="f4", class_name="video", requested_kbps=3000.0, current_in_use_kbps=8800.0)
    assert d4.decision == "reject"
    assert d4.granted_rate_kbps == 0.0


def test_qos_routing_path_and_reroute():
    router = QoSRouter(alpha=1.0, beta=10.0)

    # 1. Uncongested: s1 -> s2 -> s4 has lowest delay (2ms + 1ms = 3ms vs 15ms + 1ms = 16ms)
    path, cost, is_rerouted = router.compute_path("s1", "s4", flow_class="voice")
    assert path == ["s1", "s2", "s4"]
    assert is_rerouted is False

    # 2. Congest the primary bottleneck link (s1 -> s2) to 92% utilization
    router.update_link_utilization("s1", "s2", 0.92)

    # 3. Path calculation under congestion -> Real-time flow is rerouted via alternate path s3!
    path_cong, cost_cong, is_rerouted_cong = router.compute_path("s1", "s4", flow_class="video")
    assert path_cong == ["s1", "s3", "s4"]
    assert is_rerouted_cong is True

    # 4. Bulk flow remains pinned to default path s2
    bulk_path, bulk_cost, bulk_rerouted = router.compute_path("s1", "s4", flow_class="bulk")
    assert bulk_path == ["s1", "s2", "s4"]
    assert bulk_rerouted is False
