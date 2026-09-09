import logging
import httpx  
from zoneinfo import ZoneInfo
from app.core.config import settings
from app.movie.interfaces import BookingDTO, IEmailService

logger = logging.getLogger(__name__)

class ResendEmailService(IEmailService):
    def __init__(
        self,
        api_key: str = settings.RESEND_API_KEY,
        from_email: str = settings.SMTP_USER, 
        from_name: str = settings.SMTP_FROM_NAME,
        frontend_url: str = settings.FRONTEND_URL,
    ) -> None:
        self.api_key = api_key
        
        self.from_sender = f"{from_name} <{from_email}>"
        self.frontend_url = frontend_url
        self.api_url = "https://api.resend.com/emails"

    
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
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: 
        .ticket-card {{ max-width: 520px; margin: 0 auto; background: 
        .ticket-header {{ background: linear-gradient(135deg, 
        .ticket-header h1 {{ margin: 0; font-size: 24px; font-weight: 900; letter-spacing: 1px; }}
        .ticket-ref {{ font-family: monospace; font-size: 14px; font-weight: bold; opacity: 0.9; margin-top: 4px; }}
        .ticket-body {{ padding: 24px; }}
        .movie-title {{ font-size: 22px; font-weight: bold; color: 
        .cinema-name {{ color: 
        .info-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; background: 
        .info-label {{ font-size: 11px; text-transform: uppercase; color: 
        .info-val {{ font-size: 14px; color: 
        .btn {{ display: block; text-align: center; background: 
        .footer {{ text-align: center; color: 
      </style>
    </head>
    <body>
      <div class="ticket-card">
        <div class="ticket-header">
          <h1>CHENNAI CINEMAS</h1>
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
              <div class="info-val" style="color: 
            </div>
            <div>
              <div class="info-label">Total Amount</div>
              <div class="info-val">{amount_formatted}</div>
            </div>
            <div>
              <div class="info-label">Status</div>
              <div class="info-val" style="color: 
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
    async def send_booking_confirmation(self, to_email: str, booking: BookingDTO) -> None:
        if not self.api_key:
            logger.warning("Resend API key missing.")
            return

        ticket_url = f"{self.frontend_url}/ticket?ref={booking.ref_code}"
        
        
        payload = {
            "from": self.from_sender,
            "to": [to_email],
            "subject": f"Your Ticket: {booking.movie_title} ({booking.ref_code})",
            "html": self._build_html_email(booking, ticket_url),
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    self.api_url,
                    json=payload,
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
                response.raise_for_status()
                logger.info("Email sent via Resend to %s", to_email)
            except Exception as e:
                logger.error("Resend API Error: %s", e)

class ConsoleEmailService(IEmailService):
    """Fallback in-memory/console logger for testing."""

    def __init__(self, web_base_url: str = "http://localhost:5173") -> None:
        self.web_base_url = web_base_url
        self.sent_emails: list[dict] = []

    async def send_booking_confirmation(
        self, to_email: str, booking: BookingDTO
    ) -> None:
        ticket_url = f"{self.web_base_url}/ticket?ref={booking.ref_code}"
        self.sent_emails.append({"to": to_email, "ref": booking.ref_code})
        print(f"\n--- [CONSOLE EMAIL] To: {to_email} | Ticket: {ticket_url} ---\n")