"""
Quick Setup Script for Data Engineering Interview Prep Chatbot

This script helps you set up the chatbot by:
1. Checking for required environment variables
2. Running document ingestion
3. Providing next steps
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def check_environment():
    """Check if required environment variables are set."""
    print("🔍 Checking environment configuration...")
    
    required_vars = [
        "aws_access_key_id",
        "aws_secret_access_key"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("\n❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\n💡 Please create a .env file with your AWS credentials:")
        print("   aws_access_key_id=your_access_key")
        print("   aws_secret_access_key=your_secret_key")
        print("   aws_session_token=your_session_token (if using temporary creds)")
        return False
    
    print("✅ Environment variables configured\n")
    return True


def check_vector_db():
    """Check if vector database exists."""
    vector_db_path = Path("data/vector_db/chroma.sqlite3")
    return vector_db_path.exists()


def run_ingestion():
    """Run document ingestion."""
    print("\n📥 Starting document ingestion...")
    print("This will create a vector database using AWS Bedrock embeddings.\n")
    
    try:
        from src.ingestion import DataEngineeringDocsIngestor
        
        ingestor = DataEngineeringDocsIngestor()
        vectorstore = ingestor.ingest_all(force_recreate=True)
        
        print("\n✅ Ingestion completed successfully!")
        print("   Using AWS Bedrock (Titan) embeddings")
        print("   LLM: Amazon Nova Lite v1:0")
        return True
    
    except Exception as e:
        print(f"\n❌ Ingestion failed: {e}")
        return False


def print_next_steps():
    """Print instructions for running the chatbot."""
    print("\n" + "=" * 70)
    print("🎉 SETUP COMPLETE!")
    print("=" * 70)
    print("\n📝 Next Steps:\n")
    print("Option 1 - Run Streamlit Web App (Recommended):")
    print("   streamlit run app/main.py")
    print("\nOption 2 - Run CLI Version:")
    print("   python main.py")
    print("\n" + "=" * 70)
    print("Good luck with your interview preparation! 🚀")
    print("=" * 70 + "\n")


def main():
    """Main setup function."""
    print("=" * 70)
    print("  DATA ENGINEERING INTERVIEW PREP - SETUP")
    print("=" * 70 + "\n")
    
    # Check environment
    if not check_environment():
        sys.exit(1)
    
    # Check if vector DB already exists
    if check_vector_db():
        print("ℹ️  Vector database already exists.")
        response = input("Do you want to recreate it? (y/N): ").strip().lower()
        
        if response != 'y':
            print("\n✅ Using existing vector database")
            print_next_steps()
            return
    
    # Run ingestion
    if run_ingestion():
        print_next_steps()
    else:
        print("\n❌ Setup failed. Please check the errors above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
