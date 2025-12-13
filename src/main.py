from fastapi import FastAPI
from src.models import Base, engine
from src.routes.conversations import router as conversations_router
from src.routes.users import router as users_router

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="BOT GPT Backend", version="1.0.0")

app.include_router(conversations_router, prefix="/api/v1", tags=["Conversations"])
app.include_router(users_router, prefix="/api/v1", tags=["Users"])

@app.get("/")
def root():
    return {"message": "BOT GPT Conversational Backend"}
