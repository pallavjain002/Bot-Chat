from sqlalchemy.orm import Session
from src.models import User
from pydantic import BaseModel
from typing import List, Dict
import redis
import json

class UserService:
    def __init__(self, db: Session, redis_client: redis.Redis):
        self.db = db
        self.redis = redis_client

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
        self.redis.delete("users")
        return new_user

    def get_user(self, user_id: int) -> User:
        cached_user = self.redis.get(f"user:{user_id}")
        if cached_user:
            return User(**json.loads(cached_user))
            
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")
        
        user_dict = {"id": user.id, "username": user.username, "email": user.email, "created_at": user.created_at.isoformat()}
        self.redis.set(f"user:{user_id}", json.dumps(user_dict), ex=3600) # Cache for 1 hour
        return user

    def list_users(self) -> List[Dict]:
        cached_users = self.redis.get("users")
        if cached_users:
            return json.loads(cached_users)

        users = self.db.query(User).all()
        user_list = [{"id": u.id, "username": u.username, "email": u.email, "created_at": u.created_at.isoformat()} for u in users]
        self.redis.set("users", json.dumps(user_list), ex=3600) # Cache for 1 hour
        return user_list
