"""
Ports, domain exceptions, and value objects for the Auth module.

Rule: services.py raises ONLY exceptions defined here (or in app.shared).
      Never import FastAPI or Starlette here.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol, runtime_checkable
from uuid import UUID

from app.shared.domain_exceptions import (
    ConflictError,
    DomainError,
    DuplicateError,
    NotFoundError,
)


# ---------------------------------------------------------------------------
# Value Objects / DTOs
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class UserDTO:
    id: UUID
    email: str
    role: str
    created_at: datetime


@dataclass(frozen=True, slots=True)
class AuthResult:
    token: str
    user: UserDTO


# ---------------------------------------------------------------------------
# Domain Exceptions (plain Exception subclasses — never HTTPException)
# ---------------------------------------------------------------------------

class UserAlreadyExistsError(DuplicateError):
    """User with this email already exists."""


class InvalidCredentialsError(DomainError):
    """Email or password is incorrect."""


class InvalidTokenError(DomainError):
    """JWT is invalid, expired, or malformed."""


class UserNotFoundError(NotFoundError):
    """User does not exist."""


# ---------------------------------------------------------------------------
# Repository Port
# ---------------------------------------------------------------------------

@runtime_checkable
class IUserRepository(Protocol):
    async def get_by_id(self, user_id: UUID) -> UserDTO | None: ...
    async def get_by_email(self, email: str) -> tuple[UserDTO, str] | None:
        """Returns (UserDTO, password_hash) or None."""
        ...
    async def create(
        self, email: str, password_hash: str, role: str = "customer"
    ) -> UserDTO: ...