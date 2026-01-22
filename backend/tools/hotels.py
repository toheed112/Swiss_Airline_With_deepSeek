# backend/tools/hotels.py - Hotel tools with SQLite
import sqlite3
import logging
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Use absolute path
DB_PATH = Path(__file__).parent.parent.parent / "data" / "travel2.sqlite"


def search_hotels(location, checkin=None, checkout=None, limit=20):
    """
    Search hotels in a specific location.
    
    Args:
        location: City or location name
        checkin: Check-in date (optional, for future enhancement)
        checkout: Check-out date (optional, for future enhancement)
        limit: Maximum number of results
    
    Returns:
        List of hotel dictionaries or error message
    """
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        query = "SELECT * FROM hotels WHERE 1=1"
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
            logger.info(f"No hotels found in: {location}")
            return f"No hotels found in {location}. Try a different location."
        
        logger.info(f"Found {len(results)} hotels in {location}")
        return results
        
    except sqlite3.Error as e:
        logger.error(f"Database error in search_hotels: {e}")
        return f"Database error: {str(e)}"
    except Exception as e:
        logger.error(f"Error in search_hotels: {e}")
        return f"Error searching hotels: {str(e)}"


def book_hotel(hotel_id, passenger_id):
    """
    Book a hotel for a passenger.
    
    Args:
        hotel_id: Hotel ID to book
        passenger_id: Passenger ID for authorization
    
    Returns:
        Success message or raises ValueError
    """
    if not passenger_id:
        logger.error("Hotel booking attempted without passenger ID")
        raise ValueError("No passenger ID provided. Authorization required.")
    
    if not hotel_id:
        logger.error("Hotel booking attempted without hotel ID")
        raise ValueError("Hotel ID is required.")
    
    # In production: verify availability, process payment, create reservation
    logger.info(f"Hotel {hotel_id} booked for passenger {passenger_id}")
    return f"Hotel {hotel_id} successfully booked for passenger {passenger_id}."