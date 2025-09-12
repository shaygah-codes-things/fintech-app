from pydantic import BaseModel
import os

from dotenv import load_dotenv

load_dotenv(dotenv_path="../.env")


class Settings(BaseModel):
    env: str = os.getenv("ENV", "dev")
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://postgres:postgres@localhost:5432/fintech_app",
    )
    cors_origins: str = os.getenv("CORS_ORIGINS", "http://localhost:5173")
    webhook_secret: str = os.getenv("WEBHOOK_SHARED_SECRET", "changeme")


settings = Settings()
