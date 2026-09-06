"""Tests: alerts API (generation, dedup, acknowledge, edge cases)."""
from __future__ import annotations

import pytest


def test_alerts_list_returns_shape(client):
    r = client.get("/api/alerts", params={"demo": "true"})
    assert r.status_code == 200
    data = r.json()
    assert "count" in data and "alerts" in data
    if data["alerts"]:
        a = data["alerts"][0]
        for k in ("alert_id", "zone_id", "risk", "status", "probability"):
            assert k in a


def test_alerts_generated_for_high_risk(client):
    # With demo weather the high-precip scenario should yield HIGH+ alerts.
    r = client.get("/api/alerts", params={"demo": "true"})
    data = r.json()
    assert data["count"] >= 1
    risks = {a["risk"] for a in data["alerts"]}
    assert risks & {"HIGH", "VERY HIGH", "CRITICAL"}


def test_alert_recommendation_is_string_not_dict(client):
    r = client.get("/api/alerts", params={"demo": "true"})
    a = r.json()["alerts"][0]
    # The bug we fixed: recommendation must be a str, not built from dicts.
    assert isinstance(a["recommendation"], (str, type(None)))


def test_acknowledge_returns_acknowledged(client):
    alerts = client.get("/api/alerts", params={"demo": "true"}).json()["alerts"]
    aid = alerts[0]["alert_id"]
    r = client.post(f"/api/alerts/{aid}/acknowledge")
    assert r.status_code == 200
    assert r.json()["status"] == "acknowledged"


def test_acknowledge_unknown_404(client):
    r = client.post("/api/alerts/ALT-NOPE/acknowledge")
    assert r.status_code == 404


def test_acknowledge_idempotent(client):
    alerts = client.get("/api/alerts", params={"demo": "true"}).json()["alerts"]
    aid = alerts[0]["alert_id"]
    client.post(f"/api/alerts/{aid}/acknowledge")
    r2 = client.post(f"/api/alerts/{aid}/acknowledge")
    assert r2.status_code == 200
    assert r2.json()["status"] == "acknowledged"
