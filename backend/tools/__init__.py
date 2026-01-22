# backend/tools/__init__.py
"""
Tools package for Swiss Airlines chatbot.
Exports all tool functions for easy importing.
"""

from .flights import search_flights, update_ticket_to_new_flight
from .hotels import search_hotels, book_hotel
from .car_rentals import search_cars, book_car
from .excursions import search_excursions, book_excursion
from .policy import lookup_policy
from .utilities import fetch_user_info, search_web

__all__ = [
    "search_flights",
    "update_ticket_to_new_flight",
    "search_hotels",
    "book_hotel",
    "search_cars",
    "book_car",
    "search_excursions",
    "book_excursion",
    "lookup_policy",
    "fetch_user_info",
    "search_web",
]