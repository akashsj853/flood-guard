"""
FloodGuard AI — runtime feature engineering.

Builds the exact feature vector the trained model expects from:
  * normalized weather (current + hourly forecast)
  * static zone characteristics
  * optional scenario overrides (What-If simulator)

The MODEL_FEATURES order MUST match ml/feature_engineering.py.
"""
from __future__ import annotations

# Canonical feature order — identical to ml/feature_engineering.MODEL_FEATURES.
MODEL_FEATURES = [
    "rainfall_1h", "rainfall_3h", "rainfall_6h", "rainfall_12h", "rainfall_24h",
    "forecast_rainfall_1h", "forecast_rainfall_3h", "forecast_rainfall_6h", "forecast_rainfall_12h",
    "temperature", "humidity", "pressure", "wind_speed",
    "elevation", "slope", "drainage_capacity", "impervious_surface",
    "population_density", "historical_flood_frequency",
]

STATIC_FEATURES = {
    "elevation", "slope", "drainage_capacity", "impervious_surface",
    "population_density", "historical_flood_frequency",
}

# Human-readable labels + emoji for explainable-AI output.
FEATURE_LABELS = {
    "rainfall_1h": ("Recent rainfall (1h)", "🌧️"),
    "rainfall_3h": ("Recent rainfall (3h)", "🌧️"),
    "rainfall_6h": ("Recent rainfall (6h)", "🌧️"),
    "rainfall_12h": ("Recent rainfall (12h)", "🌧️"),
    "rainfall_24h": ("Recent rainfall (24h)", "🌧️"),
    "forecast_rainfall_1h": ("Forecast rainfall (1h)", "🔮"),
    "forecast_rainfall_3h": ("Forecast rainfall (3h)", "🔮"),
    "forecast_rainfall_6h": ("Forecast rainfall (6h)", "🔮"),
    "forecast_rainfall_12h": ("Forecast rainfall (12h)", "🔮"),
    "temperature": ("Temperature", "🌡️"),
    "humidity": ("Humidity", "💧"),
    "pressure": ("Pressure", "📊"),
    "wind_speed": ("Wind speed", "🌬️"),
    "elevation": ("Elevation", "⛰️"),
    "slope": ("Slope", "📐"),
    "drainage_capacity": ("Drainage capacity", "🚧"),
    "impervious_surface": ("Impervious surface", "🏙️"),
    "population_density": ("Population density", "👥"),
    "historical_flood_frequency": ("Historical flood frequency", "📅"),
}

# Sane bounds used for validation/clamping at inference.
BOUNDS = {
    "rainfall_1h": (0, 400), "rainfall_3h": (0, 800), "rainfall_6h": (0, 1500),
    "rainfall_12h": (0, 3000), "rainfall_24h": (0, 6000),
    "forecast_rainfall_1h": (0, 400), "forecast_rainfall_3h": (0, 800),
    "forecast_rainfall_6h": (0, 1500), "forecast_rainfall_12h": (0, 3000),
    "temperature": (-20, 55), "humidity": (0, 100), "pressure": (870, 1085),
    "wind_speed": (0, 120), "elevation": (0, 9000), "slope": (0, 90),
    "drainage_capacity": (0, 100), "impervious_surface": (0, 100),
    "population_density": (0, 1_000_000), "historical_flood_frequency": (0, 1000),
}


def _precip_series(weather: dict) -> list[float]:
    """Return the precipitation time-series: [current, f0, f1, ...] in mm."""
    current = weather.get("current", {}) or {}
    precip = [float(current.get("precipitation", 0) or 0)]
    for f in weather.get("forecast", []) or []:
        precip.append(float(f.get("precipitation", 0) or 0))
    return precip


def build_features(weather: dict, zone: dict, offset_hours: int = 0) -> dict:
    """
    Build the model feature vector.

    offset_hours shifts the baseline: for the forecast-risk timeline we treat the
    forecast hour at `offset_hours` as the new "current" and recompute
    accumulations from that point forward. This uses only real forecast data.
    """
    precip = _precip_series(weather)
    n = len(precip)
    start = min(max(offset_hours, 0), max(n - 1, 0))

    def acc(k):
        return float(sum(precip[start:start + k]))

    fc = weather.get("forecast", []) or []
    # Forecast accumulations always look forward from `start`.
    def facc(k):
        window = fc[start:start + k]
        return float(sum(float(f.get("precipitation", 0) or 0) for f in window))

    current = weather.get("current", {}) or {}
    # Use forecast sample at `start` for atmospheric vars when available.
    atm = fc[start] if start < len(fc) else current

    features = {
        "rainfall_1h": acc(1),
        "rainfall_3h": acc(3),
        "rainfall_6h": acc(6),
        "rainfall_12h": acc(12),
        "rainfall_24h": acc(24),
        "forecast_rainfall_1h": facc(1),
        "forecast_rainfall_3h": facc(3),
        "forecast_rainfall_6h": facc(6),
        "forecast_rainfall_12h": facc(12),
        "temperature": float(atm.get("temperature", current.get("temperature", 25))),
        "humidity": float(atm.get("humidity", current.get("humidity", 70))),
        "pressure": float(atm.get("pressure", current.get("pressure", 1005))),
        "wind_speed": float(atm.get("wind_speed", current.get("wind_speed", 10))),
        "elevation": float(zone.get("elevation", 0)),
        "slope": float(zone.get("slope", 0)),
        "drainage_capacity": float(zone.get("drainage_capacity", 0)),
        "impervious_surface": float(zone.get("impervious_surface", 0)),
        "population_density": float(zone.get("population_density", 0)),
        "historical_flood_frequency": float(zone.get("historical_flood_frequency", 0)),
    }
    return validate_features(features)


def validate_features(features: dict) -> dict:
    """Clamp every feature to sane bounds; fill any missing with 0."""
    out = {}
    for f in MODEL_FEATURES:
        val = features.get(f, 0)
        try:
            val = float(val)
        except (TypeError, ValueError):
            val = 0.0
        if f in BOUNDS:
            val = min(max(val, BOUNDS[f][0]), BOUNDS[f][1])
        out[f] = val
    return out


def apply_scenario(features: dict, adjustments: dict | None) -> dict:
    """
    Apply What-If scenario adjustments to a validated feature vector.

    Supported adjustments (all optional):
      rainfall_multiplier : multiply all rainfall_* features (e.g. 1.2 = +20%)
      forecast_multiplier : multiply forecast_rainfall_* features
      drainage_delta      : additive change to drainage_capacity (clamped 0..100)
      impervious_delta    : additive change to impervious_surface (clamped 0..100)
      elevation_delta     : additive change to elevation
    Returns a new validated feature vector.
    """
    if not adjustments:
        return features
    feats = dict(features)
    rm = float(adjustments.get("rainfall_multiplier", 1.0) or 1.0)
    fm = float(adjustments.get("forecast_multiplier", 1.0) or 1.0)
    for k in feats:
        if k.startswith("rainfall_") and k not in ("forecast_rainfall_1h",):
            feats[k] = feats[k] * rm
        if k.startswith("forecast_rainfall_"):
            feats[k] = feats[k] * fm
    if "drainage_delta" in adjustments and adjustments["drainage_delta"] is not None:
        feats["drainage_capacity"] = min(100.0, max(0.0,
            feats["drainage_capacity"] + float(adjustments["drainage_delta"])))
    if "impervious_delta" in adjustments and adjustments["impervious_delta"] is not None:
        feats["impervious_surface"] = min(100.0, max(0.0,
            feats["impervious_surface"] + float(adjustments["impervious_delta"])))
    if "elevation_delta" in adjustments and adjustments["elevation_delta"] is not None:
        feats["elevation"] = max(0.0, feats["elevation"] + float(adjustments["elevation_delta"]))
    return validate_features(feats)


def to_model_input(features: dict) -> list[float]:
    """Return features in the exact model order as a flat list."""
    return [float(features[f]) for f in MODEL_FEATURES]
