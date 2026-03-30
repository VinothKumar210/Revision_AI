"""
Scheduler Service — APScheduler for periodic revision reminders.
Checks for due schedules and sends revision content via WhatsApp.
"""
import logging
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from config import get_settings

logger = logging.getLogger(__name__)

_scheduler: AsyncIOScheduler | None = None


def get_scheduler() -> AsyncIOScheduler:
    """Get or create the scheduler instance."""
    global _scheduler
    if _scheduler is None:
        _scheduler = AsyncIOScheduler()
    return _scheduler


async def start_scheduler():
    """Start the scheduler with the revision check job."""
    settings = get_settings()
    scheduler = get_scheduler()

    scheduler.add_job(
        check_and_send_revisions,
        trigger=IntervalTrigger(minutes=settings.scheduler_interval_minutes),
        id="revision_check",
        name="Check and send due revisions",
        replace_existing=True,
    )

    scheduler.start()
    logger.info(
        f"⏰ Scheduler started (checking every {settings.scheduler_interval_minutes} min)"
    )


async def stop_scheduler():
    """Stop the scheduler gracefully."""
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("⏰ Scheduler stopped")
    _scheduler = None


async def check_and_send_revisions():
    """
    Main scheduler job:
    1. Find all active schedules where nextRunAt <= now
    2. Generate revision content at the topic's current level
    3. Send via WhatsApp
    4. Update schedule (nextRunAt) and topic (revisionLevel)
    5. Create WhatsApp chat record
    """
    from services.database import (
        schedules_collection,
        topics_collection,
        users_collection,
        whatsapp_chats_collection,
    )
    from services.groq_service import chat_completion
    from services.twilio_service import send_whatsapp_message
    from routes.revise import REVISION_LEVEL_PROMPTS
    from bson import ObjectId

    now = datetime.utcnow()
    logger.info(f"⏰ Checking for due revisions at {now.isoformat()}")

    try:
        # Find due schedules
        cursor = schedules_collection().find({
            "isActive": True,
            "nextRunAt": {"$lte": now},
        })

        count = 0
        async for schedule in cursor:
            try:
                # Fetch topic
                topic = await topics_collection().find_one(
                    {"_id": ObjectId(schedule["topicId"])}
                )
                if not topic:
                    logger.warning(f"Topic not found for schedule {schedule['_id']}")
                    continue

                # Fetch user
                user = await users_collection().find_one(
                    {"_id": ObjectId(schedule["userId"])}
                )
                if not user or not user.get("phone"):
                    logger.warning(f"User not found for schedule {schedule['_id']}")
                    continue

                # Determine revision level
                level = min(topic.get("revisionLevel", 0), 3)
                level_prompt = REVISION_LEVEL_PROMPTS.get(level, REVISION_LEVEL_PROMPTS[0])

                # Build content context
                content_ctx = ""
                if topic.get("enhancedContent"):
                    content_ctx = f"\n\nStudy notes:\n{topic['enhancedContent'][:500]}"
                elif topic.get("userContent"):
                    content_ctx = f"\n\nStudy notes:\n{topic['userContent'][:500]}"

                # Generate revision content
                messages = [
                    {
                        "role": "system",
                        "content": (
                            "You are Revision AI sending a WhatsApp revision reminder. "
                            "Generate concise, engaging revision content. "
                            "Use WhatsApp formatting (*bold*, _italic_). "
                            "Keep it under 1400 characters.\n\n"
                            f"{level_prompt}"
                        ),
                    },
                    {
                        "role": "user",
                        "content": f"Topic: {topic['title']}{content_ctx}",
                    },
                ]

                user_api_key = user.get("groqApiKey")
                revision_content = await chat_completion(
                    messages=messages,
                    user_api_key=user_api_key,
                    temperature=0.7,
                    max_tokens=1200,
                )

                # Format and send WhatsApp
                header = f"📚 *Revision Reminder: {topic['title']}*\n"
                header += f"_Level {level + 1} of 4_\n\n"
                full_message = header + revision_content

                phone = schedule.get("phoneNumber") or user.get("phone")
                if not phone:
                    logger.warning(f"No valid phone number for schedule {schedule['_id']}")
                    continue

                await send_whatsapp_message(phone, full_message)

                # Update schedule — move nextRunAt forward
                next_run = now + timedelta(days=schedule.get("intervalDays", 1))
                await schedules_collection().update_one(
                    {"_id": schedule["_id"]},
                    {
                        "$set": {
                            "lastSentAt": now,
                            "nextRunAt": next_run,
                        }
                    },
                )

                # Bump revision level (max 3)
                new_level = min(level + 1, 3)
                await topics_collection().update_one(
                    {"_id": topic["_id"]},
                    {"$set": {"revisionLevel": new_level, "updatedAt": now}},
                )

                # Save WhatsApp chat record
                await whatsapp_chats_collection().insert_one({
                    "userId": str(user["_id"]),
                    "topicId": str(topic["_id"]),
                    "messages": [
                        {
                            "role": "ai",
                            "content": full_message,
                            "timestamp": now,
                        }
                    ],
                    "createdAt": now,
                })

                count += 1
                logger.info(
                    f"✅ Sent revision for '{topic['title']}' to {phone} (level {level}→{new_level})"
                )

            except Exception as e:
                logger.error(
                    f"Failed to process schedule {schedule.get('_id')}: {e}",
                    exc_info=True,
                )

        if count > 0:
            logger.info(f"⏰ Sent {count} revision(s)")
        else:
            logger.debug("⏰ No due revisions found")

    except Exception as e:
        logger.error(f"Scheduler job error: {e}", exc_info=True)
