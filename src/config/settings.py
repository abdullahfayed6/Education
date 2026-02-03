"""
Enhanced Configuration Management

Centralized configuration with:
- Environment variable validation
- Type safety with Pydantic
- Support for dev/staging/prod environments
- Secrets management
- Azure Cosmos DB configuration
"""

from __future__ import annotations

import os
from enum import Enum
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(str, Enum):
    """Application environment types."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


class Settings(BaseSettings):
    """Application settings with validation."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # ============================================================
    # Application Settings
    # ============================================================
    app_name: str = "CareerForgeAI"
    app_version: str = "2.0.0"
    environment: Environment = Environment.DEVELOPMENT
    debug: bool = False
    
    # API Settings
    api_v1_prefix: str = "/api/v1"
    allowed_hosts: list[str] = ["*"]
    
    # ============================================================
    # Azure Cosmos DB Configuration
    # ============================================================
    # Cloud Configuration
    cosmos_endpoint: str = Field(
        default="",
        description="Azure Cosmos DB endpoint URL"
    )
    cosmos_key: str = Field(
        default="",
        description="Azure Cosmos DB primary/secondary key"
    )
    cosmos_database_name: str = Field(
        default="careerforge_db",
        description="Database name"
    )
    cosmos_preferred_regions: list[str] = Field(
        default_factory=lambda: ["East US", "West US"],
        description="Preferred regions for multi-region replication"
    )
    
    # Emulator Configuration
    cosmos_use_emulator: bool = Field(
        default=False,
        description="Use local Cosmos DB emulator"
    )
    cosmos_emulator_url: str = "https://localhost:8081"
    cosmos_emulator_key: str = (
        "C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw=="
    )
    
    # Performance Settings
    cosmos_max_retry_attempts: int = 3
    cosmos_latency_threshold_ms: int = 100  # Log if query exceeds this
    
    # Container Names (Following partition key best practices)
    container_users: str = "users"  # Partition key: /userId
    container_sessions: str = "sessions"  # Partition key: /userId (HPK: [/userId, /sessionId])
    container_interviews: str = "interviews"  # Partition key: /userId
    container_profiles: str = "profiles"  # Partition key: /userId
    container_recommendations: str = "recommendations"  # Partition key: /userId
    
    # ============================================================
    # LLM Provider Configuration
    # ============================================================
    llm_provider: str = Field(
        default="openai",
        description="Primary LLM provider: openai, gemini, groq, anthropic, cohere, mistral, ollama"
    )
    llm_model: Optional[str] = Field(
        default=None,
        description="Override default model for provider"
    )
    llm_temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    llm_max_tokens: int = Field(default=2000, ge=1)
    
    # Provider API Keys
    openai_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = Field(
        default=None,
        validation_alias="GOOGLE_API_KEY"
    )
    groq_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    cohere_api_key: Optional[str] = None
    mistral_api_key: Optional[str] = None
    ollama_base_url: str = "http://localhost:11434"
    
    # ============================================================
    # External API Configuration
    # ============================================================
    search_provider: str = Field(
        default="mock",
        description="Search provider: serpapi, tavily, mock"
    )
    search_api_key: Optional[str] = None
    rapidapi_key: Optional[str] = Field(
        default=None,
        description="RapidAPI key for LinkedIn and other APIs"
    )
    
    # Search Settings
    max_results: int = Field(default=20, ge=1, le=100)
    top_k: int = Field(default=5, ge=1, le=20)
    
    # ============================================================
    # Security & Authentication
    # ============================================================
    secret_key: str = Field(
        default="your-secret-key-change-in-production",
        min_length=32
    )
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # CORS Settings
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://localhost:8501"]
    )
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = Field(default_factory=lambda: ["*"])
    cors_allow_headers: list[str] = Field(default_factory=lambda: ["*"])
    
    # Rate Limiting
    rate_limit_enabled: bool = True
    rate_limit_per_minute: int = 60
    
    # ============================================================
    # Logging Configuration
    # ============================================================
    log_level: str = "INFO"
    log_format: str = "json"  # json or text
    log_file: Optional[str] = None  # Path to log file
    
    # ============================================================
    # Feature Flags
    # ============================================================
    enable_metrics: bool = True
    enable_tracing: bool = False
    enable_caching: bool = True
    cache_ttl_seconds: int = 3600
    
    # ============================================================
    # Validators
    # ============================================================
    @field_validator("environment", mode="before")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Validate and normalize environment."""
        if isinstance(v, str):
            return v.lower()
        return v
    
    @field_validator("llm_provider", mode="before")
    @classmethod
    def validate_llm_provider(cls, v: str) -> str:
        """Validate LLM provider."""
        valid_providers = {
            "openai", "gemini", "groq", "anthropic",
            "cohere", "mistral", "ollama"
        }
        if v.lower() not in valid_providers:
            raise ValueError(
                f"Invalid LLM provider: {v}. "
                f"Must be one of: {', '.join(valid_providers)}"
            )
        return v.lower()
    
    @field_validator("cosmos_endpoint")
    @classmethod
    def validate_cosmos_endpoint(cls, v: str, info) -> str:
        """Validate Cosmos DB endpoint if not using emulator."""
        use_emulator = info.data.get("cosmos_use_emulator", False)
        if not use_emulator and not v:
            raise ValueError(
                "cosmos_endpoint is required when not using emulator. "
                "Set COSMOS_USE_EMULATOR=true to use local emulator."
            )
        return v
    
    # ============================================================
    # Helper Methods
    # ============================================================
    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment == Environment.PRODUCTION
    
    @property
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.environment == Environment.DEVELOPMENT
    
    @property
    def is_testing(self) -> bool:
        """Check if running tests."""
        return self.environment == Environment.TESTING
    
    def get_cosmos_connection_string(self) -> str:
        """Get Cosmos DB connection string."""
        if self.cosmos_use_emulator:
            return f"AccountEndpoint={self.cosmos_emulator_url};AccountKey={self.cosmos_emulator_key};"
        return f"AccountEndpoint={self.cosmos_endpoint};AccountKey={self.cosmos_key};"


# Singleton settings instance
settings = Settings()


def get_settings() -> Settings:
    """Dependency injection helper for FastAPI."""
    return settings
