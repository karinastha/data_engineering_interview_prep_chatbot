"""
Topic Configuration - Single Source of Truth

This module defines all available topics for the chatbot.
To add a new topic:
1. Add a TopicConfig entry to TOPICS list
2. Add the corresponding CSV file to data/raw_docs/
3. Run: python main.py init --force

That's it! The rest of the system reads from this config.
"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class TopicConfig:
    """
    Configuration for a single topic.
    
    Attributes:
        name: Internal name used for filtering (e.g., "Python")
        display_name: UI display name with emoji (e.g., "🐍 Python")
        csv_file: Filename in data/raw_docs/ (e.g., "DE docs - Python.csv")
        keywords: Terms that indicate this topic (for classification)
        description: Brief description for LLM context
        aliases: Alternative names/abbreviations (for fuzzy matching)
    """
    name: str
    display_name: str
    csv_file: str
    keywords: tuple  # Using tuple for immutability
    description: str
    aliases: tuple = ()  # Alternative names for fuzzy matching


# =============================================================================
# TOPIC DEFINITIONS - Add new topics here!
# =============================================================================

TOPICS: List[TopicConfig] = [
    TopicConfig(
        name="Python",
        display_name="🐍 Python",
        csv_file="DE docs - Python.csv",
        keywords=(
            "pandas", "numpy", "list comprehension", "dictionary comprehension",
            "decorator", "generator", "pyspark", "fastapi", "flask", "pytest",
            "type hints", "dataclass", "pydantic", "async", "asyncio"
        ),
        description="Core Python syntax, pandas, NumPy, APIs, data wrangling, PySpark basics, decorators, error handling",
        aliases=("py", "python3"),
    ),
    TopicConfig(
        name="SQL",
        display_name="💾 SQL",
        csv_file="DE docs - SQL.csv",
        keywords=(
            "select", "join", "inner join", "left join", "window function",
            "cte", "common table expression", "subquery", "group by", "having",
            "order by", "partition by", "row_number", "rank", "dense_rank",
            "lag", "lead", "query optimization", "explain", "index"
        ),
        description="Query syntax, joins, window functions, CTEs, subqueries, GROUP BY, query optimization",
        aliases=("query", "queries"),
    ),
    TopicConfig(
        name="Database",
        display_name="🗄️ Database",
        csv_file="DE docs - Database.csv",
        keywords=(
            "acid", "transaction", "normalization", "1nf", "2nf", "3nf",
            "rdbms", "schema design", "entity relationship", "er diagram",
            "primary key", "foreign key", "constraint", "index", "b-tree",
            "locking", "concurrency", "isolation level", "migration"
        ),
        description="RDBMS design, ACID properties, transactions, indexing, normalization, schema design, migrations",
        aliases=("db", "rdbms", "relational"),
    ),
    TopicConfig(
        name="ETL",
        display_name="🔄 ETL & Data Warehousing",
        csv_file="DE docs - ETL.csv",
        keywords=(
            "etl", "elt", "data pipeline", "data warehouse", "data lake",
            "lakehouse", "delta lake", "iceberg", "hudi", "medallion",
            "bronze", "silver", "gold", "star schema", "snowflake schema",
            "fact table", "dimension", "scd", "slowly changing dimension",
            "olap", "oltp", "redshift", "snowflake", "bigquery", "airflow",
            "dbt", "data modeling", "dimensional modeling", "batch", "streaming"
        ),
        description="Data pipelines, ETL/ELT patterns, data warehousing, OLAP, dimensional modeling, data lakes, lakehouses",
        aliases=("pipeline", "warehouse", "warehousing", "data engineering"),
    ),
    # -------------------------------------------------------------------------
    # NEW TOPICS - Add as CSV files become available
    # -------------------------------------------------------------------------
    # TopicConfig(
    #     name="Orchestration",
    #     display_name="🎭 Data Pipeline Orchestration",
    #     csv_file="DE docs - Orchestration.csv",
    #     keywords=(
    #         "airflow", "prefect", "dagster", "luigi", "dag", "task",
    #         "scheduling", "dependency", "retry", "sla", "orchestration"
    #     ),
    #     description="Workflow orchestration, DAGs, scheduling, task dependencies, Airflow, Prefect, Dagster",
    #     aliases=("airflow", "dag", "workflow"),
    # ),
    # TopicConfig(
    #     name="Streaming",
    #     display_name="🌊 Batch & Stream Processing",
    #     csv_file="DE docs - Streaming.csv",
    #     keywords=(
    #         "kafka", "kinesis", "pub/sub", "streaming", "real-time",
    #         "event-driven", "message queue", "batch processing"
    #     ),
    #     description="Batch vs streaming, Kafka, event-driven architecture, real-time processing",
    #     aliases=("kafka", "real-time", "events"),
    # ),
    # TopicConfig(
    #     name="Distributed",
    #     display_name="⚡ Distributed Engines",
    #     csv_file="DE docs - Distributed.csv",
    #     keywords=(
    #         "spark", "dask", "flink", "beam", "mapreduce", "distributed",
    #         "partition", "shuffle", "rdd", "dataframe", "catalyst"
    #     ),
    #     description="Spark, Dask, Flink, distributed computing, partitioning, MapReduce paradigm",
    #     aliases=("spark", "distributed computing"),
    # ),
    # ... more topics as needed
]


# =============================================================================
# HELPER FUNCTIONS - Used by other modules
# =============================================================================

def get_topic_names() -> List[str]:
    """Get list of all topic names (internal names)."""
    return [t.name for t in TOPICS]


def get_topic_display_names() -> List[str]:
    """Get list of all display names (for UI)."""
    return [t.display_name for t in TOPICS]


def get_topic_display_string() -> str:
    """Get formatted string of topics for welcome message."""
    return " | ".join(get_topic_display_names())


def get_csv_file_mapping() -> dict:
    """Get mapping of topic name to CSV filename (for ingestion)."""
    return {t.name: t.csv_file for t in TOPICS}


def get_topic_by_name(name: str) -> Optional[TopicConfig]:
    """Get TopicConfig by exact name match."""
    for topic in TOPICS:
        if topic.name.lower() == name.lower():
            return topic
    return None


def get_topic_definitions_for_prompt() -> str:
    """
    Generate topic definitions section for LLM prompts.
    
    Returns:
        Formatted string like:
        - Python: Core Python syntax, pandas, NumPy...
        - SQL: Query syntax, joins, window functions...
    """
    lines = []
    for t in TOPICS:
        lines.append(f"- {t.name}: {t.description}")
    return "\n".join(lines)


def get_classification_rules_for_prompt() -> str:
    """
    Generate classification rules section for LLM prompts.
    
    Returns:
        Formatted string like:
        - "pandas", "list comprehensions", "decorators" → Python
        - "joins", "window functions", "CTE" → SQL
    """
    lines = []
    for t in TOPICS:
        # Take first 4 keywords as examples
        example_keywords = list(t.keywords)[:4]
        keywords_str = '", "'.join(example_keywords)
        lines.append(f'- "{keywords_str}" → {t.name}')
    return "\n".join(lines)


def match_topic(value: str) -> Optional[str]:
    """
    Match a string to a topic using fuzzy matching.
    
    Checks:
    1. Exact name match
    2. Alias match
    3. Keyword containment
    
    Args:
        value: String to match (case-insensitive)
        
    Returns:
        Topic name if matched, None otherwise
    """
    if not value:
        return None
        
    value_lower = value.lower().strip()
    
    # Check exact name match
    for topic in TOPICS:
        if topic.name.lower() == value_lower:
            return topic.name
    
    # Check aliases
    for topic in TOPICS:
        if value_lower in [a.lower() for a in topic.aliases]:
            return topic.name
    
    # Check if value contains any keyword
    for topic in TOPICS:
        for keyword in topic.keywords:
            if keyword.lower() in value_lower:
                return topic.name
    
    # Check if any keyword contains the value (reverse check)
    for topic in TOPICS:
        for keyword in topic.keywords:
            if value_lower in keyword.lower() and len(value_lower) >= 3:
                return topic.name
    
    return None
