import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_endpoint():
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["features"]["fao56_simulation"] is True

def test_presets_endpoint():
    resp = client.get("/api/farm/presets")
    assert resp.status_code == 200
    presets = resp.json()
    assert len(presets) >= 3
    assert any(p["id"] == "salinas-valley" for p in presets)

def test_crops_metadata_endpoint():
    resp = client.get("/api/farm/crops")
    assert resp.status_code == 200
    crops = resp.json()
    assert "tomato" in crops
    assert "maize" in crops
    assert crops["tomato"]["kc_mid"] > 1.0

def test_simulation_run_endpoint():
    payload = {
        "latitude": 36.6777,
        "longitude": -121.6555,
        "zone_id": "zone-test",
        "zone_name": "Test Block",
        "crop": "tomato",
        "soil": "loam",
        "area_acres": 25.0,
        "growth_stage": "mid",
        "initial_depletion_fraction": 0.20
    }
    resp = client.post("/api/simulation/run", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["daily_results"]) == 14
    assert data["summary"]["current_status"] in ("OPTIMAL", "MILD_STRESS", "CRITICAL_DROUGHT", "WATERLOGGED")

def test_prescription_calculation_endpoint():
    payload = {
        "zone_id": "zone-1",
        "water_deficit_liters": 100000.0,
        "area_acres": 15.0,
        "irrigation_type": "drip",
        "pump_flow_rate_lpm": 350.0,
        "electricity_cost_kwh": 0.15,
        "pump_power_kw": 7.5
    }
    resp = client.post("/api/prescription/calculate", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["recommended_water_liters"] > 100000.0  # Drip efficiency adjustment
    assert data["pump_runtime_hours"] > 0.0
    assert data["estimated_energy_cost"] > 0.0

def test_advisor_chat_endpoint():
    payload = {
        "message": "When should I water my tomato crop on loam soil?",
        "zone_id": "zone-1"
    }
    resp = client.post("/api/advisor/chat", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "reply" in data
    assert len(data["reply"]) > 50
