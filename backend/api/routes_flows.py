"""
REST routes for active flows and admission control decisions.
"""

import time
from typing import Any, Dict, List
from fastapi import APIRouter
from pydantic import BaseModel

from backend.database import get_recent_admission_decisions, save_admission_decision
from backend.models.schemas import AdmissionDecisionDB, FlowItem
from backend.services.telemetry_service import telemetry_service
from controller.admission import AdmissionController

router = APIRouter(prefix="/api/flows", tags=["flows"])

admission_controller = AdmissionController()


class AdmissionEvaluateRequest(BaseModel):
    flow_id: str
    class_name: str
    requested_kbps: float
    current_in_use_kbps: float = 7200.0


@router.get("", response_model=List[FlowItem])
def list_active_flows():
    """Returns active network flows with 5-tuple, classification, queue, rate, and admission status."""
    return telemetry_service.get_active_flows()


@router.get("/decisions", response_model=List[Dict[str, Any]])
def list_admission_decisions(limit: int = 50):
    """Returns recent admission control decisions with reasoning."""
    recs = get_recent_admission_decisions(limit=limit)
    if not recs:
        # Provide baseline decisions from initial active flows
        return [
            {
                "flow_id": "flow-voip-1",
                "class_name": "voice",
                "decision": "admit",
                "granted_rate_kbps": 100.0,
                "reason": "Guaranteed bandwidth headroom available on bottleneck s1->s2.",
                "timestamp": time.time() - 45,
            },
            {
                "flow_id": "flow-video-1",
                "class_name": "video",
                "decision": "admit",
                "granted_rate_kbps": 3200.0,
                "reason": "HD video stream admitted with full reservation.",
                "timestamp": time.time() - 30,
            },
            {
                "flow_id": "flow-video-2",
                "class_name": "video",
                "decision": "downgrade",
                "granted_rate_kbps": 1200.0,
                "reason": "Congested link: Video stream downgraded to standard definition (SD).",
                "timestamp": time.time() - 15,
            },
            {
                "flow_id": "flow-video-3",
                "class_name": "video",
                "decision": "reject",
                "granted_rate_kbps": 0.0,
                "reason": "Insufficient capacity: Video rejected to protect voice SLAs.",
                "timestamp": time.time() - 5,
            },
        ]
    return [r.model_dump() for r in recs]


@router.post("/evaluate-admission")
def evaluate_flow_admission(req: AdmissionEvaluateRequest) -> Dict[str, Any]:
    """Evaluates an incoming voice/video flow admission against bottleneck path capacity."""
    decision = admission_controller.evaluate(
        flow_id=req.flow_id,
        class_name=req.class_name,
        requested_kbps=req.requested_kbps,
        current_in_use_kbps=req.current_in_use_kbps,
    )
    save_admission_decision(
        AdmissionDecisionDB(
            timestamp=decision.timestamp,
            flow_id=decision.flow_id,
            class_name=decision.class_name,
            decision=decision.decision,
            granted_rate_kbps=decision.granted_rate_kbps,
            reason=decision.reason,
        )
    )
    return {
        "flow_id": decision.flow_id,
        "class_name": decision.class_name,
        "decision": decision.decision,
        "granted_rate_kbps": decision.granted_rate_kbps,
        "reason": decision.reason,
        "timestamp": decision.timestamp,
    }
