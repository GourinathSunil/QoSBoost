"""
Unit and integration tests for OpenFlow 1.3 Meters and Bandwidth Admission Control (Sections 3.3b, 3.6).
"""

import time
import pytest
from controller.admission import AdmissionController
from controller.policy_engine import MeterManager
from backend.database import (
    init_db,
    save_admission_decision,
    get_recent_admission_decisions,
    save_policy_config,
    get_latest_policy_config,
)
from backend.models.schemas import AdmissionDecisionDB, PolicyConfigDB


def test_of13_meter_manager_and_hit_counters():
    mm = MeterManager()
    stats = mm.get_meter_stats()
    assert len(stats) >= 2  # Flooder meter (1) and Bulk meter (2)

    flooder_meter = mm.meters[1]
    assert flooder_meter["action"] == "drop"
    assert flooder_meter["rate_kbps"] == 1000

    # Record hit when traffic exceeds meter threshold
    event = mm.record_hit(meter_id=1, excess_kbps=2500.0)
    assert event is not None
    assert event["event_type"] == "METER_DROP"
    assert flooder_meter["drop_byte_count"] > 0
    assert flooder_meter["drop_packet_count"] > 0


def test_admission_control_decisions():
    ac = AdmissionController(bottleneck_capacity_kbps=10000.0, safety_margin=0.10)
    # Total allocatable = 9000 kbps

    # 1. Voice flow with ample headroom -> admit
    d1 = ac.evaluate("flow-v1", "voice", requested_kbps=100.0, current_in_use_kbps=4000.0)
    assert d1.decision == "admit"
    assert d1.granted_rate_kbps == 100.0

    # 2. HD Video flow with ample headroom -> admit
    d2 = ac.evaluate("flow-vid1", "video", requested_kbps=3000.0, current_in_use_kbps=4000.0)
    assert d2.decision == "admit"
    assert d2.granted_rate_kbps == 3000.0

    # 3. Video flow when headroom is tight (~1500 kbps left) -> downgrade to SD (1200 kbps)
    d3 = ac.evaluate("flow-vid2", "video", requested_kbps=3000.0, current_in_use_kbps=7500.0)
    assert d3.decision == "downgrade"
    assert d3.granted_rate_kbps == 1200.0

    # 4. Video flow when link is fully saturated (8500 kbps used out of 9000 kbps) -> reject
    d4 = ac.evaluate("flow-vid3", "video", requested_kbps=3000.0, current_in_use_kbps=8600.0)
    assert d4.decision == "reject"
    assert d4.granted_rate_kbps == 0.0


def test_sqlite_persistence_for_policy_and_admission():
    init_db()
    now = time.time()

    # Save and retrieve policy config in SQLite
    p = PolicyConfigDB(
        timestamp=now,
        active_profile="Voice-First",
        qos_enabled=True,
        raw_yaml="active_profile: Voice-First",
    )
    save_policy_config(p)
    loaded_p = get_latest_policy_config()
    assert loaded_p is not None
    assert loaded_p.active_profile == "Voice-First"

    # Save and retrieve admission decisions in SQLite
    dec = AdmissionDecisionDB(
        timestamp=now,
        flow_id="test-flow-voice",
        class_name="voice",
        decision="admit",
        granted_rate_kbps=100.0,
        reason="Test reservation",
    )
    save_admission_decision(dec)
    recs = get_recent_admission_decisions(limit=5)
    assert any(r.flow_id == "test-flow-voice" for r in recs)
