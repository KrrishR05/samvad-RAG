"""
SAMVAD Authentication Request & Response Schemas
"""

from __future__ import annotations

import re
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator


_EMAIL_REGEX = re.compile(r"^[\w\.\+\-]+@[a-zA-Z0-9\-]+\.[a-zA-Z0-9\-\.]+$")


class SignupRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=60, description="User's full name")
    email: str = Field(..., description="Valid email address")
    password: str = Field(..., min_length=6, max_length=128, description="Account password (min 6 chars)")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        cleaned = v.strip().lower()
        if not _EMAIL_REGEX.match(cleaned):
            raise ValueError("Invalid email format.")
        return cleaned

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        cleaned = v.strip()
        if len(cleaned) < 2:
            raise ValueError("Name must be at least 2 characters.")
        return cleaned


class LoginRequest(BaseModel):
    email: str = Field(..., description="Registered email address")
    password: str = Field(..., min_length=1, description="Account password")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        cleaned = v.strip().lower()
        if not _EMAIL_REGEX.match(cleaned):
            raise ValueError("Invalid email format.")
        return cleaned


class GoogleAuthRequest(BaseModel):
    credential: Optional[str] = Field(default=None, description="Google ID token from Google Identity Services")
    # Also support direct OAuth profile payload for dev / standalone client auth
    google_id: Optional[str] = Field(default=None, description="Google user identifier")
    email: Optional[str] = Field(default=None, description="Google verified email")
    name: Optional[str] = Field(default=None, description="Google profile name")
    avatar_url: Optional[str] = Field(default=None, description="Google profile picture URL")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        cleaned = v.strip().lower()
        if not _EMAIL_REGEX.match(cleaned):
            raise ValueError("Invalid email format.")
        return cleaned


class ProfileUpdateRequest(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=60)
    plan: Optional[str] = Field(default=None, description="'free' or 'pro'")
    avatar_url: Optional[str] = Field(default=None)


class UserDTO(BaseModel):
    id: str
    email: str
    name: str
    provider: str
    google_id: Optional[str] = None
    avatar_url: Optional[str] = None
    plan: str
    created_at: str
    updated_at: str


class AuthResponse(BaseModel):
    token: str
    user: UserDTO
    message: str = "Authentication successful"


class UserResponse(BaseModel):
    user: UserDTO


class StatusMessageResponse(BaseModel):
    status: str = "ok"
    message: str


class WaitlistRequest(BaseModel):
    email: str = Field(..., description="Email address for Pro waitlist notification")
    name: Optional[str] = Field(default=None, description="Optional user name")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        cleaned = v.strip().lower()
        if not _EMAIL_REGEX.match(cleaned):
            raise ValueError("Invalid email format.")
        return cleaned


class WaitlistResponse(BaseModel):
    status: str = "joined"  # "joined" or "already_joined"
    email: str
    position: int
    email_sent: bool
    message: str


class WaitlistStatusResponse(BaseModel):
    on_waitlist: bool
    email: str
    position: Optional[int] = None
