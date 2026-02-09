"""
Core Domain Models
Data structures and enums used throughout the application.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class Topic(Enum):
    """
    Available interview preparation topics.

    NOTE: Topic definitions are managed in config/topics.py (single source of truth).
    This enum provides a type-safe way to reference topics in code.
    When adding new topics, update config/topics.py first.
    """

    PYTHON = "Python"
    SQL = "SQL"
    DATABASE = "Database"
    ETL = "ETL"
    PROJECTS = "Projects"
    # Add new topic enum values here when adding to config/topics.py

    @classmethod
    def from_string(cls, value: str) -> Optional["Topic"]:
        """
        Parse topic from string with fuzzy matching.
        Uses centralized topic config for matching logic.

        Args:
            value: String to parse (case-insensitive)

        Returns:
            Topic enum value or None if no match

        """
        if not value:
            return None

        # Use centralized matching from topics.py
        from config.topics import match_topic
        matched_name = match_topic(value)

        if matched_name:
            # Convert matched name to enum
            try:
                return cls(matched_name)
            except ValueError:
                # Topic exists in config but not in enum yet
                return None

        return None

    @classmethod
    def list_all(cls) -> list[str]:
        """Get list of all topic values from centralized config."""
        from config.topics import get_topic_names
        return get_topic_names()


class ConversationStage(Enum):
    """Stages in the conversation flow."""

    GREETING = "greeting"
    TOPIC_SELECTION = "topic_selection"
    PRACTICING = "practicing"


class MessageRole(Enum):
    """Chat message roles."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


@dataclass
class ChatMessage:
    """
    Represents a single chat message.

    Attributes:
        role: The sender role (user/assistant/system)
        content: The message content
        timestamp: When the message was created
        metadata: Optional additional data (topic, sources, etc.)

    """

    role: MessageRole
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary for Streamlit compatibility."""
        return {
            "role": self.role.value,
            "content": self.content,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ChatMessage":
        """Create from dictionary."""
        return cls(
            role=MessageRole(data["role"]),
            content=data["content"],
            metadata=data.get("metadata", {}),
        )

    def truncate(self, max_length: int = 200) -> str:
        """Get truncated content for context windows."""
        if len(self.content) <= max_length:
            return self.content
        return self.content[:max_length] + "..."


@dataclass
class ConversationState:
    """
    Tracks the current state of a conversation session.

    Attributes:
        stage: Current conversation stage
        selected_topic: Currently selected topic (if any)
        messages: Conversation history

    """

    stage: ConversationStage = ConversationStage.GREETING
    selected_topic: Topic | None = None
    messages: list[ChatMessage] = field(default_factory=list)

    def add_message(self, role: MessageRole, content: str, **metadata) -> None:
        """Add a message to conversation history."""
        self.messages.append(ChatMessage(
            role=role,
            content=content,
            metadata=metadata,
        ))

    def get_recent_history(self, max_messages: int = 4) -> list[ChatMessage]:
        """Get recent messages for context."""
        return self.messages[-max_messages:] if self.messages else []

    def format_history_for_prompt(self, max_messages: int = 4, max_length: int = 200) -> str:
        """
        Format recent history for inclusion in prompts.

        Args:
            max_messages: Maximum number of recent messages
            max_length: Maximum length per message

        Returns:
            Formatted conversation history string

        """
        recent = self.get_recent_history(max_messages)

        if not recent:
            return "This is the start of the conversation."

        lines = []
        for msg in recent:
            role_label = "Human" if msg.role == MessageRole.USER else "Assistant"
            lines.append(f"{role_label}: {msg.truncate(max_length)}")

        return "\n".join(lines)

    def reset(self) -> None:
        """Reset conversation to initial state."""
        self.stage = ConversationStage.GREETING
        self.selected_topic = None
        self.messages.clear()


@dataclass
class RetrievalResult:
    """
    Result from document retrieval.

    Attributes:
        content: Document content
        score: Similarity score (0-1, higher is better)
        topic: Source topic
        subtopic: Specific subtopic
        metadata: Additional document metadata

    """

    content: str
    score: float
    topic: str
    subtopic: str = ""
    metadata: dict = field(default_factory=dict)

    def is_relevant(self, threshold: float = 0.3) -> bool:
        """Check if result meets relevance threshold."""
        return self.score >= threshold


@dataclass
class RAGResponse:
    """
    Response from the RAG system.

    Attributes:
        content: Generated response content
        sources: Retrieved documents used
        topic: Topic context (if any)
        error: Error message (if failed)

    """

    content: str
    sources: list[RetrievalResult] = field(default_factory=list)
    topic: Topic | None = None
    error: str | None = None

    @property
    def is_success(self) -> bool:
        """Check if response was successful."""
        return self.error is None and bool(self.content)
