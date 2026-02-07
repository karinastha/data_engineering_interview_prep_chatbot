"""
Data Engineering Interview Prep Chatbot - Streamlit Application V0

Simplified version:
- No intent classification
- Single RAG flow for all messages  
- Proper conversation history support
"""

import streamlit as st
from typing import Optional

from config.topics import get_topic_names, get_topic_display_string, TOPICS
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


def add_message(role: str, content: str, sources: list = None) -> None:
    """Add a message to conversation history with optional sources."""
    message = {"role": role, "content": content}
    if sources:
        message["sources"] = sources
    st.session_state.messages.append(message)


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
        for topic in TOPICS:
            st.markdown(f"{topic.display_name}")
        
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
    topic_display = get_topic_display_string()
    
    welcome = f"""👋 **Welcome! I'm here to help you prepare for Data Engineering interviews.**

I can help with:
- ✅ Practice interview questions (Entry/Mid/Advanced levels)
- ✅ Technical concepts with examples
- ✅ Leapfrog competency-based preparation

**Topics:** {topic_display}

**Just ask me anything!** For example:
- "Give me Python interview questions"
- "Explain window functions in SQL"
- "What should I know about database indexing?"
"""
    add_message("assistant", welcome)


def render_content_with_mermaid(content: str) -> None:
    """
    Render content that may contain mermaid diagrams.
    
    Splits content into markdown and mermaid parts,
    rendering each appropriately with proper formatting.
    """
    from utils.text_processing import split_content_with_mermaid, post_process_markdown
    
    parts = split_content_with_mermaid(content)
    
    for part in parts:
        if part["type"] == "markdown":
            # Apply post-processing to fix Streamlit markdown rendering
            formatted_content = post_process_markdown(part["content"])
            st.markdown(formatted_content)
        elif part["type"] == "mermaid":
            try:
                import streamlit_mermaid as stmd
                stmd.st_mermaid(part["content"])
            except Exception as e:
                # Fallback: show as code block if mermaid fails
                st.code(part["content"], language="mermaid")


def render_sources_used(sources: list) -> None:
    """
    Display retrieved vector database chunks as expandable sources.
    Shows users exactly which documents were used to generate the answer.
    """
    if not sources:
        return
    
    with st.expander(f"📖 **Sources Used** ({len(sources)} chunks from vector database)", expanded=False):
        for i, source in enumerate(sources, 1):
            with st.container():
                # Create columns for source info
                col1, col2 = st.columns([1, 4])
                
                with col1:
                    # Source number and relevance score
                    st.metric(
                        label=f"Source {i}",
                        value=f"{source.score:.0%}",
                        help="Relevance score from vector similarity search"
                    )
                
                with col2:
                    # Source details
                    st.write(f"**{source.topic}** - {source.subtopic}")
                    st.caption(f"📄 {source.metadata.get('source', 'Unknown file')}")
                    
                    # Content preview
                    if hasattr(source, 'content') and source.content:
                        preview = source.content[:300] + "..." if len(source.content) > 300 else source.content
                        st.code(preview, language=None)
                
                if i < len(sources):  # Add separator except for last item
                    st.divider()


def render_chat_messages() -> None:
    """Render all chat messages with mermaid support."""
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            render_content_with_mermaid(message["content"])
            # Display sources if available (stored in metadata)
            if message.get("sources"):
                render_sources_used(message["sources"])


# =============================================================================
# MESSAGE HANDLING - With streaming support
# =============================================================================

def handle_message_streaming(user_input: str) -> None:
    """
    Process user input with streaming response.
    
    Flow:
    1. Get conversation history
    2. Call chat service streaming (preprocess → retrieve → stream generate)
    3. Display tokens as they arrive (markdown only during stream)
    4. Re-render with mermaid support and show sources after completion
    """
    from utils.text_processing import post_process_markdown
    
    chat_service = get_chat_service()
    history = get_history()
    
    with st.chat_message("assistant"):
        # Use placeholder for streaming
        response_placeholder = st.empty()
        full_response = ""
        
        for chunk in chat_service.answer_stream(
            message=user_input,
            history=history,
        ):
            full_response += chunk
            # Show response with typing indicator (with post-processing for proper formatting)
            response_placeholder.markdown(post_process_markdown(full_response) + "▌")
        
        # Clear placeholder and render with mermaid support
        # render_content_with_mermaid will apply post_process_markdown internally
        response_placeholder.empty()
        render_content_with_mermaid(full_response)
        
        # Get sources from the completed response
        rag_response = chat_service.get_last_response()
        if rag_response and rag_response.sources:
            render_sources_used(rag_response.sources)
    
    # Store the RAW response (without post-processing) so it can be properly formatted on re-render
    rag_response = chat_service.get_last_response()
    sources = rag_response.sources if rag_response else None
    add_message("assistant", full_response, sources)


def handle_message(user_input: str) -> None:
    """
    Process user input through RAG pipeline (non-streaming fallback).
    
    Simple flow:
    1. Get conversation history
    2. Call chat service (preprocess → retrieve → generate)
    3. Display response with sources
    """
    chat_service = get_chat_service()
    history = get_history()
    
    with st.spinner("🤔 Thinking..."):
        response = chat_service.answer(
            message=user_input,
            history=history,
        )
    
    # Display response with sources
    # render_content_with_mermaid will apply post_process_markdown internally
    with st.chat_message("assistant"):
        render_content_with_mermaid(response.content)
        if response.sources:
            render_sources_used(response.sources)
    
    # Store RAW content (without post-processing) for proper re-rendering from history
    add_message("assistant", response.content, response.sources)


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
        
        # Process and respond with streaming
        handle_message_streaming(prompt)
        
        # Refresh to show new messages in history
        st.rerun()


if __name__ == "__main__":
    main()
