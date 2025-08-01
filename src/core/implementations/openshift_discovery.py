"""
OpenShift discovery service implementation.

This module implements the discovery service for finding accessible
resources in OpenShift clusters using multiple strategies.
"""

import asyncio
import time
from typing import List, Dict, Any, Optional, Callable
from kubernetes import client
from kubernetes.client.rest import ApiException
import structlog

from ..interfaces.discovery import (
    IDiscoveryService,
    NamespaceInfo,
    ProjectInfo,
    ResourceAccess,
    ResourceType,
    DiscoveryStrategy
)
from ..interfaces.client import IOpenShiftClient
from ...config.discovery_config import DiscoveryConfig, DEFAULT_DISCOVERY_CONFIG
from .discovery_cache import DiscoveryCache

logger = structlog.get_logger(__name__)


class OpenShiftDiscoveryService(IDiscoveryService):
    """
    OpenShift discovery service implementation.
    
    This service uses multiple strategies to discover accessible
    resources in OpenShift clusters.
    """
    
    def __init__(self, client: IOpenShiftClient, config: Optional[DiscoveryConfig] = None):
        """
        Initialize the OpenShift discovery service.
        
        Args:
            client: OpenShift client instance
            config: Discovery configuration
        """
        self.client = client
        self.config = config or DEFAULT_DISCOVERY_CONFIG
        self.cache = DiscoveryCache(self.config.cache_ttl)
        self._discovery_results: Dict[str, Any] = {}
        
        # Initialize OpenShift-specific API clients if available
        self._init_openshift_apis()
        
        logger.info("OpenShift discovery service initialized", 
                   enabled_strategies=[s.value for s in self.config.enabled_strategies])
    
    def _init_openshift_apis(self) -> None:
        """Initialize OpenShift-specific API clients."""
        try:
            # Try to get OpenShift-specific API clients
            if hasattr(self.client, 'api_client'):
                # Use OpenShift-specific client instead of kubernetes.client
                import openshift
                self.project_v1_api = openshift.client.ProjectOpenshiftIoV1Api(self.client.api_client)
                self.user_v1_api = openshift.client.UserOpenshiftIoV1Api(self.client.api_client)
                logger.debug("OpenShift-specific APIs initialized")
            else:
                self.project_v1_api = None
                self.user_v1_api = None
                logger.debug("OpenShift-specific APIs not available")
        except Exception as e:
            logger.warning("Failed to initialize OpenShift-specific APIs", error=str(e))
            self.project_v1_api = None
            self.user_v1_api = None
    
    async def _discover_via_oc_cli(self) -> List[NamespaceInfo]:
        """Discover namespaces using oc CLI as fallback."""
        try:
            import subprocess
            import json
            
            # Run oc get projects command
            result = subprocess.run(
                ['oc', 'get', 'projects', '-o', 'json'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                projects_data = json.loads(result.stdout)
                namespaces = []
                
                for proj in projects_data.get('items', []):
                    metadata = proj.get('metadata', {})
                    name = metadata.get('name', '')
                    annotations = metadata.get('annotations', {})
                    
                    namespace_info = NamespaceInfo(
                        name=name,
                        display_name=annotations.get('openshift.io/display-name'),
                        description=annotations.get('openshift.io/description'),
                        status=proj.get('status', {}).get('phase')
                    )
                    namespaces.append(namespace_info)
                
                logger.info("Namespace discovery via oc CLI successful", count=len(namespaces))
                return namespaces
            else:
                logger.warning("oc CLI command failed", error=result.stderr)
                return []
                
        except Exception as e:
            logger.warning("oc CLI discovery failed", error=str(e))
            return []
    
    async def discover_namespaces(self) -> List[NamespaceInfo]:
        """
        Discover accessible namespaces using multiple strategies.
        
        Returns:
            List of accessible namespace information
        """
        cache_key = "discovery:namespaces"
        
        async def discover():
            return await self._discover_namespaces_impl()
        
        return await self.cache.get_or_set(cache_key, discover)
    
    async def discover_projects(self) -> List[ProjectInfo]:
        """
        Discover accessible OpenShift projects.
        
        Returns:
            List of accessible project information
        """
        cache_key = "discovery:projects"
        
        async def discover():
            return await self._discover_projects_impl()
        
        return await self.cache.get_or_set(cache_key, discover)
    
    async def discover_resources(self, namespace: str) -> ResourceAccess:
        """
        Discover accessible resources in a specific namespace.
        
        Args:
            namespace: The namespace to discover resources in
            
        Returns:
            Information about accessible resources in the namespace
        """
        cache_key = f"discovery:resources:{namespace}"
        
        async def discover():
            return await self._discover_resources_impl(namespace)
        
        return await self.cache.get_or_set(cache_key, discover)
    
    async def test_namespace_access(self, namespace: str) -> bool:
        """
        Test if a namespace is accessible.
        
        Args:
            namespace: The namespace to test
            
        Returns:
            True if accessible, False otherwise
        """
        try:
            # Try to get namespace info as a lightweight test
            await self._get_namespace_info(namespace)
            return True
        except Exception as e:
            logger.debug("Namespace access test failed", namespace=namespace, error=str(e))
            return False
    
    async def test_resource_access(self, namespace: str, resource_type: ResourceType) -> bool:
        """
        Test if a specific resource type is accessible in a namespace.
        
        Args:
            namespace: The namespace to test
            resource_type: The type of resource to test
            
        Returns:
            True if accessible, False otherwise
        """
        try:
            if resource_type == ResourceType.POD:
                await self.client.list_pods(namespace)
            elif resource_type == ResourceType.SERVICE:
                await self.client.list_services(namespace)
            elif resource_type == ResourceType.DEPLOYMENT:
                await self.client.list_deployments(namespace)
            elif resource_type == ResourceType.EVENT:
                await self.client.get_events(namespace, limit=1)
            else:
                logger.warning("Unknown resource type for testing", resource_type=resource_type.value)
                return False
            
            return True
        except Exception as e:
            logger.debug("Resource access test failed", 
                        namespace=namespace, resource_type=resource_type.value, error=str(e))
            return False
    
    async def get_discovery_summary(self) -> Dict[str, Any]:
        """
        Get a summary of discovery results.
        
        Returns:
            Dictionary containing discovery summary information
        """
        namespaces = await self.discover_namespaces()
        projects = await self.discover_projects()
        cache_stats = await self.cache.get_stats()
        
        return {
            "namespaces_found": len(namespaces),
            "projects_found": len(projects),
            "accessible_namespaces": [ns.name for ns in namespaces],
            "accessible_projects": [proj.name for proj in projects],
            "cache_stats": cache_stats,
            "config": {
                "enabled_strategies": [s.value for s in self.config.enabled_strategies],
                "cache_ttl": self.config.cache_ttl,
                "discovery_timeout": self.config.discovery_timeout
            }
        }
    
    async def _discover_namespaces_impl(self) -> List[NamespaceInfo]:
        """Implementation of namespace discovery using multiple strategies."""
        strategies = [
            (DiscoveryStrategy.PROJECT_API, self._discover_via_project_api),
            (DiscoveryStrategy.NAMESPACE_API, self._discover_via_namespace_api),
            (DiscoveryStrategy.COMMON_NAMESPACES, self._discover_via_common_namespaces),
            (DiscoveryStrategy.USER_PROJECTS, self._discover_via_oc_cli),  # Add oc CLI as fallback
        ]
        
        for strategy_enum, strategy_func in strategies:
            # Fix: Compare by value instead of object identity
            enabled_strategy_values = [s.value for s in self.config.enabled_strategies]
            if strategy_enum.value not in enabled_strategy_values:
                logger.debug("Strategy not enabled", strategy=strategy_enum.value)
                continue
            
            try:
                logger.debug("Trying discovery strategy", strategy=strategy_enum.value)
                result = await strategy_func()
                if result:
                    logger.info("Namespace discovery successful", 
                              strategy=strategy_enum.value, count=len(result))
                    return result
                else:
                    logger.debug("Strategy returned no results", strategy=strategy_enum.value)
            except Exception as e:
                logger.warning("Discovery strategy failed", 
                             strategy=strategy_enum.value, error=str(e))
                if self.config.fail_fast:
                    break
        
        logger.warning("All namespace discovery strategies failed")
        return []
    
    async def _discover_projects_impl(self) -> List[ProjectInfo]:
        """Implementation of project discovery using multiple strategies."""
        strategies = [
            (DiscoveryStrategy.PROJECT_API, self._discover_via_project_api_direct),
            (DiscoveryStrategy.USER_PROJECTS, self._discover_via_oc_cli_for_projects),
        ]
        
        for strategy_enum, strategy_func in strategies:
            # Fix: Compare by value instead of object identity
            enabled_strategy_values = [s.value for s in self.config.enabled_strategies]
            if strategy_enum.value not in enabled_strategy_values:
                logger.debug("Strategy not enabled", strategy=strategy_enum.value)
                continue
            
            try:
                logger.debug("Trying project discovery strategy", strategy=strategy_enum.value)
                result = await strategy_func()
                if result:
                    logger.info("Project discovery successful", 
                              strategy=strategy_enum.value, count=len(result))
                    return result
                else:
                    logger.debug("Strategy returned no results", strategy=strategy_enum.value)
            except Exception as e:
                logger.warning("Project discovery strategy failed", 
                             strategy=strategy_enum.value, error=str(e))
                if self.config.fail_fast:
                    break
        
        logger.warning("All project discovery strategies failed")
        return []
    
    async def _discover_via_project_api_direct(self) -> List[ProjectInfo]:
        """Discover projects via OpenShift Project API."""
        if not self.project_v1_api:
            logger.debug("OpenShift Project API not available")
            return []
        
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                self.project_v1_api.list_project
            )
            
            projects = []
            for proj in response.items:
                project_info = ProjectInfo(
                    name=proj.metadata.name,
                    display_name=proj.metadata.annotations.get(self.config.openshift_project_label),
                    description=proj.metadata.annotations.get(self.config.openshift_description_label),
                    status=proj.status.phase if hasattr(proj.status, 'phase') else None
                )
                projects.append(project_info)
            
            return projects
            
        except ApiException as e:
            if e.status == 403:
                logger.warning("Permission denied for project discovery")
            else:
                logger.error("Project discovery failed", error=str(e))
            return []
        except Exception as e:
            logger.error("Unexpected error in project discovery", error=str(e))
            return []
    
    async def _discover_via_oc_cli_for_projects(self) -> List[ProjectInfo]:
        """Discover projects using oc CLI."""
        try:
            import subprocess
            import json
            
            # Run oc get projects command
            result = subprocess.run(
                ['oc', 'get', 'projects', '-o', 'json'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                projects_data = json.loads(result.stdout)
                projects = []
                
                for proj in projects_data.get('items', []):
                    metadata = proj.get('metadata', {})
                    name = metadata.get('name', '')
                    annotations = metadata.get('annotations', {})
                    
                    project_info = ProjectInfo(
                        name=name,
                        display_name=annotations.get('openshift.io/display-name'),
                        description=annotations.get('openshift.io/description'),
                        status=proj.get('status', {}).get('phase')
                    )
                    projects.append(project_info)
                
                logger.info("Project discovery via oc CLI successful", count=len(projects))
                return projects
            else:
                logger.warning("oc CLI command failed", error=result.stderr)
                return []
                
        except Exception as e:
            logger.warning("oc CLI project discovery failed", error=str(e))
            return []
    
    async def _discover_via_project_api(self) -> List[NamespaceInfo]:
        """Discover namespaces via OpenShift Project API."""
        projects = await self._discover_projects_impl()
        return [
            NamespaceInfo(
                name=proj.name,
                display_name=proj.display_name,
                description=proj.description,
                status=proj.status
            )
            for proj in projects
        ]
    
    async def _discover_via_namespace_api(self) -> List[NamespaceInfo]:
        """Discover namespaces via Kubernetes Namespace API."""
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                self.client.core_v1_api.list_namespace
            )
            
            namespaces = []
            for ns in response.items:
                namespace_info = NamespaceInfo(
                    name=ns.metadata.name,
                    status=ns.status.phase if hasattr(ns.status, 'phase') else None
                )
                namespaces.append(namespace_info)
            
            return namespaces
            
        except ApiException as e:
            if e.status == 403:
                logger.warning("Permission denied for namespace discovery")
            else:
                logger.error("Namespace discovery failed", error=str(e))
            return []
        except Exception as e:
            logger.error("Unexpected error in namespace discovery", error=str(e))
            return []
    
    async def _discover_via_common_namespaces(self) -> List[NamespaceInfo]:
        """Discover namespaces by testing common namespace names."""
        namespaces = []
        
        # Test common namespaces concurrently
        tasks = [
            self._test_and_create_namespace_info(ns)
            for ns in self.config.common_namespaces
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, NamespaceInfo):
                namespaces.append(result)
            elif isinstance(result, Exception):
                logger.debug("Common namespace test failed", error=str(result))
        
        return namespaces
    
    async def _test_and_create_namespace_info(self, namespace: str) -> Optional[NamespaceInfo]:
        """Test a namespace and create NamespaceInfo if accessible."""
        if await self.test_namespace_access(namespace):
            return NamespaceInfo(name=namespace)
        return None
    
    async def _discover_resources_impl(self, namespace: str) -> ResourceAccess:
        """Implementation of resource discovery in a namespace."""
        accessible_resources = []
        
        # Test each resource type
        for resource_type_str in self.config.resource_types_to_test:
            try:
                resource_type = ResourceType(resource_type_str)
                if await self.test_resource_access(namespace, resource_type):
                    accessible_resources.append(resource_type)
            except ValueError:
                logger.warning("Unknown resource type", resource_type=resource_type_str)
        
        return ResourceAccess(
            namespace=namespace,
            accessible_resources=accessible_resources,
            last_checked=time.time()
        )
    
    async def _get_namespace_info(self, namespace: str) -> Any:
        """Get namespace information as a lightweight access test."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self.client.core_v1_api.read_namespace,
            namespace
        )
    
    async def invalidate_cache(self, pattern: Optional[str] = None) -> int:
        """
        Invalidate discovery cache.
        
        Args:
            pattern: Optional pattern to match cache keys
            
        Returns:
            Number of entries invalidated
        """
        if pattern:
            return await self.cache.invalidate_pattern(pattern)
        else:
            return await self.cache.clear()
    
    async def start_background_tasks(self) -> None:
        """Start background tasks for cache maintenance."""
        if self.config.enable_caching:
            await self.cache.start_cleanup_task()
            logger.info("Background cache cleanup task started") 