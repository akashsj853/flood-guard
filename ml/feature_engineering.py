"""
FloodGuard AI — ML feature engineering (training data generation).

This module is used by the offline training pipeline (ml/train.py,
ml/preprocess.py). It builds a physically-motivated SYNTHETIC dataset so the
project runs end-to-end without a licensed flood dataset, while preserving the
exact feature contract the production backend depends on.

The canonical feature order is shared with backend/app/utils/feature_engineering.py.
Keep MODEL_FEATURES identical in both places.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Canonical feature order. MUST match backend/app/utils/feature_engineering.py
# ---------------------------------------------------------------------------
MODEL_FEATURES = [
    "rainfall_1h", "rainfall_3h", "rainfall_6h", "rainfall_12h", "rainfall_24h",
    "forecast_rainfall_1h", "forecast_rainfall_3h", "forecast_rainfall_6h", "forecast_rainfall_12h",
    "temperature", "humidity", "pressure", "wind_speed",
    "elevation", "slope", "drainage_capacity", "impervious_surface",
    "population_density", "historical_flood_frequency",
]

# Static (zone) features vs. dynamic (weather/forecast) features.
STATIC_FEATURES = [
    "elevation", "slope", "drainage_capacity", "impervious_surface",
    "population_density", "historical_flood_frequency",
]
DYNAMIC_FEATURES = [f for f in MODEL_FEATURES if f not in STATIC_FEATURES]


def _lognormal_clip(mean, sigma, lo, hi, rng):
    """Draw a right-skewed value clipped to [lo, hi]."""
    val = rng.lognormal(mean, sigma)
    return float(np.clip(val, lo, hi))


def generate_synthetic_dataset(n_samples: int = 24000, seed: int = 42) -> pd.DataFrame:
    """
    Generate a synthetic but physically-plausible flood dataset.

    The flood propensity is a logistic function of:
      * recent + forecast rainfall (dominant),
      * impervious surface (more runoff),
      * poor drainage capacity (less conveyance),
      * low elevation / slope (slower drainage),
      * historical flood frequency (prior vulnerability),
      * population density (exposure proxy, mild).

    The binary `flood` target is sampled from the propensity.
    """
    rng = np.random.default_rng(seed)
    rows = []
    for _ in range(n_samples):
        # --- Dynamic weather features -------------------------------------
        # Base hourly rainfall, heavy-tailed.
        r1 = _lognormal_clip(1.2, 1.4, 0.0, 70.0, rng)
        # Accumulations (monotonic-ish, with noise)
        r3 = r1 + _lognormal_clip(1.6, 1.3, 0.0, 120.0, rng)
        r6 = r3 + _lognormal_clip(2.0, 1.3, 0.0, 200.0, rng)
        r12 = r6 + _lognormal_clip(2.4, 1.2, 0.0, 350.0, rng)
        r24 = r12 + _lognormal_clip(2.8, 1.2, 0.0, 600.0, rng)

        # Forecast (next hours) — correlated with current but independent noise
        f1 = max(0.0, r1 * rng.uniform(0.5, 1.4) + rng.normal(0, 3))
        f3 = max(0.0, r3 * rng.uniform(0.6, 1.3) + rng.normal(0, 8))
        f6 = max(0.0, r6 * rng.uniform(0.7, 1.2) + rng.normal(0, 15))
        f12 = max(0.0, r12 * rng.uniform(0.8, 1.15) + rng.normal(0, 25))

        temperature = float(rng.normal(27, 5))
        humidity = float(np.clip(rng.normal(78, 12), 30, 100))
        pressure = float(np.clip(rng.normal(1004, 8), 970, 1030))
        wind_speed = float(np.clip(rng.normal(14, 8), 0, 60))

        # --- Static zone features ----------------------------------------
        elevation = float(np.clip(rng.normal(20, 12), 1, 80))
        slope = float(np.clip(rng.normal(3.0, 1.8), 0.2, 12))
        drainage_capacity = float(np.clip(rng.normal(55, 16), 10, 95))
        impervious_surface = float(np.clip(rng.normal(60, 18), 10, 98))
        population_density = float(np.clip(rng.normal(6000, 3000), 200, 20000))
        historical_flood_frequency = float(np.clip(rng.normal(4, 3), 0, 15))

        # --- Physically-motivated model ----------------------------------
        # Normalise drivers to 0..1-ish contributions.
        rain_term = (
            0.020 * r1 + 0.012 * r3 + 0.010 * r6
            + 0.008 * (f1 + f3 + f6) + 0.006 * f12
        )
        imperv_term = 0.018 * (impervious_surface - 50)
        drain_term = -0.022 * (drainage_capacity - 55)
        elev_term = -0.020 * (elevation - 20)
        slope_term = -0.015 * (slope - 3)
        hist_term = 0.060 * historical_flood_frequency
        pop_term = 0.000004 * (population_density - 6000)

        logit = (
            -3.2 + rain_term + imperv_term + drain_term
            + elev_term + slope_term + hist_term + pop_term
            + rng.normal(0, 0.25)  # aleatoric noise
        )
        propensity = 1.0 / (1.0 + np.exp(-logit))
        flood = int(rng.random() < propensity)

        rows.append({
            "rainfall_1h": round(r1, 2),
            "rainfall_3h": round(r3, 2),
            "rainfall_6h": round(r6, 2),
            "rainfall_12h": round(r12, 2),
            "rainfall_24h": round(r24, 2),
            "forecast_rainfall_1h": round(f1, 2),
            "forecast_rainfall_3h": round(f3, 2),
            "forecast_rainfall_6h": round(f6, 2),
            "forecast_rainfall_12h": round(f12, 2),
            "temperature": round(temperature, 2),
            "humidity": round(humidity, 2),
            "pressure": round(pressure, 2),
            "wind_speed": round(wind_speed, 2),
            "elevation": round(elevation, 2),
            "slope": round(slope, 2),
            "drainage_capacity": round(drainage_capacity, 2),
            "impervious_surface": round(impervious_surface, 2),
            "population_density": round(population_density, 2),
            "historical_flood_frequency": round(historical_flood_frequency, 2),
            "flood": flood,
        })

    return pd.DataFrame(rows, columns=MODEL_FEATURES + ["flood"])


def add_rainfall_aggregates(df: pd.DataFrame) -> pd.DataFrame:
    """No-op compatibility helper; accumulations are generated directly."""
    return df


if __name__ == "__main__":
    df = generate_synthetic_dataset(n_samples=5000, seed=7)
    out = "data/flood_data.csv"
    df.to_csv(out, index=False)
    print(f"Wrote {len(df)} rows -> {out}")
    print(df["flood"].value_counts(normalize=True).round(3).to_dict())
