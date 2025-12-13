# BOT GPT Backend Design Document

## Architecture & Design

### High-Level Architecture Diagram

```
[Client] -> [FastAPI (API Layer)] -> [ConversationService (Service Layer)] -> [LLMService] -> [Groq API]
                                      |                                      |
                                      v                                      v
                               [SQLAlchemy (DB Layer)]               [Redis (Caching)]
                                      |
                                      v
                               [SQLite/PostgreSQL]
```

- **API Layer**: FastAPI handles HTTP requests, validation, and responses.
- **Service Layer**: Business logic for conversations, messages, and LLM calls.
- **DB Layer**: SQLAlchemy ORM for data persistence.
- **LLM Integration**: Async calls to Groq API with context management.

### Tech Stack Justification

- **FastAPI**: Async support, auto-docs, type validation. Chosen for scalability and ease of API development.
- **SQLAlchemy**: ORM for database interactions, supports multiple DBs.
- **SQLite**: Simple, file-based DB for development; can switch to PostgreSQL for production.
- **Redis**: For caching conversation history to reduce token costs.
- **Groq API**: Free tier Llama models, cost-effective.

## Data & Storage Design

### Database Choice
SQLite for simplicity and zero-config. Justified: Easy setup, ACID compliant, sufficient for moderate load. For production, switch to PostgreSQL for concurrency.

### Schema
- **User**: id (PK), username, email, created_at
- **Conversation**: id (PK), user_id (FK), title, mode (open/grounded), created_at, updated_at
- **Message**: id (PK), conversation_id (FK), role, content, timestamp, tokens_used
- **Document**: id (PK), conversation_id (FK), name, content (chunked)

Message ordering: By timestamp ASC.

## REST API Design

- **POST /conversations**: Payload {user_id, first_message, mode?, document_ids?} -> {conversation_id}
- **GET /conversations?user_id=**: List conversations for user
- **GET /conversations/{id}**: Full history
- **PUT /conversations/{id}/messages**: Payload {message, document_ids?} -> {user_message, assistant_response}
- **DELETE /conversations/{id}**: Delete conversation

HTTP Codes: 200 OK, 404 Not Found, 500 Internal Error.

## LLM Context & Cost Management

Context constructed from message history. Sliding window: Trim oldest messages if total tokens > 4000.

Strategies: Summarization (future), caching frequent responses, system prompts for grounding.

## Error Handling & Scalability

Errors: LLM timeout -> Retry 3x, DB failure -> Rollback, Token breach -> Trim context.

Scalability: API horizontal scaling, DB read replicas, Redis sharding. Bottleneck at LLM API rate limits; use queues for async processing.

## Deployment & DevOps

GitHub repo with CI/CD (tests on push). Dockerfile for containerization. Unit tests for core logic.