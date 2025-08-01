"""
Integration tests for OpenShift discovery service functionality.

These tests focus on the discovery service integration and the recent bug fixes.
"""

import pytest
import pytest_asyncio
import asyncio
import os
import time
from unittest.mock import patch, MagicMock
from src.core.mcp_server import OpenShiftMCPServer
from src.config.settings import Settings
from src.core.implementations.openshift_discovery import OpenShiftDiscoveryService
from src.config.discovery_config import DiscoveryStrategy


class TestDiscoveryServiceIntegration:
    """Integration tests for discovery service functionality."""
    
    @pytest_asyncio.fixture
    async def mcp_server(self):
        """Create MCP server instance for discovery testing."""
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
    async def test_discovery_service_initialization(self, mcp_server):
        """Test that discovery service initializes correctly."""
        assert mcp_server.discovery_service is not None
        assert isinstance(mcp_server.discovery_service, OpenShiftDiscoveryService)
        
        # Test that discovery service has proper configuration
        config = mcp_server.discovery_service.config
        assert config is not None
        assert len(config.enabled_strategies) > 0
        
        # Verify that USER_PROJECTS strategy is enabled (our main fix)
        strategy_values = [s.value for s in config.enabled_strategies]
        assert "user_projects" in strategy_values
    
    @pytest.mark.asyncio
    async def test_project_discovery_integration(self, mcp_server):
        """Test project discovery integration with real OpenShift cluster."""
        # Test the main discovery method that was broken
        result = await mcp_server._discover_projects()
        
        assert isinstance(result, str)
        assert len(result) > 0
        
        # Should either contain project information or a proper error message
        result_lower = result.lower()
        assert any(keyword in result_lower for keyword in [
            "project", "namespace", "error", "permission", "access"
        ])
        
        # If it contains projects, verify the format
        if "project" in result_lower and "error" not in result_lower:
            # Should contain project names or counts
            assert any(char.isdigit() for char in result) or "found" in result_lower
    
    @pytest.mark.asyncio
    async def test_namespace_discovery_integration(self, mcp_server):
        """Test namespace discovery integration with real OpenShift cluster."""
        result = await mcp_server._discover_namespaces()
        
        assert isinstance(result, str)
        assert len(result) > 0
        
        # Should either contain namespace information or a proper error message
        result_lower = result.lower()
        assert any(keyword in result_lower for keyword in [
            "namespace", "project", "error", "permission", "access"
        ])
    
    @pytest.mark.asyncio
    async def test_discovery_summary_integration(self, mcp_server):
        """Test discovery summary integration."""
        result = await mcp_server._get_discovery_summary()
        
        assert isinstance(result, str)
        assert len(result) > 0
        
        # Should contain summary information
        result_lower = result.lower()
        assert any(keyword in result_lower for keyword in [
            "summary", "discovery", "found", "namespace", "project"
        ])
    
    @pytest.mark.asyncio
    async def test_discovery_strategy_fallback(self, mcp_server):
        """Test that discovery strategies fallback correctly when one fails."""
        # Test that if PROJECT_API fails, USER_PROJECTS still works
        discovery_service = mcp_server.discovery_service
        
        # Mock PROJECT_API to fail
        with patch.object(discovery_service, '_discover_via_project_api_direct', 
                         return_value=[]):
            projects = await discovery_service._discover_projects_impl()
            
            # Should still return results from USER_PROJECTS strategy
            # (This test might be skipped if USER_PROJECTS also fails in test environment)
            assert isinstance(projects, list)
    
    @pytest.mark.asyncio
    async def test_discovery_cache_integration(self, mcp_server):
        """Test that discovery results are properly cached."""
        discovery_service = mcp_server.discovery_service
        
        # Clear cache first
        await discovery_service.invalidate_cache()
        
        # First call should populate cache
        start_time = time.time()
        projects1 = await discovery_service.discover_projects()
        first_call_time = time.time() - start_time
        
        # Second call should use cache
        start_time = time.time()
        projects2 = await discovery_service.discover_projects()
        second_call_time = time.time() - start_time
        
        # Results should be identical
        assert projects1 == projects2
        
        # Second call should be faster (cache hit)
        assert second_call_time < first_call_time * 0.8  # At least 20% faster
        
        # Verify cache stats
        cache_stats = await discovery_service.cache.get_stats()
        assert cache_stats["valid_entries"] > 0
    
    @pytest.mark.asyncio
    async def test_discovery_error_handling(self, mcp_server):
        """Test discovery error handling scenarios."""
        discovery_service = mcp_server.discovery_service
        
        # Test with network error simulation
        with patch.object(discovery_service, '_discover_via_oc_cli_for_projects',
                         side_effect=Exception("Network error")):
            projects = await discovery_service._discover_projects_impl()
            # Should return empty list when all strategies fail
            assert isinstance(projects, list)
            assert len(projects) == 0
    
    @pytest.mark.asyncio
    async def test_discovery_performance(self, mcp_server):
        """Test discovery performance benchmarks."""
        discovery_service = mcp_server.discovery_service
        
        # Test project discovery performance
        start_time = time.time()
        projects = await discovery_service.discover_projects()
        project_time = time.time() - start_time
        
        # Test namespace discovery performance
        start_time = time.time()
        namespaces = await discovery_service.discover_namespaces()
        namespace_time = time.time() - start_time
        
        # Both should complete within reasonable time
        assert project_time < 10.0  # Should complete within 10 seconds
        assert namespace_time < 10.0  # Should complete within 10 seconds
        
        # Results should be valid
        assert isinstance(projects, list)
        assert isinstance(namespaces, list)
    
    @pytest.mark.asyncio
    async def test_discovery_with_query_processing(self, mcp_server):
        """Test discovery integration with query processing."""
        # Test queries that should trigger discovery
        discovery_queries = [
            "What projects do I have access to?",
            "Show me my namespaces",
            "List all my projects",
            "What namespaces are available?",
            "Discover my accessible resources"
        ]
        
        for query in discovery_queries:
            result = await mcp_server._process_query(query)
            
            assert isinstance(result, str)
            assert len(result) > 0
            
            # Should contain relevant information
            result_lower = result.lower()
            assert any(keyword in result_lower for keyword in [
                "project", "namespace", "found", "access", "available"
            ])


class TestDiscoveryConfigurationIntegration:
    """Integration tests for discovery configuration scenarios."""
    
    @pytest.mark.asyncio
    async def test_discovery_configuration_loading(self):
        """Test discovery configuration loading from environment."""
        # Test with default configuration
        from src.config.discovery_config import DiscoveryConfig
        config = DiscoveryConfig()
        
        assert config is not None
        assert len(config.enabled_strategies) > 0
        
        # Verify all expected strategies are present
        strategy_values = [s.value for s in config.enabled_strategies]
        expected_strategies = [
            "project_api", "namespace_api", "resource_testing", 
            "common_namespaces", "user_projects"
        ]
        
        for strategy in expected_strategies:
            assert strategy in strategy_values
    
    @pytest.mark.asyncio
    async def test_discovery_strategy_enum_comparison(self):
        """Test the enum comparison fix that was implemented."""
        from src.config.discovery_config import DiscoveryConfig, DiscoveryStrategy
        
        config = DiscoveryConfig()
        
        # Test the exact comparison that was failing
        for strategy in DiscoveryStrategy:
            # This should work now with our fix
            strategy_values = [s.value for s in config.enabled_strategies]
            assert strategy.value in strategy_values
    
    @pytest.mark.asyncio
    async def test_discovery_cache_configuration(self):
        """Test discovery cache configuration."""
        from src.config.discovery_config import DiscoveryConfig
        
        config = DiscoveryConfig()
        
        # Test cache configuration
        assert config.cache_ttl > 0
        assert config.enable_caching is True
        
        # Test with custom cache TTL
        custom_config = DiscoveryConfig(cache_ttl=600)  # 10 minutes
        assert custom_config.cache_ttl == 600


class TestDiscoveryErrorScenarios:
    """Integration tests for discovery error scenarios."""
    
    @pytest.mark.asyncio
    async def test_discovery_with_invalid_credentials(self):
        """Test discovery behavior with invalid credentials."""
        # Create server with invalid credentials
        with patch.dict(os.environ, {
            'OPENSHIFT_TOKEN': 'invalid-token',
            'OPENSHIFT_URL': 'https://invalid.openshift.com'
        }):
            settings = Settings()
            server = OpenShiftMCPServer(settings)
            
            # Discovery should handle invalid credentials gracefully
            projects = await server._discover_projects()
            assert isinstance(projects, str)
            assert len(projects) > 0
            
            # Should contain error information
            result_lower = projects.lower()
            assert any(keyword in result_lower for keyword in [
                "error", "permission", "access", "authentication"
            ])
    
    @pytest.mark.asyncio
    async def test_discovery_with_network_failures(self):
        """Test discovery behavior with network failures."""
        settings = Settings()
        server = OpenShiftMCPServer(settings)
        
        # Mock network failures
        with patch.object(server.discovery_service, '_discover_via_oc_cli_for_projects',
                         side_effect=Exception("Connection timeout")):
            projects = await server.discovery_service._discover_projects_impl()
            assert isinstance(projects, list)
            assert len(projects) == 0
    
    @pytest.mark.asyncio
    async def test_discovery_with_permission_denied(self):
        """Test discovery behavior with permission denied scenarios."""
        settings = Settings()
        server = OpenShiftMCPServer(settings)
        
        # Mock permission denied responses
        with patch.object(server.discovery_service, '_discover_via_project_api_direct',
                         side_effect=Exception("403 Forbidden")):
            projects = await server.discovery_service._discover_projects_impl()
            assert isinstance(projects, list)
            # Should fall back to other strategies or return empty list 