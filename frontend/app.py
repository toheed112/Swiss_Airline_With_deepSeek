# frontend/app.py - Streamlit UI for Swiss Airlines Chatbot

# ----------------------------
# FIX: add project root to PYTHONPATH
# ----------------------------
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# ----------------------------
# ORIGINAL CODE (UNCHANGED)
# ----------------------------
import streamlit as st
import logging
from dotenv import load_dotenv

load_dotenv()

from backend.graph.workflow import run_graph_v4
from backend.tools.utilities import fetch_user_info

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page config
st.set_page_config(
    page_title="Swiss Airlines Assistant",
    page_icon="✈️",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .stTextInput>div>div>input {
        font-size: 16px;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .user-message {
        background-color: #e3f2fd;
    }
    .assistant-message {
        background-color: #f5f5f5;
    }
</style>
""", unsafe_allow_html=True)

# Title and header
st.title("✈️ Swiss Airlines Virtual Assistant")
st.markdown("Ask me about flights, hotels, car rentals, excursions, or company policies!")

# Sidebar with configuration
with st.sidebar:
    st.header("Configuration")
    passenger_id = st.text_input(
        "Passenger ID",
        value="3442 587242",
        help="Enter your passenger ID for personalized service"
    )
    
    st.markdown("---")
    st.markdown("### Features")
    st.markdown("✓ Flight search & booking")
    st.markdown("✓ Hotel reservations")
    st.markdown("✓ Car rentals")
    st.markdown("✓ Excursion booking")
    st.markdown("✓ Policy information")
    st.markdown("✓ Live web search")
    
    st.markdown("---")
    if st.button("Clear Chat History"):
        st.session_state.history = []
        st.success("Chat history cleared!")
        st.rerun()

# Initialize session state
if 'history' not in st.session_state:
    st.session_state.history = []
if 'processing' not in st.session_state:
    st.session_state.processing = False

# Configuration
config = {
    "passenger_id": passenger_id.replace(" ", ""),
    "user_info": ""
}

# Display chat history
for message in st.session_state.history:
    role = message.get("role", "")
    content = message.get("content", "")
    
    if role == "user":
        st.markdown(
            f'<div class="chat-message user-message"><strong>You:</strong> {content}</div>',
            unsafe_allow_html=True
        )
    elif role == "assistant":
        st.markdown(
            f'<div class="chat-message assistant-message"><strong>Assistant:</strong> {content}</div>',
            unsafe_allow_html=True
        )

# Chat input
user_input = st.chat_input("Ask about flights, hotels, or anything else...")

if user_input and not st.session_state.processing:
    st.session_state.processing = True
    
    try:
        # Add user message to display
        st.session_state.history.append({"role": "user", "content": user_input})
        
        # Show processing message
        with st.spinner("🤔 Thinking..."):
            # Run the graph workflow
            updated_history = run_graph_v4(
                user_input=user_input,
                config=config,
                history=st.session_state.history[:-1]  # Exclude the just-added user message
            )
            
            # Update session state with new history
            st.session_state.history = updated_history
        
        # Rerun to display new messages
        st.rerun()
        
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        st.error(f"An error occurred: {str(e)}")
        st.session_state.history.append({
            "role": "assistant",
            "content": "I apologize, but I encountered an error. Please try again."
        })
    
    finally:
        st.session_state.processing = False

# Example queries
if not st.session_state.history:
    st.markdown("### 💡 Try asking:")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🛫 Search flights from Zurich"):
            st.session_state.temp_input = "Show me flights from Zurich"
            st.rerun()
    
    with col2:
        if st.button("🏨 Find hotels in Zurich"):
            st.session_state.temp_input = "I need a hotel in Zurich"
            st.rerun()
    
    with col3:
        if st.button("📋 Cancellation policy"):
            st.session_state.temp_input = "What's the cancellation policy?"
            st.rerun()

# Footer
st.markdown("---")
st.markdown(
    "<center><small>Swiss Airlines Virtual Assistant v4 • Powered by AI</small></center>",
    unsafe_allow_html=True
)
