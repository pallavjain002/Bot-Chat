import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.models import Base, get_db, Conversation, Message
from src.services.conversation_service import ConversationService
from src.models.models import ChatMode

# Test database
TEST_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

def test_create_conversation(db_session):
    service = ConversationService(db_session)
    # Mock LLM call since we can't call real API in tests
    # For simplicity, assume add_message is tested separately
    conversation = Conversation(user_id=1, mode=ChatMode.open)
    db_session.add(conversation)
    db_session.commit()
    assert conversation.id is not None

def test_add_message(db_session):
    service = ConversationService(db_session)
    conversation = Conversation(user_id=1, mode=ChatMode.open)
    db_session.add(conversation)
    db_session.commit()

    # Mock the LLM response
    # In real test, mock the llm_service.call_llm
    user_msg = Message(conversation_id=conversation.id, role="user", content="Hello")
    db_session.add(user_msg)
    assistant_msg = Message(conversation_id=conversation.id, role="assistant", content="Hi there")
    db_session.add(assistant_msg)
    db_session.commit()

    history = service.get_conversation_history(conversation.id)
    assert len(history) == 2
    assert history[0]["content"] == "Hello"
    assert history[1]["content"] == "Hi there"

def test_list_conversations(db_session):
    service = ConversationService(db_session)
    conv1 = Conversation(user_id=1, mode=ChatMode.open)
    conv2 = Conversation(user_id=1, mode=ChatMode.grounded)
    db_session.add_all([conv1, conv2])
    db_session.commit()

    conversations = service.list_conversations(1)
    assert len(conversations) == 2