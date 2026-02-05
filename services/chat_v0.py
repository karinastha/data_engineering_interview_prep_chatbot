"""
Chat Service V0 - Simplified RAG-based Question Answering

Key Changes from Original:
- Single preprocessing step (query transformation + topic extraction)
- No intent classification - everything goes through RAG
- Proper conversation history integration
- 2 LLM calls max per user message

Architecture:
    User Message + History → Preprocess (LLM #1) → Retrieve → Generate (LLM #2)
"""

import logging
from typing import Optional, List, Dict

from langsmith import traceable
from pydantic import BaseModel, Field
from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from config.settings import get_config, LLMConfig
from core.models import Topic, RAGResponse
from services.retrieval import RetrievalService

logger = logging.getLogger(__name__)


# =============================================================================
# PREPROCESSING SCHEMA - Single LLM call for query transform + topic extraction
# =============================================================================

def _get_topic_description() -> str:
    """Get dynamic topic list for Pydantic field description."""
    from config.topics import get_topic_names
    topics = get_topic_names()
    return f"Detected topic for metadata filtering. Must be exactly one of: {', '.join([repr(t) for t in topics])}, or null if no specific topic."


class PreprocessedQuery(BaseModel):
    """
    Combined query transformation and topic extraction.
    
    This replaces the separate IntentAnalysis (app.py) and TransformedQuery (chat.py)
    with a single, focused preprocessing step.
    """
    standalone_query: str = Field(
        description="Rewritten query that is self-contained and doesn't need conversation "
                    "history to understand. Resolve pronouns like 'it', 'that', 'this' using context."
    )
    topic: Optional[str] = Field(
        None,
        description=_get_topic_description()
    )


# =============================================================================
# PROMPT TEMPLATES - Simplified and focused
# =============================================================================

SYSTEM_PROMPT = """You are a Data Engineering Interview Coach helping candidates prepare for technical interviews at Leapfrog.

Your knowledge covers:
- Python for data engineering (pandas, PySpark, APIs, data pipelines)
- SQL queries (joins, window functions, CTEs, optimization)
- Database design (RDBMS, ACID, indexing, normalization)
- ETL/ELT pipelines (Airflow, data warehousing, dimensional modeling, data lakes)

RESPONSE FORMATS:

**For conceptual/explanatory questions** (what is, explain, how does, difference between):
📚 **Definition:** [Clear, concise explanation of the concept]
💡 **Use Case:** [When/why this is used in data engineering - practical context]
🚀 **Example:** [Code snippet or real-world scenario]

**For practice question requests** (interview questions, practice, quiz me):
🟢 **Basic Level:**
- [2-3 foundational questions testing definitions and core concepts]

🟡 **Intermediate Level:**
- [2-3 applied/scenario questions testing practical skills]

🔴 **Advanced Level:**
- [1-2 system design or optimization questions]

**For architecture/system design questions** (design, architecture, how does X work end-to-end):
Consider including a Mermaid diagram to visualize the concept:
```mermaid
graph LR
    A[Component] --> B[Component]
```
Use diagrams for data flows, ETL pipelines, system architectures, or process flows when it helps understanding.

GUIDELINES:
1. Use the provided knowledge base context when available
2. Choose the appropriate format based on what the user is asking
3. Be accurate and practical - focus on real interview scenarios
4. If you don't know something, say so
5. For architecture questions, include Mermaid diagrams when visualization helps
5. For greetings, respond naturally and helpfully"""


def _get_preprocessing_prompt() -> str:
    """
    Build preprocessing prompt with dynamic topic definitions from config.
    This ensures topic definitions stay in sync with config/topics.py.
    """
    from config.topics import get_topic_definitions_for_prompt, get_classification_rules_for_prompt, get_topic_names
    
    topic_list = ", ".join([f"'{t}'" for t in get_topic_names()])
    
    return f"""Analyze this user message and prepare it for document retrieval.

TOPIC DEFINITIONS (our knowledge base structure):
{get_topic_definitions_for_prompt()}

CLASSIFICATION RULES:
{get_classification_rules_for_prompt()}

RECENT USER MESSAGES (most recent = most important):
{{history}}

CURRENT MESSAGE: "{{message}}"

TRANSFORMATION RULES:
1. The CURRENT MESSAGE is what the user wants NOW - focus on this
2. Use previous messages ONLY to resolve references ("it", "that", "this", "more")
3. Include the topic from context if the current message has references
4. Keep the standalone query concise (under 20 words)
5. topic must be exactly one of: {topic_list}, or null if no specific topic

EXAMPLES:
- History: ["list comprehensions", "what about dictionary comprehensions?"]
  Current: "show me examples"
  → standalone_query: "Examples of dictionary comprehensions in Python"
  → topic: "Python"

- History: []
  Current: "data warehouse vs lakehouse"
  → standalone_query: "What is the difference between data warehouse and data lakehouse?"
  → topic: "ETL"  (warehousing concepts are in ETL docs)

- History: []
  Current: "explain ACID properties"
  → standalone_query: "Explain ACID properties in databases"
  → topic: "Database"

- History: []
  Current: "hello"
  → standalone_query: "greeting"
  → topic: null

Now process the current message:"""


# Legacy constant for backward compatibility (now generated dynamically)
PREPROCESSING_PROMPT = _get_preprocessing_prompt()

QA_PROMPT_TEMPLATE = """<context>
{context}
</context>

<conversation_history>
{history}
</conversation_history>

<user_question>
{question}
</user_question>

Instructions:
- Answer based on the <context> when relevant
- If context doesn't cover the topic, use your general knowledge but mention it
- Be concise and interview-focused
- Include practical examples when helpful

Your response:"""

PRACTICE_QUESTIONS_PROMPT = """<context>
{context}
</context>

Generate interview practice content for {topic}.

Create:
1. **Entry-Level Questions** (2-3 questions)
   - Focus on fundamentals and definitions
   
2. **Mid-Level Questions** (2-3 questions)  
   - Practical scenarios and problem-solving
   
3. **Advanced Questions** (1-2 questions)
   - System design, optimization, trade-offs

For each question, briefly note what a good answer should cover.

Your response:"""


# =============================================================================
# CHAT SERVICE
# =============================================================================

class ChatService:
    """
    Simplified chat service with proper conversation history support.
    
    Flow:
    1. Preprocess: Transform query + extract topic (1 LLM call)
    2. Retrieve: Get relevant docs using standalone query + topic filter
    3. Generate: Produce answer with context (1 LLM call)
    """
    
    def __init__(
        self,
        llm: BaseChatModel,
        retrieval_service: RetrievalService,
        llm_config: Optional[LLMConfig] = None,
    ):
        self.llm = llm
        self.retrieval = retrieval_service
        self.config = llm_config or get_config().llm
        self._parser = StrOutputParser()
        
        # Initialize prompts
        self._qa_prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            ("human", QA_PROMPT_TEMPLATE),
        ])
        
        self._practice_prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            ("human", PRACTICE_QUESTIONS_PROMPT),
        ])
    
    def _format_history_for_preprocessing(self, messages: List[Dict], max_messages: int = 5) -> str:
        """
        Format conversation history for preprocessing prompt.
        
        Uses only USER messages to save tokens and reduce confusion.
        Most recent messages are most important.
        """
        if not messages:
            return "No previous messages."
        
        # Extract only user messages
        user_messages = [msg["content"] for msg in messages if msg["role"] == "user"]
        
        if not user_messages:
            return "No previous messages."
        
        # Take last N user messages (most recent first for the prompt)
        recent = user_messages[-max_messages:]
        
        # Format with recency indicator
        formatted = []
        for i, content in enumerate(reversed(recent)):
            # Truncate long messages
            content = content[:100] + "..." if len(content) > 100 else content
            if i == 0:
                formatted.append(f"[CURRENT - skip, shown separately]")
            else:
                formatted.append(f"{i}. \"{content}\"")
        
        # Remove the current message marker, return just previous ones
        return "\n".join(formatted[1:]) if len(formatted) > 1 else "No previous messages."
    
    def _format_history_for_generation(self, messages: List[Dict], max_messages: int = 6) -> str:
        """
        Format conversation history for answer generation.
        
        Includes both user and assistant messages for context.
        """
        if not messages:
            return "No previous conversation."
        
        # Take last N messages
        recent = messages[-max_messages:]
        
        formatted = []
        for msg in recent:
            role = "User" if msg["role"] == "user" else "Assistant"
            # Truncate long messages
            content = msg["content"][:300] + "..." if len(msg["content"]) > 300 else msg["content"]
            formatted.append(f"{role}: {content}")
        
        return "\n".join(formatted)
    
    @traceable(name="preprocess_query")
    def _preprocess_query(
        self,
        message: str,
        history: List[Dict],
    ) -> PreprocessedQuery:
        """
        Single LLM call to transform query and extract topic.
        
        Args:
            message: User's current message
            history: Conversation history
            
        Returns:
            PreprocessedQuery with standalone_query and optional topic
        """
        history_text = self._format_history_for_preprocessing(history)
        
        prompt = PREPROCESSING_PROMPT.format(
            history=history_text,
            message=message,
        )
        
        try:
            structured_llm = self.llm.with_structured_output(PreprocessedQuery)
            result = structured_llm.invoke(prompt)
            
            logger.info(
                f"Preprocessed: '{message}' → query='{result.standalone_query}', topic={result.topic}"
            )
            
            return result
            
        except Exception as e:
            logger.warning(f"Preprocessing failed: {e}, using original message")
            return PreprocessedQuery(
                standalone_query=message,
                topic=None,
            )
    
    @traceable(name="answer")
    def answer(
        self,
        message: str,
        history: List[Dict],
    ) -> RAGResponse:
        """
        Main entry point - answer a user message with full RAG pipeline.
        
        Args:
            message: User's current message
            history: List of previous messages [{"role": "user/assistant", "content": "..."}]
            
        Returns:
            RAGResponse with generated answer
        """
        if not message or not message.strip():
            return RAGResponse(
                content="Please provide a question.",
                error="Empty message",
            )
        
        try:
            # Step 1: Preprocess (LLM call #1)
            preprocessed = self._preprocess_query(message, history)
            
            # Convert topic string to Topic enum if present
            topic = None
            if preprocessed.topic:
                topic = Topic.from_string(preprocessed.topic)
            
            # Step 2: Retrieve relevant documents
            results = self.retrieval.retrieve(
                query=preprocessed.standalone_query,
                topic=topic,
            )
            
            # Step 3: Generate response (LLM call #2)
            context = self.retrieval.format_context(results)
            history_text = self._format_history_for_generation(history)
            
            chain = self._qa_prompt | self.llm | self._parser
            
            response = chain.invoke({
                "context": context,
                "history": history_text,
                "question": preprocessed.standalone_query,
            })
            
            return RAGResponse(
                content=response,
                sources=results,
                topic=topic,
            )
            
        except Exception as e:
            logger.exception("Error in answer()")
            return RAGResponse(
                content="I encountered an error. Please try again.",
                error=str(e),
            )
    
    @traceable(name="answer_stream")
    def answer_stream(
        self,
        message: str,
        history: List[Dict],
    ):
        """
        Streaming version of answer() - yields tokens as they're generated.
        
        Args:
            message: User's current message
            history: List of previous messages
            
        Yields:
            str: Response tokens as they're generated
            
        Returns:
            After iteration completes, can access full_response via the generator
        """
        from typing import Generator
        
        if not message or not message.strip():
            yield "Please provide a question."
            return
        
        try:
            # Step 1: Preprocess (non-streaming, ~1s)
            preprocessed = self._preprocess_query(message, history)
            
            # Convert topic string to Topic enum if present
            topic = None
            if preprocessed.topic:
                topic = Topic.from_string(preprocessed.topic)
            
            # Step 2: Retrieve relevant documents (non-streaming)
            results = self.retrieval.retrieve(
                query=preprocessed.standalone_query,
                topic=topic,
            )
            
            # Step 3: Generate response with STREAMING (LLM call #2)
            context = self.retrieval.format_context(results)
            history_text = self._format_history_for_generation(history)
            
            chain = self._qa_prompt | self.llm | self._parser
            
            full_response = ""
            for chunk in chain.stream({
                "context": context,
                "history": history_text,
                "question": preprocessed.standalone_query,
            }):
                full_response += chunk
                yield chunk
            
            # Store metadata for potential access after streaming
            self._last_response = RAGResponse(
                content=full_response,
                sources=results,
                topic=topic,
            )
            
            logger.info(f"Streamed response: {len(full_response)} chars, topic={topic}")
            
        except Exception as e:
            logger.exception("Error in answer_stream()")
            yield "I encountered an error. Please try again."
    
    def get_last_response(self) -> Optional[RAGResponse]:
        """Get the last RAGResponse from answer_stream() for metadata access."""
        return getattr(self, '_last_response', None)
    
    def generate_practice_questions(
        self,
        topic: Topic,
    ) -> RAGResponse:
        """
        Generate practice interview questions for a specific topic.
        
        Args:
            topic: Topic to generate questions for
            
        Returns:
            RAGResponse with practice content
        """
        try:
            # Get topic competencies
            results = self.retrieval.get_topic_competencies(topic)
            context = self.retrieval.format_context(results)
            
            chain = self._practice_prompt | self.llm | self._parser
            
            response = chain.invoke({
                "context": context,
                "topic": topic.value,
            })
            
            return RAGResponse(
                content=response,
                sources=results,
                topic=topic,
            )
            
        except Exception as e:
            logger.error(f"Error generating practice questions: {e}")
            return RAGResponse(
                content=f"Error generating {topic.value} practice questions. Please try again.",
                topic=topic,
                error=str(e),
            )
