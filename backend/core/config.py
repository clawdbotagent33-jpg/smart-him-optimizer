"""애플리케이션 설정 모듈"""

from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """애플리케이션 설정"""

    # 애플리케이션 기본 설정
    APP_NAME: str = "Smart HIM Optimizer 2026"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # 보안 설정
    SECRET_KEY: str = "change-me-in-production-use-environment-variable"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7일
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # 데이터베이스 설정
    DATABASE_URL: str = (
        "postgresql+asyncpg://him_admin:change_me@localhost:5432/smart_him_db"
    )
    POSTGRES_PASSWORD: Optional[str] = None
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10

    # 비식별화 설정
    ANONYMIZATION_KEY: Optional[str] = None  # AES-256 키 (32 bytes)
    ENABLE_ANONYMIZATION: bool = True

    # RAG 설정
    CHROMA_DB_PATH: str = "./data/chroma"
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50
    TOP_K_RESULTS: int = 5

    # LLM 설정
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    LLM_MODEL: str = "qwen2.5:7b"
    LLM_TEMPERATURE: float = 0.3
    LLM_MAX_TOKENS: int = 2048

    # ML 모델 설정
    ML_MODEL_PATH: str = "./ml/models"
    A_GROUP_THRESHOLD: float = 0.6
    DENIAL_THRESHOLD: float = 0.5

    # 파일 업로드 설정
    MAX_UPLOAD_SIZE: int = 100 * 1024 * 1024  # 100MB
    ALLOWED_EXTENSIONS: set = {".csv", ".xlsx", ".pdf", ".docx", ".txt", ".png", ".jpg"}
    UPLOAD_DIR: str = "./data/uploads"

    # K-DRG 설정
    KDRG_VERSION: str = "v4.7"
    KCD_VERSION: str = "KCD-9"

    # CORS 설정
    CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:8000"]

    # 로깅 설정
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "./logs/app.log"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()


def get_settings() -> Settings:
    """설정 객체 반환"""
    return settings
