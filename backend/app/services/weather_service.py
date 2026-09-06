"""
FloodGuard AI — WeatherService abstraction.

Provider-agnostic weather access. Default provider is Open-Meteo (no API key
required), ideal for hackathons. If the provider is unreachable OR the caller
requests demo mode, the service returns clearly-labelled DEMO data — never
pretending demo data is real-time.

Public API (all lat/lon required):
  get_current_weather(lat, lon)  -> normalized dict
  get_hourly_forecast(lat, lon)  -> normalized list of hours
  get_rainfall_accumulation(...) -> {1h,3h,6h,12h,24h}
  normalize(...)                 -> unified {current, forecast}
"""
from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta, timezone

import asyncio
import httpx

from app.services.cache import cache

# Allow importing demo helpers from the same package.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PROVIDER = os.getenv("WEATHER_PROVIDER", "openmeteo").lower()
OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

# Cache responses briefly to avoid hammering the provider (key -> (expiry, value)).
_HTTP_CLIENT: httpx.AsyncClient | None = None


def _client() -> httpx.AsyncClient:
    global _HTTP_CLIENT
    if _HTTP_CLIENT is None:
        _HTTP_CLIENT = httpx.AsyncClient(timeout=httpx.Timeout(10.0, connect=3.0))
    return _HTTP_CLIENT


async def _fetch_open_meteo(lat: float, lon: float, hourly: bool) -> dict:
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,relative_humidity_2m,surface_pressure,wind_speed_10m,precipitation",
        "timezone": "auto",
    }
    if hourly:
        params["hourly"] = "precipitation,temperature_2m,relative_humidity_2m,surface_pressure,wind_speed_10m"
        params["forecast_days"] = 2
    last_error = None
    for attempt in range(3):
        try:
            resp = await _client().get(OPEN_METEO_URL, params=params)
            resp.raise_for_status()
            return resp.json()
        except (httpx.HTTPError, ValueError) as exc:
            last_error = exc
            if attempt < 2:
                await asyncio.sleep(0.25 * (2 ** attempt))
    raise last_error or RuntimeError("Open-Meteo request failed")


def _parse_open_meteo(raw: dict, hourly: bool) -> dict:
    now = datetime.now(timezone.utc)
    cur = raw.get("current", {})
    normalized = {
        "source": "openmeteo",
        "is_demo": False,
        "current": {
            "temperature": float(cur.get("temperature_2m", 0) or 0),
            "humidity": float(cur.get("relative_humidity_2m", 0) or 0),
            "pressure": float(cur.get("surface_pressure", 0) or 0),
            "wind_speed": float(cur.get("wind_speed_10m", 0) or 0),
            "precipitation": float(cur.get("precipitation", 0) or 0),
            "timestamp": cur.get("time"),
        },
        "forecast": [],
    }
    if hourly:
        h = raw.get("hourly", {})
        times = h.get("time", [])
        for i, t in enumerate(times):
            # Only keep future hours.
            try:
                ts = datetime.fromisoformat(t.replace("Z", "+00:00"))
            except Exception:
                ts = now
            if ts < now - timedelta(hours=1):
                continue
            normalized["forecast"].append({
                "time": t,
                "precipitation": float((h.get("precipitation") or [0] * len(times))[i] or 0),
                "temperature": float((h.get("temperature_2m") or [0] * len(times))[i] or 0),
                "humidity": float((h.get("relative_humidity_2m") or [0] * len(times))[i] or 0),
                "pressure": float((h.get("surface_pressure") or [0] * len(times))[i] or 0),
                "wind_speed": float((h.get("wind_speed_10m") or [0] * len(times))[i] or 0),
            })
    return normalized


async def async_get_current_weather(lat: float, lon: float, demo: bool = False) -> dict:
    cache_key = f"cur:{lat:.3f}:{lon:.3f}:{demo}"
    cached = await cache.get(f"weather:{cache_key}")
    if cached:
        return cached
    if demo:
        data = _demo_weather()[0]
        await cache.set(f"weather:{cache_key}", data, 600)
        return data
    try:
        raw = await _fetch_open_meteo(lat, lon, hourly=False)
        data = _parse_open_meteo(raw, hourly=False)
    except Exception:
        data = _demo_weather(is_weather_failure=True)[0]
    await cache.set(f"weather:{cache_key}", data, 600)
    return data


async def async_get_hourly_forecast(lat: float, lon: float, demo: bool = False) -> dict:
    cache_key = f"fc:{lat:.3f}:{lon:.3f}:{demo}"
    cached = await cache.get(f"weather:{cache_key}")
    if cached:
        return cached
    if demo:
        data = _demo_weather()[1]
        await cache.set(f"weather:{cache_key}", data, 600)
        return data
    try:
        raw = await _fetch_open_meteo(lat, lon, hourly=True)
        data = _parse_open_meteo(raw, hourly=True)
    except Exception:
        data = _demo_weather(is_weather_failure=True)[1]
    await cache.set(f"weather:{cache_key}", data, 600)
    return data


async def async_get_rainfall_accumulation(lat: float, lon: float, demo: bool = False) -> dict:
    """Return recent rainfall accumulations (1h/3h/6h/12h/24h) in mm."""
    forecast = (await async_get_hourly_forecast(lat, lon, demo=demo)).get("forecast", [])
    # Use precipitation from forecast series (current hour + future).
    series = [f["precipitation"] for f in forecast[:24]]
    if not series:
        cur = (await async_get_current_weather(lat, lon, demo=demo))["current"]["precipitation"]
        series = [cur]
    return {
        "rainfall_1h": round(sum(series[:1]), 1),
        "rainfall_3h": round(sum(series[:3]), 1),
        "rainfall_6h": round(sum(series[:6]), 1),
        "rainfall_12h": round(sum(series[:12]), 1),
        "rainfall_24h": round(sum(series[:24]), 1),
    }


async def async_normalize_weather_data(lat: float, lon: float, demo: bool = False) -> dict:
    """Return unified {current, forecast} pulled from the live provider."""
    current_data, forecast_data = await asyncio.gather(
        async_get_current_weather(lat, lon, demo=demo),
        async_get_hourly_forecast(lat, lon, demo=demo),
    )
    current = current_data["current"]
    forecast = forecast_data["forecast"]
    is_demo = current.get("__demo__", demo)
    return {
        "source": "openmeteo",
        "is_demo": bool(is_demo),
        "current": {k: v for k, v in current.items() if k != "__demo__"},
        "forecast": forecast,
    }


def _run(coro):
    """Compatibility bridge for synchronous service and test callers."""
    import asyncio
    return asyncio.run(coro)


def get_current_weather(lat: float, lon: float, demo: bool = False) -> dict:
    return _run(async_get_current_weather(lat, lon, demo))


def get_hourly_forecast(lat: float, lon: float, demo: bool = False) -> dict:
    return _run(async_get_hourly_forecast(lat, lon, demo))


def get_rainfall_accumulation(lat: float, lon: float, demo: bool = False) -> dict:
    return _run(async_get_rainfall_accumulation(lat, lon, demo))


def normalize_weather_data(lat: float, lon: float, demo: bool = False) -> dict:
    return _run(async_normalize_weather_data(lat, lon, demo))


# --- Demo data -------------------------------------------------------------
def _demo_weather(is_weather_failure: bool = False) -> tuple[dict, dict]:
    """
    Deterministic, clearly-labelled demo weather.

    If is_weather_failure, the demo reflects a stalled/heavy-rain scenario so the
    rest of the pipeline (predictions, alerts, recommendations) still works
    end-to-end without any external provider.
    """
    now = datetime.now(timezone.utc)
    if is_weather_failure:
        current_precip = 38.0
        base_forecast = [42, 55, 68, 80, 92, 88, 70, 60, 45, 30, 20, 15]
    else:
        current_precip = 4.0
        base_forecast = [6, 10, 14, 18, 22, 20, 16, 12, 9, 7, 5, 4]

    current = {
        "temperature": 24.5,
        "humidity": 87.0,
        "pressure": 998.0,
        "wind_speed": 18.0,
        "precipitation": current_precip,
        "timestamp": now.isoformat(),
    }
    forecast = []
    for i, p in enumerate(base_forecast):
        t = now + timedelta(hours=i)
        forecast.append({
            "time": t.isoformat(),
            "precipitation": float(p),
            "temperature": 24.5 - i * 0.2,
            "humidity": min(99.0, 87 + i * 0.5),
            "pressure": 998 + i * 0.3,
            "wind_speed": 18 + i * 0.4,
        })
    demo_current = {
        "source": "demo",
        "is_demo": True,
        "current": current,
        "forecast": [],
    }
    demo_forecast = {
        "source": "demo",
        "is_demo": True,
        "current": current,
        "forecast": forecast,
    }
    return demo_current, demo_forecast
