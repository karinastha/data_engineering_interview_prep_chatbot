"""
Prompts package for the Data Engineering Interview Prep Chatbot.

Centralized prompt management. All prompt templates are defined here,
separate from business logic.

Usage:
    from prompts import SYSTEM_PROMPT, get_preprocessing_prompt
    from prompts import QA_PROMPT_TEMPLATE
"""

from prompts.preprocessing import PREPROCESSING_PROMPT, get_preprocessing_prompt
from prompts.system import SYSTEM_PROMPT
from prompts.templates import QA_PROMPT_TEMPLATE

__all__ = [
    "PREPROCESSING_PROMPT",
    "QA_PROMPT_TEMPLATE",
    "SYSTEM_PROMPT",
    "get_preprocessing_prompt",
]
