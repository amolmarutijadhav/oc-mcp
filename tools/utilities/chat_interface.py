#!/usr/bin/env python3
"""
Simple chat interface for OpenShift MCP Server.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.config.settings import Settings
from src.core.implementations.mvp_cache import MVPCache
from src.core.implementations.openshift_client import OpenShiftClient
from src.core.implementations.openai_provider import OpenAIProvider
import structlog

logger = structlog.get_logger(__name__)


async def chat_interface():
    """Simple chat interface for interacting with the MCP server."""
    print("🤖 OpenShift MCP Server Chat Interface")
    print("=" * 50)
    print("Type your questions about OpenShift, or 'quit' to exit")
    print("Examples:")
    print("- 'What pods are running in default namespace?'")
    print("- 'Show me the status of pod myapp'")
    print("- 'List all namespaces I have access to'")
    print("- 'quit' to exit")
    print("=" * 50)
    
    try:
        # Initialize components
        settings = Settings()
        
        cache = MVPCache(
            max_size=settings.cache_max_size,
            default_ttl=settings.cache_ttl
        )
        
        client = OpenShiftClient(
            token=settings.openshift_token,
            url=settings.openshift_url,
            timeout=settings.openshift_timeout
        )
        
        llm_provider = OpenAIProvider(
            api_key=settings.openai_api_key,
            model=settings.openai_model,
            timeout=settings.openai_timeout
        )
        
        print("✅ Server initialized successfully")
        print("🔗 Connecting to OpenShift...")
        
        # Test connection
        authenticated = await client.authenticate(
            settings.openshift_token,
            settings.openshift_url
        )
        
        if authenticated:
            print("✅ Connected to OpenShift successfully!")
        else:
            print("⚠️ OpenShift connection failed, but you can still try queries")
        
        print("\n💬 Start chatting:")
        
        while True:
            try:
                # Get user input
                user_input = input("\n🤔 You: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    break
                
                if not user_input:
                    continue
                
                # Process query
                print("🤖 Processing...")
                response = await _process_query(user_input, client, cache, settings)
                print(f"🤖 Assistant: {response}")
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
    
    except Exception as e:
        print(f"❌ Failed to initialize server: {e}")
        print("Please check your .env file and OpenShift credentials")


async def _process_query(query: str, client, cache, settings) -> str:
    """Process a natural language query."""
    # Check cache first
    cache_key = f"query:{query}"
    cached_result = await cache.get(cache_key)
    if cached_result:
        return cached_result
    
    # Ensure client is authenticated
    if not client._connected:
        try:
            authenticated = await client.authenticate(
                settings.openshift_token,
                settings.openshift_url
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
            result = await _get_pod_status(client, pod_name, namespace)
        else:
            result = "Please specify a pod name. You can also specify a namespace like 'pod my-pod in namespace my-namespace'"
    elif "list" in query_lower and "pod" in query_lower:
        # Handle list pods query
        namespace = "default"
        words = query.split()
        for i, word in enumerate(words):
            if word.lower() == "namespace" and i + 1 < len(words):
                namespace = words[i + 1]
        
        result = await _list_pods_in_namespace(client, namespace)
    elif "namespace" in query_lower and ("list" in query_lower or "show" in query_lower):
        # Handle list namespaces query
        result = await _list_accessible_namespaces(client)
    else:
        result = ("I can help you with OpenShift queries. Try asking about:\n"
                 "- Pod status: 'What is the status of pod my-pod?'\n"
                 "- List pods: 'List pods in namespace default'\n"
                 "- List namespaces: 'Show me available namespaces'\n"
                 "Note: I can only access resources you have permission to view.")
    
    # Cache result
    await cache.set(cache_key, result, settings.cache_ttl)
    return result


async def _get_pod_status(client, pod_name: str, namespace: str = "default") -> str:
    """Get status of a specific pod."""
    try:
        pod = await client.get_pod_status(pod_name, namespace)
        if not pod:
            return f"❌ Pod '{pod_name}' not found in namespace '{namespace}'"
        
        status_emoji = "✅" if pod.ready else "⚠️" if pod.status == "Pending" else "❌"
        return f"{status_emoji} Pod: {pod.name}\nStatus: {pod.status}\nAge: {pod.age}\nReady: {pod.ready}"
        
    except Exception as e:
        if "403" in str(e) or "Forbidden" in str(e) or "Permission denied" in str(e):
            return f"❌ Permission denied: You don't have access to pod '{pod_name}' in namespace '{namespace}'"
        elif "404" in str(e) or "not found" in str(e).lower():
            return f"❌ Pod '{pod_name}' not found in namespace '{namespace}'"
        else:
            return f"❌ Error getting pod status: {str(e)}"


async def _list_pods_in_namespace(client, namespace: str) -> str:
    """List pods in a specific namespace with permission handling."""
    try:
        pods = await client.list_pods(namespace)
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


async def _list_accessible_namespaces(client) -> str:
    """List namespaces the user has access to."""
    try:
        namespaces = await client.list_namespaces()
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


if __name__ == "__main__":
    asyncio.run(chat_interface()) 