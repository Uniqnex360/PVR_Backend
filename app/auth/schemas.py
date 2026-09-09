"""Pydantic request / response schemas for Auth."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Requests
# ---------------------------------------------------------------------------

class RegisterRequest(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=6, max_length=128)


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    password: str


# ---------------------------------------------------------------------------
# Responses
# ---------------------------------------------------------------------------

class UserResponse(BaseModel):
    id: UUID
    email: str
    role: str
    created_at: datetime


class AuthResponse(BaseModel):
    token: str
    user: UserResponse