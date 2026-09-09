"""
SQLAlchemy repository for Movie, Showtime, and Booking write operations.
"""

from __future__ import annotations

import uuid
from datetime import date
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.movie.interfaces import (
    BookingAlreadyCancelledError,
    BookingDTO,
    BookingNotFoundError,
    BookingOwnershipError,
    BookingSeatDTO,
    InvalidSeatSelectionError,
    RowProjectionDTO,
    SeatAlreadyBookedError,
    SeatMapDTO,
    SeatProjectionDTO,
    SeatStatus,
    ShowtimeNotFoundError,
    ShowtimeSummaryDTO,
)
from app.movie.models import (
    Booking,
    BookingSeat,
    BookingStatus,
    Cinema,
    Movie,
    Screen,
    ScreenRow,
    Seat,
    Showtime,
)


class MovieRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_showtimes_by_date(
        self, target_date: date
    ) -> list[ShowtimeSummaryDTO]:
        stmt = (
            select(Showtime, Screen, Cinema, Movie)
            .join(Screen, Showtime.screen_id == Screen.id)
            .join(Cinema, Screen.cinema_id == Cinema.id)
            .join(Movie, Showtime.movie_id == Movie.id)
            .order_by(Showtime.starts_at.asc())
        )
        result = await self._session.execute(stmt)
        rows = result.all()

        showtimes: list[ShowtimeSummaryDTO] = []
        for st, screen, cinema, movie in rows:
            cinema_tz = ZoneInfo(cinema.timezone)
            st_date_local = st.starts_at.astimezone(cinema_tz).date()

            if st_date_local == target_date:
                showtimes.append(
                    ShowtimeSummaryDTO(
                        id=st.id,
                        screen_name=screen.name,
                        cinema_name=cinema.name,
                        movie_title=movie.title,
                        language=movie.language,
                        certificate=movie.certificate,
                        duration_min=movie.duration_min,
                        starts_at=st.starts_at,
                    )
                )

        return showtimes

    async def get_seat_map(self, showtime_id: UUID) -> SeatMapDTO | None:
        st_stmt = (
            select(Showtime, Screen, Cinema, Movie)
            .join(Screen, Showtime.screen_id == Screen.id)
            .join(Cinema, Screen.cinema_id == Cinema.id)
            .join(Movie, Showtime.movie_id == Movie.id)
            .where(Showtime.id == showtime_id)
        )
        st_res = await self._session.execute(st_stmt)
        st_row = st_res.first()
        if not st_row:
            return None

        showtime, screen, cinema, movie = st_row

        row_stmt = (
            select(ScreenRow)
            .where(ScreenRow.screen_id == screen.id)
            .order_by(ScreenRow.label.asc())
        )
        rows_res = await self._session.execute(row_stmt)
        screen_rows = rows_res.scalars().all()

        row_ids = [r.id for r in screen_rows]
        seat_stmt = (
            select(Seat)
            .where(Seat.row_id.in_(row_ids))
            .order_by(Seat.number.asc())
        )
        seats_res = await self._session.execute(seat_stmt)
        all_seats = seats_res.scalars().all()

        seats_by_row: dict[UUID, list[Seat]] = {r.id: [] for r in screen_rows}
        for s in all_seats:
            if s.row_id in seats_by_row:
                seats_by_row[s.row_id].append(s)

        booked_stmt = (
            select(BookingSeat.seat_id)
            .join(Booking, BookingSeat.booking_id == Booking.id)
            .where(
                BookingSeat.showtime_id == showtime_id,
                Booking.status != BookingStatus.CANCELLED.value,
            )
        )
        booked_res = await self._session.execute(booked_stmt)
        booked_seat_ids = set(booked_res.scalars().all())

        row_dtos: list[RowProjectionDTO] = []
        for r in screen_rows:
            seat_dtos: list[SeatProjectionDTO] = []
            for s in seats_by_row.get(r.id, []):
                status = (
                    SeatStatus.BOOKED
                    if s.id in booked_seat_ids
                    else SeatStatus.AVAILABLE
                )
                seat_dtos.append(
                    SeatProjectionDTO(
                        id=s.id,
                        row_label=r.label,
                        number=s.number,
                        code=s.code,
                        price_cents=r.price_cents,
                        status=status,
                    )
                )

            row_dtos.append(
                RowProjectionDTO(
                    label=r.label,
                    price_cents=r.price_cents,
                    seats=seat_dtos,
                )
            )

        return SeatMapDTO(
            showtime_id=showtime.id,
            movie_title=movie.title,
            screen_name=screen.name,
            cinema_name=cinema.name,
            starts_at=showtime.starts_at,
            rows=row_dtos,
        )

    # -----------------------------------------------------------------------
    # Booking Lookups & Write Operations
    # -----------------------------------------------------------------------

    def _build_booking_dto(
        self,
        booking: Booking,
        showtime: Showtime,
        screen: Screen,
        cinema: Cinema,
        movie: Movie,
        seats_data: list[tuple[BookingSeat, Seat]],
    ) -> BookingDTO:
        seat_dtos = [
            BookingSeatDTO(
                seat_id=s.id,
                code=s.code,
                price_cents=bs.price_cents,
            )
            for bs, s in seats_data
        ]
        total_price = sum(s.price_cents for s in seat_dtos)

        return BookingDTO(
            id=booking.id,
            user_id=booking.user_id,
            showtime_id=showtime.id,
            movie_title=movie.title,
            screen_name=screen.name,
            cinema_name=cinema.name,
            starts_at=showtime.starts_at,
            ref_code=booking.ref_code,
            status=booking.status,
            created_at=booking.created_at,
            seats=seat_dtos,
            total_price_cents=total_price,
        )

    async def get_booking_by_id(self, booking_id: UUID) -> BookingDTO | None:
        stmt = (
            select(Booking, Showtime, Screen, Cinema, Movie)
            .join(Showtime, Booking.showtime_id == Showtime.id)
            .join(Screen, Showtime.screen_id == Screen.id)
            .join(Cinema, Screen.cinema_id == Cinema.id)
            .join(Movie, Showtime.movie_id == Movie.id)
            .where(Booking.id == booking_id)
        )
        res = await self._session.execute(stmt)
        row = res.first()
        if not row:
            return None

        booking, showtime, screen, cinema, movie = row

        bs_stmt = (
            select(BookingSeat, Seat)
            .join(Seat, BookingSeat.seat_id == Seat.id)
            .where(BookingSeat.booking_id == booking.id)
        )
        bs_res = await self._session.execute(bs_stmt)
        seats_data = bs_res.all()

        return self._build_booking_dto(
            booking, showtime, screen, cinema, movie, seats_data
        )

    async def get_booking_by_ref(self, ref_code: str) -> BookingDTO | None:
        stmt = (
            select(Booking, Showtime, Screen, Cinema, Movie)
            .join(Showtime, Booking.showtime_id == Showtime.id)
            .join(Screen, Showtime.screen_id == Screen.id)
            .join(Cinema, Screen.cinema_id == Cinema.id)
            .join(Movie, Showtime.movie_id == Movie.id)
            .where(Booking.ref_code == ref_code.strip().upper())
        )
        res = await self._session.execute(stmt)
        row = res.first()
        if not row:
            return None

        booking, showtime, screen, cinema, movie = row

        bs_stmt = (
            select(BookingSeat, Seat)
            .join(Seat, BookingSeat.seat_id == Seat.id)
            .where(BookingSeat.booking_id == booking.id)
        )
        bs_res = await self._session.execute(bs_stmt)
        seats_data = bs_res.all()

        return self._build_booking_dto(
            booking, showtime, screen, cinema, movie, seats_data
        )

    async def get_booking_by_idempotency(
        self, user_id: UUID, idempotency_key: str
    ) -> BookingDTO | None:
        stmt = select(Booking.id).where(
            Booking.user_id == user_id,
            Booking.idempotency_key == idempotency_key,
        )
        res = await self._session.execute(stmt)
        b_id = res.scalar_one_or_none()
        if not b_id:
            return None
        return await self.get_booking_by_id(b_id)

    async def create_booking(
        self,
        *,
        user_id: UUID,
        showtime_id: UUID,
        seat_ids: list[UUID],
        idempotency_key: str | None = None,
    ) -> BookingDTO:
        # 1. Idempotency Check
        if idempotency_key:
            existing = await self.get_booking_by_idempotency(
                user_id, idempotency_key
            )
            if existing:
                return existing

        # 2. Verify showtime exists
        st_stmt = (
            select(Showtime, Screen)
            .join(Screen, Showtime.screen_id == Screen.id)
            .where(Showtime.id == showtime_id)
        )
        st_res = await self._session.execute(st_stmt)
        st_row = st_res.first()
        if not st_row:
            raise ShowtimeNotFoundError(
                f"Showtime '{showtime_id}' does not exist"
            )
        showtime, screen = st_row

        # 3. Fetch requested seats and their row price snapshot
        seat_stmt = (
            select(Seat, ScreenRow)
            .join(ScreenRow, Seat.row_id == ScreenRow.id)
            .where(
                Seat.id.in_(seat_ids),
                ScreenRow.screen_id == screen.id,
            )
        )
        seat_res = await self._session.execute(seat_stmt)
        seats_with_rows = seat_res.all()

        if len(seats_with_rows) != len(set(seat_ids)):
            raise InvalidSeatSelectionError(
                "One or more selected seats do not exist on this screen"
            )

        # 4. Create Booking
        ref_code = f"PVR-{uuid.uuid4().hex[:8].upper()}"
        booking = Booking(
            id=uuid.uuid4(),
            user_id=user_id,
            showtime_id=showtime_id,
            ref_code=ref_code,
            status=BookingStatus.CONFIRMED.value,
            idempotency_key=idempotency_key,
        )

        try:
            self._session.add(booking)
            await self._session.flush()

            # 5. Insert Booking Seats (denormalized showtime_id triggers ux_showtime_seat)
            for seat, row in seats_with_rows:
                bs = BookingSeat(
                    booking_id=booking.id,
                    seat_id=seat.id,
                    showtime_id=showtime_id,
                    price_cents=row.price_cents,
                )
                self._session.add(bs)

            await self._session.commit()
        except IntegrityError as exc:
            await self._session.rollback()
            # If idempotency race:
            if idempotency_key:
                existing = await self.get_booking_by_idempotency(
                    user_id, idempotency_key
                )
                if existing:
                    return existing

            # Concurrency race on ux_showtime_seat
            raise SeatAlreadyBookedError(
                "One or more selected seats are already booked"
            ) from exc

        booking_dto = await self.get_booking_by_id(booking.id)
        if not booking_dto:
            raise BookingNotFoundError("Failed to retrieve created booking")
        return booking_dto

    async def get_user_bookings(self, user_id: UUID) -> list[BookingDTO]:
        stmt = (
            select(Booking.id)
            .where(Booking.user_id == user_id)
            .order_by(Booking.created_at.desc())
        )
        res = await self._session.execute(stmt)
        booking_ids = res.scalars().all()

        results: list[BookingDTO] = []
        for b_id in booking_ids:
            b_dto = await self.get_booking_by_id(b_id)
            if b_dto:
                results.append(b_dto)
        return results

    async def cancel_booking(
        self, *, user_id: UUID, booking_id: UUID
    ) -> BookingDTO:
        stmt = select(Booking).where(Booking.id == booking_id)
        res = await self._session.execute(stmt)
        booking = res.scalar_one_or_none()

        if not booking:
            raise BookingNotFoundError(f"Booking '{booking_id}' not found")

        if booking.user_id != user_id:
            raise BookingOwnershipError("Not authorized to cancel this booking")

        if booking.status == BookingStatus.CANCELLED.value:
            raise BookingAlreadyCancelledError("Booking is already cancelled")

        booking.status = BookingStatus.CANCELLED.value

        # Delete booking_seats so the unique index ux_showtime_seat frees the seats
        del_stmt = delete(BookingSeat).where(
            BookingSeat.booking_id == booking.id
        )
        await self._session.execute(del_stmt)

        await self._session.commit()

        b_dto = await self.get_booking_by_id(booking.id)
        if not b_dto:
            raise BookingNotFoundError("Booking not found after cancellation")
        return b_dto