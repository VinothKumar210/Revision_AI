"""
Standardized error handling for FastAPI routes.
"""
from fastapi import HTTPException
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)


class APIError(Exception):
    """Custom API error with status code and detail."""

    def __init__(self, status_code: int, detail: str, error_type: str = "api_error"):
        self.status_code = status_code
        self.detail = detail
        self.error_type = error_type
        super().__init__(detail)


def error_response(status_code: int, detail: str, error_type: str = "error") -> JSONResponse:
    """Create a standardized error response."""
    return JSONResponse(
        status_code=status_code,
        content={
            "error": True,
            "type": error_type,
            "detail": detail,
        },
    )


async def handle_api_error(e: Exception, context: str = "") -> JSONResponse:
    """
    Handle exceptions and return standardized error responses.
    Logs the error and returns an appropriate response.
    """
    prefix = f"[{context}] " if context else ""

    if isinstance(e, APIError):
        logger.warning(f"{prefix}{e.error_type}: {e.detail}")
        return error_response(e.status_code, e.detail, e.error_type)

    if isinstance(e, HTTPException):
        logger.warning(f"{prefix}HTTP {e.status_code}: {e.detail}")
        return error_response(e.status_code, e.detail, "http_error")

    if isinstance(e, ValueError):
        logger.warning(f"{prefix}Validation error: {e}")
        return error_response(400, str(e), "validation_error")

    # Groq-specific errors
    error_str = str(e).lower()
    if "rate_limit" in error_str or "rate limit" in error_str:
        logger.warning(f"{prefix}Rate limited: {e}")
        return error_response(429, "AI rate limit reached. Please try again in a moment.", "rate_limit")

    if "authentication" in error_str or "api key" in error_str or "unauthorized" in error_str:
        logger.warning(f"{prefix}Auth error: {e}")
        return error_response(401, "Invalid API key. Please check your Groq API key.", "auth_error")

    # Unexpected error
    logger.error(f"{prefix}Unexpected error: {e}", exc_info=True)
    return error_response(500, "An unexpected error occurred. Please try again.", "internal_error")
