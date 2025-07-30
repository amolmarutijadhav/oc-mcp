"""
LLM provider interface for the OpenShift MCP Server.

This module defines the abstract interface for LLM provider implementations.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class LLMProviderType(Enum):
    """Supported LLM provider types."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"
    CUSTOM = "custom"


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


@dataclass
class ToolCall:
    """Represents a tool call from the LLM."""
    name: str
    arguments: Dict[str, Any]
    call_id: Optional[str] = None


class ILLMProvider(ABC):
    """
    Abstract interface for LLM providers.
    
    This interface defines the contract for LLM provider implementations
    that can be used by the MCP server to generate responses.
    """
    
    @abstractmethod
    def get_provider_type(self) -> LLMProviderType:
        """
        Get the type of this LLM provider.
        
        Returns:
            The provider type
        """
        pass
    
    @abstractmethod
    async def generate_response(self, request: LLMRequest) -> LLMResponse:
        """
        Generate a response from the LLM.
        
        Args:
            request: The LLM request
            
        Returns:
            The LLM response
        """
        pass
    
    @abstractmethod
    async def generate_tool_response(self, request: LLMRequest, 
                                   tool_results: List[Dict[str, Any]]) -> LLMResponse:
        """
        Generate a response with tool results.
        
        Args:
            request: The original LLM request
            tool_results: Results from tool executions
            
        Returns:
            The LLM response with tool results
        """
        pass
    
    @abstractmethod
    def convert_mcp_tools_to_native(self, mcp_tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Convert MCP tools to the native format for this LLM provider.
        
        Args:
            mcp_tools: List of MCP tool definitions
            
        Returns:
            List of tools in native format
        """
        pass
    
    @abstractmethod
    def extract_tool_calls(self, response: LLMResponse) -> List[ToolCall]:
        """
        Extract tool calls from an LLM response.
        
        Args:
            response: The LLM response
            
        Returns:
            List of tool calls
        """
        pass
    
    @abstractmethod
    async def is_available(self) -> bool:
        """
        Check if the LLM provider is available.
        
        Returns:
            True if available, False otherwise
        """
        pass
    
    @abstractmethod
    async def close(self) -> None:
        """
        Close the LLM provider connection.
        """
        pass 