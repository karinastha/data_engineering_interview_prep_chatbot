"""Preprocessing prompt for query transformation and topic extraction."""


def get_preprocessing_prompt() -> str:
    """
    Build preprocessing prompt with dynamic topic definitions from config.

    This ensures topic definitions stay in sync with config/topics.py.

    Returns:
        Formatted preprocessing prompt string.

    """
    # Import here to avoid circular dependency: topics.py may depend on prompts
    from config.topics import (  # noqa: PLC0415
        get_classification_rules_for_prompt,
        get_topic_definitions_for_prompt,
        get_topic_names,
    )

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
  → is_greeting: false

- History: []
  Current: "data warehouse vs lakehouse"
  → standalone_query: "What is the difference between data warehouse and data lakehouse?"
  → topic: "ETL"  (warehousing concepts are in ETL docs)
  → is_greeting: false

- History: []
  Current: "explain ACID properties"
  → standalone_query: "Explain ACID properties in databases"
  → topic: "Database"
  → is_greeting: false

- History: []
  Current: "give me real world ETL projects" or "show me hands-on projects"
  → standalone_query: "Real world data engineering projects"
  → topic: "Projects"
  → is_greeting: false

- History: []
  Current: "ETL project" or "ELT project" or "portfolio projects"
  → standalone_query: "Data engineering project assignments"
  → topic: "Projects"
  → is_greeting: false

- History: ["Assistant: I have hands-on projects: 1. ETL to Insights 2. ELT with dbt. Which interests you?"]
  Current: "ELT"
  → standalone_query: "ELT project details and requirements"
  → topic: "Projects"
  → is_greeting: false

- History: ["Assistant: Real-World Data Engineering Projects: 1. ETL project 2. ELT project"]
  Current: "ETL"
  → standalone_query: "ETL project specifications and implementation"
  → topic: "Projects"
  → is_greeting: false

- History: ["Assistant: Which project type interests you - ETL or ELT?"]
  Current: "tell me about the ELT one"
  → standalone_query: "ELT project details"
  → topic: "Projects"
  → is_greeting: false

- History: []
  Current: "hello" or "hi" or "hey" or "good morning"
  → standalone_query: "greeting"
  → topic: null
  → is_greeting: true

- History: []
  Current: "thanks" or "thank you"
  → standalone_query: "acknowledgment"
  → topic: null
  → is_greeting: true

IMPORTANT: Set is_greeting=true ONLY for pure greetings/thanks/small talk.
Questions like "hi, explain ETL" should have is_greeting=false.

Now process the current message:"""


# Pre-built prompt for backward compatibility
# Note: This is evaluated at import time, so topic config must be available
PREPROCESSING_PROMPT = get_preprocessing_prompt()
