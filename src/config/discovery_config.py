"""
Configuration for the OpenShift discovery service.

This module defines configuration settings for resource discovery
strategies, timeouts, and common namespaces to test.
"""

from dataclasses import dataclass, field
from typing import List
from enum import Enum


class DiscoveryStrategy(Enum):
    """Available discovery strategies in order of preference."""
    PROJECT_API = "project_api"
    NAMESPACE_API = "namespace_api"
    RESOURCE_TESTING = "resource_testing"
    COMMON_NAMESPACES = "common_namespaces"
    USER_PROJECTS = "user_projects"


@dataclass
class DiscoveryConfig:
    """Configuration for resource discovery."""
    
    # Discovery strategies (in order of preference)
    enabled_strategies: List[DiscoveryStrategy] = field(default_factory=lambda: [
        DiscoveryStrategy.PROJECT_API,
        DiscoveryStrategy.NAMESPACE_API,
        DiscoveryStrategy.RESOURCE_TESTING,
        DiscoveryStrategy.COMMON_NAMESPACES
    ])
    
    # Timeouts and limits
    discovery_timeout: int = 10
    max_concurrent_discoveries: int = 5
    cache_ttl: int = 300  # 5 minutes
    retry_attempts: int = 3
    retry_delay: float = 1.0  # seconds
    
    # Common namespaces to test (in order of likelihood)
    common_namespaces: List[str] = field(default_factory=lambda: [
        'default',
        'kube-system',
        'openshift-system',
        'openshift',
        'development',
        'test',
        'production',
        'demo',
        'sandbox',
        'workshop',
        'lab',
        'training',
        'user',
        'myproject'
    ])
    
    # OpenShift-specific settings
    openshift_project_label: str = 'openshift.io/display-name'
    openshift_description_label: str = 'openshift.io/description'
    enable_user_project_discovery: bool = True
    
    # Resource types to test
    resource_types_to_test: List[str] = field(default_factory=lambda: [
        'pod',
        'service',
        'deployment',
        'event'
    ])
    
    # Performance settings
    enable_caching: bool = True
    enable_metrics: bool = True
    enable_logging: bool = True
    
    # Error handling
    fail_fast: bool = False  # Continue trying strategies even if some fail
    log_failed_strategies: bool = True
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        if self.discovery_timeout <= 0:
            raise ValueError("discovery_timeout must be positive")
        
        if self.max_concurrent_discoveries <= 0:
            raise ValueError("max_concurrent_discoveries must be positive")
        
        if self.cache_ttl <= 0:
            raise ValueError("cache_ttl must be positive")
        
        if self.retry_attempts < 0:
            raise ValueError("retry_attempts must be non-negative")
        
        if self.retry_delay < 0:
            raise ValueError("retry_delay must be non-negative")


# Default configuration instance
DEFAULT_DISCOVERY_CONFIG = DiscoveryConfig()


def create_discovery_config_from_env() -> DiscoveryConfig:
    """Create discovery configuration from environment variables."""
    import os
    
    config = DiscoveryConfig()
    
    # Override with environment variables if present
    if os.getenv('DISCOVERY_TIMEOUT'):
        config.discovery_timeout = int(os.getenv('DISCOVERY_TIMEOUT'))
    
    if os.getenv('DISCOVERY_CACHE_TTL'):
        config.cache_ttl = int(os.getenv('DISCOVERY_CACHE_TTL'))
    
    if os.getenv('DISCOVERY_MAX_CONCURRENT'):
        config.max_concurrent_discoveries = int(os.getenv('DISCOVERY_MAX_CONCURRENT'))
    
    if os.getenv('DISCOVERY_RETRY_ATTEMPTS'):
        config.retry_attempts = int(os.getenv('DISCOVERY_RETRY_ATTEMPTS'))
    
    if os.getenv('DISCOVERY_RETRY_DELAY'):
        config.retry_delay = float(os.getenv('DISCOVERY_RETRY_DELAY'))
    
    if os.getenv('DISCOVERY_ENABLE_CACHING'):
        config.enable_caching = os.getenv('DISCOVERY_ENABLE_CACHING').lower() == 'true'
    
    if os.getenv('DISCOVERY_ENABLE_METRICS'):
        config.enable_metrics = os.getenv('DISCOVERY_ENABLE_METRICS').lower() == 'true'
    
    if os.getenv('DISCOVERY_ENABLE_LOGGING'):
        config.enable_logging = os.getenv('DISCOVERY_ENABLE_LOGGING').lower() == 'true'
    
    if os.getenv('DISCOVERY_FAIL_FAST'):
        config.fail_fast = os.getenv('DISCOVERY_FAIL_FAST').lower() == 'true'
    
    return config 