"""Tests: recommendation engine (decision-support, not instructions)."""
from __future__ import annotations

from app.services import recommendation_engine as rcm
from app.services import risk_engine


def _pred(prob, risk, zone=None, forecast_3h=None):
    return {
        "probability": prob,
        "risk": risk,
        "population_exposure_estimate": 0,
        "_zone": zone or {"drainage_capacity": 50, "historical_flood_frequency": 0},
        "forecast": {"+3 HOURS": {"probability": forecast_3h if forecast_3h is not None else prob}},
        "risk_factors": [],
    }


def test_recommendations_is_list_of_strings():
    recs = rcm.generate_recommendations(_pred(85, "CRITICAL"))
    assert isinstance(recs, list)
    assert all(isinstance(r, str) for r in recs)


def test_critical_recommends_escalation():
    recs = rcm.generate_recommendations(_pred(85, "CRITICAL"))
    assert any("critical response" in r.lower() for r in recs)


def test_low_risk_routine():
    # drainage >= 55 and exposure 0 -> no specific branch fires -> routine message.
    recs = rcm.generate_recommendations(_pred(5, "LOW", {"drainage_capacity": 60, "historical_flood_frequency": 0}))
    assert any("normal range" in r.lower() for r in recs)


def test_population_exposure_recommendation():
    recs = rcm.generate_recommendations(_pred(70, "VERY HIGH", {"drainage_capacity": 50, "historical_flood_frequency": 0}, 70))
    pred = _pred(70, "VERY HIGH", {"drainage_capacity": 50, "historical_flood_frequency": 0})
    pred["population_exposure_estimate"] = 9000
    recs = rcm.generate_recommendations(pred)
    assert any("people exposed" in r for r in recs)


def test_drainage_low_inspection():
    pred = _pred(50, "HIGH", {"drainage_capacity": 30, "historical_flood_frequency": 0})
    recs = rcm.generate_recommendations(pred)
    assert any("drainage" in r.lower() for r in recs)


def test_forecast_trend_warning():
    pred = _pred(50, "HIGH", {"drainage_capacity": 50, "historical_flood_frequency": 0})
    pred["forecast"] = {"+3 HOURS": {"probability": 75}}
    recs = rcm.generate_recommendations(pred)
    assert any("increase" in r.lower() for r in recs)


def test_alert_reason_uses_factors():
    pred = _pred(70, "VERY HIGH")
    pred["risk_factors"] = [
        {"label": "Recent rainfall (3h)", "impact": "HIGH"},
        {"label": "Drainage capacity", "impact": "HIGH"},
    ]
    reason = rcm.generate_alert_reason(pred)
    assert "Elevated risk driven by" in reason
    assert "Recent rainfall (3h)" in reason


def test_disclaimer_present():
    assert "decision-support" in rcm.RECOMMENDATION_DISCLAIMER.lower()
    out = rcm.recommendations_with_disclaimer(_pred(85, "CRITICAL"))
    assert out["disclaimer"] == rcm.RECOMMENDATION_DISCLAIMER
    assert isinstance(out["recommendations"], list)
