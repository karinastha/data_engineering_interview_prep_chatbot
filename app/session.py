"""Session state management for the Streamlit application."""

import streamlit as st

from services.chat import ChatService
from services.generation import GenerationService
from services.ingestion import IngestionService
from services.preprocessing import PreprocessingService
from services.retrieval import RetrievalService
from utils.helper_cred import get_embeddings, get_llm


def init_session_state() -> None:
    """Initialize session state variables."""
    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "chat_service" not in st.session_state:
        _init_chat_service()


def _init_chat_service() -> None:
    """Initialize the chat service with dependencies."""
    with st.spinner("🔄 Initializing AI system..."):
        embeddings = get_embeddings()
        llm = get_llm()

        # Initialize infrastructure
        ingestion = IngestionService(embeddings)
        vectorstore = ingestion.initialize()

        # Create services with proper dependency injection
        retrieval = RetrievalService(vectorstore)
        preprocessing = PreprocessingService(llm)
        generation = GenerationService(llm, retrieval)

        # Inject all dependencies into ChatService
        st.session_state.chat_service = ChatService(
            preprocessing_service=preprocessing,
            generation_service=generation,
            retrieval_service=retrieval,
        )

    st.success("✅ Chatbot ready!")


def add_message(
    role: str,
    content: str,
    sources: list | None = None,
    project_resource_types: list[str] | None = None,
) -> None:
    """Add a message to conversation history with optional sources."""
    message = {"role": role, "content": content}
    if sources:
        message["sources"] = sources
    if project_resource_types:
        message["project_resource_types"] = project_resource_types
    st.session_state.messages.append(message)


def get_history() -> list:
    """Get conversation history for chat service."""
    return st.session_state.messages


def get_chat_service() -> ChatService:
    """Get the chat service from session state."""
    return st.session_state.chat_service


def reset_conversation() -> None:
    """Reset the conversation history."""
    st.session_state.messages = []
