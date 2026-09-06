from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.auth import require_roles
from app.models.database import get_db
from app.models.models import AlertSubscription, SavedLocation, User
from app.models.schemas import SavedLocationRequest, SubscriptionRequest
from app.services.zone_service import get_zone

router = APIRouter(prefix="/api/profile", tags=["profile"])


@router.get("/locations")
def list_locations(db: Session = Depends(get_db), user: User = Depends(require_roles("citizen", "operator", "admin"))):
    return {"locations": [{"id": item.id, "zone_id": item.zone_id, "label": item.label} for item in user.saved_locations]}


@router.post("/locations", status_code=201)
def save_location(payload: SavedLocationRequest, db: Session = Depends(get_db), user: User = Depends(require_roles("citizen", "operator", "admin"))):
    if not get_zone(payload.zone_id, db):
        raise HTTPException(status_code=404, detail="Zone not found")
    existing = db.query(SavedLocation).filter(SavedLocation.user_id == user.id, SavedLocation.zone_id == payload.zone_id).first()
    if existing:
        existing.label = payload.label
        db.commit()
        return {"id": existing.id, "zone_id": existing.zone_id, "label": existing.label}
    item = SavedLocation(user_id=user.id, zone_id=payload.zone_id, label=payload.label)
    db.add(item)
    db.commit()
    db.refresh(item)
    return {"id": item.id, "zone_id": item.zone_id, "label": item.label}


@router.delete("/locations/{location_id}")
def delete_location(location_id: int, db: Session = Depends(get_db), user: User = Depends(require_roles("citizen", "operator", "admin"))):
    item = db.query(SavedLocation).filter(SavedLocation.id == location_id, SavedLocation.user_id == user.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Saved location not found")
    db.delete(item)
    db.commit()
    return {"deleted": location_id}


@router.get("/subscriptions")
def list_subscriptions(user: User = Depends(require_roles("citizen", "operator", "admin"))):
    return {"subscriptions": [{"id": item.id, "zone_id": item.zone_id, "risk_threshold": item.risk_threshold, "channels": item.channels.split(","), "enabled": item.enabled} for item in user.alert_subscriptions]}


@router.post("/subscriptions", status_code=201)
def subscribe(payload: SubscriptionRequest, db: Session = Depends(get_db), user: User = Depends(require_roles("citizen", "operator", "admin"))):
    valid_thresholds = {"LOW", "MODERATE", "HIGH", "VERY HIGH", "CRITICAL"}
    if payload.risk_threshold not in valid_thresholds or not get_zone(payload.zone_id, db):
        raise HTTPException(status_code=400, detail="Invalid zone or risk threshold")
    item = AlertSubscription(user_id=user.id, zone_id=payload.zone_id, risk_threshold=payload.risk_threshold, channels=",".join(payload.channels[:3]))
    db.add(item)
    db.commit()
    db.refresh(item)
    return {"id": item.id, "zone_id": item.zone_id, "risk_threshold": item.risk_threshold, "channels": payload.channels[:3], "enabled": item.enabled}