"""
Webhook route — Twilio inbound WhatsApp messages for doubt clarification.
"""
from fastapi import APIRouter, Request, Response
from services.database import users_collection, topics_collection, whatsapp_chats_collection
from services.groq_service import chat_completion
from utils.errors import handle_api_error
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/twilio")
async def twilio_webhook(request: Request):
    """
    Receive inbound WhatsApp messages from Twilio.

    Flow:
    1. Parse incoming message from Twilio
    2. Identify user by phone number
    3. Find the most recent topic sent to this user
    4. Use AI to clarify the user's doubt
    5. Reply via Twilio
    6. Save conversation to WhatsAppChat history
    """
    try:
        # Parse Twilio form data
        form_data = await request.form()
        from_number = form_data.get("From", "")  # e.g., "whatsapp:+919876543210"
        body = form_data.get("Body", "").strip()

        if not from_number or not body:
            return Response(content="<Response></Response>", media_type="application/xml")

        # Extract phone number (remove "whatsapp:" prefix)
        phone = from_number.replace("whatsapp:", "")

        logger.info(f"Inbound WhatsApp from {phone}: {body[:50]}...")

        # Find user by phone
        user = await users_collection().find_one({"phone": phone})
        if not user:
            logger.warning(f"Unknown phone number: {phone}")
            # Return TwiML response
            twiml = (
                "<Response><Message>"
                "Sorry, I don't recognize this number. Please sign up at our website first."
                "</Message></Response>"
            )
            return Response(content=twiml, media_type="application/xml")

        # Find the most recent WhatsApp chat for context
        recent_chat = await whatsapp_chats_collection().find_one(
            {"userId": str(user["_id"])},
            sort=[("createdAt", -1)],
        )

        # Build context for AI
        context_messages = []
        if recent_chat and recent_chat.get("messages"):
            for msg in recent_chat["messages"][-6:]:  # Last 6 messages for context
                context_messages.append({
                    "role": "assistant" if msg["role"] == "ai" else "user",
                    "content": msg["content"],
                })

        # Get topic context
        topic_context = ""
        if recent_chat:
            topic = await topics_collection().find_one({"_id": recent_chat.get("topicId")})
            if topic:
                topic_context = f"\nTopic being revised: {topic['title']}"
                if topic.get("enhancedContent"):
                    topic_context += f"\nTopic content: {topic['enhancedContent'][:500]}"

        messages = [
            {
                "role": "system",
                "content": (
                    "You are Revision AI on WhatsApp. A student is asking a doubt about "
                    "a revision topic you sent them. Clarify their doubt clearly and concisely. "
                    "Use WhatsApp formatting (*bold*, _italic_). Keep response under 1000 characters."
                    f"{topic_context}"
                ),
            },
            *context_messages,
            {"role": "user", "content": body},
        ]

        # Get AI response
        user_api_key = user.get("groqApiKey")
        ai_response = await chat_completion(
            messages=messages,
            user_api_key=user_api_key,
            temperature=0.6,
            max_tokens=800,
        )

        # Save to chat history
        now = datetime.utcnow()
        if recent_chat:
            await whatsapp_chats_collection().update_one(
                {"_id": recent_chat["_id"]},
                {
                    "$push": {
                        "messages": {
                            "$each": [
                                {"role": "user", "content": body, "timestamp": now},
                                {"role": "ai", "content": ai_response, "timestamp": now},
                            ]
                        }
                    }
                },
            )

        # Send reply via Twilio (import here to avoid circular deps)
        from services.twilio_service import send_whatsapp_message
        await send_whatsapp_message(from_number, ai_response)

        # Return empty TwiML (we handle reply ourselves)
        return Response(content="<Response></Response>", media_type="application/xml")

    except Exception as e:
        logger.error(f"Webhook error: {e}", exc_info=True)
        return Response(content="<Response></Response>", media_type="application/xml")
