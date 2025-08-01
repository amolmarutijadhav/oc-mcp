# LLM Provider Configuration Guide

This document explains how to configure different LLM providers for the OpenShift MCP Server.

## Overview

The OpenShift MCP Server supports multiple LLM providers through a flexible configuration system. You can easily switch between different providers by changing environment variables.

## Supported Provider Types

### 1. OpenAI (Default)
- **Provider Type**: `openai`
- **Description**: Standard OpenAI API
- **Use Case**: Production OpenAI usage

### 2. Azure OpenAI
- **Provider Type**: `azure_openai`
- **Description**: Microsoft Azure OpenAI Service
- **Use Case**: Enterprise Azure environments

### 3. Custom OpenAI-Compatible
- **Provider Type**: `custom_openai`
- **Description**: Any API that mimics OpenAI's interface
- **Use Case**: Self-hosted models, local LLMs, other providers

### 4. Anthropic (Planned)
- **Provider Type**: `anthropic`
- **Description**: Claude API
- **Use Case**: Alternative to OpenAI

### 5. Google (Planned)
- **Provider Type**: `google`
- **Description**: Google Gemini API
- **Use Case**: Google Cloud environments

### 6. Custom (Planned)
- **Provider Type**: `custom`
- **Description**: Completely custom provider
- **Use Case**: Proprietary or specialized LLM services

## Configuration Options

### Basic Configuration

```bash
# Choose your provider type
LLM_PROVIDER_TYPE=openai

# API Key (required for all providers)
OPENAI_API_KEY=your_api_key_here

# Model name
OPENAI_MODEL=gpt-4

# Timeout settings
OPENAI_TIMEOUT=30
OPENAI_TEMPERATURE=0.7
OPENAI_MAX_TOKENS=1000
```

### Complete OpenAI API URL

For any provider that supports custom URLs:

```bash
# Complete OpenAI API URL (overrides default OpenAI URL)
# You can specify the URL up to /chat/completions - it will be automatically processed
LLM_BASE_URL=https://openai-proxy.your-company.com/v1/chat/completions
LLM_BASE_URL=https://openai-proxy.your-company.com/v1
```

### Azure OpenAI Configuration

```bash
# Provider type
LLM_PROVIDER_TYPE=azure_openai

# Azure-specific settings
LLM_BASE_URL=https://your-resource.openai.azure.com/openai/deployments/chat/completions
LLM_BASE_URL=https://your-resource.openai.azure.com/openai/deployments
LLM_API_VERSION=2024-02-15-preview
LLM_DEPLOYMENT_NAME=your-deployment-name
```

### Custom Headers

For providers requiring additional headers:

```bash
# JSON format for custom headers
LLM_ADDITIONAL_HEADERS={"X-Custom-Header": "value", "Authorization": "Bearer token"}
```

## Configuration Examples

### Example 1: Standard OpenAI

```bash
LLM_PROVIDER_TYPE=openai
OPENAI_API_KEY=sk-your-openai-key
OPENAI_MODEL=gpt-4
```

### Example 2: Azure OpenAI

```bash
LLM_PROVIDER_TYPE=azure_openai
OPENAI_API_KEY=your-azure-api-key
LLM_BASE_URL=https://your-resource.openai.azure.com/openai/deployments/chat/completions
LLM_API_VERSION=2024-02-15-preview
LLM_DEPLOYMENT_NAME=gpt-4-deployment
```

### Example 3: Self-Hosted OpenAI-Compatible

```bash
LLM_PROVIDER_TYPE=custom_openai
OPENAI_API_KEY=your-api-key
LLM_BASE_URL=https://your-self-hosted-llm.com/v1
OPENAI_MODEL=gpt-4
```

### Example 4: Local LLM (e.g., Ollama)

```bash
LLM_PROVIDER_TYPE=custom_openai
OPENAI_API_KEY=dummy-key
LLM_BASE_URL=http://localhost:11434/v1
OPENAI_MODEL=llama2
```

### Example 5: Enterprise LLM Service

```bash
LLM_PROVIDER_TYPE=custom_openai
OPENAI_API_KEY=your-enterprise-key
LLM_BASE_URL=https://llm.your-company.com/v1
LLM_ADDITIONAL_HEADERS={"X-API-Version": "2024-01-01", "X-Client-ID": "your-client-id"}
```

### Example 6: Organizational OpenAI Proxy

```bash
# Use your organization's OpenAI proxy instead of direct OpenAI API
LLM_PROVIDER_TYPE=openai
OPENAI_API_KEY=your-openai-api-key
LLM_BASE_URL=https://openai-proxy.your-company.com/v1/chat/completions
LLM_ADDITIONAL_HEADERS={"X-Organization": "your-org-id", "X-Proxy-Auth": "proxy-token"}
```

## Architecture Benefits

### 1. **Environment-Based Configuration**
- Easy switching between environments (dev, staging, prod)
- No code changes required
- Supports different providers per environment

### 2. **Strategy Pattern**
- Clean separation of concerns
- Easy to add new providers
- Consistent interface across providers

### 3. **Factory Pattern**
- Centralized provider creation
- Runtime provider selection
- Configuration validation

### 4. **Extensibility**
- Easy to add new provider types
- Custom configuration options
- Plugin-like architecture

## Implementation Details

### Provider Factory

The `LLMProviderFactory` creates provider instances based on configuration:

```python
factory = LLMProviderFactory()
provider = factory.create_provider(config)
```

### Configuration Loading

Settings are loaded from environment variables with fallbacks:

```python
config = LLMConfig(
    provider_type=LLMProviderType.OPENAI,
    api_key=settings.openai_api_key,
    base_url=settings.llm_base_url,
    # ... other settings
)
```

### Error Handling

Each provider includes specific error handling:

- **404**: Endpoint not found
- **401**: Authentication failed
- **403**: Access denied
- **Custom**: Provider-specific errors

## Migration Guide

### From OpenAI to Azure OpenAI

1. Update environment variables:
```bash
LLM_PROVIDER_TYPE=azure_openai
LLM_BASE_URL=https://your-resource.openai.azure.com/openai/deployments/chat/completions
LLM_API_VERSION=2024-02-15-preview
LLM_DEPLOYMENT_NAME=your-deployment
```

2. Restart the server

### From OpenAI to Custom Provider

1. Update environment variables:
```bash
LLM_PROVIDER_TYPE=custom_openai
LLM_BASE_URL=https://your-custom-endpoint.com/v1
```

2. Ensure your custom endpoint follows OpenAI's API format
3. Restart the server

## Troubleshooting

### Common Issues

1. **Provider not found**: Check `LLM_PROVIDER_TYPE` value
2. **Authentication failed**: Verify API key and base URL
3. **Endpoint not found**: Check `LLM_BASE_URL` format (can include /chat/completions, will be automatically processed)
4. **Model not found**: Verify model name for your provider

### Debug Mode

Enable debug logging to see provider initialization:

```bash
LOG_LEVEL=DEBUG
```

### Testing Providers

Use the test script to verify provider configuration:

```bash
python test_mcp_interaction.py
```

## Future Enhancements

### Planned Features

1. **Anthropic Provider**: Claude API integration
2. **Google Provider**: Gemini API integration
3. **Custom Provider**: Generic provider interface
4. **Provider Health Checks**: Automatic provider availability testing
5. **Load Balancing**: Multiple provider support
6. **Fallback Providers**: Automatic failover

### Contributing

To add a new provider:

1. Implement the `ILLMProvider` interface
2. Add provider type to `LLMProviderType` enum
3. Update factory to handle new provider
4. Add configuration options to settings
5. Update documentation

## Security Considerations

1. **API Key Management**: Use secure key management systems
2. **Network Security**: Ensure secure connections to LLM providers
3. **Data Privacy**: Be aware of data sent to external providers
4. **Rate Limiting**: Implement appropriate rate limiting
5. **Audit Logging**: Log provider usage for compliance 