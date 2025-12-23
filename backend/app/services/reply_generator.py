"""AI reply generation service using Groq."""

import logging
from groq import Groq
from app.config import settings
from app.schemas.ticket import ReplyResult
from app.prompts.reply import REPLY_SYSTEM_PROMPT, get_reply_prompt

logger = logging.getLogger(__name__)


class ReplyGeneratorService:
    """Service for generating AI replies to customer tickets."""
    
    def __init__(self):
        """Initialize Groq client."""
        self.client = Groq(api_key=settings.groq_api_key)
        self.model = settings.groq_model
    
    def generate_reply(
        self,
        subject: str,
        body: str,
        intent: str,
        urgency: str
    ) -> ReplyResult:
        """
        Generate an AI reply for a ticket.
        
        Args:
            subject: Email subject line
            body: Email body content
            intent: Classified intent
            urgency: Classified urgency level
            
        Returns:
            ReplyResult with generated reply and confidence
            
        Raises:
            Exception: If reply generation fails
        """
        try:
            # Generate prompt
            user_prompt = get_reply_prompt(subject, body, intent, urgency)
            
            # Call Groq API with slightly higher temperature for natural responses
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": REPLY_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2,
                max_tokens=1000
            )
            
            # Extract reply
            reply_text = response.choices[0].message.content.strip()
            
            # Calculate confidence based on response quality
            # For now, use a simple heuristic
            confidence = self._calculate_confidence(reply_text, intent, urgency)
            
            result = ReplyResult(
                reply=reply_text,
                confidence=confidence
            )
            
            logger.info(f"Generated reply with confidence {confidence}")
            
            return result
            
        except Exception as e:
            logger.error(f"Reply generation failed: {e}")
            raise Exception(f"Reply generation error: {str(e)}")
    
    def _calculate_confidence(self, reply: str, intent: str, urgency: str) -> float:
        """
        Calculate confidence score for generated reply.
        
        Simple heuristic based on:
        - Reply length (too short = low confidence)
        - Presence of unsafe phrases
        - Urgency level (critical = lower confidence)
        """
        confidence = 0.85  # Base confidence
        
        # Penalize very short replies
        if len(reply) < 50:
            confidence -= 0.2
        
        # Penalize if contains potentially unsafe phrases
        unsafe_phrases = [
            "refund", "guarantee", "promise", "will fix",
            "by tomorrow", "compensation", "credit"
        ]
        for phrase in unsafe_phrases:
            if phrase.lower() in reply.lower():
                confidence -= 0.15
                logger.warning(f"Detected potentially unsafe phrase: {phrase}")
        
        # Lower confidence for critical urgency
        if urgency == "critical":
            confidence -= 0.1
        
        # Ensure confidence is in valid range
        return max(0.0, min(1.0, confidence))


# Singleton instance
reply_generator_service = ReplyGeneratorService()
