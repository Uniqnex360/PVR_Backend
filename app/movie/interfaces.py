"""
Ports, domain exceptions, and value objects for the Movie and Booking module.

Rule: services.py imports ONLY from here and app.shared.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass
from datetime import date, datetime
from typing import Protocol, runtime_checkable
from uuid import UUID

from app.shared.domain_exceptions import (
    ConflictError,
    DomainError,
    NotFoundError,
)


# ---------------------------------------------------------------------------
# Enums & Value Objects / DTOs
# ---------------------------------------------------------------------------

class SeatStatus(str, enum.Enum):
    AVAILABLE = "AVAILABLE"
    BOOKED = "BOOKED"


@dataclass(frozen=True, slots=True)
class SeatProjectionDTO:
    id: UUID
    row_label: str
    number: int
    code: str
    price_cents: int
    status: SeatStatus


@dataclass(frozen=True, slots=True)
class RowProjectionDTO:
    label: str
    price_cents: int
    seats: list[SeatProjectionDTO]


@dataclass(frozen=True, slots=True)
class SeatMapDTO:
    showtime_id: UUID
    movie_title: str
    screen_name: str
    cinema_name: str
    starts_at: datetime
    rows: list[RowProjectionDTO]


@dataclass(frozen=True, slots=True)
class ShowtimeSummaryDTO:
    id: UUID
    screen_name: str
    cinema_name: str
    movie_title: str
    language: str
    certificate: str
    duration_min: int
    starts_at: datetime


@dataclass(frozen=True, slots=True)
class BookingSeatDTO:
    seat_id: UUID
    code: str
    price_cents: int


@dataclass(frozen=True, slots=True)
class BookingDTO:
    id: UUID
    user_id: UUID
    showtime_id: UUID
    movie_title: str
    screen_name: str
    cinema_name: str
    starts_at: datetime
    ref_code: str
    status: str
    created_at: datetime
    seats: list[BookingSeatDTO]
    total_price_cents: int


# ---------------------------------------------------------------------------
# Domain Exceptions
# ---------------------------------------------------------------------------

class ShowtimeNotFoundError(NotFoundError):
    """Showtime does not exist."""


class SeatAlreadyBookedError(ConflictError):
    """One or more requested seats are already booked for this showtime."""


class InvalidSeatSelectionError(DomainError):
    """Invalid seat count, empty selection, or seats not found on screen."""


class BookingNotFoundError(NotFoundError):
    """Booking does not exist."""


class TicketNotFoundError(NotFoundError):
    """Ticket with the given ref_code does not exist."""


class BookingOwnershipError(DomainError):
    """Caller is not authorized to access or modify this booking."""


class BookingAlreadyCancelledError(DomainError):
    """Booking is already cancelled."""


# ---------------------------------------------------------------------------
# Repository Port
# ---------------------------------------------------------------------------

@runtime_checkable
class IMovieRepository(Protocol):
    async def get_showtimes_by_date(
        self, target_date: date
    ) -> list[ShowtimeSummaryDTO]: ...

    async def get_seat_map(
        self, showtime_id: UUID
    ) -> SeatMapDTO | None: ...

    async def create_booking(
        self,
        *,
        user_id: UUID,
        showtime_id: UUID,
        seat_ids: list[UUID],
        idempotency_key: str | None = None,
    ) -> BookingDTO: ...

    async def get_booking_by_id(
        self, booking_id: UUID
    ) -> BookingDTO | None: ...

    async def get_booking_by_ref(
        self, ref_code: str
    ) -> BookingDTO | None: ...

    async def get_user_bookings(
        self, user_id: UUID
    ) -> list[BookingDTO]: ...

    async def cancel_booking(
        self, *, user_id: UUID, booking_id: UUID
    ) -> BookingDTO: ...


# ---------------------------------------------------------------------------
# Email Service Port
# ---------------------------------------------------------------------------

@runtime_checkable
class IEmailService(Protocol):
    async def send_booking_confirmation(
        self, to_email: str, booking: BookingDTO
    ) -> None: ...