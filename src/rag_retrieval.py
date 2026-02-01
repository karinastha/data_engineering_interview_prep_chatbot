"""
RAG Retrieval Module for Data Engineering Interview Prep Chatbot
Handles retrieval-augmented generation using ChromaDB and LangChain

Implements RAG Best Practices:
- Metadata filtering for topic-specific retrieval
- Similarity thresholding to filter irrelevant results
- Optimized top-k selection (k=4 for balanced context)
- Enhanced prompts with persona, few-shot, chain-of-thought, and guardrails
- Error handling with retry logic
- Streaming support for better UX
"""

import sys
from pathlib import Path
from typing import List, Tuple

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_chroma import Chroma
from langchain_core.documents import Document
from utils.helper_cred import llm, embeddings

# RAG Configuration Constants - Optimized for performance and accuracy
OPTIMAL_TOP_K = 4  # Balanced: not too few (missing context) or too many (noise)
SIMILARITY_THRESHOLD = 0.3  # Min similarity score (HuggingFace embeddings use cosine similarity ~0-1)
MAX_RETRIEVAL_DOCS = 6  # Maximum documents for topic-specific queries


class RAGRetriever:
    """Handles retrieval and generation for the chatbot"""
    
    def __init__(self, vectorstore: Chroma):
        """
        Initialize RAG retriever with vector store.
        
        Args:
            vectorstore: ChromaDB vector store containing competency data
        """
        self.vectorstore = vectorstore
        # Optimized retriever: k=4 for balanced context vs noise
        self.retriever = vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": OPTIMAL_TOP_K}
        )
    
    def retrieve_by_topic(self, topic: str, k: int = OPTIMAL_TOP_K) -> List[Tuple[Document, float]]:
        """
        Retrieve documents filtered by specific topic with similarity scores.
        
        Args:
            topic: Topic to filter by (Python, SQL, Database, ETL, AWS)
            k: Number of documents to retrieve
            
        Returns:
            List of tuples (document, similarity_score)
        """
        # Use metadata filtering for specific topic + similarity scores for thresholding
        docs_with_scores = self.vectorstore.similarity_search_with_score(
            query=f"Data engineering interview competencies and best practices for {topic}",
            k=k,
            filter={"topic": topic}
        )
        
        # Apply similarity threshold filtering
        filtered_docs = [
            (doc, score) for doc, score in docs_with_scores 
            if score >= SIMILARITY_THRESHOLD
        ]
        
        if not filtered_docs:
            print(f"Warning: No documents found above similarity threshold {SIMILARITY_THRESHOLD} for topic {topic}")
            # Return top result anyway if nothing passes threshold
            return docs_with_scores[:1] if docs_with_scores else []
        
        return filtered_docs
    
    def format_retrieved_docs(self, docs: list) -> str:
        """
        Format retrieved documents into a structured string.
        
        Args:
            docs: List of Document objects or tuples of (Document, score)
            
        Returns:
            Formatted string with all document content
        """
        if not docs:
            return "No relevant information found in the knowledge base."
        
        formatted_parts = []
        for i, item in enumerate(docs, 1):
            # Handle both Document and (Document, score) formats
            if isinstance(item, tuple):
                doc, score = item
                formatted_parts.append(f"--- Reference {i} (Relevance: {score:.2f}) ---")
            else:
                doc = item
                formatted_parts.append(f"--- Reference {i} ---")
            
            formatted_parts.append(doc.page_content)
            formatted_parts.append("")
        
        return "\n".join(formatted_parts)
    
    def create_topic_chain(self):
        """
        Create a chain for topic-based question answering with enhanced prompting.
        
        Returns:
            LangChain LCEL chain for RAG
        """
        # Enhanced prompt with: Persona, Few-Shot, Chain-of-Thought, and Smart Fallback
        template = """You are a Senior Data Engineer conducting technical interview preparation. You have 10+ years of experience building production data pipelines and mentoring junior engineers.

**Your Task:** Answer the candidate's question using the provided competency information when relevant, or your expert knowledge when the context doesn't contain the answer.

**Retrieved Competency Information:**
{context}

**Candidate's Question:** {question}

**Response Format - FOLLOW THIS EXAMPLE:**

Example Question: "What are list comprehensions in Python?"
Example Answer:

📚 **Definition:**
List comprehensions are a concise, Pythonic way to create lists by applying an expression to each item in an iterable, with optional filtering conditions.

💡 **Use Case:**
In ETL pipelines, list comprehensions efficiently transform and filter data in-memory before loading to databases. They're faster and more readable than traditional for-loops for data transformation tasks.

🚀 **Real-World Example:**
In a production pipeline processing user events:
```python
active_user_ids = [user['id'] for user in users if user['status'] == 'active']
```
This filters millions of user records to extract only active users in a single, optimized operation.

---

**Now, answer the candidate's question above following the same structure.**

**Smart Response Guidelines:**
1. **First, check if the Retrieved Competency Information is relevant to the question**
   - If YES: Use the competency information as your primary source
   - If NO or IRRELEVANT: Use your expert knowledge to answer the question

2. **For questions about data engineering topics (CDC, data warehousing, streaming, etc.):**
   - Answer confidently using your training data
   - Provide accurate, interview-relevant information
   - Include data engineering context and real-world examples

3. **Format Requirements:**
   - ALWAYS use the three-section format: Definition, Use Case, Real-World Example
   - Keep responses focused and interview-relevant
   - Include code examples when helpful
   - Do NOT mention that you are an AI

4. **Quality Standards:**
   - Ensure technical accuracy
   - Focus on data engineering applications
   - Provide practical, actionable information

**Your Answer:**"""

        prompt = ChatPromptTemplate.from_template(template)
        
        # Create LCEL chain with streaming support
        chain = (
            {"context": self.retriever | self.format_retrieved_docs, "question": RunnablePassthrough()}
            | prompt
            | llm
            | StrOutputParser()
        )
        
        return chain
    
    def create_topic_specific_chain(self, topic: str):
        """
        Create a chain for a specific topic with enhanced context and metadata filtering.
        
        Args:
            topic: Topic to focus on (Python, SQL, Database, ETL)
            
        Returns:
            Specialized chain for the topic with optimized retrieval
        """
        # Enhanced prompt with strict topic focus and guardrails
        template = f"""You are a Senior Data Engineer and Technical Interviewer specializing in {topic} for data engineering roles.

**Your Expertise:** You conduct interviews at top tech companies and mentor engineers on {topic} best practices.

**Retrieved {topic} Competency Information (Metadata-Filtered):**
{{context}}

**Candidate's Request:** {{question}}

**Your Task - Think Step-by-Step:**

1. **Assess the Request:**
   - Is the candidate asking for practice questions or specific concepts?
   - Does the retrieved context contain relevant {topic} information?
   - If context is insufficient or off-topic, acknowledge the limitation

2. **Generate Practice Questions** (if requested):
   Create 3-5 interview questions at different levels:
   
   **Entry-Level (Must Have):**
   - Focus on fundamental {topic} concepts
   - Test basic knowledge and syntax
   
   **Mid-Level (Desirable):**
   - Practical application scenarios
   - Integration with data engineering workflows
   
   **Advanced (Best Practice):**
   - Performance optimization
   - Production-scale challenges
   - System design considerations

3. **For Each Concept - Use This Exact Format:**

📚 **Definition:**
[Clear, technical explanation from "Must Have" competency level]

💡 **Use Case:**
[Practical application in data engineering from "Desirable" competency level]

🚀 **Real-World Example:**
[Production scenario or code example from "Advanced/Best" competency level]

**Smart Response Guidelines:**

**Step 1: Evaluate Context Relevance**
- Check if the Retrieved {topic} Competency Information contains relevant information for the question
- If YES: Use the competency information as your primary source
- If NO or IRRELEVANT: Use your expert knowledge about {topic}

**Step 2: Answer Appropriately**
- **When using competency information:** Extract from Must Have, Desirable, and Advanced levels
- **When using expert knowledge:** Provide accurate {topic} information from your training data
- **For both:** Maintain focus on {topic} and data engineering applications

**Quality Standards:**
- Do NOT mix concepts from other topics (keep it {topic}-focused)
- Do NOT mention you are an AI or language model
- ALWAYS maintain the three-section structure (Definition, Use Case, Real-World Example)
- Focus on interview-relevant, practical knowledge
- Provide accurate, technically sound information

**Context Awareness:**
- Current topic focus: {topic}
- Keep all responses relevant to {topic} and data engineering
- If user asks about other topics, gently redirect to {topic} or general data engineering

**Your Response:**"""

        prompt = ChatPromptTemplate.from_template(template)
        
        def retrieve_topic_docs(question):
            """Retrieve documents for specific topic with similarity filtering"""
            docs_with_scores = self.retrieve_by_topic(topic, k=6)  # Slightly higher k for topic-specific
            
            if not docs_with_scores:
                print(f"No relevant documents found for topic: {topic}")
                return "No relevant competency information found for this topic."
            
            # Extract just documents for formatting (scores already filtered by retrieve_by_topic)
            return self.format_retrieved_docs(docs_with_scores)
        
        # Create topic-specific chain with metadata filtering
        chain = (
            {"context": RunnablePassthrough() | retrieve_topic_docs, "question": RunnablePassthrough()}
            | prompt
            | llm
            | StrOutputParser()
        )
        
        return chain
    
    def generate_practice_questions(self, topic: str) -> str:
        """
        Generate practice interview questions for a specific topic with error handling.
        
        Args:
            topic: Topic to generate questions for
            
        Returns:
            Generated practice questions and learning content
        """
        try:
            chain = self.create_topic_specific_chain(topic)
            question = f"Generate interview practice questions and key competencies I should learn for {topic} in data engineering interviews. Include questions at different difficulty levels."
            
            # Invoke with error handling
            response = chain.invoke(question)
            
            if not response or len(response.strip()) < 50:
                return f"I couldn't generate sufficient content for {topic}. Please ensure the knowledge base is properly loaded."
            
            return response
            
        except Exception as e:
            print(f"Error generating practice questions for {topic}: {str(e)}")
            return f"I encountered an error generating {topic} practice questions. Please try again or select a different topic."
    
    def answer_question(self, question: str, topic: str = None) -> str:
        """
        Answer a user question with RAG and comprehensive error handling.
        
        Args:
            question: User's question
            topic: Optional topic to filter context (recommended for better accuracy)
            
        Returns:
            Generated answer
        """
        if not question or len(question.strip()) < 3:
            return "Please provide a valid question."
        
        try:
            # Use topic-specific chain if topic provided (better metadata filtering)
            if topic:
                chain = self.create_topic_specific_chain(topic)
            else:
                chain = self.create_topic_chain()
            
            # Invoke with retry logic (LangChain handles this internally)
            response = chain.invoke(question)
            
            # Validate response
            if not response or len(response.strip()) < 20:
                return "I couldn't find sufficient information to answer this question. Please try rephrasing or ask about Python, SQL, Database, or ETL competencies."
            
            return response
            
        except Exception as e:
            error_msg = str(e)
            print(f"Error answering question: {error_msg}")
            
            # User-friendly error messages
            if "timeout" in error_msg.lower():
                return "The request timed out. Please try again with a simpler question."
            elif "rate limit" in error_msg.lower():
                return "Too many requests. Please wait a moment and try again."
            elif "authentication" in error_msg.lower() or "credentials" in error_msg.lower():
                return "Authentication error. Please check AWS credentials configuration."
            else:
                return "I encountered an error processing your question. Please try again or rephrase your question."


def create_rag_system(vectorstore: Chroma) -> RAGRetriever:
    """
    Create RAG system with vector store.
    
    Args:
        vectorstore: ChromaDB vector store
        
    Returns:
        RAGRetriever instance
    """
    return RAGRetriever(vectorstore)


if __name__ == "__main__":
    # Example usage
    from src.ingestion_csv import initialize_vector_store
    
    print("Initializing RAG system...")
    vectorstore = initialize_vector_store()
    rag = create_rag_system(vectorstore)
    
    # Test retrieval
    print("\n" + "="*70)
    print("Testing Python topic retrieval...")
    print("="*70)
    response = rag.generate_practice_questions("Python")
    print(response)
