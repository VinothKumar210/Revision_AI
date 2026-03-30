"""
Enhance route — Improve user-pasted study content using AI.
"""
from fastapi import APIRouter
from models.schemas import EnhanceRequest, EnhanceResponse
from services.groq_service import chat_completion
from services.database import users_collection
from utils.errors import handle_api_error

router = APIRouter()


@router.post("/", response_model=EnhanceResponse)
async def enhance_content(request: EnhanceRequest):
    """
    Enhance user-provided study content.

    Takes raw notes/content and returns an improved, structured version
    while preserving the original information.
    """
    try:
        # Look up user for custom API key
        user = await users_collection().find_one({"clerkId": request.clerk_id})
        user_api_key = user.get("groqApiKey") if user else None

        messages = [
            {
                "role": "system",
                "content": (
                    "You are an expert study content enhancer. The user has pasted their "
                    "study notes about a topic. Your job is to:\n"
                    "1. Improve clarity and structure\n"
                    "2. Fix any errors or misconceptions\n"
                    "3. Add important points they might have missed\n"
                    "4. Format it clearly with headings and bullet points\n"
                    "Keep the original information intact. Enhance, don't replace."
                ),
            },
            {
                "role": "user",
                "content": f"Topic: {request.topic_title}\n\nMy notes:\n{request.content}",
            },
        ]

        enhanced = await chat_completion(
            messages=messages,
            user_api_key=user_api_key,
            temperature=0.5,
            max_tokens=2048,
        )

        return EnhanceResponse(
            original=request.content,
            enhanced=enhanced,
        )

    except Exception as e:
        return await handle_api_error(e, context="enhance")
