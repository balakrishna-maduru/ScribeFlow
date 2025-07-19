"""Database models for ScribeFlow."""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    JSON,
    Enum as SQLEnum,
    func,
)
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class TimestampMixin:
    """Mixin for timestamp fields."""
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)


class DocumentStatus(enum.Enum):
    """Document status enumeration."""
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class AIProvider(enum.Enum):
    """AI provider enumeration."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    COHERE = "cohere"


class User(Base, TimestampMixin):
    """User model."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(50), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    
    # Profile information
    avatar_url = Column(String(255), nullable=True)
    bio = Column(Text, nullable=True)
    location = Column(String(100), nullable=True)
    website = Column(String(255), nullable=True)
    
    # Preferences
    preferred_ai_provider = Column(SQLEnum(AIProvider), default=AIProvider.OPENAI)
    preferred_model = Column(String(100), default="gpt-4")
    
    # OAuth information
    github_id = Column(String(50), nullable=True, unique=True)
    google_id = Column(String(50), nullable=True, unique=True)
    
    # Relationships
    documents = relationship("Document", back_populates="owner")
    ai_sessions = relationship("AISession", back_populates="user")


class Document(Base, TimestampMixin):
    """Document model."""
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=True)
    status = Column(SQLEnum(DocumentStatus), default=DocumentStatus.DRAFT)
    
    # Metadata
    description = Column(Text, nullable=True)
    tags = Column(JSON, default=list)  # List of strings
    word_count = Column(Integer, default=0)
    
    # Ownership
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Publishing
    published_at = Column(DateTime, nullable=True)
    published_url = Column(String(255), nullable=True)
    
    # File information
    file_path = Column(String(255), nullable=True)
    file_type = Column(String(50), nullable=True)
    file_size = Column(Integer, nullable=True)
    
    # Relationships
    owner = relationship("User", back_populates="documents")
    ai_sessions = relationship("AISession", back_populates="document")
    code_blocks = relationship("CodeBlock", back_populates="document")


class AISession(Base, TimestampMixin):
    """AI interaction session model."""
    __tablename__ = "ai_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), unique=True, index=True, nullable=False)
    
    # AI Configuration
    provider = Column(SQLEnum(AIProvider), nullable=False)
    model = Column(String(100), nullable=False)
    temperature = Column(String(10), default="0.7")
    max_tokens = Column(Integer, default=4000)
    
    # Session data
    messages = Column(JSON, default=list)  # Conversation history
    context = Column(Text, nullable=True)  # Document context
    
    # Relationships
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=True)
    
    user = relationship("User", back_populates="ai_sessions")
    document = relationship("Document", back_populates="ai_sessions")


class CodeBlock(Base, TimestampMixin):
    """Code block model for executable code snippets."""
    __tablename__ = "code_blocks"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=True)
    language = Column(String(50), nullable=False)
    code = Column(Text, nullable=False)
    
    # Execution metadata
    is_executable = Column(Boolean, default=False)
    last_executed_at = Column(DateTime, nullable=True)
    execution_output = Column(Text, nullable=True)
    execution_error = Column(Text, nullable=True)
    
    # Relationships
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    document = relationship("Document", back_populates="code_blocks")


class Template(Base, TimestampMixin):
    """Document template model."""
    __tablename__ = "templates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    content = Column(Text, nullable=False)
    
    # Template metadata
    category = Column(String(100), nullable=True)
    tags = Column(JSON, default=list)
    is_public = Column(Boolean, default=False)
    
    # Usage statistics
    usage_count = Column(Integer, default=0)
    
    # Ownership
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_by = relationship("User")


class APIKey(Base, TimestampMixin):
    """User API keys for external services."""
    __tablename__ = "api_keys"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    provider = Column(SQLEnum(AIProvider), nullable=False)
    key_hash = Column(String(255), nullable=False)  # Encrypted API key
    is_active = Column(Boolean, default=True)
    
    # Usage tracking
    last_used_at = Column(DateTime, nullable=True)
    usage_count = Column(Integer, default=0)
    
    # Relationships
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User")


class AuditLog(Base, TimestampMixin):
    """Audit log for tracking user actions."""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    action = Column(String(100), nullable=False)
    resource_type = Column(String(50), nullable=False)
    resource_id = Column(String(100), nullable=True)
    details = Column(JSON, nullable=True)
    
    # User information
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    user_email = Column(String(255), nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(255), nullable=True)
    
    user = relationship("User")
