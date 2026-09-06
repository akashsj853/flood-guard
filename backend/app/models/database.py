"""
FloodGuard AI — database engine, session, and schema bootstrap.

Uses SQLite for development; switch DATABASE_URL to PostgreSQL for deployment.
"""
from __future__ import annotations

import os
from pathlib import Path

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./floodguard.db")

# SQLite needs check_same_thread=False for FastAPI's threadpool.
_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

# Resolve relative sqlite paths against the backend/ directory so the DB file
# lives next to the app regardless of the working directory.
if DATABASE_URL.startswith("sqlite:///") and not DATABASE_URL.startswith("sqlite:////"):
    rel = DATABASE_URL.replace("sqlite:///", "", 1)
    if not os.path.isabs(rel):
        backend_dir = Path(__file__).resolve().parents[2]
        DATABASE_URL = f"sqlite:///{backend_dir / rel}"

engine = create_engine(DATABASE_URL, connect_args=_connect_args, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()


def get_db():
    """FastAPI dependency yielding a scoped session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create tables (idempotent). Imports models to register them on Base."""
    from app.models import models  # noqa: F401  (registers tables on Base)
    Base.metadata.create_all(bind=engine)
    _upgrade_existing_users_table()


def _upgrade_existing_users_table() -> None:
    """Add auth columns to developer databases created before auth existed."""
    columns = {column["name"] for column in inspect(engine).get_columns("users")}
    additions = {
        "email": "VARCHAR(255)",
        "hashed_password": "VARCHAR(255)",
    }
    with engine.begin() as connection:
        for name, definition in additions.items():
            if name not in columns:
                connection.execute(text(f"ALTER TABLE users ADD COLUMN {name} {definition}"))


def seed_zones_if_empty() -> None:
    """Seed the Zone table from ml/data/zones.csv when it is empty."""
    from app.models.models import Zone

    db = SessionLocal()
    try:
        if db.query(Zone).count() > 0:
            return
        csv_path = Path(__file__).resolve().parents[3] / "ml" / "data" / "zones.csv"
        if not csv_path.exists():
            return
        import csv

        with open(csv_path, newline="") as f:
            for row in csv.DictReader(f):
                db.add(Zone(
                    zone_id=row["zone_id"],
                    name=row["name"],
                    latitude=float(row["latitude"]),
                    longitude=float(row["longitude"]),
                    elevation=float(row["elevation"]),
                    slope=float(row["slope"]),
                    drainage_capacity=float(row["drainage_capacity"]),
                    impervious_surface=float(row["impervious_surface"]),
                    population=int(float(row["population"])),
                    population_density=float(row["population_density"]),
                    historical_flood_frequency=int(float(row["historical_flood_frequency"])),
                ))
        db.commit()
    finally:
        db.close()
