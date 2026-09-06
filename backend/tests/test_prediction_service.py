"""Tests: prediction service (fallback + trained model, forecast timeline)."""
from __future__ import annotations

import pytest

from app.services import prediction_service as ps
from app.services import weather_service


def test_service_singleton():
    assert ps.get_prediction_service() is ps.get_prediction_service()


def test_predict_returns_required_keys(demo_weather, sample_zone):
    svc = ps.get_prediction_service()
    res = svc.predict(demo_weather, {**sample_zone, "_zone": sample_zone})
    for k in ("zone_id", "probability", "risk", "forecast", "risk_factors",
              "explanation", "population_exposure_estimate", "is_demo", "model_type"):
        assert k in res
    assert 0 <= res["probability"] <= 100


def test_risk_matches_probability(demo_weather, sample_zone):
    from app.services import risk_engine
    svc = ps.get_prediction_service()
    res = svc.predict(demo_weather, {**sample_zone, "_zone": sample_zone})
    assert res["risk"] == risk_engine.classify(res["probability"])


def test_forecast_timeline_keys(demo_weather, sample_zone):
    svc = ps.get_prediction_service()
    res = svc.predict(demo_weather, {**sample_zone, "_zone": sample_zone})
    for label in ("NOW", "+1 HOUR", "+3 HOURS", "+6 HOURS"):
        assert label in res["forecast"]
        assert "probability" in res["forecast"][label]
        assert "risk" in res["forecast"][label]


def test_scenario_changes_probability(demo_weather, sample_zone):
    svc = ps.get_prediction_service()
    base = svc.predict(demo_weather, {**sample_zone, "_zone": sample_zone})
    wet = svc.predict(demo_weather, {**sample_zone, "_zone": sample_zone},
                      scenario={"rainfall_multiplier": 3.0})
    assert wet["probability"] >= base["probability"]


def test_population_exposure_scales_with_probability(demo_weather, sample_zone):
    svc = ps.get_prediction_service()
    res = svc.predict(demo_weather, {**sample_zone, "_zone": sample_zone})
    expected = round(sample_zone.get("population", 0) * res["probability"] / 100.0, 0)
    assert res["population_exposure_estimate"] == expected


def test_threshold_loaded_or_default():
    svc = ps.get_prediction_service()
    assert 0.0 < svc._threshold <= 1.0
