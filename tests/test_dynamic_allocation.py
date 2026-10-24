"""
Unit tests for Phase 6: Dynamic Bandwidth Allocation and OF1.3 Meters.
"""

import pytest
from controller.policy_engine import DynamicBandwidthAllocator, MeterManager
from controller.queue_manager import QueueManager


def test_dynamic_allocation_trigger_and_hysteresis():
    qm = QueueManager()
    allocator = DynamicBandwidthAllocator(
        queue_manager=qm,
        high_watermark=0.80,
        low_watermark=0.60,
        cooldown_seconds=4.0
    )

    t0 = 100.0
    # 1. Normal utilization (50%) -> No adjustment
    ev1 = allocator.evaluate(link_utilization=0.50, voice_latency_ms=10.0, current_time=t0)
    assert ev1 is None
    assert allocator.current_bulk_max_kbps == 8000

    # 2. Congestion spike (85% utilization) -> Triggers throttle
    t1 = 101.0
    ev2 = allocator.evaluate(link_utilization=0.85, voice_latency_ms=12.0, current_time=t1)
    assert ev2 is not None
    assert ev2["event_type"] == "ADAPTATION"
    assert allocator.current_bulk_max_kbps < 8000
    assert allocator.is_throttled is True

    # 3. Flapping prevention: Next tick within cooldown (t=102.0) -> No change even under high util
    t2 = 102.0
    ev3 = allocator.evaluate(link_utilization=0.90, voice_latency_ms=15.0, current_time=t2)
    assert ev3 is None

    # 4. Hysteresis release: After cooldown (t=106.0) with low utilization (45%) -> Triggers recovery
    t3 = 106.0
    rate_before = allocator.current_bulk_max_kbps
    ev4 = allocator.evaluate(link_utilization=0.45, voice_latency_ms=9.0, current_time=t3)
    assert ev4 is not None
    assert ev4["event_type"] == "RECOVERY"
    assert allocator.current_bulk_max_kbps > rate_before


def test_meter_manager():
    mm = MeterManager()
    stats = mm.get_meter_stats()
    assert len(stats) == 2
    assert stats[0]["name"] == "flooder_meter"
    assert stats[0]["rate_kbps"] == 1000

    # Record excessive burst (3000 kbps - 1000 limit = 2000 excess)
    ev = mm.record_hit(meter_id=1, excess_kbps=2000.0)
    assert ev is not None
    assert ev["event_type"] == "METER_DROP"
    assert mm.meters[1]["drop_byte_count"] > 0
