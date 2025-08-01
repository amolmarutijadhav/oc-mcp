"""
Configuration settings for the OpenShift MCP Server.
"""

from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings."""
    
    # OpenShift Configuration
    openshift_token: str = Field(..., env="OPENSHIFT_TOKEN")
    openshift_url: str = Field(..., env="OPENSHIFT_URL")
    openshift_timeout: int = Field(30, env="OPENSHIFT_TIMEOUT")
    
    # OpenAI Configuration
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    openai_model: str = Field("gpt-4", env="OPENAI_MODEL")
    openai_timeout: int = Field(30, env="OPENAI_TIMEOUT")
    openai_temperature: float = Field(0.7, env="OPENAI_TEMPERATURE")
    openai_max_tokens: int = Field(1000, env="OPENAI_MAX_TOKENS")
    
    # LLM Provider Configuration (NEW)
    llm_provider_type: str = Field("openai", env="LLM_PROVIDER_TYPE")  # openai, azure, custom
    llm_base_url: Optional[str] = Field(None, env="LLM_BASE_URL")  # Complete OpenAI API URL (e.g., https://openai-proxy.company.com/v1/chat/completions)
    llm_api_version: Optional[str] = Field(None, env="LLM_API_VERSION")  # API version for Azure
    llm_deployment_name: Optional[str] = Field(None, env="LLM_DEPLOYMENT_NAME")  # Azure deployment name
    llm_additional_headers: Optional[str] = Field(None, env="LLM_ADDITIONAL_HEADERS")  # Custom headers as JSON string
    
    # Cache Configuration
    cache_ttl: int = Field(300, env="CACHE_TTL")
    cache_max_size: int = Field(1000, env="CACHE_MAX_SIZE")
    cache_enable_stale: bool = Field(True, env="CACHE_ENABLE_STALE")
    
    # Server Configuration
    server_timeout: int = Field(30, env="SERVER_TIMEOUT")
    server_host: str = Field("localhost", env="SERVER_HOST")
    server_port: int = Field(8000, env="SERVER_PORT")
    
    # Logging Configuration
    log_level: str = Field("INFO", env="LOG_LEVEL")
    log_format: str = Field("json", env="LOG_FORMAT")
    
    # Background Task Configuration
    background_task_timeout: int = Field(60, env="BACKGROUND_TASK_TIMEOUT")
    background_task_max_concurrent: int = Field(10, env="BACKGROUND_TASK_MAX_CONCURRENT")
    
    # Performance Configuration
    query_timeout: int = Field(5, env="QUERY_TIMEOUT")
    enable_background_refresh: bool = Field(True, env="ENABLE_BACKGROUND_REFRESH")
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False
    } 