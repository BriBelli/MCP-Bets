"""
Configuration Module for MCP Bets

Manages all application settings, environment variables, and configuration.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # ========================================================================
    # Application Settings
    # ========================================================================
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    DEBUG: bool = Field(default=True, env="DEBUG")
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    API_VERSION: str = Field(default="v1", env="API_VERSION")
    
    # ========================================================================
    # LLM API Keys
    # ========================================================================
    OPENAI_API_KEY: str = Field(..., env="OPENAI_API_KEY")
    ANTHROPIC_API_KEY: str = Field(..., env="ANTHROPIC_API_KEY")
    GEMINI_API_KEY: str = Field(..., env="GEMINI_API_KEY")
    
    # ========================================================================
    # SportsDataIO API
    # ========================================================================
    SPORTSDATAIO_API_KEY: str = Field(..., env="SPORTSDATAIO_API_KEY")
    SPORTSDATAIO_BASE_URL: str = Field(
        default="https://api.sportsdata.io/v3/nfl",
        env="SPORTSDATAIO_BASE_URL"
    )
    SPORTSDATAIO_REQUESTS_PER_SECOND: int = Field(default=2, env="SPORTSDATAIO_REQUESTS_PER_SECOND")
    SPORTSDATAIO_REQUESTS_PER_MONTH: int = Field(default=10000, env="SPORTSDATAIO_REQUESTS_PER_MONTH")
    SPORTSDATAIO_BURST_SIZE: int = Field(default=5, env="SPORTSDATAIO_BURST_SIZE")
    
    # ========================================================================
    # Database Configuration
    # ========================================================================
    DATABASE_URL: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/mcp_bets",
        env="DATABASE_URL"
    )
    DB_HOST: str = Field(default="localhost", env="DB_HOST")
    DB_PORT: int = Field(default=5432, env="DB_PORT")
    DB_NAME: str = Field(default="mcp_bets", env="DB_NAME")
    DB_USER: str = Field(default="postgres", env="DB_USER")
    DB_PASSWORD: str = Field(default="postgres", env="DB_PASSWORD")
    DB_POOL_SIZE: int = Field(default=20, env="DB_POOL_SIZE")
    DB_MAX_OVERFLOW: int = Field(default=10, env="DB_MAX_OVERFLOW")
    
    # ========================================================================
    # Redis Configuration
    # ========================================================================
    REDIS_URL: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    REDIS_HOST: str = Field(default="localhost", env="REDIS_HOST")
    REDIS_PORT: int = Field(default=6379, env="REDIS_PORT")
    REDIS_DB: int = Field(default=0, env="REDIS_DB")
    REDIS_PASSWORD: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    
    # ========================================================================
    # Judge System Configuration
    # ========================================================================
    JUDGE_CLAUDE_MODEL: str = Field(default="claude-sonnet-4.5", env="JUDGE_CLAUDE_MODEL")
    JUDGE_GPT_MODEL: str = Field(default="gpt-4o", env="JUDGE_GPT_MODEL")
    JUDGE_GEMINI_MODEL: str = Field(default="gemini-2.5-pro", env="JUDGE_GEMINI_MODEL")
    JUDGE_TEMPERATURE: float = Field(default=0.2, env="JUDGE_TEMPERATURE")
    JUDGE_MAX_TOKENS: int = Field(default=4096, env="JUDGE_MAX_TOKENS")
    
    # ========================================================================
    # RAG System Configuration
    # ========================================================================
    EMBEDDING_MODEL: str = Field(default="text-embedding-3-large", env="EMBEDDING_MODEL")
    EMBEDDING_DIMENSION: int = Field(default=3072, env="EMBEDDING_DIMENSION")
    RAG_RETRIEVAL_TOP_K: int = Field(default=10, env="RAG_RETRIEVAL_TOP_K")
    RAG_CHUNK_SIZE: int = Field(default=800, env="RAG_CHUNK_SIZE")
    RAG_CHUNK_OVERLAP: int = Field(default=100, env="RAG_CHUNK_OVERLAP")
    
    # ========================================================================
    # API Gateway
    # ========================================================================
    API_GATEWAY_SECRET_KEY: str = Field(
        default="your_secret_key_change_this_in_production",
        env="API_GATEWAY_SECRET_KEY"
    )
    API_GATEWAY_ALGORITHM: str = Field(default="HS256", env="API_GATEWAY_ALGORITHM")
    API_GATEWAY_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=60,
        env="API_GATEWAY_ACCESS_TOKEN_EXPIRE_MINUTES"
    )
    
    # ========================================================================
    # Budget & Monitoring
    # ========================================================================
    MONTHLY_API_BUDGET: float = Field(default=500.0, env="MONTHLY_API_BUDGET")
    BUDGET_ALERT_THRESHOLD: float = Field(default=0.80, env="BUDGET_ALERT_THRESHOLD")
    SENTRY_DSN: Optional[str] = Field(default=None, env="SENTRY_DSN")
    SENTRY_ENVIRONMENT: str = Field(default="development", env="SENTRY_ENVIRONMENT")
    
    # ========================================================================
    # AWS Configuration (for production)
    # ========================================================================
    AWS_REGION: str = Field(default="us-east-1", env="AWS_REGION")
    AWS_ACCESS_KEY_ID: Optional[str] = Field(default=None, env="AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY: Optional[str] = Field(default=None, env="AWS_SECRET_ACCESS_KEY")
    S3_BUCKET_NAME: Optional[str] = Field(default="mcp-bets-data", env="S3_BUCKET_NAME")
    
    # ========================================================================
    # CORS Configuration
    # ========================================================================
    CORS_ORIGINS: str = Field(
        default="http://localhost:3000,http://localhost:3001",
        env="CORS_ORIGINS"
    )
    CORS_ALLOW_CREDENTIALS: bool = Field(default=True, env="CORS_ALLOW_CREDENTIALS")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
    
    def get_cors_origins(self) -> list[str]:
        """Parse CORS origins from comma-separated string"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]


# Global settings instance
settings = Settings()
