#!/usr/bin/env python3
"""
Idempotent seed for the PVR demo database.

Safe to run 50 times — uses natural-key lookups, not "insert and pray".
Showtimes are relative to today so the demo never shows yesterday's
sold-out 6 pm slot.

Usage:
    python scripts/seed.py                  # uses DATABASE_URL from .env
    python scripts/seed.py <database_url>   # explicit override (for tests)
"""

from __future__ import annotations

import sys
import uuid
from datetime import datetime, time
from pathlib import Path
from zoneinfo import ZoneInfo

# Ensure app is importable from the repo root or backend/.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from passlib.context import CryptContext  # noqa: E402
from sqlalchemy import create_engine, func, select  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.core.config import settings  # noqa: E402
from app.movie.models import (  # noqa: E402
    Cinema,
    Movie,
    Screen,
    ScreenRow,
    Seat,
    Showtime,
    User,
)

pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

ROW_CONFIGS: list[tuple[str, int, int]] = [
    ("A", 20, 19_000),
    ("B", 20, 19_000),
    ("C", 20, 19_000),
    ("D", 22, 29_000),
    ("E", 22, 29_000),
    ("F", 22, 29_000),
    ("G", 26, 39_000),
    ("H", 26, 39_000),
    ("I", 28, 39_000),
    ("J", 28, 39_000),
]
SHOWTIME_TIMES = [time(15, 30), time(19, 0), time(22, 15)]


def _to_sync_url(async_url: str) -> str:
    return (
        async_url.replace("+aiosqlite", "")
        .replace("+asyncpg", "")
    )


def seed(db_url: str | None = None) -> None:
    url = _to_sync_url(db_url or settings.DATABASE_URL)
    engine = create_engine(url)

    with Session(engine) as s:
        # ---- user ----
        user = s.execute(
            select(User).where(User.email == "demo@pvr.local")
        ).scalar_one_or_none()
        if not user:
            user = User(
                id=uuid.uuid4(),
                email="demo@pvr.local",
                password_hash=pwd.hash("demo1234"),
                role="customer",
            )
            s.add(user)
            s.flush()

        # ---- cinema ----
        cinema = s.execute(
            select(Cinema).where(Cinema.name == "PVR Lulu Mall")
        ).scalar_one_or_none()
        if not cinema:
            cinema = Cinema(
                id=uuid.uuid4(),
                name="PVR Lulu Mall",
                city="Kochi",
                timezone="Asia/Kolkata",
            )
            s.add(cinema)
            s.flush()

        # ---- screen ----
        screen = s.execute(
            select(Screen).where(
                Screen.cinema_id == cinema.id,
                Screen.name == "Screen 1",
            )
        ).scalar_one_or_none()
        if not screen:
            screen = Screen(
                id=uuid.uuid4(),
                cinema_id=cinema.id,
                name="Screen 1",
            )
            s.add(screen)
            s.flush()

        # ---- rows + seats ----
        for label, seat_count, price_cents in ROW_CONFIGS:
            row = s.execute(
                select(ScreenRow).where(
                    ScreenRow.screen_id == screen.id,
                    ScreenRow.label == label,
                )
            ).scalar_one_or_none()
            if not row:
                row = ScreenRow(
                    id=uuid.uuid4(),
                    screen_id=screen.id,
                    label=label,
                    seat_count=seat_count,
                    price_cents=price_cents,
                )
                s.add(row)
                s.flush()

            existing = s.execute(
                select(func.count())
                .select_from(Seat)
                .where(Seat.row_id == row.id)
            ).scalar()
            if existing == 0:
                for num in range(1, seat_count + 1):
                    s.add(
                        Seat(
                            id=uuid.uuid4(),
                            row_id=row.id,
                            number=num,
                            code=f"{label}{num:02d}",
                        )
                    )
                s.flush()

        # ---- movie ----
        movie = s.execute(
            select(Movie).where(Movie.title == "I am Game")
        ).scalar_one_or_none()
        if not movie:
            movie = Movie(
                id=uuid.uuid4(),
                title="I am Game",
                duration_min=162,
                language="Malayalam",
                certificate="UA",
                release_year=2025,
            )
            s.add(movie)
            s.flush()

        # ---- showtimes (relative to today in cinema tz) ----
        tz = ZoneInfo(cinema.timezone)
        today = datetime.now(tz).date()
        showtime_ids: list[str] = []

        for t in SHOWTIME_TIMES:
            local_dt = datetime.combine(today, t, tzinfo=tz)
            utc_dt = local_dt.astimezone(ZoneInfo("UTC"))

            st = s.execute(
                select(Showtime).where(
                    Showtime.screen_id == screen.id,
                    Showtime.starts_at == utc_dt,
                )
            ).scalar_one_or_none()
            if not st:
                st = Showtime(
                    id=uuid.uuid4(),
                    screen_id=screen.id,
                    movie_id=movie.id,
                    starts_at=utc_dt,
                )
                s.add(st)
                s.flush()
            showtime_ids.append(str(st.id))

        s.commit()

    print(
        "Seeded: 1 user, 1 cinema, 1 screen, 10 rows, "
        "234 seats, 1 movie, 3 showtimes"
    )
    print(f"Showtime IDs: {', '.join(showtime_ids)}")


if __name__ == "__main__":
    seed(sys.argv[1] if len(sys.argv) > 1 else None)