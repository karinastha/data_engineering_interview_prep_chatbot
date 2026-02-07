"""
Configuration Settings Module
Centralized configuration for the Data Engineering Interview Prep Chatbot.

All configuration values are defined here to avoid scattered magic numbers
and enable environment-based configuration.
"""

import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Environment(Enum):
    """Application environment modes."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


@dataclass(frozen=True)
class AWSConfig:
    """AWS-specific configuration settings."""
    region: str = field(default_factory=lambda: os.getenv("AWS_REGION", "us-east-1"))
    access_key_id: Optional[str] = field(default_factory=lambda: os.getenv("aws_access_key_id"))
    secret_access_key: Optional[str] = field(default_factory=lambda: os.getenv("aws_secret_access_key"))
    session_token: Optional[str] = field(default_factory=lambda: os.getenv("aws_session_token"))
    
    def validate(self) -> bool:
        """Validate required AWS credentials are present."""
        return all([self.access_key_id, self.secret_access_key])


@dataclass(frozen=True)
class LLMConfig:
    """LLM configuration settings for Amazon Bedrock."""
    model_id: str = "amazon.nova-lite-v1:0"
    temperature: float = 0.5
    max_tokens: int = 1500
    
    # Response validation
    min_response_length: int = 50
    max_retries: int = 2


@dataclass(frozen=True)
class RAGConfig:
    """RAG retrieval configuration settings."""
    # Retrieval parameters
    top_k: int = 4  # Number of documents to retrieve
    similarity_threshold: float = 0.4  # Minimum similarity score (0-1), ~0.5 for L2 distance=1.0
    max_topic_docs: int = 6  # Max docs for topic-specific queries
    
    # Context formatting
    max_context_length: int = 3000  # Max chars of context to include
    max_chat_history_messages: int = 4  # Recent messages to include
    max_message_preview_length: int = 200  # Truncate long messages in history


@dataclass(frozen=True)
class EmbeddingConfig:
    """Embedding model configuration."""
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    device: str = "cpu"
    normalize_embeddings: bool = True


@dataclass(frozen=True)
class VectorStoreConfig:
    """Vector store configuration settings."""
    collection_name: str = "de_interview_prep"
    persist_directory: str = "data/vector_db"


@dataclass(frozen=True)
class DataConfig:
    """Data source configuration."""
    raw_docs_directory: str = "data/raw_docs"
    projects_directory: str = "data/real_world_projects"
    
    # CSV file mapping is now defined in config/topics.py
    # Use get_csv_file_mapping() to get the mapping
    
    @property
    def csv_files(self) -> dict:
        """Get CSV file mapping from topics config (single source of truth)."""
        from config.topics import get_csv_file_mapping
        return get_csv_file_mapping()
    
    @property
    def project_files(self) -> dict:
        """Mapping of project type to markdown filename."""
        return {
            "ETL": "ETL_INSIGHTS.md",
            "ELT": "ELT_DBT.md",
        }


@dataclass
class AppConfig:
    """Main application configuration container."""
    
    # Environment
    env: Environment = field(
        default_factory=lambda: Environment(os.getenv("APP_ENV", "development"))
    )
    debug: bool = field(default_factory=lambda: os.getenv("DEBUG", "false").lower() == "true")
    
    # Component configs
    aws: AWSConfig = field(default_factory=AWSConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    rag: RAGConfig = field(default_factory=RAGConfig)
    embedding: EmbeddingConfig = field(default_factory=EmbeddingConfig)
    vector_store: VectorStoreConfig = field(default_factory=VectorStoreConfig)
    data: DataConfig = field(default_factory=DataConfig)
    
    # Paths
    project_root: Path = field(default_factory=lambda: Path(__file__).parent.parent)
    
    def get_data_path(self) -> Path:
        """Get absolute path to data directory."""
        return self.project_root / self.data.raw_docs_directory
    
    def get_vector_store_path(self) -> Path:
        """Get absolute path to vector store directory."""
        return self.project_root / self.vector_store.persist_directory
    
    def validate(self) -> list[str]:
        """
        Validate configuration and return list of issues.
        
        Returns:
            List of validation error messages (empty if valid)
        """
        issues = []
        
        if not self.aws.validate():
            issues.append("AWS credentials not configured. Set aws_access_key_id and aws_secret_access_key.")
        
        if not self.get_data_path().exists():
            issues.append(f"Data directory not found: {self.get_data_path()}")
        
        return issues


# Global configuration instance (singleton pattern)
_config: Optional[AppConfig] = None


def get_config() -> AppConfig:
    """
    Get the application configuration singleton.
    
    Returns:
        AppConfig instance with all settings loaded
    """
    global _config
    if _config is None:
        _config = AppConfig()
    return _config


def reset_config() -> None:
    """Reset configuration (useful for testing)."""
    global _config
    _config = None


# Available topics - now defined in config/topics.py (single source of truth)
# Import from there: from config.topics import get_topic_names, TOPICS

def get_available_topics() -> list[str]:
    """Get available topics from the centralized config."""
    from config.topics import get_topic_names
    return get_topic_names()

# Backward compatibility alias
AVAILABLE_TOPICS = property(lambda self: get_available_topics())
