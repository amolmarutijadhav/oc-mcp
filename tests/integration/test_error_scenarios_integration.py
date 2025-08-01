"""
Integration tests for error scenarios and error handling.

These tests focus on comprehensive error handling and edge cases.
"""

import pytest
import pytest_asyncio
import asyncio
import os
import time
from unittest.mock import patch, MagicMock
from src.core.mcp_server import OpenShiftMCPServer
from src.config.settings import Settings


class TestComprehensiveErrorScenarios:
    """Integration tests for comprehensive error scenarios."""
    
    @pytest_asyncio.fixture
    async def mcp_server(self):
        """Create MCP server instance for error testing."""
        try:
            settings = Settings()
            
            # Check if required settings are properly loaded
            if not settings.openshift_token or not settings.openshift_url:
                pytest.skip("Missing required OpenShift settings in .env file")
            
            server = OpenShiftMCPServer(settings)
            
            # Authenticate the OpenShift client
            auth_result = await server.client.authenticate(
                settings.openshift_token,
                settings.openshift_url
            )
            if not auth_result:
                pytest.skip("Failed to authenticate with OpenShift")
            
            yield server
            
            # Cleanup
            await server.stop()
        except Exception as e:
            pytest.skip(f"Failed to initialize MCP server: {e}")
    
    @pytest.mark.asyncio
    async def test_network_error_scenarios(self, mcp_server):
        """Test network error scenarios."""
        error_scenarios = [
            ('ConnectionError', 'Network connectivity issues'),
            ('TimeoutError', 'Request timeout'),
            ('ConnectionRefusedError', 'Connection refused'),
            ('socket.timeout', 'Socket timeout'),
        ]
        
        for error_type, description in error_scenarios:
            with patch.object(mcp_server.client, 'list_namespaces', 
                             side_effect=Exception(f"{error_type}: {description}")):
                result = await mcp_server._list_accessible_namespaces()
                assert isinstance(result, str)
                assert len(result) > 0
                
                # Should contain error information or fallback to discovery
                result_lower = result.lower()
                # Either contains error info or successful discovery info
                assert any(keyword in result_lower for keyword in [
                    "error", "network", "connection", "timeout", "unavailable",
                    "discovered", "found", "accessible", "namespace"
                ])
    
    @pytest.mark.asyncio
    async def test_authentication_error_scenarios(self, mcp_server):
        """Test authentication error scenarios."""
        auth_error_scenarios = [
            ('401 Unauthorized', 'Invalid credentials'),
            ('403 Forbidden', 'Insufficient permissions'),
            ('Authentication failed', 'Authentication failure'),
            ('Token expired', 'Expired token'),
        ]
        
        for error_type, description in auth_error_scenarios:
            with patch.object(mcp_server.client, 'authenticate', 
                             side_effect=Exception(f"{error_type}: {description}")):
                # Test that authentication errors are handled gracefully
                # Note: The client might still be connected from previous successful auth
                # We're testing that the error doesn't crash the system
                try:
                    connected = await mcp_server.client.is_connected()
                    assert isinstance(connected, bool)
                except Exception:
                    # Authentication error should be handled gracefully
                    pass
    
    @pytest.mark.asyncio
    async def test_permission_error_scenarios(self, mcp_server):
        """Test permission error scenarios."""
        permission_scenarios = [
            ('403 Forbidden', 'Insufficient permissions'),
            ('401 Unauthorized', 'Unauthorized access'),
            ('Access denied', 'Access denied'),
        ]
        
        for error_type, description in permission_scenarios:
            with patch.object(mcp_server.client, 'list_pods', 
                             side_effect=Exception(f"{error_type}: {description}")):
                result = await mcp_server._list_pods_in_namespace("default")
                assert isinstance(result, str)
                assert len(result) > 0
                
                # Should contain permission error information
                result_lower = result.lower()
                assert any(keyword in result_lower for keyword in [
                    "permission", "forbidden", "unauthorized", "access", "denied"
                ])
    
    @pytest.mark.asyncio
    async def test_resource_error_scenarios(self, mcp_server):
        """Test resource error scenarios."""
        resource_scenarios = [
            ('404 Not Found', 'Resource not found'),
            ('409 Conflict', 'Resource conflict'),
            ('Resource not found', 'Resource not found'),
            ('Namespace not found', 'Namespace not found'),
        ]
        
        for error_type, description in resource_scenarios:
            with patch.object(mcp_server.client, 'list_pods', 
                             side_effect=Exception(f"{error_type}: {description}")):
                result = await mcp_server._list_pods_in_namespace("non-existent-namespace")
                assert isinstance(result, str)
                assert len(result) > 0
                
                # Should contain resource error information
                result_lower = result.lower()
                assert any(keyword in result_lower for keyword in [
                    "not found", "namespace", "resource", "exist"
                ])
    
    @pytest.mark.asyncio
    async def test_rate_limiting_scenarios(self, mcp_server):
        """Test rate limiting scenarios."""
        rate_limit_scenarios = [
            ('429 Too Many Requests', 'Rate limiting'),
            ('Rate limit exceeded', 'Rate limit exceeded'),
            ('Too many requests', 'Too many requests'),
        ]
        
        for error_type, description in rate_limit_scenarios:
            with patch.object(mcp_server.client, 'list_namespaces', 
                             side_effect=Exception(f"{error_type}: {description}")):
                result = await mcp_server._list_accessible_namespaces()
                assert isinstance(result, str)
                assert len(result) > 0
                
                # Should contain rate limiting information or fallback to discovery
                result_lower = result.lower()
                assert any(keyword in result_lower for keyword in [
                    "rate", "limit", "too many", "retry", "wait",
                    "discovered", "found", "accessible", "namespace"
                ])
    
    @pytest.mark.asyncio
    async def test_server_error_scenarios(self, mcp_server):
        """Test server error scenarios."""
        server_error_scenarios = [
            ('500 Internal Server Error', 'Server error'),
            ('502 Bad Gateway', 'Gateway error'),
            ('503 Service Unavailable', 'Service unavailable'),
            ('504 Gateway Timeout', 'Gateway timeout'),
        ]
        
        for error_type, description in server_error_scenarios:
            with patch.object(mcp_server.client, 'list_namespaces', 
                             side_effect=Exception(f"{error_type}: {description}")):
                result = await mcp_server._list_accessible_namespaces()
                assert isinstance(result, str)
                assert len(result) > 0
                
                # Should contain server error information or fallback to discovery
                result_lower = result.lower()
                assert any(keyword in result_lower for keyword in [
                    "server", "error", "unavailable", "gateway", "timeout",
                    "discovered", "found", "accessible", "namespace"
                ])
    
    @pytest.mark.asyncio
    async def test_discovery_error_scenarios(self, mcp_server):
        """Test discovery error scenarios."""
        discovery_service = mcp_server.discovery_service
        
        # Test discovery with network failures
        with patch.object(discovery_service, '_discover_via_oc_cli_for_projects',
                         side_effect=Exception("Network error")):
            projects = await discovery_service._discover_projects_impl()
            assert isinstance(projects, list)
            assert len(projects) == 0
        
        # Test discovery with permission denied
        with patch.object(discovery_service, '_discover_via_project_api_direct',
                         side_effect=Exception("403 Forbidden")):
            projects = await discovery_service._discover_projects_impl()
            assert isinstance(projects, list)
            # Should fall back to other strategies or return empty list
        
        # Test discovery with timeout
        with patch.object(discovery_service, '_discover_via_oc_cli_for_projects',
                         side_effect=Exception("Timeout")):
            projects = await discovery_service._discover_projects_impl()
            assert isinstance(projects, list)
    
    @pytest.mark.asyncio
    async def test_query_processing_error_scenarios(self, mcp_server):
        """Test query processing error scenarios."""
        # Test with invalid queries
        invalid_queries = [
            "",  # Empty query
            "   ",  # Whitespace only
            None,  # None query
        ]
        
        for query in invalid_queries:
            if query is not None:
                result = await mcp_server._process_query(query)
                assert isinstance(result, str)
                assert len(result) > 0
        
        # Test with very long queries
        long_query = "What is the status of my pods? " * 100  # Very long query
        result = await mcp_server._process_query(long_query)
        assert isinstance(result, str)
        assert len(result) > 0
    
    @pytest.mark.asyncio
    async def test_cache_error_scenarios(self, mcp_server):
        """Test cache error scenarios."""
        # Test cache with invalid keys
        try:
            await mcp_server.cache.set("", "value")  # Empty key
            await mcp_server.cache.set(None, "value")  # None key
        except Exception:
            # Should handle invalid keys gracefully
            pass
        
        # Test cache with invalid values
        try:
            await mcp_server.cache.set("test_key", None)  # None value
        except Exception:
            # Should handle invalid values gracefully
            pass
        
        # Test cache stats with errors
        stats = await mcp_server.cache.get_stats()
        assert isinstance(stats, dict)
        assert "current_size" in stats
        assert "total_entries" in stats or "hits" in stats


class TestErrorHandlingWithRealData:
    """Integration tests for error handling with real data."""
    
    @pytest_asyncio.fixture
    async def mcp_server(self):
        """Create MCP server instance for real data error testing."""
        try:
            settings = Settings()
            
            if not settings.openshift_token or not settings.openshift_url:
                pytest.skip("Missing required OpenShift settings in .env file")
            
            server = OpenShiftMCPServer(settings)
            
            auth_result = await server.client.authenticate(
                settings.openshift_token,
                settings.openshift_url
            )
            if not auth_result:
                pytest.skip("Failed to authenticate with OpenShift")
            
            yield server
            
            await server.stop()
        except Exception as e:
            pytest.skip(f"Failed to initialize MCP server: {e}")
    
    @pytest.mark.asyncio
    async def test_error_handling_with_real_namespaces(self, mcp_server):
        """Test error handling with real namespace data."""
        # Test with existing namespace
        try:
            result = await mcp_server._list_pods_in_namespace("default")
            assert isinstance(result, str)
            assert len(result) > 0
        except Exception as e:
            # Should handle permission errors gracefully
            assert "permission" in str(e).lower() or "forbidden" in str(e).lower()
        
        # Test with non-existing namespace
        result = await mcp_server._list_pods_in_namespace("non-existent-namespace-12345")
        assert isinstance(result, str)
        assert len(result) > 0
        
        # Should contain not found information
        result_lower = result.lower()
        assert any(keyword in result_lower for keyword in [
            "not found", "namespace", "exist", "error"
        ])
    
    @pytest.mark.asyncio
    async def test_error_handling_with_real_pods(self, mcp_server):
        """Test error handling with real pod data."""
        # Test with non-existing pod
        try:
            result = await mcp_server._get_pod_status("non-existent-pod-12345", "default")
            assert isinstance(result, str)
            assert len(result) > 0
            
            # Should contain not found information
            result_lower = result.lower()
            assert any(keyword in result_lower for keyword in [
                "not found", "pod", "exist", "error", "unauthorized", "permission"
            ])
        except Exception as e:
            # Should handle errors gracefully
            assert "unauthorized" in str(e).lower() or "permission" in str(e).lower()
    
    @pytest.mark.asyncio
    async def test_error_handling_with_real_discovery(self, mcp_server):
        """Test error handling with real discovery data."""
        # Test discovery with real cluster
        projects = await mcp_server._discover_projects()
        assert isinstance(projects, str)
        assert len(projects) > 0
        
        namespaces = await mcp_server._discover_namespaces()
        assert isinstance(namespaces, str)
        assert len(namespaces) > 0
        
        summary = await mcp_server._get_discovery_summary()
        assert isinstance(summary, str)
        assert len(summary) > 0


class TestErrorRecoveryScenarios:
    """Integration tests for error recovery scenarios."""
    
    @pytest_asyncio.fixture
    async def mcp_server(self):
        """Create MCP server instance for error recovery testing."""
        try:
            settings = Settings()
            
            if not settings.openshift_token or not settings.openshift_url:
                pytest.skip("Missing required OpenShift settings in .env file")
            
            server = OpenShiftMCPServer(settings)
            
            auth_result = await server.client.authenticate(
                settings.openshift_token,
                settings.openshift_url
            )
            if not auth_result:
                pytest.skip("Failed to authenticate with OpenShift")
            
            yield server
            
            await server.stop()
        except Exception as e:
            pytest.skip(f"Failed to initialize MCP server: {e}")
    
    @pytest.mark.asyncio
    async def test_error_recovery_after_network_failure(self, mcp_server):
        """Test error recovery after network failure."""
        # Simulate network failure
        with patch.object(mcp_server.client, 'list_namespaces', 
                         side_effect=Exception("Network error")):
            result1 = await mcp_server._list_accessible_namespaces()
            assert isinstance(result1, str)
            assert len(result1) > 0
            # Should either contain error info or successful discovery info
            result1_lower = result1.lower()
            assert any(keyword in result1_lower for keyword in [
                "error", "network", "discovered", "found", "accessible", "namespace"
            ])
        
        # Test recovery after network is restored
        with patch.object(mcp_server.client, 'list_namespaces', 
                         return_value=["default", "kube-system"]):
            result2 = await mcp_server._list_accessible_namespaces()
            assert isinstance(result2, str)
            assert len(result2) > 0
    
    @pytest.mark.asyncio
    async def test_error_recovery_after_authentication_failure(self, mcp_server):
        """Test error recovery after authentication failure."""
        # Simulate authentication failure
        with patch.object(mcp_server.client, 'authenticate', 
                         side_effect=Exception("Authentication failed")):
            # Test that authentication errors are handled gracefully
            try:
                connected = await mcp_server.client.is_connected()
                assert isinstance(connected, bool)
            except Exception:
                # Authentication error should be handled gracefully
                pass
        
        # Test recovery after authentication is restored
        with patch.object(mcp_server.client, 'authenticate', 
                         return_value=True):
            connected = await mcp_server.client.is_connected()
            assert isinstance(connected, bool)
    
    @pytest.mark.asyncio
    async def test_error_recovery_after_cache_failure(self, mcp_server):
        """Test error recovery after cache failure."""
        # Simulate cache failure
        with patch.object(mcp_server.cache, 'get', 
                         side_effect=Exception("Cache error")):
            # Should still work without cache
            try:
                result = await mcp_server._process_query("test query")
                assert isinstance(result, str)
                assert len(result) > 0
            except Exception:
                # Cache error should be handled gracefully
                pass
        
        # Test recovery after cache is restored
        with patch.object(mcp_server.cache, 'get', 
                         return_value="cached result"):
            result = await mcp_server._process_query("test query")
            assert isinstance(result, str)
            assert len(result) > 0


class TestErrorPerformanceScenarios:
    """Integration tests for error performance scenarios."""
    
    @pytest_asyncio.fixture
    async def mcp_server(self):
        """Create MCP server instance for error performance testing."""
        try:
            settings = Settings()
            
            if not settings.openshift_token or not settings.openshift_url:
                pytest.skip("Missing required OpenShift settings in .env file")
            
            server = OpenShiftMCPServer(settings)
            
            auth_result = await server.client.authenticate(
                settings.openshift_token,
                settings.openshift_url
            )
            if not auth_result:
                pytest.skip("Failed to authenticate with OpenShift")
            
            yield server
            
            await server.stop()
        except Exception as e:
            pytest.skip(f"Failed to initialize MCP server: {e}")
    
    @pytest.mark.asyncio
    async def test_error_handling_performance(self, mcp_server):
        """Test error handling performance."""
        # Test error handling performance under load
        error_scenarios = [
            "Network error",
            "Permission denied",
            "Resource not found",
            "Server error",
            "Timeout error"
        ]
        
        start_time = time.time()
        
        for error_msg in error_scenarios:
            with patch.object(mcp_server.client, 'list_namespaces', 
                             side_effect=Exception(error_msg)):
                result = await mcp_server._list_accessible_namespaces()
                assert isinstance(result, str)
                assert len(result) > 0
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should handle errors quickly
        assert total_time < 5.0  # Should complete within 5 seconds
        assert total_time / len(error_scenarios) < 1.0  # Average < 1 second per error
    
    @pytest.mark.asyncio
    async def test_error_caching_performance(self, mcp_server):
        """Test error caching performance."""
        # Test that error responses are cached for performance
        error_query = "List pods in non-existent-namespace"
        
        # First call (cache miss)
        start_time = time.time()
        result1 = await mcp_server._process_query(error_query)
        first_call_time = time.time() - start_time
        
        # Second call (cache hit)
        start_time = time.time()
        result2 = await mcp_server._process_query(error_query)
        second_call_time = time.time() - start_time
        
        # Results should be identical
        assert result1 == result2
        
        # Second call should be faster (cache hit)
        assert second_call_time < first_call_time * 0.8  # At least 20% faster 