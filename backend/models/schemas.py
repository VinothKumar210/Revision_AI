"""
Pydantic schemas for API request/response models.
These mirror the Prisma schema fields for consistency.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


# ---- Enums (match Prisma enums) ----

class TopicStatus(str, Enum):
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"


class MessageRole(str, Enum):
    USER = "user"
    AI = "ai"


# ---- Embedded Types ----

class WhatsAppMessageSchema(BaseModel):
    """Matches Prisma's WhatsAppMessage embedded type."""
    role: str  # "ai" or "user"
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ---- Document Schemas (match Prisma models for DB reads) ----

class UserDoc(BaseModel):
    """Matches Prisma User model."""
    id: Optional[str] = Field(None, alias="_id")
    clerkId: str
    email: str
    name: str
    phone: str
    groqApiKey: Optional[str] = None
    isOnboarded: bool = False
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: datetime = Field(default_factory=datetime.utcnow)


class CategoryDoc(BaseModel):
    """Matches Prisma Category model."""
    id: Optional[str] = Field(None, alias="_id")
    userId: str
    name: str
    color: str = "#6C5CE7"
    createdAt: datetime = Field(default_factory=datetime.utcnow)


class TopicDoc(BaseModel):
    """Matches Prisma Topic model."""
    id: Optional[str] = Field(None, alias="_id")
    userId: str
    categoryId: Optional[str] = None
    title: str
    userContent: Optional[str] = None
    enhancedContent: Optional[str] = None
    revisionLevel: int = 0
    status: TopicStatus = TopicStatus.ACTIVE
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: datetime = Field(default_factory=datetime.utcnow)


class ScheduleDoc(BaseModel):
    """Matches Prisma Schedule model."""
    id: Optional[str] = Field(None, alias="_id")
    userId: str
    topicId: str
    intervalDays: int
    preferredTime: str  # "HH:MM"
    nextRunAt: datetime
    lastSentAt: Optional[datetime] = None
    isActive: bool = True
    createdAt: datetime = Field(default_factory=datetime.utcnow)


class WhatsAppChatDoc(BaseModel):
    """Matches Prisma WhatsAppChat model."""
    id: Optional[str] = Field(None, alias="_id")
    userId: str
    topicId: str
    messages: List[WhatsAppMessageSchema] = []
    createdAt: datetime = Field(default_factory=datetime.utcnow)


# ---- API Request Models ----

class ChatRequest(BaseModel):
    """Request body for /chat endpoint."""
    message: str = Field(..., description="User message")
    conversation_history: List[dict] = Field(default_factory=list)
    clerk_id: str = Field(..., description="Clerk user ID")


class EnhanceRequest(BaseModel):
    """Request body for /enhance endpoint."""
    content: str = Field(..., description="User-pasted study content")
    topic_title: str = Field(..., description="Topic title for context")
    clerk_id: str = Field(..., description="Clerk user ID")


class ReviseRequest(BaseModel):
    """Request body for /revise endpoint."""
    topic_id: str = Field(..., description="MongoDB topic ID")
    revision_level: int = Field(default=0, description="Depth level 0-3")
    clerk_id: str = Field(..., description="Clerk user ID")


class SaveTopicRequest(BaseModel):
    """Request body for saving a confirmed topic."""
    clerk_id: str = Field(..., description="Clerk user ID")
    title: str = Field(..., description="Topic title")
    category: str = Field(..., description="Category name")
    user_content: Optional[str] = Field(None, description="User-pasted content")
    enhanced_content: Optional[str] = Field(None, description="AI-enhanced content")
    interval_days: Optional[int] = Field(None, description="Desired schedule repetition interval")
    preferred_time: Optional[str] = Field(None, description="Preferred schedule time (HH:MM)")


# ---- API Response Models ----

class ConfirmedData(BaseModel):
    """Structured data for a confirmed topic."""
    title: str
    category: str
    subtopics: Optional[List[str]] = None
    user_content: Optional[str] = None
    interval_days: Optional[int] = None
    preferred_time: Optional[str] = None


class ChatResponse(BaseModel):
    """Response from /chat endpoint."""
    message: str
    intent: Optional[str] = None  # "greeting", "clarify", "suggest", "confirm", "save"
    suggested_topics: Optional[List[str]] = None
    suggested_category: Optional[str] = None
    confirmed_data: Optional[ConfirmedData] = None
    enhanced_content: Optional[str] = None


class EnhanceResponse(BaseModel):
    """Response from /enhance endpoint."""
    original: str
    enhanced: str


class ReviseResponse(BaseModel):
    """Response from /revise endpoint."""
    topic_id: str
    revision_level: int
    content: str


class SaveTopicResponse(BaseModel):
    """Response from save topic endpoint."""
    success: bool
    topic_id: str
    title: str
    category: str


class HealthResponse(BaseModel):
    """Response from /health endpoint."""
    status: str
    service: str
    version: str
