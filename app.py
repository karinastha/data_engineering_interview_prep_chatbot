"""
Data Engineering Interview Prep Chatbot - Streamlit Application
A conversational chatbot using LangChain and Amazon Nova Lite for interview preparation
"""

import streamlit as st
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent))

from src.ingestion_csv import initialize_vector_store
from src.rag_retrieval import create_rag_system


# Page configuration
st.set_page_config(
    page_title="DE Interview Prep Assistant",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)


def initialize_session_state():
    """Initialize Streamlit session state variables"""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "selected_topic" not in st.session_state:
        st.session_state.selected_topic = None
    
    if "conversation_stage" not in st.session_state:
        st.session_state.conversation_stage = "greeting" 
    
    # Initialize RAG system with error handling
    if "rag_system" not in st.session_state:
        try:
            with st.spinner("🔄 Initializing AI system..."):
                vectorstore = initialize_vector_store()
                st.session_state.rag_system = create_rag_system(vectorstore)
            st.success("✓ Chatbot ready!")
        except Exception as e:
            st.error(f"❌ Failed to initialize chatbot: {str(e)}")
            st.info("💡 Tip: Ensure the vector store is created by running: `python src/ingestion_csv.py`")
            st.stop()


def display_header():
    """Display application header"""
    st.markdown("""
    <div style='text-align: center; padding: 1rem; background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); border-radius: 10px; margin-bottom: 2rem;'>
        <h1 style='color: white; margin: 0;'>💼 DATA ENGINEERING INTERVIEW PREP ASSISTANT</h1>
        <p style='color: #f0f0f0; margin: 0.5rem 0 0 0;'>Powered by Amazon Nova Lite & LangChain</p>
    </div>
    """, unsafe_allow_html=True)


def display_welcome_message():
    """Display welcome message in chat"""
    welcome_msg = """👋 **Welcome! I'm here to help you prepare for Data Engineering interviews.**

I'll provide:
✅ Practice interview questions (Entry/Mid/Advanced levels)
✅ Key competencies with Definition, Use Case, and Real-World Examples
✅ Content from curated data engineering documentation

**Available Topics:**
- 🐍 **Python** - Data engineering with Python
- 💾 **SQL** - Queries and database operations
- 🗄️ **Database** - RDBMS design and optimization
- 🔄 **ETL** - Data pipelines and transformations

**To get started, just type a topic name** (e.g., "Python") **or say "give me practice questions"**
"""
    st.session_state.messages.append({"role": "assistant", "content": welcome_msg})


def display_topic_selection_message():
    """Display topic selection message"""
    topic_msg = """**Great! Which topic would you like to practice?**

Select ONE topic by typing its name:
  - 🐍 **Python**
  - 💾 **SQL**
  - 🗄️ **Database**
  - 🔄 **ETL**

I'll generate practice questions and key competencies from the documentation.
"""
    
    st.session_state.messages.append({"role": "assistant", "content": topic_msg})


def format_conversation_history(messages: list, max_messages: int = 6) -> str:
    """
    Format conversation history for RAG context.
    
    Args:
        messages: List of chat messages
        max_messages: Maximum recent messages to include
        
    Returns:
        Formatted conversation history string
    """
    if not messages or len(messages) < 2:
        return "This is the start of the conversation."
    
    # Get recent messages (excluding the current user message being processed)
    recent_messages = messages[-max_messages:-1] if len(messages) > 1 else messages[:-1]
    
    formatted_history = []
    for msg in recent_messages:
        role = "Human" if msg["role"] == "user" else "Assistant"
        # Truncate long messages to keep context manageable
        content = msg["content"][:200] + "..." if len(msg["content"]) > 200 else msg["content"]
        formatted_history.append(f"{role}: {content}")
    
    return "\n".join(formatted_history)

def detect_topic_from_message(message: str) -> str:
    """
    Detect topic from user message with improved pattern matching.
    
    Args:
        message: User's message
        
    Returns:
        Detected topic or None
    """
    message_lower = message.lower().strip()
    
    # Topic keyword mapping with variations
    topics = {
        "Python": ["python", "py", "python3"],
        "SQL": ["sql", "query", "queries", "sequel"],
        "Database": ["database", "db", "rdbms", "databases"],
        "ETL": ["etl", "pipeline", "data pipeline", "pipelines"]
    }
    
    # Check for exact matches first (user just types "python")
    for topic, keywords in topics.items():
        if message_lower in keywords:
            return topic
    
    # Check for keywords within the message
    for topic, keywords in topics.items():
        if any(keyword in message_lower for keyword in keywords):
            return topic
    
    return None


def handle_user_input(user_message: str):
    """
    Handle user input and generate responses with conversation memory.
    
    Args:
        user_message: User's message
    """
    user_message_lower = user_message.lower()
    
    print(f"[DEBUG] Processing message: {user_message}")
    print(f"[DEBUG] Current stage: {st.session_state.conversation_stage}")
    
    # Get formatted conversation history for context
    chat_history = format_conversation_history(st.session_state.messages)
    
    # Stage 1: Greeting/Initial request
    if st.session_state.conversation_stage == "greeting":
        # First check if user directly mentions a topic
        topic = detect_topic_from_message(user_message)
        
        if topic:
            print(f"[DEBUG] Topic detected: {topic}")
            # User directly selected a topic - go straight to practicing
            st.session_state.selected_topic = topic
            st.session_state.conversation_stage = "practicing"
            
            # Generate practice content immediately with conversation context
            try:
                print(f"[DEBUG] Generating practice questions for {topic}...")
                response = st.session_state.rag_system.generate_practice_questions(topic, chat_history)
                print(f"[DEBUG] Response generated, length: {len(response)}")
                
                st.session_state.messages.append({"role": "assistant", "content": response})
                
                # Offer to continue
                follow_up = f"\n\n---\n\n💡 **Want to dive deeper?** Ask me specific questions about {topic}, or say **'more topics'** to explore other areas!"
                st.session_state.messages.append({"role": "assistant", "content": follow_up})
                print(f"[DEBUG] Messages added to session state")
                
            except Exception as e:
                print(f"[ERROR] Exception generating questions: {str(e)}")
                import traceback
                traceback.print_exc()
                error_msg = f"⚠️ Error generating content: {str(e)}. Please try again."
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
        
        # Check if user asks for practice questions (without specifying topic)
        elif any(keyword in user_message_lower for keyword in ["practice", "question", "list", "help", "prepare", "interview", "start"]):
            st.session_state.conversation_stage = "topic_selection"
            display_topic_selection_message()
        
        else:
            # General response
            response = "Hello! I'm here to help you prepare for Data Engineering interviews! **Just type a topic name** (Python, SQL, Database, or ETL) to get started, or say **'give me practise questions'**."
            st.session_state.messages.append({"role": "assistant", "content": response})
    
    # Stage 2: Topic Selection
    elif st.session_state.conversation_stage == "topic_selection":
        # Detect topic
        topic = detect_topic_from_message(user_message)
        
        if topic:
            st.session_state.selected_topic = topic
            st.session_state.conversation_stage = "practicing"
            
            # Generate practice content for the selected topic with conversation context
            with st.spinner(f"🔍 Retrieving {topic} competencies and generating practice questions..."):
                response = st.session_state.rag_system.generate_practice_questions(topic, chat_history)
            
            st.session_state.messages.append({"role": "assistant", "content": response})
            
            # Offer to continue
            follow_up = f"\n\n---\n\n💡 **Want to dive deeper?** Ask me specific questions about {topic}, or say **'more topics'** to explore other areas!"
            st.session_state.messages.append({"role": "assistant", "content": follow_up})
        else:
            # Topic not recognized
            response = "I didn't catch that topic. Please choose one of: **Python**, **SQL**, **Database**, or **ETL**."
            st.session_state.messages.append({"role": "assistant", "content": response})
    
    # Stage 3: Active Practice/Q&A
    elif st.session_state.conversation_stage == "practicing":
        # Check if user wants to change topics
        if any(keyword in user_message_lower for keyword in ["more topics", "other topic", "change topic", "different topic", "switch topic"]):
            st.session_state.conversation_stage = "topic_selection"
            st.session_state.selected_topic = None
            display_topic_selection_message()
        
        # Check if user asks for more questions/list for current topic
        elif any(keyword in user_message_lower for keyword in ["give me list", "list of", "more questions", "practice questions", "interview questions", "scenario", "scenarios"]) and st.session_state.selected_topic:
            with st.spinner(f"🔍 Generating more {st.session_state.selected_topic} practice questions..."):
                try:
                    response = st.session_state.rag_system.generate_practice_questions(st.session_state.selected_topic, chat_history)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                except Exception as e:
                    error_msg = f"⚠️ Error: {str(e)}. Please try again."
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})
        
        # Check if user wants to switch to a new topic directly
        elif new_topic := detect_topic_from_message(user_message):
            if new_topic != st.session_state.selected_topic:
                st.session_state.selected_topic = new_topic
                
                with st.spinner(f"🔍 Switching to {new_topic}..."):
                    try:
                        response = st.session_state.rag_system.generate_practice_questions(new_topic, chat_history)
                        st.session_state.messages.append({"role": "assistant", "content": response})
                        
                        follow_up = f"\n\n---\n\n💡 Ask me specific questions about {new_topic}, or say 'more topics' to explore other areas!"
                        st.session_state.messages.append({"role": "assistant", "content": follow_up})
                    except Exception as e:
                        error_msg = f"⚠️ Error: {str(e)}"
                        st.session_state.messages.append({"role": "assistant", "content": error_msg})
            else:
                # User mentioned current topic - regenerate questions
                with st.spinner(f"🔍 Generating {new_topic} practice content..."):
                    try:
                        response = st.session_state.rag_system.generate_practice_questions(new_topic, chat_history)
                        st.session_state.messages.append({"role": "assistant", "content": response})
                    except Exception as e:
                        error_msg = f"⚠️ Error: {str(e)}"
                        st.session_state.messages.append({"role": "assistant", "content": error_msg})
        
        # Answer specific questions about current topic with conversation context
        else:
            with st.spinner("💭 Generating answer..."):
                try:
                    response = st.session_state.rag_system.answer_question(
                        user_message,
                        topic=st.session_state.selected_topic,
                        chat_history=chat_history
                    )
                    st.session_state.messages.append({"role": "assistant", "content": response})
                except Exception as e:
                    error_msg = f"⚠️ Error: {str(e)}. Please try rephrasing your question."
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})


def display_sidebar():
    """Display sidebar with information"""
    with st.sidebar:
        st.markdown("### 📚 About")
        st.markdown("""
        This chatbot helps you prepare for **Data Engineering interviews** using:
        - Amazon Nova Lite (LLM)
        - LangChain (RAG Framework)
        - ChromaDB (Vector Store)
        - AWS Bedrock (Embeddings)
        """)
        
        st.markdown("---")
        
        st.markdown("### 🎯 Available Topics")
        topics_available = ["Python", "SQL", "Database", "ETL"]
        for topic in topics_available:
            if st.session_state.selected_topic == topic:
                st.markdown(f"✅ **{topic}** (Current)")
            else:
                st.markdown(f"📌 {topic}")
        
        st.markdown("---")
        
        st.markdown("### 💡 Tips")
        st.markdown("""
        - Start with "give me practice questions"
        - Select a topic to focus on
        - Ask specific questions about concepts
        - Say "more topics" to explore other areas
        - Answers include: Definition, Use Case, and Real-World Examples
        """)
        
        st.markdown("---")
        
        if st.button("🔄 Reset Conversation", use_container_width=True):
            st.session_state.messages = []
            st.session_state.conversation_stage = "greeting"
            st.session_state.selected_topic = None
            st.rerun()
        
        st.markdown("---")
        st.markdown("### ℹ️ Current Status")
        st.markdown(f"**Stage:** {st.session_state.conversation_stage}")
        if st.session_state.selected_topic:
            st.markdown(f"**Topic:** {st.session_state.selected_topic}")


def main():
    """Main application function"""
    
    # Initialize
    initialize_session_state()
    
    # Display header
    display_header()
    
    # Display sidebar
    display_sidebar()
    
    # Display welcome message on first load
    if len(st.session_state.messages) == 0:
        display_welcome_message()
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Type your message here..."):
        # Add user message to chat
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate assistant response
        handle_user_input(prompt)
        
        # Rerun to display new messages in the chat history
        st.rerun()


if __name__ == "__main__":
    main()
