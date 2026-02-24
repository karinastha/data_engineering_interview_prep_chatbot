"""
Chat Service - Orchestrates the RAG pipeline.

This is the main entry point for chat functionality. It coordinates:
- Preprocessing: Query transformation and topic extraction
- Retrieval: Getting relevant documents from vector store
- Generation: Producing answers with LLM

Architecture:
    User Message + History → Preprocess (LLM #1) → Retrieve → Generate (LLM #2)
"""

from collections.abc import Generator

from langsmith import traceable

from schemas import RAGResponse, Topic
from services.generation import GenerationService
from services.preprocessing import PreprocessingService
from services.retrieval import RetrievalService
from utils.logging import get_logger

logger = get_logger(__name__)


class ChatService:
    """
    Orchestrates the RAG pipeline for answering user questions.

    Coordinates preprocessing, retrieval, and generation services to provide
    a complete conversational RAG experience.
    """

    def __init__(
        self,
        preprocessing_service: PreprocessingService,
        generation_service: GenerationService,
        retrieval_service: RetrievalService,
    ) -> None:
        """
        Initialize the chat service with injected dependencies.

        Args:
            preprocessing_service: Service for query transformation.
            generation_service: Service for response generation.
            retrieval_service: Service for retrieving context documents.

        """
        self._preprocessing = preprocessing_service
        self._generation = generation_service
        self._retrieval = retrieval_service
        self._last_response: RAGResponse | None = None

    @traceable(name="chat_answer", run_type="chain", metadata={"pipeline": "rag"})
    def answer(
        self,
        message: str,
        history: list[dict],
    ) -> RAGResponse:
        """
        Answer a user message with full RAG pipeline.

        Args:
            message: User's current message.
            history: List of previous messages [{"role": "user/assistant", "content": "..."}].

        Returns:
            RAGResponse with generated answer.

        """
        if not message or not message.strip():
            return RAGResponse(
                content="Please provide a question.",
                error="Empty message",
            )

        # Step 1: Preprocess (LLM call #1)
        preprocessed = self._preprocessing.preprocess(message, history)

        # Convert topic strings to Topic enums
        topics = [Topic.from_string(t) for t in preprocessed.topics if Topic.from_string(t)]

        # Step 2: Retrieve relevant documents (loop over all detected topics)
        if topics:
            results = []
            for t in topics:
                results.extend(self._retrieval.retrieve(query=preprocessed.standalone_query, topic=t))
        else:
            results = []

        # Step 3: Generate response (LLM call #2)
        response = self._generation.generate(
            query=preprocessed.standalone_query,
            results=results,
            history=history,
            topic=topics[0] if topics else None,
        )
        response.project_resource_types = preprocessed.project_resource_types
        return response

    @traceable(name="chat_answer_stream", run_type="chain", metadata={"pipeline": "rag_stream"})
    def answer_stream(
        self,
        message: str,
        history: list[dict],
    ) -> Generator[str, None, None]:
        """
        Stream an answer to a user message.

        Args:
            message: User's current message.
            history: List of previous messages.

        Yields:
            Response tokens as they're generated.

        """
        if not message or not message.strip():
            yield "Please provide a question."
            return

        # Step 1: Preprocess (non-streaming)
        preprocessed = self._preprocessing.preprocess(message, history)

        # Convert topic strings to Topic enums
        topics = [Topic.from_string(t) for t in preprocessed.topics if Topic.from_string(t)]
        topic = topics[0] if topics else None

        # Check if this is a greeting - skip retrieval if so
        if preprocessed.is_greeting:
            logger.info("Greeting detected, skipping retrieval")
            full_response = ""
            for chunk in self._generation.generate_without_retrieval_stream(
                query=preprocessed.standalone_query,
                history=history,
            ):
                full_response += chunk
                yield chunk

            # Store response WITHOUT sources
            self._last_response = RAGResponse(
                content=full_response,
                sources=[],
                topic=None,
            )
            return

        # Step 2: Retrieve relevant documents (loop over all detected topics)
        if topics:
            results = []
            for t in topics:
                results.extend(self._retrieval.retrieve(query=preprocessed.standalone_query, topic=t))
        else:
            results = []

        # Step 3: Generate response with streaming (LLM call #2)
        full_response = ""
        for chunk in self._generation.generate_stream(
            query=preprocessed.standalone_query,
            results=results,
            history=history,
            topic=topic,
        ):
            full_response += chunk
            yield chunk

        # Store for later access
        self._last_response = RAGResponse(
            content=full_response,
            sources=results,
            topic=topic,
            project_resource_types=preprocessed.project_resource_types,
        )

    def get_last_response(self) -> RAGResponse | None:
        """Get the last RAGResponse from answer_stream() for metadata access."""
        return self._last_response
