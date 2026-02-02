"""
Setup and initialization script for the modernized chatbot.

This script helps set up the environment, install dependencies,
and initialize the system for first use.
"""

import os
import sys
import subprocess
from pathlib import Path
import logging


def setup_logging():
    """Setup logging for the setup process."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)


def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version}")
    return True


def install_requirements(logger):
    """Install required packages."""
    try:
        requirements_file = Path(__file__).parent / "requirements_modern.txt"
        
        if not requirements_file.exists():
            logger.error(f"Requirements file not found: {requirements_file}")
            return False
        
        logger.info("Installing requirements...")
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info("✅ Requirements installed successfully")
            return True
        else:
            logger.error(f"❌ Failed to install requirements: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"Failed to install requirements: {str(e)}")
        return False


def create_env_file(logger):
    """Create .env file template if it doesn't exist."""
    try:
        env_file = Path(__file__).parent / ".env"
        
        if env_file.exists():
            logger.info("✅ .env file already exists")
            return True
        
        env_template = """# Environment Configuration
ENVIRONMENT=development

# AWS Configuration
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
AWS_REGION=us-east-1

# LLM Configuration
LLM_MODEL_ID=amazon.nova-lite-v1:0
LLM_MAX_TOKENS=2048
LLM_TEMPERATURE=0.1

# Vector Store Configuration
VECTOR_STORE_COLLECTION_NAME=data_engineering_docs
VECTOR_STORE_PERSIST_PATH=./data/vector_store_new
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# RAG Configuration
RAG_MAX_CONTEXT_LENGTH=4000
RAG_SIMILARITY_THRESHOLD=0.7
RAG_MAX_RETRIEVE_DOCUMENTS=5

# Memory Configuration
MEMORY_STORAGE_PATH=./data/memory
MEMORY_MAX_SIZE_MB=100
"""
        
        env_file.write_text(env_template)
        logger.info(f"✅ Created .env template at: {env_file}")
        logger.warning("⚠️  Please update .env file with your actual AWS credentials")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create .env file: {str(e)}")
        return False


def create_directories(logger):
    """Create necessary directories."""
    try:
        directories = [
            "data/vector_store_new",
            "data/memory",
            "logs",
            "backup_pre_migration"
        ]
        
        for directory in directories:
            dir_path = Path(__file__).parent / directory
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"✅ Created directory: {directory}")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to create directories: {str(e)}")
        return False


def check_aws_credentials(logger):
    """Check if AWS credentials are configured."""
    try:
        # Try to load environment
        from dotenv import load_dotenv
        load_dotenv()
        
        access_key = os.getenv("AWS_ACCESS_KEY_ID")
        secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        
        if not access_key or access_key == "your_access_key_here":
            logger.warning("⚠️  AWS_ACCESS_KEY_ID not configured in .env")
            return False
        
        if not secret_key or secret_key == "your_secret_key_here":
            logger.warning("⚠️  AWS_SECRET_ACCESS_KEY not configured in .env")
            return False
        
        logger.info("✅ AWS credentials configured")
        return True
        
    except Exception as e:
        logger.warning(f"Could not verify AWS credentials: {str(e)}")
        return False


def test_system_health(logger):
    """Test if the system is working correctly."""
    try:
        logger.info("Testing system health...")
        
        # Test configuration loading
        from config.settings import get_config
        config = get_config()
        logger.info("✅ Configuration loaded successfully")
        
        # Test vector store initialization
        from infrastructure.vector_store.chroma_store import ChromaVectorStore
        vector_store = ChromaVectorStore()
        
        if vector_store.health_check():
            logger.info("✅ Vector store healthy")
        else:
            logger.warning("⚠️  Vector store health check failed")
        
        return True
        
    except Exception as e:
        logger.error(f"System health test failed: {str(e)}")
        return False


def main():
    """Main setup function."""
    logger = setup_logging()
    
    print("🔧 Data Engineering Chatbot Setup")
    print("=" * 40)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Install requirements
    if not install_requirements(logger):
        print("❌ Setup failed during requirements installation")
        sys.exit(1)
    
    # Create environment file
    if not create_env_file(logger):
        print("❌ Setup failed during .env creation")
        sys.exit(1)
    
    # Create directories
    if not create_directories(logger):
        print("❌ Setup failed during directory creation")
        sys.exit(1)
    
    # Check AWS credentials
    aws_configured = check_aws_credentials(logger)
    
    # Test system health
    if test_system_health(logger):
        logger.info("✅ System health test passed")
    else:
        logger.warning("⚠️  System health test failed")
    
    # Final instructions
    print("\\n🎉 Setup completed!")
    print("=" * 40)
    
    if not aws_configured:
        print("⚠️  IMPORTANT: Please configure your AWS credentials in .env file")
        print("   1. Open .env file")
        print("   2. Replace 'your_access_key_here' with your AWS Access Key ID")
        print("   3. Replace 'your_secret_key_here' with your AWS Secret Access Key")
    
    print("\\n📋 Next steps:")
    print("   1. Configure AWS credentials (if not done)")
    print("   2. Run migration: python migrate.py")
    print("   3. Start the app: streamlit run app_modern.py")
    
    print("\\n🆘 If you encounter issues:")
    print("   - Check logs in chatbot.log")
    print("   - Verify your .env configuration")
    print("   - Ensure AWS credentials are valid")


if __name__ == "__main__":
    main()