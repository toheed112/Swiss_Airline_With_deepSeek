# excursion_booking.py - Specialized excursion booking agent
from .primary_assistant import agent

def excursion_assistant(state: dict) -> dict:
    """Excursion booking expert assistant."""
    # Use primary agent with excursion-specific prompt
    state = agent(state)
    return state