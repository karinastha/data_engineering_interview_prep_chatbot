"""Query preprocessing service for transforming user messages."""

from langchain_core.exceptions import OutputParserException
from langchain_core.language_models import BaseChatModel
from langsmith import traceable
from pydantic import BaseModel, Field, ValidationError

from prompts import PREPROCESSING_PROMPT
from services.history import format_history_for_preprocessing
from utils.logging import get_logger

logger = get_logger(__name__)


def _get_topics_description() -> str:
    """Get dynamic topic list for Pydantic field description."""
    # Import here to avoid circular dependency: topics.py may depend on services
    from config.topics import get_topic_names  # noqa: PLC0415

    topics = get_topic_names()
    return (
        f"List of detected topics for metadata filtering. Each must be exactly one of: "
        f"{', '.join([repr(t) for t in topics])}. Empty list if no specific topic detected."
    )


class PreprocessedQuery(BaseModel):
    """
    Combined query transformation and topic extraction.

    This replaces the separate IntentAnalysis (app.py) and TransformedQuery (chat.py)
    with a single, focused preprocessing step.
    """

    standalone_query: str = Field(
        description=(
            "Rewritten query that is self-contained and doesn't need conversation "
            "history to understand. Resolve pronouns like 'it', 'that', 'this' using context."
        ),
    )
    topics: list[str] = Field(
        default_factory=list,
        description=_get_topics_description(),
    )
    is_greeting: bool = Field(
        default=False,
        description="True if message is a greeting/small talk that doesn't need retrieval",
    )
    project_resource_types: list[str] = Field(
        default_factory=list,
        description=(
            "List of specific project types to show download resources for. "
            "Valid values: 'ETL', 'ELT'. "
            "Non-empty ONLY when user wants details about a SPECIFIC project. "
            "CONSTRAINT: If non-empty, topics MUST be ['Projects']."
        ),
    )


class PreprocessingService:
    """Service for preprocessing user queries before retrieval."""

    def __init__(self, llm: BaseChatModel) -> None:
        """
        Initialize the preprocessing service.

        Args:
            llm: Language model for query transformation.

        """
        self.llm = llm

    @traceable(name="preprocess_query")
    def preprocess(
        self,
        message: str,
        history: list[dict],
    ) -> PreprocessedQuery:
        """
        Transform query and extract topic with a single LLM call.

        Args:
            message: User's current message.
            history: Conversation history.

        Returns:
            PreprocessedQuery with standalone_query and optional topic.

        Note:
            Gracefully degrades to original message if structured output parsing fails.
            This ensures the chat continues working even if preprocessing has issues.

        """
        history_text = format_history_for_preprocessing(history)

        prompt = PREPROCESSING_PROMPT.format(
            history=history_text,
            message=message,
        )

        try:
            structured_llm = self.llm.with_structured_output(PreprocessedQuery)
            result = structured_llm.invoke(prompt)

            # Enforce constraint: project resources require Projects topic
            if result.project_resource_types and "Projects" not in result.topics:
                logger.warning(
                    "Fixing topic mismatch: project_resources=%s but topics=%s "
                    "→ forcing topics=['Projects']",
                    result.project_resource_types,
                    result.topics,
                )
                result.topics = ["Projects"]

            logger.info(
                "Preprocessed: '%s' → query='%s', topics=%s, project_resources=%s",
                message,
                result.standalone_query,
                result.topics,
                result.project_resource_types,
            )

            return result

        except (OutputParserException, ValidationError) as e:
            # Graceful degradation: if LLM output parsing fails, use original message
            logger.warning("Preprocessing failed: %s, using original message", e)
            return PreprocessedQuery(
                standalone_query=message,
                topics=[],
            )
