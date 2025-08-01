"""
Discovery service interface for the OpenShift MCP Server.

This module defines the abstract interface for resource discovery implementations
that can find accessible namespaces, projects, and resources in OpenShift clusters.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class ResourceType(Enum):
    """Types of resources that can be discovered."""
    NAMESPACE = "namespace"
    PROJECT = "project"
    POD = "pod"
    SERVICE = "service"
    DEPLOYMENT = "deployment"
    EVENT = "event"


@dataclass
class NamespaceInfo:
    """Information about a discovered namespace."""
    name: str
    display_name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    accessible_resources: List[ResourceType] = None
    
    def __post_init__(self):
        if self.accessible_resources is None:
            self.accessible_resources = []


@dataclass
class ProjectInfo:
    """Information about a discovered OpenShift project."""
    name: str
    display_name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    accessible_resources: List[ResourceType] = None
    
    def __post_init__(self):
        if self.accessible_resources is None:
            self.accessible_resources = []


@dataclass
class ResourceAccess:
    """Information about resource access in a namespace."""
    namespace: str
    accessible_resources: List[ResourceType]
    last_checked: Optional[float] = None


class DiscoveryStrategy(Enum):
    """Available discovery strategies."""
    PROJECT_API = "project_api"
    NAMESPACE_API = "namespace_api"
    RESOURCE_TESTING = "resource_testing"
    COMMON_NAMESPACES = "common_namespaces"
    USER_PROJECTS = "user_projects"


class IDiscoveryService(ABC):
    """
    Abstract interface for OpenShift resource discovery services.
    
    This interface defines the contract for discovery implementations
    that can find accessible resources in OpenShift clusters.
    """
    
    @abstractmethod
    async def discover_namespaces(self) -> List[NamespaceInfo]:
        """
        Discover accessible namespaces.
        
        Returns:
            List of accessible namespace information
        """
        pass
    
    @abstractmethod
    async def discover_projects(self) -> List[ProjectInfo]:
        """
        Discover accessible OpenShift projects.
        
        Returns:
            List of accessible project information
        """
        pass
    
    @abstractmethod
    async def discover_resources(self, namespace: str) -> ResourceAccess:
        """
        Discover accessible resources in a specific namespace.
        
        Args:
            namespace: The namespace to discover resources in
            
        Returns:
            Information about accessible resources in the namespace
        """
        pass
    
    @abstractmethod
    async def test_namespace_access(self, namespace: str) -> bool:
        """
        Test if a namespace is accessible.
        
        Args:
            namespace: The namespace to test
            
        Returns:
            True if accessible, False otherwise
        """
        pass
    
    @abstractmethod
    async def test_resource_access(self, namespace: str, resource_type: ResourceType) -> bool:
        """
        Test if a specific resource type is accessible in a namespace.
        
        Args:
            namespace: The namespace to test
            resource_type: The type of resource to test
            
        Returns:
            True if accessible, False otherwise
        """
        pass
    
    @abstractmethod
    async def get_discovery_summary(self) -> Dict[str, Any]:
        """
        Get a summary of discovery results.
        
        Returns:
            Dictionary containing discovery summary information
        """
        pass 