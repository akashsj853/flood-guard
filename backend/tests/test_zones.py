"""Tests: zones repository + API."""
from __future__ import annotations

import pytest

from app.services.zone_service import get_all_zones, get_zone


def test_get_all_zones_returns_data():
    zones = get_all_zones(None)
    assert len(zones) > 0
    z = zones[0]
    for k in ("zone_id", "name", "latitude", "longitude"):
        assert k in z


def test_get_zone_finds_by_id():
    zones = get_all_zones(None)
    target = zones[0]["zone_id"]
    z = get_zone(target, None)
    assert z is not None
    assert z["zone_id"] == target


def test_get_zone_missing_returns_none():
    assert get_zone("DOES_NOT_EXIST", None) is None


def test_zone_api_list(client):
    r = client.get("/api/zones")
    assert r.status_code == 200
    data = r.json()
    assert "zones" in data
    assert len(data["zones"]) > 0


def test_zone_api_detail(client):
    zones = client.get("/api/zones").json()["zones"]
    zid = zones[0]["zone_id"]
    r = client.get(f"/api/zones/{zid}")
    assert r.status_code == 200
    assert r.json()["zone_id"] == zid


def test_zone_api_detail_missing(client):
    r = client.get("/api/zones/NOPE")
    assert r.status_code == 404
