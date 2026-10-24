"""
Configuration management using Pydantic Settings.
Compatible with SQLite by default, easily swappable with PostgreSQL.
"""

from pathlib import Path
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "AI-Based Smart City Complaint Management System"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"

    # Base Directories
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    UPLOAD_DIR: Path = DATA_DIR / "uploads"
    KNOWLEDGE_BASE_DIR: Path = BASE_DIR.parent / "data" / "knowledge_base"
    INDEX_DIR: Path = BASE_DIR / "app" / "data" / "index"

    # Database: SQLite default, PostgreSQL compatible
    DATABASE_URL: str = f"sqlite:///{(BASE_DIR / 'smart_city.db').as_posix()}"

    # CORS configuration
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]

    # File Upload limits
    MAX_FILE_SIZE_MB: int = 10

    # Assistant/Retrieval parameters
    RETRIEVAL_TOP_K: int = 4
    SIMILARITY_THRESHOLD: float = 0.12

    # Local Open-Source Vision (Ollama + Gemma 3 Vision)
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_VISION_MODEL: str = "gemma3:4b"
    OLLAMA_TIMEOUT_SECONDS: float = 25.0

    # Local Open-Source Speech Recognition (Faster-Whisper)
    WHISPER_MODEL_SIZE: str = "base"
    WHISPER_DEVICE: str = "cpu"
    WHISPER_COMPUTE_TYPE: str = "int8"

    # Generative AI & Gemini API configuration (Optional for assistant)
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-2.5-flash"

    # Authentication & JWT Security
    SECRET_KEY: str = "smart-city-super-secret-jwt-key-2026-academic-project"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=[".env", str(Path(__file__).resolve().parent.parent.parent / ".env"), str(Path(__file__).resolve().parent.parent.parent.parent / ".env")],
        extra="ignore"
    )


settings = Settings()

# Ensure required runtime directories exist
settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
settings.INDEX_DIR.mkdir(parents=True, exist_ok=True)
