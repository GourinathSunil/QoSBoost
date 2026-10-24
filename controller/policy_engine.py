r"""
QoSBoost Policy Engine: Dynamic Bandwidth Allocation and OpenFlow 1.3 Meters.

1. DynamicBandwidthAllocator:
   - Evaluates link utilization against high-water (80%) and low-water (60%) thresholds.
   - Triggers dynamic rate adjustment when latency or jitter targets are violated.
   - Employs hysteresis and a cooldown timer (4s) to eliminate flapping and oscillations.
   - Emits structured audit events for every adjustment.

2. MeterManager:
   - Configures OpenFlow 1.3 meters for rate limiting and rogue traffic mitigation.
   - Tracks meter hit counters and dropped/remarked bytes.
"""

import logging
import time
from typing import Any, Callable, Dict, List, Optional

from controller.queue_manager import QueueManager

logger = logging.getLogger("qosboost.controller.policy_engine")


class DynamicBandwidthAllocator:
    """Dynamic Bandwidth Allocation controller with hysteresis."""

    def __init__(
        self,
        queue_manager: Optional[QueueManager] = None,
        high_watermark: float = 0.80,
        low_watermark: float = 0.60,
        cooldown_seconds: float = 4.0,
        event_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    ):
        self.qm = queue_manager or QueueManager()
        self.high_watermark = high_watermark
        self.low_watermark = low_watermark
        self.cooldown_seconds = cooldown_seconds
        self.event_callback = event_callback

        self.is_throttled = False
        self.last_adjustment_time = 0.0
        self.base_bulk_max_kbps = 8000
        self.current_bulk_max_kbps = 8000
        self.min_bulk_floor_kbps = 200

    def evaluate(
        self,
        link_utilization: float,
        voice_latency_ms: float = 10.0,
        target_latency_ms: float = 30.0,
        current_time: Optional[float] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Evaluates current telemetric conditions and adjusts queue rates if thresholds are crossed.
        Returns the event dict if an adjustment occurred, otherwise None.
        """
        now = current_time if current_time is not None else time.time()

        # Check cooldown to prevent rapid flapping
        if (now - self.last_adjustment_time) < self.cooldown_seconds:
            return None

        # Condition A: Severe congestion or latency target violation -> Throttle bulk
        if link_utilization >= self.high_watermark or voice_latency_ms > target_latency_ms:
            if self.current_bulk_max_kbps > self.min_bulk_floor_kbps:
                before_val = self.current_bulk_max_kbps
                # Reduce by 35%
                new_rate = max(self.min_bulk_floor_kbps, int(self.current_bulk_max_kbps * 0.65))
                self.current_bulk_max_kbps = new_rate
                self.qm.update_queue_rate(queue_id=3, max_rate_kbps=new_rate)
                self.is_throttled = True
                self.last_adjustment_time = now

                event = {
                    "timestamp": round(now, 2),
                    "event_type": "ADAPTATION",
                    "message": f"Link congestion ({int(link_utilization*100)}% util). Bulk queue clamped {before_val}k -> {new_rate}k.",
                    "reason": "High-watermark threshold / latency SLA violation",
                    "before_value": f"{before_val} kbps",
                    "after_value": f"{new_rate} kbps",
                }
                logger.info("Dynamic Allocation Triggered: %s", event["message"])
                if self.event_callback:
                    self.event_callback(event)
                return event

        # Condition B: Under low watermark and currently throttled -> Gradually release bulk
        elif link_utilization <= self.low_watermark and self.is_throttled:
            before_val = self.current_bulk_max_kbps
            new_rate = min(self.base_bulk_max_kbps, int(self.current_bulk_max_kbps * 1.5))
            self.current_bulk_max_kbps = new_rate
            self.qm.update_queue_rate(queue_id=3, max_rate_kbps=new_rate)
            self.last_adjustment_time = now

            if new_rate >= self.base_bulk_max_kbps:
                self.is_throttled = False

            event = {
                "timestamp": round(now, 2),
                "event_type": "RECOVERY",
                "message": f"Link recovered ({int(link_utilization*100)}% util). Bulk queue restored {before_val}k -> {new_rate}k.",
                "reason": "Low-watermark hysteresis release",
                "before_value": f"{before_val} kbps",
                "after_value": f"{new_rate} kbps",
            }
            logger.info("Dynamic Recovery Triggered: %s", event["message"])
            if self.event_callback:
                self.event_callback(event)
            return event

        return None


class MeterManager:
    """Manages OpenFlow 1.3 meters."""

    def __init__(self):
        # Meter ID -> Config
        self.meters: Dict[int, Dict[str, Any]] = {
            1: {
                "id": 1,
                "name": "flooder_meter",
                "rate_kbps": 1000,
                "burst_kbps": 200,
                "action": "drop",
                "packet_in_count": 0,
                "drop_packet_count": 0,
                "drop_byte_count": 0,
            },
            2: {
                "id": 2,
                "name": "bulk_meter",
                "rate_kbps": 6000,
                "burst_kbps": 1000,
                "action": "dscp_remark",
                "remark_dscp": 8,
                "packet_in_count": 0,
                "drop_packet_count": 0,
                "drop_byte_count": 0,
            },
        }

    def record_hit(self, meter_id: int, excess_kbps: float) -> Optional[Dict[str, Any]]:
        """Updates meter stats and returns an event if rate exceeded."""
        if meter_id not in self.meters:
            return None

        m = self.meters[meter_id]
        if excess_kbps > 0:
            dropped_bytes = int((excess_kbps * 1000 / 8))
            m["drop_byte_count"] += dropped_bytes
            m["drop_packet_count"] += int(dropped_bytes / 500)

            event = {
                "timestamp": time.time(),
                "event_type": "METER_DROP",
                "message": f"OF1.3 Meter #{meter_id} ({m['name']}) enforced: rate limited {int(excess_kbps)} kbps.",
                "reason": f"Traffic exceeded meter band ({m['rate_kbps']} kbps)",
                "before_value": f"{m['rate_kbps']} kbps target",
                "after_value": f"{m['action']} excess",
            }
            return event
        return None

    def get_meter_stats(self) -> List[Dict[str, Any]]:
        return list(self.meters.values())
