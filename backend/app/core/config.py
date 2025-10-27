"""Application configuration"""

from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
import yaml
from pathlib import Path


class Settings(BaseSettings):
    """Application settings"""

    # Application
    APP_NAME: str = "AccuSync"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_RELOAD: bool = True

    # Database
    DATABASE_URL: str
    POSTGRES_USER: str = "accusync"
    POSTGRES_PASSWORD: str = "accusync_pass"
    POSTGRES_DB: str = "accusync"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Storage (S3 compatible)
    S3_ENDPOINT: str = "http://localhost:9000"
    S3_ACCESS_KEY: str = "minioadmin"
    S3_SECRET_KEY: str = "minioadmin"
    S3_BUCKET: str = "accusync-storage"
    S3_REGION: str = "us-east-1"

    # AI Configuration
    AI_PROVIDER: str = "openai"  # openai, claude, google_document_ai, multi
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    GOOGLE_CREDENTIALS_PATH: Optional[str] = None
    GOOGLE_PROJECT_ID: Optional[str] = None

    # AI Feature Flags
    AI_ENABLE_FILE_DETECTION: bool = True
    AI_ENABLE_DATA_EXTRACTION: bool = True
    AI_ENABLE_AUTO_MAPPING: bool = True
    AI_ENABLE_DATA_QUALITY_CHECK: bool = True

    # AI Parameters
    AI_CONFIDENCE_THRESHOLD: float = 0.8
    AI_MAX_RETRIES: int = 3
    AI_TIMEOUT_SECONDS: int = 60
    AI_TEMPERATURE: float = 0.1
    AI_MAX_TOKENS: int = 4000

    # Email (Optional)
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    def load_ai_config(self) -> dict:
        """Load AI configuration from YAML file"""
        config_path = Path(__file__).parent.parent.parent.parent / "config" / "ai_settings.yaml"

        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)

        return {}


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


settings = get_settings()
