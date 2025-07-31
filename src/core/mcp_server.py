"""
Main MCP server implementation for the OpenShift MCP Server.
"""

import asyncio
from typing import Dict, Any, List, Optional
import structlog
from mcp.server import Server, InitializationOptions
from mcp import StdioServerParameters

from .interfaces.cache import ICacheProvider
from .interfaces.client import IOpenShiftClient
from .interfaces.llm import ILLMProvider, LLMRequest
from .implementations.mvp_cache import MVPCache
from .implementations.openshift_client import OpenShiftClient
from .implementations.llm_provider_factory import create_llm_provider_from_settings
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
        
        self.llm_provider = create_llm_provider_from_settings(self.settings)
        
        # MCP server instance
        self.server = Server("openshift-mcp-server")
        self._register_tools()
        
        logger.info("OpenShift MCP Server initialized")
    
    def _register_tools(self):
        """Register MCP tools."""
        
        @self.server.call_tool()
        async def query_openshift(query: str) -> str:
            """Query OpenShift cluster using natural language."""
            try:
                return await self._process_query(query)
            except Exception as e:
                logger.error("Error processing query", error=str(e))
                return f"Error: {str(e)}"
        
        @self.server.call_tool()
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
        
        # Ensure client is authenticated
        if not self.client._connected:
            try:
                authenticated = await self.client.authenticate(
                    self.settings.openshift_token,
                    self.settings.openshift_url
                )
                if not authenticated:
                    return "❌ Failed to authenticate with OpenShift. Please check your credentials."
            except Exception as e:
                return f"❌ Authentication error: {str(e)}"
        
        # Simple query processing for MVP
        query_lower = query.lower()
        
        if "pod" in query_lower and "status" in query_lower:
            # Extract pod name from query (simple approach)
            words = query.split()
            pod_name = None
            namespace = "default"  # Default namespace
            
            for i, word in enumerate(words):
                if word.lower() in ["pod", "pods"] and i + 1 < len(words):
                    pod_name = words[i + 1]
                    break
                elif word.lower() == "namespace" and i + 1 < len(words):
                    namespace = words[i + 1]
            
            if pod_name:
                result = await self._get_pod_status(pod_name, namespace)
            else:
                result = "Please specify a pod name. You can also specify a namespace like 'pod my-pod in namespace my-namespace'"
        elif "list" in query_lower and "pod" in query_lower:
            # Handle list pods query
            namespace = "default"
            words = query.split()
            for i, word in enumerate(words):
                if word.lower() == "namespace" and i + 1 < len(words):
                    namespace = words[i + 1]
            
            result = await self._list_pods_in_namespace(namespace)
        elif "namespace" in query_lower and ("list" in query_lower or "show" in query_lower):
            # Handle list namespaces query
            result = await self._list_accessible_namespaces()
        else:
            result = ("I can help you with OpenShift queries. Try asking about:\n"
                     "- Pod status: 'What is the status of pod my-pod?'\n"
                     "- List pods: 'List pods in namespace default'\n"
                     "- List namespaces: 'Show me available namespaces'\n"
                     "Note: I can only access resources you have permission to view.")
        
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
    
    async def _list_pods_in_namespace(self, namespace: str) -> str:
        """List pods in a specific namespace with permission handling."""
        try:
            pods = await self.client.list_pods(namespace)
            if not pods:
                return f"No pods found in namespace '{namespace}'"
            
            result = f"📦 Pods in namespace '{namespace}':\n"
            for pod in pods:
                status_emoji = "✅" if pod.ready else "⚠️" if pod.status == "Pending" else "❌"
                result += f"{status_emoji} {pod.name} - {pod.status} ({pod.age})\n"
            
            return result
            
        except Exception as e:
            if "403" in str(e) or "Forbidden" in str(e) or "Permission denied" in str(e):
                return f"❌ Permission denied: You don't have access to list pods in namespace '{namespace}'"
            elif "404" in str(e) or "not found" in str(e).lower():
                return f"❌ Namespace '{namespace}' not found"
            else:
                return f"❌ Error listing pods in namespace '{namespace}': {str(e)}"
    
    async def _list_accessible_namespaces(self) -> str:
        """List namespaces the user has access to."""
        try:
            namespaces = await self.client.list_namespaces()
            if not namespaces:
                return "No namespaces found or you don't have permission to list namespaces."
            
            result = "📁 Available namespaces:\n"
            for ns in namespaces[:10]:  # Limit to first 10
                result += f"  - {ns}\n"
            
            if len(namespaces) > 10:
                result += f"  ... and {len(namespaces) - 10} more\n"
            
            return result
            
        except Exception as e:
            if "403" in str(e) or "Forbidden" in str(e) or "Permission denied" in str(e):
                return ("❌ Permission denied: You don't have permission to list namespaces.\n"
                       "You can still query specific namespaces you have access to, like 'default'.")
            else:
                return f"❌ Error listing namespaces: {str(e)}"
    
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
            
            # Start the server using stdio
            import sys
            from mcp import StdioServerParameters
            
            params = StdioServerParameters(
                command=["python", "-m", "src.core.mcp_server"],
                read_stream=sys.stdin.buffer,
                write_stream=sys.stdout.buffer
            )
            
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