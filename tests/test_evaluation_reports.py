"""
Unit and integration tests for Evaluation Module and Export Reports (Section 3.8).
"""

import os
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from network.scenario import build_comparison_report, export_charts

client = TestClient(app)


def test_comparison_report_structure():
    report = build_comparison_report(duration_seconds=30)
    assert "baseline_off" in report
    assert "qos_on" in report
    assert "improvement_percentages" in report

    imp = report["improvement_percentages"]
    assert imp["latency_reduction_percent"] > 50.0
    assert imp["jitter_reduction_percent"] > 50.0
    assert imp["loss_elimination_percent"] >= 90.0


def test_chart_exports_png_and_pdf(tmp_path):
    report = build_comparison_report(duration_seconds=20)
    png_path = str(tmp_path / "test_report.png")
    pdf_path = str(tmp_path / "test_report.pdf")

    out_png, out_pdf = export_charts(report, png_path=png_path, pdf_path=pdf_path)
    assert os.path.exists(out_png)
    assert os.path.getsize(out_png) > 1000
    assert os.path.exists(out_pdf)
    assert os.path.getsize(out_pdf) > 1000


def test_api_classifier_routes():
    # GET /api/classifier/status
    res = client.get("/api/classifier/status")
    assert res.status_code == 200
    data = res.json()
    assert "ml_mode" in data
    assert "model_info" in data
    assert "overall_accuracy" in data["model_info"]

    # POST /api/classifier/mode
    res = client.post("/api/classifier/mode", json={"ml_mode": True})
    assert res.status_code == 200
    assert res.json()["ml_mode"] is True

    # Reset to False
    res = client.post("/api/classifier/mode", json={"ml_mode": False})
    assert res.status_code == 200
    assert res.json()["ml_mode"] is False


def test_api_meters_routes():
    res = client.get("/api/meters")
    assert res.status_code == 200
    meters = res.json()
    assert len(meters) >= 2

    # Update meter
    res = client.put("/api/meters/1", json={"rate_kbps": 1200})
    assert res.status_code == 200
    assert res.json()["rate_kbps"] == 1200


def test_api_scenario_report_endpoints():
    # GET /api/scenario/report
    res = client.get("/api/scenario/report")
    assert res.status_code == 200
    data = res.json()
    assert "improvement_percentages" in data

    # GET /api/scenario/report/png
    res_png = client.get("/api/scenario/report/png")
    assert res_png.status_code == 200
    assert "image/png" in res_png.headers["content-type"]

    # GET /api/scenario/report/pdf
    res_pdf = client.get("/api/scenario/report/pdf")
    assert res_pdf.status_code == 200
    assert "application/pdf" in res_pdf.headers["content-type"]
