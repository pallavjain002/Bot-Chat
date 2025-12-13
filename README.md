# BOT GPT Conversational Backend

A production-grade conversational AI backend for BOT GPT, supporting open chat and grounded/RAG modes.

## Features
- REST API for conversation management (CRUD)
- Integration with Groq API (Llama models)
- SQLite persistence
- RAG simulation for grounded conversations
- Docker support
- Unit tests

## Setup

1. Clone the repo
2. Create virtual environment: `python3 -m venv .venv && source .venv/bin/activate`
3. Install dependencies: `pip install -r requirements.txt`
4. Set environment variables: `export GROQ_API_KEY=your_key`
5. Run: `uvicorn src.main:app --reload`

## API Endpoints

- POST /conversations: Create new conversation
- GET /conversations?user_id=1: List conversations
- GET /conversations/{id}: Get history
- PUT /conversations/{id}/messages: Add message
- DELETE /conversations/{id}: Delete conversation

## Testing

Run tests: `pytest app/tests/`

## Docker

Build: `docker build -t bot-gpt .`
Run: `docker run -p 8000:8000 bot-gpt`