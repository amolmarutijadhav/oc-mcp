"""
Cache provider interface for the OpenShift MCP Server.

This module defines the abstract interface for cache implementations.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional, Dict
from dataclasses import dataclass
from datetime import datetime


@dataclass
class CacheEntry:
    """Represents a cache entry with metadata."""
    data: Any
    timestamp: datetime
    ttl: int
    access_count: int = 0
    last_accessed: datetime = None


class ICacheProvider(ABC):
    """
    Abstract interface for cache providers.
    
    This interface defines the contract for cache implementations
    that can be used by the MCP server for performance optimization.
    """
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """
        Retrieve a value from the cache.
        
        Args:
            key: The cache key to retrieve
            
        Returns:
            The cached value if found and not expired, None otherwise
        """
        pass
    
    @abstractmethod
    async def set(self, key: str, data: Any, ttl: int = None) -> None:
        """
        Store a value in the cache.
        
        Args:
            key: The cache key
            data: The data to cache
            ttl: Time to live in seconds (optional)
        """
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """
        Check if a key exists in the cache.
        
        Args:
            key: The cache key to check
            
        Returns:
            True if the key exists and is not expired, False otherwise
        """
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """
        Delete a key from the cache.
        
        Args:
            key: The cache key to delete
            
        Returns:
            True if the key was deleted, False if it didn't exist
        """
        pass
    
    @abstractmethod
    async def clear(self) -> None:
        """
        Clear all entries from the cache.
        """
        pass
    
    @abstractmethod
    async def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary containing cache statistics
        """
        pass
    
    @abstractmethod
    async def is_stale(self, key: str) -> bool:
        """
        Check if a cached value is stale (expired but still present).
        
        Args:
            key: The cache key to check
            
        Returns:
            True if the value is stale, False otherwise
        """
        pass 