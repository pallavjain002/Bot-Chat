from sqlalchemy.orm import Session
from src.models import User
from pydantic import BaseModel
from typing import List, Dict

class UserService:
    def __init__(self, db: Session):
        self.db = db

    def create_user(self, username: str, email: str) -> User:
        # Check if user already exists
        if self.db.query(User).filter(User.username == username).first():
            raise ValueError("Username already registered")
        if self.db.query(User).filter(User.email == email).first():
            raise ValueError("Email already registered")
            
        new_user = User(username=username, email=email)
        self.db.add(new_user)
        self.db.commit()
        self.db.refresh(new_user)
        return new_user

    def get_user(self, user_id: int) -> User:
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")
        return user

    def list_users(self) -> List[Dict]:
        users = self.db.query(User).all()
        return [{"id": u.id, "username": u.username, "email": u.email, "created_at": u.created_at} for u in users]
