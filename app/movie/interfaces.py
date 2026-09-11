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


class HoldStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    COMMITTED = "COMMITTED"
    EXPIRED = "EXPIRED"
    RELEASED = "RELEASED"


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
    barcode: str | None = None


@dataclass(frozen=True, slots=True)
class HoldSeatDTO:
    seat_id: UUID
    code: str
    price_cents: int


@dataclass(frozen=True, slots=True)
class HoldDTO:
    id: UUID
    showtime_id: UUID
    partner_id: UUID
    end_user_ref: str | None
    status: str
    idempotency_key: str
    quote_total: int
    currency: str
    expires_at: datetime
    created_at: datetime
    updated_at: datetime
    seats: list[HoldSeatDTO]


# ---------------------------------------------------------------------------
# Domain Exceptions
# ---------------------------------------------------------------------------

class ShowtimeNotFoundError(NotFoundError):
    """Showtime does not exist."""


class SeatAlreadyBookedError(ConflictError):
    """One or more requested seats are already booked for this showtime."""


class SeatUnavailableError(ConflictError):
    """One or more requested seats are unavailable (booked or active hold)."""

    def __init__(self, unavailable_seat_ids: list[UUID]) -> None:
        super().__init__(
            f"Seats unavailable: {', '.join(str(s) for s in unavailable_seat_ids)}"
        )
        self.unavailable_seat_ids = unavailable_seat_ids


class HoldNotFoundError(NotFoundError):
    """Hold does not exist."""


class HoldExpiredError(DomainError):
    """Hold is expired or released."""


class HoldAlreadyCommittedError(ConflictError):
    """Hold was already committed into a booking."""

    def __init__(self, booking: BookingDTO) -> None:
        super().__init__("Hold already committed")
        self.booking = booking


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

    async def create_hold(
        self,
        *,
        partner_id: UUID,
        showtime_id: UUID,
        seat_ids: list[UUID],
        idempotency_key: str,
        end_user_ref: str | None = None,
        ttl_seconds: int = 600,
    ) -> HoldDTO: ...

    async def get_hold_by_id(
        self, hold_id: UUID
    ) -> HoldDTO | None: ...

    async def commit_hold(
        self, *, hold_id: UUID, payment_ref: str | None = None
    ) -> BookingDTO: ...

    async def release_hold(
        self, hold_id: UUID
    ) -> None: ...

    async def release_expired_holds(
        self
    ) -> list[UUID]: ...


# ---------------------------------------------------------------------------
# Email Service Port
# ---------------------------------------------------------------------------

@runtime_checkable
class IEmailService(Protocol):
    async def send_booking_confirmation(
        self, to_email: str, booking: BookingDTO
    ) -> None: ...