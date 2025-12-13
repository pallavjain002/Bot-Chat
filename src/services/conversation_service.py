from sqlalchemy.orm import Session
from src.models import Conversation, Message, Document, ChatMode
from src.services.llm_service import llm_service
from typing import List, Dict, Optional

class ConversationService:
    def __init__(self, db: Session):
        self.db = db

    async def create_conversation(self, user_id: int, first_message: str, mode: ChatMode = ChatMode.open, document_ids: Optional[List[int]] = None) -> Conversation:
        conversation = Conversation(user_id=user_id, mode=mode)
        self.db.add(conversation)
        self.db.commit()
        self.db.refresh(conversation)

        response = await self.add_message(conversation.id, first_message, document_ids)        
        return conversation

    async def add_message(self, conversation_id: int, user_message: str, document_ids: Optional[List[int]] = None) -> Dict:
        conversation = self.db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if not conversation:
            raise ValueError("Conversation not found")

        existing_messages = self.db.query(Message).filter(Message.conversation_id == conversation_id).order_by(Message.timestamp).all()
        history = [{"role": msg.role, "content": msg.content} for msg in existing_messages]

        history.append({"role": "user", "content": user_message})
        if conversation.mode == ChatMode.grounded and document_ids:
            document_chunks = []
            for doc_id in document_ids:
                doc = self.db.query(Document).filter(Document.id == doc_id).first()
                if doc:
                    document_chunks.extend(doc.content.split("\n\n"))
            rag_context = llm_service.retrieve_rag_context(user_message, document_chunks)
            history.insert(0, {"role": "system", "content": f"Relevant context: {rag_context}"})

        try:
            llm_response = await llm_service.call_llm(history)
        except Exception as e:
            print(f"LLM Failed: {e}")
            raise e
        user_msg = Message(conversation_id=conversation_id, role="user", content=user_message)
        assistant_msg = Message(conversation_id=conversation_id, role="assistant", content=llm_response["content"], tokens_used=llm_response["tokens_used"])
        self.db.add(user_msg)
        self.db.add(assistant_msg)
        self.db.commit()

        return {"user_message": user_message, "assistant_response": llm_response["content"]}

    def get_conversation_history(self, conversation_id: int) -> List[Dict]:
        messages = self.db.query(Message).filter(Message.conversation_id == conversation_id).order_by(Message.timestamp).all()
        return [{"role": msg.role, "content": msg.content, "timestamp": msg.timestamp} for msg in messages]

    def list_conversations(self, user_id: int) -> List[Dict]:
        conversations = self.db.query(Conversation).filter(Conversation.user_id == user_id).all()
        return [{"id": c.id, "title": c.title, "mode": c.mode.value, "created_at": c.created_at} for c in conversations]

    def delete_conversation(self, conversation_id: int):
        self.db.query(Message).filter(Message.conversation_id == conversation_id).delete()
        self.db.query(Document).filter(Document.conversation_id == conversation_id).delete()
        self.db.query(Conversation).filter(Conversation.id == conversation_id).delete()
        self.db.commit()