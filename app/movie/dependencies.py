"""Composition root for Movie & Booking module."""

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_session
from app.movie.email_service import ConsoleEmailService, SMTPEmailService
from app.movie.interfaces import IEmailService
from app.movie.repository import MovieRepository
from app.movie.services import MovieService


def get_email_service() -> IEmailService:
    if settings.SMTP_USER and settings.SMTP_PASSWORD:
        return SMTPEmailService()
    return ConsoleEmailService()


def get_movie_service(
    session: AsyncSession = Depends(get_session),
    email_service: IEmailService = Depends(get_email_service),
) -> MovieService:
    repo = MovieRepository(session)
    return MovieService(movie_repo=repo, email_service=email_service)