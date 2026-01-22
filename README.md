# Swiss Airlines Chatbot (LangGraph-Inspired)

Adapted for Ollama (conversational AI), OpenAI (embeddings), Tavily (search).

## Setup
1. Edit .env with API keys (OpenAI, Tavily).
2. pip install -r requirements.txt
3. ollama serve (terminal)
4. python backend/database/populate_db.py (setup DB)
5. streamlit run frontend/app.py (launch UI)

## VS Code
- Open folder, select Python interpreter.
- Run 'pip install -r requirements.txt' in terminal.
- F5 to debug main.py.

## Structure
- backend/database: SQLite setup.
- backend/tools: RAG, flights, etc.
- backend/agents: Specialized assistants.
- backend/graph: Workflow simulation.
- frontend: Streamlit UI.
- data: DB files.
