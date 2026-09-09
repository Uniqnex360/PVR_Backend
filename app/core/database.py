"""
Single source of truth for Base, engine, and session factory.

One Base in the whole project.  Do NOT create a second one in
app/shared/ or anywhere else.
"""

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


class Base(DeclarativeBase):
    pass


engine = create_async_engine(settings.DATABASE_URL, echo=False)

async_session_factory = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def get_session() -> AsyncSession:  # type: ignore[misc]
    async with async_session_factory() as session:
        yield session