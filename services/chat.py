"""
Chat Service - RAG-based Question Answering
Orchestrates retrieval and generation for conversational responses.

Responsibilities:
- Build prompts with context and history
- Generate responses using LLM
- Handle errors gracefully
- Provide practice question generation
"""

import logging
from typing import Optional

from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from config.settings import get_config, LLMConfig
from core.models import Topic, ConversationState, RAGResponse
from services.retrieval import RetrievalService

logger = logging.getLogger(__name__)


# =============================================================================
# PROMPT TEMPLATES - Simplified and focused
# =============================================================================

SYSTEM_PROMPT = """You are a Senior Data Engineer helping candidates prepare for technical interviews. You have extensive experience with Python, SQL, databases, and ETL pipelines.

Guidelines:
- Be concise and practical
- Use the provided reference material when relevant
- Structure answers with: Definition, Use Case, and Example
- Include code snippets when helpful
- Stay focused on data engineering applications"""

QA_TEMPLATE = """Reference Material:
{context}

Previous Conversation:
{history}

Question: {question}

Provide a helpful, interview-focused answer. Use the reference material if relevant, otherwise use your expertise."""

PRACTICE_TEMPLATE = """Reference Material:
{context}

Generate interview practice content for {topic} in data engineering. Include:

1. **Entry-Level Questions** (2-3 questions)
   - Focus on fundamentals and basic concepts

2. **Mid-Level Questions** (2-3 questions)  
   - Practical application and problem-solving

3. **Advanced Questions** (1-2 questions)
   - System design and optimization challenges

4. **Key Competencies to Know**
   For each competency from the reference material, provide:
   - 📚 **Definition**: Core concept explanation
   - 💡 **Use Case**: Practical application in data engineering
   - 🚀 **Example**: Real-world scenario or code snippet

Keep responses practical and interview-relevant."""


class ChatService:
    """
    Service for handling RAG-based chat interactions.
    
    Combines document retrieval with LLM generation for
    context-aware responses.
    """
    
    def __init__(
        self,
        llm: BaseChatModel,
        retrieval_service: RetrievalService,
        llm_config: Optional[LLMConfig] = None,
    ):
        """
        Initialize the chat service.
        
        Args:
            llm: Language model instance
            retrieval_service: Document retrieval service
            llm_config: LLM configuration (uses default if None)
        """
        self.llm = llm
        self.retrieval = retrieval_service
        self.config = llm_config or get_config().llm
        
        # Initialize prompt templates
        self._qa_prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            ("human", QA_TEMPLATE),
        ])
        
        self._practice_prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            ("human", PRACTICE_TEMPLATE),
        ])
        
        # Output parser
        self._parser = StrOutputParser()
    
    def answer_question(
        self,
        question: str,
        conversation: Optional[ConversationState] = None,
        topic: Optional[Topic] = None,
    ) -> RAGResponse:
        """
        Answer a user question using RAG.
        
        Args:
            question: User's question
            conversation: Conversation state for history
            topic: Optional topic filter for retrieval
            
        Returns:
            RAGResponse with generated answer
        """
        if not question or len(question.strip()) < 3:
            return RAGResponse(
                content="Please provide a valid question.",
                error="Invalid question",
            )
        
        try:
            # Retrieve relevant documents
            results = self.retrieval.retrieve(question, topic=topic)
            context = self.retrieval.format_context(results)
            
            # Format conversation history
            history = "This is the start of the conversation."
            if conversation:
                history = conversation.format_history_for_prompt()
            
            # Build and execute chain
            chain = self._qa_prompt | self.llm | self._parser
            
            response = chain.invoke({
                "context": context,
                "history": history,
                "question": question,
            })
            
            # Validate response
            if not response or len(response.strip()) < self.config.min_response_length:
                return RAGResponse(
                    content="I couldn't generate a sufficient answer. Please try rephrasing your question.",
                    sources=results,
                    topic=topic,
                    error="Response too short",
                )
            
            return RAGResponse(
                content=response,
                sources=results,
                topic=topic,
            )
            
        except Exception as e:
            logger.error(f"Error answering question: {e}")
            return RAGResponse(
                content=self._get_error_message(str(e)),
                topic=topic,
                error=str(e),
            )
    
    def generate_practice_questions(
        self,
        topic: Topic,
        conversation: Optional[ConversationState] = None,
    ) -> RAGResponse:
        """
        Generate practice interview questions for a topic.
        
        Args:
            topic: Topic to generate questions for
            conversation: Conversation state for context
            
        Returns:
            RAGResponse with practice content
        """
        try:
            # Get comprehensive topic competencies
            results = self.retrieval.get_topic_competencies(topic)
            context = self.retrieval.format_context(results)
            
            # Build and execute chain
            chain = self._practice_prompt | self.llm | self._parser
            
            response = chain.invoke({
                "context": context,
                "topic": topic.value,
            })
            
            # Validate response
            if not response or len(response.strip()) < self.config.min_response_length:
                return RAGResponse(
                    content=f"I couldn't generate sufficient practice content for {topic.value}. Please try again.",
                    sources=results,
                    topic=topic,
                    error="Response too short",
                )
            
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
    
    @staticmethod
    def _get_error_message(error: str) -> str:
        """
        Convert technical errors to user-friendly messages.
        
        Args:
            error: Error string
            
        Returns:
            User-friendly error message
        """
        error_lower = error.lower()
        
        if "timeout" in error_lower:
            return "The request timed out. Please try again with a simpler question."
        elif "rate limit" in error_lower:
            return "Too many requests. Please wait a moment and try again."
        elif "authentication" in error_lower or "credentials" in error_lower:
            return "Authentication error. Please check AWS credentials configuration."
        else:
            return "I encountered an error. Please try again or rephrase your question."


def create_chat_service(
    llm: BaseChatModel,
    retrieval_service: RetrievalService,
) -> ChatService:
    """
    Factory function to create a ChatService instance.
    
    Args:
        llm: Language model
        retrieval_service: Retrieval service
        
    Returns:
        Configured ChatService instance
    """
    return ChatService(llm, retrieval_service)
