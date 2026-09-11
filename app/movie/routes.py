"""
FastAPI routes for Movie, Showtimes, Bookings, Holds, and Public Tickets.
Mounted with prefix /v1 via app.include_router(movie_router, prefix="/v1").
"""

from __future__ import annotations

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status

from app.auth.dependencies import get_current_user
from app.auth.interfaces import UserDTO
from app.movie.dependencies import get_movie_service
from app.movie.exceptions import (
    BookingAlreadyCancelledHTTPError,
    BookingForbiddenHTTPError,
    BookingNotFoundHTTPError,
    HoldAlreadyCommittedHTTPError,
    HoldExpiredHTTPError,
    HoldNotFoundHTTPError,
    InvalidSeatSelectionHTTPError,
    SeatConflictHTTPError,
    SeatUnavailableHTTPError,
    ShowtimeNotFoundHTTPError,
    TicketNotFoundHTTPError,
)
from app.movie.interfaces import (
    BookingAlreadyCancelledError,
    BookingDTO,
    BookingNotFoundError,
    BookingOwnershipError,
    HoldAlreadyCommittedError,
    HoldDTO,
    HoldExpiredError,
    HoldNotFoundError,
    InvalidSeatSelectionError,
    SeatAlreadyBookedError,
    SeatUnavailableError,
    ShowtimeNotFoundError,
    TicketNotFoundError,
)
from app.movie.schemas import (
    BookingResponse,
    BookingSeatResponse,
    CommitHoldRequest,
    CreateBookingRequest,
    CreateHoldRequest,
    HoldDetailResponse,
    HoldResponse,
    HoldSeatResponse,
    RowResponse,
    SeatMapResponse,
    SeatResponse,
    ShowtimeResponse,
    TicketResponse,
)
from app.movie.services import MovieService

movie_router = APIRouter(tags=["movie"])


def _dto_to_booking_response(dto: BookingDTO) -> BookingResponse:
    return BookingResponse(
        id=dto.id,
        booking_id=dto.id,
        user_id=dto.user_id,
        showtime_id=dto.showtime_id,
        movie_title=dto.movie_title,
        screen_name=dto.screen_name,
        cinema_name=dto.cinema_name,
        starts_at=dto.starts_at,
        ref_code=dto.ref_code,
        status=dto.status,
        created_at=dto.created_at,
        seats=[
            BookingSeatResponse(
                seat_id=s.seat_id,
                code=s.code,
                price_cents=s.price_cents,
            )
            for s in dto.seats
        ],
        total_price_cents=dto.total_price_cents,
        barcode=dto.barcode or f"BARCODE-{dto.ref_code}",
    )


def _dto_to_hold_response(dto: HoldDTO) -> HoldResponse:
    return HoldResponse(
        hold_id=dto.id,
        expires_at=dto.expires_at,
        seats=[
            HoldSeatResponse(
                seat_id=s.seat_id,
                code=s.code,
                price_cents=s.price_cents,
            )
            for s in dto.seats
        ],
        total=dto.quote_total,
        currency=dto.currency,
    )


# ---------------------------------------------------------------------------
# Showtimes & Seat Map
# ---------------------------------------------------------------------------

@movie_router.get("/showtimes", response_model=list[ShowtimeResponse])
async def list_showtimes(
    date: date | None = Query(None, description="Filter showtimes by date (YYYY-MM-DD)"),
    movie_service: MovieService = Depends(get_movie_service),
):
    dtos = await movie_service.get_showtimes(date)
    return [
        ShowtimeResponse(
            id=st.id,
            screen_name=st.screen_name,
            cinema_name=st.cinema_name,
            movie_title=st.movie_title,
            language=st.language,
            certificate=st.certificate,
            duration_min=st.duration_min,
            starts_at=st.starts_at,
        )
        for st in dtos
    ]


@movie_router.get("/showtimes/{showtime_id}/seats", response_model=SeatMapResponse)
async def get_seat_map(
    showtime_id: UUID,
    movie_service: MovieService = Depends(get_movie_service),
):
    try:
        dto = await movie_service.get_seat_map(showtime_id)
        return SeatMapResponse(
            showtime_id=dto.showtime_id,
            movie_title=dto.movie_title,
            screen_name=dto.screen_name,
            cinema_name=dto.cinema_name,
            starts_at=dto.starts_at,
            rows=[
                RowResponse(
                    label=r.label,
                    price_cents=r.price_cents,
                    seats=[
                        SeatResponse(
                            id=s.id,
                            code=s.code,
                            number=s.number,
                            price_cents=s.price_cents,
                            status=s.status.value,
                        )
                        for s in r.seats
                    ],
                )
                for r in dto.rows
            ],
        )
    except ShowtimeNotFoundError as exc:
        raise ShowtimeNotFoundHTTPError(str(exc))


# ---------------------------------------------------------------------------
# Holds Endpoints
# ---------------------------------------------------------------------------

@movie_router.post(
    "/holds",
    response_model=HoldResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_hold(
    body: CreateHoldRequest,
    current_user: UserDTO = Depends(get_current_user),
    movie_service: MovieService = Depends(get_movie_service),
):
    try:
        hold = await movie_service.create_hold(
            partner_id=current_user.id,
            showtime_id=body.showtime_id,
            seat_ids=body.seat_ids,
            idempotency_key=body.idempotency_key,
            end_user_ref=body.end_user_ref,
        )
        return _dto_to_hold_response(hold)
    except SeatUnavailableError as exc:
        raise SeatUnavailableHTTPError(exc.unavailable_seat_ids)
    except ShowtimeNotFoundError as exc:
        raise ShowtimeNotFoundHTTPError(str(exc))
    except InvalidSeatSelectionError as exc:
        raise InvalidSeatSelectionHTTPError(str(exc))


@movie_router.post(
    "/holds/{hold_id}/commit",
    response_model=BookingResponse,
    status_code=status.HTTP_200_OK,
)
async def commit_hold(
    hold_id: UUID,
    body: CommitHoldRequest | None = None,
    current_user: UserDTO = Depends(get_current_user),
    movie_service: MovieService = Depends(get_movie_service),
):
    payment_ref = body.payment_ref if body else None
    try:
        booking = await movie_service.commit_hold(
            hold_id=hold_id, payment_ref=payment_ref
        )
        return _dto_to_booking_response(booking)
    except HoldAlreadyCommittedError as exc:
        raise HoldAlreadyCommittedHTTPError(_dto_to_booking_response(exc.booking).model_dump(mode="json"))
    except HoldExpiredError as exc:
        raise HoldExpiredHTTPError(str(exc))
    except HoldNotFoundError as exc:
        raise HoldNotFoundHTTPError(str(exc))
    except SeatAlreadyBookedError as exc:
        raise SeatConflictHTTPError(str(exc))


@movie_router.delete(
    "/holds/{hold_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_hold(
    hold_id: UUID,
    current_user: UserDTO = Depends(get_current_user),
    movie_service: MovieService = Depends(get_movie_service),
):
    await movie_service.release_hold(hold_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@movie_router.get(
    "/holds/{hold_id}",
    response_model=HoldDetailResponse,
)
async def get_hold(
    hold_id: UUID,
    current_user: UserDTO = Depends(get_current_user),
    movie_service: MovieService = Depends(get_movie_service),
):
    try:
        dto = await movie_service.get_hold(hold_id)
        return HoldDetailResponse(
            hold_id=dto.id,
            showtime_id=dto.showtime_id,
            status=dto.status,
            expires_at=dto.expires_at,
            quote_total=dto.quote_total,
            currency=dto.currency,
            seats=[
                HoldSeatResponse(
                    seat_id=s.seat_id,
                    code=s.code,
                    price_cents=s.price_cents,
                )
                for s in dto.seats
            ],
            created_at=dto.created_at,
            updated_at=dto.updated_at,
        )
    except HoldNotFoundError as exc:
        raise HoldNotFoundHTTPError(str(exc))


# ---------------------------------------------------------------------------
# Bookings Write Operations
# ---------------------------------------------------------------------------

@movie_router.post(
    "/bookings",
    response_model=BookingResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_booking(
    body: CreateBookingRequest,
    current_user: UserDTO = Depends(get_current_user),
    movie_service: MovieService = Depends(get_movie_service),
):
    try:
        booking = await movie_service.book_seats(
            user_id=current_user.id,
            user_email=current_user.email,
            showtime_id=body.showtime_id,
            seat_ids=body.seat_ids,
            idempotency_key=body.idempotency_key,
        )
        return _dto_to_booking_response(booking)
    except SeatAlreadyBookedError as exc:
        raise SeatConflictHTTPError(str(exc))
    except ShowtimeNotFoundError as exc:
        raise ShowtimeNotFoundHTTPError(str(exc))
    except InvalidSeatSelectionError as exc:
        raise InvalidSeatSelectionHTTPError(str(exc))


@movie_router.get("/bookings/me", response_model=list[BookingResponse])
async def get_my_bookings(
    current_user: UserDTO = Depends(get_current_user),
    movie_service: MovieService = Depends(get_movie_service),
):
    bookings = await movie_service.get_my_bookings(current_user.id)
    return [_dto_to_booking_response(b) for b in bookings]


@movie_router.post(
    "/bookings/{booking_id}/cancel",
    response_model=BookingResponse,
)
async def cancel_booking(
    booking_id: UUID,
    current_user: UserDTO = Depends(get_current_user),
    movie_service: MovieService = Depends(get_movie_service),
):
    try:
        cancelled = await movie_service.cancel_booking(
            user_id=current_user.id, booking_id=booking_id
        )
        return _dto_to_booking_response(cancelled)
    except BookingNotFoundError as exc:
        raise BookingNotFoundHTTPError(str(exc))
    except BookingOwnershipError as exc:
        raise BookingForbiddenHTTPError(str(exc))
    except BookingAlreadyCancelledError as exc:
        raise BookingAlreadyCancelledHTTPError(str(exc))


# ---------------------------------------------------------------------------
# Public Ticket Page (Unauthenticated by design)
# ---------------------------------------------------------------------------

@movie_router.get("/tickets/{ref_code}", response_model=TicketResponse)
async def get_ticket_by_ref(
    ref_code: str,
    movie_service: MovieService = Depends(get_movie_service),
):
    try:
        dto = await movie_service.get_ticket(ref_code)
        return TicketResponse(
            ref_code=dto.ref_code,
            status=dto.status,
            movie_title=dto.movie_title,
            screen_name=dto.screen_name,
            cinema_name=dto.cinema_name,
            starts_at=dto.starts_at,
            created_at=dto.created_at,
            seats=[
                BookingSeatResponse(
                    seat_id=s.seat_id,
                    code=s.code,
                    price_cents=s.price_cents,
                )
                for s in dto.seats
            ],
            total_price_cents=dto.total_price_cents,
        )
    except TicketNotFoundError as exc:
        raise TicketNotFoundHTTPError(str(exc))