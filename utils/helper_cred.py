import os
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.output_parsers import StrOutputParser

# Load environment variables (.env file)
load_dotenv()

# Select LLM Provider based on available environment variables
groq_api_key = os.getenv("GROQ_API_KEY")
google_api_key = os.getenv("GOOGLE_API_KEY")

if groq_api_key:
    from langchain_groq import ChatGroq
    llm = ChatGroq(
        model_name="llama-3.3-70b-versatile",
        temperature=0.5,
        max_tokens=1000,
        groq_api_key=groq_api_key
    )
elif google_api_key:
    from langchain_google_genai import ChatGoogleGenerativeAI
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        temperature=0.5,
        max_output_tokens=1000,
        google_api_key=google_api_key
    )
else:
    from langchain_ollama import ChatOllama
    llm = ChatOllama(
        model=os.getenv("OLLAMA_MODEL", "llama3.2"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
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
__all__ = ['llm', 'embeddings']