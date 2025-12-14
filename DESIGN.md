# BOT GPT – Conversational Backend Design Document

## 1. Overview

BOT GPT is a production-grade conversational backend designed to support:

- Open-ended chat with Large Language Models (LLMs)
- Grounded conversations (RAG) over user-provided documents
- Persistent, multi-turn conversations
- Cost-aware, scalable LLM integration

This system focuses on clean backend architecture, API design, data modeling, and LLM orchestration, not model training or fine-tuning.

### High-Level Architecture Diagram

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────┐
│         CLIENT / USER INTERFACE                 │
└──────────────────┬──────────────────────────────┘
                   │ HTTP/REST (JSON)
                   ▼
┌─────────────────────────────────────────────────┐
│                  API LAYER                      │
│    FastAPI - Routes, Validation, Auth           │
└──────────────────┬──────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────┐
│           SERVICE LAYER                         │
│  ┌──────────────────┐  ┌──────────────────┐     │
│  │ Conversation     │  │  RAG Service     │     │
│  │   Service        │  │  (Retrieval)     │     │
│  └──────────────────┘  └──────────────────┘     │
└────────┬─────────────────────────┬──────────────┘
         │                         │
         ▼                         ▼
┌──────────────────┐    ┌──────────────────────┐
│  DATA LAYER      │    │  INTEGRATION LAYER   │
│  SQLAlchemy ORM  │    │    LLM Service       │
└────────┬─────────┘    └──────────┬───────────┘
         │                         │
         ▼                         ▼
┌──────────────────┐    ┌──────────────────────┐
│   PostgreSQL     │    │   Groq API (Llama)   │
│   + Redis Cache  │    │   External Provider  │
└──────────────────┘    └──────────────────────┘
```
**RAG Flow:**

```
+---+---------------------------------------------------+
|            SERVICE LAYER (Orchestrator)               |
|                                                       |
|  +-------------------------------------------------+  |
|  | (A) RETRIEVAL PHASE                             |  |
|  | 1. Identify associated document IDs             |  |
|  | 2. Perform simple keyword/text search on        |  |
|  |    document chunks in DB based on user query.   |  |
|  |    (Simulated Retrieval)                        |  |
|  +------------------------+------------------------+  |
|                           |                           |
|                           | (3) Search Query          |
|                           V                           |
|  +------------------------+------------------------+  |
|  |             DATA LAYER (Storage)                |  |
|  | [Stored Document Text Chunks]                   |  |
|  +------------------------+------------------------+  |
|                           |                           |
|                           | (4) Return Relevant Chunks|
|                           V                           |
|  +------------------------+------------------------+  |
|  | (B) AUGMENTATION & GENERATION PHASE             |  |
|  | 1. Retrieve Conversation History from DB.       |  |
|  |                                                 |  |
|  | 2. Construct Prompt: Combine System instructions,| |
|  |    retrieved context chunks, history, and current| |
|  |    user message.                                |  |
|  +------------------------+------------------------+  |
|                           |                           |
|                           | (5) Call LLM API with     |
|                           |     constructed prompt    |
|                           |                           |
|                           V                           |
+---+-----------------------+---------------------------+
```


- **API Layer**: FastAPI for validation, auth, routing, Swagger docs
- **Service Layer**: Conversation Service for state management, RAG Service for retrieval
- **LLM Service**: Prompt construction, token management, LLM calls
- **Database**: PostgreSQL for ACID compliance and concurrency
- **Caching**: Redis for recent conversations and token optimization

## 3. Tech Stack & Justification

| Component | Technology | Justification |
|-----------|------------|---------------|
| API | FastAPI | Async support, auto-generated docs, type safety |
| Database | PostgreSQL | ACID compliance, concurrency, scalability |
| ORM | SQLAlchemy | Clean schema modeling |
| Cache | Redis | Reduce DB reads and LLM token costs |
| LLM | Groq API (Llama) | Free tier, low latency, production-ready |
| Deployment | Docker | Reproducible builds, easy scaling |

## 4. Core Conversation Flow

**Modes Supported:**

- **Open Chat Mode**: No external context, conversation history forwarded to LLM
- **Grounded Chat (RAG) Mode**: Conversation linked to documents, relevant chunks retrieved per query

In both modes: Conversation history persisted, messages ordered, token usage tracked.

## 5. Data & Storage Design

**Entities:**

- **User**: id (PK), username, email, created_at
- **Conversation**: id (PK), user_id (FK), title, mode (open/grounded), state (active/archived), created_at, updated_at
- **Message**: id (PK), conversation_id (FK), role (user/assistant/system), content, timestamp, tokens_used
- **Document**: id (PK), conversation_id (FK), name, content_chunks (stored as chunked text)

### Entity Relationship Diagram

```
┌─────────────┐
│    User     │
│─────────────│
│ id (PK)     │
│ username    │
│ email       │
│ created_at  │
└──────┬──────┘
       │ 1:N
       │
┌──────▼────────────┐
│  Conversation     │
│───────────────────│
│ id (PK)           │
│ user_id (FK)      │
│ title             │
│ mode (enum)       │◄─────┐
│ state (enum)      │      │ 1:N
│ created_at        │      │
│ updated_at        │      │
└──────┬────────────┘      │
       │ 1:N               │
       │            ┌──────┴────────┐
┌──────▼──────────┐ │   Document    │
│    Message      │ │───────────────│
│─────────────────│ │ id (PK)       │
│ id (PK)         │ │ conv_id (FK)  │
│ conv_id (FK)    │ │ name          │
│ role (enum)     │ │ chunks (text) │
│ content (text)  │ │ uploaded_at   │
│ timestamp       │ └───────────────┘
│ tokens_used     │
└─────────────────┘
```

**Document Storage and Chunking:**

Documents are associated with conversations via document_ids. Content is chunked into passages (500–800 tokens) and stored as delimited text in the database. For simulation, chunks are split by double newlines (\n\n) and stored as a single text field.

**Message Ordering:** Messages ordered by timestamp ASC for deterministic context reconstruction.

## Message Processing & LLM Integration

### Processing Flow

```
1. Client Request
   ↓
2. Validate Ownership (user owns conversation)
   ↓
3. Fetch Conversation History from DB
   ↓
4. Apply Token Window (sliding window if > 4000 tokens)
   ↓
5. RAG Mode: Retrieve Relevant Document Chunks
   ↓
6. Construct Prompt
   • System prompt
   • Retrieved context (if RAG)
   • Conversation history
   • User query
   ↓
7. Call LLM API (Groq)
   ↓
8. Parse Response & Count Tokens
   ↓
9. Persist Assistant Message to DB
   ↓
10. Return Response to Client
```

## 6. Conversation Lifecycle

| State | Description |
|-------|-------------|
| ACTIVE | Ongoing conversation |
| ARCHIVED | Read-only, preserved |
| DELETED | Soft-deleted |

State transitions enforced at service layer for data integrity.

## 7. REST API Design

**Endpoints:**

- **POST /users**: Create User
- **GET /users/{user_id}**: Get user details
- **GET /users**: List users

- **POST /conversations**: Create conversation, payload {user_id, first_message, mode?, document_ids?}
- **POST /conversations/{id}/messages**: Add message, payload {message}
- **GET /conversations?user_id=**: List user conversations
- **GET /conversations/{id}**: Get conversation history
- **DELETE /conversations/{id}**: Delete conversation
- **PATCH /conversations/{conversation_id}/archive**: Archive a conversation

**HTTP Status Codes:** 200 OK, 404 Not Found, 400 Bad Request, 500 Internal Server Error.

## 8. Message Processing Flow

1. Client sends user message
2. API validates ownership and payload
3. Service retrieves conversation history
4. Apply token window (sliding window)
5. For grounded mode: Retrieve relevant document chunks
6. Assemble prompt with context
7. Invoke LLM API
8. Persist assistant response
9. Return response to client

This ensures LLM statelessness while backend owns conversation state.

## 9. Prompt Construction Strategy

**Prompt Structure:**

- System Prompt: Defines behavior and safety
- Context: Retrieved document chunks (RAG mode)
- Conversation History: Last N messages
- User Query

Layered approach minimizes hallucinations and controls costs.

## 10. RAG Retrieval Strategy

**Document Indexing and Storage:**

Documents uploaded and associated with conversations. Content chunked into passages (e.g., by paragraphs or fixed token size) and stored in database as text.

**Retrieval Method:**

For each user message, perform simple keyword matching: Split query into words, find chunks with overlapping words. Select top K (e.g., 3) relevant chunks. This simulates retrieval without complex infrastructure.

**Context Combination:**

Retrieved chunks concatenated and injected as system message: "Relevant context: [chunks]". Combined with conversation history and user query in LLM prompt. Entire documents never sent to LLM.

Balances relevance, cost, and latency.

## 11. LLM Context & Cost Management

**Strategies:**

- Sliding window for history (Trim oldest messages if total tokens > 4000)
- Token counting per message
- Future: Redis caching for repeated context 
- Future: Automated summarization

**Benefits:** Reduced costs, faster responses, predictable usage.

## 12. Error Handling

| Failure | Handling |
|---------|----------|
| LLM timeout | Retry with backoff |
| Token overflow | Context trimming |
| DB failure | Transaction rollback |
| Invalid state | Graceful error response |

## 13. Scalability Analysis

### 13.1 Bottleneck Identification

**At 1M Users:**

1. **LLM API Rate Limits** (Primary Bottleneck)
   - Solution: Use async workers (Celery) for non-blocking calls

2. **Database Connections**
   - Solution: Connection pooling

3. **API Server Capacity**
   - Solution: Horizontal scaling (Kubernetes pods)

## 14. Security Considerations

- User-level conversation authorization (middleware)
- Rate limiting
- Environment-based secrets

## 15. Deployment & DevOps

- Public GitHub repo
- Dockerized application
- CI pipeline with tests
- Swagger API docs

## 16. Future Enhancements

- Streaming responses (SSE/WebSockets)
- Vector DB integration for advanced RAG
- Usage analytics dashboard

**Conclusion:** Design prioritizes clarity, scalability, and cost-efficiency for production conversational AI.