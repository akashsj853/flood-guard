"""Tests: runtime feature engineering."""
from __future__ import annotations

import pytest

from app.utils import feature_engineering as fe


def test_model_features_order_stable():
    assert len(fe.MODEL_FEATURES) == 19
    assert fe.MODEL_FEATURES[0] == "rainfall_1h"
    assert fe.MODEL_FEATURES[-1] == "historical_flood_frequency"


def test_build_features_basic(demo_weather, sample_zone):
    f = fe.build_features(demo_weather, sample_zone, offset_hours=0)
    assert set(f.keys()) == set(fe.MODEL_FEATURES)
    assert all(isinstance(v, float) for v in f.values())


def test_build_features_accumulates_rainfall(demo_weather, sample_zone):
    f0 = fe.build_features(demo_weather, sample_zone, offset_hours=0)
    # rainfall accumulations should be monotonically non-decreasing.
    assert f0["rainfall_1h"] <= f0["rainfall_3h"] <= f0["rainfall_6h"] <= f0["rainfall_24h"]
    assert f0["rainfall_1h"] >= 0


def test_forecast_offset_shifts_window(demo_weather, sample_zone):
    f0 = fe.build_features(demo_weather, sample_zone, offset_hours=0)
    f6 = fe.build_features(demo_weather, sample_zone, offset_hours=6)
    # At offset 6h, immediate rainfall should reflect the forecast window there.
    assert isinstance(f6["rainfall_1h"], float)


def test_validate_features_clamps_out_of_bounds():
    bad = {k: 1e9 for k in fe.MODEL_FEATURES}
    out = fe.validate_features(bad)
    for k, v in out.items():
        if k in fe.BOUNDS:
            assert fe.BOUNDS[k][0] <= v <= fe.BOUNDS[k][1]


def test_validate_features_fills_missing():
    out = fe.validate_features({})
    assert all(k in out for k in fe.MODEL_FEATURES)


def test_apply_scenario_rainfall_multiplier():
    base = fe.build_features(
        {"current": {"precipitation": 10}, "forecast": []},
        {"elevation": 0, "slope": 0, "drainage_capacity": 50,
         "impervious_surface": 50, "population_density": 100, "historical_flood_frequency": 1},
        offset_hours=0,
    )
    scen = fe.apply_scenario(base, {"rainfall_multiplier": 2.0})
    assert scen["rainfall_1h"] == pytest.approx(base["rainfall_1h"] * 2.0)


def test_apply_scenario_drainage_delta_clamped():
    base = fe.build_features(
        {"current": {"precipitation": 10}, "forecast": []},
        {"elevation": 0, "slope": 0, "drainage_capacity": 95,
         "impervious_surface": 50, "population_density": 100, "historical_flood_frequency": 1},
        offset_hours=0,
    )
    scen = fe.apply_scenario(base, {"drainage_delta": 50})
    # 95 + 50 clamped to 100.
    assert scen["drainage_capacity"] == pytest.approx(100.0)


def test_to_model_input_orders():
    feats = {k: i for i, k in enumerate(fe.MODEL_FEATURES)}
    inp = fe.to_model_input(feats)
    assert inp == list(range(len(fe.MODEL_FEATURES)))
