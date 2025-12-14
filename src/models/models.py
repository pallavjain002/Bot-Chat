from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy import Enum as SQLEnum
from .database import Base
import enum

class ChatMode(enum.Enum):
    OPEN = "open"
    GROUNDED = "grounded"

class ConversationState(enum.Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    conversations = relationship("Conversation", back_populates="user")

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String, nullable=True)
    mode = Column(
        SQLEnum(
            ChatMode,
            values_callable=lambda e: [i.value for i in e],
            name="chatmode",
        ),
        default=ChatMode.OPEN,
        nullable=False,
    )

    state = Column(
        SQLEnum(
            ConversationState,
            values_callable=lambda e: [i.value for i in e],
            name="conversationstate",
        ),
        default=ConversationState.ACTIVE,
        nullable=False,
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation")
    documents = relationship("Document", back_populates="conversation")

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"))
    role = Column(String)  # user or assistant or system
    content = Column(Text)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    tokens_used = Column(Integer, nullable=True)

    conversation = relationship("Conversation", back_populates="messages")

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"))
    name = Column(String)
    content = Column(Text)  # Chunked content for RAG

    conversation = relationship("Conversation", back_populates="documents")