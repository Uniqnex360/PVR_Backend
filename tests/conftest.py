

from __future__ import annotations

import os
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.movie.models import *  


def _db_urls() -> list[str]:
    urls = ["sqlite+aiosqlite://"]  
    pg = os.getenv("TEST_DATABASE_URL")
    if pg:
        urls.append(pg)
    return urls


@pytest_asyncio.fixture(
    params=_db_urls(), ids=lambda u: u.split("+")[0]
)
async def session_factory(request):
    url = request.param
    engine_kwargs = {"echo": False}
    if "sqlite" in url:
        engine_kwargs["connect_args"] = {"check_same_thread": False}
        engine_kwargs["poolclass"] = StaticPool

    engine = create_async_engine(url, **engine_kwargs)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    yield factory

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def session(session_factory):
    async with session_factory() as sess:
        yield sess