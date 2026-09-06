"""
FloodGuard AI — prediction service.

Loads the persisted ML model, builds features from weather + zone data, returns
flood probability, risk class, a forecast-risk timeline (NOW/+1h/+3h/+6h),
human-readable SHAP explanations (with a transparent fallback), and an
estimated population exposure.

If the model is not trained yet, a deterministic rule-based fallback predictor
is used so the API always works; this is flagged in `is_demo`-like metadata
via `model_fallback`.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import joblib
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.feature_engineering import (  # noqa: E402
    MODEL_FEATURES, FEATURE_LABELS, build_features, validate_features,
    apply_scenario, to_model_input,
)
from app.services import risk_engine  # noqa: E402
from app.services.weather_service import (  # noqa: E402
    normalize_weather_data, _demo_weather,
)

ML_DIR = Path(__file__).resolve().parents[1] / "ml"
MODEL_PATH = ML_DIR / "flood_model.pkl"
META_PATH = ML_DIR / "model_metadata.json"

# Default decision threshold. Loaded from model_metadata.json when available so
# the backend and training pipeline agree on the operating point. This point is
# tuned to prioritise recall (minimise missed floods) while keeping precision
# above a usable floor.
DEFAULT_THRESHOLD = 0.5

# Forecast timeline offsets (hours).
TIMELINE = [("NOW", 0), ("+1 HOUR", 1), ("+3 HOURS", 3), ("+6 HOURS", 6)]


class PredictionService:
    def __init__(self) -> None:
        self._model = None
        self._model_type = None
        self._fallback = False
        self._threshold = DEFAULT_THRESHOLD
        self._background_means = None
        self._explainer = None
        self._load()

    def _load(self) -> None:
        if MODEL_PATH.exists():
            try:
                self._model = joblib.load(MODEL_PATH)
                self._model_type = type(self._model).__name__
            except Exception:
                self._model = None
        if self._model is None:
            self._fallback = True
            self._model_type = "RuleBasedFallback"
        # Load the trained operating point so backend + training agree.
        if META_PATH.exists():
            try:
                with open(META_PATH) as f:
                    meta = json.load(f)
                thr = meta.get("threshold")
                if isinstance(thr, (int, float)):
                    self._threshold = float(thr)
            except (json.JSONDecodeError, OSError):
                pass
        # Background means for SHAP / proxy explanations.
        csv_path = Path(__file__).resolve().parents[3] / "ml" / "data" / "flood_data.csv"
        try:
            import pandas as pd
            df = pd.read_csv(csv_path)
            self._background_means = df[MODEL_FEATURES].mean().to_dict()
        except Exception:
            self._background_means = None

    # --- core probability --------------------------------------------------
    def _raw_proba(self, features: dict) -> float:
        """Return flood probability in [0, 100]."""
        if self._model is not None:
            x = np.array([to_model_input(features)], dtype=float)
            try:
                proba = float(self._model.predict_proba(x)[0, 1])
            except Exception:
                proba = float(self._model.predict(x)[0])
            return round(proba * 100, 2)
        # Rule-based fallback (kept transparent & conservative).
        return round(self._rule_based(features), 2)

    @staticmethod
    def _rule_based(features: dict) -> float:
        rain = (0.5 * features["rainfall_1h"] + 0.4 * features["rainfall_3h"]
                + 0.3 * features["rainfall_6h"] + 0.2 * features["forecast_rainfall_3h"])
        imperv = 0.2 * (features["impervious_surface"] - 50)
        drain = -0.3 * (features["drainage_capacity"] - 55)
        elev = -0.2 * (features["elevation"] - 20)
        hist = 2.0 * features["historical_flood_frequency"]
        score = -20 + rain + imperv + drain + elev + hist
        return 100 / (1 + np.exp(-score / 20))

    # --- forecast timeline -------------------------------------------------
    def forecast_timeline(self, weather: dict, zone: dict) -> dict:
        out = {}
        for label, offset in TIMELINE:
            feats = build_features(weather, zone, offset_hours=offset)
            proba = self._raw_proba(feats)
            out[label] = {
                "probability": proba,
                "risk": risk_engine.classify(proba),
            }
        return out

    # --- explanations ------------------------------------------------------
    def _explain(self, features: dict) -> tuple[list[dict], list[str]]:
        contrib = self._feature_contributions(features)
        # Impact bucket by absolute contribution.
        def bucket(v):
            return "HIGH" if v >= 0.6 else ("MEDIUM" if v >= 0.3 else "LOW")
        factors = []
        for feat, score, direction in contrib:
            label, emoji = FEATURE_LABELS.get(feat, (feat, "•"))
            factors.append({
                "feature": feat,
                "label": label,
                "emoji": emoji,
                "impact": bucket(abs(score)),
                "contribution": round(score * direction, 3),
            })
        # Human-readable explanation (top 3 positive drivers).
        positives = [c for c in contrib if c[2] > 0]
        positives.sort(key=lambda c: -c[1])
        expl = []
        for feat, _, _ in positives[:3]:
            label, _ = FEATURE_LABELS.get(feat, (feat, "•"))
            expl.append(f"{label} is contributing to elevated flood risk.")
        if not expl:
            expl.append("No single dominant driver; combined conditions are moderate.")
        return factors, expl

    def _feature_contributions(self, features: dict):
        """
        Return list of (feature, magnitude 0..1, direction +1/-1).

        Uses SHAP TreeExplainer when possible; otherwise a transparent
        baseline-difference proxy (how much probability drops when the feature
        is replaced by its background mean).
        """
        baseline = dict(features)
        if self._background_means:
            for k, v in self._background_means.items():
                baseline[k] = float(v)
        try:
            import shap
            x = np.array([to_model_input(features)], dtype=float)
            if self._explainer is None:
                self._explainer = shap.TreeExplainer(self._model)
            sv = self._explainer.shap_values(x)
            if isinstance(sv, list):
                vals = np.abs(np.array(sv[1])).flatten()
            else:
                vals = np.abs(np.array(sv)).flatten()
            total = vals.sum() + 1e-9
            contrib = []
            for i, f in enumerate(MODEL_FEATURES):
                mag = float(vals[i]) / total
                direction = 1 if (isinstance(sv, list) and sv[1][0][i] > 0) or (not isinstance(sv, list) and sv[0][i] > 0) else -1
                contrib.append((f, min(1.0, mag * 5), direction))
            contrib.sort(key=lambda c: -abs(c[1]))
            return contrib
        except Exception:
            pass
        # Proxy path: measure probability change vs. background mean.
        base_proba = self._raw_proba(baseline)
        cur_proba = self._raw_proba(features)
        contrib = []
        for f in MODEL_FEATURES:
            ablated = dict(features)
            ablated[f] = baseline[f]
            ablated = validate_features(ablated)
            p = self._raw_proba(ablated)
            delta = (cur_proba - p) / 100.0  # signed contribution to prob
            contrib.append((f, min(1.0, abs(delta) * 5), 1 if delta >= 0 else -1))
        contrib.sort(key=lambda c: -abs(c[1]))
        return contrib

    # --- public predict ----------------------------------------------------
    def predict(self, weather: dict, zone: dict, scenario: dict | None = None) -> dict:
        is_demo = bool(weather.get("is_demo", False))
        feats = build_features(weather, zone, offset_hours=0)
        if scenario:
            feats = apply_scenario(feats, scenario)
        proba = self._raw_proba(feats)
        risk = risk_engine.classify(proba)
        timeline = self.forecast_timeline(weather, zone)
        factors, expl = self._explain(feats)
        exposure = round(zone.get("population", 0) * proba / 100.0, 0)
        return {
            "zone_id": zone.get("zone_id"),
            "zone_name": zone.get("name", ""),
            "probability": proba,
            "risk": risk,
            "forecast": timeline,
            "risk_factors": factors,
            "explanation": expl,
            "population_exposure_estimate": exposure,
            "is_demo": is_demo,
            "model_type": self._model_type,
        }


# Module-level singleton (reloaded if needed).
_prediction_service: PredictionService | None = None


def get_prediction_service() -> PredictionService:
    global _prediction_service
    if _prediction_service is None:
        _prediction_service = PredictionService()
    return _prediction_service
