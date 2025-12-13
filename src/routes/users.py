from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.models import get_db
from src.services.user_service import UserService
from pydantic import BaseModel
from typing import List

router = APIRouter()

class CreateUserRequest(BaseModel):
    username: str
    email: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str

    class Config:
        from_attributes = True

@router.post("/users", response_model=UserResponse, tags=["Users"])
def create_user(request: CreateUserRequest, db: Session = Depends(get_db)):
    try:
        service = UserService(db)
        user = service.create_user(username=request.username, email=request.email)
        return user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/users/{user_id}", response_model=UserResponse, tags=["Users"])
def get_user(user_id: int, db: Session = Depends(get_db)):
    try:
        service = UserService(db)
        user = service.get_user(user_id)
        return user
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/users", response_model=List[UserResponse], tags=["Users"])
def list_users(db: Session = Depends(get_db)):
    service = UserService(db)
    return service.list_users()
