"""
Unit tests for the MVP cache implementation.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from src.core.implementations.mvp_cache import MVPCache


class TestMVPCache:
    """Test cases for MVPCache."""
    
    @pytest.fixture
    async def cache(self):
        """Create a cache instance for testing."""
        cache = MVPCache(max_size=10, default_ttl=60)
        yield cache
        await cache.clear()
    
    @pytest.mark.asyncio
    async def test_set_and_get(self, cache):
        """Test setting and getting values."""
        await cache.set("test_key", "test_value")
        result = await cache.get("test_key")
        assert result == "test_value"
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_key(self, cache):
        """Test getting a key that doesn't exist."""
        result = await cache.get("nonexistent_key")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_exists(self, cache):
        """Test checking if a key exists."""
        await cache.set("test_key", "test_value")
        assert await cache.exists("test_key") is True
        assert await cache.exists("nonexistent_key") is False
    
    @pytest.mark.asyncio
    async def test_delete(self, cache):
        """Test deleting a key."""
        await cache.set("test_key", "test_value")
        assert await cache.delete("test_key") is True
        assert await cache.get("test_key") is None
        assert await cache.delete("nonexistent_key") is False
    
    @pytest.mark.asyncio
    async def test_clear(self, cache):
        """Test clearing the cache."""
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        await cache.clear()
        assert await cache.get("key1") is None
        assert await cache.get("key2") is None
    
    @pytest.mark.asyncio
    async def test_ttl_expiration(self, cache):
        """Test TTL expiration."""
        # Create cache with very short TTL
        short_ttl_cache = MVPCache(max_size=10, default_ttl=1)
        
        await short_ttl_cache.set("test_key", "test_value")
        assert await short_ttl_cache.get("test_key") == "test_value"
        
        # Wait for expiration
        await asyncio.sleep(1.1)
        assert await short_ttl_cache.get("test_key") is None
    
    @pytest.mark.asyncio
    async def test_custom_ttl(self, cache):
        """Test custom TTL for individual entries."""
        await cache.set("test_key", "test_value", ttl=1)
        assert await cache.get("test_key") == "test_value"
        
        # Wait for expiration
        await asyncio.sleep(1.1)
        assert await cache.get("test_key") is None
    
    @pytest.mark.asyncio
    async def test_lru_eviction(self, cache):
        """Test LRU eviction when cache is full."""
        # Fill cache to capacity
        for i in range(10):
            await cache.set(f"key{i}", f"value{i}")
        
        # Add one more entry, should evict the least recently used
        await cache.set("new_key", "new_value")
        
        # First key should be evicted
        assert await cache.get("key0") is None
        # New key should be present
        assert await cache.get("new_key") == "new_value"
    
    @pytest.mark.asyncio
    async def test_get_stats(self, cache):
        """Test getting cache statistics."""
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        await cache.get("key1")  # Hit
        await cache.get("key3")  # Miss
        
        stats = await cache.get_stats()
        
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["sets"] == 2
        assert stats["current_size"] == 2
        assert stats["max_size"] == 10
        assert 0 <= stats["hit_rate"] <= 1
    
    @pytest.mark.asyncio
    async def test_is_stale(self, cache):
        """Test checking if a value is stale."""
        # Create cache with very short TTL
        short_ttl_cache = MVPCache(max_size=10, default_ttl=1)
        
        await short_ttl_cache.set("test_key", "test_value")
        assert await short_ttl_cache.is_stale("test_key") is False
        
        # Wait for expiration
        await asyncio.sleep(1.1)
        assert await short_ttl_cache.is_stale("test_key") is True
    
    @pytest.mark.asyncio
    async def test_get_stale_data(self, cache):
        """Test getting stale data."""
        # Create cache with very short TTL
        short_ttl_cache = MVPCache(max_size=10, default_ttl=1)
        
        await short_ttl_cache.set("test_key", "test_value")
        
        # Wait for expiration
        await asyncio.sleep(1.1)
        
        stale_data = await short_ttl_cache.get_stale_data("test_key")
        assert stale_data == "test_value"
    
    @pytest.mark.asyncio
    async def test_cleanup_expired(self, cache):
        """Test cleaning up expired entries."""
        # Create cache with very short TTL
        short_ttl_cache = MVPCache(max_size=10, default_ttl=1)
        
        await short_ttl_cache.set("key1", "value1")
        await short_ttl_cache.set("key2", "value2")
        
        # Wait for expiration
        await asyncio.sleep(1.1)
        
        # Clean up expired entries
        removed_count = await short_ttl_cache.cleanup_expired()
        assert removed_count == 2
        
        # Check that entries are gone
        assert await short_ttl_cache.get("key1") is None
        assert await short_ttl_cache.get("key2") is None 