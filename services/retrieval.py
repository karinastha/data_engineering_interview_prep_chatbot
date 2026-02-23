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

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langsmith import traceable

from config.settings import RAGConfig, get_config
from schemas import RetrievalResult, Topic

logger = logging.getLogger(__name__)


class RetrievalService:
    """
    Service for retrieving relevant documents from the vector store.

    Supports both general semantic search and topic-filtered retrieval.
    """

    def __init__(
        self,
        vectorstore: Chroma,
        rag_config: RAGConfig | None = None,
    ) -> None:
        """
        Initialize the retrieval service.

        Args:
            vectorstore: ChromaDB vector store instance
            rag_config: RAG configuration (uses default if None)

        """
        self.vectorstore = vectorstore
        self.config = rag_config or get_config().rag

    @traceable(name="vector_retrieval")
    def retrieve(
        self,
        query: str,
        topic: Topic | None = None,
        top_k: int | None = None,
    ) -> list[RetrievalResult]:
        """
        Retrieve relevant documents for a query with optional topic filtering.

        Unified retrieval method that handles both general and topic-specific searches.
        This eliminates code duplication and makes the implementation more maintainable.

        Args:
            query: Search query
            topic: Optional topic to filter by (Python, SQL, Database, ETL)
            top_k: Number of results (uses config default if None)

        Returns:
            List of RetrievalResult objects sorted by relevance

        Examples:
            # General search
            results = retrieval.retrieve("What is data partitioning?")

            # Topic-filtered search
            results = retrieval.retrieve("list comprehensions", topic=Topic.PYTHON)

        """
        k = top_k or self.config.top_k
        # todo
        try:
            # Build search parameters based on whether topic is specified
            search_params = {"k": k}

            # Enhance query with topic context if topic is specified
            search_query = query
            if topic:
                search_query = f"Data engineering {topic.value}: {query}"
                search_params["filter"] = {"topic": topic.value}

            # Execute unified similarity search
            docs_with_scores = self.vectorstore.similarity_search_with_score(
                query=search_query,
                **search_params,
            )

            # Process and filter results
            results = self._process_results(docs_with_scores)

            # Log warning if topic-specific search returns no results
            if topic and not results:
                logger.warning(f"No documents found for topic: {topic.value}")

            return results

        except Exception as e:
            logger.error(f"Retrieval error: {e}", exc_info=True)
            return []

    def _process_results(
        self,
        docs_with_scores: list[tuple[Document, float]],
    ) -> list[RetrievalResult]:
        """
        Process raw results into RetrievalResult objects.

        Applies similarity threshold filtering and converts distance scores
        to similarity scores.

        ChromaDB Distance Metrics:
        - **Cosine Distance**: [0, 2] - Used for normalized embeddings (our case)
          * 0 = identical vectors, 2 = opposite vectors
          * Conversion: similarity = 1 - distance → [-1, 1], clamped to [0, 1]
        - **L2/Euclidean**: [0, ∞) - Unbounded distance
          * Conversion: similarity = 1 / (1 + distance)

        Args:
            docs_with_scores: List of (Document, score) tuples from ChromaDB

        Returns:
            Filtered and processed results with normalized similarity scores

        """
        results = []

        for doc, score in docs_with_scores:
            # Convert ChromaDB distance to similarity score (0-1, higher is better)
            similarity = self._distance_to_similarity(score)

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

        # If nothing passes threshold, return empty list
        # This allows the LLM to provide general guidance without being
        # misled by irrelevant context
        if not results:
            logger.info(
                f"No results above threshold ({self.config.similarity_threshold}). "
                "LLM will respond without knowledge base context.",
            )

        return results

    def _distance_to_similarity(self, distance: float) -> float:
        """
        Convert ChromaDB cosine distance to similarity score.

        ChromaDB with cosine distance (hnsw:space = 'cosine'):
        - Range: [0, 2] for normalized vectors
        - 0 = identical vectors (similarity = 1)
        - 1 = orthogonal vectors (similarity = 0)
        - 2 = opposite vectors (similarity = -1, rare)

        Conversion: similarity = 1 - distance

        Args:
            distance: ChromaDB cosine distance score (lower is better)

        Returns:
            Similarity score in [0, 1] range (higher is better)

        """
        # Cosine distance to similarity: subtract from 1
        similarity = 1.0 - distance

        # Clamp to [0, 1] range
        return max(0.0, min(1.0, similarity))

    def format_context(
        self,
        results: list[RetrievalResult],
        max_length: int | None = None,
    ) -> str:
        """
        Format retrieval results into context string for LLM.

        Includes topic and subtopic metadata so LLM can generate proper citations.

        Args:
            results: List of RetrievalResult objects
            max_length: Maximum context length (uses config if None)

        Returns:
            Formatted context string with metadata for citations

        """
        if not results:
            return "No relevant information found in the knowledge base."

        max_len = max_length or self.config.max_context_length

        parts = []
        current_length = 0

        for i, result in enumerate(results, 1):
            # Format individual result with topic/subtopic metadata for proper citations
            topic_info = f"Topic: {result.topic}"
            if result.subtopic:
                topic_info += f" - Subtopic: {result.subtopic}"

            section = f"--- {topic_info} ---\n{result.content}\n"

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
