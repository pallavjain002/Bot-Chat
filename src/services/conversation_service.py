from sqlalchemy.orm import Session
from src.models import Conversation, Message, Document, ChatMode, ConversationState
from src.services.llm_service import LLMService
from typing import List, Dict, Optional
import redis
import json

class ConversationService:
    def __init__(self, db: Session, redis_client: redis.Redis):
        self.db = db
        self.redis = redis_client
        self.llm_service = LLMService()

    async def create_conversation(self, user_id: int, first_message: str, mode: ChatMode = ChatMode.OPEN, document_ids: Optional[List[int]] = None) -> Conversation:
        conversation = Conversation(user_id=user_id, mode=mode, state=ConversationState.ACTIVE)
        self.db.add(conversation)
        self.db.commit()
        self.db.refresh(conversation)

        response = await self.add_message(conversation.id, first_message, document_ids)
        self.redis.delete(f"conversations:{user_id}")
        return conversation

    async def add_message(self, conversation_id: int, user_message: str, document_ids: Optional[List[int]] = None) -> Dict:
        conversation = self.db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if not conversation or conversation.state != ConversationState.ACTIVE:
            raise ValueError("Conversation not found or not active")

        existing_messages = self.db.query(Message).filter(Message.conversation_id == conversation_id).order_by(Message.timestamp).all()
        history = [{"role": msg.role, "content": msg.content} for msg in existing_messages]

        history.append({"role": "user", "content": user_message})
        if conversation.mode == ChatMode.GROUNDED and document_ids:
            document_chunks = []
            for doc_id in document_ids:
                doc = self.db.query(Document).filter(Document.id == doc_id).first()
                if doc:
                    document_chunks.extend(doc.content.split("\n\n"))
            rag_context = self.llm_service.retrieve_rag_context(user_message, document_chunks)
            history.insert(0, {"role": "system", "content": f"Relevant context: {rag_context}"})

        try:
            llm_response = await self.llm_service.call_llm(history)
        except Exception as e:
            print(f"LLM Failed: {e}")
            raise e
        user_msg = Message(conversation_id=conversation_id, role="user", content=user_message)
        assistant_msg = Message(conversation_id=conversation_id, role="assistant", content=llm_response["content"], tokens_used=llm_response["tokens_used"])
        self.db.add(user_msg)
        self.db.add(assistant_msg)
        self.db.commit()

        self.redis.delete(f"conversation:{conversation_id}:history")

        return {"user_message": user_message, "assistant_response": llm_response["content"]}

    def get_conversation_history(self, conversation_id: int) -> List[Dict]:
        conversation = self.db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if not conversation or conversation.state == ConversationState.DELETED:
            raise ValueError("Conversation not found")

        cached_history = self.redis.get(f"conversation:{conversation_id}:history")
        if cached_history:
            return json.loads(cached_history)

        messages = self.db.query(Message).filter(Message.conversation_id == conversation_id).order_by(Message.timestamp).all()
        history = [{"role": msg.role, "content": msg.content, "timestamp": msg.timestamp.isoformat()} for msg in messages]
        self.redis.set(f"conversation:{conversation_id}:history", json.dumps(history), ex=3600) # Cache for 1 hour
        return history

    def list_conversations(self, user_id: int, page: int = 1, limit: int = 10) -> Dict:
        offset = (page - 1) * limit
        total = self.db.query(Conversation).filter(Conversation.user_id == user_id, Conversation.state != ConversationState.DELETED).count()
        conversations = self.db.query(Conversation).filter(Conversation.user_id == user_id, Conversation.state != ConversationState.DELETED).order_by(Conversation.created_at.desc()).offset(offset).limit(limit).all()
        conversation_list = [{"id": c.id, "title": c.title, "mode": c.mode.value, "state": c.state.value, "created_at": c.created_at.isoformat()} for c in conversations]
        return {"conversations": conversation_list, "page": page, "limit": limit, "total": total}

    def delete_conversation(self, conversation_id: int):
        conversation = self.db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if conversation and conversation.state != ConversationState.DELETED:
            conversation.state = ConversationState.DELETED
            self.db.commit()
            self.redis.delete(f"conversation:{conversation_id}:history")
            self.redis.delete(f"conversations:{conversation.user_id}")

    def archive_conversation(self, conversation_id: int):
        conversation = self.db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if conversation and conversation.state == ConversationState.ACTIVE:
            conversation.state = ConversationState.ARCHIVED
            self.db.commit()
            self.redis.delete(f"conversation:{conversation_id}:history")
            self.redis.delete(f"conversations:{conversation.user_id}")

