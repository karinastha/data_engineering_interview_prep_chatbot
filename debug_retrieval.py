"""Debug script to check retrieval and similarity scores."""
from langchain_chroma import Chroma
from utils.helper_cred import get_embeddings
from pathlib import Path

# Load vector store
persist_dir = Path('data/vector_db')
embeddings = get_embeddings()
vectorstore = Chroma(
    collection_name='de_interview_prep',
    embedding_function=embeddings,
    persist_directory=str(persist_dir)
)

print("="*60)
print("RAW SIMILARITY SEARCH (no filter)")
print("="*60)

results = vectorstore.similarity_search_with_score("SQL joins", k=5)
for doc, score in results:
    topic = doc.metadata.get("topic")
    content_preview = doc.page_content[:100].replace("\n", " ")
    print(f"Score: {score:.4f} | Topic: {topic} | {content_preview}...")

print("\n" + "="*60)
print("WITH TOPIC FILTER (SQL)")
print("="*60)

results = vectorstore.similarity_search_with_score("SQL joins", k=5, filter={"topic": "SQL"})
for doc, score in results:
    topic = doc.metadata.get("topic")
    content_preview = doc.page_content[:100].replace("\n", " ")
    print(f"Score: {score:.4f} | Topic: {topic} | {content_preview}...")

print("\n" + "="*60)
print("SIMILARITY CONVERSION TEST")
print("="*60)
print("ChromaDB returns DISTANCE (lower = better)")
print("If score ~0.5-1.5, these are distances, not similarities!")
print("Conversion: similarity = 1 - distance")
print()

# Show what the threshold filter is doing
threshold = 0.3
for doc, distance_score in results[:3]:
    similarity = 1.0 - distance_score
    similarity_clamped = max(0.0, min(1.0, similarity))
    passes = similarity_clamped >= threshold
    print(f"Distance: {distance_score:.4f} -> Similarity: {similarity_clamped:.4f} -> Passes {threshold}: {passes}")
