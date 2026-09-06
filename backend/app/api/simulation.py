"""FloodGuard AI — What-If simulation API routes."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.models.database import get_db
from app.models.schemas import SimulationRequest, SimulationResponse
from app.services.zone_service import get_zone
from app.services import prediction_service, weather_service, risk_engine
from app.api.auth import require_roles

router = APIRouter(prefix="/api/simulation", tags=["simulation"])


@router.post("")
async def simulate(
    req: SimulationRequest,
    demo: bool = False,
    db: Session = Depends(get_db),
    _user=Depends(require_roles("admin", "operator")),
):
    """Run a baseline vs. scenario prediction for a zone (decision-support only)."""
    zone = get_zone(req.zone_id, db)
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found.")

    svc = prediction_service.get_prediction_service()
    weather = await weather_service.async_normalize_weather_data(
        zone["latitude"], zone["longitude"], demo=demo
    )
    payload = {**zone, "_zone": zone}

    baseline = svc.predict(weather, payload)
    scenario = svc.predict(weather, payload, scenario=req.adjustments or {})

    return SimulationResponse(
        zone_id=zone["zone_id"],
        zone_name=zone["name"],
        baseline_probability=baseline["probability"],
        baseline_risk=baseline["risk"],
        scenario_probability=scenario["probability"],
        scenario_risk=scenario["risk"],
        delta=round(scenario["probability"] - baseline["probability"], 2),
        risk_factors=scenario.get("risk_factors", []),
        explanation=scenario.get("explanation", []),
    )
