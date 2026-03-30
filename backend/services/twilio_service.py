"""
Twilio Service — WhatsApp messaging via Twilio.
Handles outbound messages with automatic splitting for long content.
"""
import logging
from twilio.rest import Client
from config import get_settings

logger = logging.getLogger(__name__)

_client: Client | None = None


def get_twilio_client() -> Client:
    """Get or create Twilio client."""
    global _client
    if _client is None:
        settings = get_settings()
        if not settings.twilio_account_sid or not settings.twilio_auth_token:
            raise ValueError("Twilio credentials not configured.")
        _client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
    return _client


async def send_whatsapp_message(to: str, body: str) -> list[str]:
    """
    Send a WhatsApp message via Twilio.

    Args:
        to: Recipient number (e.g., "whatsapp:+919876543210" or "+919876543210")
        body: Message content

    Returns:
        List of message SIDs
    """
    settings = get_settings()
    client = get_twilio_client()

    # Ensure whatsapp: prefix
    if not to.startswith("whatsapp:"):
        to = f"whatsapp:{to}"

    # Split long messages (WhatsApp limit ~1600 chars)
    chunks = split_message(body, max_length=1500)
    sids = []

    for chunk in chunks:
        try:
            message = client.messages.create(
                body=chunk,
                from_=settings.twilio_whatsapp_from,
                to=to,
            )
            sids.append(message.sid)
            logger.info(f"WhatsApp sent to {to}: SID={message.sid}")
        except Exception as e:
            logger.error(f"Failed to send WhatsApp to {to}: {e}")
            raise

    return sids


def split_message(text: str, max_length: int = 1500) -> list[str]:
    """
    Split a long message into chunks that fit WhatsApp limits.
    Tries to split on paragraph/line boundaries.
    """
    if len(text) <= max_length:
        return [text]

    chunks = []
    remaining = text

    while remaining:
        if len(remaining) <= max_length:
            chunks.append(remaining)
            break

        # Try to split at a paragraph break
        split_pos = remaining.rfind("\n\n", 0, max_length)
        if split_pos == -1:
            # Try line break
            split_pos = remaining.rfind("\n", 0, max_length)
        if split_pos == -1:
            # Try space
            split_pos = remaining.rfind(" ", 0, max_length)
        if split_pos == -1:
            # Force split
            split_pos = max_length

        chunks.append(remaining[:split_pos].strip())
        remaining = remaining[split_pos:].strip()

    return chunks
