"""
Cache implementation for the OpenShift discovery service.

This module provides caching functionality for discovery results
to improve performance and reduce API calls.
"""

import time
import asyncio
from typing import Any, Dict, Optional, Callable
from dataclasses import dataclass
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class CacheEntry:
    """A cache entry with data and metadata."""
    data: Any
    timestamp: float
    ttl: int


class DiscoveryCache:
    """Cache for discovery results with TTL and invalidation."""
    
    def __init__(self, default_ttl: int = 300):
        """
        Initialize the discovery cache.
        
        Args:
            default_ttl: Default time-to-live in seconds
        """
        self.cache: Dict[str, CacheEntry] = {}
        self.default_ttl = default_ttl
        self._lock = asyncio.Lock()
        
        logger.info("Discovery cache initialized", default_ttl=default_ttl)
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get a value from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value if valid, None otherwise
        """
        async with self._lock:
            if key not in self.cache:
                return None
            
            entry = self.cache[key]
            if self._is_expired(entry):
                del self.cache[key]
                logger.debug("Cache entry expired", key=key)
                return None
            
            logger.debug("Cache hit", key=key)
            return entry.data
    
    async def set(self, key: str, data: Any, ttl: Optional[int] = None) -> None:
        """
        Set a value in the cache.
        
        Args:
            key: Cache key
            data: Data to cache
            ttl: Time-to-live in seconds (uses default if None)
        """
        async with self._lock:
            cache_ttl = ttl if ttl is not None else self.default_ttl
            entry = CacheEntry(
                data=data,
                timestamp=time.time(),
                ttl=cache_ttl
            )
            
            self.cache[key] = entry
            logger.debug("Cache entry set", key=key, ttl=cache_ttl)
    
    async def get_or_set(self, key: str, getter_func: Callable, ttl: Optional[int] = None) -> Any:
        """
        Get from cache or compute and cache the result.
        
        Args:
            key: Cache key
            getter_func: Async function to call if cache miss
            ttl: Time-to-live in seconds (uses default if None)
            
        Returns:
            Cached or computed value
        """
        # Try to get from cache first
        cached_value = await self.get(key)
        if cached_value is not None:
            return cached_value
        
        # Cache miss, compute the value
        logger.debug("Cache miss, computing value", key=key)
        try:
            value = await getter_func()
            await self.set(key, value, ttl)
            return value
        except Exception as e:
            logger.error("Error computing cached value", key=key, error=str(e))
            raise
    
    async def invalidate(self, key: str) -> bool:
        """
        Invalidate a cache entry.
        
        Args:
            key: Cache key to invalidate
            
        Returns:
            True if entry was found and removed, False otherwise
        """
        async with self._lock:
            if key in self.cache:
                del self.cache[key]
                logger.debug("Cache entry invalidated", key=key)
                return True
            return False
    
    async def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate all cache entries matching a pattern.
        
        Args:
            pattern: Pattern to match (simple substring match)
            
        Returns:
            Number of entries invalidated
        """
        async with self._lock:
            keys_to_remove = [key for key in self.cache.keys() if pattern in key]
            for key in keys_to_remove:
                del self.cache[key]
            
            logger.debug("Cache entries invalidated by pattern", 
                        pattern=pattern, count=len(keys_to_remove))
            return len(keys_to_remove)
    
    async def clear(self) -> int:
        """
        Clear all cache entries.
        
        Returns:
            Number of entries cleared
        """
        async with self._lock:
            count = len(self.cache)
            self.cache.clear()
            logger.info("Cache cleared", entries_cleared=count)
            return count
    
    async def cleanup_expired(self) -> int:
        """
        Remove all expired entries from the cache.
        
        Returns:
            Number of expired entries removed
        """
        async with self._lock:
            expired_keys = [
                key for key, entry in self.cache.items()
                if self._is_expired(entry)
            ]
            
            for key in expired_keys:
                del self.cache[key]
            
            if expired_keys:
                logger.debug("Expired cache entries cleaned up", 
                            count=len(expired_keys))
            
            return len(expired_keys)
    
    def _is_expired(self, entry: CacheEntry) -> bool:
        """Check if a cache entry is expired."""
        return time.time() - entry.timestamp > entry.ttl
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        async with self._lock:
            now = time.time()
            total_entries = len(self.cache)
            expired_entries = sum(
                1 for entry in self.cache.values()
                if self._is_expired(entry)
            )
            
            return {
                "total_entries": total_entries,
                "expired_entries": expired_entries,
                "valid_entries": total_entries - expired_entries,
                "cache_size": len(self.cache),
                "default_ttl": self.default_ttl
            }
    
    async def start_cleanup_task(self, interval: int = 60) -> None:
        """
        Start a background task to clean up expired entries.
        
        Args:
            interval: Cleanup interval in seconds
        """
        async def cleanup_loop():
            while True:
                try:
                    await asyncio.sleep(interval)
                    await self.cleanup_expired()
                except Exception as e:
                    logger.error("Error in cache cleanup task", error=str(e))
        
        asyncio.create_task(cleanup_loop())
        logger.info("Cache cleanup task started", interval=interval) 