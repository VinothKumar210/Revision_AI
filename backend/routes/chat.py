"""
Chat route — AI conversation for topic clarification.
Uses the topic agent for multi-turn clarification and content enhancement.
"""
from fastapi import APIRouter
from models.schemas import ChatRequest, ChatResponse, EnhanceRequest, EnhanceResponse
from agents.topic_agent import run_topic_agent
from services.groq_service import chat_completion
from services.database import users_collection
from utils.errors import handle_api_error
from prompts.chat_prompts import CONTENT_ENHANCE_PROMPT

router = APIRouter()


@router.post("/", response_model=ChatResponse)
async def chat_with_ai(request: ChatRequest):
    """
    Chat with AI to clarify and confirm revision topics.

    The topic agent will:
    1. Understand the topic the user wants to revise
    2. Ask clarifying questions (subject, subtopic, depth)
    3. Suggest categories and topics
    4. Confirm final topics before saving

    Returns structured response with intent classification.
    """
    try:
        response = await run_topic_agent(
            message=request.message,
            conversation_history=request.conversation_history,
            clerk_id=request.clerk_id,
        )
        return response

    except Exception as e:
        return await handle_api_error(e, context="chat")


@router.post("/enhance", response_model=EnhanceResponse)
async def enhance_content(request: EnhanceRequest):
    """
    Enhance user-pasted study content within the chat flow.
    """
    try:
        # Look up user for custom API key
        user = await users_collection().find_one({"clerkId": request.clerk_id})
        user_api_key = user.get("groqApiKey") if user else None

        messages = [
            {"role": "system", "content": CONTENT_ENHANCE_PROMPT},
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
        return await handle_api_error(e, context="chat/enhance")
