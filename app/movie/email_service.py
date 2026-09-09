"""
Email notification service implementation (Console & Gmail SMTP).
"""

from __future__ import annotations

import asyncio
import email.utils
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from zoneinfo import ZoneInfo

from app.core.config import settings
from app.movie.interfaces import BookingDTO, IEmailService

logger = logging.getLogger(__name__)


class SMTPEmailService(IEmailService):
    """
    Production SMTP Email Service for Gmail and other standard SMTP providers.
    Uses asyncio.to_thread to prevent blocking the async event loop.
    """

    def __init__(
        self,
        host: str = settings.SMTP_HOST,
        port: int = settings.SMTP_PORT,
        username: str | None = settings.SMTP_USER,
        password: str | None = settings.SMTP_PASSWORD,
        from_name: str = settings.SMTP_FROM_NAME,
        frontend_url: str = settings.FRONTEND_URL,
    ) -> None:
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.from_name = from_name
        self.frontend_url = frontend_url

    def _build_html_email(self, booking: BookingDTO, ticket_url: str) -> str:
        starts_at_ist = booking.starts_at.astimezone(
            ZoneInfo("Asia/Kolkata")
        ).strftime("%A, %d %B %Y at %I:%M %p")
        seat_codes = ", ".join(s.code for s in booking.seats)
        amount_formatted = f"₹{booking.total_price_cents / 100:.2f}"

        return f"""\
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #0a0a0a; color: #f5f5f5; margin: 0; padding: 20px; }}
    .ticket-card {{ max-width: 520px; margin: 0 auto; background: #171717; border-radius: 16px; border: 1px solid #262626; overflow: hidden; }}
    .ticket-header {{ background: linear-gradient(135deg, #f59e0b, #d97706); color: #000; padding: 24px; }}
    .ticket-header h1 {{ margin: 0; font-size: 24px; font-weight: 900; letter-spacing: 1px; }}
    .ticket-ref {{ font-family: monospace; font-size: 14px; font-weight: bold; opacity: 0.9; margin-top: 4px; }}
    .ticket-body {{ padding: 24px; }}
    .movie-title {{ font-size: 22px; font-weight: bold; color: #ffffff; margin: 0 0 4px 0; }}
    .cinema-name {{ color: #a3a3a3; font-size: 14px; margin-bottom: 20px; }}
    .info-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; background: #262626; padding: 16px; border-radius: 12px; margin-bottom: 24px; }}
    .info-label {{ font-size: 11px; text-transform: uppercase; color: #737373; font-weight: bold; }}
    .info-val {{ font-size: 14px; color: #f5f5f5; font-weight: bold; margin-top: 2px; }}
    .btn {{ display: block; text-align: center; background: #f59e0b; color: #000; text-decoration: none; font-weight: bold; padding: 14px; border-radius: 10px; font-size: 14px; }}
    .footer {{ text-align: center; color: #525252; font-size: 12px; margin-top: 20px; }}
  </style>
</head>
<body>
  <div class="ticket-card">
    <div class="ticket-header">
      <h1>PVR CINEMAS</h1>
      <div class="ticket-ref">BOOKING CONFIRMED: {booking.ref_code}</div>
    </div>
    <div class="ticket-body">
      <div class="movie-title">{booking.movie_title}</div>
      <div class="cinema-name">{booking.cinema_name} • {booking.screen_name}</div>
      
      <div class="info-grid">
        <div>
          <div class="info-label">Showtime</div>
          <div class="info-val">{starts_at_ist}</div>
        </div>
        <div>
          <div class="info-label">Seats ({len(booking.seats)})</div>
          <div class="info-val" style="color: #f59e0b;">{seat_codes}</div>
        </div>
        <div>
          <div class="info-label">Total Amount</div>
          <div class="info-val">{amount_formatted}</div>
        </div>
        <div>
          <div class="info-label">Status</div>
          <div class="info-val" style="color: #4ade80;">{booking.status}</div>
        </div>
      </div>

      <a href="{ticket_url}" class="btn">View & Download Ticket</a>
    </div>
  </div>
  <div class="footer">
    Please present the digital ticket at the cinema gate. Enjoy your movie!
  </div>
</body>
</html>
"""

    def _send_sync(self, to_email: str, booking: BookingDTO) -> None:
        if not self.username or not self.password:
            logger.warning(
                "SMTP credentials not configured. Email to %s skipped.", to_email
            )
            return

        ticket_url = f"{self.frontend_url}/ticket?ref={booking.ref_code}"
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"Your Ticket: {booking.movie_title} ({booking.ref_code})"
        msg["From"] = email.utils.formataddr((self.from_name, self.username))
        msg["To"] = to_email

        # 1. Plain text fallback
        plain_text = (
            f"PVR Cinema Booking Confirmation\n"
            f"Ref: {booking.ref_code}\n"
            f"Movie: {booking.movie_title}\n"
            f"Cinema: {booking.cinema_name} ({booking.screen_name})\n"
            f"Seats: {', '.join(s.code for s in booking.seats)}\n"
            f"View your ticket: {ticket_url}\n"
        )
        msg.attach(MIMEText(plain_text, "plain"))

        # 2. HTML template
        html_content = self._build_html_email(booking, ticket_url)
        msg.attach(MIMEText(html_content, "html"))

        try:
            with smtplib.SMTP(self.host, self.port, timeout=10) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.sendmail(self.username, [to_email], msg.as_string())
            logger.info("Confirmation email successfully sent to %s", to_email)
        except Exception as exc:
            logger.error("Failed to send SMTP email to %s: %s", to_email, exc)

    async def send_booking_confirmation(
        self, to_email: str, booking: BookingDTO
    ) -> None:
        # Offload blocking network I/O to worker thread
        await asyncio.to_thread(self._send_sync, to_email, booking)


class ConsoleEmailService(IEmailService):
    """Fallback console email implementation for dev/testing."""

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
        print(f"\n--- [EMAIL CONSOLE FALLBACK] To: {to_email} | Ticket: {ticket_url} ---\n")