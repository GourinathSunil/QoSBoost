r"""
QoSBoost Admission Controller.

Evaluates newly arriving real-time flows (voice, video) against remaining path headroom.
Decisions:
1. 'admit': Sufficient bandwidth available within capacity and safety margin.
2. 'downgrade': Insufficient bandwidth for full HD video; admitted with lowered rate.
3. 'reject': Bottleneck fully saturated; rejected to prevent SLA degradation of existing active flows.
"""

import logging
import time
from dataclasses import dataclass

logger = logging.getLogger("qosboost.controller.admission")


@dataclass
class AdmissionDecision:
    flow_id: str
    class_name: str
    decision: str  # admit, downgrade, reject
    granted_rate_kbps: float
    reason: str
    timestamp: float


class AdmissionController:
    """Bandwidth-aware admission controller."""

    def __init__(self, bottleneck_capacity_kbps: float = 10000.0, safety_margin: float = 0.10):
        self.capacity_kbps = bottleneck_capacity_kbps
        self.safety_margin = safety_margin
        # Maximum allowed active allocation before admission gating
        self.max_allocatable_kbps = bottleneck_capacity_kbps * (1.0 - safety_margin)

    def evaluate(
        self, flow_id: str, class_name: str, requested_kbps: float, current_in_use_kbps: float
    ) -> AdmissionDecision:
        """Determines admission status for incoming flow."""
        available_kbps = max(0.0, self.max_allocatable_kbps - current_in_use_kbps)
        now = time.time()

        # 1. Voice traffic (critical priority, small requirement ~100 kbps)
        if class_name == "voice":
            if available_kbps >= requested_kbps:
                decision = "admit"
                granted = requested_kbps
                reason = "Guaranteed bandwidth headroom available."
            elif available_kbps >= (requested_kbps * 0.5):
                # Voice fallback to lower bitrate codec (e.g. G.729 at 32 kbps)
                decision = "downgrade"
                granted = requested_kbps * 0.5
                reason = "Headroom constrained: Adapted to low-bitrate voice codec."
            else:
                decision = "reject"
                granted = 0.0
                reason = "Bottleneck saturated: Voice call rejected to preserve existing calls."

        # 2. Video traffic (high bandwidth ~3000 kbps)
        elif class_name == "video":
            if available_kbps >= requested_kbps:
                decision = "admit"
                granted = requested_kbps
                reason = "HD video stream admitted with full reservation."
            elif available_kbps >= 1200.0:
                decision = "downgrade"
                granted = 1200.0
                reason = "Congested link: Video stream downgraded to standard definition (SD)."
            else:
                decision = "reject"
                granted = 0.0
                reason = "Insufficient capacity: Video rejected to protect voice SLAs."

        # 3. Best-effort / Bulk traffic (always admitted into scavenger queue)
        else:
            decision = "admit"
            granted = min(requested_kbps, available_kbps)
            reason = "Elastic bulk flow admitted into scavenger queue."

        res = AdmissionDecision(
            flow_id=flow_id,
            class_name=class_name,
            decision=decision,
            granted_rate_kbps=granted,
            reason=reason,
            timestamp=now,
        )
        logger.info(
            "Admission Control [%s] flow %s: %s (%s)", class_name, flow_id, decision, reason
        )
        return res
