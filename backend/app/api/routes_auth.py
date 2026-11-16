"""
SAMVAD API — Authentication & User Profile Routes

Provides production-grade authentication:
- Email/Password Signup & Login
- Google OAuth (Google Identity Services ID Token / Profile)
- Session verification (GET /auth/me)
- Profile management & Plan upgrades (PATCH /auth/profile)
- Session Logout (POST /auth/logout)
"""

from __future__ import annotations

import base64
import json
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status

from app.core.auth_store import AuthStore, UserRecord, get_auth_store
from app.schemas.auth import (
    AuthResponse,
    GoogleAuthRequest,
    LoginRequest,
    ProfileUpdateRequest,
    SignupRequest,
    StatusMessageResponse,
    UserDTO,
    UserResponse,
)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


def _extract_bearer_token(authorization: Optional[str] = Header(None)) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or malformed Authorization header. Expected 'Bearer <token>'.",
        )
    return authorization[7:].strip()


def get_current_user(
    token: str = Depends(_extract_bearer_token),
    store: AuthStore = Depends(get_auth_store),
) -> UserRecord:
    user = store.get_user_from_token(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired or invalid. Please sign in again.",
        )
    return user


def _to_user_dto(record: UserRecord) -> UserDTO:
    return UserDTO(
        id=record.id,
        email=record.email,
        name=record.name,
        provider=record.provider,
        google_id=record.google_id,
        avatar_url=record.avatar_url,
        plan=record.plan,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


@router.post(
    "/signup",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account with email and password",
)
async def signup(payload: SignupRequest, store: AuthStore = Depends(get_auth_store)) -> AuthResponse:
    existing = store.get_user_by_email(str(payload.email))
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists. Please log in.",
        )

    user = store.create_user_with_password(
        email=str(payload.email),
        password=payload.password,
        name=payload.name,
    )
    token = store.create_session(user.id)
    return AuthResponse(
        token=token,
        user=_to_user_dto(user),
        message="Account created successfully. Welcome to SAMVAD!",
    )


@router.post(
    "/login",
    response_model=AuthResponse,
    summary="Authenticate existing user with email and password",
)
async def login(payload: LoginRequest, store: AuthStore = Depends(get_auth_store)) -> AuthResponse:
    user = store.verify_credentials(str(payload.email), payload.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password. Please verify your credentials.",
        )

    token = store.create_session(user.id)
    return AuthResponse(
        token=token,
        user=_to_user_dto(user),
        message=f"Welcome back, {user.name}!",
    )


@router.post(
    "/google",
    response_model=AuthResponse,
    summary="Authenticate with Google (Continue with Google / Google One-Tap)",
)
async def google_auth(payload: GoogleAuthRequest, store: AuthStore = Depends(get_auth_store)) -> AuthResponse:
    google_id = payload.google_id
    email = str(payload.email) if payload.email else None
    name = payload.name
    avatar_url = payload.avatar_url

    # If Google ID Token is provided, parse standard unencrypted JWT claims
    if payload.credential:
        try:
            parts = payload.credential.split(".")
            if len(parts) >= 2:
                # Add padding if required
                padded = parts[1] + "=" * ((4 - len(parts[1]) % 4) % 4)
                claims = json.loads(base64.urlsafe_b64decode(padded).decode("utf-8"))
                google_id = claims.get("sub", google_id)
                email = claims.get("email", email)
                name = claims.get("name", name)
                avatar_url = claims.get("picture", avatar_url)
        except Exception:
            pass  # Fall back to payload fields if credential decoding fails

    if not google_id or not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incomplete Google authentication payload: both google_id and email are required.",
        )

    user = store.create_or_update_google_user(
        google_id=google_id,
        email=email,
        name=name or "Google User",
        avatar_url=avatar_url,
    )
    token = store.create_session(user.id)
    return AuthResponse(
        token=token,
        user=_to_user_dto(user),
        message=f"Signed in with Google as {user.name}.",
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current authenticated user profile",
)
async def get_me(user: UserRecord = Depends(get_current_user)) -> UserResponse:
    return UserResponse(user=_to_user_dto(user))


@router.patch(
    "/profile",
    response_model=UserResponse,
    summary="Update user profile settings (name, avatar, subscription plan)",
)
async def update_profile(
    payload: ProfileUpdateRequest,
    user: UserRecord = Depends(get_current_user),
    store: AuthStore = Depends(get_auth_store),
) -> UserResponse:
    updated = store.update_user_profile(
        user_id=user.id,
        name=payload.name,
        plan=payload.plan,
        avatar_url=payload.avatar_url,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="User not found.")
    return UserResponse(user=_to_user_dto(updated))


@router.post(
    "/logout",
    response_model=StatusMessageResponse,
    summary="Revoke active user session",
)
async def logout(
    token: str = Depends(_extract_bearer_token),
    store: AuthStore = Depends(get_auth_store),
) -> StatusMessageResponse:
    store.revoke_session(token)
    return StatusMessageResponse(message="Logged out successfully.")

