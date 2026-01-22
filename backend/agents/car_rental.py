# backend/agents/car_rental.py - Specialized car rental agent
from .primary_assistant import agent
import logging

logger = logging.getLogger(__name__)

def car_rental_assistant(state: dict) -> dict:
    """
    Car rental expert assistant.
    Uses primary agent with car-specific context.
    """
    logger.info("Car rental assistant activated")
    
    # Add car-specific context to the state
    messages = state.get("messages", [])
    if messages:
        last_message = messages[-1].get("content", "")
        # Enhance with car-specific instructions
        enhanced_message = f"[Car Rental Query] {last_message}"
        messages[-1]["content"] = enhanced_message
        state["messages"] = messages
    
    # Use primary agent
    state = agent(state)
    return state