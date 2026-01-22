# backend/agents/flight_booking.py - Specialized flight agent
from dotenv import load_dotenv
import os
import json
import logging

load_dotenv()

from openai import OpenAI
import ollama
from datetime import datetime

from backend.tools.flights import search_flights, update_ticket_to_new_flight
from backend.tools.policy import lookup_policy
from backend.tools.utilities import search_web, fetch_user_info

logger = logging.getLogger(__name__)

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "deepseek-r1:7b")

# Flight-specific tools for OpenAI
flight_tools = [
    {
        "type": "function",
        "function": {
            "name": "search_flights",
            "description": "Search flights from database. Returns available flights.",
            "parameters": {
                "type": "object",
                "properties": {
                    "departure_airport": {
                        "type": "string",
                        "description": "Departure airport code (e.g., ZUR, JFK)"
                    },
                    "arrival_airport": {
                        "type": "string",
                        "description": "Arrival airport code (optional)"
                    },
                    "limit": {
                        "type": "integer",
                        "default": 5,
                        "description": "Maximum number of results"
                    }
                },
                "required": ["departure_airport"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_ticket_to_new_flight",
            "description": "Update an existing ticket to a new flight.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticket_no": {"type": "string", "description": "Ticket number"},
                    "new_flight_id": {"type": "integer", "description": "New flight ID"},
                    "passenger_id": {"type": "string", "description": "Passenger ID"}
                },
                "required": ["ticket_no", "new_flight_id", "passenger_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "Search web for live flight delays, status, or current information.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"}
                },
                "required": ["query"]
            }
        }
    },
]


def flight_assistant(state: dict) -> dict:
    """
    Flight expert assistant: OpenAI calls flight tools, DeepSeek summarizes.
    This provides better tool calling accuracy with OpenAI + natural language from DeepSeek.
    """
    history = state.get("messages", [])
    user_query = history[-1]["content"] if history else ""
    passenger_id = state.get("passenger_id", "")
    
    logger.info(f"Flight assistant processing: {user_query[:100]}...")
    
    # Step 1: OpenAI for intelligent flight tool calling
    messages = [
        {
            "role": "system",
            "content": "You are a flight booking expert. Analyze the user's query and call the appropriate tools to search flights, update tickets, or check live status."
        },
        {"role": "user", "content": user_query}
    ]
    
    try:
        tool_response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=flight_tools,
            tool_choice="auto"
        )
        logger.info("✓ OpenAI tool selection complete")
    except Exception as e:
        logger.error(f"OpenAI tool calling failed: {e}")
        state["messages"].append({
            "role": "assistant",
            "content": "I'm having trouble accessing flight information right now. Please try again."
        })
        return state

    # Step 2: Execute tool if called
    tool_result = ""
    if tool_response.choices[0].message.tool_calls:
        tool_call = tool_response.choices[0].message.tool_calls[0]
        func_name = tool_call.function.name
        args = json.loads(tool_call.function.arguments)
        
        logger.info(f"Executing tool: {func_name} with args: {args}")
        
        try:
            # Inject passenger_id if needed
            if "passenger_id" in args and not args["passenger_id"]:
                args["passenger_id"] = passenger_id
            
            if func_name == "search_flights":
                result = search_flights(**args)
                tool_result = json.dumps(result, default=str, indent=2)
            elif func_name == "update_ticket_to_new_flight":
                result = update_ticket_to_new_flight(**args)
                tool_result = str(result)
            elif func_name == "search_web":
                result = search_web(**args)
                tool_result = str(result)
            else:
                tool_result = "Tool not found"
            
            logger.info(f"✓ Tool {func_name} executed successfully")
        except Exception as e:
            logger.error(f"Tool execution failed: {e}")
            tool_result = f"Error executing {func_name}: {str(e)}"
    else:
        tool_result = "No specific flight tool needed. Using general knowledge."

    # Step 3: DeepSeek for natural, conversational flight response
    history_text = "\n".join([f"{m['role']}: {m['content']}" for m in history[-4:]])
    
    ollama_prompt = f"""You are a Swiss Airlines flight expert assistant.

Conversation history:
{history_text}

User's question: {user_query}

Tool result (trusted data):
{tool_result}

Instructions:
- Provide a natural, helpful response based on the tool result
- Be conversational and professional
- If flights are available, present them clearly with key details (flight number, route, time, price)
- If no results, suggest alternatives or ask for more details
- Keep response concise but complete

Your response:"""

    try:
        ollama_response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[{"role": "user", "content": ollama_prompt}],
            options={"temperature": 0.7, "num_predict": 400}
        )
        bot_content = ollama_response["message"]["content"].strip()
        logger.info("✓ Ollama response generated")
    except Exception as e:
        logger.error(f"Ollama failed: {e}")
        bot_content = f"I found flight information but had trouble formatting it. Raw data: {tool_result[:200]}"

    state["messages"].append({"role": "assistant", "content": bot_content})
    return state