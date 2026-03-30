"""
Revise route — Generate progressive revision content at specific depth levels.
"""
from fastapi import APIRouter
from bson import ObjectId
from models.schemas import ReviseRequest, ReviseResponse
from services.groq_service import chat_completion
from services.database import topics_collection, users_collection
from utils.errors import handle_api_error, APIError

router = APIRouter()

REVISION_LEVEL_PROMPTS = {
    0: (
        "Generate a BASIC revision of this topic. Include:\n"
        "- Core concepts explained simply\n"
        "- A simple analogy or metaphor\n"
        "- *One real-world/real-time example* to illustrate the concept\n"
        "- 2-3 key points to remember\n"
        "- *Short code snippet or pseudo-code* if applicable\n"
        "Keep it concise and beginner-friendly."
    ),
    1: (
        "Generate a DETAILED revision of this topic. Include:\n"
        "- Thorough explanation of concepts\n"
        "- *One practical real-time example* or case study\n"
        "- *Clean code snippet with comments* for key logic\n"
        "- Common mistakes to avoid\n"
        "- Practice-style questions at the end"
    ),
    2: (
        "Generate an IN-DEPTH revision with STORYTELLING. Include:\n"
        "- A narrative or story that teaches the concept\n"
        "- Deep dive into how and why things work\n"
        "- *One real-time scenario* where this is used right now\n"
        "- *Code snippet* showing the 'under-the-hood' implementation if possible\n"
        "- Connections to related topics\n"
        "- Memorable analogies and visual descriptions"
    ),
    3: (
        "Generate an ADVANCED revision of this topic. Include:\n"
        "- Edge cases and tricky scenarios\n"
        "- Advanced patterns and optimizations\n"
        "- *One high-scale real-time example* (e.g. how Google/Meta use it)\n"
        "- *Production-ready code snippet* or advanced design pattern\n"
        "- Interview-style questions with answers\n"
        "- Common pitfalls and system design connections"
    ),
}


@router.post("/", response_model=ReviseResponse)
async def generate_revision(request: ReviseRequest):
    """
    Generate revision content at a specific depth level (0-3).

    Level 0: Basic — core concepts + simple analogy
    Level 1: Detailed — examples + practice questions
    Level 2: In-depth — storytelling approach
    Level 3: Advanced — edge cases + interview prep
    """
    try:
        # Validate revision level
        level = min(max(request.revision_level, 0), 3)

        # Fetch topic from DB
        topic = await topics_collection().find_one({"_id": ObjectId(request.topic_id)})
        if not topic:
            raise APIError(404, f"Topic not found: {request.topic_id}", "not_found")

        # Look up user for custom API key
        user = await users_collection().find_one({"clerkId": request.clerk_id})
        user_api_key = user.get("groqApiKey") if user else None

        # Build revision prompt
        level_prompt = REVISION_LEVEL_PROMPTS.get(level, REVISION_LEVEL_PROMPTS[0])
        content_context = ""
        if topic.get("enhancedContent"):
            content_context = f"\n\nUser's study notes (enhanced):\n{topic['enhancedContent']}"
        elif topic.get("userContent"):
            content_context = f"\n\nUser's study notes:\n{topic['userContent']}"

        messages = [
            {
                "role": "system",
                "content": (
                    "You are Revision AI, an expert tutor creating revision material. "
                    "Generate content suitable for WhatsApp messages (use *bold*, _italic_, "
                    "and line breaks for formatting). Keep it under 1500 characters.\n\n"
                    f"{level_prompt}"
                ),
            },
            {
                "role": "user",
                "content": f"Topic: {topic['title']}{content_context}",
            },
        ]

        revision_content = await chat_completion(
            messages=messages,
            user_api_key=user_api_key,
            temperature=0.7,
            max_tokens=1500,
        )

        return ReviseResponse(
            topic_id=request.topic_id,
            revision_level=level,
            content=revision_content,
        )

    except Exception as e:
        return await handle_api_error(e, context="revise")
