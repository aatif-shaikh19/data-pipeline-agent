from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings and environment configuration."""
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # LLM Settings
    LLM_PROVIDER: str = "groq"
    GROQ_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    GROQ_MODEL: str = "qwen/qwen3.8-27b"
    GEMINI_MODEL: str = "gemini-2.0-flash"

    # Database
    DATABASE_URL: str = ""

    # Auth: Bearer Token Hash (SHA-256)
    API_BEARER_TOKEN: Optional[str] = None
    API_BEARER_TOKEN_HASH: str = ""

    # App
    ENVIRONMENT: str = "development"
    PORT: int = 8000
    RATE_LIMIT_STRING: str = "20/minute"


settings = Settings()
