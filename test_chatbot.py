"""
Quick test script to verify the chatbot functionality
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.ingestion_csv import initialize_vector_store
from src.rag_retrieval import create_rag_system

print("=" * 70)
print("  TESTING DATA ENGINEERING INTERVIEW PREP CHATBOT")
print("=" * 70)
print()

# Initialize system
print("🔄 Initializing vector store and RAG system...")
vectorstore = initialize_vector_store()
rag = create_rag_system(vectorstore)
print("✅ System initialized successfully!")
print()

# Test 1: Generate practice questions for Python
print("=" * 70)
print("TEST 1: Generate Python practice questions")
print("=" * 70)
print()

response = rag.generate_practice_questions("Python")
print(response)
print()

# Test 2: Answer specific question
print("=" * 70)
print("TEST 2: Answer specific question about list comprehensions")
print("=" * 70)
print()

question = "Explain list comprehensions in Python with use cases and examples"
response = rag.answer_question(question, topic="Python")
print(response)
print()

print("=" * 70)
print("  ALL TESTS COMPLETED SUCCESSFULLY! ✅")
print("=" * 70)
print()
print("🚀 The chatbot is ready to use!")
print("   Run: streamlit run app.py")
