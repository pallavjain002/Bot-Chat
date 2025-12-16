import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.models import Base, Conversation, Message, ChatMode
from src.services.conversation_service import ConversationService

# ---------------------------
# Test DB setup
# ---------------------------
TEST_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture
def mock_redis():
    redis = MagicMock()
    redis.get.return_value = None
    return redis

# ---------------------------
# Tests
# ---------------------------

@pytest.mark.asyncio
async def test_create_conversation(db_session, mock_redis, monkeypatch):
    service = ConversationService(db_session, mock_redis)

    # Mock LLM call
    monkeypatch.setattr(
        service.llm_service,
        "call_llm",
        AsyncMock(return_value={"content": "Hi!", "tokens_used": 5})
    )

    conversation = await service.create_conversation(
        user_id=1,
        first_message="Hello",
        mode=ChatMode.OPEN
    )

    assert conversation.id is not None

    messages = (
        db_session.query(Message)
        .filter(Message.conversation_id == conversation.id)
        .all()
    )
    assert len(messages) == 2
    assert messages[0].role == "user"
    assert messages[1].role == "assistant"


@pytest.mark.asyncio
async def test_get_conversation_history(db_session, mock_redis):
    service = ConversationService(db_session, mock_redis)

    conversation = Conversation(user_id=1, mode=ChatMode.OPEN)
    db_session.add(conversation)
    db_session.commit()

    db_session.add_all([
        Message(conversation_id=conversation.id, role="user", content="Hello"),
        Message(conversation_id=conversation.id, role="assistant", content="Hi")
    ])
    db_session.commit()

    history = service.get_conversation_history(conversation.id)

    assert len(history) == 2
    assert history[0]["content"] == "Hello"
    assert history[1]["content"] == "Hi"
