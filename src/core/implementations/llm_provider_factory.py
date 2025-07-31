"""
LLM Provider Factory implementation.

This module provides a factory pattern for creating different LLM providers
based on configuration, supporting multiple provider types and custom URLs.
"""

from typing import List
import structlog
from ..interfaces.llm import (
    ILLMProvider, 
    ILLMProviderFactory, 
    LLMProviderType, 
    LLMConfig
)
from .openai_provider import OpenAIProvider, CustomOpenAIProvider

logger = structlog.get_logger(__name__)


class LLMProviderFactory(ILLMProviderFactory):
    """Factory for creating LLM provider instances."""
    
    def create_provider(self, config: LLMConfig) -> ILLMProvider:
        """Create an LLM provider instance based on configuration."""
        
        logger.info(
            "Creating LLM provider",
            provider_type=config.provider_type.value,
            base_url=config.base_url
        )
        
        if config.provider_type == LLMProviderType.OPENAI:
            return OpenAIProvider(config)
        
        elif config.provider_type == LLMProviderType.AZURE_OPENAI:
            return OpenAIProvider(config)
        
        elif config.provider_type == LLMProviderType.CUSTOM_OPENAI:
            return CustomOpenAIProvider(config)
        
        elif config.provider_type == LLMProviderType.ANTHROPIC:
            # TODO: Implement Anthropic provider
            raise NotImplementedError("Anthropic provider not yet implemented")
        
        elif config.provider_type == LLMProviderType.GOOGLE:
            # TODO: Implement Google provider
            raise NotImplementedError("Google provider not yet implemented")
        
        elif config.provider_type == LLMProviderType.CUSTOM:
            # TODO: Implement generic custom provider
            raise NotImplementedError("Custom provider not yet implemented")
        
        else:
            raise ValueError(f"Unsupported provider type: {config.provider_type}")
    
    def get_supported_providers(self) -> List[LLMProviderType]:
        """Get list of supported provider types."""
        return [
            LLMProviderType.OPENAI,
            LLMProviderType.AZURE_OPENAI,
            LLMProviderType.CUSTOM_OPENAI,
            # LLMProviderType.ANTHROPIC,  # TODO: Add when implemented
            # LLMProviderType.GOOGLE,     # TODO: Add when implemented
            # LLMProviderType.CUSTOM,     # TODO: Add when implemented
        ]


def create_llm_provider_from_settings(settings) -> ILLMProvider:
    """Convenience function to create LLM provider from settings."""
    
    # Determine provider type
    provider_type_str = settings.llm_provider_type.lower()
    
    if provider_type_str == "openai":
        provider_type = LLMProviderType.OPENAI
    elif provider_type_str == "azure_openai":
        provider_type = LLMProviderType.AZURE_OPENAI
    elif provider_type_str == "custom_openai":
        provider_type = LLMProviderType.CUSTOM_OPENAI
    elif provider_type_str == "anthropic":
        provider_type = LLMProviderType.ANTHROPIC
    elif provider_type_str == "google":
        provider_type = LLMProviderType.GOOGLE
    elif provider_type_str == "custom":
        provider_type = LLMProviderType.CUSTOM
    else:
        raise ValueError(f"Unsupported provider type: {provider_type_str}")
    
    # Create configuration
    config = LLMConfig(
        provider_type=provider_type,
        api_key=settings.openai_api_key,
        base_url=settings.llm_base_url,
        model=settings.openai_model,
        timeout=settings.openai_timeout,
        temperature=settings.openai_temperature,
        max_tokens=settings.openai_max_tokens,
        api_version=settings.llm_api_version,
        deployment_name=settings.llm_deployment_name
    )
    
    # Create factory and provider
    factory = LLMProviderFactory()
    return factory.create_provider(config) 