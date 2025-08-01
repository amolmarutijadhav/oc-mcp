"""
Example usage of the OpenShift discovery service.

This example demonstrates how to use the discovery service to find
accessible namespaces, projects, and resources in OpenShift clusters.
"""

import asyncio
import os
from src.core.implementations.openshift_discovery import OpenShiftDiscoveryService
from src.core.implementations.openshift_client import OpenShiftClient
from src.config.discovery_config import DiscoveryConfig, create_discovery_config_from_env


async def main():
    """Example usage of the OpenShift discovery service."""
    
    # Load environment variables
    openshift_token = os.getenv('OPENSHIFT_TOKEN')
    openshift_url = os.getenv('OPENSHIFT_URL')
    
    if not openshift_token or not openshift_url:
        print("❌ Please set OPENSHIFT_TOKEN and OPENSHIFT_URL environment variables")
        return
    
    # Create OpenShift client
    client = OpenShiftClient(token=openshift_token, url=openshift_url)
    
    # Authenticate
    if not await client.authenticate(openshift_token, openshift_url):
        print("❌ Failed to authenticate with OpenShift")
        return
    
    print("✅ OpenShift authentication successful")
    
    # Create discovery configuration
    config = create_discovery_config_from_env()
    print(f"🔧 Discovery config: {len(config.enabled_strategies)} strategies enabled")
    
    # Create discovery service
    discovery_service = OpenShiftDiscoveryService(client, config)
    
    try:
        print("\n🔍 Discovering accessible resources...")
        
        # Discover namespaces
        print("\n📁 Discovering namespaces...")
        namespaces = await discovery_service.discover_namespaces()
        print(f"Found {len(namespaces)} accessible namespaces:")
        for ns in namespaces:
            print(f"  • {ns.name}")
            if ns.display_name:
                print(f"    Display Name: {ns.display_name}")
            if ns.description:
                print(f"    Description: {ns.description}")
        
        # Discover projects
        print("\n📋 Discovering projects...")
        projects = await discovery_service.discover_projects()
        print(f"Found {len(projects)} accessible projects:")
        for proj in projects:
            print(f"  • {proj.name}")
            if proj.display_name:
                print(f"    Display Name: {proj.display_name}")
            if proj.description:
                print(f"    Description: {proj.description}")
        
        # Discover resources in each namespace
        if namespaces:
            print("\n🔧 Discovering resources in namespaces...")
            for ns in namespaces[:3]:  # Limit to first 3 namespaces
                print(f"\n  Namespace: {ns.name}")
                try:
                    resources = await discovery_service.discover_resources(ns.name)
                    print(f"    Accessible resources: {len(resources.accessible_resources)}")
                    for resource in resources.accessible_resources:
                        print(f"      • {resource.value}")
                except Exception as e:
                    print(f"    ❌ Error discovering resources: {e}")
        
        # Get discovery summary
        print("\n📊 Discovery Summary:")
        summary = await discovery_service.get_discovery_summary()
        print(f"  Namespaces found: {summary['namespaces_found']}")
        print(f"  Projects found: {summary['projects_found']}")
        print(f"  Cache stats: {summary['cache_stats']}")
        
        # Test specific namespace access
        if namespaces:
            test_namespace = namespaces[0].name
            print(f"\n🧪 Testing access to namespace: {test_namespace}")
            has_access = await discovery_service.test_namespace_access(test_namespace)
            print(f"  Access: {'✅ Yes' if has_access else '❌ No'}")
        
        print("\n✅ Discovery service example completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during discovery: {e}")
    
    finally:
        # Clean up
        await client.close()


if __name__ == "__main__":
    # Set up environment variables for testing (if not already set)
    if not os.getenv('OPENSHIFT_TOKEN'):
        os.environ.setdefault('OPENSHIFT_TOKEN', 'your-token-here')
    if not os.getenv('OPENSHIFT_URL'):
        os.environ.setdefault('OPENSHIFT_URL', 'https://your-cluster.com')
    
    asyncio.run(main()) 