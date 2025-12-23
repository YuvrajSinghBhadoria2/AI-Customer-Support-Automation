"""Intent and urgency classification service using Groq."""

import json
import logging
from groq import Groq
from app.config import settings
from app.schemas.ticket import ClassificationResult
from app.prompts.classifier import CLASSIFIER_SYSTEM_PROMPT, get_classifier_prompt

logger = logging.getLogger(__name__)


class ClassifierService:
    """Service for classifying customer support tickets."""
    
    def __init__(self):
        """Initialize Groq client."""
        self.client = Groq(api_key=settings.groq_api_key)
        self.model = settings.groq_model
    
    def classify_ticket(self, subject: str, body: str) -> ClassificationResult:
        """
        Classify a ticket's intent and urgency.
        
        Args:
            subject: Email subject line
            body: Email body content
            
        Returns:
            ClassificationResult with intent, urgency, and confidence
            
        Raises:
            Exception: If classification fails
        """
        try:
            # Generate prompt
            user_prompt = get_classifier_prompt(subject, body)
            
            # Call Groq API with low temperature for consistency
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": CLASSIFIER_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=500,
                response_format={"type": "json_object"}
            )
            
            # Parse JSON response
            result_text = response.choices[0].message.content
            result_data = json.loads(result_text)
            
            # Validate and create result
            classification = ClassificationResult(
                intent=result_data["intent"],
                urgency=result_data["urgency"],
                confidence=result_data["confidence"],
                reasoning=result_data.get("reasoning")
            )
            
            logger.info(
                f"Classified ticket: intent={classification.intent}, "
                f"urgency={classification.urgency}, confidence={classification.confidence}"
            )
            
            return classification
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            raise Exception("Invalid JSON response from LLM")
        except Exception as e:
            logger.error(f"Classification failed: {e}")
            raise Exception(f"Classification error: {str(e)}")


# Singleton instance
classifier_service = ClassifierService()
