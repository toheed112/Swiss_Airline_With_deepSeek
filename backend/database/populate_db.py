# populate_db.py - Create and populate SQLite DB with sample data
import sqlite3
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv
load_dotenv()

db = 'data/travel2.sqlite'

def populate_database():
    conn = sqlite3.connect(db)
    cursor = conn.cursor()

    # Flights table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS flights (
        id INTEGER PRIMARY KEY,
        flight_no TEXT,
        departure_airport TEXT,
        arrival_airport TEXT,
        departure_time TEXT,
        arrival_time TEXT,
        aircraft TEXT,
        price REAL
    )
    ''')

    # Sample flights (isoformat for datetimes)
    base_time = datetime(2025, 11, 10, 10, 0, tzinfo=pytz.UTC)
    flights_data = [
        ("LX123", "ZUR", "JFK", base_time.isoformat(), (base_time + timedelta(hours=9)).isoformat(), "A380", 800.0),
        ("LX456", "JFK", "ZUR", (base_time + timedelta(hours=12)).isoformat(), (base_time + timedelta(hours=21)).isoformat(), "A330", 900.0),
        ("LX789", "ZUR", "LON", base_time.isoformat(), (base_time + timedelta(hours=2)).isoformat(), "A320", 300.0),
    ]
    cursor.executemany(
        "INSERT OR REPLACE INTO flights (flight_no, departure_airport, arrival_airport, departure_time, arrival_time, aircraft, price) VALUES (?, ?, ?, ?, ?, ?, ?)",
        flights_data
    )
    conn.commit()

    # Hotels table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS hotels (
        id INTEGER PRIMARY KEY,
        name TEXT,
        location TEXT,
        price_per_night REAL,
        availability INTEGER
    )
    ''')
    hotels_data = [("Grand Hotel", "ZUR", 200.0, 5), ("City Inn", "JFK", 150.0, 10)]
    cursor.executemany(
        "INSERT OR REPLACE INTO hotels (name, location, price_per_night, availability) VALUES (?, ?, ?, ?)",
        hotels_data
    )
    conn.commit()

    # Cars table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS cars (
        id INTEGER PRIMARY KEY,
        model TEXT,
        location TEXT,
        price_per_day REAL
    )
    ''')
    cars_data = [("Sedan", "ZUR", 50.0)]
    cursor.executemany(
        "INSERT OR REPLACE INTO cars (model, location, price_per_day) VALUES (?, ?, ?)",
        cars_data
    )
    conn.commit()

    # Excursions table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS excursions (
        id INTEGER PRIMARY KEY,
        name TEXT,
        location TEXT,
        price REAL
    )
    ''')
    excursions_data = [("City Tour", "ZUR", 100.0)]
    cursor.executemany(
        "INSERT OR REPLACE INTO excursions (name, location, price) VALUES (?, ?, ?)",
        excursions_data
    )
    conn.commit()

    conn.close()
    print(f"DB populated: {db}")
    return db

if __name__ == '__main__':
    populate_database()