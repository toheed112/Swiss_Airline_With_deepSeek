# backend/agents/primary_assistant.py

from __future__ import annotations

import json
import os
import logging
from datetime import datetime
from typing import Any, Dict, List
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI
import ollama

from backend.agents.gemini_refiner import refine_with_gemini
from backend.tools import (
    lookup_policy,
    search_flights,
    update_ticket_to_new_flight,
    search_cars,
    book_car,
    search_hotels,
    book_hotel,
    search_excursions,
    book_excursion,
    search_web,
    fetch_user_info,
)

load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ----------------------------
# Clients & models
# ----------------------------

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
OPENAI_ROUTER_MODEL = os.getenv("OPENAI_ROUTER_MODEL", "gpt-4o-mini")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "deepseek-r1:1.5b")
USE_GEMINI_REFINEMENT = os.getenv("USE_GEMINI_REFINEMENT", "false").lower() == "true"

# Validate environment
def validate_environment():
    """Validate required environment variables."""
    required = {
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
        "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY"),
    }
    missing = [k for k, v in required.items() if not v]
    if missing:
        logger.warning(f"Missing optional env vars: {missing}")
    
    # Check if Ollama is running
    try:
        ollama.list()
        logger.info("✓ Ollama connection verified")
    except Exception as e:
        logger.error(f"✗ Ollama not running: {e}")
        raise RuntimeError("Ollama service not available. Run 'ollama serve' first.")

validate_environment()

# ----------------------------
# Tool execution
# ----------------------------

def _execute_tool(name: str, args: Dict[str, Any], passenger_id: str | None) -> Any:
    """Execute a tool by name with given arguments."""
    booking_tools = {
        "book_hotel",
        "book_car",
        "book_excursion",
        "update_ticket_to_new_flight",
    }

    # Auto-inject passenger_id for booking tools
    if name in booking_tools and not args.get("passenger_id") and passenger_id:
        args["passenger_id"] = passenger_id

    tools = {
        "search_flights": search_flights,
        "search_hotels": search_hotels,
        "search_cars": search_cars,
        "search_excursions": search_excursions,
        "book_hotel": book_hotel,
        "book_car": book_car,
        "book_excursion": book_excursion,
        "update_ticket_to_new_flight": update_ticket_to_new_flight,
        "lookup_policy": lookup_policy,
        "search_web": search_web,
        "fetch_user_info": fetch_user_info,
    }

    if name not in tools:
        logger.error(f"Unknown tool requested: {name}")
        return f"Unknown tool: {name}"

    try:
        result = tools[name](**args)
        logger.info(f"Tool {name} executed successfully")
        return result
    except Exception as e:
        logger.error(f"Tool {name} failed: {e}")
        return f"Tool execution failed: {str(e)}"


def _extract_search_params(query: str) -> Dict[str, Any]:
    """Extract search parameters from user query using simple keyword detection."""
    query_lower = query.lower()
    params = {}
    
    # Extract locations (common airport codes and cities)
    airports = ["zur", "jfk", "lhr", "cdg", "fra", "zrh", "nyc", "lon", "par"]
    cities = ["zurich", "new york", "london", "paris", "frankfurt"]
    
    for airport in airports:
        if airport in query_lower:
            params["location"] = airport.upper()
            break
    
    for city in cities:
        if city in query_lower:
            params["location"] = city.title()
            break
    
    if not params.get("location"):
        params["location"] = "Zurich"  # Default
    
    return params


# ----------------------------
# Main agent
# ----------------------------

def agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Primary assistant agent.
    - Intelligently routes queries to appropriate tools
    - Uses Ollama DeepSeek for response generation
    - Optionally refines with Gemini
    """
    messages: List[Dict[str, Any]] = state.get("messages", [])
    passenger_id: str | None = state.get("passenger_id")
    user_info: str | None = state.get("user_info")

    if not messages:
        raise ValueError("State contains no messages")

    # Get conversation history and latest query
    *history, last_msg = messages
    user_query = last_msg.get("content", "")
    
    logger.info(f"Processing query: {user_query[:100]}...")

    # ----------------------------
    # Intelligent tool routing
    # ----------------------------
    tool_results: Dict[str, Any] = {}
    query_lower = user_query.lower()

    try:
        # Extract parameters from query
        params = _extract_search_params(user_query)
        
        # Route to appropriate tools based on keywords
        if any(word in query_lower for word in ["flight", "fly", "departure", "arrival"]):
            logger.info("Routing to flight search")
            tool_results["flights"] = search_flights(
                departure_airport=params.get("location"),
                limit=5
            )
        
        elif any(word in query_lower for word in ["hotel", "stay", "accommodation", "room"]):
            logger.info("Routing to hotel search")
            tool_results["hotels"] = search_hotels(
                location=params.get("location", "Zurich")
            )
        
        elif any(word in query_lower for word in ["car", "rental", "vehicle", "drive"]):
            logger.info("Routing to car rental search")
            tool_results["cars"] = search_cars(
                location=params.get("location", "Zurich"),
                dates=None
            )
        
        elif any(word in query_lower for word in ["policy", "rule", "cancellation", "refund", "baggage"]):
            logger.info("Routing to policy lookup")
            tool_results["policy"] = lookup_policy(user_query)
        
        elif any(word in query_lower for word in ["excursion", "tour", "activity", "sightseeing"]):
            logger.info("Routing to excursion search")
            tool_results["excursions"] = search_excursions(
                location=params.get("location", "Zurich")
            )
        
        elif any(word in query_lower for word in ["delay", "status", "live", "current", "real-time"]):
            logger.info("Routing to web search for live info")
            tool_results["web_search"] = search_web(user_query)
        
        # Always fetch user info if passenger_id available
        if passenger_id:
            tool_results["user_info"] = fetch_user_info(passenger_id)

    except Exception as e:
        logger.error(f"Tool execution error: {e}")
        tool_results["error"] = f"Tool error: {str(e)}"

    # ----------------------------
    # Build context-aware prompt
    # ----------------------------
    
    # Limit history to last 6 messages for token efficiency
    recent_history = history[-6:] if len(history) > 6 else history
    
    prompt = f"""You are a helpful Swiss Airlines virtual assistant.

Current UTC time: {datetime.utcnow().isoformat()}Z

Recent conversation history:
{json.dumps(recent_history, indent=2)}

User's current question:
{user_query}

Available tool results (trusted data from systems):
{json.dumps(tool_results, indent=2, default=str)}

User information:
{user_info or "No user info available"}

INSTRUCTIONS:
- Base your answer ONLY on the tool results provided above
- Do NOT invent flights, prices, hotels, or policies
- If tool results are empty or show "No results found", inform the user politely
- Be concise, helpful, and professional
- Use natural conversational language
- If the user asks about bookings, remind them you can help with that
- Format prices in CHF (Swiss Francs) when mentioned

Provide a helpful, accurate response:"""

    # ----------------------------
    # Generate response with Ollama DeepSeek
    # ----------------------------
    answer = ""
    try:
        logger.info("Generating response with Ollama DeepSeek")
        response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[{"role": "user", "content": prompt}],
            options={
                "temperature": 0.7,
                "num_predict": 500,
            }
        )
        answer = response["message"]["content"].strip()
        logger.info("✓ Ollama response generated")

    except Exception as ollama_error:
        logger.error(f"Ollama error: {ollama_error}")
        
        # Fallback: Try Gemini
        try:
            logger.info("Falling back to Gemini")
            answer = refine_with_gemini(prompt)
            logger.info("✓ Gemini fallback successful")
        except Exception as gemini_error:
            logger.error(f"Gemini fallback failed: {gemini_error}")
            answer = "I apologize, but I'm having trouble generating a response right now. Please try again in a moment."

    # ----------------------------
    # Optional Gemini refinement
    # ----------------------------
    if USE_GEMINI_REFINEMENT and answer and "apologize" not in answer.lower():
        try:
            logger.info("Refining response with Gemini")
            refined = refine_with_gemini(
                f"Improve clarity and professionalism without adding facts:\n\n{answer}"
            )
            if refined and not refined.startswith("(Gemini"):
                answer = refined
                logger.info("✓ Gemini refinement applied")
        except Exception as e:
            logger.warning(f"Gemini refinement skipped: {e}")

    # ----------------------------
    # Update state
    # ----------------------------
    messages.append({
        "role": "assistant",
        "content": answer
    })
    
    state["messages"] = messages
    logger.info("Agent processing complete")
    
    return state