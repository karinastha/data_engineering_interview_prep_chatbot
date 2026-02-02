"""
Data Engineering Interview Prep Chatbot - Streamlit Application
A conversational chatbot using RAG for interview preparation.

This is a thin UI layer - all business logic is in services.
"""

import streamlit as st
from typing import Optional

from config.settings import AVAILABLE_TOPICS
from core.models import Topic, ConversationStage, MessageRole
from services.ingestion import IngestionService
from services.retrieval import RetrievalService
from services.chat import ChatService
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
    
    if "selected_topic" not in st.session_state:
        st.session_state.selected_topic = None
    
    if "stage" not in st.session_state:
        st.session_state.stage = ConversationStage.GREETING
    
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
        - Key competencies with examples
        - Context-aware responses
        """)
        
        st.markdown("---")
        
        st.markdown("### 🎯 Topics")
        for topic in AVAILABLE_TOPICS:
            if st.session_state.selected_topic == topic:
                st.markdown(f"✅ **{topic}** (Current)")
            else:
                st.markdown(f"📌 {topic}")
        
        st.markdown("---")
        
        st.markdown("### 💡 Quick Tips")
        st.markdown("""
        - Type a topic name to start
        - Ask specific questions
        - Say "more topics" to switch
        """)
        
        st.markdown("---")
        
        if st.button("🔄 Reset Conversation", use_container_width=True):
            st.session_state.messages = []
            st.session_state.stage = ConversationStage.GREETING
            st.session_state.selected_topic = None
            st.rerun()
        
        st.markdown("---")
        st.caption(f"Stage: {st.session_state.stage.value}")
        if st.session_state.selected_topic:
            st.caption(f"Topic: {st.session_state.selected_topic}")


def render_welcome() -> None:
    """Display welcome message."""
    welcome = """👋 **Welcome! I'm here to help you prepare for Data Engineering interviews.**

I can provide:
- ✅ Practice interview questions (Entry/Mid/Advanced)
- ✅ Key competencies with definitions and examples
- ✅ Context-aware answers to your questions

**Available Topics:** 🐍 Python | 💾 SQL | 🗄️ Database | 🔄 ETL

**To start, just type a topic name** (e.g., "Python") **or ask a question!**
"""
    add_message("assistant", welcome)


def render_topic_prompt() -> None:
    """Prompt user to select a topic."""
    prompt = """**Which topic would you like to practice?**

Select by typing the name:
- 🐍 **Python** - Data engineering with Python
- 💾 **SQL** - Queries and database operations  
- 🗄️ **Database** - Design and optimization
- 🔄 **ETL** - Pipelines and transformations
"""
    add_message("assistant", prompt)


def render_chat_messages() -> None:
    """Render all chat messages."""
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])


# =============================================================================
# MESSAGE HANDLING
# =============================================================================

def detect_topic(text: str) -> Optional[Topic]:
    """Detect topic from user message."""
    return Topic.from_string(text)


def handle_message(user_input: str) -> None:
    """
    Process user input and generate response.
    
    Routes to appropriate handler based on conversation stage.
    """
    stage = st.session_state.stage
    chat_service = get_chat_service()
    
    # Check for topic change request
    if _wants_topic_change(user_input):
        st.session_state.stage = ConversationStage.TOPIC_SELECTION
        st.session_state.selected_topic = None
        render_topic_prompt()
        return
    
    # Try to detect topic in message
    detected_topic = detect_topic(user_input)
    
    # Stage: Greeting - initial interaction
    if stage == ConversationStage.GREETING:
        if detected_topic:
            _handle_topic_selection(detected_topic, chat_service)
        elif _wants_practice(user_input):
            st.session_state.stage = ConversationStage.TOPIC_SELECTION
            render_topic_prompt()
        else:
            add_message("assistant", 
                "Hello! Type a **topic name** (Python, SQL, Database, ETL) to start practicing, "
                "or ask any data engineering question!")
    
    # Stage: Topic Selection
    elif stage == ConversationStage.TOPIC_SELECTION:
        if detected_topic:
            _handle_topic_selection(detected_topic, chat_service)
        else:
            add_message("assistant", 
                "Please choose a topic: **Python**, **SQL**, **Database**, or **ETL**")
    
    # Stage: Active Practice
    elif stage == ConversationStage.PRACTICING:
        if detected_topic and detected_topic.value != st.session_state.selected_topic:
            # Switching to new topic
            _handle_topic_selection(detected_topic, chat_service)
        elif _wants_more_questions(user_input):
            # Generate more questions for current topic
            _generate_practice(chat_service)
        else:
            # Answer the question
            _answer_question(user_input, chat_service)


def _wants_topic_change(text: str) -> bool:
    """Check if user wants to change topics."""
    keywords = ["more topics", "other topic", "change topic", "different topic", "switch"]
    return any(kw in text.lower() for kw in keywords)


def _wants_practice(text: str) -> bool:
    """Check if user wants practice questions."""
    keywords = ["practice", "question", "help", "prepare", "interview", "start"]
    return any(kw in text.lower() for kw in keywords)


def _wants_more_questions(text: str) -> bool:
    """Check if user wants more practice questions."""
    keywords = ["more questions", "practice questions", "list", "scenario"]
    return any(kw in text.lower() for kw in keywords)


def _handle_topic_selection(topic: Topic, chat_service: ChatService) -> None:
    """Handle topic selection and generate practice content."""
    st.session_state.selected_topic = topic.value
    st.session_state.stage = ConversationStage.PRACTICING
    _generate_practice(chat_service)


def _generate_practice(chat_service: ChatService) -> None:
    """Generate practice questions for current topic."""
    topic = Topic.from_string(st.session_state.selected_topic)
    
    with st.spinner(f"🔍 Generating {topic.value} practice content..."):
        response = chat_service.generate_practice_questions(topic)
    
    if response.is_success:
        add_message("assistant", response.content)
        add_message("assistant", 
            f"\n---\n💡 Ask me specific questions about {topic.value}, "
            "or say **'more topics'** to explore other areas!")
    else:
        add_message("assistant", f"⚠️ {response.content}")


def _answer_question(question: str, chat_service: ChatService) -> None:
    """Answer a user question using RAG."""
    topic = None
    if st.session_state.selected_topic:
        topic = Topic.from_string(st.session_state.selected_topic)
    
    with st.spinner("💭 Thinking..."):
        response = chat_service.answer_question(question, topic=topic)
    
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
    if prompt := st.chat_input("Type your message..."):
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
