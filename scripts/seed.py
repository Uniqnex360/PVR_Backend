
from __future__ import annotations

import sys
import uuid
from datetime import datetime, time
from pathlib import Path
from zoneinfo import ZoneInfo


sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from passlib.context import CryptContext  
from sqlalchemy import create_engine, func, select  
from sqlalchemy.orm import Session  

from app.core.config import settings  
from app.movie.models import (  
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

MOVIE_1_TIMES = [time(15, 30), time(19, 0), time(22, 15)]
MOVIE_2_TIMES = [time(14, 0), time(17, 30), time(21, 0)]


def _to_sync_url(async_url: str) -> str:
    return async_url.replace("+aiosqlite", "").replace("+asyncpg", "")


def seed(db_url: str | None = None) -> None:
    url = _to_sync_url(db_url or settings.DATABASE_URL)
    engine = create_engine(url)

    with Session(engine) as s:
        
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

        
        screens_dict = {}
        for screen_name in ["Screen 1", "Screen 2"]:
            scr = s.execute(
                select(Screen).where(
                    Screen.cinema_id == cinema.id,
                    Screen.name == screen_name,
                )
            ).scalar_one_or_none()
            if not scr:
                scr = Screen(
                    id=uuid.uuid4(), cinema_id=cinema.id, name=screen_name
                )
                s.add(scr)
                s.flush()
            screens_dict[screen_name] = scr

            
            for label, seat_count, price_cents in ROW_CONFIGS:
                row = s.execute(
                    select(ScreenRow).where(
                        ScreenRow.screen_id == scr.id,
                        ScreenRow.label == label,
                    )
                ).scalar_one_or_none()
                if not row:
                    row = ScreenRow(
                        id=uuid.uuid4(),
                        screen_id=scr.id,
                        label=label,
                        seat_count=seat_count,
                        price_cents=price_cents,
                    )
                    s.add(row)
                    s.flush()

                existing_seats = s.execute(
                    select(func.count())
                    .select_from(Seat)
                    .where(Seat.row_id == row.id)
                ).scalar()
                if existing_seats == 0:
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

        
        
        m1 = s.execute(
            select(Movie).where(Movie.title == "I Am Game")
        ).scalar_one_or_none()
        if not m1:
            m1 = Movie(
                id=uuid.uuid4(),
                title="I Am Game",
                duration_min=162,
                language="Malayalam",
                certificate="UA",
                release_year=2025,
            )
            s.add(m1)
            s.flush()

        
        m2 = s.execute(
            select(Movie).where(Movie.title == "The Final Whistle")
        ).scalar_one_or_none()
        if not m2:
            m2 = Movie(
                id=uuid.uuid4(),
                title="The Final Whistle",
                duration_min=120,
                language="English",
                certificate="UA",
                release_year=2025,
            )
            s.add(m2)
            s.flush()

        
        tz = ZoneInfo(cinema.timezone)
        today = datetime.now(tz).date()

        
        for t in MOVIE_1_TIMES:
            local_dt = datetime.combine(today, t, tzinfo=tz)
            utc_dt = local_dt.astimezone(ZoneInfo("UTC"))
            st = s.execute(
                select(Showtime).where(
                    Showtime.screen_id == screens_dict["Screen 1"].id,
                    Showtime.starts_at == utc_dt,
                )
            ).scalar_one_or_none()
            if not st:
                s.add(
                    Showtime(
                        id=uuid.uuid4(),
                        screen_id=screens_dict["Screen 1"].id,
                        movie_id=m1.id,
                        starts_at=utc_dt,
                    )
                )

        
        for t in MOVIE_2_TIMES:
            local_dt = datetime.combine(today, t, tzinfo=tz)
            utc_dt = local_dt.astimezone(ZoneInfo("UTC"))
            st = s.execute(
                select(Showtime).where(
                    Showtime.screen_id == screens_dict["Screen 2"].id,
                    Showtime.starts_at == utc_dt,
                )
            ).scalar_one_or_none()
            if not st:
                s.add(
                    Showtime(
                        id=uuid.uuid4(),
                        screen_id=screens_dict["Screen 2"].id,
                        movie_id=m2.id,
                        starts_at=utc_dt,
                    )
                )

        s.commit()

    print(
        "Seeded successfully: 2 Screens, 468 Seats total, 2 Movies, 6 Showtimes."
    )


if __name__ == "__main__":
    seed(sys.argv[1] if len(sys.argv) > 1 else None)