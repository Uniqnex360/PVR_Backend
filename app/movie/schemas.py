"""Pydantic request / response schemas for the Movie and Booking module."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Movie / Showtime Responses
# ---------------------------------------------------------------------------

class SeatResponse(BaseModel):
    id: UUID
    code: str
    number: int
    price_cents: int
    status: str  # "AVAILABLE" | "BOOKED"


class RowResponse(BaseModel):
    label: str
    price_cents: int
    seats: list[SeatResponse]


class SeatMapResponse(BaseModel):
    showtime_id: UUID
    movie_title: str
    screen_name: str
    cinema_name: str
    starts_at: datetime
    rows: list[RowResponse]


class ShowtimeResponse(BaseModel):
    id: UUID
    screen_name: str
    cinema_name: str
    movie_title: str
    language: str
    certificate: str
    duration_min: int
    starts_at: datetime


# ---------------------------------------------------------------------------
# Booking Requests / Responses
# ---------------------------------------------------------------------------

class CreateBookingRequest(BaseModel):
    showtime_id: UUID
    seat_ids: list[UUID] = Field(min_length=1, max_length=10)
    idempotency_key: str | None = Field(default=None, max_length=128)


class BookingSeatResponse(BaseModel):
    seat_id: UUID
    code: str
    price_cents: int


class BookingResponse(BaseModel):
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
    seats: list[BookingSeatResponse]
    total_price_cents: int
    barcode: str | None = None
    booking_id: UUID | None = None


# ---------------------------------------------------------------------------
# Hold Requests / Responses
# ---------------------------------------------------------------------------

class CreateHoldRequest(BaseModel):
    showtime_id: UUID
    seat_ids: list[UUID] = Field(min_length=1)
    idempotency_key: str = Field(min_length=1, max_length=128)
    end_user_ref: str | None = Field(default=None, max_length=128)


class HoldSeatResponse(BaseModel):
    seat_id: UUID
    code: str
    price_cents: int


class HoldResponse(BaseModel):
    hold_id: UUID
    expires_at: datetime
    seats: list[HoldSeatResponse]
    total: int
    currency: str


class HoldDetailResponse(BaseModel):
    hold_id: UUID
    showtime_id: UUID
    status: str
    expires_at: datetime
    quote_total: int
    currency: str
    seats: list[HoldSeatResponse]
    created_at: datetime
    updated_at: datetime


class CommitHoldRequest(BaseModel):
    payment_ref: str | None = None


# ---------------------------------------------------------------------------
# Public Ticket Response
# ---------------------------------------------------------------------------

class TicketResponse(BaseModel):
    ref_code: str
    status: str
    movie_title: str
    screen_name: str
    cinema_name: str
    starts_at: datetime
    created_at: datetime
    seats: list[BookingSeatResponse]
    total_price_cents: int