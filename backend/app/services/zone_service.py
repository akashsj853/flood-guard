"""
FloodGuard AI — zone repository helper.

Loads zones from the DB (seeded from ml/data/zones.csv). Falls back to the CSV
directly if the DB is unavailable so the API remains usable.
"""
from __future__ import annotations

import csv
import time
from pathlib import Path

from sqlalchemy.orm import Session

from app.models.models import Zone

_ZONE_FIELDS = [
    "zone_id", "name", "latitude", "longitude", "elevation", "slope",
    "drainage_capacity", "impervious_surface", "population",
    "population_density", "historical_flood_frequency",
]
_ZONE_CACHE: tuple[float, list[dict]] | None = None


def _row_to_dict(row) -> dict:
    if isinstance(row, Zone):
        return {k: getattr(row, k) for k in _ZONE_FIELDS}
    return {k: row[k] for k in _ZONE_FIELDS if k in row}


def get_all_zones(db: Session | None = None) -> list[dict]:
    global _ZONE_CACHE
    if db is not None:
        rows = db.query(Zone).all()
        if rows:
            zones = [_row_to_dict(r) for r in rows]
            _ZONE_CACHE = (time.monotonic() + 3600, zones)
            return zones
    if _ZONE_CACHE and _ZONE_CACHE[0] > time.monotonic():
        return _ZONE_CACHE[1]
    # CSV fallback.
    csv_path = Path(__file__).resolve().parents[3] / "ml" / "data" / "zones.csv"
    if csv_path.exists():
        with open(csv_path, newline="") as f:
            zones = [{k: _coerce(k, r[k]) for k in _ZONE_FIELDS} for r in csv.DictReader(f)]
            _ZONE_CACHE = (time.monotonic() + 3600, zones)
            return zones
    return []


def get_zone(zone_id: str, db: Session | None = None) -> dict | None:
    if db is not None:
        row = db.query(Zone).filter(Zone.zone_id == zone_id).first()
        if row:
            return _row_to_dict(row)
    for z in get_all_zones(db):
        if z["zone_id"] == zone_id:
            return z
    return None


def _coerce(field: str, value: str):
    if field in ("population", "historical_flood_frequency"):
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return 0
    try:
        return float(value)
    except (TypeError, ValueError):
        return value
