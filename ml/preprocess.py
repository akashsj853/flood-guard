"""
FloodGuard AI — preprocessing for the offline training pipeline.

Validates and cleans the generated/real dataset before model training.
Mirrors validation semantics used at inference in
backend/app/utils/feature_engineering.py (validate_features).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from feature_engineering import MODEL_FEATURES

# Physically-sane bounds per feature (used for clamping, not dropping).
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


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """Clamp numeric features to sane bounds and fill missing with median."""
    df = df.copy()
    for col in MODEL_FEATURES:
        if col not in df.columns:
            raise ValueError(f"Missing required feature column: {col}")
        df[col] = pd.to_numeric(df[col], errors="coerce")
        lo, hi = BOUNDS.get(col, (-1e9, 1e9))
        df[col] = df[col].clip(lower=lo, upper=hi)
        if df[col].isna().any():
            df[col] = df[col].fillna(df[col].median())
    return df


def split(df: pd.DataFrame, target: str = "flood", test_size: float = 0.2, seed: int = 42):
    from sklearn.model_selection import train_test_split
    X = df[MODEL_FEATURES]
    y = df[target].astype(int)
    return train_test_split(X, y, test_size=test_size, random_state=seed, stratify=y)
