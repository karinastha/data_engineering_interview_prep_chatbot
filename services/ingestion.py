"""
Document Ingestion Service
Handles loading CSV documents and creating/loading the vector store.

Responsibilities:
- Load CSV files from raw_docs directory
- Transform rows into LangChain Documents with metadata
- Create and persist ChromaDB vector store
- Load existing vector store
"""

import logging
from pathlib import Path
from typing import Optional

import pandas as pd
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

from config.settings import get_config, DataConfig, VectorStoreConfig

logger = logging.getLogger(__name__)


class IngestionService:
    """
    Service for ingesting CSV documents into a vector store.
    
    Uses row-based chunking strategy where each CSV row becomes
    a single document, preserving complete competency context.
    """
    
    def __init__(
        self,
        embeddings: Embeddings,
        data_config: Optional[DataConfig] = None,
        vector_store_config: Optional[VectorStoreConfig] = None,
    ):
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
        
        logger.info(f"Loading CSV files from {data_dir}")
        
        for topic, filename in self.data_config.csv_files.items():
            file_path = data_dir / filename
            
            if not file_path.exists():
                logger.warning(f"File not found: {filename}, skipping")
                continue
            
            try:
                topic_docs = self._process_csv_file(file_path, topic, filename)
                documents.extend(topic_docs)
                logger.info(f"Loaded {len(topic_docs)} documents from {filename}")
                
            except Exception as e:
                logger.error(f"Error loading {filename}: {e}")
                continue
        
        logger.info(f"Total documents loaded: {len(documents)}")
        return documents
    
    def _process_csv_file(
        self,
        file_path: Path,
        topic: str,
        filename: str
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
        filename: str
    ) -> Optional[Document]:
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
        subtopic = str(row.get('Topics', '')).strip()
        
        # Skip invalid rows (empty or header rows)
        if not subtopic or subtopic == 'nan' or 'Competency Area' in subtopic:
            return None
        
        must_have = self._clean_field(row.get('Must Have', ''))
        desirable = self._clean_field(row.get('Desirable', ''))
        advanced = self._clean_field(row.get('Advanced/ Best', ''))
        
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
            }
        )
    
    @staticmethod
    def _clean_field(value) -> str:
        """Clean and validate a field value."""
        if pd.isna(value):
            return ""
        text = str(value).strip()
        return "" if text == 'nan' else text
    
    @staticmethod
    def _format_content(
        topic: str,
        subtopic: str,
        must_have: str,
        desirable: str,
        advanced: str
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
            parts.extend([
                "Definition (Foundational):",
                must_have,
                "",
            ])
        
        if desirable:
            parts.extend([
                "Intermediate:",
                desirable,
                "",
            ])
        
        if advanced:
            parts.extend([
                "Advanced:",
                advanced,
                "",
            ])
        
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
        
        logger.info(f"Creating vector store with {len(documents)} documents")
        
        vectorstore = Chroma.from_documents(
            documents=documents,
            embedding=self.embeddings,
            persist_directory=persist_dir,
            collection_name=self.vector_store_config.collection_name,
            collection_metadata={"hnsw:space": "cosine"},  # Use cosine distance
        )
        
        logger.info(f"Vector store created at {persist_dir} (using cosine distance)")
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
            raise FileNotFoundError(
                f"Vector store not found at {persist_dir}. "
                "Run ingestion first to create it."
            )
        
        logger.info(f"Loading vector store from {persist_dir}")
        
        return Chroma(
            persist_directory=str(persist_dir),
            embedding_function=self.embeddings,
            collection_name=self.vector_store_config.collection_name,
        )
    
    def initialize(self, force_recreate: bool = False) -> Chroma:
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
        documents = self.load_csv_documents()
        
        if not documents:
            raise ValueError("No documents found to index. Check CSV files in raw_docs/")
        
        return self.create_vector_store(documents)
