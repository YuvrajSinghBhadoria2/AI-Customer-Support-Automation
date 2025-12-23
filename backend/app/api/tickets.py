"""Ticket API endpoints."""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import get_db
from app.models.ticket import Ticket, TicketStatus
from app.schemas.ticket import (
    TicketCreate,
    TicketResponse,
    TicketUpdate,
    TicketApprove,
    TicketFeedback
)
from app.services import (
    classifier_service,
    reply_generator_service,
    router_service,
    gmail_service
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tickets", tags=["tickets"])


@router.post("", response_model=TicketResponse)
async def create_manual_ticket(
    ticket_data: TicketCreate,
    db: Session = Depends(get_db)
):
    """
    Manually create and process a ticket (useful for testing).
    """
    ticket = Ticket(
        source=ticket_data.source,
        customer_email=ticket_data.customer_email,
        subject=ticket_data.subject,
        body=ticket_data.body,
        status=TicketStatus.PENDING_REVIEW
    )
    
    # Process with AI
    try:
        classification = classifier_service.classify_ticket(
            ticket_data.subject,
            ticket_data.body
        )
        ticket.intent = classification.intent
        ticket.urgency = classification.urgency
        ticket.confidence_score = classification.confidence
        
        reply_result = reply_generator_service.generate_reply(
            ticket_data.subject,
            ticket_data.body,
            classification.intent.value,
            classification.urgency.value
        )
        ticket.ai_reply = reply_result.reply
        
        ticket.assigned_team = router_service.route_ticket(
            classification.intent,
            classification.urgency
        )
    except Exception as e:
        logger.error(f"Manual processing failed: {e}")
        ticket.status = TicketStatus.ESCALATED
    
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket


@router.post("/ingest", response_model=dict)
async def ingest_tickets(db: Session = Depends(get_db)):
    """
    Fetch new emails from Gmail and process them.
    """
    try:
        # Fetch unread emails
        ticket_data_list = gmail_service.fetch_unread_emails(max_results=10)
        
        if not ticket_data_list:
            return {"message": "No new emails found", "processed": 0}
        
        processed_count = 0
        
        for ticket_data in ticket_data_list:
            # Create ticket in database
            ticket = Ticket(
                source=ticket_data.source,
                customer_email=ticket_data.customer_email,
                subject=ticket_data.subject,
                body=ticket_data.body,
                status=TicketStatus.PENDING_REVIEW
            )
            
            # Classify ticket
            try:
                classification = classifier_service.classify_ticket(
                    ticket_data.subject,
                    ticket_data.body
                )
                ticket.intent = classification.intent
                ticket.urgency = classification.urgency
                ticket.confidence_score = classification.confidence
                
                # Generate AI reply
                reply_result = reply_generator_service.generate_reply(
                    ticket_data.subject,
                    ticket_data.body,
                    classification.intent.value,
                    classification.urgency.value
                )
                ticket.ai_reply = reply_result.reply
                
                # Update confidence with reply confidence
                ticket.confidence_score = min(
                    classification.confidence,
                    reply_result.confidence
                )
                
                # Route to team
                ticket.assigned_team = router_service.route_ticket(
                    classification.intent,
                    classification.urgency
                )
                
                # Check if should escalate
                if router_service.should_escalate(
                    ticket.confidence_score,
                    classification.urgency
                ):
                    ticket.status = TicketStatus.ESCALATED
                
            except Exception as e:
                logger.error(f"Failed to process ticket: {e}")
                ticket.status = TicketStatus.ESCALATED
            
            db.add(ticket)
            processed_count += 1
        
        db.commit()
        
        return {
            "message": f"Processed {processed_count} tickets",
            "processed": processed_count
        }
        
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=List[TicketResponse])
async def list_tickets(
    status: Optional[TicketStatus] = None,
    urgency: Optional[str] = None,
    intent: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    List tickets with optional filters.
    """
    query = db.query(Ticket)
    
    if status:
        query = query.filter(Ticket.status == status)
    if urgency:
        query = query.filter(Ticket.urgency == urgency)
    if intent:
        query = query.filter(Ticket.intent == intent)
    
    tickets = query.order_by(Ticket.created_at.desc()).offset(skip).limit(limit).all()
    return tickets


@router.get("/{ticket_id}", response_model=TicketResponse)
async def get_ticket(ticket_id: int, db: Session = Depends(get_db)):
    """
    Get ticket details by ID.
    """
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket


@router.put("/{ticket_id}/approve", response_model=TicketResponse)
async def approve_ticket(
    ticket_id: int,
    approve_data: TicketApprove,
    db: Session = Depends(get_db)
):
    """
    Approve and send AI reply (with optional edits).
    """
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    # Use edited reply if provided, otherwise use AI reply
    final_reply = approve_data.edited_reply or ticket.ai_reply
    
    if not final_reply:
        raise HTTPException(status_code=400, detail="No reply to send")
    
    # Send email
    success = gmail_service.send_email(
        to=ticket.customer_email,
        subject=ticket.subject,
        body=final_reply
    )
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to send email")
    
    # Update ticket
    ticket.final_reply = final_reply
    ticket.status = TicketStatus.SENT
    ticket.resolved_at = datetime.utcnow()
    
    db.commit()
    db.refresh(ticket)
    
    return ticket


@router.put("/{ticket_id}/escalate", response_model=TicketResponse)
async def escalate_ticket(ticket_id: int, db: Session = Depends(get_db)):
    """
    Escalate ticket to human team.
    """
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    ticket.status = TicketStatus.ESCALATED
    ticket.assigned_team = f"{ticket.assigned_team} - ESCALATED"
    
    db.commit()
    db.refresh(ticket)
    
    return ticket


@router.post("/{ticket_id}/feedback", response_model=TicketResponse)
async def submit_feedback(
    ticket_id: int,
    feedback_data: TicketFeedback,
    db: Session = Depends(get_db)
):
    """
    Submit feedback for a ticket.
    """
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    ticket.feedback = feedback_data.feedback
    ticket.feedback_rating = feedback_data.rating
    
    db.commit()
    db.refresh(ticket)
    
    return ticket


@router.delete("/{ticket_id}")
async def delete_ticket(ticket_id: int, db: Session = Depends(get_db)):
    """
    Delete a ticket (for testing purposes).
    """
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    db.delete(ticket)
    db.commit()
    
    return {"message": "Ticket deleted"}
