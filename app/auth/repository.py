"""
SQLAlchemy repository for Users.
"""

from __future__ import annotations

from uuid import UUID
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.interfaces import UserAlreadyExistsError, UserDTO
from app.auth.models import User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, user_id: UUID) -> UserDTO | None:
        stmt = select(User).where(User.id == user_id)
        result = await self._session.execute(stmt)
        user = result.scalar_one_or_none()
        if not user:
            return None
        return UserDTO(
            id=user.id,
            email=user.email,
            role=user.role,
            created_at=user.created_at,
        )

    async def get_by_email(self, email: str) -> tuple[UserDTO, str] | None:
        stmt = select(User).where(User.email == email.lower().strip())
        result = await self._session.execute(stmt)
        user = result.scalar_one_or_none()
        if not user:
            return None
        dto = UserDTO(
            id=user.id,
            email=user.email,
            role=user.role,
            created_at=user.created_at,
        )
        return dto, user.password_hash

    async def create(
        self, email: str, password_hash: str, role: str = "customer"
    ) -> UserDTO:
        user = User(
            email=email.lower().strip(),
            password_hash=password_hash,
            role=role,
        )
        self._session.add(user)
        try:
            await self._session.commit()
        except IntegrityError as exc:
            await self._session.rollback()
            raise UserAlreadyExistsError(
                f"User with email '{email}' already exists"
            ) from exc

        return UserDTO(
            id=user.id,
            email=user.email,
            role=user.role,
            created_at=user.created_at,
        )