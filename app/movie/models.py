
from __future__ import annotations

import enum
import uuid

import sqlalchemy as sa
from sqlalchemy import (
    CheckConstraint,
    Column,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)

from app.core.database import Base
from app.shared.timeutil import TZDateTime, utcnow
from app.auth.models import User  
class HoldStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    COMMITTED = "COMMITTED"
    EXPIRED = "EXPIRED"
    RELEASED = "RELEASED"


class Hold(Base):
    __tablename__ = "holds"

    id = Column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    showtime_id = Column(
        sa.Uuid,
        ForeignKey("showtimes.id", ondelete="CASCADE"),
        nullable=False,
    )
    partner_id = Column(sa.Uuid, ForeignKey("users.id"), nullable=False)
    end_user_ref = Column(String, nullable=True)
    status = Column(
        String, nullable=False, server_default=sa.text("'ACTIVE'")
    )
    idempotency_key = Column(String, nullable=False)
    quote_total = Column(Integer, nullable=False)
    currency = Column(
        String, nullable=False, server_default=sa.text("'INR'")
    )
    expires_at = Column(TZDateTime, nullable=False)
    created_at = Column(
        TZDateTime,
        nullable=False,
        default=utcnow,
        server_default=sa.text("CURRENT_TIMESTAMP"),
    )
    updated_at = Column(
        TZDateTime,
        nullable=False,
        default=utcnow,
        onupdate=utcnow,
        server_default=sa.text("CURRENT_TIMESTAMP"),
    )

    __table_args__ = (
        UniqueConstraint(
            "partner_id",
            "end_user_ref",
            "idempotency_key",
            name="uq_hold_partner_enduser_idempotency",
        ),
        Index(
            "ix_holds_showtime_status_expires",
            "showtime_id",
            "status",
            "expires_at",
        ),
    )
class HoldSeat(Base):
    __tablename__ = "hold_seats"

    hold_id = Column(
        sa.Uuid,
        ForeignKey("holds.id", ondelete="CASCADE"),
        primary_key=True,
    )
    seat_id = Column(
        sa.Uuid, ForeignKey("seats.id"), primary_key=True
    )
    showtime_id = Column(
        sa.Uuid, ForeignKey("showtimes.id"), nullable=False
    )
    price_cents = Column(Integer, nullable=False)

    __table_args__ = (
        Index(
            "ux_hold_showtime_seat",
            "showtime_id",
            "seat_id",
            unique=True,
        ),
    )

class BookingStatus(str, enum.Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"






class Cinema(Base):
    __tablename__ = "cinemas"

    id = Column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    city = Column(String, nullable=False)
    timezone = Column(
        String, nullable=False, server_default=sa.text("'Asia/Kolkata'")
    )


class Screen(Base):
    __tablename__ = "screens"

    id = Column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    cinema_id = Column(
        sa.Uuid, ForeignKey("cinemas.id"), nullable=False
    )
    name = Column(String, nullable=False)


class ScreenRow(Base):
    __tablename__ = "screen_rows"

    id = Column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    screen_id = Column(
        sa.Uuid, ForeignKey("screens.id"), nullable=False
    )
    label = Column(String, nullable=False)
    seat_count = Column(Integer, nullable=False)
    price_cents = Column(Integer, nullable=False)

    __table_args__ = (
        UniqueConstraint("screen_id", "label", name="uq_screen_row_label"),
        CheckConstraint(
            "seat_count > 0", name="ck_seat_count_positive"
        ),
        CheckConstraint(
            "price_cents >= 0", name="ck_price_cents_non_negative"
        ),
    )


class Seat(Base):
    __tablename__ = "seats"

    id = Column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    row_id = Column(
        sa.Uuid, ForeignKey("screen_rows.id"), nullable=False
    )
    number = Column(Integer, nullable=False)
    code = Column(String, nullable=False)

    __table_args__ = (
        UniqueConstraint("row_id", "number", name="uq_seat_row_number"),
        UniqueConstraint("row_id", "code", name="uq_seat_row_code"),
    )






class Movie(Base):
    __tablename__ = "movies"

    id = Column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    duration_min = Column(Integer, nullable=False)
    language = Column(String, nullable=False)
    certificate = Column(String, nullable=False)
    release_year = Column(Integer, nullable=False)


class Showtime(Base):
    __tablename__ = "showtimes"

    id = Column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    screen_id = Column(
        sa.Uuid, ForeignKey("screens.id"), nullable=False
    )
    movie_id = Column(
        sa.Uuid, ForeignKey("movies.id"), nullable=False
    )
    starts_at = Column(TZDateTime, nullable=False)
    created_by_partner_id = Column(sa.Uuid, nullable=True)






class Booking(Base):
    __tablename__ = "bookings"

    id = Column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    user_id = Column(
        sa.Uuid, ForeignKey("users.id"), nullable=False
    )
    showtime_id = Column(
        sa.Uuid, ForeignKey("showtimes.id"), nullable=False
    )
    ref_code = Column(String, unique=True, nullable=False)
    status = Column(
        String, nullable=False, server_default=sa.text("'PENDING'")
    )
    idempotency_key = Column(String, nullable=True)
    created_at = Column(
        TZDateTime,
        nullable=False,
        default=utcnow,
        server_default=sa.text("CURRENT_TIMESTAMP"),
    )

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "idempotency_key",
            name="uq_booking_user_idempotency",
        ),
    )


class BookingSeat(Base):
    __tablename__ = "booking_seats"

    booking_id = Column(
        sa.Uuid,
        ForeignKey("bookings.id", ondelete="CASCADE"),
        primary_key=True,
    )
    seat_id = Column(
        sa.Uuid, ForeignKey("seats.id"), primary_key=True
    )
    showtime_id = Column(
        sa.Uuid, ForeignKey("showtimes.id"), nullable=False
    )
    price_cents = Column(Integer, nullable=False)

    __table_args__ = (
        Index(
            "ux_showtime_seat",
            "showtime_id",
            "seat_id",
            unique=True,
        ),
    )