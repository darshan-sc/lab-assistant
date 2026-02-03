from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = BACKEND_DIR / ".env"

class Settings(BaseSettings):
    PROJECT_NAME: str = "ResearchNexus"
    DATABASE_URL: str
    MAX_UPLOAD_MB: int

    # Supabase Auth
    SUPABASE_URL: str = ""
    SUPABASE_JWT_SECRET: str = ""
    SUPABASE_JWT_ALGORITHM: str = "HS256"
    SUPABASE_JWT_PUBLIC_KEY: str = ""
    
    # CORS
    CORS_ORIGINS: str = ""

    # OpenAI
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"

    # Worker
    WORKER_POLL_INTERVAL: int = 5
    WORKER_MAX_RETRIES: int = 3

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

settings = Settings()