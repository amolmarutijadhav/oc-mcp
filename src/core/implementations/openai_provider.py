"""
OpenAI provider implementation for the OpenShift MCP Server.

This module implements the OpenAI LLM provider using the OpenAI Python client.
"""

import asyncio
import json
from typing import List, Dict, Any, Optional
import structlog
from openai import OpenAI
from openai.types.chat import ChatCompletion

from ..interfaces.llm import (
    ILLMProvider, 
    LLMProviderType, 
    LLMRequest, 
    LLMResponse, 
    ToolCall
)


logger = structlog.get_logger(__name__)


class OpenAIProvider(ILLMProvider):
    """
    OpenAI provider implementation using OpenAI Python client.
    
    This implementation provides:
    - OpenAI API integration
    - Tool calling support
    - Async operations
    - Error handling
    """
    
    def __init__(self, api_key: str, model: str = "gpt-4", timeout: int = 30):
        """
        Initialize the OpenAI provider.
        
        Args:
            api_key: OpenAI API key
            model: OpenAI model to use
            timeout: Request timeout in seconds
        """
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.client = OpenAI(api_key=api_key)
        
        logger.info("OpenAI provider initialized", model=model, timeout=timeout)
    
    def get_provider_type(self) -> LLMProviderType:
        """
        Get the type of this LLM provider.
        
        Returns:
            The provider type
        """
        return LLMProviderType.OPENAI
    
    async def generate_response(self, request: LLMRequest) -> LLMResponse:
        """
        Generate a response from the LLM.
        
        Args:
            request: The LLM request
            
        Returns:
            The LLM response
        """
        try:
            # Convert MCP tools to OpenAI format
            openai_tools = self.convert_mcp_tools_to_native(request.tools)
            
            # Prepare messages
            messages = [
                {"role": "system", "content": self._get_system_prompt()},
                {"role": "user", "content": request.prompt}
            ]
            
            # Make API call
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                self._make_openai_call,
                messages,
                openai_tools,
                request.temperature,
                request.max_tokens
            )
            
            # Parse response
            return self._parse_openai_response(response)
            
        except Exception as e:
            logger.error("Failed to generate OpenAI response", error=str(e))
            raise OpenAIError(f"Failed to generate response: {e}")
    
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
        try:
            # Prepare messages with tool results
            messages = [
                {"role": "system", "content": self._get_system_prompt()},
                {"role": "user", "content": request.prompt}
            ]
            
            # Add tool results to messages
            for result in tool_results:
                messages.append({
                    "role": "tool",
                    "tool_call_id": result["call_id"],
                    "content": result["result"]
                })
            
            # Make API call without tools (since we already have results)
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                self._make_openai_call,
                messages,
                [],  # No tools needed for follow-up
                request.temperature,
                request.max_tokens
            )
            
            # Parse response
            return self._parse_openai_response(response)
            
        except Exception as e:
            logger.error("Failed to generate OpenAI tool response", error=str(e))
            raise OpenAIError(f"Failed to generate tool response: {e}")
    
    def convert_mcp_tools_to_native(self, mcp_tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Convert MCP tools to OpenAI format.
        
        Args:
            mcp_tools: List of MCP tool definitions
            
        Returns:
            List of tools in OpenAI format
        """
        openai_tools = []
        
        for tool in mcp_tools:
            openai_tool = {
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool.get("description", ""),
                    "parameters": tool.get("input_schema", {})
                }
            }
            openai_tools.append(openai_tool)
        
        logger.debug("Converted MCP tools to OpenAI format", count=len(openai_tools))
        return openai_tools
    
    def extract_tool_calls(self, response: LLMResponse) -> List[ToolCall]:
        """
        Extract tool calls from an LLM response.
        
        Args:
            response: The LLM response
            
        Returns:
            List of tool calls
        """
        tool_calls = []
        
        for call in response.tool_calls:
            try:
                # Parse function arguments
                if isinstance(call["function"]["arguments"], str):
                    arguments = json.loads(call["function"]["arguments"])
                else:
                    arguments = call["function"]["arguments"]
                
                tool_call = ToolCall(
                    name=call["function"]["name"],
                    arguments=arguments,
                    call_id=call.get("id")
                )
                tool_calls.append(tool_call)
                
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning("Failed to parse tool call", error=str(e), call=call)
                continue
        
        logger.debug("Extracted tool calls", count=len(tool_calls))
        return tool_calls
    
    async def is_available(self) -> bool:
        """
        Check if the LLM provider is available.
        
        Returns:
            True if available, False otherwise
        """
        try:
            # Make a simple test call
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                self._make_openai_call,
                [{"role": "user", "content": "Hello"}],
                [],
                0.7,
                10
            )
            
            return response is not None
            
        except Exception as e:
            logger.warning("OpenAI provider not available", error=str(e))
            return False
    
    async def close(self) -> None:
        """
        Close the LLM provider connection.
        """
        # OpenAI client doesn't need explicit closing
        logger.info("OpenAI provider closed")
    
    def _make_openai_call(self, messages: List[Dict[str, str]], 
                         tools: List[Dict[str, Any]], 
                         temperature: float, 
                         max_tokens: int) -> ChatCompletion:
        """
        Make a call to the OpenAI API.
        
        Args:
            messages: List of messages
            tools: List of tools
            temperature: Temperature setting
            max_tokens: Maximum tokens
            
        Returns:
            OpenAI API response
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=tools if tools else None,
                tool_choice="auto" if tools else None,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=self.timeout
            )
            
            return response
            
        except Exception as e:
            logger.error("OpenAI API call failed", error=str(e))
            raise OpenAIError(f"OpenAI API call failed: {e}")
    
    def _parse_openai_response(self, response: ChatCompletion) -> LLMResponse:
        """
        Parse OpenAI API response.
        
        Args:
            response: OpenAI API response
            
        Returns:
            Parsed LLM response
        """
        try:
            message = response.choices[0].message
            
            # Extract content
            content = message.content or ""
            
            # Extract tool calls
            tool_calls = []
            if message.tool_calls:
                for tool_call in message.tool_calls:
                    tool_calls.append({
                        "id": tool_call.id,
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
            
            # Extract metadata
            metadata = {
                "model": response.model,
                "finish_reason": response.choices[0].finish_reason
            }
            
            return LLMResponse(
                content=content,
                tool_calls=tool_calls,
                usage=usage,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error("Failed to parse OpenAI response", error=str(e))
            raise OpenAIError(f"Failed to parse response: {e}")
    
    def _get_system_prompt(self) -> str:
        """
        Get the system prompt for OpenAI.
        
        Returns:
            System prompt string
        """
        return """You are an OpenShift expert assistant. You have access to OpenShift cluster 
        through MCP tools. Use these tools to help users with their OpenShift queries.
        
        Available tools:
        - query_openshift: General OpenShift queries
        - get_pod_status: Get specific pod status
        - list_projects: List available projects
        - get_pod_logs: Get logs from a pod
        - list_services: List services in a namespace
        
        Always use the appropriate tool for queries and provide helpful explanations.
        Be concise but informative in your responses.
        """


class OpenAIError(Exception):
    """Exception for OpenAI provider errors."""
    pass 