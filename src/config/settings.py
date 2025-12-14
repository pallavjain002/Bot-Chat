from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    groq_api_key: str
    redis_url: str = "redis://localhost:6379"
    database_url: str

    class Config:
        env_file = ".env"

settings = Settings()
