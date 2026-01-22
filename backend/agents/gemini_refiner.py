# backend/agents/gemini_refiner.py
# Gemini is used ONLY for refinement or fallback (FREE TIER SAFE)

import os
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# ONLY free + guaranteed model
GEMINI_MODEL = "gemini-1.5-flash"

# Try importing Gemini
try:
    from google import genai
    _client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None
except ImportError:
    logger.warning("google-generativeai not installed. Gemini features disabled.")
    _client = None


def refine_with_gemini(prompt: str) -> str:
    """
    Refines an already-generated response.
    NO tool calling, NO routing, NO hallucination.
    """
    if not _client:
        logger.warning("Gemini client not available")
        return prompt  # Return original if Gemini unavailable
    
    try:
        response = _client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
        )
        result = response.text.strip()
        logger.info("✓ Gemini refinement successful")
        return result
    except Exception as e:
        logger.error(f"Gemini refinement failed: {e}")
        return prompt  # Return original on error