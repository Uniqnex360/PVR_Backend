"""
Single source of truth for Base, engine, and session factory.
"""

from collections.abc import AsyncGenerator
import urllib.parse

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


class Base(DeclarativeBase):
    pass


def clean_async_db_url(url: str) -> str:
    """
    Ensure URL is fully compatible with asyncpg:
    - Sets postgresql+asyncpg:// prefix
    - Converts sslmode= -> ssl=
    - Strips unsupported libpq parameters like channel_binding, gssencmode, etc.
    """
    if not url:
        return url

    clean_url = url
    if clean_url.startswith("postgres://"):
        clean_url = clean_url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif clean_url.startswith("postgresql://") and not clean_url.startswith("postgresql+asyncpg://"):
        clean_url = clean_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    parsed = urllib.parse.urlsplit(clean_url)
    if not parsed.query:
        return clean_url

    query_params = urllib.parse.parse_qs(parsed.query)
    filtered_params: dict[str, list[str]] = {}

    for key, values in query_params.items():
        if key == "sslmode":
            filtered_params["ssl"] = values
        elif key in ("channel_binding", "gssencmode", "target_session_attrs"):
            continue
        else:
            filtered_params[key] = values

    flat_query = []
    for key, val_list in filtered_params.items():
        for val in val_list:
            flat_query.append(f"{key}={val}")

    new_query = "&".join(flat_query)
    return urllib.parse.urlunsplit(parsed._replace(query=new_query))


engine = create_async_engine(clean_async_db_url(settings.DATABASE_URL), echo=False)

async_session_factory = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session