# OpenAI Proxy Configuration Guide

This guide explains how to configure the OpenShift MCP Server to use your organization's OpenAI proxy instead of the direct OpenAI API.

## Overview

The system now supports complete URL externalization for OpenAI, allowing you to:
- Use your organization's proxy URL instead of direct OpenAI API
- Add custom headers for authentication and organization-specific requirements
- Maintain the same OpenAI API interface while routing through your proxy

## Configuration Options

### 1. Complete OpenAI API URL Configuration

Set your organization's complete OpenAI API URL using the `LLM_BASE_URL` environment variable:

```bash
# Use your organization's OpenAI proxy
# You can specify the URL up to /chat/completions - it will be automatically processed
LLM_BASE_URL=https://openai-proxy.your-company.com/v1/chat/completions
LLM_BASE_URL=https://openai-proxy.your-company.com/v1
```

### 2. Additional Headers Configuration

Add custom headers for authentication, organization ID, or other requirements:

```bash
# JSON format for custom headers
LLM_ADDITIONAL_HEADERS={"X-Organization": "your-org-id", "X-Proxy-Auth": "proxy-token"}
```

## Complete Configuration Examples

### Example 1: Basic Organizational Proxy

```bash
# Environment variables
LLM_PROVIDER_TYPE=openai
OPENAI_API_KEY=your-openai-api-key
LLM_BASE_URL=https://openai-proxy.your-company.com/v1/chat/completions
```

### Example 2: Organizational Proxy with Custom Headers

```bash
# Environment variables
LLM_PROVIDER_TYPE=openai
OPENAI_API_KEY=your-openai-api-key
LLM_BASE_URL=https://openai-proxy.your-company.com/v1/chat/completions
LLM_ADDITIONAL_HEADERS={"X-Organization": "your-org-id", "X-Proxy-Auth": "proxy-token", "X-Client-ID": "your-client-id"}
```

### Example 3: Using .env file

Create a `.env` file in your project root:

```env
# OpenShift Configuration
OPENSHIFT_TOKEN=your_openshift_token_here
OPENSHIFT_URL=https://your-cluster.openshift.com:6443

# LLM Provider Configuration
LLM_PROVIDER_TYPE=openai
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4
OPENAI_TIMEOUT=30

# Complete OpenAI API URL Configuration
LLM_BASE_URL=https://openai-proxy.your-company.com/v1/chat/completions
LLM_ADDITIONAL_HEADERS={"X-Organization": "your-org-id", "X-Proxy-Auth": "proxy-token"}
```

### Example 4: MCP Configuration (mcp.json)

```json
{
  "mcpServers": {
    "openshift-mcp-server": {
      "command": "python",
      "args": ["run_mcp_server.py"],
      "env": {
        "OPENSHIFT_TOKEN": "${OPENSHIFT_TOKEN}",
        "OPENSHIFT_URL": "${OPENSHIFT_URL}",
        "LLM_PROVIDER_TYPE": "openai",
        "OPENAI_API_KEY": "${OPENAI_API_KEY}",
        "LLM_BASE_URL": "https://openai-proxy.your-company.com/v1/chat/completions",
        "LLM_ADDITIONAL_HEADERS": "{\"X-Organization\": \"your-org-id\", \"X-Proxy-Auth\": \"proxy-token\"}"
      }
    }
  }
}
```

## Implementation Details

### What Was Added

1. **Settings Configuration**: Added `llm_additional_headers` field to support custom headers
2. **Factory Implementation**: Enhanced the LLM provider factory to parse and pass additional headers
3. **OpenAI Provider**: Enhanced to support URLs up to `/chat/completions` with automatic processing
4. **Documentation**: Updated examples and configuration guides

### Key Features

- **JSON Header Parsing**: Headers are parsed from JSON string format
- **Error Handling**: Graceful handling of malformed JSON headers
- **Logging**: Comprehensive logging for debugging configuration issues
- **Backward Compatibility**: Existing configurations continue to work unchanged

## Testing Your Configuration

To verify your proxy configuration is working:

1. Set up your environment variables as shown in the examples above
2. Run the MCP server
3. Check the logs for successful provider initialization
4. Test with a simple query to ensure the proxy is being used

## Troubleshooting

### Common Issues

1. **Invalid JSON Headers**: Ensure your `LLM_ADDITIONAL_HEADERS` is valid JSON
2. **Complete URL Format**: You can specify URLs up to `/chat/completions` - they will be automatically processed
3. **Authentication**: Verify your API key and any proxy authentication headers are correct

### Debug Information

The system logs the following information during initialization:
- Provider type
- Complete OpenAI API URL
- Model configuration
- Timeout settings
- Additional headers (if configured)

## Migration from Direct OpenAI

If you're currently using direct OpenAI API, simply add these environment variables:

```bash
# Add these to your existing configuration
LLM_BASE_URL=https://openai-proxy.your-company.com/v1/chat/completions
LLM_ADDITIONAL_HEADERS={"X-Organization": "your-org-id"}
```

No code changes are required - the system will automatically use your complete OpenAI API URL instead of the default OpenAI API endpoint.

## Security Considerations

- Store sensitive headers in environment variables, not in code
- Use secure methods to pass API keys and tokens
- Consider using a secrets management system for production deployments
- Ensure your proxy endpoint uses HTTPS in production

## Support

For additional help with proxy configuration, refer to:
- `docs/LLM_PROVIDER_CONFIGURATION.md` - Detailed provider configuration guide
- `env.example` - Complete environment variable reference
- `mcp.json.example` - MCP configuration examples 