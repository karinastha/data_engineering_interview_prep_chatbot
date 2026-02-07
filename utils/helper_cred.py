"""
Credentials and Model Initialization Module
Provides configured LLM and embedding instances.

Uses centralized configuration from config/settings.py
"""

import logging
from functools import lru_cache
from typing import Optional

from langchain_aws import ChatBedrock
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.language_models import BaseChatModel
from langchain_core.embeddings import Embeddings

from config.settings import get_config

logger = logging.getLogger(__name__)


class CredentialsError(Exception):
    """Raised when AWS credentials are missing or invalid."""
    pass


@lru_cache(maxsize=1)
def get_llm() -> BaseChatModel:
    """
    Get configured LLM instance (singleton pattern with caching).
    
    Returns:
        Configured ChatBedrock instance
        
    Raises:
        CredentialsError: If AWS credentials are not configured
    """
    config = get_config()
    
    if not config.aws.validate():
        raise CredentialsError(
            "AWS credentials not configured. "
            "Set aws_access_key_id and aws_secret_access_key in .env file."
        )
    
    logger.info(f"Initializing LLM: {config.llm.model_id}")
    
    return ChatBedrock(
        model_id=config.llm.model_id,
        region_name=config.aws.region,
        aws_access_key_id=config.aws.access_key_id,
        aws_secret_access_key=config.aws.secret_access_key,
        aws_session_token=config.aws.session_token,
        model_kwargs={
            "temperature": config.llm.temperature,
            "max_tokens": config.llm.max_tokens,
        }
    )


@lru_cache(maxsize=1)
def get_embeddings() -> Embeddings:
    """
    Get configured embeddings instance (singleton pattern with caching).
    
    Uses HuggingFace sentence-transformers for local, free embeddings.
    
    Returns:
        Configured HuggingFaceEmbeddings instance
    """
    config = get_config()
    
    logger.info(f"Initializing embeddings: {config.embedding.model_name}")
    
    return HuggingFaceEmbeddings(
        model_name=config.embedding.model_name,
        model_kwargs={'device': config.embedding.device},
        encode_kwargs={'normalize_embeddings': config.embedding.normalize_embeddings}
    )


# Lazy-loaded module-level instances for backward compatibility
# These are created on first access, not at import time
_llm: Optional[BaseChatModel] = None
_embeddings: Optional[Embeddings] = None


def _get_lazy_llm() -> BaseChatModel:
    """Get lazy-loaded LLM instance."""
    global _llm
    if _llm is None:
        _llm = get_llm()
    return _llm


def _get_lazy_embeddings() -> Embeddings:
    """Get lazy-loaded embeddings instance."""
    global _embeddings
    if _embeddings is None:
        _embeddings = get_embeddings()
    return _embeddings


# Module-level properties for backward compatibility with existing imports
# Usage: from utils.helper_cred import llm, embeddings
class _LazyLoader:
    """Lazy loader for module-level instances."""
    
    @property
    def llm(self) -> BaseChatModel:
        return _get_lazy_llm()
    
    @property
    def embeddings(self) -> Embeddings:
        return _get_lazy_embeddings()


_loader = _LazyLoader()

# These will trigger lazy loading when accessed
llm = property(lambda self: _get_lazy_llm())
embeddings = property(lambda self: _get_lazy_embeddings())

# For backward compatibility, expose as module attributes
def __getattr__(name: str):
    """Module-level attribute access for lazy loading."""
    if name == "llm":
        return _get_lazy_llm()
    elif name == "embeddings":
        return _get_lazy_embeddings()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    'get_llm',
    'get_embeddings', 
    'llm',
    'embeddings',
    'CredentialsError',
]