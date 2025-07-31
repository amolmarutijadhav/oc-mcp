"""
LLM provider interfaces and types.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from enum import Enum


class LLMProviderType(str, Enum):
    """Supported LLM provider types."""
    OPENAI = "openai"
    AZURE_OPENAI = "azure_openai"
    CUSTOM_OPENAI = "custom_openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    CUSTOM = "custom"


@dataclass
class LLMConfig:
    """Configuration for LLM providers."""
    provider_type: LLMProviderType
    api_key: str
    base_url: Optional[str] = None
    model: str = "gpt-4"
    timeout: int = 30
    temperature: float = 0.7
    max_tokens: int = 1000
    api_version: Optional[str] = None
    deployment_name: Optional[str] = None
    additional_headers: Optional[Dict[str, str]] = None
    custom_config: Optional[Dict[str, Any]] = None


@dataclass
class LLMRequest:
    """Represents an LLM request."""
    prompt: str
    tools: List[Dict[str, Any]]
    context: Optional[Dict[str, Any]] = None
    temperature: float = 0.7
    max_tokens: int = 1000


@dataclass
class LLMResponse:
    """Represents an LLM response."""
    content: str
    tool_calls: List[Dict[str, Any]]
    usage: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class ILLMProvider(ABC):
    """Abstract interface for LLM providers."""
    
    @abstractmethod
    async def generate_response(self, request: LLMRequest) -> LLMResponse:
        """Generate a response from the LLM."""
        pass
    
    @abstractmethod
    async def is_available(self) -> bool:
        """Check if the LLM provider is available."""
        pass
    
    @abstractmethod
    def get_provider_type(self) -> LLMProviderType:
        """Get the provider type."""
        pass
    
    @abstractmethod
    async def close(self) -> None:
        """Close the provider connection."""
        pass


class ILLMProviderFactory(ABC):
    """Abstract factory for creating LLM providers."""
    
    @abstractmethod
    def create_provider(self, config: LLMConfig) -> ILLMProvider:
        """Create an LLM provider instance."""
        pass
    
    @abstractmethod
    def get_supported_providers(self) -> List[LLMProviderType]:
        """Get list of supported provider types."""
        pass 