# OpenShift MCP Server Setup Guide

## Overview

The OpenShift MCP Server provides a Model Context Protocol (MCP) interface to interact with OpenShift clusters using natural language queries. This guide explains how to set up and use the MCP server.

## Prerequisites

1. **Python 3.8+** installed
2. **OpenShift Cluster** access with valid token
3. **OpenAI API Key** (or other supported LLM provider)
4. **MCP Client** (Claude Desktop, MCP CLI, etc.)

## Installation

1. **Clone and setup the project:**
   ```bash
   git clone <your-repo-url>
   cd oc-mcp
   pip install -r requirements.txt
   ```

2. **Set up environment variables:**
   ```bash
   cp env.example .env
   # Edit .env with your credentials
   ```

## Configuration

### Environment Variables

Create a `.env` file with the following variables:

```bash
# OpenShift Configuration
OPENSHIFT_TOKEN=your_openshift_token_here
OPENSHIFT_URL=https://your-cluster.openshift.com:6443
OPENSHIFT_TIMEOUT=30

# LLM Provider Configuration
LLM_PROVIDER_TYPE=openai  # openai, azure_openai, custom_openai, anthropic, google, custom
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4
OPENAI_TIMEOUT=30
OPENAI_TEMPERATURE=0.7
OPENAI_MAX_TOKENS=1000

# Optional: Custom LLM Base URL (for custom providers)
LLM_BASE_URL=https://your-custom-llm-endpoint.com/v1

# Cache Configuration
CACHE_TTL=300
CACHE_MAX_SIZE=1000
CACHE_ENABLE_STALE=true

# Server Configuration
SERVER_TIMEOUT=30
LOG_LEVEL=INFO
```

### MCP Configuration

Create an `mcp.json` file for your MCP client:

```json
{
  "mcpServers": {
    "openshift-mcp-server": {
      "command": "python",
      "args": ["run_mcp_server.py"],
      "env": {
        "OPENSHIFT_TOKEN": "${OPENSHIFT_TOKEN}",
        "OPENSHIFT_URL": "${OPENSHIFT_URL}",
        "OPENAI_API_KEY": "${OPENAI_API_KEY}",
        "OPENAI_MODEL": "gpt-4",
        "OPENAI_TIMEOUT": "30",
        "OPENAI_TEMPERATURE": "0.7",
        "OPENAI_MAX_TOKENS": "1000",
        "CACHE_TTL": "300",
        "CACHE_MAX_SIZE": "1000",
        "SERVER_TIMEOUT": "30",
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

## Usage

### 1. Testing the Server

Run the server directly to test functionality:

```bash
python run_mcp_server.py
```

This will:
- Test OpenShift authentication
- Test LLM provider availability
- Test cache functionality
- Test query processing

### 2. Using with MCP Clients

#### Claude Desktop

1. Copy `mcp.json` to your Claude Desktop configuration directory
2. Restart Claude Desktop
3. The OpenShift MCP Server will be available as a tool

#### MCP CLI

```bash
# Install MCP CLI
pip install mcp

# Run with the server
mcp --server python run_mcp_server.py
```

#### Other MCP Clients

Place the `mcp.json` file in the appropriate configuration directory for your MCP client.

### 3. Available Tools

The MCP server provides the following tools:

#### `query_openshift`
Query OpenShift cluster using natural language.

**Examples:**
- "What is the status of my pods?"
- "List pods in namespace default"
- "Show me available namespaces"
- "What is the status of pod my-app in namespace production?"

#### `get_pod_status`
Get detailed status of a specific pod.

**Parameters:**
- `pod_name` (required): Name of the pod
- `namespace` (optional): Namespace (defaults to "default")

## Supported LLM Providers

### OpenAI
```bash
LLM_PROVIDER_TYPE=openai
OPENAI_API_KEY=your_api_key
```

### Azure OpenAI
```bash
LLM_PROVIDER_TYPE=azure_openai
OPENAI_API_KEY=your_api_key
LLM_BASE_URL=https://your-resource.openai.azure.com
LLM_API_VERSION=2024-02-15-preview
LLM_DEPLOYMENT_NAME=your-deployment-name
```

### Custom OpenAI-Compatible
```bash
LLM_PROVIDER_TYPE=custom_openai
OPENAI_API_KEY=your_api_key
LLM_BASE_URL=https://your-custom-endpoint.com/v1
```

## Troubleshooting

### Common Issues

1. **Authentication Failed**
   - Verify your OpenShift token is valid
   - Check the OpenShift URL format
   - Ensure you have proper permissions

2. **LLM Provider Unavailable**
   - Verify your API key is correct
   - Check network connectivity
   - Verify the LLM provider configuration

3. **Permission Denied Errors**
   - The server respects OpenShift RBAC
   - You can only access resources you have permission to view
   - Check your OpenShift permissions

### Logs

The server uses structured logging. Set `LOG_LEVEL=DEBUG` for detailed logs:

```bash
LOG_LEVEL=DEBUG
```

### Testing

Run the test suite to verify everything is working:

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test categories
python -m pytest tests/unit/ -v
python -m pytest tests/integration/ -v
python -m pytest tests/manual/ -v
```

## Development

### Project Structure

```
oc-mcp/
├── src/
│   ├── core/
│   │   ├── interfaces/          # Abstract interfaces
│   │   ├── implementations/     # Concrete implementations
│   │   └── mcp_server.py       # Main MCP server
│   └── config/
│       └── settings.py         # Configuration management
├── tests/                      # Test suite
├── scripts/                    # Utility scripts
├── mcp.json                    # MCP client configuration
├── env.example                 # Environment template
└── requirements.txt            # Dependencies
```

### Adding New Tools

1. Define the tool in `src/core/mcp_server.py`
2. Add the implementation method
3. Update tests
4. Update documentation

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## Security Considerations

- Never commit API keys or tokens to version control
- Use environment variables for sensitive configuration
- The server respects OpenShift RBAC permissions
- Consider using service accounts for production deployments

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review the logs with `LOG_LEVEL=DEBUG`
3. Run the test suite to verify functionality
4. Open an issue on the repository 