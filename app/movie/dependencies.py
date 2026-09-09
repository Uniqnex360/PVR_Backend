"""Composition root for Movie & Booking module."""

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.movie.email_service import ConsoleEmailService
from app.movie.interfaces import IEmailService
from app.movie.repository import MovieRepository
from app.movie.services import MovieService

_email_service_instance = ConsoleEmailService()


def get_email_service() -> IEmailService:
    return _email_service_instance


def get_movie_service(
    session: AsyncSession = Depends(get_session),
    email_service: IEmailService = Depends(get_email_service),
) -> MovieService:
    repo = MovieRepository(session)
    return MovieService(movie_repo=repo, email_service=email_service)