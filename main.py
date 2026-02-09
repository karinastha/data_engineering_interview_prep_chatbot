"""
Main Entry Point - CLI Interface
Provides command-line interface for initialization, testing, and running the chatbot.

Usage:
    python main.py init          # Initialize/recreate vector store
    python main.py test          # Run a quick test
    python main.py run           # Start Streamlit app
"""

import argparse
import sys
from pathlib import Path

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.logging import setup_logging, get_logger

logger = get_logger(__name__)


def cmd_init(force: bool = False) -> int:
    """
    Initialize or recreate the vector store.
    
    Args:
        force: If True, recreate even if exists
        
    Returns:
        Exit code (0 for success)
    """
    from services.ingestion import IngestionService
    from utils.helper_cred import get_embeddings
    
    logger.info("Initializing vector store...")
    
    try:
        embeddings = get_embeddings()
        service = IngestionService(embeddings)
        vectorstore = service.initialize(force_recreate=force)
        
        # Verify
        count = vectorstore._collection.count()
        logger.info(f"✅ Vector store ready with {count} documents")
        return 0
        
    except Exception as e:
        logger.error(f"❌ Initialization failed: {e}")
        return 1


def cmd_test() -> int:
    """
    Run a quick test of the RAG pipeline.
    
    Returns:
        Exit code (0 for success)
    """
    from services.ingestion import IngestionService
    from services.retrieval import RetrievalService
    from services.chat import ChatService
    from schemas import Topic
    from utils.helper_cred import get_llm, get_embeddings
    
    logger.info("Running RAG pipeline test...")
    
    try:
        # Initialize components
        embeddings = get_embeddings()
        llm = get_llm()
        
        ingestion = IngestionService(embeddings)
        vectorstore = ingestion.initialize()
        
        retrieval = RetrievalService(vectorstore)
        chat = ChatService(llm, retrieval)
        
        # Test retrieval
        logger.info("Testing retrieval for Python topic...")
        results = retrieval.retrieve("list comprehensions", topic=Topic.PYTHON)
        logger.info(f"Retrieved {len(results)} documents")
        
        if results:
            logger.info(f"Top result score: {results[0].score:.3f}")
            logger.info(f"Top result topic: {results[0].topic}")
        
        # Test chat response
        logger.info("Testing chat response...")
        response = chat.answer_question(
            "What are list comprehensions in Python?",
            topic=Topic.PYTHON
        )
        
        if response.is_success:
            logger.info("✅ Chat response generated successfully")
            logger.info(f"Response length: {len(response.content)} chars")
        else:
            logger.warning(f"⚠️ Chat response error: {response.error}")
        
        logger.info("✅ All tests passed!")
        return 0
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


def cmd_run() -> int:
    """
    Start the Streamlit application.
    
    Returns:
        Exit code (0 for success)
    """
    import subprocess
    
    logger.info("Starting Streamlit application...")
    
    app_path = PROJECT_ROOT / "app.py"
    
    try:
        result = subprocess.run(
            ["streamlit", "run", str(app_path)],
            cwd=str(PROJECT_ROOT)
        )
        return result.returncode
        
    except FileNotFoundError:
        logger.error("❌ Streamlit not found. Install with: pip install streamlit")
        return 1
    except KeyboardInterrupt:
        logger.info("Application stopped")
        return 0


def main() -> int:
    """Main entry point."""
    setup_logging()
    
    parser = argparse.ArgumentParser(
        description="Data Engineering Interview Prep Chatbot CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py init          Initialize vector store
  python main.py init --force  Recreate vector store  
  python main.py test          Run pipeline test
  python main.py run           Start Streamlit app
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # init command
    init_parser = subparsers.add_parser("init", help="Initialize vector store")
    init_parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="Force recreation even if exists"
    )
    
    # test command
    subparsers.add_parser("test", help="Run pipeline test")
    
    # run command
    subparsers.add_parser("run", help="Start Streamlit application")
    
    args = parser.parse_args()
    
    if args.command == "init":
        return cmd_init(force=args.force)
    elif args.command == "test":
        return cmd_test()
    elif args.command == "run":
        return cmd_run()
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
