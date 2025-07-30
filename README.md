# OpenShift MCP Server

A high-performance Model Context Protocol (MCP) server for OpenShift that enables LLMs and chatbots to query OpenShift clusters using natural language with sub-second response times.

## 🚀 Features

- **Fast Response Times**: <500ms for cached queries, <2s for fresh queries
- **Natural Language Queries**: Convert user queries to OpenShift operations
- **Multi-Layer Caching**: In-memory caching with background refresh
- **LLM Integration**: OpenAI provider with extensible architecture
- **MCP Compliance**: Full MCP server specification implementation
- **Testable Design**: 90% unit test coverage with comprehensive mocking

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   LLM/Chatbot   │◄──►│  MCP Server     │◄──►│  OpenShift API  │
│   (OpenAI)      │    │  (Our Code)     │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Response       │    │  Cache Layer    │    │  Background     │
│  Templates      │    │  (Memory)       │    │  Refresh        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📋 Requirements

- Python 3.11+
- OpenShift cluster access
- OpenAI API key
- OpenShift token

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd oc-mcp
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Run the server**
   ```bash
   python -m src.core.mcp_server
   ```

## ⚙️ Configuration

Create a `.env` file with the following variables:

```env
# OpenShift Configuration
OPENSHIFT_TOKEN=your_openshift_token
OPENSHIFT_URL=https://your-cluster.com
OPENSHIFT_TIMEOUT=30

# LLM Configuration
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4
OPENAI_TIMEOUT=30

# Cache Configuration
CACHE_TTL=300
CACHE_MAX_SIZE=1000

# Server Configuration
SERVER_TIMEOUT=30
LOG_LEVEL=INFO
```

## 🎯 Usage

### Basic Usage

```python
from src.core.mcp_server import OpenShiftMCPServer
from src.config.settings import Settings

# Load configuration
settings = Settings()

# Create server instance
server = OpenShiftMCPServer(settings)

# Start server
await server.start()
```

### Example Queries

- "Show me all pods in the default namespace"
- "What's the status of the myapp pod?"
- "List all services in the production project"
- "Get logs from the database pod"

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
make test

# Run specific test categories
make test-unit         # Unit tests only
make test-integration  # Integration tests only
make test-manual       # Manual verification tests

# Run with coverage
pytest --cov=src

# Or use pytest directly
pytest tests/unit/
pytest tests/integration/
```

## 📊 Performance

| Query Type | Cached Response | Fresh Response | Cache Hit Rate |
|------------|----------------|----------------|----------------|
| Pod List   | <200ms         | <2s            | >85%           |
| Pod Status | <100ms         | <1s            | >90%           |
| Services   | <150ms         | <1.5s          | >80%           |
| Logs       | <500ms         | <3s            | >75%           |

## 🔧 Development

### Project Structure

```
oc-mcp/
├── src/
│   ├── core/
│   │   ├── interfaces/           # Abstract base classes
│   │   ├── implementations/      # Concrete implementations
│   │   └── mcp_server.py         # Main MCP server
│   └── config/                   # Configuration
├── tests/
│   ├── unit/                     # Unit tests
│   ├── integration/              # Integration tests
│   └── manual/                   # Manual verification tests
├── scripts/                      # Utility scripts
│   ├── run_server.py            # Server runner
│   └── setup_environment.py     # Environment setup
├── examples/                     # Usage examples
├── Makefile                      # Development tasks
└── requirements.txt              # Dependencies
```

### Design Patterns

- **Strategy Pattern**: LLM provider abstraction
- **Factory Pattern**: LLM provider creation
- **Template Pattern**: Response formatting
- **Adapter Pattern**: MCP to LLM tool conversion

### Adding New Features

1. **New LLM Provider**: Implement `ILLMProvider` interface
2. **New OpenShift Resource**: Add to `IOpenShiftClient` interface
3. **New Response Template**: Create template class
4. **New MCP Tool**: Add tool method to server

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details

## 🆘 Support

- **Issues**: Create an issue on GitHub
- **Documentation**: Check the docs/ directory
- **Examples**: See the examples/ directory

## 🗺️ Roadmap

### MVP (Current)
- ✅ Basic OpenShift queries
- ✅ OpenAI integration
- ✅ Multi-layer caching
- ✅ MCP compliance

### Phase 2
- 🔄 Multi-cluster support
- 🔄 Advanced LLM providers
- 🔄 Real-time streaming
- 🔄 Performance monitoring

### Phase 3
- 📋 Production deployment
- 📋 Advanced OpenShift features
- 📋 Enterprise features
- 📋 Plugin system 