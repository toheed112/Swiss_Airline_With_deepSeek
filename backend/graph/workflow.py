# backend/graph/workflow.py

from __future__ import annotations

import logging
from typing import Any, Dict, List
from typing_extensions import TypedDict

from backend.agents.primary_assistant import agent

logger = logging.getLogger(__name__)


class State(TypedDict, total=False):
    """State structure for the graph workflow."""
    messages: List[Dict[str, Any]]
    user_info: str
    passenger_id: str
    interrupt: bool


def run_graph_v4(
    user_input: str,
    config: Dict[str, Any],
    history: List[Dict[str, Any]] | None = None,
) -> List[Dict[str, Any]]:
    """
    Main workflow execution function.
    
    - Takes the existing chat history + new user_input
    - Builds a State object (with passenger_id)
    - Calls the primary assistant (intelligent routing + AI response)
    - Returns the updated message history (last 10 messages for efficiency)
    
    Args:
        user_input: User's latest message
        config: Configuration dict with passenger_id, user_info, etc.
        history: Previous conversation history (optional)
    
    Returns:
        Updated message history (last 10 messages)
    """
    if history is None:
        history = []
    
    passenger_id = config.get("passenger_id", "")
    user_info = config.get("user_info", "")
    
    logger.info(f"Workflow started for passenger: {passenger_id}")
    
    # Build state
    state: State = {
        "messages": history + [{"role": "user", "content": user_input}],
        "passenger_id": passenger_id,
        "user_info": user_info,
        "interrupt": False,
    }
    
    try:
        # Call primary agent
        state = agent(state)
        logger.info("✓ Agent processing complete")
    except Exception as e:
        logger.error(f"Agent error: {e}")
        # Add error message to conversation
        state["messages"].append({
            "role": "assistant",
            "content": "I apologize, but I encountered an error processing your request. Please try again."
        })
    
    # Return last 10 messages to manage token usage
    messages = state["messages"]
    if len(messages) > 10:
        logger.info(f"Trimming history: {len(messages)} -> 10 messages")
        return messages[-10:]
    
    return messages