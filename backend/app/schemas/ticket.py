from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from app.models.ticket import IntentType, UrgencyLevel, TicketStatus


class TicketBase(BaseModel):
    """Base ticket schema."""
    customer_email: EmailStr
    subject: str
    body: str
    source: str = "gmail"


class TicketCreate(TicketBase):
    """Schema for creating a new ticket."""
    pass


class ClassificationResult(BaseModel):
    """AI classification result."""
    intent: IntentType
    urgency: UrgencyLevel
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: Optional[str] = None


class ReplyResult(BaseModel):
    """AI reply generation result."""
    reply: str
    confidence: float = Field(ge=0.0, le=1.0)


class TicketUpdate(BaseModel):
    """Schema for updating a ticket."""
    intent: Optional[IntentType] = None
    urgency: Optional[UrgencyLevel] = None
    ai_reply: Optional[str] = None
    final_reply: Optional[str] = None
    status: Optional[TicketStatus] = None
    assigned_team: Optional[str] = None
    feedback: Optional[str] = None
    feedback_rating: Optional[int] = Field(None, ge=1, le=5)


class TicketResponse(TicketBase):
    """Schema for ticket response."""
    id: int
    intent: Optional[IntentType]
    urgency: Optional[UrgencyLevel]
    category: Optional[str]
    confidence_score: Optional[float]
    ai_reply: Optional[str]
    final_reply: Optional[str]
    assigned_team: Optional[str]
    status: TicketStatus
    feedback: Optional[str]
    feedback_rating: Optional[int]
    created_at: datetime
    updated_at: Optional[datetime]
    resolved_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class TicketApprove(BaseModel):
    """Schema for approving a ticket."""
    edited_reply: Optional[str] = None


class TicketFeedback(BaseModel):
    """Schema for ticket feedback."""
    feedback: str
    rating: int = Field(ge=1, le=5)
