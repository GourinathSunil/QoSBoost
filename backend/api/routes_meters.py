"""
REST routes for OpenFlow 1.3 Meters and Rate-limiting Hit Counters.
"""

import time
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.database import save_event
from backend.models.schemas import EventRecordDB
from controller.policy_engine import MeterManager

router = APIRouter(prefix="/api/meters", tags=["meters"])

meter_manager = MeterManager()


class UpdateMeterRequest(BaseModel):
    rate_kbps: Optional[int] = None
    burst_kbps: Optional[int] = None
    action: Optional[str] = None


@router.get("", response_model=List[Dict[str, Any]])
def list_meters() -> List[Dict[str, Any]]:
    """Returns active OpenFlow 1.3 meters and per-meter hit counters."""
    return meter_manager.get_meter_stats()


@router.get("/{meter_id}")
def get_meter(meter_id: int) -> Dict[str, Any]:
    if meter_id not in meter_manager.meters:
        raise HTTPException(status_code=404, detail=f"Meter {meter_id} not found")
    return meter_manager.meters[meter_id]


@router.put("/{meter_id}")
def update_meter(meter_id: int, req: UpdateMeterRequest) -> Dict[str, Any]:
    """Updates meter rate or burst limits live."""
    if meter_id not in meter_manager.meters:
        raise HTTPException(status_code=404, detail=f"Meter {meter_id} not found")

    m = meter_manager.meters[meter_id]
    before_rate = m["rate_kbps"]

    if req.rate_kbps is not None:
        m["rate_kbps"] = req.rate_kbps
    if req.burst_kbps is not None:
        m["burst_kbps"] = req.burst_kbps
    if req.action is not None:
        m["action"] = req.action

    save_event(
        EventRecordDB(
            timestamp=time.time(),
            event_type="METER_CONFIG",
            message=f"OpenFlow 1.3 Meter #{meter_id} ({m['name']}) rate updated to {m['rate_kbps']} kbps",
            reason="User modification via dashboard",
            before_value=f"{before_rate} kbps",
            after_value=f"{m['rate_kbps']} kbps",
        )
    )
    return m
