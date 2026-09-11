"""
Periodic background task to sweep and mark expired holds.
Safe to run concurrently from multiple workers.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.database import async_session_factory
from app.movie.repository import MovieRepository


async def main() -> None:
    async with async_session_factory() as session:
        repo = MovieRepository(session)
        expired_ids = await repo.release_expired_holds()
        print(f"Swept {len(expired_ids)} expired hold(s): {expired_ids}")


if __name__ == "__main__":
    asyncio.run(main())