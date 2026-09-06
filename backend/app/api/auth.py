from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.models.database import get_db
from app.models.models import User
from app.models.schemas import (
    AdminRegisterRequest, AuthResponse, ForgotPasswordRequest, LoginRequest,
    RegisterRequest, UserResponse,
)
from app.services.auth_service import (
    access_token, decode_token, hash_password, refresh_token, verify_password,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


def serialize_user(user: User) -> UserResponse:
    return UserResponse(id=user.id, username=user.username, email=user.email, role=user.role)


def _set_tokens(response: Response, user: User) -> None:
    response.set_cookie("access_token", access_token(user.id, user.role), httponly=True, samesite="lax", max_age=1800)
    response.set_cookie("refresh_token", refresh_token(user.id, user.role), httponly=True, samesite="lax", max_age=1209600)


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    token = request.cookies.get("access_token")
    if not token:
        authorization = request.headers.get("Authorization", "")
        if authorization.lower().startswith("bearer "):
            token = authorization[7:].strip()
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    try:
        payload = decode_token(token)
        user = db.query(User).filter(User.id == int(payload["sub"])).first()
    except (ValueError, TypeError):
        user = None
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials")
    return user


def require_roles(*roles: str):
    def dependency(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return user
    return dependency


@router.post("/register", response_model=AuthResponse, status_code=201)
def register(payload: RegisterRequest, response: Response, db: Session = Depends(get_db)):
    if db.query(User).filter((User.username == payload.username) | (User.email == payload.email)).first():
        raise HTTPException(status_code=409, detail="Username or email already registered")
    user = User(username=payload.username, email=payload.email, hashed_password=hash_password(payload.password), role="citizen")
    db.add(user)
    db.commit()
    db.refresh(user)
    _set_tokens(response, user)
    return AuthResponse(user=serialize_user(user), message="Registration successful")


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter((User.username == payload.username) | (User.email == payload.username)).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    _set_tokens(response, user)
    return AuthResponse(user=serialize_user(user))


@router.post("/admin-login", response_model=AuthResponse)
def admin_login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter((User.username == payload.username) | (User.email == payload.username)).first()
    if not user or user.role != "admin" or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid administrator credentials")
    _set_tokens(response, user)
    return AuthResponse(user=serialize_user(user), message="Administrator authenticated")


@router.post("/admin-register", response_model=AuthResponse, status_code=201)
def admin_register(payload: AdminRegisterRequest, response: Response, db: Session = Depends(get_db)):
    if db.query(User).filter((User.username == payload.username) | (User.email == payload.email)).first():
        raise HTTPException(status_code=409, detail="Username or email already registered")
    user = User(
        username=payload.username,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        role="admin",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    _set_tokens(response, user)
    return AuthResponse(user=serialize_user(user), message="Administrator account created")


@router.post("/refresh", response_model=AuthResponse)
def refresh(request: Request, response: Response, db: Session = Depends(get_db)):
    token = request.cookies.get("refresh_token")
    if not token:
        raise HTTPException(status_code=401, detail="Refresh token required")
    try:
        payload = decode_token(token, "refresh")
        user = db.query(User).filter(User.id == int(payload["sub"])).first()
    except (ValueError, TypeError):
        user = None
    if not user:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    _set_tokens(response, user)
    return AuthResponse(user=serialize_user(user), message="Token refreshed")


@router.get("/me", response_model=UserResponse)
def me(user: User = Depends(get_current_user)):
    return serialize_user(user)


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return {"message": "Logged out"}


@router.post("/forgot-password")
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    exists = db.query(User).filter(User.email == payload.email).first() is not None
    return {"message": "If that email exists, a reset link has been queued for development delivery.", "accepted": exists}