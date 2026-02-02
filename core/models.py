"""
Core Domain Models
Data structures and enums used throughout the application.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class Topic(Enum):
    """Available interview preparation topics."""
    PYTHON = "Python"
    SQL = "SQL"
    DATABASE = "Database"
    ETL = "ETL"
    
    @classmethod
    def from_string(cls, value: str) -> Optional["Topic"]:
        """
        Parse topic from string with fuzzy matching.
        
        Args:
            value: String to parse (case-insensitive)
            
        Returns:
            Topic enum value or None if no match
        """
        value_lower = value.lower().strip()
        
        # Direct matches
        topic_map = {
            "python": cls.PYTHON,
            "py": cls.PYTHON,
            "sql": cls.SQL,
            "query": cls.SQL,
            "database": cls.DATABASE,
            "db": cls.DATABASE,
            "rdbms": cls.DATABASE,
            "etl": cls.ETL,
            "pipeline": cls.ETL,
        }
        
        # Check exact match first
        if value_lower in topic_map:
            return topic_map[value_lower]
        
        # Check if any keyword is contained in the value
        for keyword, topic in topic_map.items():
            if keyword in value_lower:
                return topic
        
        return None
    
    @classmethod
    def list_all(cls) -> list[str]:
        """Get list of all topic values."""
        return [topic.value for topic in cls]


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
            metadata=data.get("metadata", {})
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
    selected_topic: Optional[Topic] = None
    messages: list[ChatMessage] = field(default_factory=list)
    
    def add_message(self, role: MessageRole, content: str, **metadata) -> None:
        """Add a message to conversation history."""
        self.messages.append(ChatMessage(
            role=role,
            content=content,
            metadata=metadata
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
    topic: Optional[Topic] = None
    error: Optional[str] = None
    
    @property
    def is_success(self) -> bool:
        """Check if response was successful."""
        return self.error is None and bool(self.content)
