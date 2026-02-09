"""
Document Ingestion Service.

Handles loading CSV documents and creating/loading the vector store.

Responsibilities:
- Load CSV files from raw_docs directory
- Transform rows into LangChain Documents with metadata
- Create and persist ChromaDB vector store
- Load existing vector store
"""

import re
from pathlib import Path

import pandas as pd
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

from config.settings import DataConfig, VectorStoreConfig, get_config
from utils.logging import get_logger

logger = get_logger(__name__)

MIN_SECTION_LENGTH = 50  # Minimum characters for a valid section


class IngestionService:
    """
    Service for ingesting CSV documents into a vector store.

    Uses row-based chunking strategy where each CSV row becomes
    a single document, preserving complete competency context.
    """

    def __init__(
        self,
        embeddings: Embeddings,
        data_config: DataConfig | None = None,
        vector_store_config: VectorStoreConfig | None = None,
    ) -> None:
        """
        Initialize the ingestion service.

        Args:
            embeddings: Embedding model for document vectorization
            data_config: Data source configuration (uses default if None)
            vector_store_config: Vector store configuration (uses default if None)

        """
        config = get_config()
        self.embeddings = embeddings
        self.data_config = data_config or config.data
        self.vector_store_config = vector_store_config or config.vector_store
        self.project_root = config.project_root

    def load_csv_documents(self) -> list[Document]:
        """
        Load all CSV files and convert to LangChain Documents.

        Each CSV row becomes ONE document with:
        - Structured content combining all competency levels
        - Rich metadata for filtering (topic, subtopic, source)

        Returns:
            List of Document objects ready for vectorization

        """
        documents = []
        data_dir = self.project_root / self.data_config.raw_docs_directory

        logger.info("Loading CSV files from %s", data_dir)

        for topic, filename in self.data_config.csv_files.items():
            file_path = data_dir / filename

            if not file_path.exists():
                logger.warning("File not found: %s, skipping", filename)
                continue

            topic_docs = self._process_csv_file(file_path, topic, filename)
            documents.extend(topic_docs)
            logger.info("Loaded %d documents from %s", len(topic_docs), filename)

        logger.info("Total documents loaded: %d", len(documents))
        return documents

    def _process_csv_file(
        self,
        file_path: Path,
        topic: str,
        filename: str,
    ) -> list[Document]:
        """
        Process a single CSV file into documents.

        Args:
            file_path: Path to the CSV file
            topic: Topic label for metadata
            filename: Source filename for tracking

        Returns:
            List of Document objects from this file

        """
        documents = []
        df = pd.read_csv(file_path)

        for idx, row in df.iterrows():
            doc = self._row_to_document(row, idx, topic, filename)
            if doc:
                documents.append(doc)

        return documents

    def _row_to_document(
        self,
        row: pd.Series,
        row_idx: int,
        topic: str,
        filename: str,
    ) -> Document | None:
        """
        Convert a single CSV row to a structured Document.

        Args:
            row: DataFrame row
            row_idx: Row index for tracking
            topic: Topic label
            filename: Source file

        Returns:
            Document object or None if row is invalid

        """
        # Extract and validate fields
        subtopic = str(row.get("Topics", "")).strip()

        # Skip invalid rows (empty or header rows)
        if not subtopic or subtopic == "nan" or "Competency Area" in subtopic:
            return None

        must_have = self._clean_field(row.get("Must Have", ""))
        desirable = self._clean_field(row.get("Desirable", ""))
        advanced = self._clean_field(row.get("Advanced/ Best", ""))

        # Skip if all levels empty
        if not any([must_have, desirable, advanced]):
            return None

        # Build structured content
        content = self._format_content(topic, subtopic, must_have, desirable, advanced)

        # Create document with rich metadata
        return Document(
            page_content=content,
            metadata={
                "topic": topic,
                "subtopic": subtopic,
                "source": filename,
                "row_index": row_idx,
                "has_all_levels": bool(must_have and desirable and advanced),
            },
        )

    @staticmethod
    def _clean_field(value) -> str:
        """Clean and validate a field value."""
        if pd.isna(value):
            return ""
        text = str(value).strip()
        return "" if text == "nan" else text

    @staticmethod
    def _format_content(
        topic: str,
        subtopic: str,
        must_have: str,
        desirable: str,
        advanced: str,
    ) -> str:
        """
        Format document content for optimal retrieval.

        Structure optimized for semantic search and LLM consumption.
        """
        parts = [
            f"Topic: {topic}",
            f"Subtopic: {subtopic}",
            "",
        ]

        if must_have:
            parts.extend(
                [
                    "Definition (Foundational):",
                    must_have,
                    "",
                ],
            )

        if desirable:
            parts.extend(
                [
                    "Intermediate:",
                    desirable,
                    "",
                ],
            )

        if advanced:
            parts.extend(
                [
                    "Advanced:",
                    advanced,
                    "",
                ],
            )

        return "\n".join(parts)

    def create_vector_store(self, documents: list[Document]) -> Chroma:
        """
        Create and persist a new vector store from documents.

        Uses cosine distance for similarity search (optimal for normalized embeddings).

        Args:
            documents: List of documents to index

        Returns:
            ChromaDB vector store instance

        """
        persist_dir = str(self.project_root / self.vector_store_config.persist_directory)

        logger.info("Creating vector store with %d documents", len(documents))

        vectorstore = Chroma.from_documents(
            documents=documents,
            embedding=self.embeddings,
            persist_directory=persist_dir,
            collection_name=self.vector_store_config.collection_name,
            collection_metadata={"hnsw:space": "cosine"},  # Use cosine distance
        )

        logger.info("Vector store created at %s (using cosine distance)", persist_dir)
        return vectorstore

    def load_vector_store(self) -> Chroma:
        """
        Load an existing vector store from disk.

        Returns:
            ChromaDB vector store instance

        Raises:
            FileNotFoundError: If vector store doesn't exist

        """
        persist_dir = self.project_root / self.vector_store_config.persist_directory
        db_file = persist_dir / "chroma.sqlite3"

        if not db_file.exists():
            msg = f"Vector store not found at {persist_dir}. Run ingestion first to create it."
            raise FileNotFoundError(
                msg,
            )

        logger.info("Loading vector store from %s", persist_dir)

        return Chroma(
            persist_directory=str(persist_dir),
            embedding_function=self.embeddings,
            collection_name=self.vector_store_config.collection_name,
        )

    def initialize(self, *, force_recreate: bool = False) -> Chroma:
        """
        Initialize vector store - create new or load existing.

        Args:
            force_recreate: If True, recreate even if exists

        Returns:
            ChromaDB vector store ready for use

        """
        persist_dir = self.project_root / self.vector_store_config.persist_directory
        db_exists = (persist_dir / "chroma.sqlite3").exists()

        if db_exists and not force_recreate:
            logger.info("Found existing vector store, loading...")
            return self.load_vector_store()

        logger.info("Creating new vector store...")

        # Load CSV documents (competency-based content)
        documents = self.load_csv_documents()

        # Load markdown project documents
        project_docs = self.load_project_documents()
        documents.extend(project_docs)

        if not documents:
            msg = "No documents found to index. Check CSV files in raw_docs/"
            raise ValueError(msg)

        return self.create_vector_store(documents)

    def load_project_documents(self) -> list[Document]:
        """
        Load project markdown files with section-based chunking.

        Each major section (## heading) becomes a document for better retrieval.
        Also creates a summary document for project overview queries.

        Returns:
            List of Document objects from project files

        """
        documents = []
        projects_dir = self.project_root / self.data_config.projects_directory

        if not projects_dir.exists():
            logger.warning("Projects directory not found: %s", projects_dir)
            return documents

        logger.info("Loading project files from %s", projects_dir)

        # Project file definitions
        project_files = {
            "ETL_INSIGHTS.md": {
                "project_type": "ETL",
                "title": "ETL to Insights Assignment",
                "description": "Build a complete ETL pipeline with Python, analytics with SQL, "
                "API development, and visualization",
            },
            "ELT_DBT.md": {
                "project_type": "ELT",
                "title": "E-Commerce ELT Pipeline with dbt",
                "description": "Production-grade ELT pipeline extracting from REST API, loading "
                "to PostgreSQL, transforming with dbt",
            },
        }

        # Create project overview document (retrieved when user asks "what projects are available")
        overview_content = self._create_projects_overview(project_files)
        documents.append(
            Document(
                page_content=overview_content,
                metadata={
                    "topic": "Projects",
                    "subtopic": "Overview",
                    "source": "project_overview",
                    "project_type": "all",
                },
            ),
        )

        # Load each project file
        for filename, meta in project_files.items():
            file_path = projects_dir / filename

            if not file_path.exists():
                logger.warning("Project file not found %s: %s", filename, file_path)
                continue

            try:
                project_docs = self._process_markdown_file(file_path, meta)
                documents.extend(project_docs)
                logger.info("Loaded %d chunks from %s", len(project_docs), filename)

            except Exception:
                logger.exception("Error loading %s", filename)
                continue

        logger.info("Total project documents loaded: %d", len(documents))
        return documents

    def _create_projects_overview(self, project_files: dict) -> str:
        """Create overview content for project listing queries."""
        lines = [
            "Topic: Projects",
            "Subtopic: Available Projects Overview",
            "",
            "Real-World Data Engineering Projects:",
            "",
        ]

        for i, (_filename, meta) in enumerate(project_files.items(), 1):
            lines.extend(
                [
                    f"{i}. **{meta['title']}** ({meta['project_type']})",
                    f"   {meta['description']}",
                    "",
                ],
            )

        lines.extend(
            [
                "Ask about a specific project type (ETL or ELT) to get full details.",
            ],
        )

        return "\n".join(lines)

    def _process_markdown_file(
        self,
        file_path: Path,
        meta: dict,
    ) -> list[Document]:
        """
        Process a markdown file into section-based chunks.

        Strategy:
        - Split on ## headers (major sections)
        - Each section becomes a document
        - Preserve section context in content

        Args:
            file_path: Path to markdown file
            meta: Project metadata dict

        Returns:
            List of Document objects

        """
        documents = []
        content = file_path.read_text(encoding="utf-8")

        # Split on ## headers (keep the header with the content)
        sections = re.split(r"\n(?=## )", content)

        for section in sections:
            cleaned_section = section.strip()
            if not cleaned_section or len(cleaned_section) < MIN_SECTION_LENGTH:
                continue

            # Extract section title
            title_match = re.match(r"^##\s*(.+?)(?:\n|$)", cleaned_section)
            section_title = title_match.group(1).strip() if title_match else "Overview"

            # Clean section title (remove markdown formatting)
            section_title = re.sub(r"\*\*|\*|`", "", section_title)

            # Create document with project context
            doc_content = f"Topic: Projects\nProject: {meta['title']}\nProject Type: "
            f"{meta['project_type']}\nSection: {section_title}\n\n{cleaned_section}"

            documents.append(
                Document(
                    page_content=doc_content,
                    metadata={
                        "topic": "Projects",
                        "subtopic": section_title,
                        "source": file_path.name,
                        "project_type": meta["project_type"],
                        "project_title": meta["title"],
                    },
                ),
            )

        return documents
