"""Response generation service for producing answers with LLM."""

from collections.abc import Generator
from typing import TYPE_CHECKING

from langchain_core.language_models import BaseChatModel
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langsmith import traceable

from prompts import QA_PROMPT_TEMPLATE, SYSTEM_PROMPT
from schemas import RAGResponse, RetrievalResult, Topic
from services.history import format_history_for_generation
from utils.logging import get_logger

if TYPE_CHECKING:
    from services.retrieval import RetrievalService

logger = get_logger(__name__)


class GenerationService:
    """Service for generating responses using LLM with retrieved context."""

    def __init__(
        self,
        llm: BaseChatModel,
        retrieval_service: "RetrievalService",
    ) -> None:
        """
        Initialize the generation service.

        Args:
            llm: Language model for response generation.
            retrieval_service: Service for retrieving context documents.

        """
        self.llm = llm
        self.retrieval = retrieval_service
        self._parser = StrOutputParser()

        self._qa_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", SYSTEM_PROMPT),
                ("human", QA_PROMPT_TEMPLATE),
            ],
        )

    @traceable(name="generate_answer")
    def generate(
        self,
        query: str,
        results: list[RetrievalResult],
        history: list[dict],
        topic: Topic | None = None,
    ) -> RAGResponse:
        """
        Generate a response based on retrieved context.

        Args:
            query: The preprocessed standalone query.
            results: Retrieved documents from vector store.
            history: Conversation history for context.
            topic: Optional topic for metadata.

        Returns:
            RAGResponse with generated content and sources.

        """
        context = self.retrieval.format_context(results)
        history_text = format_history_for_generation(history)

        chain = self._qa_prompt | self.llm | self._parser

        response = chain.invoke(
            {
                "context": context,
                "history": history_text,
                "question": query,
            },
        )

        return RAGResponse(
            content=response,
            sources=results,
            topic=topic,
        )

    @traceable(name="generate_answer_stream")
    def generate_stream(
        self,
        query: str,
        results: list[RetrievalResult],
        history: list[dict],
        topic: Topic | None = None,
    ) -> Generator[str, None, RAGResponse]:
        """
        Generate a streaming response based on retrieved context.

        Args:
            query: The preprocessed standalone query.
            results: Retrieved documents from vector store.
            history: Conversation history for context.
            topic: Optional topic for metadata.

        Yields:
            Response tokens as they're generated.

        Returns:
            Complete RAGResponse after streaming finishes (access via generator).

        """
        context = self.retrieval.format_context(results)
        history_text = format_history_for_generation(history)

        chain = self._qa_prompt | self.llm | self._parser

        full_response = ""
        for chunk in chain.stream(
            {
                "context": context,
                "history": history_text,
                "question": query,
            },
        ):
            full_response += chunk
            yield chunk

        logger.info("Streamed response: %d chars, topic=%s", len(full_response), topic)

        return RAGResponse(
            content=full_response,
            sources=results,
            topic=topic,
        )
