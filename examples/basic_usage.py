"""
Basic usage example for the OpenShift MCP Server.

This example demonstrates how to use the MCP server with OpenAI integration.
"""

import asyncio
import os
from src.core.mcp_server import OpenShiftMCPServer
from src.config.settings import Settings


async def main():
    """Example usage of the OpenShift MCP Server."""
    
    # Load settings
    settings = Settings()
    
    # Create server instance
    server = OpenShiftMCPServer(settings)
    
    try:
        # Example queries
        queries = [
            "What's the status of myapp pod?",
            "Show me the status of database pod",
            "Get status of web-server pod in production namespace"
        ]
        
        print("OpenShift MCP Server Example")
        print("=" * 40)
        
        for query in queries:
            print(f"\nQuery: {query}")
            print("-" * 20)
            
            # Process query
            result = await server._process_query(query)
            print(f"Result: {result}")
            
            # Wait a bit between queries
            await asyncio.sleep(1)
        
        print("\nExample completed successfully!")
        
    except Exception as e:
        print(f"Error: {e}")
    
    finally:
        await server.stop()


if __name__ == "__main__":
    # Set up environment variables for testing
    os.environ.setdefault("OPENSHIFT_TOKEN", "your-token-here")
    os.environ.setdefault("OPENSHIFT_URL", "https://your-cluster.com")
    os.environ.setdefault("OPENAI_API_KEY", "your-openai-key-here")
    
    asyncio.run(main()) 