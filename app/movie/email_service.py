import logging
import httpx  # Run: pip install httpx
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
        # Resend prefers "Name <email@domain.com>" format
        self.from_sender = f"{from_name} <{from_email}>"
        self.frontend_url = frontend_url
        self.api_url = "https://api.resend.com/emails"

    

    async def send_booking_confirmation(self, to_email: str, booking: BookingDTO) -> None:
        if not self.api_key:
            logger.warning("Resend API key missing.")
            return

        ticket_url = f"{self.frontend_url}/ticket?ref={booking.ref_code}"
        
        # Build the payload using your HTML
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
