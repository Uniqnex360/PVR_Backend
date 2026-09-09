"""
Async Alembic environment.
Dynamically uses settings.DATABASE_URL in production with asyncpg sanitization.
"""

import asyncio
import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

# Ensure the backend root is importable regardless of cwd
sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

from app.core.config import settings  # noqa: E402
from app.core.database import Base, clean_async_db_url  # noqa: E402
from app.movie.models import *  # noqa: E402, F401, F403

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Inject sanitized environment DATABASE_URL into alembic config
if getattr(settings, "DATABASE_URL", None):
    config.set_main_option(
        "sqlalchemy.url", clean_async_db_url(settings.DATABASE_URL)
    )

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        render_as_batch=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()