"""
Document Retrieval Service
Handles retrieving relevant documents from the vector store.

Responsibilities:
- Retrieve documents by similarity search
- Filter by topic metadata
- Apply similarity thresholds
- Format context for LLM consumption
"""

import logging
from typing import Optional

from langchain_chroma import Chroma
from langchain_core.documents import Document

from config.settings import get_config, RAGConfig
from core.models import Topic, RetrievalResult

logger = logging.getLogger(__name__)


class RetrievalService:
    """
    Service for retrieving relevant documents from the vector store.
    
    Supports both general semantic search and topic-filtered retrieval.
    """
    
    def __init__(
        self,
        vectorstore: Chroma,
        rag_config: Optional[RAGConfig] = None,
    ):
        """
        Initialize the retrieval service.
        
        Args:
            vectorstore: ChromaDB vector store instance
            rag_config: RAG configuration (uses default if None)
        """
        self.vectorstore = vectorstore
        self.config = rag_config or get_config().rag
    
    def retrieve(
        self,
        query: str,
        topic: Optional[Topic] = None,
        top_k: Optional[int] = None,
    ) -> list[RetrievalResult]:
        """
        Retrieve relevant documents for a query.
        
        Args:
            query: Search query
            topic: Optional topic to filter by
            top_k: Number of results (uses config default if None)
            
        Returns:
            List of RetrievalResult objects sorted by relevance
        """
        k = top_k or self.config.top_k
        
        try:
            if topic:
                return self._retrieve_by_topic(query, topic, k)
            else:
                return self._retrieve_general(query, k)
                
        except Exception as e:
            logger.error(f"Retrieval error: {e}")
            return []
    
    def _retrieve_general(self, query: str, k: int) -> list[RetrievalResult]:
        """
        Perform general similarity search without topic filter.
        
        Args:
            query: Search query
            k: Number of results
            
        Returns:
            List of RetrievalResult objects
        """
        docs_with_scores = self.vectorstore.similarity_search_with_score(
            query=query,
            k=k,
        )
        
        return self._process_results(docs_with_scores)
    
    def _retrieve_by_topic(
        self,
        query: str,
        topic: Topic,
        k: int,
    ) -> list[RetrievalResult]:
        """
        Retrieve documents filtered by topic.
        
        Args:
            query: Search query
            topic: Topic to filter by
            k: Number of results
            
        Returns:
            List of RetrievalResult objects
        """
        # Enhance query with topic context for better matching
        enhanced_query = f"Data engineering {topic.value}: {query}"
        
        docs_with_scores = self.vectorstore.similarity_search_with_score(
            query=enhanced_query,
            k=k,
            filter={"topic": topic.value},
        )
        
        results = self._process_results(docs_with_scores)
        
        if not results:
            logger.warning(f"No documents found for topic: {topic.value}")
        
        return results
    
    def _process_results(
        self,
        docs_with_scores: list[tuple[Document, float]],
    ) -> list[RetrievalResult]:
        """
        Process raw results into RetrievalResult objects.
        
        Applies similarity threshold filtering.
        
        Args:
            docs_with_scores: List of (Document, score) tuples
            
        Returns:
            Filtered and processed results
        """
        results = []
        
        for doc, score in docs_with_scores:
            # Note: ChromaDB returns distance, lower is better
            # Convert to similarity score (higher is better)
            similarity = 1 - score if score <= 1 else 1 / (1 + score)
            
            result = RetrievalResult(
                content=doc.page_content,
                score=similarity,
                topic=doc.metadata.get("topic", ""),
                subtopic=doc.metadata.get("subtopic", ""),
                metadata=doc.metadata,
            )
            
            # Apply threshold filter
            if result.is_relevant(self.config.similarity_threshold):
                results.append(result)
        
        # If nothing passes threshold, return top result anyway
        if not results and docs_with_scores:
            doc, score = docs_with_scores[0]
            results.append(RetrievalResult(
                content=doc.page_content,
                score=1 - score if score <= 1 else 1 / (1 + score),
                topic=doc.metadata.get("topic", ""),
                subtopic=doc.metadata.get("subtopic", ""),
                metadata=doc.metadata,
            ))
            logger.info("No results above threshold, returning top result")
        
        return results
    
    def format_context(
        self,
        results: list[RetrievalResult],
        max_length: Optional[int] = None,
    ) -> str:
        """
        Format retrieval results into context string for LLM.
        
        Args:
            results: List of RetrievalResult objects
            max_length: Maximum context length (uses config if None)
            
        Returns:
            Formatted context string
        """
        if not results:
            return "No relevant information found in the knowledge base."
        
        max_len = max_length or self.config.max_context_length
        
        parts = []
        current_length = 0
        
        for i, result in enumerate(results, 1):
            # Format individual result
            section = f"[Source {i}]\n{result.content}\n"
            
            # Check length limit
            if current_length + len(section) > max_len:
                break
            
            parts.append(section)
            current_length += len(section)
        
        return "\n".join(parts)
    
    def get_topic_competencies(self, topic: Topic) -> list[RetrievalResult]:
        """
        Get all competencies for a specific topic.
        
        Useful for generating comprehensive practice content.
        
        Args:
            topic: Topic to retrieve competencies for
            
        Returns:
            List of all relevant competencies
        """
        query = f"Key competencies and interview topics for {topic.value} in data engineering"
        return self.retrieve(query, topic=topic, top_k=self.config.max_topic_docs)
