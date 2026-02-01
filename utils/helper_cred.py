import os
from dotenv import load_dotenv
from langchain_aws import ChatBedrock
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.output_parsers import StrOutputParser

# Load environment variables (.env file)
load_dotenv()

# AWS Configuration
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
AWS_ACCESS_KEY_ID = os.getenv("aws_access_key_id")
AWS_SECRET_ACCESS_KEY = os.getenv("aws_secret_access_key")
AWS_SESSION_TOKEN = os.getenv("aws_session_token")

# Initialize Nova Lite LLM
llm = ChatBedrock(
    model_id="amazon.nova-lite-v1:0",
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    aws_session_token=AWS_SESSION_TOKEN,
    model_kwargs={"temperature": 0.5, "max_tokens": 1000}
)

# Initialize HuggingFace Embeddings (free, local alternative)
# Using all-MiniLM-L6-v2 - fast and efficient for semantic search
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    model_kwargs={'device': 'cpu'},
    encode_kwargs={'normalize_embeddings': True}
)

# Export commonly used items
__all__ = ['llm', 'embeddings', 'AWS_REGION', 'AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'AWS_SESSION_TOKEN']