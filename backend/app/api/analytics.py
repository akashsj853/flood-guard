"""FloodGuard AI — analytics API routes."""
from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.models.database import get_db
from app.models.schemas import AnalyticsResponse
from app.services.zone_service import get_all_zones
from app.services import prediction_service, weather_service, risk_engine
from app.api.auth import require_roles

router = APIRouter(prefix="/api/analytics", tags=["analytics"])

_METADATA_PATH = (
    Path(__file__).resolve().parents[2] / "app" / "ml" / "model_metadata.json"
)


def _load_model_metadata() -> dict:
    if _METADATA_PATH.exists():
        try:
            with open(_METADATA_PATH) as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


@router.get("")
async def analytics(
    demo: bool = False,
    db: Session = Depends(get_db),
    _user=Depends(require_roles("admin", "operator")),
):
    """Aggregate analytics across all zones + model performance."""
    svc = prediction_service.get_prediction_service()
    zones = get_all_zones(db)

    distribution: dict[str, int] = {r: 0 for r in risk_engine.RISK_ORDER}
    rainfall_24h = {}
    forecast_12h: dict[str, float] = {}
    risk_trend: dict[str, float] = {}

    for z in zones:
        try:
            weather = await weather_service.async_normalize_weather_data(
                z["latitude"], z["longitude"], demo=demo
            )
            res = svc.predict(weather, {**z, "_zone": z})
        except Exception:
            res = {"probability": 0.0, "risk": "LOW"}
        distribution[res["risk"]] = distribution.get(res["risk"], 0) + 1
        risk_trend[z["zone_id"]] = res["probability"]

        current = weather.get("current", {})
        obs_rain = current.get("rainfall_24h", current.get("precipitation", 0.0))
        rainfall_24h[z["zone_id"]] = round(float(obs_rain), 2)

        fr = res.get("forecast", {})
        f3 = fr.get("+3 HOURS", {}).get("rainfall_3h", 0.0)
        forecast_12h[z["zone_id"]] = round(float(f3), 2)

    meta = _load_model_metadata()
    return AnalyticsResponse(
        rainfall_last_24h=[{"zone_id": k, "rainfall_24h": v} for k, v in rainfall_24h.items()],
        forecast_next_12h=[{"zone_id": k, "forecast_rainfall_3h": v} for k, v in forecast_12h.items()],
        zone_distribution=distribution,
        risk_trend=risk_trend,
        model_performance=meta.get("metrics", {}) if meta else {},
    )
