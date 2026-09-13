"""Test RAG System"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.ingestion_csv import initialize_vector_store
from src.rag_retrieval import create_rag_system

print("="*70)
print("Testing RAG System")
print("="*70)

print("\n1. Loading vector store...")
vectorstore = initialize_vector_store()

print("\n2. Creating RAG system...")
rag = create_rag_system(vectorstore)

print("\n3. Testing Python question generation...")
try:
    result = rag.generate_practice_questions("Python")
    print(f"\n✅ SUCCESS! Generated {len(result)} characters")
    print("\nFirst 500 characters:")
    print("-" * 70)
    print(result[:500])
    print("-" * 70)
except Exception as e:
    print(f"\n❌ FAILED: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n" + "="*70)
print("Test Complete")
print("="*70)
