"""
Data Engineering Interview Prep Chatbot - Streamlit Application V0

Simplified version:
- No intent classification
- Single RAG flow for all messages  
- Proper conversation history support
"""

import streamlit as st
from typing import Optional

from config.settings import AVAILABLE_TOPICS
from core.models import Topic
from services.ingestion import IngestionService
from services.retrieval import RetrievalService
from services.chat_v0 import ChatService
from utils.helper_cred import get_llm, get_embeddings
from utils.logging import setup_logging

# Setup logging
setup_logging()

# Page configuration
st.set_page_config(
    page_title="DE Interview Prep Assistant",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =============================================================================
# SESSION STATE MANAGEMENT
# =============================================================================

def init_session_state() -> None:
    """Initialize session state variables."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "chat_service" not in st.session_state:
        _init_chat_service()


def _init_chat_service() -> None:
    """Initialize the chat service with dependencies."""
    try:
        with st.spinner("🔄 Initializing AI system..."):
            # Initialize components
            embeddings = get_embeddings()
            llm = get_llm()
            
            # Initialize vector store
            ingestion = IngestionService(embeddings)
            vectorstore = ingestion.initialize()
            
            # Create services
            retrieval = RetrievalService(vectorstore)
            st.session_state.chat_service = ChatService(llm, retrieval)
        
        st.success("✅ Chatbot ready!")
        
    except Exception as e:
        st.error(f"❌ Failed to initialize: {str(e)}")
        st.info("💡 Ensure AWS credentials are configured in .env file")
        st.stop()


def add_message(role: str, content: str) -> None:
    """Add a message to conversation history."""
    st.session_state.messages.append({"role": role, "content": content})


def get_history() -> list:
    """Get conversation history for chat service."""
    return st.session_state.messages


def get_chat_service() -> ChatService:
    """Get the chat service from session state."""
    return st.session_state.chat_service


# =============================================================================
# UI COMPONENTS
# =============================================================================

def render_header() -> None:
    """Render application header."""
    st.markdown("""
    <div style='text-align: center; padding: 1rem; background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); border-radius: 10px; margin-bottom: 2rem;'>
        <h1 style='color: white; margin: 0;'>💼 DATA ENGINEERING INTERVIEW PREP</h1>
        <p style='color: #f0f0f0; margin: 0.5rem 0 0 0;'>Powered by Amazon Nova Lite & LangChain</p>
    </div>
    """, unsafe_allow_html=True)


def render_sidebar() -> None:
    """Render sidebar with info and controls."""
    with st.sidebar:
        st.markdown("### 📚 About")
        st.markdown("""
        Prepare for Data Engineering interviews with:
        - Practice questions at all levels
        - Leapfrog competency framework
        - Context-aware responses
        """)
        
        st.markdown("---")
        
        st.markdown("### 🎯 Topics")
        for topic in AVAILABLE_TOPICS:
            st.markdown(f"📌 {topic}")
        
        st.markdown("---")
        
        st.markdown("### 💡 Example Questions")
        st.markdown("""
        - "Give me Python interview questions"
        - "Explain SQL joins with examples"
        - "What are ETL best practices?"
        - "More scenario-based questions"
        """)
        
        st.markdown("---")
        
        if st.button("🔄 Reset Conversation", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
        
        st.markdown("---")
        st.caption(f"💬 Messages: {len(st.session_state.messages)}")


def render_welcome() -> None:
    """Display welcome message."""
    welcome = """👋 **Welcome! I'm here to help you prepare for Data Engineering interviews.**

I can help with:
- ✅ Practice interview questions (Entry/Mid/Advanced levels)
- ✅ Technical concepts with examples
- ✅ Leapfrog competency-based preparation

**Topics:** 🐍 Python | 💾 SQL | 🗄️ Database | 🔄 ETL

**Just ask me anything!** For example:
- "Give me Python interview questions"
- "Explain window functions in SQL"
- "What should I know about database indexing?"
"""
    add_message("assistant", welcome)


def render_chat_messages() -> None:
    """Render all chat messages."""
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])


# =============================================================================
# MESSAGE HANDLING - Simplified, no intent routing
# =============================================================================

def handle_message(user_input: str) -> None:
    """
    Process user input through RAG pipeline.
    
    Simple flow:
    1. Get conversation history
    2. Call chat service (preprocess → retrieve → generate)
    3. Display response
    """
    chat_service = get_chat_service()
    history = get_history()
    
    with st.spinner("🤔 Thinking..."):
        response = chat_service.answer(
            message=user_input,
            history=history,  # Pass full conversation history
        )
    
    add_message("assistant", response.content)


# =============================================================================
# MAIN APPLICATION
# =============================================================================

def main() -> None:
    """Main application entry point."""
    # Initialize
    init_session_state()
    
    # Render UI
    render_header()
    render_sidebar()
    
    # Show welcome on first load
    if not st.session_state.messages:
        render_welcome()
    
    # Display chat history
    render_chat_messages()
    
    # Chat input
    if prompt := st.chat_input("Ask me anything about data engineering interviews..."):
        # Show user message
        add_message("user", prompt)
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Process and respond
        handle_message(prompt)
        
        # Refresh to show new messages
        st.rerun()


if __name__ == "__main__":
    main()
