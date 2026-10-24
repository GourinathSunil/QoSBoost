"""
REST routes for Audit Log Events (adjustments, admission decisions, meter hits, reroutes).
"""

from typing import Any, Dict, List

from fastapi import APIRouter, Query

from backend.database import get_all_events
from backend.services.telemetry_service import telemetry_service

router = APIRouter(prefix="/api/events", tags=["events"])


@router.get("")
def list_events(limit: int = Query(default=50, ge=1, le=200)) -> List[Dict[str, Any]]:
    """Returns chronologically ordered audit events."""
    db_events = get_all_events(limit=limit)

    # Also collect any in-flight events from scenario engine
    live_engine_events = getattr(telemetry_service.scenario_engine, "events", [])

    combined = []
    for ev in live_engine_events:
        combined.append(
            {
                "timestamp": ev.get("timestamp"),
                "event_type": ev.get("type", "ADAPTATION"),
                "message": ev.get("message"),
                "reason": ev.get("reason"),
                "source": "live_engine",
            }
        )

    for r in db_events:
        combined.append(
            {
                "id": r.id,
                "timestamp": r.timestamp,
                "event_type": r.event_type,
                "message": r.message,
                "reason": r.reason,
                "before_value": r.before_value,
                "after_value": r.after_value,
                "source": "database",
            }
        )

    return combined[:limit]
