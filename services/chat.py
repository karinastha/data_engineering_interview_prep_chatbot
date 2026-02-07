# """
# Chat Service - RAG-based Question Answering
# Orchestrates retrieval and generation for conversational responses.

# Responsibilities:
# - Query transformation with conversation history
# - Build prompts with context and history
# - Generate responses using LLM
# - Handle errors gracefully
# - Provide practice question generation
# """

# import logging
# from typing import Optional

# from pydantic import BaseModel, Field
# from langchain_core.language_models import BaseChatModel
# from langchain_core.prompts import ChatPromptTemplate
# from langchain_core.output_parsers import StrOutputParser

# from config.settings import get_config, LLMConfig
# from core.models import Topic, ConversationState, RAGResponse
# from services.retrieval import RetrievalService

# logger = logging.getLogger(__name__)


# # =============================================================================
# # QUERY TRANSFORMATION SCHEMA
# # =============================================================================

# class TransformedQuery(BaseModel):
#     """
#     Structured output for query transformation.
    
#     Converts conversational queries into standalone, context-aware queries
#     for better document retrieval.
#     """
#     standalone_query: str = Field(
#         description="Standalone query with full context from conversation history, "
#                     "suitable for semantic search without additional context"
#     )
#     original_intent: str = Field(
#         description="Brief description of what the user is actually asking about"
#     )
#     requires_history: bool = Field(
#         description="Whether the query needed conversation history to be understood"
#     )


# # =============================================================================
# # PROMPT TEMPLATES - Simplified and focused
# # =============================================================================

# SYSTEM_PROMPT = """You are a Senior Data Engineering Interview Coach with 10+ years of experience preparing candidates for roles at FAANG and top tech companies.

# Your Expertise:
# - Python for data engineering (pandas, PySpark, data pipelines)
# - SQL and database design (PostgreSQL, optimization, indexing)
# - ETL/ELT pipelines (Apache Airflow, data orchestration)
# - Data warehousing and distributed systems

# Core Principles:
# 1. ACCURACY: Only state facts you are certain about
# 2. GROUNDING: When knowledge base context is provided, use ONLY that information
# 3. CLARITY: Explain concepts as if teaching a motivated junior engineer
# 4. PRACTICALITY: Focus on real-world interview scenarios and applications
# 5. HONESTY: If you don't know something, say so directly

# Response Structure (when applicable):
# - Definition: Clear, concise explanation
# - Why It Matters: Data engineering context
# - Example: Code snippet or real-world scenario
# - Interview Tip: How to discuss this in an interview

# Keep responses focused, accurate, and interview-ready."""

# QA_WITH_CONTEXT_TEMPLATE = """KNOWLEDGE BASE CONTEXT:
# {context}

# CONVERSATION HISTORY:
# {history}

# CANDIDATE'S QUESTION: {question}

# CRITICAL INSTRUCTIONS:
# 1. Use ONLY information from the KNOWLEDGE BASE CONTEXT above
# 2. Every factual claim MUST cite its source using [Source N]
# 3. If the context doesn't fully answer the question, acknowledge the gap
# 4. Do NOT introduce information from your general knowledge
# 5. If multiple sources conflict, cite both and explain the difference

# REASONING PROCESS:
# - Step 1: Identify which sources contain relevant information
# - Step 2: Extract key facts from those sources
# - Step 3: Synthesize a clear, structured answer
# - Step 4: Ensure every claim has a citation

# FORMAT YOUR RESPONSE AS:

# **Answer:**
# [Your comprehensive answer with inline citations like "According to [Source 1], ACID properties..."]

# **Key Points:**
# - [Bullet point 1 with citation]
# - [Bullet point 2 with citation]

# **Example:**
# [Code snippet or practical scenario if applicable]

# **Interview Tip:**
# [How to effectively discuss this topic in an interview]

# Begin your response:"""

# QA_WITHOUT_CONTEXT_TEMPLATE = """CONVERSATION HISTORY:
# {history}

# CANDIDATE'S QUESTION: {question}

# SITUATION: This topic was not found in our curated data engineering interview prep knowledge base.

# YOUR TASK:
# 1. First, assess if this question is relevant to data engineering interviews
# 2. If YES and you have reliable general knowledge:
#    - Provide a helpful answer
#    - Clearly state: "This is general knowledge, not from our prep materials"
#    - Focus on data engineering applications if applicable
   
# 3. If NO (out of scope):
#    - Politely explain this isn't typically covered in data engineering interviews
#    - Suggest refocusing on core topics: Python, SQL, Databases, ETL
   
# 4. If you're uncertain about the answer:
#    - Say so directly: "I don't have reliable information about this"
#    - Suggest the candidate research authoritative sources

# IMPORTANT: 
# - Be honest about the source of information
# - Don't speculate or provide uncertain information
# - Keep the candidate focused on interview-relevant topics

# Begin your response:"""

# PRACTICE_TEMPLATE = """KNOWLEDGE BASE CONTENT:
# {context}

# TOPIC: {topic}

# TASK: Generate comprehensive interview practice materials for {topic} in data engineering.

# QUALITY REQUIREMENTS:
# - Questions must be realistic and commonly asked in interviews
# - Difficulty must progress from entry to advanced
# - Each question should test a distinct competency from the knowledge base
# - Provide brief answer guidance (not full answers)

# OUTPUT STRUCTURE:

# **Entry-Level Questions** (2-3 questions)
# Target: Candidates with 0-2 years experience
# Focus: Definitions, basic syntax, fundamental concepts

# Q1: [Clear, specific question]
#    Expected knowledge: [What the candidate should know]
   
# Q2: [Clear, specific question]
#    Expected knowledge: [What the candidate should know]

# **Mid-Level Questions** (2-3 questions)
# Target: Candidates with 2-5 years experience
# Focus: Practical application, trade-offs, problem-solving

# Q1: [Scenario-based question]
#    Expected approach: [How to tackle this]
   
# Q2: [Scenario-based question]
#    Expected approach: [How to tackle this]

# **Advanced Questions** (1-2 questions)
# Target: Senior candidates (5+ years)
# Focus: System design, optimization, architectural decisions

# Q1: [Complex, open-ended question]
#    Discussion points: [Key areas to cover]

# **Core Competencies**
# For each major competency from the knowledge base:

# **Competency: [Name]**
# - What it is: [Brief definition]
# - Why it matters: [Data engineering context]
# - Interview relevance: [When/how this comes up]
# - Example: [Code or scenario]
# - Common pitfalls: [What candidates get wrong]

# Ensure all content is grounded in the provided knowledge base context.

# Begin your response:"""

# QUERY_TRANSFORMATION_TEMPLATE = """TASK: Transform a conversational query into a standalone search query.

# CURRENT CONTEXT:
# Topic: {topic}
# Recent Conversation:
# {history}

# USER'S QUERY: "{question}"

# TRANSFORMATION RULES:
# 1. If query references previous context ("it", "that", "this", "also"):
#    → Incorporate specific context from conversation history
   
# 2. If query is already standalone and clear:
#    → Return as-is (minimal changes)
   
# 3. If query is vague or ambiguous:
#    → Add topic context to disambiguate
   
# 4. If query is a greeting or off-topic:
#    → Mark as non-transformable
   
# 5. Always include topic (Python/SQL/Database/ETL) when it adds clarity

# EXAMPLES:

# Example 1:
# History: "List comprehensions in Python create lists using concise syntax..."
# Query: "What about lambda functions?"
# Transformed: "What are lambda functions in Python and how do they differ from regular functions?"

# Example 2:
# History: "Window functions in SQL operate on partitions..."
# Query: "How does it work with PARTITION BY?"
# Transformed: "How do SQL window functions work with PARTITION BY clause?"

# Example 3:
# History: [none]
# Query: "What is ETL?"
# Transformed: "What is ETL in data engineering?"

# Example 4:
# History: "Apache Airflow is used for workflow orchestration..."
# Query: "Can you explain the syntax better?"
# Transformed: "Explain Apache Airflow DAG syntax and structure"

# Example 5:
# Query: "Hello"
# Transformed: [Mark as greeting, no transformation needed]

# NOW TRANSFORM THE CURRENT QUERY:
# Analyze the query, apply the rules, and provide the standalone version."""


# class ChatService:
#     """
#     Service for handling RAG-based chat interactions.
    
#     Combines document retrieval with LLM generation for
#     context-aware responses.
#     """
    
#     def __init__(
#         self,
#         llm: BaseChatModel,
#         retrieval_service: RetrievalService,
#         llm_config: Optional[LLMConfig] = None,
#     ):
#         """
#         Initialize the chat service.
        
#         Args:
#             llm: Language model instance
#             retrieval_service: Document retrieval service
#             llm_config: LLM configuration (uses default if None)
#         """
#         self.llm = llm
#         self.retrieval = retrieval_service
#         self.config = llm_config or get_config().llm
        
#         # Initialize prompt templates
#         self._qa_prompt_with_context = ChatPromptTemplate.from_messages([
#             ("system", SYSTEM_PROMPT),
#             ("human", QA_WITH_CONTEXT_TEMPLATE),
#         ])
        
#         self._qa_prompt_without_context = ChatPromptTemplate.from_messages([
#             ("system", SYSTEM_PROMPT),
#             ("human", QA_WITHOUT_CONTEXT_TEMPLATE),
#         ])
        
#         self._practice_prompt = ChatPromptTemplate.from_messages([
#             ("system", SYSTEM_PROMPT),
#             ("human", PRACTICE_TEMPLATE),
#         ])
        
#         # Output parser
#         self._parser = StrOutputParser()
    
#     def _transform_query(
#         self,
#         question: str,
#         conversation: Optional[ConversationState],
#         topic: Optional[Topic]
#     ) -> str:
#         """
#         Transform conversational query into standalone query using LLM.
        
#         This addresses the core problem: conversational queries often have implicit
#         context (pronouns, references to previous topics) that hurt retrieval quality.
        
#         Examples:
#         - "What about lambda functions?" → "What are lambda functions in Python?"
#         - "How does it work?" → "How do SQL window functions work?"
#         - "Can you explain that better?" → "Can you explain list comprehensions in Python?"
        
#         Args:
#             question: User's original question
#             conversation: Conversation state with history
#             topic: Current topic context
            
#         Returns:
#             Standalone query suitable for semantic search
#         """
#         # If no conversation history, use original question
#         if not conversation or not conversation.messages:
#             logger.debug("No conversation history - using original query")
#             return question
        
#         # Get recent conversation for context
#         history_text = conversation.format_history_for_prompt(max_messages=4)
        
#         # Build transformation prompt using template
#         transformation_prompt = QUERY_TRANSFORMATION_TEMPLATE.format(
#             topic=topic.value if topic else 'General Data Engineering',
#             history=history_text,
#             question=question
#         )

#         try:
#             # Use structured output for reliable parsing
#             structured_llm = self.llm.with_structured_output(TransformedQuery)
#             result = structured_llm.invoke(transformation_prompt)
            
#             logger.info(
#                 f"Query transformed: '{question}' → '{result.standalone_query}' "
#                 f"(required history: {result.requires_history})"
#             )
            
#             return result.standalone_query
            
#         except Exception as e:
#             # Fallback to original query on error
#             logger.warning(f"Query transformation failed: {e}, using original query")
#             return question
    
#     def answer_question(
#         self,
#         question: str,
#         conversation: Optional[ConversationState] = None,
#         topic: Optional[Topic] = None,
#     ) -> RAGResponse:
#         """
#         Answer a user question using RAG.
        
#         Args:
#             question: User's question
#             conversation: Conversation state for history
#             topic: Optional topic filter for retrieval
            
#         Returns:
#             RAGResponse with generated answer
#         """
#         if not question or not question.strip():
#             return RAGResponse(
#                 content="Please provide a valid question.",
#                 error="Invalid question",
#             )
        
#         try:
#             # Transform query using conversation history for better retrieval
#             transformed_query = self._transform_query(question, conversation, topic)
            
#             # Retrieve relevant documents using transformed query
#             results = self.retrieval.retrieve(transformed_query, topic=topic)
            
#             # Format conversation history
#             history = "This is the start of the conversation."
#             if conversation:
#                 history = conversation.format_history_for_prompt()
            
#             # Choose appropriate prompt and build chain based on whether we have context
#             if results:
#                 # Scenario A: Knowledge base has relevant information
#                 context = self.retrieval.format_context(results)
#                 chain = self._qa_prompt_with_context | self.llm | self._parser
                
#                 response = chain.invoke({
#                     "context": context,
#                     "history": history,
#                     "question": question,
#                 })
                
#                 # Add KB indicator to response
#                 response = f"📚 **From Knowledge Base**\n\n{response}"
                
#             else:
#                 # Scenario B: No relevant KB content found
#                 chain = self._qa_prompt_without_context | self.llm | self._parser
                
#                 response = chain.invoke({
#                     "history": history,
#                     "question": question,
#                 })
                
#                 # Add general knowledge indicator to response
#                 response = f"💡 **General Guidance** (not from curated knowledge base)\n\n{response}"
            
#             # Validate response
#             if not response:
#                 return RAGResponse(
#                     content="I couldn't generate a sufficient answer. Please try rephrasing your question.",
#                     sources=results,
#                     topic=topic,
#                     error="Response too short",
#                 )
            
#             return RAGResponse(
#                 content=response,
#                 sources=results,
#                 topic=topic,
#             )
            
#         except Exception as e:
#             logger.exception("Error answering question")
#             return RAGResponse(
#                 # TODO 
#                 content=self._get_error_message(str(e)),
#                 topic=topic,
#                 error=str(e),
#             )
    
#     def generate_practice_questions(
#         self,
#         topic: Topic,
#         conversation: Optional[ConversationState] = None,
#     ) -> RAGResponse:
#         """
#         Generate practice interview questions for a topic.
        
#         Args:
#             topic: Topic to generate questions for
#             conversation: Conversation state for context
            
#         Returns:
#             RAGResponse with practice content
#         """
#         try:
#             # Get comprehensive topic competencies
#             results = self.retrieval.get_topic_competencies(topic)
#             context = self.retrieval.format_context(results)
            
#             # Build and execute chain
#             chain = self._practice_prompt | self.llm | self._parser
            
#             response = chain.invoke({
#                 "context": context,
#                 "topic": topic.value,
#             })
            
#             # Validate response
#             if not response or len(response.strip()) < self.config.min_response_length:
#                 return RAGResponse(
#                     content=f"I couldn't generate sufficient practice content for {topic.value}. Please try again.",
#                     sources=results,
#                     topic=topic,
#                     error="Response too short",
#                 )
            
#             return RAGResponse(
#                 content=response,
#                 sources=results,
#                 topic=topic,
#             )
            
#         except Exception as e:
#             logger.error(f"Error generating practice questions: {e}")
#             return RAGResponse(
#                 content=f"Error generating {topic.value} practice questions. Please try again.",
#                 topic=topic,
#                 error=str(e),
#             )
    
#     @staticmethod
#     def _get_error_message(error: str) -> str:
#         """
#         Convert technical errors to user-friendly messages.
        
#         Args:
#             error: Error string
            
#         Returns:
#             User-friendly error message
#         """
#         error_lower = error.lower()
        
#         if "timeout" in error_lower:
#             return "The request timed out. Please try again with a simpler question."
#         elif "rate limit" in error_lower:
#             return "Too many requests. Please wait a moment and try again."
#         elif "authentication" in error_lower or "credentials" in error_lower:
#             return "Authentication error. Please check AWS credentials configuration."
#         else:
#             return "I encountered an error. Please try again or rephrase your question."


# def create_chat_service(
#     llm: BaseChatModel,
#     retrieval_service: RetrievalService,
# ) -> ChatService:
#     """
#     Factory function to create a ChatService instance.
    
#     Args:
#         llm: Language model
#         retrieval_service: Retrieval service
        
#     Returns:
#         Configured ChatService instance
#     """
#     return ChatService(llm, retrieval_service)
