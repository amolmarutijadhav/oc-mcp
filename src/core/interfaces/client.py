"""
OpenShift client interface for the OpenShift MCP Server.

This module defines the abstract interface for OpenShift API client implementations.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class PodInfo:
    """Represents pod information."""
    name: str
    namespace: str
    status: str
    ready: bool
    containers: List[str]
    age: str


@dataclass
class ServiceInfo:
    """Represents service information."""
    name: str
    namespace: str
    type: str
    cluster_ip: str
    external_ip: Optional[str]
    ports: List[str]
    age: str


@dataclass
class DeploymentInfo:
    """Represents deployment information."""
    name: str
    namespace: str
    replicas: int
    available: int
    ready: int
    age: str


class IOpenShiftClient(ABC):
    """
    Abstract interface for OpenShift API clients.
    
    This interface defines the contract for OpenShift client implementations
    that can be used by the MCP server to interact with OpenShift clusters.
    """
    
    @abstractmethod
    async def authenticate(self, token: str, url: str) -> bool:
        """
        Authenticate with OpenShift cluster.
        
        Args:
            token: OpenShift authentication token
            url: OpenShift cluster URL
            
        Returns:
            True if authentication successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def list_pods(self, namespace: str = "default") -> List[PodInfo]:
        """
        List pods in a namespace.
        
        Args:
            namespace: The namespace to list pods from
            
        Returns:
            List of pod information
        """
        pass
    
    @abstractmethod
    async def get_pod_status(self, name: str, namespace: str = "default") -> Optional[PodInfo]:
        """
        Get status of a specific pod.
        
        Args:
            name: Pod name
            namespace: Pod namespace
            
        Returns:
            Pod information if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def list_services(self, namespace: str = "default") -> List[ServiceInfo]:
        """
        List services in a namespace.
        
        Args:
            namespace: The namespace to list services from
            
        Returns:
            List of service information
        """
        pass
    
    @abstractmethod
    async def get_service(self, name: str, namespace: str = "default") -> Optional[ServiceInfo]:
        """
        Get information about a specific service.
        
        Args:
            name: Service name
            namespace: Service namespace
            
        Returns:
            Service information if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def list_deployments(self, namespace: str = "default") -> List[DeploymentInfo]:
        """
        List deployments in a namespace.
        
        Args:
            namespace: The namespace to list deployments from
            
        Returns:
            List of deployment information
        """
        pass
    
    @abstractmethod
    async def get_deployment(self, name: str, namespace: str = "default") -> Optional[DeploymentInfo]:
        """
        Get information about a specific deployment.
        
        Args:
            name: Deployment name
            namespace: Deployment namespace
            
        Returns:
            Deployment information if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def get_pod_logs(self, name: str, namespace: str = "default", 
                          tail_lines: int = 100) -> Optional[str]:
        """
        Get logs from a pod.
        
        Args:
            name: Pod name
            namespace: Pod namespace
            tail_lines: Number of lines to retrieve
            
        Returns:
            Pod logs if available, None otherwise
        """
        pass
    
    @abstractmethod
    async def list_namespaces(self) -> List[str]:
        """
        List available namespaces.
        
        Returns:
            List of namespace names
        """
        pass
    
    @abstractmethod
    async def get_events(self, namespace: str = "default", 
                        limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get events from a namespace.
        
        Args:
            namespace: The namespace to get events from
            limit: Maximum number of events to retrieve
            
        Returns:
            List of events
        """
        pass
    
    @abstractmethod
    async def is_connected(self) -> bool:
        """
        Check if the client is connected to the cluster.
        
        Returns:
            True if connected, False otherwise
        """
        pass
    
    @abstractmethod
    async def close(self) -> None:
        """
        Close the client connection.
        """
        pass 