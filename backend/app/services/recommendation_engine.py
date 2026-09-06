"""
FloodGuard AI — decision-support recommendation engine.

Generates clearly-labelled DECISION-SUPPORT recommendations (not official
emergency instructions) from the prediction result.

Rules are driven by flood probability, forecast rainfall, drainage capacity,
elevation, population exposure, and historical flood frequency.
"""
from __future__ import annotations

from app.services import risk_engine


def generate_recommendations(prediction: dict) -> list[str]:
    recs: list[str] = []
    prob = float(prediction.get("probability", 0))
    risk = prediction.get("risk", "LOW")
    zone = prediction.get("_zone", {})
    forecast_3h = (prediction.get("forecast", {}).get("+3 HOURS", {}) or {}).get("probability", prob)

    # Critical / very high.
    if prob >= 80 or risk in ("CRITICAL", "VERY HIGH"):
        recs.append("Escalate to critical response: coordinate emergency response and issue appropriate public advisory.")
        recs.append("Mobilise emergency resources (pumps, shelters, medical) to the zone.")
    elif prob >= 60:  # HIGH
        recs.append("Prepare emergency resources and pre-position response teams.")
        recs.append("Issue a warning to relevant authorities and vulnerable communities.")

    # Drainage.
    drainage = float(zone.get("drainage_capacity", 50))
    if drainage < 40:
        recs.append("Inspect and clear drainage networks; capacity is below safe threshold.")
    elif drainage < 55:
        recs.append("Schedule drainage inspection; capacity is moderate.")

    # Population exposure.
    exposure = float(prediction.get("population_exposure_estimate", 0))
    if exposure >= 5000:
        recs.append(f"Prioritise this zone: estimated {int(exposure):,} people exposed.")
    elif exposure >= 1500:
        recs.append("Plan for possible evacuation of low-lying neighbourhoods.")

    # Forecast trend.
    if forecast_3h - prob >= 10:
        recs.append("Risk is forecast to increase within 3 hours — monitor closely.")

    # Historical vulnerability.
    if int(zone.get("historical_flood_frequency", 0)) >= 7:
        recs.append("Zone has a high historical flood frequency — apply conservative thresholds.")

    if not recs:
        recs.append("Conditions within normal range; continue routine monitoring.")

    # Disclaimer is attached at the API layer.
    return recs


def generate_alert_reason(prediction: dict) -> str:
    factors = prediction.get("risk_factors", [])
    top = [f for f in factors if f.get("impact") == "HIGH"][:2]
    if not top:
        top = factors[:2]
    parts = [f"{f['label']} (high impact)" for f in top]
    return "Elevated risk driven by: " + "; ".join(parts) + "." if parts else "Conditions indicate elevated flood risk."


# ---------------------------------------------------------------------------
# Convenience for APIs: attach disclaimer.
RECOMMENDATION_DISCLAIMER = (
    "These are decision-support recommendations, not official emergency "
    "instructions. Follow directions from authorised disaster-management "
    "agencies."
)


def recommendations_with_disclaimer(prediction: dict) -> dict:
    return {
        "recommendations": generate_recommendations(prediction),
        "disclaimer": RECOMMENDATION_DISCLAIMER,
        "risk": prediction.get("risk"),
        "probability": prediction.get("probability"),
    }
