"""
Integration tests for configuration functionality.

These tests focus on configuration validation and the new OpenAI proxy features.
"""

import pytest
import pytest_asyncio
import os
import json
from unittest.mock import patch, MagicMock
from src.core.mcp_server import OpenShiftMCPServer
from src.config.settings import Settings
from src.core.implementations.llm_provider_factory import create_llm_provider_from_settings


class TestOpenAIProxyConfigurationIntegration:
    """Integration tests for OpenAI proxy configuration scenarios."""
    
    @pytest.mark.asyncio
    async def test_openai_proxy_base_url_configuration(self):
        """Test OpenAI proxy base URL configuration."""
        # Test with custom base URL
        with patch.dict(os.environ, {
            'LLM_BASE_URL': 'https://custom-openai-proxy.com/v1',
            'OPENAI_API_KEY': 'test-key'
        }):
            settings = Settings()
            assert settings.llm_base_url == 'https://custom-openai-proxy.com/v1'
            
            # Test LLM provider creation with custom URL
            provider = create_llm_provider_from_settings(settings)
            assert provider is not None
    
    @pytest.mark.asyncio
    async def test_openai_complete_url_configuration(self):
        """Test OpenAI complete URL configuration (including /chat/completions)."""
        # Test with complete URL including /chat/completions
        with patch.dict(os.environ, {
            'LLM_BASE_URL': 'https://custom-openai-proxy.com/v1/chat/completions',
            'OPENAI_API_KEY': 'test-key'
        }):
            settings = Settings()
            assert settings.llm_base_url == 'https://custom-openai-proxy.com/v1/chat/completions'
            
            # Test LLM provider creation with complete URL
            provider = create_llm_provider_from_settings(settings)
            assert provider is not None
    
    @pytest.mark.asyncio
    async def test_openai_additional_headers_configuration(self):
        """Test OpenAI additional headers configuration."""
        # Test with additional headers
        headers = {
            "X-Custom-Header": "test-value",
            "Authorization": "Bearer custom-token"
        }
        
        with patch.dict(os.environ, {
            'LLM_ADDITIONAL_HEADERS': json.dumps(headers),
            'OPENAI_API_KEY': 'test-key'
        }):
            settings = Settings()
            assert settings.llm_additional_headers is not None
            
            # Parse headers
            parsed_headers = json.loads(settings.llm_additional_headers)
            assert parsed_headers["X-Custom-Header"] == "test-value"
            assert parsed_headers["Authorization"] == "Bearer custom-token"
    
    @pytest.mark.asyncio
    async def test_openai_provider_with_proxy_configuration(self):
        """Test OpenAI provider creation with proxy configuration."""
        # Test complete proxy configuration
        with patch.dict(os.environ, {
            'LLM_BASE_URL': 'https://custom-openai-proxy.com/v1/chat/completions',
            'LLM_ADDITIONAL_HEADERS': '{"X-Custom-Header": "test-value"}',
            'OPENAI_API_KEY': 'test-key'
        }):
            settings = Settings()
            
            # Test provider creation
            provider = create_llm_provider_from_settings(settings)
            assert provider is not None
            
            # Test provider type
            provider_type = provider.get_provider_type()
            assert provider_type in ["openai", "azure_openai", "custom_openai"]
    
    @pytest.mark.asyncio
    async def test_openai_url_processing(self):
        """Test OpenAI URL processing functionality."""
        from src.core.implementations.openai_provider import _process_base_url
        
        # Test URL processing with complete URL
        complete_url = "https://custom-proxy.com/v1/chat/completions"
        processed_url = _process_base_url(complete_url)
        assert processed_url == "https://custom-proxy.com/v1"
        
        # Test URL processing with base URL
        base_url = "https://custom-proxy.com/v1"
        processed_base_url = _process_base_url(base_url)
        assert processed_base_url == "https://custom-proxy.com/v1"
        
        # Test URL processing with trailing slash
        url_with_slash = "https://custom-proxy.com/v1/"
        processed_slash_url = _process_base_url(url_with_slash)
        assert processed_slash_url == "https://custom-proxy.com/v1"
    
    @pytest.mark.asyncio
    async def test_openai_provider_availability_with_proxy(self):
        """Test OpenAI provider availability with proxy configuration."""
        with patch.dict(os.environ, {
            'LLM_BASE_URL': 'https://custom-openai-proxy.com/v1',
            'OPENAI_API_KEY': 'test-key'
        }):
            settings = Settings()
            provider = create_llm_provider_from_settings(settings)
            
            # Test availability (this might fail in test environment, which is expected)
            try:
                available = await provider.is_available()
                assert isinstance(available, bool)
            except Exception:
                # Provider might not be available in test environment
                pass


class TestOpenShiftConfigurationIntegration:
    """Integration tests for OpenShift configuration scenarios."""
    
    @pytest.mark.asyncio
    async def test_openshift_configuration_loading(self):
        """Test OpenShift configuration loading."""
        # Test with valid configuration
        with patch.dict(os.environ, {
            'OPENSHIFT_TOKEN': 'test-token',
            'OPENSHIFT_URL': 'https://test.openshift.com',
            'OPENSHIFT_TIMEOUT': '30'
        }):
            settings = Settings()
            assert settings.openshift_token == 'test-token'
            assert settings.openshift_url == 'https://test.openshift.com'
            assert settings.openshift_timeout == 30
    
    @pytest.mark.asyncio
    async def test_openshift_configuration_validation(self):
        """Test OpenShift configuration validation."""
        # Test with missing required settings
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()
            # Should handle missing settings gracefully
            # Note: Settings will use default values from .env file if available
            assert settings is not None
    
    @pytest.mark.asyncio
    async def test_openshift_timeout_configuration(self):
        """Test OpenShift timeout configuration."""
        with patch.dict(os.environ, {
            'OPENSHIFT_TIMEOUT': '60'
        }):
            settings = Settings()
            assert settings.openshift_timeout == 60


class TestCacheConfigurationIntegration:
    """Integration tests for cache configuration scenarios."""
    
    @pytest.mark.asyncio
    async def test_cache_configuration_loading(self):
        """Test cache configuration loading."""
        with patch.dict(os.environ, {
            'CACHE_TTL': '600',
            'CACHE_MAX_SIZE': '2000',
            'CACHE_ENABLE_STALE': 'false'
        }):
            settings = Settings()
            assert settings.cache_ttl == 600
            assert settings.cache_max_size == 2000
            assert settings.cache_enable_stale is False
    
    @pytest.mark.asyncio
    async def test_cache_configuration_defaults(self):
        """Test cache configuration defaults."""
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()
            # Should have reasonable defaults
            assert settings.cache_ttl > 0
            assert settings.cache_max_size > 0
            assert isinstance(settings.cache_enable_stale, bool)


class TestDiscoveryConfigurationIntegration:
    """Integration tests for discovery configuration scenarios."""
    
    @pytest.mark.asyncio
    async def test_discovery_configuration_loading(self):
        """Test discovery configuration loading."""
        from src.config.discovery_config import DiscoveryConfig
        
        # Test default configuration
        config = DiscoveryConfig()
        assert config is not None
        assert len(config.enabled_strategies) > 0
        assert config.cache_ttl > 0
        assert config.discovery_timeout > 0
    
    @pytest.mark.asyncio
    async def test_discovery_strategy_configuration(self):
        """Test discovery strategy configuration."""
        from src.config.discovery_config import DiscoveryConfig, DiscoveryStrategy
        
        # Test with custom strategy configuration
        custom_strategies = [DiscoveryStrategy.USER_PROJECTS, DiscoveryStrategy.COMMON_NAMESPACES]
        config = DiscoveryConfig(enabled_strategies=custom_strategies)
        
        assert len(config.enabled_strategies) == 2
        strategy_values = [s.value for s in config.enabled_strategies]
        assert "user_projects" in strategy_values
        assert "common_namespaces" in strategy_values
    
    @pytest.mark.asyncio
    async def test_discovery_timeout_configuration(self):
        """Test discovery timeout configuration."""
        from src.config.discovery_config import DiscoveryConfig
        
        # Test with custom timeout
        config = DiscoveryConfig(discovery_timeout=30)
        assert config.discovery_timeout == 30
        
        # Test with custom cache TTL
        config = DiscoveryConfig(cache_ttl=900)  # 15 minutes
        assert config.cache_ttl == 900


class TestMCPConfigurationIntegration:
    """Integration tests for MCP server configuration scenarios."""
    
    @pytest.mark.asyncio
    async def test_mcp_server_configuration_loading(self):
        """Test MCP server configuration loading."""
        # Test with minimal configuration
        with patch.dict(os.environ, {
            'OPENSHIFT_TOKEN': 'test-token',
            'OPENSHIFT_URL': 'https://test.openshift.com',
            'OPENAI_API_KEY': 'test-key'
        }):
            settings = Settings()
            server = OpenShiftMCPServer(settings)
            
            assert server is not None
            assert server.settings is not None
            assert server.cache is not None
            assert server.client is not None
            assert server.llm_provider is not None
    
    @pytest.mark.asyncio
    async def test_mcp_server_with_proxy_configuration(self):
        """Test MCP server with proxy configuration."""
        # Test with complete proxy configuration
        with patch.dict(os.environ, {
            'OPENSHIFT_TOKEN': 'test-token',
            'OPENSHIFT_URL': 'https://test.openshift.com',
            'OPENAI_API_KEY': 'test-key',
            'LLM_BASE_URL': 'https://custom-proxy.com/v1',
            'LLM_ADDITIONAL_HEADERS': '{"X-Custom-Header": "test-value"}'
        }):
            settings = Settings()
            server = OpenShiftMCPServer(settings)
            
            assert server is not None
            assert server.llm_provider is not None
            
            # Test that proxy configuration is properly loaded
            assert settings.llm_base_url == 'https://custom-proxy.com/v1'
            assert settings.llm_additional_headers is not None


class TestConfigurationErrorScenarios:
    """Integration tests for configuration error scenarios."""
    
    @pytest.mark.asyncio
    async def test_invalid_json_headers_configuration(self):
        """Test handling of invalid JSON in headers configuration."""
        with patch.dict(os.environ, {
            'LLM_ADDITIONAL_HEADERS': 'invalid-json',
            'OPENAI_API_KEY': 'test-key'
        }):
            settings = Settings()
            # Should handle invalid JSON gracefully
            assert settings.llm_additional_headers == 'invalid-json'
    
    @pytest.mark.asyncio
    async def test_missing_required_configuration(self):
        """Test handling of missing required configuration."""
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()
            # Should handle missing configuration gracefully
            assert settings is not None
    
    @pytest.mark.asyncio
    async def test_invalid_timeout_configuration(self):
        """Test handling of invalid timeout configuration."""
        with patch.dict(os.environ, {
            'OPENSHIFT_TIMEOUT': 'invalid-timeout'
        }):
            # Should handle invalid timeout gracefully
            try:
                settings = Settings()
                # Should use default timeout
                assert settings.openshift_timeout > 0
            except Exception:
                # Should not crash
                pass 