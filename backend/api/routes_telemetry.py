"""
REST routes for telemetry and historical metrics.
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Query

from backend.database import get_recent_snapshots
from backend.services.telemetry_service import telemetry_service

router = APIRouter(prefix="/api/telemetry", tags=["telemetry"])


@router.get("/latest")
def get_latest_telemetry() -> Optional[Dict[str, Any]]:
    """Returns the most recent network telemetry snapshot."""
    snap = telemetry_service.get_latest_snapshot()
    if snap is None:
        # Generate initial sample if buffer is still empty
        sample = telemetry_service.scenario_engine.tick(elapsed=1.0)
        return sample
    return snap


@router.get("/history")
def get_telemetry_history(limit: int = Query(default=60, ge=1, le=300)) -> List[Dict[str, Any]]:
    """Returns rolling time-series window of recent metric snapshots."""
    in_memory = telemetry_service.get_history(limit=limit)
    if in_memory:
        return in_memory

    # Fallback to persistent SQLite history
    db_records = get_recent_snapshots(limit=limit)
    return [
        {
            "timestamp": r.timestamp,
            "qos_enabled": r.qos_enabled,
            "link_utilization": r.link_utilization,
            "voice": {
                "latency_ms": r.voice_latency_ms,
                "jitter_ms": r.voice_jitter_ms,
                "loss_percent": r.voice_loss_percent,
                "throughput_kbps": r.voice_throughput_kbps,
            },
            "video": {"throughput_kbps": r.video_throughput_kbps},
            "bulk": {"throughput_kbps": r.bulk_throughput_kbps},
            "path": r.active_path,
        }
        for r in db_records
    ]
