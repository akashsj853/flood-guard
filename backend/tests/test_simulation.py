"""Tests: What-If simulation API + scenario math."""
from __future__ import annotations

import pytest

from app.services import prediction_service as ps
from app.services import weather_service


def test_simulation_endpoint(client):
    body = {"zone_id": "Z001", "adjustments": {"rainfall_multiplier": 2.0}}
    r = client.post("/api/simulation", json=body)
    assert r.status_code == 200
    data = r.json()
    assert data["zone_id"] == "Z001"
    assert "baseline_probability" in data and "scenario_probability" in data
    assert data["delta"] == pytest.approx(
        round(data["scenario_probability"] - data["baseline_probability"], 2), abs=1e-6)


def test_simulation_unknown_zone(client):
    r = client.post("/api/simulation", json={"zone_id": "ZZZ"})
    assert r.status_code == 404


def test_scenario_wetter_than_baseline(client):
    base = client.post("/api/simulation",
                       json={"zone_id": "Z001", "adjustments": {}}).json()
    wet = client.post("/api/simulation",
                      json={"zone_id": "Z001", "adjustments": {"rainfall_multiplier": 3.0}}).json()
    assert wet["scenario_probability"] >= base["scenario_probability"]


def test_drainage_improvement_lowers_risk(client):
    base = client.post("/api/simulation",
                       json={"zone_id": "Z001", "adjustments": {}}).json()
    improved = client.post("/api/simulation",
                           json={"zone_id": "Z001",
                                 "adjustments": {"drainage_delta": 50, "impervious_delta": -30}}).json()
    assert improved["scenario_probability"] <= base["scenario_probability"]


def test_simulation_validation_empty_body(client):
    # Missing required zone_id -> 422 validation error.
    r = client.post("/api/simulation", json={})
    assert r.status_code == 422
