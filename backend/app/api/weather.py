"""FloodGuard AI — weather API routes."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.services import weather_service

router = APIRouter(prefix="/api/weather", tags=["weather"])


@router.get("/current")
async def current_weather(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude"),
    demo: bool = Query(False, description="Force demo data"),
):
    if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
        raise HTTPException(status_code=400, detail="Invalid coordinates.")
    data = await weather_service.async_get_current_weather(lat, lon, demo=demo)
    return data


@router.get("/forecast")
async def hourly_forecast(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude"),
    demo: bool = Query(False, description="Force demo data"),
):
    if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
        raise HTTPException(status_code=400, detail="Invalid coordinates.")
    data = await weather_service.async_get_hourly_forecast(lat, lon, demo=demo)
    return data


@router.get("/rainfall")
async def rainfall_accumulation(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude"),
    demo: bool = Query(False, description="Force demo data"),
):
    if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
        raise HTTPException(status_code=400, detail="Invalid coordinates.")
    return await weather_service.async_get_rainfall_accumulation(lat, lon, demo=demo)
