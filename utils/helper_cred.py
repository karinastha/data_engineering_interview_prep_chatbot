import os
from dotenv import load_dotenv
from langchain_ollama import ChatOllama
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.output_parsers import StrOutputParser

# Load environment variables (.env file)
load_dotenv()

# Ollama Configuration
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

# Initialize Ollama LLM
llm = ChatOllama(
    model=OLLAMA_MODEL,
    base_url=OLLAMA_BASE_URL,
    temperature=0.5
)

# Initialize HuggingFace Embeddings (free, local alternative)
# Using all-MiniLM-L6-v2 - fast and efficient for semantic search
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    model_kwargs={'device': 'cpu'},
    encode_kwargs={'normalize_embeddings': True}
)

# Export commonly used items
__all__ = ['llm', 'embeddings', 'OLLAMA_MODEL', 'OLLAMA_BASE_URL']