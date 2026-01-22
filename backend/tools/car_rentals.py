# backend/tools/car_rentals.py - Car rental tools with SQLite
import sqlite3
import logging
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Use absolute path
DB_PATH = Path(__file__).parent.parent.parent / "data" / "travel2.sqlite"


def search_cars(location, dates=None, limit=20):
    """
    Search available rental cars.
    
    Args:
        location: City or location name
        dates: Rental dates (optional, for future enhancement)
        limit: Maximum number of results
    
    Returns:
        List of car dictionaries or error message
    """
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        query = "SELECT * FROM cars WHERE 1=1"
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
            logger.info(f"No cars found in: {location}")
            return f"No rental cars available in {location}. Try a different location."
        
        logger.info(f"Found {len(results)} cars in {location}")
        return results
        
    except sqlite3.Error as e:
        logger.error(f"Database error in search_cars: {e}")
        return f"Database error: {str(e)}"
    except Exception as e:
        logger.error(f"Error in search_cars: {e}")
        return f"Error searching cars: {str(e)}"


def book_car(car_id, passenger_id):
    """
    Book a rental car for a passenger.
    
    Args:
        car_id: Car ID to book
        passenger_id: Passenger ID for authorization
    
    Returns:
        Success message or raises ValueError
    """
    if not passenger_id:
        logger.error("Car booking attempted without passenger ID")
        raise ValueError("No passenger ID provided. Authorization required.")
    
    if not car_id:
        logger.error("Car booking attempted without car ID")
        raise ValueError("Car ID is required.")
    
    # In production: check availability, process payment, create reservation
    logger.info(f"Car {car_id} booked for passenger {passenger_id}")
    return f"Car {car_id} successfully booked for passenger {passenger_id}."