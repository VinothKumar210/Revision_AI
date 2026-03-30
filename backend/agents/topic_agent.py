"""
Topic Agent — Multi-turn conversation for topic clarification.
Uses Groq/Llama to guide users through identifying and confirming revision topics.
"""
import json
import logging
from services.groq_service import chat_completion
from services.database import users_collection, categories_collection, topics_collection
from prompts.chat_prompts import TOPIC_AGENT_SYSTEM_PROMPT
from models.schemas import ChatResponse

logger = logging.getLogger(__name__)


async def get_user_context(clerk_id: str) -> dict:
    """Fetch user's existing categories and topics for context."""
    context = {"categories": [], "topics": [], "user_api_key": None}

    try:
        user = await users_collection().find_one({"clerkId": clerk_id})
        if not user:
            return context

        context["user_api_key"] = user.get("groqApiKey")
        user_id = str(user["_id"])

        # Fetch categories
        categories_cursor = categories_collection().find({"userId": user_id})
        async for cat in categories_cursor:
            context["categories"].append(cat["name"])

        # Fetch recent topics
        topics_cursor = topics_collection().find(
            {"userId": user_id}
        ).sort("createdAt", -1).limit(20)
        async for topic in topics_cursor:
            context["topics"].append(topic["title"])

    except Exception as e:
        logger.warning(f"Failed to fetch user context: {e}")

    return context


def build_context_message(user_context: dict) -> str:
    """Build a context string about the user's existing data."""
    parts = []
    if user_context["categories"]:
        parts.append(f"User's existing categories: {', '.join(user_context['categories'])}")
    if user_context["topics"]:
        parts.append(f"User's existing topics: {', '.join(user_context['topics'][:10])}")
    if not parts:
        parts.append("This is a new user with no existing topics or categories.")
    return "\n".join(parts)


def parse_ai_response(raw_response: str) -> dict:
    """
    Parse the AI's JSON response, handling common formatting issues.
    Falls back to plain message if JSON parsing fails.
    """
    # Try to extract JSON from the response
    text = raw_response.strip()

    # Remove markdown code block if present
    if text.startswith("```"):
        lines = text.split("\n")
        # Remove first and last lines (``` markers)
        json_lines = []
        in_block = False
        for line in lines:
            if line.strip().startswith("```") and not in_block:
                in_block = True
                continue
            elif line.strip() == "```" and in_block:
                break
            elif in_block:
                json_lines.append(line)
        text = "\n".join(json_lines)

    try:
        parsed = json.loads(text)
        return {
            "message": parsed.get("message", raw_response),
            "intent": parsed.get("intent", "clarify"),
            "suggested_topics": parsed.get("suggested_topics"),
            "suggested_category": parsed.get("suggested_category"),
            "confirmed_data": parsed.get("confirmed_data"),
        }
    except json.JSONDecodeError:
        # If JSON parsing fails, treat the whole response as the message
        logger.warning("Failed to parse AI response as JSON, using raw text")
        return {
            "message": raw_response,
            "intent": "clarify",
            "suggested_topics": None,
            "suggested_category": None,
            "confirmed_data": None,
        }


async def run_topic_agent(
    message: str,
    conversation_history: list[dict],
    clerk_id: str,
) -> ChatResponse:
    """
    Run the topic clarification agent.

    Args:
        message: Current user message
        conversation_history: Previous messages in the conversation
        clerk_id: Clerk user ID for context lookup

    Returns:
        ChatResponse with AI message, intent, and optional topic data
    """
    # Fetch user context (existing categories, topics, API key)
    user_context = await get_user_context(clerk_id)

    # Build the messages list
    context_info = build_context_message(user_context)

    messages = [
        {
            "role": "system",
            "content": f"{TOPIC_AGENT_SYSTEM_PROMPT}\n\n## User Context\n{context_info}",
        },
    ]

    # Add conversation history
    for msg in conversation_history:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        # Map "ai" role to "assistant" for Groq
        if role == "ai":
            role = "assistant"
        messages.append({"role": role, "content": content})

    # Add current message
    messages.append({"role": "user", "content": message})

    # Call Groq
    raw_response = await chat_completion(
        messages=messages,
        user_api_key=user_context["user_api_key"],
        temperature=0.7,
        max_tokens=1024,
    )

    # Parse structured response
    parsed = parse_ai_response(raw_response)

    return ChatResponse(
        message=parsed["message"],
        intent=parsed["intent"],
        suggested_topics=parsed.get("suggested_topics"),
        confirmed_data=parsed.get("confirmed_data"),
        enhanced_content=None,
    )
