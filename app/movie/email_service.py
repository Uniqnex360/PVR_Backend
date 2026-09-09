

from __future__ import annotations

import logging
from app.movie.interfaces import BookingDTO, IEmailService

logger = logging.getLogger(__name__)


class ConsoleEmailService(IEmailService):
  

    def __init__(self, web_base_url: str = "http://localhost:5173") -> None:
        self.web_base_url = web_base_url
        self.sent_emails: list[dict] = []

    async def send_booking_confirmation(
        self, to_email: str, booking: BookingDTO
    ) -> None:
        ticket_url = f"{self.web_base_url}/ticket?ref={booking.ref_code}"
        seat_codes = ", ".join(s.code for s in booking.seats)

        email_payload = {
            "to": to_email,
            "subject": f"Your Booking Confirmation: {booking.ref_code}",
            "ref_code": booking.ref_code,
            "movie": booking.movie_title,
            "screen": booking.screen_name,
            "cinema": booking.cinema_name,
            "seats": seat_codes,
            "ticket_url": ticket_url,
            "total_price_cents": booking.total_price_cents,
        }

        self.sent_emails.append(email_payload)

        print(f"\n--- [EMAIL SENT] to: {to_email} ---")
        print(f"Subject: Your PVR Ticket ({booking.ref_code})")
        print(f"Movie: {booking.movie_title} @ {booking.cinema_name} ({booking.screen_name})")
        print(f"Seats: {seat_codes} | Total: ₹{booking.total_price_cents / 100:.2f}")
        print(f"Ticket Link: {ticket_url}")
        print("----------------------------------------\n")