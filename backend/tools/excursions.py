# backend/tools/excursions.py - Excursion tools with SQLite
import sqlite3
import logging
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Use absolute path
DB_PATH = Path(__file__).parent.parent.parent / "data" / "travel2.sqlite"


def search_excursions(location, limit=20):
    """
    Search excursions and tours in a location.
    
    Args:
        location: City or location name
        limit: Maximum number of results
    
    Returns:
        List of excursion dictionaries or error message
    """
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        query = "SELECT * FROM excursions WHERE 1=1"
        params = []
        
        if location:
            query += " AND location LIKE ?"
            params.append(f"%{location}%")
        
        query += " LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        columns = [col[0] for col in cursor.description]
        results = [dict(zip(columns, row)) for row in rows]
        conn.close()
        
        if not results:
            logger.info(f"No excursions found in: {location}")
            return f"No excursions available in {location}. Try a different location."
        
        logger.info(f"Found {len(results)} excursions in {location}")
        return results
        
    except sqlite3.Error as e:
        logger.error(f"Database error in search_excursions: {e}")
        return f"Database error: {str(e)}"
    except Exception as e:
        logger.error(f"Error in search_excursions: {e}")
        return f"Error searching excursions: {str(e)}"


def book_excursion(excursion_id, passenger_id):
    """
    Book an excursion for a passenger.
    
    Args:
        excursion_id: Excursion ID to book
        passenger_id: Passenger ID for authorization
    
    Returns:
        Success message or raises ValueError
    """
    if not passenger_id:
        logger.error("Excursion booking attempted without passenger ID")
        raise ValueError("No passenger ID provided. Authorization required.")
    
    if not excursion_id:
        logger.error("Excursion booking attempted without excursion ID")
        raise ValueError("Excursion ID is required.")
    
    # In production: check availability, process payment, create booking
    logger.info(f"Excursion {excursion_id} booked for passenger {passenger_id}")
    return f"Excursion {excursion_id} successfully booked for passenger {passenger_id}."