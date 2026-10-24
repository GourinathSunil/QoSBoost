"""
Unit and integration tests for Phase 5: FastAPI Backend REST API and Telemetry.
"""

from fastapi.testclient import TestClient

from backend.database import init_db
from backend.main import app

init_db()
client = TestClient(app)


def test_root_endpoint():
    res = client.get("/")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "online"
    assert data["system"] == "QoSBoost SDN QoS Management"


def test_topology_endpoint():
    res = client.get("/api/topology")
    assert res.status_code == 200
    topo = res.json()
    assert len(topo["switches"]) == 4
    assert len(topo["hosts"]) == 6
    assert len(topo["links"]) >= 10


def test_telemetry_latest():
    res = client.get("/api/telemetry/latest")
    assert res.status_code == 200
    data = res.json()
    assert "voice" in data
    assert "link_utilization" in data


def test_flows_endpoint():
    res = client.get("/api/flows")
    assert res.status_code == 200
    flows = res.json()
    assert len(flows) >= 4
    assert any(f["class_name"] == "voice" for f in flows)
    assert any(f["class_name"] == "video" for f in flows)


def test_policies_get_and_put():
    # 1. GET policies
    res = client.get("/api/policies")
    assert res.status_code == 200
    data = res.json()
    assert "active_profile" in data
    assert "Balanced" in data["profiles"]

    # 2. Preset switch
    res_switch = client.post("/api/policies/preset/Voice-First")
    assert res_switch.status_code == 200
    assert res_switch.json()["active_profile"] == "Voice-First"

    # Reset back to Balanced
    client.post("/api/policies/preset/Balanced")


def test_scenario_status_and_report():
    # Scenario status
    res_stat = client.get("/api/scenario/status")
    assert res_stat.status_code == 200
    assert "running" in res_stat.json()

    # Scenario report
    res_rep = client.get("/api/scenario/report")
    assert res_rep.status_code == 200
    rep = res_rep.json()
    assert "baseline_off" in rep
    assert "qos_on" in rep
    assert "improvement_percentages" in rep
    assert rep["improvement_percentages"]["latency_reduction_percent"] > 50.0
