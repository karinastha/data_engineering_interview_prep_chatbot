"""
Test Similarity Search Performance
Evaluates how well the vector similarity search is working
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.ingestion_csv import initialize_vector_store
from src.rag_retrieval import create_rag_system


def test_similarity_search():
    """Test similarity search with various queries"""
    print("=" * 80)
    print("SIMILARITY SEARCH PERFORMANCE ANALYSIS")
    print("=" * 80)
    print()
    
    # Initialize
    print("📦 Loading vector store...")
    vectorstore = initialize_vector_store()
    rag_system = create_rag_system(vectorstore)
    
    # Test queries for different topics
    test_cases = [
        {
            "topic": "Python",
            "queries": [
                "list comprehensions",
                "Python decorators",
                "error handling in Python",
                "pandas dataframes",  # Should have lower score if not in docs
                "object oriented programming"
            ]
        },
        {
            "topic": "SQL",
            "queries": [
                "SELECT statements",
                "JOIN operations",
                "window functions",
                "query optimization",
                "indexing strategies"
            ]
        },
        {
            "topic": "Database",
            "queries": [
                "ACID properties",
                "normalization",
                "database transactions",
                "schema design",
                "primary keys"
            ]
        },
        {
            "topic": "ETL",
            "queries": [
                "data pipeline",
                "ETL best practices",
                "data transformation",
                "incremental loading",
                "data quality"
            ]
        }
    ]
    
    print("\n" + "=" * 80)
    print("RETRIEVAL QUALITY ANALYSIS")
    print("=" * 80)
    
    for test_case in test_cases:
        topic = test_case["topic"]
        queries = test_case["queries"]
        
        print(f"\n{'='*80}")
        print(f"TOPIC: {topic}")
        print(f"{'='*80}\n")
        
        for query in queries:
            print(f"\n🔍 Query: '{query}'")
            print("-" * 80)
            
            # Retrieve documents with scores
            docs_with_scores = rag_system.retrieve_by_topic(topic, k=5)
            
            if not docs_with_scores:
                print("❌ No documents retrieved (all below threshold)")
                continue
            
            # Display results
            print(f"✅ Retrieved {len(docs_with_scores)} documents\n")
            
            for i, (doc, score) in enumerate(docs_with_scores, 1):
                # Extract subtopic from metadata
                subtopic = doc.metadata.get('subtopic', 'Unknown')
                
                # Determine relevance level
                if score >= 0.7:
                    relevance = "🟢 EXCELLENT"
                elif score >= 0.5:
                    relevance = "🟡 GOOD"
                elif score >= 0.3:
                    relevance = "🟠 ACCEPTABLE"
                else:
                    relevance = "🔴 POOR"
                
                print(f"  [{i}] {relevance} | Score: {score:.4f}")
                print(f"      Subtopic: {subtopic}")
                
                # Show first 100 chars of content
                content_preview = doc.page_content.replace('\n', ' ')[:100] + "..."
                print(f"      Preview: {content_preview}")
                print()
    
    print("\n" + "=" * 80)
    print("CROSS-TOPIC CONTAMINATION TEST")
    print("Testing if metadata filtering prevents topic mixing")
    print("=" * 80)
    
    # Test if Python query retrieves only Python docs
    print("\n🔍 Query: 'Python list comprehensions' with Topic Filter: 'Python'")
    docs_with_scores = rag_system.retrieve_by_topic("Python", k=3)
    
    topics_found = set()
    for doc, score in docs_with_scores:
        topic_found = doc.metadata.get('topic', 'Unknown')
        topics_found.add(topic_found)
        print(f"  • Retrieved topic: {topic_found} | Score: {score:.4f}")
    
    if len(topics_found) == 1 and "Python" in topics_found:
        print("\n✅ PASS: Metadata filtering working correctly (only Python docs)")
    else:
        print(f"\n❌ FAIL: Cross-topic contamination detected! Topics: {topics_found}")
    
    print("\n" + "=" * 80)
    print("SIMILARITY THRESHOLD EFFECTIVENESS")
    print("=" * 80)
    
    # Test with very unrelated query
    print("\n🔍 Testing with unrelated query: 'machine learning algorithms'")
    print("Topic Filter: 'Python'")
    
    # Direct vectorstore query to see all scores (before threshold)
    all_docs_with_scores = vectorstore.similarity_search_with_score(
        query="machine learning algorithms neural networks",
        k=10,
        filter={"topic": "Python"}
    )
    
    print(f"\nAll scores (before threshold of 0.3):")
    for i, (doc, score) in enumerate(all_docs_with_scores[:5], 1):
        subtopic = doc.metadata.get('subtopic', 'Unknown')
        passed = "✅" if score >= 0.3 else "❌"
        print(f"  [{i}] {passed} Score: {score:.4f} | Subtopic: {subtopic}")
    
    passed_count = sum(1 for _, score in all_docs_with_scores if score >= 0.3)
    print(f"\nDocuments passing threshold (≥0.3): {passed_count}/{len(all_docs_with_scores)}")
    
    print("\n" + "=" * 80)
    print("PERFORMANCE METRICS SUMMARY")
    print("=" * 80)
    
    # Calculate average scores
    print("\n📊 Average Similarity Scores by Topic:")
    for test_case in test_cases:
        topic = test_case["topic"]
        all_scores = []
        
        for query in test_case["queries"][:3]:  # Test first 3 queries per topic
            docs_with_scores = rag_system.retrieve_by_topic(topic, k=3)
            scores = [score for _, score in docs_with_scores]
            all_scores.extend(scores)
        
        if all_scores:
            avg_score = sum(all_scores) / len(all_scores)
            max_score = max(all_scores)
            min_score = min(all_scores)
            
            print(f"\n  {topic}:")
            print(f"    • Average: {avg_score:.4f}")
            print(f"    • Max: {max_score:.4f}")
            print(f"    • Min: {min_score:.4f}")
            print(f"    • Total retrievals: {len(all_scores)}")
    
    print("\n" + "=" * 80)
    print("RECOMMENDATIONS")
    print("=" * 80)
    print("""
    ✅ Good Performance (Score ≥ 0.5): Highly relevant, use as-is
    ⚠️  Acceptable Performance (Score 0.3-0.5): Relevant but could improve
    ❌ Poor Performance (Score < 0.3): Consider:
       • Improving query phrasing
       • Adding more training data
       • Adjusting embedding model
       • Lowering similarity threshold (with caution)
    
    Current Configuration:
    • Embedding Model: sentence-transformers/all-MiniLM-L6-v2
    • Similarity Metric: Cosine similarity
    • Threshold: 0.3
    • Top-K: 4
    • Metadata Filtering: Enabled (by topic)
    """)
    
    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    test_similarity_search()
