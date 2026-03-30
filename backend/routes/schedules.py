"""
Schedules route — Create, update, delete revision schedules.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timedelta
from bson import ObjectId
from services.database import users_collection, schedules_collection, topics_collection
from utils.errors import handle_api_error, APIError
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


class CreateScheduleRequest(BaseModel):
    clerk_id: str
    topic_id: str
    interval_days: int = Field(1, ge=0, le=30)
    preferred_time: str = Field("08:00", description="HH:MM format")
    phone_number: Optional[str] = None


class UpdateScheduleRequest(BaseModel):
    clerk_id: str
    interval_days: Optional[int] = Field(None, ge=0, le=30)
    preferred_time: Optional[str] = None
    phone_number: Optional[str] = None
    is_active: Optional[bool] = None


@router.post("/")
async def create_schedule(request: CreateScheduleRequest):
    """Create a new revision schedule for a topic."""
    try:
        user = await users_collection().find_one({"clerkId": request.clerk_id})
        if not user:
            raise APIError(404, "User not found", "not_found")

        user_id = str(user["_id"])

        # Verify topic exists and belongs to user
        topic = await topics_collection().find_one({
            "_id": ObjectId(request.topic_id),
            "userId": user_id,
        })
        if not topic:
            raise APIError(404, "Topic not found", "not_found")

        # Check for existing schedule
        existing = await schedules_collection().find_one({
            "userId": user_id,
            "topicId": request.topic_id,
            "isActive": True,
        })
        if existing:
            raise APIError(409, "An active schedule already exists for this topic", "conflict")

        now = datetime.utcnow()
        next_run = now + timedelta(days=request.interval_days)

        result = await schedules_collection().insert_one({
            "userId": user_id,
            "topicId": request.topic_id,
            "intervalDays": request.interval_days,
            "preferredTime": request.preferred_time,
            "phoneNumber": request.phone_number,
            "nextRunAt": next_run,
            "lastSentAt": None,
            "isActive": True,
            "createdAt": now,
        })

        logger.info(f"Created schedule for topic {request.topic_id}")

        return {
            "success": True,
            "schedule_id": str(result.inserted_id),
            "next_run_at": next_run.isoformat(),
        }

    except Exception as e:
        return await handle_api_error(e, context="schedules/create")


@router.get("/")
async def get_schedules(clerk_id: str):
    """Get all schedules for a user."""
    try:
        user = await users_collection().find_one({"clerkId": clerk_id})
        if not user:
            return {"schedules": []}

        user_id = str(user["_id"])
        schedules = []
        cursor = schedules_collection().find({"userId": user_id}).sort("createdAt", -1)

        async for sched in cursor:
            # Get topic name
            topic_title = "Unknown"
            if sched.get("topicId"):
                topic = await topics_collection().find_one({"_id": ObjectId(sched["topicId"])})
                if topic:
                    topic_title = topic["title"]

            schedules.append({
                "id": str(sched["_id"]),
                "topicId": sched["topicId"],
                "topicTitle": topic_title,
                "intervalDays": sched["intervalDays"],
                "preferredTime": sched.get("preferredTime", "08:00"),
                "phoneNumber": sched.get("phoneNumber"),
                "nextRunAt": sched["nextRunAt"].isoformat() if sched.get("nextRunAt") else None,
                "lastSentAt": sched["lastSentAt"].isoformat() if sched.get("lastSentAt") else None,
                "isActive": sched.get("isActive", True),
                "createdAt": sched["createdAt"].isoformat() if sched.get("createdAt") else None,
            })

        return {"schedules": schedules}

    except Exception as e:
        return await handle_api_error(e, context="schedules/list")


@router.put("/{schedule_id}")
async def update_schedule(schedule_id: str, request: UpdateScheduleRequest):
    """Update a schedule."""
    try:
        user = await users_collection().find_one({"clerkId": request.clerk_id})
        if not user:
            raise APIError(404, "User not found", "not_found")

        update_data = {}
        if request.interval_days is not None:
            update_data["intervalDays"] = request.interval_days
            # Recalculate next run
            now = datetime.utcnow()
            update_data["nextRunAt"] = now + timedelta(days=request.interval_days)
        if request.preferred_time is not None:
            update_data["preferredTime"] = request.preferred_time
        if request.phone_number is not None:
            update_data["phoneNumber"] = request.phone_number
        if request.is_active is not None:
            update_data["isActive"] = request.is_active

        if not update_data:
            raise APIError(400, "No fields to update", "validation_error")

        result = await schedules_collection().update_one(
            {"_id": ObjectId(schedule_id), "userId": str(user["_id"])},
            {"$set": update_data},
        )

        if result.matched_count == 0:
            raise APIError(404, "Schedule not found", "not_found")

        # Get updated schedule
        updated = await schedules_collection().find_one({"_id": ObjectId(schedule_id)})
        
        # Format for frontend
        topic = await topics_collection().find_one({"_id": ObjectId(updated["topicId"])})
        formatted = {
            "id": str(updated["_id"]),
            "topicId": updated["topicId"],
            "topicTitle": topic["title"] if topic else "Unknown",
            "intervalDays": updated["intervalDays"],
            "preferredTime": updated.get("preferredTime", "08:00"),
            "phoneNumber": updated.get("phoneNumber"),
            "nextRunAt": updated["nextRunAt"].isoformat() if updated.get("nextRunAt") else None,
            "isActive": updated.get("isActive", True),
        }

        return {"success": True, "schedule": formatted}

    except Exception as e:
        return await handle_api_error(e, context="schedules/update")


@router.delete("/{schedule_id}")
async def delete_schedule(schedule_id: str, clerk_id: str):
    """Delete a schedule."""
    try:
        user = await users_collection().find_one({"clerkId": clerk_id})
        if not user:
            raise APIError(404, "User not found", "not_found")

        result = await schedules_collection().delete_one({
            "_id": ObjectId(schedule_id),
            "userId": str(user["_id"]),
        })

        if result.deleted_count == 0:
            raise APIError(404, "Schedule not found", "not_found")

        return {"success": True}

    except Exception as e:
        return await handle_api_error(e, context="schedules/delete")
