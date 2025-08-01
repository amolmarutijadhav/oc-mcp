"""
Abstract interfaces for the OpenShift MCP Server.

This package contains all abstract base classes that define
the contracts for implementations.
"""

from .client import IOpenShiftClient
from .discovery import IDiscoveryService, NamespaceInfo, ProjectInfo, ResourceAccess, ResourceType

__all__ = [
    'IOpenShiftClient',
    'IDiscoveryService',
    'NamespaceInfo', 
    'ProjectInfo',
    'ResourceAccess',
    'ResourceType'
] 