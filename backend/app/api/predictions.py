"""FloodGuard AI — predictions API routes."""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.models.database import get_db
from app.models.models import Prediction
from app.models.schemas import BulkPredictionRequest, PredictionRequest
from app.services.cache import cache
from app.services.zone_service import get_all_zones, get_zone
from app.services import prediction_service, weather_service, risk_engine
from app.services.recommendation_engine import (
    generate_recommendations, generate_alert_reason, RECOMMENDATION_DISCLAIMER,
)

router = APIRouter(prefix="/api", tags=["predictions"])


async def _resolve_weather(zone: dict, demo: bool) -> dict:
    return await weather_service.async_normalize_weather_data(
        zone["latitude"], zone["longitude"], demo=demo
    )


@router.post("/predict")
async def predict(req: PredictionRequest, demo: bool = False, db: Session = Depends(get_db)):
    zone = get_zone(req.zone_id, db)
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found.")
    cache_key = f"prediction:{req.zone_id}:{demo}:{datetime.now(timezone.utc).strftime('%Y%m%d%H%M')}:{req.scenario or {}}"
    cached = await cache.get(cache_key)
    if cached:
        return cached
    svc = prediction_service.get_prediction_service()
    weather = await _resolve_weather(zone, demo)
    payload = {**zone, "_zone": zone}
    result = svc.predict(weather, payload, scenario=req.scenario)
    # Attach recommendations (decision-support).
    result["recommendations"] = generate_recommendations(result)
    result["recommendation_disclaimer"] = RECOMMENDATION_DISCLAIMER
    result["alert_reason"] = generate_alert_reason(result)
    db.add(Prediction(zone_id=zone["zone_id"], probability=result["probability"], risk=result["risk"], is_demo=result.get("is_demo", demo)))
    db.commit()
    await cache.set(cache_key, result, 60)
    return result


@router.post("/predictions/bulk")
async def bulk_predict(req: BulkPredictionRequest, demo: bool = False, db: Session = Depends(get_db)):
    """Return predictions for multiple zones with shared weather requests."""
    zones = {z["zone_id"]: z for z in get_all_zones(db)}
    missing = [zone_id for zone_id in req.zone_ids if zone_id not in zones]
    if missing:
        raise HTTPException(status_code=404, detail=f"Zone not found: {missing[0]}")

    svc = prediction_service.get_prediction_service()

    async def predict_one(zone_id: str):
        zone = zones[zone_id]
        weather = await _resolve_weather(zone, demo)
        result = svc.predict(weather, {**zone, "_zone": zone}, scenario=req.scenario)
        result["recommendations"] = generate_recommendations(result)
        result["recommendation_disclaimer"] = RECOMMENDATION_DISCLAIMER
        result["alert_reason"] = generate_alert_reason(result)
        db.add(Prediction(zone_id=zone["zone_id"], probability=result["probability"], risk=result["risk"], is_demo=result.get("is_demo", demo)))
        return result

    predictions = await asyncio.gather(*(predict_one(z) for z in req.zone_ids))
    db.commit()
    return {"is_demo": demo, "predictions": predictions}


@router.get("/predictions/overview")
async def predictions_overview(demo: bool = False, db: Session = Depends(get_db)):
    """Predict for every zone (used by the map / dashboard)."""
    zones = get_all_zones(db)
    svc = prediction_service.get_prediction_service()
    async def predict_zone(z):
        try:
            weather = await _resolve_weather(z, demo)
            res = svc.predict(weather, {**z, "_zone": z})
        except Exception:
            weather = {"is_demo": demo}
            res = {"probability": 0, "risk": "LOW", "population_exposure_estimate": 0}
        return {
            "zone_id": z["zone_id"],
            "zone_name": z["name"],
            "latitude": z["latitude"],
            "longitude": z["longitude"],
            "probability": res["probability"],
            "risk": res["risk"],
            "population_exposure_estimate": res["population_exposure_estimate"],
            "is_demo": weather.get("is_demo", demo),
        }

    out = await asyncio.gather(*(predict_zone(z) for z in zones))
    distribution: dict[str, int] = {r: 0 for r in risk_engine.RISK_ORDER}
    for z in out:
        distribution[z["risk"]] = distribution.get(z["risk"], 0) + 1
    return {
        "is_demo": any(z.get("is_demo") for z in out) if out else demo,
        "zones": out,
        "distribution": distribution,
    }
