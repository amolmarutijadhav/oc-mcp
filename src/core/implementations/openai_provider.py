"""
OpenAI provider implementation with support for custom URLs and Azure OpenAI.
"""

import asyncio
from typing import Dict, Any, List, Optional
import structlog
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion

from ..interfaces.llm import (
    ILLMProvider, 
    LLMProviderType, 
    LLMRequest, 
    LLMResponse,
    LLMConfig
)

logger = structlog.get_logger(__name__)


class OpenAIProvider(ILLMProvider):
    """OpenAI provider implementation with custom URL support."""
    
    def __init__(self, config: LLMConfig):
        """Initialize the OpenAI provider."""
        self.config = config
        self.provider_type = config.provider_type
        
        # Configure client based on provider type
        if config.provider_type == LLMProviderType.AZURE_OPENAI:
            self._setup_azure_client()
        else:
            self._setup_openai_client()
        
        logger.info(
            "OpenAI provider initialized",
            provider_type=config.provider_type.value,
            model=config.model,
            timeout=config.timeout,
            base_url=config.base_url
        )
    
    def _setup_openai_client(self):
        """Setup standard OpenAI client."""
        client_kwargs = {
            "api_key": self.config.api_key,
            "timeout": self.config.timeout
        }
        
        # Use custom base URL if provided
        if self.config.base_url:
            client_kwargs["base_url"] = self.config.base_url
        
        # Add custom headers if provided
        if self.config.additional_headers:
            client_kwargs["default_headers"] = self.config.additional_headers
        
        self.client = AsyncOpenAI(**client_kwargs)
    
    def _setup_azure_client(self):
        """Setup Azure OpenAI client."""
        if not self.config.api_version:
            raise ValueError("API version is required for Azure OpenAI")
        
        client_kwargs = {
            "api_key": self.config.api_key,
            "api_version": self.config.api_version,
            "timeout": self.config.timeout
        }
        
        # Azure OpenAI requires specific base URL format
        if self.config.base_url:
            client_kwargs["azure_endpoint"] = self.config.base_url
        
        # Add custom headers if provided
        if self.config.additional_headers:
            client_kwargs["default_headers"] = self.config.additional_headers
        
        self.client = AsyncOpenAI(**client_kwargs)
    
    async def generate_response(self, request: LLMRequest) -> LLMResponse:
        """Generate a response from the LLM."""
        try:
            # Prepare messages
            messages = [{"role": "user", "content": request.prompt}]
            
            # Prepare completion parameters
            completion_params = {
                "model": self.config.model,
                "messages": messages,
                "temperature": request.temperature or self.config.temperature,
                "max_tokens": request.max_tokens or self.config.max_tokens
            }
            
            # Add tools if provided
            if request.tools:
                completion_params["tools"] = request.tools
                completion_params["tool_choice"] = "auto"
            
            # Use deployment name for Azure OpenAI
            if self.config.provider_type == LLMProviderType.AZURE_OPENAI and self.config.deployment_name:
                completion_params["model"] = self.config.deployment_name
            
            # Make the API call
            response = await self.client.chat.completions.create(**completion_params)
            
            # Extract response content
            content = response.choices[0].message.content or ""
            
            # Extract tool calls
            tool_calls = []
            if response.choices[0].message.tool_calls:
                for tool_call in response.choices[0].message.tool_calls:
                    tool_calls.append({
                        "id": tool_call.id,
                        "type": tool_call.type,
                        "function": {
                            "name": tool_call.function.name,
                            "arguments": tool_call.function.arguments
                        }
                    })
            
            # Extract usage information
            usage = None
            if response.usage:
                usage = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            
            return LLMResponse(
                content=content,
                tool_calls=tool_calls,
                usage=usage,
                metadata={"model": response.model, "provider": self.provider_type.value}
            )
            
        except Exception as e:
            logger.error("Failed to generate response", error=str(e))
            raise Exception(f"OpenAI API call failed: {str(e)}")
    
    async def is_available(self) -> bool:
        """Check if the LLM provider is available."""
        try:
            # Simple test call
            response = await self.client.chat.completions.create(
                model=self.config.model,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=1
            )
            return True
        except Exception as e:
            logger.warning("LLM provider availability check failed", error=str(e))
            return False
    
    def get_provider_type(self) -> LLMProviderType:
        """Get the provider type."""
        return self.provider_type
    
    async def close(self) -> None:
        """Close the provider connection."""
        try:
            await self.client.close()
        except Exception as e:
            logger.warning("Error closing OpenAI client", error=str(e))


class CustomOpenAIProvider(OpenAIProvider):
    """Custom OpenAI-compatible provider for any API that mimics OpenAI."""
    
    def __init__(self, config: LLMConfig):
        """Initialize custom OpenAI provider."""
        if not config.base_url:
            raise ValueError("Base URL is required for custom OpenAI provider")
        
        # Ensure provider type is set correctly
        config.provider_type = LLMProviderType.CUSTOM_OPENAI
        
        super().__init__(config)
        
        logger.info(
            "Custom OpenAI provider initialized",
            base_url=config.base_url,
            model=config.model
        )
    
    async def generate_response(self, request: LLMRequest) -> LLMResponse:
        """Generate response with custom error handling."""
        try:
            return await super().generate_response(request)
        except Exception as e:
            # Enhanced error handling for custom providers
            error_msg = str(e)
            if "404" in error_msg:
                raise Exception(f"Custom LLM endpoint not found: {self.config.base_url}")
            elif "401" in error_msg:
                raise Exception("Authentication failed for custom LLM provider")
            elif "403" in error_msg:
                raise Exception("Access denied to custom LLM provider")
            else:
                raise Exception(f"Custom LLM provider error: {error_msg}") 