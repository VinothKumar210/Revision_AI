"""
Topics route — Save and manage confirmed topics from the chat flow.
"""
from fastapi import APIRouter
from datetime import datetime
from typing import Optional
from models.schemas import SaveTopicRequest, SaveTopicResponse
from services.database import users_collection, categories_collection, topics_collection, schedules_collection
from utils.errors import handle_api_error, APIError
from bson import ObjectId
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/save", response_model=SaveTopicResponse)
async def save_topic(request: SaveTopicRequest):
    """
    Save a confirmed topic from the chat flow.

    1. Find or create the category
    2. Create the topic
    3. Return the saved topic ID
    """
    try:
        # Find user
        user = await users_collection().find_one({"clerkId": request.clerk_id})
        if not user:
            raise APIError(404, "User not found. Please complete onboarding.", "not_found")

        user_id = str(user["_id"])

        # Find or create category
        category = await categories_collection().find_one({
            "userId": user_id,
            "name": request.category,
        })

        if not category:
            cat_result = await categories_collection().insert_one({
                "userId": user_id,
                "name": request.category,
                "color": "#6C5CE7",
                "createdAt": datetime.utcnow(),
            })
            category_id = str(cat_result.inserted_id)
            logger.info(f"Created category: {request.category} for user {user_id}")
        else:
            category_id = str(category["_id"])

        # Create topic
        now = datetime.utcnow()
        topic_result = await topics_collection().insert_one({
            "userId": user_id,
            "categoryId": category_id,
            "title": request.title,
            "userContent": request.user_content,
            "enhancedContent": request.enhanced_content,
            "revisionLevel": 0,
            "status": "ACTIVE",
            "createdAt": now,
            "updatedAt": now,
        })

        topic_id = str(topic_result.inserted_id)
        logger.info(f"Saved topic: {request.title} (id={topic_id})")

        # Automatically create schedule if requested
        if request.interval_days is not None and request.preferred_time:
            from services.database import schedules_collection
            import datetime as dt
            
            # Setup next run timestamp
            next_run = dt.datetime.utcnow() + dt.timedelta(days=request.interval_days)
            try:
                hours, mins = map(int, request.preferred_time.split(':'))
                next_run = next_run.replace(hour=hours, minute=mins, second=0, microsecond=0)
            except ValueError:
                pass
            
            await schedules_collection().insert_one({
                "userId": user_id,
                "topicId": topic_id,
                "intervalDays": request.interval_days,
                "preferredTime": request.preferred_time,
                "nextRunAt": next_run,
                "lastSentAt": None,
                "isActive": True,
                "createdAt": now,
            })
            logger.info(f"Created schedule automatically for topic {topic_id}")

        return SaveTopicResponse(
            success=True,
            topic_id=topic_id,
            title=request.title,
            category=request.category,
        )

    except Exception as e:
        return await handle_api_error(e, context="topics/save")


@router.get("/")
async def get_topics(clerk_id: str):
    """Get all topics for a user."""
    try:
        user = await users_collection().find_one({"clerkId": clerk_id})
        if not user:
            return {"topics": []}

        user_id = str(user["_id"])
        topics = []
        cursor = topics_collection().find({"userId": user_id}).sort("createdAt", -1)

        async for topic in cursor:
            # Fetch category name
            category_name = "Uncategorized"
            if topic.get("categoryId"):
                from bson import ObjectId
                cat = await categories_collection().find_one({"_id": ObjectId(topic["categoryId"])})
                if cat:
                    category_name = cat["name"]

            topics.append({
                "id": str(topic["_id"]),
                "title": topic["title"],
                "category": category_name,
                "categoryId": topic.get("categoryId"),
                "revisionLevel": topic.get("revisionLevel", 0),
                "status": topic.get("status", "ACTIVE"),
                "userContent": topic.get("userContent"),
                "enhancedContent": topic.get("enhancedContent"),
                "createdAt": topic.get("createdAt", "").isoformat() if topic.get("createdAt") else None,
            })

        return {"topics": topics}

    except Exception as e:
        return await handle_api_error(e, context="topics/list")

@router.patch("/{topic_id}")
async def update_topic(topic_id: str, request: dict):
    """Update topic details (title, category, etc)."""
    try:
        clerk_id = request.get("clerk_id")
        if not clerk_id:
            raise APIError(400, "clerk_id is required", "validation_error")

        user = await users_collection().find_one({"clerkId": clerk_id})
        if not user:
            raise APIError(404, "User not found", "not_found")

        update_data = {}
        if "title" in request:
            update_data["title"] = request["title"]
        if "status" in request:
            update_data["status"] = request["status"]
        if "user_content" in request:
            update_data["userContent"] = request["user_content"]

        update_data["updatedAt"] = datetime.utcnow()

        result = await topics_collection().update_one(
            {"_id": ObjectId(topic_id), "userId": str(user["_id"])},
            {"$set": update_data}
        )

        if result.matched_count == 0:
            raise APIError(404, "Topic not found", "not_found")

        # Get updated topic
        updated = await topics_collection().find_one({"_id": ObjectId(topic_id)})
        
        # Format for frontend (include category name)
        category_name = "Uncategorized"
        if updated.get("categoryId"):
            cat = await categories_collection().find_one({"_id": ObjectId(updated["categoryId"])})
            if cat:
                category_name = cat["name"]

        formatted = {
            "id": str(updated["_id"]),
            "title": updated["title"],
            "category": category_name,
            "categoryId": updated.get("categoryId"),
            "revisionLevel": updated.get("revisionLevel", 0),
            "status": updated.get("status", "ACTIVE"),
            "userContent": updated.get("userContent"),
            "enhancedContent": updated.get("enhancedContent"),
            "createdAt": updated.get("createdAt").isoformat() if updated.get("createdAt") else None,
        }

        return {"success": True, "topic": formatted}
    except Exception as e:
        return await handle_api_error(e, context="topics/update")


@router.delete("/{topic_id}")
async def delete_topic(topic_id: str, clerk_id: str):
    """Delete a topic and its associated schedules."""
    try:
        user = await users_collection().find_one({"clerkId": clerk_id})
        if not user:
            raise APIError(404, "User not found", "not_found")

        user_id = str(user["_id"])

        # Delete schedules first
        await schedules_collection().delete_many({
            "topicId": topic_id,
            "userId": user_id
        })

        # Delete topic
        result = await topics_collection().delete_one({
            "_id": ObjectId(topic_id),
            "userId": user_id
        })

        if result.deleted_count == 0:
            raise APIError(404, "Topic not found", "not_found")

        return {"success": True}
    except Exception as e:
        return await handle_api_error(e, context="topics/delete")
