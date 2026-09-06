"""FloodGuard AI — alerts API routes."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from app.models.database import get_db
from app.models.models import Alert, User
from app.models.schemas import (
    AlertResponse, AcknowledgeResponse,
)
from app.services.zone_service import get_all_zones, get_zone
from app.services import prediction_service, weather_service, risk_engine
from app.services.recommendation_engine import (
    generate_alert_reason, generate_recommendations,
)
from app.api.auth import require_roles

router = APIRouter(prefix="/api/alerts", tags=["alerts"])

# Risk levels that warrant an alert.
_ALERT_RISKS = {"HIGH", "VERY HIGH", "CRITICAL"}


def _response(alert: Alert, zone_name: Optional[str]) -> AlertResponse:
    return AlertResponse(
        alert_id=alert.alert_id,
        zone_id=alert.zone_id,
        zone_name=zone_name,
        created_at=alert.created_at.isoformat() if alert.created_at else "",
        probability=alert.probability,
        risk=alert.risk,
        forecast_rainfall_3h=alert.forecast_rainfall_3h,
        reason=alert.reason,
        recommendation=alert.recommendation,
        status=alert.status,
        risk_level=alert.risk,
        acknowledged=alert.status == "acknowledged",
    )


@router.get("")
async def list_alerts(db: Session = Depends(get_db), demo: bool = False):
    """List active/acknowledged alerts, plus auto-generate for current high-risk zones."""
    svc = prediction_service.get_prediction_service()
    generated = []
    for z in get_all_zones(db):
        try:
            weather = await weather_service.async_normalize_weather_data(
                z["latitude"], z["longitude"], demo=demo
            )
            res = svc.predict(weather, {**z, "_zone": z})
        except Exception:
            continue
        if res["risk"] not in _ALERT_RISKS:
            continue
        # De-duplicate: one active alert per zone per risk.
        existing = (
            db.query(Alert)
            .filter(Alert.zone_id == z["zone_id"], Alert.status == "active")
            .first()
        )
        if existing:
            generated.append(existing)
            continue
        fr = res.get("forecast", {})
        reason = generate_alert_reason(res)
        recs = generate_recommendations(res)
        alert = Alert(
            alert_id=f"ALT-{uuid.uuid4().hex[:12].upper()}",
            zone_id=z["zone_id"],
            probability=res["probability"],
            risk=res["risk"],
            forecast_rainfall_3h=fr.get("+3 HOURS", {}).get("rainfall_3h"),
            reason=reason,
            recommendation=" ".join(recs)[:500] if recs else None,
            status="active",
        )
        db.add(alert)
        db.commit()
        db.refresh(alert)
        generated.append(alert)

    zone_names = {z["zone_id"]: z["name"] for z in get_all_zones(db)}
    # Also include any previously-acknowledged alerts for full history.
    historical = (
        db.query(Alert)
        .filter(Alert.status == "acknowledged")
        .order_by(Alert.acknowledged_at.desc())
        .limit(20)
        .all()
    )
    seen_ids = {a.alert_id for a in generated}
    combined = generated + [a for a in historical if a.alert_id not in seen_ids]
    return {
        "count": len(combined),
        "alerts": [_response(a, zone_names.get(a.zone_id)) for a in combined],
    }


@router.post("/{alert_id}/acknowledge")
def acknowledge_alert(
    alert_id: str,
    user_id: Optional[int] = None,
    db: Session = Depends(get_db),
    _user=Depends(require_roles("admin", "operator")),
):
    alert = db.query(Alert).filter(Alert.alert_id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found.")
    alert.acknowledged_by = _user.id
    alert.status = "acknowledged"
    from datetime import datetime, timezone
    alert.acknowledged_at = datetime.now(timezone.utc)
    db.commit()
    return AcknowledgeResponse(alert_id=alert.alert_id, status=alert.status)
