"""Prompts package."""
from app.prompts.classifier import CLASSIFIER_SYSTEM_PROMPT, get_classifier_prompt
from app.prompts.reply import REPLY_SYSTEM_PROMPT, get_reply_prompt

__all__ = [
    "CLASSIFIER_SYSTEM_PROMPT",
    "get_classifier_prompt",
    "REPLY_SYSTEM_PROMPT",
    "get_reply_prompt"
]
