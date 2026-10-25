"""
REST routes for Demo Evaluation and Automated Scenarios.
"""

import json
import os
import time
from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from backend.services.telemetry_service import telemetry_service
from network.scenario import (
    DEFAULT_BASELINE_PATH,
    build_comparison_report,
    export_charts,
    run_scenario,
)

router = APIRouter(prefix="/api/scenario", tags=["scenario"])

PNG_REPORT_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "network", "scenarios", "evaluation_summary.png"
)
PDF_REPORT_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "network", "scenarios", "evaluation_summary.pdf"
)


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
    rep = build_comparison_report()
    return rep


@router.post("/report/generate")
def generate_fresh_report() -> Dict[str, Any]:
    """Forces re-run of comparison evaluation and exports PNG + PDF charts."""
    rep = build_comparison_report()
    export_charts(rep, png_path=PNG_REPORT_PATH, pdf_path=PDF_REPORT_PATH)
    return {
        "status": "generated",
        "improvement_percentages": rep["improvement_percentages"],
        "png_path": PNG_REPORT_PATH,
        "pdf_path": PDF_REPORT_PATH,
    }


@router.get("/report/png")
def get_report_png():
    """Serves the generated high-resolution comparison chart in PNG format."""
    if not os.path.exists(PNG_REPORT_PATH):
        rep = build_comparison_report()
        export_charts(rep, png_path=PNG_REPORT_PATH, pdf_path=PDF_REPORT_PATH)

    if not os.path.exists(PNG_REPORT_PATH):
        raise HTTPException(status_code=404, detail="PNG report not found")

    return FileResponse(
        PNG_REPORT_PATH,
        media_type="image/png",
        filename="qosboost-evaluation-summary.png",
    )


@router.get("/report/pdf")
def get_report_pdf():
    """Serves the generated multi-page evaluation report in PDF format."""
    if not os.path.exists(PDF_REPORT_PATH):
        rep = build_comparison_report()
        export_charts(rep, png_path=PNG_REPORT_PATH, pdf_path=PDF_REPORT_PATH)

    if not os.path.exists(PDF_REPORT_PATH):
        raise HTTPException(status_code=404, detail="PDF report not found")

    return FileResponse(
        PDF_REPORT_PATH,
        media_type="application/pdf",
        filename="qosboost-evaluation-summary.pdf",
    )
