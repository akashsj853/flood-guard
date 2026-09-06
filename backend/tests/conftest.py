"""FloodGuard AI — pytest fixtures.

Sets up an isolated SQLite DB + FastAPI TestClient before importing app code so
tests never touch the developer's `floodguard.db`.
"""
from __future__ import annotations

import os
import tempfile

import pytest


def _make_tmp_db() -> str:
    fd, path = tempfile.mkstemp(suffix=".db", prefix="fgtest_")
    os.close(fd)
    return f"sqlite:///{path}"


@pytest.fixture(scope="session")
def db_url() -> str:
    url = _make_tmp_db()
    # Must be set before importing app.models.database (reads env at import).
    os.environ["DATABASE_URL"] = url
    return url


@pytest.fixture()
def client(db_url):
    from fastapi.testclient import TestClient
    from app.main import app
    from app.models.database import init_db, seed_zones_if_empty

    # The db_url session fixture already set DATABASE_URL; re-init for safety.
    init_db()
    seed_zones_if_empty()

    with TestClient(app) as c:
        from app.models.database import SessionLocal
        from app.models.models import User
        from app.services.auth_service import hash_password
        db = SessionLocal()
        operator = db.query(User).filter(User.username == "test-operator").first()
        if not operator:
            operator = User(
                username="test-operator",
                email="test-operator@example.com",
                hashed_password=hash_password("test-password-123"),
                role="operator",
            )
            db.add(operator)
            db.commit()
        db.close()
        login = c.post("/api/auth/login", json={"username": "test-operator", "password": "test-password-123"})
        assert login.status_code == 200
        yield c


@pytest.fixture()
def demo_weather() -> dict:
    """A clearly-labelled demo current/forecast payload."""
    from app.services import weather_service

    return weather_service.normalize_weather_data(12.97, 77.59, demo=True)


@pytest.fixture()
def sample_zone() -> dict:
    from app.services.zone_service import get_all_zones

    zones = get_all_zones(None)
    assert zones, "zones.csv must be available for tests"
    return zones[0]
