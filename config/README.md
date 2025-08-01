# Configuration Directory

This directory contains configuration files and templates for the OpenShift MCP Server.

## Structure

```
config/
├── examples/          # Example configuration files
│   ├── env.example    # Environment variables template
│   └── mcp.json.example  # MCP server configuration template
└── templates/         # Configuration templates (future use)
```

## Usage

### Environment Configuration
1. Copy `examples/env.example` to `.env` in the project root
2. Update the values according to your environment

### MCP Server Configuration
1. Copy `examples/mcp.json.example` to `mcp.json` in the project root
2. Update the configuration for your MCP server setup

## Configuration Options

### Environment Variables (.env)
- `OPENSHIFT_TOKEN`: Your OpenShift authentication token
- `OPENSHIFT_URL`: OpenShift cluster URL
- `OPENAI_API_KEY`: OpenAI API key
- `LLM_BASE_URL`: Custom OpenAI proxy URL (optional)
- `LLM_ADDITIONAL_HEADERS`: Additional HTTP headers (optional)

### MCP Server Configuration (mcp.json)
- Server host and port settings
- Timeout configurations
- Logging settings
- Cache configurations

For detailed configuration options, see the main [README.md](../README.md) and [MCP_SETUP.md](../MCP_SETUP.md). 