"""
Movie & Booking Service — pure domain logic.

Boundary Contract Checklist:
- ZERO imports from fastapi or starlette
- ZERO imports from schemas.py, exceptions.py, models.py, repository.py
- Imports ONLY from interfaces.py and app.shared
- Raises ONLY domain exceptions
"""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID
from zoneinfo import ZoneInfo

from app.movie.interfaces import (
    BookingDTO,
    IEmailService,
    IMovieRepository,
    InvalidSeatSelectionError,
    SeatMapDTO,
    ShowtimeNotFoundError,
    ShowtimeSummaryDTO,
    TicketNotFoundError,
)


class MovieService:
    def __init__(
        self,
        movie_repo: IMovieRepository,
        email_service: IEmailService | None = None,
    ) -> None:
        self._repo = movie_repo
        self._email_service = email_service

    async def get_showtimes(
        self, target_date: date | None = None
    ) -> list[ShowtimeSummaryDTO]:
        if target_date is None:
            target_date = datetime.now(ZoneInfo("Asia/Kolkata")).date()

        return await self._repo.get_showtimes_by_date(target_date)

    async def get_seat_map(self, showtime_id: UUID) -> SeatMapDTO:
        seat_map = await self._repo.get_seat_map(showtime_id)
        if seat_map is None:
            raise ShowtimeNotFoundError(
                f"Showtime '{showtime_id}' does not exist"
            )
        return seat_map

    async def book_seats(
        self,
        *,
        user_id: UUID,
        user_email: str,
        showtime_id: UUID,
        seat_ids: list[UUID],
        idempotency_key: str | None = None,
    ) -> BookingDTO:
        if not seat_ids:
            raise InvalidSeatSelectionError("Must select at least 1 seat")
        if len(seat_ids) > 10:
            raise InvalidSeatSelectionError("Cannot book more than 10 seats")

        # 1. Atomic claim & commit in the database
        booking = await self._repo.create_booking(
            user_id=user_id,
            showtime_id=showtime_id,
            seat_ids=seat_ids,
            idempotency_key=idempotency_key,
        )

        # 2. Trigger email confirmation POST-COMMIT
        if self._email_service:
            await self._email_service.send_booking_confirmation(
                to_email=user_email, booking=booking
            )

        return booking

    async def get_my_bookings(self, user_id: UUID) -> list[BookingDTO]:
        return await self._repo.get_user_bookings(user_id)

    async def cancel_booking(
        self, user_id: UUID, booking_id: UUID
    ) -> BookingDTO:
        return await self._repo.cancel_booking(
            user_id=user_id, booking_id=booking_id
        )

    async def get_ticket(self, ref_code: str) -> BookingDTO:
        booking = await self._repo.get_booking_by_ref(ref_code)
        if booking is None:
            raise TicketNotFoundError(f"Ticket '{ref_code}' not found")
        return booking