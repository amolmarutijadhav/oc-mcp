# Tools Directory

This directory contains development tools, scripts, and utilities for the OpenShift MCP Server.

## Structure

```
tools/
├── scripts/           # Production and development scripts
│   ├── run_server.py  # Main server runner
│   ├── setup_environment.py  # Environment setup
│   └── run_server.py  # Alternative server runner
├── debug/             # Debug and test scripts
│   ├── test_*.py      # Debug test scripts
│   └── *.json         # Debug output files
└── utilities/         # Utility scripts and tools
```

## Scripts

### Production Scripts
- `scripts/run_server.py`: Main MCP server runner
- `scripts/setup_environment.py`: Environment setup and configuration
- `scripts/run_server.py`: Alternative server runner

### Debug Scripts
- `debug/test_discovery_config.py`: Discovery configuration testing
- `debug/test_mcp_discovery.py`: MCP discovery testing
- `debug/test_verbose_discovery.py`: Verbose discovery testing
- `debug/test_cache_clear.py`: Cache clearing testing
- `debug/test_oc_cli_direct_call.py`: OC CLI direct testing
- `debug/test_query_processing.py`: Query processing testing
- `debug/test_mcp_query.py`: MCP query testing
- `debug/test_mcp_interaction.py`: MCP interaction testing
- `debug/test_llm_providers.py`: LLM providers testing

### Debug Output Files
- `debug/*.json`: Integration test reports and debug outputs

## Usage

### Running Production Scripts
```bash
# Run the MCP server
python tools/scripts/run_server.py

# Setup environment
python tools/scripts/setup_environment.py
```

### Running Debug Scripts
```bash
# Test discovery configuration
python tools/debug/test_discovery_config.py

# Test MCP discovery
python tools/debug/test_mcp_discovery.py
```

### Using Makefile
```bash
# Run server (uses tools/scripts/run_server.py)
make run

# Setup environment (uses tools/scripts/setup_environment.py)
make setup

# Run debug scripts
make debug
```

## Notes

- Debug scripts are for development and testing purposes only
- Debug output files (*.json) contain test results and should not be committed
- Production scripts are safe to run in any environment
- Always check script dependencies before running 