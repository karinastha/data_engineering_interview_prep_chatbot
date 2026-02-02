"""
Advanced Memory Management for RAG Chatbot

This module provides conversation memory features including:
- Conversation summarization for long chats
- Semantic memory retrieval for cross-session learning
- Memory buffer management
"""

import json
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class ConversationMemory:
    """Data structure for storing conversation memories"""
    session_id: str
    timestamp: datetime
    topic: str
    summary: str
    key_concepts: List[str]
    user_questions: List[str]
    
    def to_dict(self) -> Dict:
        return {
            "session_id": self.session_id,
            "timestamp": self.timestamp.isoformat(),
            "topic": self.topic,
            "summary": self.summary,
            "key_concepts": self.key_concepts,
            "user_questions": self.user_questions
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ConversationMemory':
        return cls(
            session_id=data["session_id"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            topic=data["topic"],
            summary=data["summary"],
            key_concepts=data["key_concepts"],
            user_questions=data["user_questions"]
        )

class ConversationMemoryManager:
    """
    Manages conversation memory with summarization and persistence.
    
    This class provides advanced memory features for future implementation:
    - Long conversation summarization
    - Cross-session memory retrieval
    - Memory persistence to disk
    """
    
    def __init__(self, memory_file: str = "data/conversation_memories.json"):
        self.memory_file = Path(memory_file)
        self.memory_file.parent.mkdir(parents=True, exist_ok=True)
        self.memories: List[ConversationMemory] = self._load_memories()
    
    def _load_memories(self) -> List[ConversationMemory]:
        """Load conversation memories from disk"""
        if not self.memory_file.exists():
            return []
        
        try:
            with open(self.memory_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return [ConversationMemory.from_dict(item) for item in data]
        except Exception as e:
            print(f"Error loading memories: {e}")
            return []
    
    def _save_memories(self):
        """Save conversation memories to disk"""
        try:
            data = [memory.to_dict() for memory in self.memories]
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving memories: {e}")
    
    def summarize_conversation(self, messages: List[Dict], topic: str = None) -> str:
        """
        Create a summary of the conversation for memory storage.
        
        Args:
            messages: List of chat messages
            topic: Main topic discussed
            
        Returns:
            Conversation summary
        """
        if not messages or len(messages) < 4:
            return "Brief conversation with minimal content."
        
        # Extract key information
        user_messages = [msg["content"] for msg in messages if msg["role"] == "user"]
        assistant_messages = [msg["content"] for msg in messages if msg["role"] == "assistant"]
        
        # Simple extractive summarization
        key_questions = [msg for msg in user_messages if "?" in msg][:3]
        
        summary_parts = []
        if topic:
            summary_parts.append(f"User practiced {topic} interview preparation.")
        
        if key_questions:
            summary_parts.append(f"Key questions: {'; '.join(key_questions[:2])}")
        
        summary_parts.append(f"Conversation had {len(messages)} exchanges.")
        
        return " ".join(summary_parts)
    
    def extract_key_concepts(self, messages: List[Dict], topic: str = None) -> List[str]:
        """
        Extract key concepts discussed in the conversation.
        
        Args:
            messages: List of chat messages
            topic: Main topic discussed
            
        Returns:
            List of key concepts
        """
        # Simple keyword extraction
        all_text = " ".join([msg["content"].lower() for msg in messages])
        
        # Common data engineering concepts
        concepts = {
            "Python": ["list comprehension", "pandas", "numpy", "decorators", "exception handling"],
            "SQL": ["joins", "window functions", "indexing", "stored procedures", "normalization"],
            "Database": ["ACID", "transactions", "indexing", "partitioning", "replication"],
            "ETL": ["pipeline", "transformation", "data quality", "scheduling", "monitoring"]
        }
        
        found_concepts = []
        if topic and topic in concepts:
            for concept in concepts[topic]:
                if concept in all_text:
                    found_concepts.append(concept)
        
        # Add general concepts
        general_concepts = ["data pipeline", "performance", "scalability", "best practices"]
        for concept in general_concepts:
            if concept in all_text:
                found_concepts.append(concept)
        
        return list(set(found_concepts))[:5]  # Limit to 5 concepts
    
    def store_conversation_memory(self, session_id: str, messages: List[Dict], topic: str = None):
        """
        Store conversation as a memory for future reference.
        
        Args:
            session_id: Unique session identifier
            messages: List of chat messages
            topic: Main topic discussed
        """
        if len(messages) < 4:  # Don't store very short conversations
            return
        
        summary = self.summarize_conversation(messages, topic)
        key_concepts = self.extract_key_concepts(messages, topic)
        user_questions = [msg["content"] for msg in messages if msg["role"] == "user" and "?" in msg["content"]][:5]
        
        memory = ConversationMemory(
            session_id=session_id,
            timestamp=datetime.now(),
            topic=topic or "General",
            summary=summary,
            key_concepts=key_concepts,
            user_questions=user_questions
        )
        
        self.memories.append(memory)
        self._save_memories()
    
    def get_relevant_memories(self, topic: str = None, limit: int = 3) -> List[ConversationMemory]:
        """
        Retrieve relevant conversation memories.
        
        Args:
            topic: Topic to filter by
            limit: Maximum number of memories to return
            
        Returns:
            List of relevant memories
        """
        relevant_memories = []
        
        for memory in self.memories:
            if topic and memory.topic.lower() == topic.lower():
                relevant_memories.append(memory)
            elif not topic:
                relevant_memories.append(memory)
        
        # Sort by recency and return limited results
        relevant_memories.sort(key=lambda x: x.timestamp, reverse=True)
        return relevant_memories[:limit]
    
    def format_memory_context(self, memories: List[ConversationMemory]) -> str:
        """
        Format memories for inclusion in prompts.
        
        Args:
            memories: List of conversation memories
            
        Returns:
            Formatted memory context string
        """
        if not memories:
            return "No relevant previous conversations found."
        
        formatted_parts = ["Previous Learning Context:"]
        
        for i, memory in enumerate(memories, 1):
            formatted_parts.append(f"\nSession {i} ({memory.topic}):")
            formatted_parts.append(f"- {memory.summary}")
            if memory.key_concepts:
                formatted_parts.append(f"- Key concepts: {', '.join(memory.key_concepts)}")
        
        return "\n".join(formatted_parts)

# Future enhancement: This can be integrated into the main RAG system
# by calling store_conversation_memory when a session ends and 
# get_relevant_memories to provide cross-session learning context

if __name__ == "__main__":
    # Example usage for future implementation
    manager = ConversationMemoryManager()
    
    # Simulate storing a conversation
    example_messages = [
        {"role": "user", "content": "What are list comprehensions?"},
        {"role": "assistant", "content": "List comprehensions are..."},
        {"role": "user", "content": "How do I use them in data pipelines?"},
        {"role": "assistant", "content": "In data engineering..."}
    ]
    
    manager.store_conversation_memory("session_001", example_messages, "Python")
    
    # Retrieve relevant memories
    memories = manager.get_relevant_memories("Python")
    context = manager.format_memory_context(memories)
    print(context)