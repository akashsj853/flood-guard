"""Authentication and authorization contract tests."""
from __future__ import annotations

import uuid


def test_register_defaults_to_citizen(client):
    suffix = uuid.uuid4().hex[:8]
    response = client.post("/api/auth/register", json={
        "username": f"new-citizen-{suffix}",
        "email": f"new-citizen-{suffix}@example.com",
        "password": "strong-pass-123",
        "role": "admin",
    })
    assert response.status_code == 201
    assert response.json()["user"]["role"] == "citizen"


def test_login_me_and_refresh(client):
    response = client.post("/api/auth/login", json={
        "username": "test-operator",
        "password": "test-password-123",
    })
    assert response.status_code == 200
    assert client.get("/api/auth/me").json()["role"] == "operator"
    refreshed = client.post("/api/auth/refresh")
    assert refreshed.status_code == 200
    assert refreshed.json()["user"]["username"] == "test-operator"


def test_admin_login_requires_admin_role(client):
    rejected = client.post("/api/auth/admin-login", json={
        "username": "test-operator",
        "password": "test-password-123",
    })
    assert rejected.status_code == 401

    from app.models.database import SessionLocal
    from app.models.models import User
    from app.services.auth_service import hash_password
    import uuid
    suffix = uuid.uuid4().hex[:8]
    db = SessionLocal()
    admin = User(
        username=f"test-admin-{suffix}",
        email=f"test-admin-{suffix}@example.com",
        hashed_password=hash_password("admin-password-123"),
        role="admin",
    )
    admin_username = admin.username
    db.add(admin)
    db.commit()
    db.close()
    authenticated = client.post("/api/auth/admin-login", json={
        "username": admin_username,
        "password": "admin-password-123",
    })
    assert authenticated.status_code == 200
    assert authenticated.json()["user"]["role"] == "admin"


def test_admin_register_without_invite(client):
    import uuid
    suffix = uuid.uuid4().hex[:8]
    response = client.post("/api/auth/admin-register", json={
        "username": f"admin-{suffix}",
        "email": f"admin-{suffix}@example.com",
        "password": "admin-password-123",
    })
    assert response.status_code == 201
    assert response.json()["user"]["role"] == "admin"


def test_anonymous_cannot_simulate(client):
    client.post("/api/auth/logout")
    response = client.post("/api/simulation", json={"zone_id": "Z001", "adjustments": {}})
    assert response.status_code == 401


def test_citizen_cannot_use_operations(client):
    client.post("/api/auth/logout")
    suffix = uuid.uuid4().hex[:8]
    registered = client.post("/api/auth/register", json={
        "username": f"citizen-only-{suffix}",
        "email": f"citizen-only-{suffix}@example.com",
        "password": "strong-pass-123",
    })
    assert registered.status_code == 201
    response = client.post("/api/simulation", json={"zone_id": "Z001", "adjustments": {}})
    assert response.status_code == 403


def test_profile_locations_and_subscriptions(client):
    saved = client.post("/api/profile/locations", json={"zone_id": "Z001", "label": "Home"})
    assert saved.status_code == 201
    assert saved.json()["label"] == "Home"
    listed = client.get("/api/profile/locations")
    assert listed.status_code == 200
    assert listed.json()["locations"]
    subscription = client.post("/api/profile/subscriptions", json={"zone_id": "Z001", "risk_threshold": "HIGH"})
    assert subscription.status_code == 201
    assert client.get("/api/profile/subscriptions").json()["subscriptions"]


def test_zone_history_is_public(client):
    client.post("/api/auth/logout")
    response = client.get("/api/zones/Z001/history")
    assert response.status_code == 200
    assert response.json()["zone_id"] == "Z001"