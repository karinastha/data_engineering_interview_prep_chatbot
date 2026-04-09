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

KNOWLEDGE BASE TOPICS:
{get_topic_definitions_for_prompt()}

KEYWORD → TOPIC MAPPING:
{get_classification_rules_for_prompt()}

---

CONTEXT:
Previous messages: {{history}}
Current message: "{{message}}"

---

OUTPUT FIELDS:

1. standalone_query (string): Self-contained rewrite of the current message.
   - Resolve pronouns ("it", "that", "more") using previous messages.
   - Keep under 20 words.

2. topics (list of strings): Which knowledge base topic(s) to search.
   - Each value must be one of: {topic_list}
   - Usually one topic. Use multiple only when the query spans two areas.
   - Empty list only for greetings/small talk.

3. is_greeting (boolean): true only for pure greetings, thanks, or small talk.
   "hi, explain ETL" → false (has a technical question).

4. project_resource_types (list of strings): Which project download buttons to show.
   - Valid values: "ETL", "ELT". Empty list = no buttons.
   - Non-empty ONLY when user wants details about a SPECIFIC project.
   - CONSTRAINT: If non-empty, topics MUST be ["Projects"].

---

CLASSIFICATION PRIORITY (apply in order):

1. SPECIFIC PROJECT SELECTION: If the user is selecting a specific project
   (after seeing a project listing, or explicitly saying "ETL project" / "ELT project"):
   → topics: ["Projects"], project_resource_types: ["ETL"] or ["ELT"]
   IMPORTANT: "etl"/"elt" as bare words normally map to the ETL concept topic,
   BUT when the previous assistant message listed projects, the user is selecting a project.

2. PROJECT OVERVIEW: If asking about projects generally ("show me projects", "real world projects"):
   → topics: ["Projects"], project_resource_types: []

3. DEFAULT: Use the keyword → topic mapping above.

---

EXAMPLES:

Topic queries:
- "explain ACID properties"
  → standalone_query: "Explain ACID properties in databases"
  → topics: ["Database"], is_greeting: false, project_resource_types: []

- "data warehouse vs lakehouse"
  → standalone_query: "Difference between data warehouse and data lakehouse"
  → topics: ["ETL"], is_greeting: false, project_resource_types: []

- "compare SQL joins and pandas merges"
  → standalone_query: "Comparison of SQL joins and pandas DataFrame merges"
  → topics: ["SQL", "Python"], is_greeting: false, project_resource_types: []

- History: ["list comprehensions", "dictionary comprehensions?"]
  Current: "show me examples"
  → standalone_query: "Examples of dictionary comprehensions in Python"
  → topics: ["Python"], is_greeting: false, project_resource_types: []

Project overview (no download buttons):
- "show me real world projects" or "hands-on projects"
  → standalone_query: "Real world data engineering projects"
  → topics: ["Projects"], is_greeting: false, project_resource_types: []

Specific project (download buttons shown):
- "ETL project"
  → standalone_query: "ETL to Insights project details and requirements"
  → topics: ["Projects"], is_greeting: false, project_resource_types: ["ETL"]

- History: [Assistant listed projects: ETL to Insights, ELT with dbt]
  Current: "ELT" or "tell me about elt"
  → standalone_query: "ELT with dbt project details and requirements"
  → topics: ["Projects"], is_greeting: false, project_resource_types: ["ELT"]

- History: [Assistant listed projects: ETL to Insights, ELT with dbt]
  Current: "tell me about etl"
  → standalone_query: "ETL to Insights project details and requirements"
  → topics: ["Projects"], is_greeting: false, project_resource_types: ["ETL"]

Greetings:
- "hello" or "thanks"
  → standalone_query: "greeting"
  → topics: [], is_greeting: true, project_resource_types: []

Now process the current message:"""


# Pre-built prompt for backward compatibility
# Note: This is evaluated at import time, so topic config must be available
PREPROCESSING_PROMPT = get_preprocessing_prompt()
