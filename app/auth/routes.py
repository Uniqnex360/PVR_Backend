"""
FastAPI routes for Auth.
Mounted with prefix /v1 via app.include_router(auth_router, prefix="/v1").
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, status

from app.auth.dependencies import get_auth_service, get_current_user
from app.auth.exceptions import (
    InvalidCredentialsHTTPError,
    UserAlreadyExistsHTTPError,
)
from app.auth.interfaces import (
    InvalidCredentialsError,
    UserAlreadyExistsError,
    UserDTO,
)
from app.auth.schemas import AuthResponse, LoginRequest, RegisterRequest, UserResponse
from app.auth.services import AuthService

auth_router = APIRouter(tags=["auth"])


@auth_router.post(
    "/auth/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    req: RegisterRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    try:
        result = await auth_service.register(req.email, req.password)
        return AuthResponse(
            token=result.token,
            user=UserResponse(
                id=result.user.id,
                email=result.user.email,
                role=result.user.role,
                created_at=result.user.created_at,
            ),
        )
    except UserAlreadyExistsError as exc:
        raise UserAlreadyExistsHTTPError(str(exc))


@auth_router.post("/auth/login", response_model=AuthResponse)
async def login(
    req: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    try:
        result = await auth_service.login(req.email, req.password)
        return AuthResponse(
            token=result.token,
            user=UserResponse(
                id=result.user.id,
                email=result.user.email,
                role=result.user.role,
                created_at=result.user.created_at,
            ),
        )
    except InvalidCredentialsError as exc:
        raise InvalidCredentialsHTTPError(str(exc))


@auth_router.get("/auth/me", response_model=UserResponse)
async def me(current_user: UserDTO = Depends(get_current_user)):
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        role=current_user.role,
        created_at=current_user.created_at,
    )