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
from .interfaces.discovery import IDiscoveryService, NamespaceInfo, ResourceType
from .implementations.mvp_cache import MVPCache
from .implementations.openshift_client import OpenShiftClient
from .implementations.openshift_discovery import OpenShiftDiscoveryService
from .implementations.llm_provider_factory import create_llm_provider_from_settings
from ..config.settings import Settings
from ..config.discovery_config import create_discovery_config_from_env


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
        
        # Initialize discovery service
        discovery_config = create_discovery_config_from_env()
        self.discovery_service = OpenShiftDiscoveryService(self.client, discovery_config)
        
        self.llm_provider = create_llm_provider_from_settings(self.settings)
        
        # MCP server instance
        self.server = Server("openshift-mcp-server")
        self._register_tools()
        
        logger.info("OpenShift MCP Server initialized with discovery service")
    
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
        
        @self.server.call_tool()
        async def discover_namespaces() -> str:
            """Discover accessible namespaces using multiple strategies."""
            try:
                return await self._discover_namespaces()
            except Exception as e:
                return f"Error: {str(e)}"
        
        @self.server.call_tool()
        async def discover_projects() -> str:
            """Discover accessible OpenShift projects."""
            try:
                return await self._discover_projects()
            except Exception as e:
                return f"Error: {str(e)}"
        
        @self.server.call_tool()
        async def discover_resources(namespace: str) -> str:
            """Discover accessible resources in a specific namespace."""
            try:
                return await self._discover_resources(namespace)
            except Exception as e:
                return f"Error: {str(e)}"
        
        @self.server.call_tool()
        async def get_discovery_summary() -> str:
            """Get a summary of discovery results."""
            try:
                return await self._get_discovery_summary()
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
        elif "discover" in query_lower and "resource" in query_lower:
            # Handle resource discovery query
            namespace = "default"
            words = query.split()
            for i, word in enumerate(words):
                if word.lower() == "namespace" and i + 1 < len(words):
                    namespace = words[i + 1]
            result = await self._discover_resources(namespace)
        elif "namespace" in query_lower and ("list" in query_lower or "show" in query_lower or "discover" in query_lower):
            # Handle list namespaces query using discovery service
            result = await self._discover_namespaces()
        elif "project" in query_lower and ("list" in query_lower or "show" in query_lower or "discover" in query_lower):
            # Handle list projects query using discovery service
            result = await self._discover_projects()
        else:
            result = ("I can help you with OpenShift queries. Try asking about:\n"
                     "- Pod status: 'What is the status of pod my-pod?'\n"
                     "- List pods: 'List pods in namespace default'\n"
                     "- Discover namespaces: 'Show me available namespaces' or 'Discover namespaces'\n"
                     "- Discover projects: 'Show me available projects' or 'Discover projects'\n"
                     "- Discover resources: 'Discover resources in namespace default'\n"
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
    
    async def _discover_namespaces(self) -> str:
        """Discover accessible namespaces using the discovery service."""
        try:
            namespaces = await self.discovery_service.discover_namespaces()
            
            if not namespaces:
                return ("❌ No accessible namespaces found.\n\n"
                       "💡 Suggestions:\n"
                       "• Use 'oc projects' to see your accessible projects\n"
                       "• Try querying specific namespaces you know\n"
                       "• Contact your administrator for access\n"
                       "• Check if your token has expired")
            
            result = "📁 Discovered accessible namespaces:\n"
            for ns in namespaces[:10]:  # Limit to first 10
                result += f"  • {ns.name}"
                if ns.display_name and ns.display_name != ns.name:
                    result += f" (Display: {ns.display_name})"
                if ns.description:
                    result += f" - {ns.description}"
                if ns.status:
                    result += f" [{ns.status}]"
                result += "\n"
            
            if len(namespaces) > 10:
                result += f"  ... and {len(namespaces) - 10} more namespaces\n"
            
            result += f"\n💡 Found {len(namespaces)} accessible namespace(s)"
            return result
            
        except Exception as e:
            logger.error("Error discovering namespaces", error=str(e))
            return f"❌ Error discovering namespaces: {str(e)}"
    
    async def _discover_projects(self) -> str:
        """Discover accessible OpenShift projects."""
        try:
            projects = await self.discovery_service.discover_projects()
            
            if not projects:
                return ("❌ No accessible projects found.\n\n"
                       "💡 Suggestions:\n"
                       "• Use 'oc projects' to see your accessible projects\n"
                       "• Try querying specific namespaces you know\n"
                       "• Contact your administrator for access")
            
            result = "📋 Discovered accessible projects:\n"
            for proj in projects[:10]:  # Limit to first 10
                result += f"  • {proj.name}"
                if proj.display_name and proj.display_name != proj.name:
                    result += f" (Display: {proj.display_name})"
                if proj.description:
                    result += f" - {proj.description}"
                if proj.status:
                    result += f" [{proj.status}]"
                result += "\n"
            
            if len(projects) > 10:
                result += f"  ... and {len(projects) - 10} more projects\n"
            
            result += f"\n💡 Found {len(projects)} accessible project(s)"
            return result
            
        except Exception as e:
            logger.error("Error discovering projects", error=str(e))
            return f"❌ Error discovering projects: {str(e)}"
    
    async def _discover_resources(self, namespace: str) -> str:
        """Discover accessible resources in a specific namespace."""
        try:
            # First check if namespace is accessible
            has_access = await self.discovery_service.test_namespace_access(namespace)
            if not has_access:
                return f"❌ No access to namespace '{namespace}'\n\n💡 Try discovering accessible namespaces first."
            
            resources = await self.discovery_service.discover_resources(namespace)
            
            if not resources.accessible_resources:
                return f"📭 No accessible resources found in namespace '{namespace}'"
            
            result = f"🔧 Accessible resources in namespace '{namespace}':\n"
            for resource in resources.accessible_resources:
                result += f"  • {resource.value}\n"
            
            result += f"\n💡 Found {len(resources.accessible_resources)} accessible resource type(s)"
            return result
            
        except Exception as e:
            logger.error("Error discovering resources", error=str(e))
            return f"❌ Error discovering resources in namespace '{namespace}': {str(e)}"
    
    async def _get_discovery_summary(self) -> str:
        """Get a summary of discovery results."""
        try:
            summary = await self.discovery_service.get_discovery_summary()
            
            result = "📊 Discovery Summary:\n\n"
            result += f"📁 Namespaces: {summary['namespaces_found']} found\n"
            result += f"📋 Projects: {summary['projects_found']} found\n"
            
            if summary['accessible_namespaces']:
                result += f"\n📁 Accessible namespaces:\n"
                for ns in summary['accessible_namespaces'][:5]:
                    result += f"  • {ns}\n"
                if len(summary['accessible_namespaces']) > 5:
                    result += f"  ... and {len(summary['accessible_namespaces']) - 5} more\n"
            
            if summary['accessible_projects']:
                result += f"\n📋 Accessible projects:\n"
                for proj in summary['accessible_projects'][:5]:
                    result += f"  • {proj}\n"
                if len(summary['accessible_projects']) > 5:
                    result += f"  ... and {len(summary['accessible_projects']) - 5} more\n"
            
            result += f"\n💾 Cache stats: {summary['cache_stats']['valid_entries']} valid entries"
            return result
            
        except Exception as e:
            logger.error("Error getting discovery summary", error=str(e))
            return f"❌ Error getting discovery summary: {str(e)}"
    
    async def _list_accessible_namespaces(self) -> str:
        """List namespaces the user has access to (legacy method - now uses discovery service)."""
        return await self._discover_namespaces()
    
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
            
            # Start discovery service background tasks
            await self.discovery_service.start_background_tasks()
            
            logger.info("Starting OpenShift MCP Server with discovery service")
            
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
            # Clear discovery service cache
            await self.discovery_service.invalidate_cache()
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