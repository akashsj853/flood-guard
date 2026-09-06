"""FloodGuard AI — FastAPI application entrypoint.

Real-time AI urban flood prediction, early-warning and decision-support API.
No IoT / sensor ingestion — all inputs come from weather + forecast providers
behind the WeatherService abstraction.
"""
from __future__ import annotations

from contextlib import asynccontextmanager
import hashlib
import logging
import time
from collections import defaultdict, deque

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from starlette.requests import Request

from app.models.database import init_db, seed_zones_if_empty
from app.api import (
    weather, zones, predictions, alerts, simulation, analytics,
)
from app.api import auth
from app.api import profile


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    seed_zones_if_empty()
    yield


app = FastAPI(
    title="FloodGuard AI",
    description=(
        "Real-Time AI Urban Flood Prediction, Early Warning and Decision Support. "
        "This platform produces decision-support outputs and does NOT replace "
        "official disaster-management warnings."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

logger = logging.getLogger("floodguard.api")
_request_windows: dict[str, deque[float]] = defaultdict(deque)


@app.middleware("http")
async def performance_middleware(request: Request, call_next):
    started = time.perf_counter()
    client = request.client.host if request.client else "unknown"
    if request.url.path.startswith("/api/"):
        now = time.monotonic()
        window = _request_windows[client]
        while window and now - window[0] > 60:
            window.popleft()
        if len(window) >= 120:
            from fastapi.responses import JSONResponse
            return JSONResponse({"detail": "Rate limit exceeded."}, status_code=429)
        window.append(now)

    response = await call_next(request)
    elapsed = time.perf_counter() - started
    if elapsed > 0.3:
        logger.warning("slow request path=%s duration_ms=%.1f", request.url.path, elapsed * 1000)
    if request.method == "GET" and response.status_code == 200:
        response.headers.setdefault("Cache-Control", "public, max-age=30, stale-while-revalidate=60")
        body = b""
        async for chunk in response.body_iterator:
            body += chunk
        response.headers["ETag"] = hashlib.sha256(body).hexdigest()[:16]
        from starlette.responses import Response
        return Response(content=body, status_code=response.status_code, headers=dict(response.headers), media_type=response.media_type)
    return response


app.add_middleware(GZipMiddleware, minimum_size=1000)

# CORS — allow the Vite dev server (5173) and any same-origin deployment.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(weather.router)
app.include_router(zones.router)
app.include_router(predictions.router)
app.include_router(alerts.router)
app.include_router(simulation.router)
app.include_router(analytics.router)
app.include_router(auth.router)
app.include_router(profile.router)


@app.get("/api/health", tags=["health"])
def health():
    return {
        "status": "ok",
        "service": "floodguard-ai",
        "version": "1.0.0",
        "message": "Real-time AI urban flood prediction API is running.",
    }


@app.get("/", tags=["health"])
def root():
    return {"status": "ok", "docs": "/docs", "health": "/api/health"}
