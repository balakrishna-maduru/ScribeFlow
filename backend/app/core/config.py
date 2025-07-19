"""Core application configuration."""

from functools import lru_cache
from typing import Any, Dict, List, Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # App Configuration
    app_name: str = "ScribeFlow"
    app_version: str = "1.0.0"
    debug: bool = False
    api_prefix: str = "/api/v1"
    
    # Database Configuration
    database_url: str = "sqlite+aiosqlite:///./scribeflow.db"
    database_echo: bool = False
    
    # Authentication
    secret_key: str = "your-secret-key-change-in-production"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    algorithm: str = "HS256"
    
    # AI Provider Configuration
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    google_ai_api_key: Optional[str] = None
    cohere_api_key: Optional[str] = None
    
    # AI Model Settings
    default_ai_provider: str = "openai"
    default_model: str = "gpt-4"
    max_tokens: int = 4000
    temperature: float = 0.7
    
    # Redis Configuration
    redis_url: str = "redis://localhost:6379"
    redis_db: int = 0
    
    # File Storage
    upload_path: str = "./uploads"
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    allowed_file_types: List[str] = [
        "text/plain",
        "text/markdown",
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ]
    
    # Security
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:5173"]
    cors_allow_credentials: bool = True
    cors_allow_methods: List[str] = ["*"]
    cors_allow_headers: List[str] = ["*"]
    
    # Rate Limiting
    rate_limit_requests: int = 100
    rate_limit_window: int = 60  # seconds
    
    # Monitoring
    sentry_dsn: Optional[str] = None
    log_level: str = "INFO"
    
    # External Services
    github_client_id: Optional[str] = None
    github_client_secret: Optional[str] = None
    google_client_id: Optional[str] = None
    google_client_secret: Optional[str] = None
    
    @field_validator("cors_origins", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Any) -> List[str]:
        """Parse CORS origins from environment variable."""
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, list):
            return v
        elif isinstance(v, str):
            return [v]
        raise ValueError(v)
    
    @field_validator("allowed_file_types", mode="before")
    @classmethod
    def assemble_allowed_file_types(cls, v: Any) -> List[str]:
        """Parse allowed file types from environment variable."""
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, list):
            return v
        elif isinstance(v, str):
            return [v]
        raise ValueError(v)
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()


# Database configuration
def get_database_url() -> str:
    """Get database URL for SQLAlchemy."""
    settings = get_settings()
    return settings.database_url


# AI Provider configuration
def get_ai_config() -> Dict[str, Any]:
    """Get AI provider configuration."""
    settings = get_settings()
    return {
        "openai": {
            "api_key": settings.openai_api_key,
            "models": ["gpt-4", "gpt-3.5-turbo", "gpt-4-turbo-preview"]
        },
        "anthropic": {
            "api_key": settings.anthropic_api_key,
            "models": ["claude-3-opus", "claude-3-sonnet", "claude-3-haiku"]
        },
        "google": {
            "api_key": settings.google_ai_api_key,
            "models": ["gemini-pro", "gemini-pro-vision"]
        },
        "cohere": {
            "api_key": settings.cohere_api_key,
            "models": ["command", "command-nightly"]
        }
    }
