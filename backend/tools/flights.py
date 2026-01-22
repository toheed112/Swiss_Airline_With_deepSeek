# backend/tools/flights.py - Flight search/update tools with SQLite
import sqlite3
import logging
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Use absolute path relative to this file
DB_PATH = Path(__file__).parent.parent.parent / "data" / "travel2.sqlite"


def search_flights(departure_airport=None, arrival_airport=None, limit=20):
    """
    Search flights from database.
    
    Args:
        departure_airport: Departure airport code (e.g., 'ZUR', 'JFK')
        arrival_airport: Arrival airport code (optional)
        limit: Maximum number of results
    
    Returns:
        List of flight dictionaries or error message string
    """
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        query = "SELECT * FROM flights WHERE 1=1"
        params = []
        
        if departure_airport:
            query += " AND departure_airport = ?"
            params.append(departure_airport.upper())
        
        if arrival_airport:
            query += " AND arrival_airport = ?"
            params.append(arrival_airport.upper())
        
        query += " LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        columns = [col[0] for col in cursor.description]
        results = [dict(zip(columns, row)) for row in rows]
        conn.close()
        
        if not results:
            logger.info(f"No flights found for: {departure_airport} -> {arrival_airport}")
            return "No flights found for your criteria. Try broader search or different airports."
        
        logger.info(f"Found {len(results)} flights")
        return results
        
    except sqlite3.Error as e:
        logger.error(f"Database error in search_flights: {e}")
        return f"Database error: {str(e)}"
    except Exception as e:
        logger.error(f"Unexpected error in search_flights: {e}")
        return f"Error searching flights: {str(e)}"


def update_ticket_to_new_flight(ticket_no, new_flight_id, passenger_id):
    """
    Update an existing ticket to a new flight.
    
    Args:
        ticket_no: Ticket number to update
        new_flight_id: ID of the new flight
        passenger_id: Passenger ID for authorization
    
    Returns:
        Success message or raises ValueError
    """
    if not passenger_id:
        logger.error("Ticket update attempted without passenger ID")
        raise ValueError("No passenger ID provided. Authorization required.")
    
    if not ticket_no or not new_flight_id:
        logger.error("Missing ticket number or flight ID")
        raise ValueError("Ticket number and new flight ID are required.")
    
    # In production, this would:
    # 1. Verify passenger owns the ticket
    # 2. Check new flight availability
    # 3. Update database
    # 4. Send confirmation email
    
    logger.info(f"Ticket {ticket_no} updated to flight {new_flight_id} for passenger {passenger_id}")
    return f"Ticket {ticket_no} successfully updated to flight {new_flight_id}."