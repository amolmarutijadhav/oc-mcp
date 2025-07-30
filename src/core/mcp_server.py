"""
Main MCP server implementation for the OpenShift MCP Server.
"""

import asyncio
from typing import Dict, Any, List, Optional
import structlog
from mcp import Server, StdioServerParameters
from mcp.server import Session
from mcp.server.models import InitializationOptions

from .interfaces.cache import ICacheProvider
from .interfaces.client import IOpenShiftClient
from .interfaces.llm import ILLMProvider, LLMRequest
from .implementations.mvp_cache import MVPCache
from .implementations.openshift_client import OpenShiftClient
from .implementations.openai_provider import OpenAIProvider
from ..config.settings import Settings


logger = structlog.get_logger(__name__)


class OpenShiftMCPServer:
    """Main MCP server for OpenShift integration."""
    
    def __init__(self, settings: Optional[Settings] = None):
        """Initialize the MCP server."""
        self.settings = settings or Settings()
        
        # Initialize components
        self.cache = MVPCache(
            max_size=self.settings.cache_max_size,
            default_ttl=self.settings.cache_ttl
        )
        
        self.client = OpenShiftClient(
            token=self.settings.openshift_token,
            url=self.settings.openshift_url,
            timeout=self.settings.openshift_timeout
        )
        
        self.llm_provider = OpenAIProvider(
            api_key=self.settings.openai_api_key,
            model=self.settings.openai_model,
            timeout=self.settings.openai_timeout
        )
        
        # MCP server instance
        self.server = Server("openshift-mcp-server")
        self._register_tools()
        
        logger.info("OpenShift MCP Server initialized")
    
    def _register_tools(self):
        """Register MCP tools."""
        
        @self.server.tool("query_openshift")
        async def query_openshift(query: str) -> str:
            """Query OpenShift cluster using natural language."""
            try:
                return await self._process_query(query)
            except Exception as e:
                logger.error("Error processing query", error=str(e))
                return f"Error: {str(e)}"
        
        @self.server.tool("get_pod_status")
        async def get_pod_status(pod_name: str, namespace: str = "default") -> str:
            """Get status of a specific pod."""
            try:
                return await self._get_pod_status(pod_name, namespace)
            except Exception as e:
                return f"Error: {str(e)}"
    
    async def _process_query(self, query: str) -> str:
        """Process a natural language query."""
        # Check cache first
        cache_key = f"query:{query}"
        cached_result = await self.cache.get(cache_key)
        if cached_result:
            return cached_result
        
        # Simple query processing for MVP
        if "pod" in query.lower() and "status" in query.lower():
            # Extract pod name from query (simple approach)
            words = query.split()
            pod_name = None
            for i, word in enumerate(words):
                if word.lower() in ["pod", "pods"] and i + 1 < len(words):
                    pod_name = words[i + 1]
                    break
            
            if pod_name:
                result = await self._get_pod_status(pod_name)
            else:
                result = "Please specify a pod name"
        else:
            result = "I can help you with pod status queries. Try asking about a specific pod."
        
        # Cache result
        await self.cache.set(cache_key, result, ttl=300)
        return result
    
    async def _get_pod_status(self, pod_name: str, namespace: str = "default") -> str:
        """Get pod status with caching."""
        cache_key = f"pod_status:{namespace}:{pod_name}"
        
        # Check cache first
        cached_result = await self.cache.get(cache_key)
        if cached_result:
            return cached_result
        
        # Get fresh data
        pod_info = await self.client.get_pod_status(pod_name, namespace)
        
        if not pod_info:
            result = f"Pod '{pod_name}' not found in namespace '{namespace}'"
        else:
            status_emoji = "✅" if pod_info.ready else "⚠️" if pod_info.status == "Pending" else "❌"
            result = f"{status_emoji} **{pod_info.name}** - Status: {pod_info.status}\n"
            result += f"Namespace: {pod_info.namespace}\n"
            result += f"Age: {pod_info.age}\n"
            result += f"Containers: {', '.join(pod_info.containers)}"
        
        # Cache result
        await self.cache.set(cache_key, result, ttl=60)
        return result
    
    async def start(self):
        """Start the MCP server."""
        try:
            # Authenticate with OpenShift
            authenticated = await self.client.authenticate(
                self.settings.openshift_token,
                self.settings.openshift_url
            )
            
            if not authenticated:
                raise Exception("Failed to authenticate with OpenShift")
            
            logger.info("Starting OpenShift MCP Server")
            
            # Start the server
            async with StdioServerParameters() as params:
                await self.server.run(params)
                
        except Exception as e:
            logger.error("Failed to start MCP server", error=str(e))
            raise
    
    async def stop(self):
        """Stop the MCP server."""
        try:
            await self.client.close()
            await self.llm_provider.close()
            logger.info("OpenShift MCP Server stopped")
        except Exception as e:
            logger.error("Error stopping MCP server", error=str(e))


async def main():
    """Main entry point."""
    # Configure logging
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Create and start server
    server = OpenShiftMCPServer()
    
    try:
        await server.start()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal, shutting down")
    except Exception as e:
        logger.error("Server error", error=str(e))
        raise
    finally:
        await server.stop()


if __name__ == "__main__":
    asyncio.run(main()) 