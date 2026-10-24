"""
REST routes for Demo Evaluation and Automated Scenarios.
"""

import json
import os
import time
from typing import Any, Dict

from fastapi import APIRouter
from pydantic import BaseModel

from backend.services.telemetry_service import telemetry_service
from network.scenario import DEFAULT_BASELINE_PATH, run_scenario

router = APIRouter(prefix="/api/scenario", tags=["scenario"])


class StartScenarioRequest(BaseModel):
    qos_enabled: bool = True
    duration_seconds: int = 65


@router.post("/start")
def start_demo_scenario(req: StartScenarioRequest) -> Dict[str, Any]:
    """Starts live scripted demonstration scenario."""
    telemetry_service.start_scenario(qos_enabled=req.qos_enabled)
    return {
        "status": "started",
        "qos_enabled": req.qos_enabled,
        "duration_seconds": req.duration_seconds,
        "start_time": telemetry_service.scenario_start_time,
    }


@router.post("/stop")
def stop_demo_scenario() -> Dict[str, Any]:
    telemetry_service.stop_scenario()
    return {"status": "stopped"}


@router.get("/status")
def get_scenario_status() -> Dict[str, Any]:
    running = telemetry_service.scenario_running
    elapsed = time.time() - telemetry_service.scenario_start_time if running else 0.0
    return {
        "running": running,
        "elapsed_seconds": round(elapsed, 1),
        "qos_enabled": telemetry_service.qos_enabled,
    }


@router.get("/report")
def get_comparison_report() -> Dict[str, Any]:
    """
    Returns side-by-side comparison report:
    Baseline (QoS OFF) vs Prioritized (QoS ON) with percentage improvements.
    """
    baseline_data = None
    if os.path.exists(DEFAULT_BASELINE_PATH):
        try:
            with open(DEFAULT_BASELINE_PATH, "r", encoding="utf-8") as f:
                baseline_data = json.load(f)
        except Exception:
            pass

    if not baseline_data:
        # Generate on-demand if not pre-cached
        baseline_data = run_scenario(qos_enabled=False, duration_seconds=65)

    # Generate QoS ON run
    qos_on_data = run_scenario(qos_enabled=True, duration_seconds=65)

    base_summary = baseline_data["summary"]
    qos_summary = qos_on_data["summary"]

    # Compute percentage improvements
    # Latency improvement: (base - qos) / base * 100
    lat_imp = (
        (base_summary["avg_voice_latency_ms"] - qos_summary["avg_voice_latency_ms"])
        / base_summary["avg_voice_latency_ms"]
    ) * 100.0
    jit_imp = (
        (base_summary["avg_voice_jitter_ms"] - qos_summary["avg_voice_jitter_ms"])
        / max(0.1, base_summary["avg_voice_jitter_ms"])
    ) * 100.0
    loss_imp = (
        (base_summary["avg_voice_loss_percent"] - qos_summary["avg_voice_loss_percent"])
        / max(0.1, base_summary["avg_voice_loss_percent"])
    ) * 100.0

    return {
        "timestamp": time.time(),
        "baseline_off": base_summary,
        "qos_on": qos_summary,
        "improvement_percentages": {
            "latency_reduction_percent": round(lat_imp, 1),
            "jitter_reduction_percent": round(jit_imp, 1),
            "loss_elimination_percent": round(min(100.0, loss_imp), 1),
        },
        "baseline_trajectory": baseline_data["trajectory"],
        "qos_on_trajectory": qos_on_data["trajectory"],
    }
