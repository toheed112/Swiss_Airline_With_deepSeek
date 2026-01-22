# backend/agents/hotel_booking.py - Specialized hotel booking agent
from dotenv import load_dotenv
import os
import json
import logging

load_dotenv()

from openai import OpenAI
import ollama

from backend.tools.hotels import search_hotels, book_hotel
from backend.tools.utilities import search_web

logger = logging.getLogger(__name__)

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "deepseek-r1:7b")

# Hotel-specific tools for OpenAI
hotel_tools = [
    {
        "type": "function",
        "function": {
            "name": "search_hotels",
            "description": "Search hotels in a specific location.",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string", "description": "City or location"},
                    "checkin": {"type": "string", "description": "Check-in date (optional)"},
                    "checkout": {"type": "string", "description": "Check-out date (optional)"},
                    "limit": {"type": "integer", "default": 5}
                },
                "required": ["location"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "book_hotel",
            "description": "Book a hotel for a passenger.",
            "parameters": {
                "type": "object",
                "properties": {
                    "hotel_id": {"type": "integer", "description": "Hotel ID"},
                    "passenger_id": {"type": "string", "description": "Passenger ID"}
                },
                "required": ["hotel_id", "passenger_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "Search web for hotel reviews or availability.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"}
                },
                "required": ["query"]
            }
        }
    },
]


def hotel_assistant(state: dict) -> dict:
    """Hotel booking expert: OpenAI calls hotel tools, DeepSeek summarizes."""
    history = state.get("messages", [])
    user_query = history[-1]["content"] if history else ""
    passenger_id = state.get("passenger_id", "")
    
    logger.info(f"Hotel assistant processing: {user_query[:100]}...")

    # Step 1: OpenAI for hotel tool calling
    messages = [
        {
            "role": "system",
            "content": "You are a hotel booking expert. Call tools to search hotels or make bookings."
        },
        {"role": "user", "content": user_query}
    ]
    
    try:
        tool_response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=hotel_tools,
            tool_choice="auto"
        )
        logger.info("✓ OpenAI hotel tool selection complete")
    except Exception as e:
        logger.error(f"OpenAI failed: {e}")
        state["messages"].append({
            "role": "assistant",
            "content": "I'm having trouble accessing hotel information. Please try again."
        })
        return state

    # Step 2: Execute tool if called
    tool_result = ""
    if tool_response.choices[0].message.tool_calls:
        tool_call = tool_response.choices[0].message.tool_calls[0]
        func_name = tool_call.function.name
        args = json.loads(tool_call.function.arguments)
        
        logger.info(f"Executing: {func_name}")
        
        try:
            if "passenger_id" in args and not args["passenger_id"]:
                args["passenger_id"] = passenger_id
            
            if func_name == "search_hotels":
                result = search_hotels(**args)
                tool_result = json.dumps(result, default=str, indent=2)
            elif func_name == "book_hotel":
                result = book_hotel(**args)
                tool_result = str(result)
            elif func_name == "search_web":
                result = search_web(**args)
                tool_result = str(result)
            
            logger.info(f"✓ {func_name} executed")
        except Exception as e:
            logger.error(f"Tool error: {e}")
            tool_result = f"Error: {str(e)}"
    else:
        tool_result = "No specific hotel tool needed."

    # Step 3: DeepSeek for natural response
    history_text = "\n".join([f"{m['role']}: {m['content']}" for m in history[-4:]])
    
    ollama_prompt = f"""You are a Swiss Airlines hotel booking assistant.

History: {history_text}
User: {user_query}
Tool result: {tool_result}

Provide a natural, helpful response about hotels. Be conversational and clear.

Response:"""

    try:
        ollama_response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[{"role": "user", "content": ollama_prompt}],
            options={"temperature": 0.7}
        )
        bot_content = ollama_response["message"]["content"].strip()
        logger.info("✓ Response generated")
    except Exception as e:
        logger.error(f"Ollama error: {e}")
        bot_content = f"Hotel information: {tool_result[:200]}"

    state["messages"].append({"role": "assistant", "content": bot_content})
    return state