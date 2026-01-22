# main.py - Entry point: Setup + Launch UI
import logging
import sys
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('chatbot.log')
    ]
)
logger = logging.getLogger(__name__)

if __name__ == '__main__':
    logger.info("=" * 50)
    logger.info("Swiss Airlines Chatbot Starting...")
    logger.info("=" * 50)
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    logger.info("✓ Environment variables loaded")
    
    # Setup database
    try:
        from backend.database.populate_db import populate_database
        db_path = populate_database()
        logger.info(f"✓ Database ready: {db_path}")
    except Exception as e:
        logger.error(f"✗ Database setup failed: {e}")
        sys.exit(1)
    
    # Test imports
    try:
        from backend.tools.policy import lookup_policy
        from backend.graph.workflow import run_graph_v4
        logger.info("✓ Tools and graph loaded successfully")
    except Exception as e:
        logger.error(f"✗ Import failed: {e}")
        sys.exit(1)
    
    # Launch Streamlit UI
    logger.info("Launching Streamlit UI...")
    logger.info("=" * 50)
    
    import subprocess
    try:
        subprocess.run(["streamlit", "run", "frontend/app.py"], check=True)
    except KeyboardInterrupt:
        logger.info("\nChatbot stopped by user")
    except FileNotFoundError:
        logger.error("✗ Streamlit not found. Install with: pip install streamlit")
        sys.exit(1)
    except Exception as e:
        logger.error(f"✗ Failed to launch UI: {e}")
        sys.exit(1)