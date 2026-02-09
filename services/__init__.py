"""Services package initialization."""

from services.ingestion import IngestionService
from services.retrieval import RetrievalService

# Try to import from chat.py, fallback to chat_v0.py if not available
try:
    from services.chat import ChatService, create_chat_service
except ImportError:
    # chat.py may be commented out, use chat_v0.py instead
    from services.chat import ChatService
    create_chat_service = None  # Not available in v0

__all__ = [
    "IngestionService",
    "RetrievalService", 
    "ChatService",
    "create_chat_service",
]
