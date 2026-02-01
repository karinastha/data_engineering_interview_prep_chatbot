# """
# Data Ingestion Module for Data Engineering Interview Prep Chatbot

# This module handles:
# 1. Loading CSV documents from data/raw_docs/
# 2. Creating embeddings using AWS Bedrock or OpenAI
# 3. Storing vectors in ChromaDB
# 4. Providing retrieval functionality for RAG-based Q&A
# """

# import os
# import sys
# import pandas as pd
# from pathlib import Path
# from typing import List, Dict, Optional

# # Add parent directory to path for imports
# sys.path.append(str(Path(__file__).parent.parent))

# from langchain_community.vectorstores import Chroma
# from langchain_core.documents import Document
# from langchain_text_splitters import RecursiveCharacterTextSplitter
# from utils.helper_cred import embeddings as bedrock_embeddings


# class DataEngineeringDocsIngestor:
#     """
#     Handles ingestion of Data Engineering documentation into vector database.
#     Supports multiple topics: Python, SQL, Database, AWS
#     """
    
#     def __init__(
#         self,
#         data_dir: str = "data/raw_docs",
#         vector_db_dir: str = "data/vector_db",
#         collection_name: str = "de_interview_docs"
#     ):
#         """
#         Initialize the ingestion pipeline.
        
#         Args:
#             data_dir: Directory containing CSV files
#             vector_db_dir: Directory to store ChromaDB
#             collection_name: Name for the ChromaDB collection
#         """
#         self.data_dir = Path(data_dir)
#         self.vector_db_dir = Path(vector_db_dir)
#         self.collection_name = collection_name
        
#         # Use embeddings from helper_cred (AWS Bedrock Titan)
#         self.embeddings = bedrock_embeddings
        
#         # Topic mapping to CSV files
#         self.topic_files = {
#             "Python": "DE docs - Python.csv",
#             "SQL": "DE docs - SQL.csv",
#             "Database": "DE docs - Database.csv",
#             "ETL": "DE docs - ETL.csv"
#         }
    
#     def load_csv_documents(self, topic: Optional[str] = None) -> List[Document]:
#         """
#         Load CSV files and convert to LangChain Documents.
        
#         Args:
#             topic: Specific topic to load (Python, SQL, Database, ETL). 
#                    If None, loads all topics.
        
#         Returns:
#             List of Document objects with metadata
#         """
#         documents = []
        
#         # Determine which files to load
#         if topic and topic in self.topic_files:
#             files_to_load = {topic: self.topic_files[topic]}
#         else:
#             files_to_load = self.topic_files
        
#         for topic_name, filename in files_to_load.items():
#             filepath = self.data_dir / filename
            
#             if not filepath.exists():
#                 print(f"Warning: File not found - {filepath}")
#                 continue
            
#             print(f"Loading {topic_name} documentation from {filename}...")
            
#             # Read CSV file
#             df = pd.read_csv(filepath)
            
#             # Process each row into a structured document
#             for idx, row in df.iterrows():
#                 # Skip header rows or empty content
#                 if pd.isna(row.get('Topics')) or row.get('Topics') == 'Topics':
#                     continue
                
#                 # Create structured content
#                 content = self._create_document_content(row)
                
#                 # Create document with rich metadata
#                 doc = Document(
#                     page_content=content,
#                     metadata={
#                         "topic": topic_name,
#                         "competency_area": row.get('Competency Area', ''),
#                         "subtopic": row.get('Topics', ''),
#                         "source": filename,
#                         "row_index": idx
#                     }
#                 )
#                 documents.append(doc)
        
#         print(f"Loaded {len(documents)} documents")
#         return documents
    
#     def _create_document_content(self, row: pd.Series) -> str:
#         """
#         Create structured content from CSV row.
        
#         Args:
#             row: DataFrame row
        
#         Returns:
#             Formatted document content
#         """
#         content_parts = []
        
#         # Topic/Subject
#         if pd.notna(row.get('Topics')):
#             content_parts.append(f"Topic: {row['Topics']}")
        
#         # Competency levels
#         if pd.notna(row.get('Must Have')):
#             content_parts.append(f"Must Have: {row['Must Have']}")
        
#         if pd.notna(row.get('Desirable')):
#             content_parts.append(f"Desirable: {row['Desirable']}")
        
#         if pd.notna(row.get('Advanced/ Best')):
#             content_parts.append(f"Advanced/Best: {row['Advanced/ Best']}")
        
#         return "\n\n".join(content_parts)
    
#     def chunk_documents(
#         self,
#         documents: List[Document],
#         chunk_size: int = 1000,
#         chunk_overlap: int = 200
#     ) -> List[Document]:
#         """
#         Split documents into smaller chunks for better retrieval.
        
#         Args:
#             documents: List of documents to chunk
#             chunk_size: Maximum size of each chunk
#             chunk_overlap: Overlap between chunks
        
#         Returns:
#             List of chunked documents
#         """
#         text_splitter = RecursiveCharacterTextSplitter(
#             chunk_size=chunk_size,
#             chunk_overlap=chunk_overlap,
#             separators=["\n\n", "\n", ". ", " ", ""]
#         )
        
#         chunks = text_splitter.split_documents(documents)
#         print(f"Split into {len(chunks)} chunks")
#         return chunks
    
#     def create_vector_store(
#         self,
#         documents: List[Document],
#         force_recreate: bool = False
#     ) -> Chroma:
#         """
#         Create or load ChromaDB vector store.
        
#         Args:
#             documents: Documents to embed and store
#             force_recreate: If True, delete existing DB and recreate
        
#         Returns:
#             ChromaDB vector store
#         """
#         # Create vector_db directory if it doesn't exist
#         self.vector_db_dir.mkdir(parents=True, exist_ok=True)
        
#         # Check if vector store already exists
#         if force_recreate and self.vector_db_dir.exists():
#             print(f"Recreating vector store at {self.vector_db_dir}")
#             import shutil
#             if (self.vector_db_dir / "chroma.sqlite3").exists():
#                 shutil.rmtree(self.vector_db_dir)
        
#         # Create vector store
#         print(f"Creating vector store with {len(documents)} documents...")
#         vectorstore = Chroma.from_documents(
#             documents=documents,
#             embedding=self.embeddings,
#             persist_directory=str(self.vector_db_dir),
#             collection_name=self.collection_name
#         )
        
#         print(f"Vector store created successfully at {self.vector_db_dir}")
#         return vectorstore
    
#     def load_existing_vector_store(self) -> Optional[Chroma]:
#         """
#         Load existing vector store from disk.
        
#         Returns:
#             ChromaDB vector store or None if doesn't exist
#         """
#         if not (self.vector_db_dir / "chroma.sqlite3").exists():
#             print("No existing vector store found")
#             return None
        
#         print(f"Loading existing vector store from {self.vector_db_dir}")
#         vectorstore = Chroma(
#             persist_directory=str(self.vector_db_dir),
#             embedding_function=self.embeddings,
#             collection_name=self.collection_name
#         )
        
#         return vectorstore
    
#     def ingest_all(self, force_recreate: bool = False) -> Chroma:
#         """
#         Complete ingestion pipeline: load, chunk, embed, store.
        
#         Args:
#             force_recreate: If True, recreate vector store from scratch
        
#         Returns:
#             ChromaDB vector store
#         """
#         # Load all documents
#         documents = self.load_csv_documents()
        
#         # Chunk documents
#         chunks = self.chunk_documents(documents)
        
#         # Create vector store
#         vectorstore = self.create_vector_store(chunks, force_recreate=force_recreate)
        
#         return vectorstore
    
#     def get_retriever(self, search_type: str = "similarity", k: int = 5):
#         """
#         Get a retriever for the vector store.
        
#         Args:
#             search_type: Type of search ("similarity", "mmr")
#             k: Number of documents to retrieve
        
#         Returns:
#             Retriever object
#         """
#         vectorstore = self.load_existing_vector_store()
        
#         if vectorstore is None:
#             print("Vector store not found. Running ingestion...")
#             vectorstore = self.ingest_all()
        
#         return vectorstore.as_retriever(
#             search_type=search_type,
#             search_kwargs={"k": k}
#         )


# def main():
#     """
#     Main function to run ingestion pipeline.
#     """
#     print("="*60)
#     print("Data Engineering Interview Prep - Document Ingestion")
#     print("="*60)
    
#     # Initialize ingestor (uses AWS Bedrock embeddings from helper_cred)
#     ingestor = DataEngineeringDocsIngestor()
    
#     # Run full ingestion
#     vectorstore = ingestor.ingest_all(force_recreate=True)
    
#     print("\n" + "="*60)
#     print("Ingestion Complete!")
#     print("="*60)
    
#     # Test retrieval
#     print("\nTesting retrieval with sample query...")
#     query = "What are Python comprehensions?"
#     results = vectorstore.similarity_search(query, k=3)
    
#     print(f"\nQuery: {query}")
#     print(f"Found {len(results)} relevant documents:\n")
#     for i, doc in enumerate(results, 1):
#         print(f"{i}. Topic: {doc.metadata.get('topic')}")
#         print(f"   Subtopic: {doc.metadata.get('subtopic')}")
#         print(f"   Content: {doc.page_content[:200]}...")
#         print()


# if __name__ == "__main__":
#     main()