"""
Data Engineering Interview Prep Chatbot - Streamlit Application
A conversational chatbot using RAG for interview preparation.

This is a thin UI layer - all business logic is in services.
Uses LLM-driven intent routing instead of hard-coded rules.
"""

import streamlit as st
from typing import Optional
from enum import Enum
from pydantic import BaseModel, Field

from config.settings import AVAILABLE_TOPICS
from core.models import Topic, MessageRole, ConversationState, ChatMessage
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
    
    if "chat_service" not in st.session_state:
        _init_chat_service()


def _init_chat_service() -> None:
    """Initialize the chat service with dependencies."""
    try:
        with st.spinner("🔄Initializing AI system..."):
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
            st.session_state.selected_topic = None
            st.rerun()
        
        st.markdown("---")
        if st.session_state.selected_topic:
            st.caption(f"📍 Current Topic: {st.session_state.selected_topic}")
        else:
            st.caption("📍 No topic selected")


def render_welcome() -> None:
    """Display welcome message."""
    welcome = """👋 **Welcome! I'm here to help you prepare for Data Engineering interviews.**

I can provide:
- ✅ Practice interview questions (Entry/Mid/Advanced)
- ✅ Key competencies with definitions and examples
- ✅ Context-aware answers to your questions

**Available Topics:** 🐍 Python | 💾 SQL | 🗄️ Database | 🔄 ETL DataWarehouse

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
# INTENT ROUTING - LLM-Driven (No Hard-coded Rules)
# =============================================================================

class UserIntent(str, Enum):
    """Possible user intents - extensible without code changes."""
    GREETING = "greeting"
    SELECT_TOPIC = "select_topic"
    GENERATE_PRACTICE = "generate_practice"
    ASK_QUESTION = "ask_question"
    CHANGE_TOPIC = "change_topic"
    SELECT_OPTION = "select_option"  # User selecting from presented choices
    UNKNOWN = "unknown"


class IntentAnalysis(BaseModel):
    """
    Structured output from LLM intent classifier.
    
    This replaces all hard-coded rule functions like _wants_practice(),
    _wants_topic_change(), etc.
    """
    intent: UserIntent = Field(
        description="The primary intent/action the user wants to perform"
    )
    topic: Optional[str] = Field(
        None,
        description="Detected topic: 'Python', 'SQL', 'Database', 'ETL', 'Projects', or None if not mentioned"
    )
    standalone_query: str = Field(
        description="A standalone, context-aware rephrasing of the user's message suitable for retrieval. "
                    "MUST include full context from conversation when user is making a selection or follow-up"
    )
    selection_context: Optional[str] = Field(
        None,
        description="When user is selecting from options, describe what they selected (e.g., 'ELT project details')"
    )
    confidence: float = Field(
        ge=0.0, le=1.0,
        description="Confidence score for the intent classification (0-1)"
    )


def classify_intent(user_message: str, current_topic: Optional[str], recent_messages: list) -> IntentAnalysis:
    """
    Use LLM to classify user intent and extract entities.
    
    This is the SINGLE decision point that replaces all rule-based branching.
    
    Args:
        user_message: The user's input
        current_topic: Currently selected topic (if any)
        recent_messages: Recent conversation history for context
        
    Returns:
        IntentAnalysis with intent, topic, and standalone query
    """
    llm = get_llm()
    
    # Create a structured output LLM
    structured_llm = llm.with_structured_output(IntentAnalysis)
    
    # Build conversation history context - INCLUDE FULL CONTENT for proper context
    # Use up to 500 chars per message to capture enough context for selections
    history_context = "\n".join([
        f"{msg['role'].title()}: {msg['content'][:500]}" + ("..." if len(msg['content']) > 500 else "")
        for msg in recent_messages[-4:]
    ]) if recent_messages else "No previous conversation"
    
    # Context-aware classification prompt
    classification_prompt = f"""Analyze this user message and determine their intent in a Data Engineering interview prep chatbot.

Current Context:
- Selected Topic: {current_topic or 'None selected'}
- Recent Conversation:
{history_context}

User Message: "{user_message}"

Intent Categories:
- greeting: Initial hello, general inquiry, or casual conversation starter
- select_topic: User wants to choose or learn about a specific topic (Python, SQL, Database, ETL)
- generate_practice: User wants practice questions, interview prep, or topic overview
- ask_question: User has a specific technical question about a concept
- change_topic: User wants to switch to a different topic or explore other areas
- select_option: User is SELECTING from options/choices that were just presented by the assistant (IMPORTANT: use this when assistant gave choices and user picks one)
- unknown: Intent unclear or off-topic

CRITICAL RULES FOR select_option:
- If the assistant just presented choices (like "ELT OR ETL", "option 1 or 2", etc.) and user responds with one of the options, this is select_option
- The standalone_query MUST reference what they are selecting (e.g., "Show details for the ELT project" not just "What is ELT")
- Set selection_context to describe what was selected

Instructions:
1. Determine the PRIMARY intent - look for selection patterns first!
2. Extract any mentioned topic (Python, SQL, Database, ETL, Projects)
3. Create a standalone query by rephrasing with FULL context from conversation
4. If user is making a selection, set selection_context
5. Provide a confidence score

Examples:
- "Python" (no prior context) → intent=select_topic, topic=Python, standalone="Select Python topic for interview practice"
- "Give me practice questions" → intent=generate_practice, topic={current_topic}, standalone="Generate practice interview questions for {current_topic or 'data engineering'}"
- "What are list comprehensions?" → intent=ask_question, standalone="What are list comprehensions in Python and how are they used in data engineering?"
- "Let's try SQL instead" → intent=change_topic, topic=SQL, standalone="Change topic to SQL"
- (After assistant says "2 choices: ELT or ETL project") User: "elt" → intent=select_option, topic=Projects, standalone="Show me the ELT project details", selection_context="ELT project from the offered choices"
- (After assistant offers options A or B) User: "A" or "first one" → intent=select_option, standalone="Provide details for option A that was offered"

Respond with the structured analysis."""

    try:
        result = structured_llm.invoke(classification_prompt)
        return result
    except Exception as e:
        # Fallback to safe default
        return IntentAnalysis(
            intent=UserIntent.ASK_QUESTION,
            topic=current_topic,
            standalone_query=user_message,
            selection_context=None,
            confidence=0.5
        )


def detect_topic(text: str) -> Optional[Topic]:
    """Detect topic from user message (kept for backward compatibility)."""
    return Topic.from_string(text)


def handle_message(user_input: str) -> None:
    """
    Process user input using LLM-driven intent classification.
    
    NO HARD-CODED RULES - All decisions made by LLM structured output.
    This makes the system more maintainable, extensible, and robust.
    
    Args:
        user_input: The user's message
    """
    chat_service = get_chat_service()
    
    # Get recent conversation history for context
    recent_messages = st.session_state.messages[-5:] if st.session_state.messages else []
    
    # LLM-driven intent classification (replaces all rule-based branching)
    with st.spinner("🤔 Understanding your request..."):
        intent_result = classify_intent(
            user_input,
            st.session_state.selected_topic,
            recent_messages
        )
    
    # Declarative intent-to-action mapping (extensible without code changes)
    action_handlers = {
        UserIntent.GREETING: _handle_greeting,
        UserIntent.SELECT_TOPIC: _handle_topic_selection_from_intent,
        UserIntent.GENERATE_PRACTICE: _handle_practice_request,
        UserIntent.ASK_QUESTION: _handle_question,
        UserIntent.CHANGE_TOPIC: _handle_topic_change,
        UserIntent.SELECT_OPTION: _handle_selection,  # New: handle user selections from offered choices
        UserIntent.UNKNOWN: _handle_unknown,
    }
    
    # Route to appropriate handler
    handler = action_handlers.get(intent_result.intent, _handle_unknown)
    handler(intent_result, chat_service)


# =============================================================================
# INTENT HANDLERS - Declarative action functions
# =============================================================================

def _handle_greeting(intent: IntentAnalysis, chat_service: ChatService) -> None:
    """Handle greeting intent."""
    add_message("assistant", 
        "Hello! Type a **topic name** (Python, SQL, Database, ETL) to start practicing, "
        "or ask any data engineering question!")


def _handle_topic_selection_from_intent(intent: IntentAnalysis, chat_service: ChatService) -> None:
    """Handle topic selection intent with LLM-extracted topic."""
    if intent.topic:
        topic = Topic.from_string(intent.topic)
        if topic:
            st.session_state.selected_topic = topic.value
            _generate_practice(chat_service)
            return
    
    # No valid topic detected - prompt user
    render_topic_prompt()


def _handle_practice_request(intent: IntentAnalysis, chat_service: ChatService) -> None:
    """Handle practice question generation request."""
    if st.session_state.selected_topic:
        # Generate for current topic
        _generate_practice(chat_service)
    elif intent.topic:
        # Topic mentioned in request - use it
        topic = Topic.from_string(intent.topic)
        if topic:
            st.session_state.selected_topic = topic.value
            _generate_practice(chat_service)
        else:
            render_topic_prompt()
    else:
        # Need topic selection
        render_topic_prompt()


def  _handle_question(intent: IntentAnalysis, chat_service: ChatService) -> None:
    """Handle technical question using standalone query."""
    topic = None
    if st.session_state.selected_topic:
        topic = Topic.from_string(st.session_state.selected_topic)
    elif intent.topic:
        # Use LLM-detected topic if available
        topic = Topic.from_string(intent.topic)
    
    with st.spinner("Thinking..."):
        # Use the LLM-generated standalone query for better retrieval
        response = chat_service.answer_question(intent.standalone_query, topic=topic)
    
    add_message("assistant", response.content)


def _handle_topic_change(intent: IntentAnalysis, chat_service: ChatService) -> None:
    """Handle topic change request."""
    if intent.topic:
        topic = Topic.from_string(intent.topic)
        if topic and topic.value != st.session_state.selected_topic:
            # Switch to new topic
            st.session_state.selected_topic = topic.value
            _generate_practice(chat_service)
            return
    
    # Prompt for topic selection
    st.session_state.selected_topic = None
    render_topic_prompt()


def _handle_unknown(intent: IntentAnalysis, chat_service: ChatService) -> None:
    """Handle unknown/unclear intent - try to answer as question."""
    # Graceful fallback - treat as question
    _handle_question(intent, chat_service)


def _handle_selection(intent: IntentAnalysis, chat_service: ChatService) -> None:
    """
    Handle user selecting from options presented by the assistant.
    
    This is critical for maintaining conversation context when the bot
    offers choices and the user picks one.
    """
    # Build conversation state for context
    conversation = _build_conversation_state()
    
    # Determine topic - check for Projects or use detected/current topic
    topic = None
    if intent.topic:
        topic = Topic.from_string(intent.topic)
    if not topic and st.session_state.selected_topic:
        topic = Topic.from_string(st.session_state.selected_topic)
    
    with st.spinner("Getting details for your selection..."):
        # Use the context-aware standalone query which should reference the selection
        response = chat_service.answer_question(
            intent.standalone_query,
            conversation=conversation,
            topic=topic
        )
    
    add_message("assistant", response.content)


def _build_conversation_state() -> ConversationState:
    """
    Build a ConversationState object from Streamlit session messages.
    
    This bridges the gap between Streamlit's simple message storage
    and the ChatService's ConversationState model.
    """
    state = ConversationState()
    
    # Set topic if selected
    if st.session_state.selected_topic:
        state.selected_topic = Topic.from_string(st.session_state.selected_topic)
    
    # Convert session messages to ChatMessages
    for msg in st.session_state.messages:
        role = MessageRole.USER if msg["role"] == "user" else MessageRole.ASSISTANT
        state.add_message(role, msg["content"])
    
    return state


def _handle_topic_selection(topic: Topic, chat_service: ChatService) -> None:
    """Handle topic selection and generate practice content."""
    st.session_state.selected_topic = topic.value
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

        # TODO (Karina):
        # Process and respond using LLM-driven intent routing
        # SOLVED: Replaced hard-coded rules with structured LLM output
        # - Intent classification via structured output (Pydantic)
        # - Query transformation for standalone queries
        # - Declarative action handlers
        # - Easy to extend with new intents
        handle_message(prompt)
        
        # Refresh to show new messages
        st.rerun()


if __name__ == "__main__":
    main()
