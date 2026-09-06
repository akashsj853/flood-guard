from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-only-change-this-secret")
ALGORITHM = "HS256"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hashed_password: str | None) -> bool:
    return bool(hashed_password and pwd_context.verify(password, hashed_password))


def create_token(user_id: int, role: str, token_type: str, expires_delta: timedelta) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {"sub": str(user_id), "role": role, "type": token_type, "iat": now, "exp": now + expires_delta},
        SECRET_KEY,
        algorithm=ALGORITHM,
    )


def decode_token(token: str, expected_type: str = "access") -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError as exc:
        raise ValueError("Invalid or expired token") from exc
    if payload.get("type") != expected_type or not payload.get("sub"):
        raise ValueError("Invalid token type")
    return payload


def access_token(user_id: int, role: str) -> str:
    return create_token(user_id, role, "access", timedelta(minutes=30))


def refresh_token(user_id: int, role: str) -> str:
    return create_token(user_id, role, "refresh", timedelta(days=14))