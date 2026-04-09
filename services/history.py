"""Conversation history formatting utilities."""

# Default configuration values
DEFAULT_MAX_MESSAGES = 6
PREPROCESSING_TRUNCATION_LENGTH = 600
GENERATION_TRUNCATION_LENGTH = 300


def format_history_for_preprocessing(
    messages: list[dict],
    max_messages: int = DEFAULT_MAX_MESSAGES,
) -> str:
    """
    Format conversation history for preprocessing prompt.

    Includes BOTH user and assistant messages to properly handle:
    - User selections from choices offered by assistant
    - Follow-up questions that reference assistant responses
    - Context from previous exchanges

    The last assistant message is especially important when user is making a selection.

    Args:
        messages: List of message dicts with 'role' and 'content' keys.
        max_messages: Maximum number of recent messages to include.

    Returns:
        Formatted string of recent conversation history.

    """
    if not messages:
        return "No previous messages."

    recent = messages[-max_messages:]

    if not recent:
        return "No previous messages."

    formatted = []
    for msg in recent:
        role = "User" if msg["role"] == "user" else "Assistant"
        content = msg["content"]
        if len(content) > PREPROCESSING_TRUNCATION_LENGTH:
            content = content[:PREPROCESSING_TRUNCATION_LENGTH] + "..."
        formatted.append(f"{role}: {content}")

    return "\n".join(formatted) if formatted else "No previous messages."


def format_history_for_generation(
    messages: list[dict],
    max_messages: int = DEFAULT_MAX_MESSAGES,
) -> str:
    """
    Format conversation history for answer generation.

    Includes both user and assistant messages for context.

    Args:
        messages: List of message dicts with 'role' and 'content' keys.
        max_messages: Maximum number of recent messages to include.

    Returns:
        Formatted string of recent conversation history.

    """
    if not messages:
        return "No previous conversation."

    recent = messages[-max_messages:]

    formatted = []
    for msg in recent:
        role = "User" if msg["role"] == "user" else "Assistant"
        content = msg["content"]
        if len(content) > GENERATION_TRUNCATION_LENGTH:
            content = content[:GENERATION_TRUNCATION_LENGTH] + "..."
        formatted.append(f"{role}: {content}")

    return "\n".join(formatted)
