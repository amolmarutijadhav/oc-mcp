"""
Settings configuration for the OpenShift MCP Server.

This module defines the main configuration classes using Pydantic.
"""

from pydantic import BaseSettings, Field
from typing import Optional
from enum import Enum


class LogLevel(str, Enum):
    """Log level enumeration."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class Settings(BaseSettings):
    """
    Main settings configuration for the OpenShift MCP Server.
    
    This class uses Pydantic for validation and environment variable loading.
    """
    
    # OpenShift Configuration
    openshift_token: str = Field(
        env="OPENSHIFT_TOKEN",
        description="OpenShift authentication token"
    )
    openshift_url: str = Field(
        env="OPENSHIFT_URL",
        description="OpenShift cluster URL"
    )
    openshift_timeout: int = Field(
        default=30,
        env="OPENSHIFT_TIMEOUT",
        description="OpenShift API timeout in seconds"
    )
    
    # LLM Configuration
    openai_api_key: str = Field(
        env="OPENAI_API_KEY",
        description="OpenAI API key"
    )
    openai_model: str = Field(
        default="gpt-4",
        env="OPENAI_MODEL",
        description="OpenAI model to use"
    )
    openai_timeout: int = Field(
        default=30,
        env="OPENAI_TIMEOUT",
        description="OpenAI API timeout in seconds"
    )
    openai_temperature: float = Field(
        default=0.7,
        env="OPENAI_TEMPERATURE",
        description="OpenAI temperature setting"
    )
    openai_max_tokens: int = Field(
        default=1000,
        env="OPENAI_MAX_TOKENS",
        description="OpenAI max tokens setting"
    )
    
    # Cache Configuration
    cache_ttl: int = Field(
        default=300,
        env="CACHE_TTL",
        description="Default cache TTL in seconds"
    )
    cache_max_size: int = Field(
        default=1000,
        env="CACHE_MAX_SIZE",
        description="Maximum number of cache entries"
    )
    cache_enable_stale: bool = Field(
        default=True,
        env="CACHE_ENABLE_STALE",
        description="Enable returning stale data while refreshing"
    )
    
    # Server Configuration
    server_timeout: int = Field(
        default=30,
        env="SERVER_TIMEOUT",
        description="Server timeout in seconds"
    )
    server_host: str = Field(
        default="localhost",
        env="SERVER_HOST",
        description="Server host address"
    )
    server_port: int = Field(
        default=8000,
        env="SERVER_PORT",
        description="Server port"
    )
    
    # Logging Configuration
    log_level: LogLevel = Field(
        default=LogLevel.INFO,
        env="LOG_LEVEL",
        description="Logging level"
    )
    log_format: str = Field(
        default="json",
        env="LOG_FORMAT",
        description="Log format (json or text)"
    )
    
    # Background Task Configuration
    background_task_timeout: int = Field(
        default=60,
        env="BACKGROUND_TASK_TIMEOUT",
        description="Background task timeout in seconds"
    )
    background_task_max_concurrent: int = Field(
        default=10,
        env="BACKGROUND_TASK_MAX_CONCURRENT",
        description="Maximum concurrent background tasks"
    )
    
    # Performance Configuration
    query_timeout: int = Field(
        default=5,
        env="QUERY_TIMEOUT",
        description="Query execution timeout in seconds"
    )
    enable_background_refresh: bool = Field(
        default=True,
        env="ENABLE_BACKGROUND_REFRESH",
        description="Enable background cache refresh"
    )
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        
    def get_openai_config(self) -> dict:
        """Get OpenAI configuration as dictionary."""
        return {
            "api_key": self.openai_api_key,
            "model": self.openai_model,
            "timeout": self.openai_timeout,
            "temperature": self.openai_temperature,
            "max_tokens": self.openai_max_tokens
        }
    
    def get_openshift_config(self) -> dict:
        """Get OpenShift configuration as dictionary."""
        return {
            "token": self.openshift_token,
            "url": self.openshift_url,
            "timeout": self.openshift_timeout
        }
    
    def get_cache_config(self) -> dict:
        """Get cache configuration as dictionary."""
        return {
            "ttl": self.cache_ttl,
            "max_size": self.cache_max_size,
            "enable_stale": self.cache_enable_stale
        } 