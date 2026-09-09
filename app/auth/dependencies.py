"""
Composition root for Auth.
"""

from __future__ import annotations

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.exceptions import InvalidTokenHTTPError, UserNotFoundHTTPError
from app.auth.interfaces import InvalidTokenError, UserDTO, UserNotFoundError
from app.auth.repository import UserRepository
from app.auth.services import AuthService
from app.core.config import settings
from app.core.database import get_session

bearer_scheme = HTTPBearer(auto_error=False)


def get_auth_service(
    session: AsyncSession = Depends(get_session),
) -> AuthService:
    repo = UserRepository(session)
    return AuthService(
        user_repo=repo,
        jwt_secret=settings.JWT_SECRET,
    )


async def get_current_user(
    auth: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    auth_service: AuthService = Depends(get_auth_service),
) -> UserDTO:
    if auth is None or not auth.credentials:
        raise InvalidTokenHTTPError("Missing or invalid authorization token")

    try:
        user_id = auth_service.decode_token(auth.credentials)
        return await auth_service.get_user_by_id(user_id)
    except InvalidTokenError:
        raise InvalidTokenHTTPError("Invalid or expired token")
    except UserNotFoundError:
        raise UserNotFoundHTTPError("User not found")