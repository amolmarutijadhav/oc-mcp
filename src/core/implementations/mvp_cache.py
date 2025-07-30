"""
MVP Cache implementation for the OpenShift MCP Server.

This module implements a simple but effective in-memory cache with LRU eviction
and TTL support for the MVP version.
"""

import asyncio
import time
from typing import Any, Optional, Dict, List
from datetime import datetime
from collections import OrderedDict
import structlog

from ..interfaces.cache import ICacheProvider, CacheEntry


logger = structlog.get_logger(__name__)


class MVPCache(ICacheProvider):
    """
    MVP Cache implementation with LRU eviction and TTL support.
    
    This implementation provides:
    - In-memory storage with configurable size limits
    - LRU (Least Recently Used) eviction policy
    - TTL (Time To Live) support
    - Background refresh capability
    - Stale data support
    """
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        """
        Initialize the MVP cache.
        
        Args:
            max_size: Maximum number of cache entries
            default_ttl: Default TTL in seconds
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "sets": 0,
            "deletes": 0
        }
        self._lock = asyncio.Lock()
        
        logger.info("MVP Cache initialized", max_size=max_size, default_ttl=default_ttl)
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Retrieve a value from the cache.
        
        Args:
            key: The cache key to retrieve
            
        Returns:
            The cached value if found and not expired, None otherwise
        """
        async with self._lock:
            if key not in self.cache:
                self.stats["misses"] += 1
                logger.debug("Cache miss", key=key)
                return None
            
            entry = self.cache[key]
            
            # Check if entry is expired
            if self._is_expired(entry):
                # Remove expired entry
                del self.cache[key]
                self.stats["misses"] += 1
                logger.debug("Cache entry expired", key=key)
                return None
            
            # Update access count and last accessed time
            entry.access_count += 1
            entry.last_accessed = datetime.now()
            
            # Move to end (LRU)
            self.cache.move_to_end(key)
            
            self.stats["hits"] += 1
            logger.debug("Cache hit", key=key, access_count=entry.access_count)
            
            return entry.data
    
    async def set(self, key: str, data: Any, ttl: int = None) -> None:
        """
        Store a value in the cache.
        
        Args:
            key: The cache key
            data: The data to cache
            ttl: Time to live in seconds (optional)
        """
        async with self._lock:
            # Remove existing entry if it exists
            if key in self.cache:
                del self.cache[key]
            
            # Check if we need to evict entries
            if len(self.cache) >= self.max_size:
                await self._evict_lru()
            
            # Create new entry
            entry = CacheEntry(
                data=data,
                timestamp=datetime.now(),
                ttl=ttl or self.default_ttl,
                access_count=1,
                last_accessed=datetime.now()
            )
            
            # Add to cache
            self.cache[key] = entry
            
            self.stats["sets"] += 1
            logger.debug("Cache set", key=key, ttl=entry.ttl)
    
    async def exists(self, key: str) -> bool:
        """
        Check if a key exists in the cache.
        
        Args:
            key: The cache key to check
            
        Returns:
            True if the key exists and is not expired, False otherwise
        """
        async with self._lock:
            if key not in self.cache:
                return False
            
            entry = self.cache[key]
            return not self._is_expired(entry)
    
    async def delete(self, key: str) -> bool:
        """
        Delete a key from the cache.
        
        Args:
            key: The cache key to delete
            
        Returns:
            True if the key was deleted, False if it didn't exist
        """
        async with self._lock:
            if key in self.cache:
                del self.cache[key]
                self.stats["deletes"] += 1
                logger.debug("Cache delete", key=key)
                return True
            return False
    
    async def clear(self) -> None:
        """
        Clear all entries from the cache.
        """
        async with self._lock:
            self.cache.clear()
            logger.info("Cache cleared")
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary containing cache statistics
        """
        async with self._lock:
            total_requests = self.stats["hits"] + self.stats["misses"]
            hit_rate = self.stats["hits"] / total_requests if total_requests > 0 else 0
            
            return {
                "hits": self.stats["hits"],
                "misses": self.stats["misses"],
                "hit_rate": hit_rate,
                "evictions": self.stats["evictions"],
                "sets": self.stats["sets"],
                "deletes": self.stats["deletes"],
                "current_size": len(self.cache),
                "max_size": self.max_size,
                "expired_entries": await self._count_expired_entries()
            }
    
    async def is_stale(self, key: str) -> bool:
        """
        Check if a cached value is stale (expired but still present).
        
        Args:
            key: The cache key to check
            
        Returns:
            True if the value is stale, False otherwise
        """
        async with self._lock:
            if key not in self.cache:
                return False
            
            entry = self.cache[key]
            return self._is_expired(entry)
    
    async def get_stale_data(self, key: str) -> Optional[Any]:
        """
        Get stale data (expired but still present) from cache.
        
        Args:
            key: The cache key
            
        Returns:
            The stale data if available, None otherwise
        """
        async with self._lock:
            if key not in self.cache:
                return None
            
            entry = self.cache[key]
            if self._is_expired(entry):
                logger.debug("Returning stale data", key=key)
                return entry.data
            
            return None
    
    def _is_expired(self, entry: CacheEntry) -> bool:
        """
        Check if a cache entry is expired.
        
        Args:
            entry: The cache entry to check
            
        Returns:
            True if expired, False otherwise
        """
        age = (datetime.now() - entry.timestamp).total_seconds()
        return age > entry.ttl
    
    async def _evict_lru(self) -> None:
        """
        Evict the least recently used entry from the cache.
        """
        if not self.cache:
            return
        
        # Remove the first item (least recently used)
        key, entry = self.cache.popitem(last=False)
        self.stats["evictions"] += 1
        
        logger.debug("LRU eviction", key=key, access_count=entry.access_count)
    
    async def _count_expired_entries(self) -> int:
        """
        Count the number of expired entries in the cache.
        
        Returns:
            Number of expired entries
        """
        count = 0
        for entry in self.cache.values():
            if self._is_expired(entry):
                count += 1
        return count
    
    async def cleanup_expired(self) -> int:
        """
        Remove all expired entries from the cache.
        
        Returns:
            Number of entries removed
        """
        async with self._lock:
            expired_keys = []
            for key, entry in self.cache.items():
                if self._is_expired(entry):
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self.cache[key]
            
            logger.info("Cleaned up expired entries", count=len(expired_keys))
            return len(expired_keys) 