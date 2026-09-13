"""
CSV Document Ingestion Module for Data Engineering Interview Prep Chatbot
Loads CSV files from data/raw_docs and creates a vector store using ChromaDB

Implements RAG Best Practices:
- Row-based chunking strategy (each CSV row = one document, no mid-row splits)
- Rich metadata tagging for topic filtering
- Structured content formatting for optimal retrieval
- Persistent vector store with ChromaDB
"""

import os
import sys
import pandas as pd
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from langchain_chroma import Chroma
from langchain_core.documents import Document
from utils.helper_cred import embeddings


def load_csv_files(data_dir: str = "data/raw_docs") -> list[Document]:
    """
    Load all CSV files from the data directory and convert them to LangChain documents.
    
    CHUNKING STRATEGY: Row-based chunking
    - Each CSV row becomes ONE document (no mid-row splits)
    - Preserves complete competency context (Must Have + Desirable + Advanced)
    - Rich metadata for topic filtering
    
    Args:
        data_dir: Path to directory containing CSV files
        
    Returns:
        List of LangChain Document objects with competency data and metadata
    """
    documents = []
    
    # CSV file mapping with topic metadata
    csv_files = {
        "Python": "DE docs - Python.csv",
        "SQL": "DE docs - SQL.csv",
        "Database": "DE docs - Database.csv",
        "ETL": "DE docs - ETL.csv"
    }
    
    for topic, filename in csv_files.items():
        file_path = os.path.join(data_dir, filename)
        
        if not os.path.exists(file_path):
            print(f"⚠️  Warning: {filename} not found, skipping...")
            continue
            
        print(f"📄 Loading {filename}...")
        
        try:
            # Read CSV file
            df = pd.read_csv(file_path)
            
            # ROW-BASED CHUNKING: Process each row as a complete document
            for idx, row in df.iterrows():
                # Skip empty rows or header rows
                if pd.isna(row.get('Topics')) or row.get('Topics') == '' or 'Competency Area' in str(row.get('Topics')):
                    continue
                
                # Extract information from each competency level (complete row context)
                subtopic = str(row.get('Topics', '')).strip()
                must_have = str(row.get('Must Have', '')).strip()
                desirable = str(row.get('Desirable', '')).strip()
                advanced = str(row.get('Advanced/ Best', '')).strip()
                
                # Skip if all competency levels are empty (invalid row)
                if not must_have and not desirable and not advanced:
                    continue
                
                # Create structured content - optimized for RAG retrieval
                # Format: Topic Area → Subtopic → Definition → Use Case → Example
                content_parts = [f"**Topic Area:** {topic}"]
                content_parts.append(f"**Subtopic:** {subtopic}")
                content_parts.append("")
                
                # Add competency levels with semantic markers for LLM understanding
                if must_have and must_have != 'nan':
                    content_parts.append("**📚 Definition/Must Have (Foundational):**")
                    content_parts.append(must_have)
                    content_parts.append("")
                
                if desirable and desirable != 'nan':
                    content_parts.append("**💡 Use Case/Desirable (Intermediate):**")
                    content_parts.append(desirable)
                    content_parts.append("")
                
                if advanced and advanced != 'nan':
                    content_parts.append("**🚀 Real-World Example/Advanced (Best Practice):**")
                    content_parts.append(advanced)
                    content_parts.append("")
                
                content = "\n".join(content_parts)
                
                # METADATA TAGGING: Rich metadata for filtering and retrieval
                # Critical for topic-specific searches (e.g., user selects "Python")
                doc = Document(
                    page_content=content,
                    metadata={
                        "topic": topic,  # PRIMARY FILTER: Python, SQL, Database, ETL
                        "subtopic": subtopic,  # Secondary filter for specific concepts
                        "source": filename,  # Source tracking
                        "row_index": idx,  # Row tracking for debugging
                        # Store competency levels for potential filtering
                        "must_have": must_have if must_have != 'nan' else "",
                        "desirable": desirable if desirable != 'nan' else "",
                        "advanced": advanced if advanced != 'nan' else "",
                        # Completeness indicator
                        "has_all_levels": bool(must_have and desirable and advanced)
                    }
                )
                
                documents.append(doc)
        
        except Exception as e:
            print(f"❌ Error loading {filename}: {str(e)}")
            continue
    
    print(f"✅ Loaded {len(documents)} documents from CSV files (row-based chunking)")
    return documents


def create_vector_store(documents: list[Document], persist_directory: str = "data/vector_db") -> Chroma:
    """
    Create and persist a ChromaDB vector store from documents.
    
    Args:
        documents: List of LangChain Document objects
        persist_directory: Directory to persist the vector store
        
    Returns:
        ChromaDB vector store
    """
    print(f"🔄 Creating vector store with {len(documents)} documents...")
    
    # Create vector store
    vectorstore = Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        persist_directory=persist_directory,
        collection_name="de_interview_prep"
    )
    
    print(f"✅ Vector store created and persisted to {persist_directory}")
    return vectorstore


def load_existing_vector_store(persist_directory: str = "data/vector_db") -> Chroma:
    """
    Load an existing vector store from disk.
    
    Args:
        persist_directory: Directory where vector store is persisted
        
    Returns:
        ChromaDB vector store
    """
    print(f"📂 Loading existing vector store from {persist_directory}...")
    
    vectorstore = Chroma(
        persist_directory=persist_directory,
        embedding_function=embeddings,
        collection_name="de_interview_prep"
    )
    
    print(" Vector store loaded successfully")
    return vectorstore


def initialize_vector_store(force_recreate: bool = False) -> Chroma:
    """
    Initialize vector store - create new or load existing.
    
    Args:
        force_recreate: If True, recreate vector store even if it exists
        
    Returns:
        ChromaDB vector store
    """
    persist_directory = "data/vector_db"
    
    # Check if vector store exists
    if os.path.exists(os.path.join(persist_directory, "chroma.sqlite3")) and not force_recreate:
        print("📦 Existing vector store found, loading...")
        return load_existing_vector_store(persist_directory)
    else:
        print("🆕 Creating new vector store...")
        documents = load_csv_files()
        return create_vector_store(documents, persist_directory)


if __name__ == "__main__":
    # Example usage: recreate vector store
    print("=" * 70)
    print("  DATA ENGINEERING INTERVIEW PREP - VECTOR STORE SETUP")
    print("=" * 70)
    print()
    
    vectorstore = initialize_vector_store(force_recreate=True)
    
    print()
    print("=" * 70)
    print("  SETUP COMPLETE!")
    print("=" * 70)
