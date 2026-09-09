
from fastapi import HTTPException, status


class ShowtimeNotFoundHTTPError(HTTPException):
    def __init__(self, detail: str = "Showtime not found"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class SeatConflictHTTPError(HTTPException):
    def __init__(self, detail: str = "One or more selected seats are already booked"):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)


class InvalidSeatSelectionHTTPError(HTTPException):
    def __init__(self, detail: str = "Invalid seat selection"):
        super().__init__(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail)


class BookingNotFoundHTTPError(HTTPException):
    def __init__(self, detail: str = "Booking not found"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class TicketNotFoundHTTPError(HTTPException):
    def __init__(self, detail: str = "Ticket not found"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class BookingForbiddenHTTPError(HTTPException):
    def __init__(self, detail: str = "Not authorized to access this booking"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class BookingAlreadyCancelledHTTPError(HTTPException):
    def __init__(self, detail: str = "Booking is already cancelled"):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)