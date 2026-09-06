"""FloodGuard AI — zones API routes."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.models.database import get_db
from app.models.models import Prediction
from app.services.zone_service import get_all_zones, get_zone
from app.services import prediction_service

router = APIRouter(prefix="/api/zones", tags=["zones"])


@router.get("")
def list_zones(db: Session = Depends(get_db)):
    zones = get_all_zones(db)
    return {"count": len(zones), "zones": zones}


@router.get("/{zone_id}")
def zone_detail(zone_id: str, db: Session = Depends(get_db)):
    zone = get_zone(zone_id, db)
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found.")
    return zone


@router.get("/{zone_id}/history")
def zone_history(zone_id: str, limit: int = 30, offset: int = 0, db: Session = Depends(get_db)):
    if not get_zone(zone_id, db):
        raise HTTPException(status_code=404, detail="Zone not found.")
    limit = min(max(limit, 1), 100)
    rows = (db.query(Prediction).filter(Prediction.zone_id == zone_id).order_by(Prediction.created_at.desc()).offset(offset).limit(limit).all())
    return {"zone_id": zone_id, "count": len(rows), "history": [{"timestamp": row.created_at.isoformat() if row.created_at else "", "probability": row.probability, "risk": row.risk, "is_demo": row.is_demo} for row in rows]}


@router.get("/{zone_id}/prediction")
async def zone_prediction(zone_id: str, demo: bool = False, db: Session = Depends(get_db)):
    zone = get_zone(zone_id, db)
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found.")
    svc = prediction_service.get_prediction_service()
    weather = await weather_service_normalized(zone, demo)
    result = svc.predict(weather, {**zone, "_zone": zone})
    result["zone_id"] = zone_id
    return result


async def weather_service_normalized(zone: dict, demo: bool) -> dict:
    from app.services import weather_service
    return await weather_service.async_normalize_weather_data(zone["latitude"], zone["longitude"], demo=demo)
