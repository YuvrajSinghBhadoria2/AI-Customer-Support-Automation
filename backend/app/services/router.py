"""Routing service for assigning tickets to teams."""

import logging
from typing import Dict
from app.models.ticket import IntentType, UrgencyLevel

logger = logging.getLogger(__name__)


class RouterService:
    """Service for routing tickets to appropriate teams."""
    
    # Intent to team mapping
    INTENT_TEAM_MAP: Dict[IntentType, str] = {
        IntentType.BILLING: "Finance Team",
        IntentType.TECHNICAL_ISSUE: "Tech Support",
        IntentType.ACCOUNT_ACCESS: "Account Services",
        IntentType.CANCELLATION: "Retention Team",
        IntentType.FEATURE_REQUEST: "Product Team",
        IntentType.GENERAL_INQUIRY: "General Support"
    }
    
    # SLA hours by urgency
    SLA_HOURS: Dict[UrgencyLevel, int] = {
        UrgencyLevel.LOW: 48,
        UrgencyLevel.MEDIUM: 24,
        UrgencyLevel.HIGH: 8,
        UrgencyLevel.CRITICAL: 2
    }
    
    def route_ticket(self, intent: IntentType, urgency: UrgencyLevel) -> str:
        """
        Route ticket to appropriate team based on intent.
        
        Args:
            intent: Ticket intent
            urgency: Ticket urgency level
            
        Returns:
            Team name to assign ticket to
        """
        team = self.INTENT_TEAM_MAP.get(intent, "General Support")
        
        # Escalate critical issues to senior team
        if urgency == UrgencyLevel.CRITICAL:
            team = f"{team} - ESCALATED"
            logger.warning(f"Critical ticket routed to: {team}")
        
        logger.info(f"Routed {intent} ticket to {team}")
        return team
    
    def get_sla_hours(self, urgency: UrgencyLevel) -> int:
        """
        Get SLA hours for urgency level.
        
        Args:
            urgency: Ticket urgency level
            
        Returns:
            SLA hours
        """
        return self.SLA_HOURS.get(urgency, 24)
    
    def should_auto_send(self, confidence: float, urgency: UrgencyLevel) -> bool:
        """
        Determine if reply should be auto-sent based on confidence and urgency.
        
        Args:
            confidence: AI confidence score (0-1)
            urgency: Ticket urgency level
            
        Returns:
            True if should auto-send, False if needs human review
        """
        # Never auto-send critical or high urgency tickets
        if urgency in [UrgencyLevel.CRITICAL, UrgencyLevel.HIGH]:
            logger.info("High/Critical urgency - requires human review")
            return False
        
        # Auto-send if confidence is high enough
        from app.config import settings
        if confidence >= settings.auto_send_threshold:
            logger.info(f"Auto-send approved (confidence: {confidence})")
            return True
        
        logger.info(f"Confidence too low ({confidence}) - requires human review")
        return False
    
    def should_escalate(self, confidence: float, urgency: UrgencyLevel) -> bool:
        """
        Determine if ticket should be escalated.
        
        Args:
            confidence: AI confidence score (0-1)
            urgency: Ticket urgency level
            
        Returns:
            True if should escalate
        """
        # Always escalate critical
        if urgency == UrgencyLevel.CRITICAL:
            return True
        
        # Escalate if confidence is very low
        from app.config import settings
        if confidence < settings.escalation_threshold:
            logger.warning(f"Low confidence ({confidence}) - escalating")
            return True
        
        return False


# Singleton instance
router_service = RouterService()
