"""
Groq Service — LLM client for Groq API (Llama 3.3 70B Versatile).
Supports per-user API keys with fallback to default.
"""
import logging
from groq import AsyncGroq
from config import get_settings

logger = logging.getLogger(__name__)


def get_groq_client(user_api_key: str | None = None) -> AsyncGroq:
    """
    Get an async Groq client.
    Uses user's API key if provided, otherwise falls back to default.
    """
    settings = get_settings()
    api_key = user_api_key or settings.groq_api_key

    if not api_key:
        raise ValueError("No Groq API key available. Set GROQ_API_KEY or provide a user key.")

    return AsyncGroq(api_key=api_key)


async def chat_completion(
    messages: list[dict],
    user_api_key: str | None = None,
    model: str | None = None,
    temperature: float = 0.7,
    max_tokens: int = 2048,
) -> str:
    """
    Send a chat completion request to Groq.

    Args:
        messages: List of message dicts [{"role": "system/user/assistant", "content": "..."}]
        user_api_key: Optional per-user Groq API key
        model: LLM model override (defaults to config)
        temperature: Creativity (0.0-1.0)
        max_tokens: Max response tokens

    Returns:
        The assistant's response text
    """
    settings = get_settings()
    client = get_groq_client(user_api_key)
    model_name = model or settings.groq_model

    try:
        response = await client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        content = response.choices[0].message.content
        logger.info(f"Groq response: {len(content)} chars, model={model_name}")
        return content

    except Exception as e:
        logger.error(f"Groq API error: {e}")
        raise
