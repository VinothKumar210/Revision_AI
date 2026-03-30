"""
MongoDB connection using Motor (async driver).
Connects to the same MongoDB Atlas database as Prisma on the frontend.
Collection names match Prisma's @@map() values.
"""
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from config import get_settings

logger = logging.getLogger(__name__)

_client: AsyncIOMotorClient | None = None
_db = None


async def connect_db():
    """Connect to MongoDB Atlas. Call during app startup."""
    global _client, _db
    settings = get_settings()

    if not settings.mongodb_uri or settings.mongodb_uri == "mongodb://localhost:27017/revision-ai":
        logger.warning("⚠️ No MongoDB URI configured. DB features will not work.")
        return

    try:
        _client = AsyncIOMotorClient(
            settings.mongodb_uri,
            serverSelectionTimeoutMS=5000,
            retryWrites=True,
        )
        # Extract DB name from URI or use default
        db_name = settings.mongodb_uri.split("/")[-1].split("?")[0] or "revision-ai"
        _db = _client[db_name]

        # Verify connection
        await _client.admin.command("ping")
        logger.info(f"✅ Connected to MongoDB Atlas (database: {db_name})")
    except Exception as e:
        logger.warning(f"⚠️ MongoDB connection failed (server will run without DB): {e}")
        _client = None
        _db = None


async def disconnect_db():
    """Disconnect from MongoDB. Call during app shutdown."""
    global _client, _db
    if _client:
        _client.close()
        _client = None
        _db = None
        logger.info("🔌 Disconnected from MongoDB")


def get_db():
    """Get the database instance. Raises if not connected."""
    if _db is None:
        raise RuntimeError("Database not connected. Call connect_db() first.")
    return _db


# ---- Collection accessors (match Prisma's @@map names) ----

def users_collection():
    return get_db()["users"]


def categories_collection():
    return get_db()["categories"]


def topics_collection():
    return get_db()["topics"]


def schedules_collection():
    return get_db()["schedules"]


def whatsapp_chats_collection():
    return get_db()["whatsapp_chats"]
