"""Core application configuration."""

from functools import lru_cache
from typing import Any, Dict, List, Optional, Union
import secrets
import os

from pydantic import field_validator, ConfigDict, Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # App Configuration
    app_name: str = "ScribeFlow"
    app_version: str = "1.0.0"
    debug: bool = False
    api_prefix: str = "/api/v1"
    
    # Database Configuration
    database_url: str = "sqlite+aiosqlite:///./scribeflow.db"
    database_echo: bool = False
    
    # Authentication - Use Field with default_factory for proper secret generation
    secret_key: str = Field(default_factory=lambda: os.getenv("SECRET_KEY", secrets.token_urlsafe(32)))
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    algorithm: str = "HS256"
    
    # AI Provider Configuration
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    google_api_key: Optional[str] = Field(default=None, alias="GEMINI_API_KEY")
    gemini_api_key: Optional[str] = None  # Alternative field name
    cohere_api_key: Optional[str] = None
    
    # AI Model Settings
    default_ai_provider: str = "google"
    default_model: str = "gemini-1.5-flash"
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
    cors_allow_methods: List[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
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
    def assemble_cors_origins(cls, v: Union[str, List[str], None]) -> List[str]:
        """Parse CORS origins from environment variable."""
        if v is None:
            return ["http://localhost:3000", "http://localhost:5173"]
        if isinstance(v, str):
            if not v.strip():
                return []
            if v.startswith("[") and v.endswith("]"):
                try:
                    import json
                    return json.loads(v)
                except json.JSONDecodeError:
                    pass
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        elif isinstance(v, list):
            return [str(origin).strip() for origin in v if str(origin).strip()]
        return []
    
    @field_validator("allowed_file_types", mode="before")
    @classmethod
    def assemble_allowed_file_types(cls, v: Union[str, List[str], None]) -> List[str]:
        """Parse allowed file types from environment variable."""
        default_types = [
            "text/plain",
            "text/markdown",
            "application/pdf", 
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ]
        
        if v is None:
            return default_types
        if isinstance(v, str):
            if not v.strip():
                return default_types
            if v.startswith("[") and v.endswith("]"):
                try:
                    import json
                    return json.loads(v)
                except json.JSONDecodeError:
                    pass
            return [file_type.strip() for file_type in v.split(",") if file_type.strip()]
        elif isinstance(v, list):
            return [str(file_type).strip() for file_type in v if str(file_type).strip()]
        return default_types
    
    @field_validator("cors_allow_methods", mode="before")
    @classmethod
    def assemble_cors_methods(cls, v: Union[str, List[str], None]) -> List[str]:
        """Parse CORS methods from environment variable."""
        default_methods = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
        
        if v is None:
            return default_methods
        if isinstance(v, str):
            if v == "*":
                return ["*"]
            if not v.strip():
                return default_methods
            if v.startswith("[") and v.endswith("]"):
                try:
                    import json
                    return json.loads(v)
                except json.JSONDecodeError:
                    pass
            return [method.strip().upper() for method in v.split(",") if method.strip()]
        elif isinstance(v, list):
            return [str(method).strip().upper() for method in v if str(method).strip()]
        return default_methods
    
    @field_validator("secret_key", mode="after")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        """Validate secret key length."""
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        return v
    
    @field_validator("default_ai_provider", mode="after")
    @classmethod
    def validate_ai_provider(cls, v: str) -> str:
        """Validate AI provider is supported."""
        supported_providers = ["openai", "anthropic", "google", "cohere"]
        if v not in supported_providers:
            raise ValueError(f"AI provider must be one of: {supported_providers}")
        return v


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
    # Use gemini_api_key if available, otherwise fall back to google_api_key
    google_key = settings.gemini_api_key or settings.google_api_key
    return {
        "openai": {
            "api_key": settings.openai_api_key,
            "models": ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"]
        },
        "anthropic": {
            "api_key": settings.anthropic_api_key,
            "models": ["claude-3-5-sonnet-20241022", "claude-3-opus-20240229", "claude-3-haiku-20240307"]
        },
        "google": {
            "api_key": google_key,
            "base_url": "https://generativelanguage.googleapis.com/v1beta",
            "models": ["gemini-2.0-flash", "gemini-1.5-pro", "gemini-1.5-flash", "gemini-pro"]
        },
        "cohere": {
            "api_key": settings.cohere_api_key,
            "models": ["command-r-plus", "command-r", "command"]
        }
    }


def get_active_ai_config() -> Dict[str, Any]:
    """Get configuration for the active AI provider."""
    settings = get_settings()
    ai_config = get_ai_config()
    
    if settings.default_ai_provider not in ai_config:
        raise ValueError(f"AI provider '{settings.default_ai_provider}' not configured")
    
    provider_config = ai_config[settings.default_ai_provider]
    if not provider_config.get("api_key"):
        # Don't raise error immediately - allow for runtime configuration
        import warnings
        warnings.warn(f"API key not configured for provider '{settings.default_ai_provider}'")
    
    return {
        "provider": settings.default_ai_provider,
        "api_key": provider_config.get("api_key"),
        "model": settings.default_model,
        "max_tokens": settings.max_tokens,
        "temperature": settings.temperature,
        "available_models": provider_config["models"]
    }


def get_env_variables_info() -> Dict[str, Dict[str, Any]]:
    """Get information about all environment variables."""
    return {
        # Required/Important Variables
        "SECRET_KEY": {
            "required": True,
            "description": "Secret key for JWT tokens and encryption (min 32 chars)",
            "default": "Auto-generated secure random string",
            "example": "your-super-secret-key-here-minimum-32-characters"
        },
        
        # Database
        "DATABASE_URL": {
            "required": False,
            "description": "Database connection URL",
            "default": "sqlite+aiosqlite:///./scribeflow.db",
            "example": "postgresql+asyncpg://user:pass@localhost/scribeflow"
        },
        "DATABASE_ECHO": {
            "required": False,
            "description": "Enable SQL query logging",
            "default": "False",
            "example": "True"
        },
        
        # AI Provider API Keys (at least one required)
        "OPENAI_API_KEY": {
            "required": False,
            "description": "OpenAI API key for GPT models",
            "default": "None",
            "example": "sk-..."
        },
        "ANTHROPIC_API_KEY": {
            "required": False,
            "description": "Anthropic API key for Claude models",
            "default": "None",
            "example": "sk-ant-..."
        },
        "GOOGLE_API_KEY": {
            "required": False,
            "description": "Google AI API key for Gemini models",
            "default": "None",
            "example": "AIza..."
        },
        "COHERE_API_KEY": {
            "required": False,
            "description": "Cohere API key",
            "default": "None",
            "example": "..."
        },
        
        # App Configuration
        "APP_NAME": {
            "required": False,
            "description": "Application name",
            "default": "ScribeFlow",
            "example": "MyScribeFlow"
        },
        "APP_VERSION": {
            "required": False,
            "description": "Application version",
            "default": "1.0.0",
            "example": "2.0.0"
        },
        "DEBUG": {
            "required": False,
            "description": "Enable debug mode",
            "default": "False",
            "example": "True"
        },
        "API_PREFIX": {
            "required": False,
            "description": "API route prefix",
            "default": "/api/v1",
            "example": "/api/v2"
        },
        
        # AI Settings
        "DEFAULT_AI_PROVIDER": {
            "required": False,
            "description": "Default AI provider (openai, anthropic, google, cohere)",
            "default": "openai",
            "example": "anthropic"
        },
        "DEFAULT_MODEL": {
            "required": False,
            "description": "Default AI model name",
            "default": "gpt-4",
            "example": "claude-3-5-sonnet-20241022"
        },
        "MAX_TOKENS": {
            "required": False,
            "description": "Maximum tokens for AI responses",
            "default": "4000",
            "example": "8000"
        },
        "TEMPERATURE": {
            "required": False,
            "description": "AI response creativity (0.0-1.0)",
            "default": "0.7",
            "example": "0.5"
        },
        
        # Authentication
        "ACCESS_TOKEN_EXPIRE_MINUTES": {
            "required": False,
            "description": "JWT access token expiration in minutes",
            "default": "30",
            "example": "60"
        },
        "REFRESH_TOKEN_EXPIRE_DAYS": {
            "required": False,
            "description": "JWT refresh token expiration in days",
            "default": "7",
            "example": "30"
        },
        "ALGORITHM": {
            "required": False,
            "description": "JWT algorithm",
            "default": "HS256",
            "example": "HS256"
        },
        
        # Redis
        "REDIS_URL": {
            "required": False,
            "description": "Redis connection URL",
            "default": "redis://localhost:6379",
            "example": "redis://localhost:6379/1"
        },
        "REDIS_DB": {
            "required": False,
            "description": "Redis database number",
            "default": "0",
            "example": "1"
        },
        
        # File Storage
        "UPLOAD_PATH": {
            "required": False,
            "description": "File upload directory",
            "default": "./uploads",
            "example": "/var/uploads"
        },
        "MAX_FILE_SIZE": {
            "required": False,
            "description": "Maximum file size in bytes",
            "default": "10485760",  # 10MB
            "example": "52428800"  # 50MB
        },
        "ALLOWED_FILE_TYPES": {
            "required": False,
            "description": "Comma-separated list of allowed MIME types",
            "default": "text/plain,text/markdown,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "example": "text/plain,application/pdf"
        },
        
        # Security/CORS
        "CORS_ORIGINS": {
            "required": False,
            "description": "Comma-separated list of allowed CORS origins",
            "default": "http://localhost:3000,http://localhost:5173",
            "example": "https://myapp.com,https://api.myapp.com"
        },
        "CORS_ALLOW_CREDENTIALS": {
            "required": False,
            "description": "Allow credentials in CORS requests",
            "default": "True",
            "example": "False"
        },
        "CORS_ALLOW_METHODS": {
            "required": False,
            "description": "Comma-separated list of allowed HTTP methods",
            "default": "GET,POST,PUT,DELETE,OPTIONS",
            "example": "GET,POST"
        },
        "CORS_ALLOW_HEADERS": {
            "required": False,
            "description": "Comma-separated list of allowed headers",
            "default": "*",
            "example": "Content-Type,Authorization"
        },
        
        # Rate Limiting
        "RATE_LIMIT_REQUESTS": {
            "required": False,
            "description": "Number of requests per rate limit window",
            "default": "100",
            "example": "200"
        },
        "RATE_LIMIT_WINDOW": {
            "required": False,
            "description": "Rate limit window in seconds",
            "default": "60",
            "example": "300"
        },
        
        # Monitoring
        "SENTRY_DSN": {
            "required": False,
            "description": "Sentry DSN for error tracking",
            "default": "None",
            "example": "https://..."
        },
        "LOG_LEVEL": {
            "required": False,
            "description": "Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
            "default": "INFO",
            "example": "DEBUG"
        },
        
        # External OAuth Services
        "GITHUB_CLIENT_ID": {
            "required": False,
            "description": "GitHub OAuth client ID",
            "default": "None",
            "example": "your-github-client-id"
        },
        "GITHUB_CLIENT_SECRET": {
            "required": False,
            "description": "GitHub OAuth client secret",
            "default": "None",
            "example": "your-github-client-secret"
        },
        "GOOGLE_CLIENT_ID": {
            "required": False,
            "description": "Google OAuth client ID",
            "default": "None",
            "example": "your-google-client-id"
        },
        "GOOGLE_CLIENT_SECRET": {
            "required": False,
            "description": "Google OAuth client secret",
            "default": "None",
            "example": "your-google-client-secret"
        }
    }


def get_required_env_vars() -> Dict[str, str]:
    """Get the minimum required environment variables to run the application."""
    return {
        "SECRET_KEY": "Secure secret key for JWT tokens (minimum 32 characters)",
        # At least one AI provider API key is required
        "OPENAI_API_KEY": "OpenAI API key (if using OpenAI as default provider)",
        "ANTHROPIC_API_KEY": "Anthropic API key (if using Anthropic as default provider)", 
        "GOOGLE_API_KEY": "Google AI API key (if using Google as default provider)",
        "COHERE_API_KEY": "Cohere API key (if using Cohere as default provider)"
    }

def get_recommended_env_vars() -> Dict[str, str]:
    """Get recommended environment variables for production deployment."""
    return {
        "DATABASE_URL": "Production database connection string",
        "REDIS_URL": "Redis connection URL for caching",
        "CORS_ORIGINS": "Comma-separated list of allowed frontend origins",
        "SENTRY_DSN": "Sentry DSN for error tracking and monitoring",
        "LOG_LEVEL": "Logging level (INFO for production, DEBUG for development)"
    }

def print_required_env_vars():
    """Print the required environment variables."""
    print("🔴 REQUIRED Environment Variables:")
    print("="*50)
    
    required = get_required_env_vars()
    
    print(f"\n1. {list(required.keys())[0]}")
    print(f"   {required['SECRET_KEY']}")
    print("   Example: export SECRET_KEY='your-super-secure-32-char-minimum-key'")
    
    print(f"\n2. AI Provider API Key (choose one):")
    for key in list(required.keys())[1:]:
        print(f"   - {key}: {required[key]}")
    
    print(f"\n   Examples:")
    print(f"   export OPENAI_API_KEY='sk-...'")
    print(f"   export ANTHROPIC_API_KEY='sk-ant-...'")
    print(f"   export GOOGLE_API_KEY='AIza...'")
    
    print(f"\n🟡 RECOMMENDED for Production:")
    print("="*50)
    recommended = get_recommended_env_vars()
    for key, desc in recommended.items():
        print(f"   {key}: {desc}")

if __name__ == "__main__":
    print_required_env_vars()
