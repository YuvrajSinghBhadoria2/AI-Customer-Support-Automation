from sqlalchemy import Column, Integer, String, Text, Float, DateTime, Enum
from sqlalchemy.sql import func
from app.database import Base
import enum


class IntentType(str, enum.Enum):
    """Customer intent categories."""
    BILLING = "billing"
    TECHNICAL_ISSUE = "technical_issue"
    ACCOUNT_ACCESS = "account_access"
    CANCELLATION = "cancellation"
    FEATURE_REQUEST = "feature_request"
    GENERAL_INQUIRY = "general_inquiry"


class UrgencyLevel(str, enum.Enum):
    """Ticket urgency levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TicketStatus(str, enum.Enum):
    """Ticket processing status."""
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    SENT = "sent"
    ESCALATED = "escalated"
    CLOSED = "closed"


class Ticket(Base):
    """Ticket model for customer support requests."""
    
    __tablename__ = "tickets"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Source Information
    source = Column(String(50), nullable=False, default="gmail")
    customer_email = Column(String(255), nullable=False, index=True)
    subject = Column(String(500), nullable=False)
    body = Column(Text, nullable=False)
    
    # AI Classification
    intent = Column(Enum(IntentType), nullable=True)
    urgency = Column(Enum(UrgencyLevel), nullable=True)
    category = Column(String(100), nullable=True)
    confidence_score = Column(Float, nullable=True)
    
    # AI Response
    ai_reply = Column(Text, nullable=True)
    final_reply = Column(Text, nullable=True)  # After human edit
    
    # Routing
    assigned_team = Column(String(100), nullable=True)
    
    # Status
    status = Column(Enum(TicketStatus), default=TicketStatus.PENDING_REVIEW, nullable=False)
    
    # Feedback
    feedback = Column(Text, nullable=True)
    feedback_rating = Column(Integer, nullable=True)  # 1-5
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self):
        return f"<Ticket {self.id}: {self.subject[:30]}... - {self.status}>"
