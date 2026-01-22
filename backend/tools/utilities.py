# backend/tools/utilities.py - Utility tools (user info, Tavily web search)
import os
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Try to import Tavily
try:
    from tavily import TavilyClient
    TAVILY_AVAILABLE = True
except ImportError:
    logger.warning("tavily-python not installed. Web search will use mock responses.")
    TAVILY_AVAILABLE = False
    TavilyClient = None

# Initialize Tavily client if API key available
api_key = os.getenv("TAVILY_API_KEY")
tavily = None

if TAVILY_AVAILABLE and api_key:
    api_key = api_key.strip()
    if api_key.startswith('tvly-'):
        try:
            tavily = TavilyClient(api_key=api_key)
            logger.info("✓ Tavily client initialized")
        except Exception as e:
            logger.warning(f"Tavily initialization failed: {e}")
    else:
        logger.warning("Invalid TAVILY_API_KEY format (should start with 'tvly-')")
else:
    logger.info("Tavily not configured - web search will use mock responses")


def fetch_user_info(passenger_id):
    """
    Fetch user booking information.
    
    In production, this would query the user database for:
    - Current bookings
    - Past trips
    - Preferences
    - Loyalty status
    
    Args:
        passenger_id: Passenger ID
    
    Returns:
        User information string
    """
    if not passenger_id:
        logger.warning("fetch_user_info called without passenger_id")
        return "No passenger information available."
    
    # Mock implementation
    # In production: query database
    logger.info(f"Fetching info for passenger: {passenger_id}")
    return f"Passenger {passenger_id} has active booking: Flight LX123 (ZUR→JFK)."


def search_web(query):
    """
    Search the web for live information using Tavily.
    Falls back to mock responses if Tavily not available.
    
    Args:
        query: Search query string
    
    Returns:
        Search results as formatted string
    """
    logger.info(f"Web search: {query[:100]}")
    
    if tavily is None:
        logger.info("Using mock web search response")
        return (
            "Mock search result: No significant flight delays reported for Swiss Airlines today. "
            "(Configure TAVILY_API_KEY in .env for live web search capability.)"
        )
    
    try:
        logger.info("Executing Tavily web search...")
        results = tavily.search(query=query, max_results=3)
        
        if not results.get('results'):
            return "No web results found for your query."
        
        # Format results
        formatted = []
        for r in results['results']:
            title = r.get('title', 'No title')
            content = r.get('content', '')[:150]
            url = r.get('url', '')
            formatted.append(f"• {title}\n  {content}...\n  Source: {url}")
        
        output = "\n\n".join(formatted)
        logger.info(f"✓ Found {len(results['results'])} web results")
        return output
        
    except Exception as e:
        logger.error(f"Tavily search failed: {e}")
        return f"Web search temporarily unavailable. Error: {str(e)}"