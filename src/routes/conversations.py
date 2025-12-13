from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.models import get_db, Conversation, ChatMode
from src.services.conversation_service import ConversationService
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()

class CreateConversationRequest(BaseModel):
    user_id: int
    first_message: str
    mode: ChatMode = ChatMode.open
    document_ids: Optional[List[int]] = None

class AddMessageRequest(BaseModel):
    message: str
    document_ids: Optional[List[int]] = None

@router.post("/conversations", response_model=dict)
async def create_conversation(request: CreateConversationRequest, db: Session = Depends(get_db)):
    try:
        service = ConversationService(db)
        conversation = await service.create_conversation(request.user_id, request.first_message, request.mode, request.document_ids)
        return {"conversation_id": conversation.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/conversations", response_model=List[dict])
def list_conversations(user_id: int, db: Session = Depends(get_db)):
    service = ConversationService(db)
    return service.list_conversations(user_id)

@router.get("/conversations/{conversation_id}", response_model=List[dict])
def get_conversation_history(conversation_id: int, db: Session = Depends(get_db)):
    service = ConversationService(db)
    return service.get_conversation_history(conversation_id)

@router.put("/conversations/{conversation_id}/messages", response_model=dict)
async def add_message(conversation_id: int, request: AddMessageRequest, db: Session = Depends(get_db)):
    try:
        service = ConversationService(db)
        return await service.add_message(conversation_id, request.message, request.document_ids)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/conversations/{conversation_id}")
def delete_conversation(conversation_id: int, db: Session = Depends(get_db)):
    service = ConversationService(db)
    service.delete_conversation(conversation_id)
    return {"message": "Conversation deleted"}