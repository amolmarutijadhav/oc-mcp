# OpenShift MCP Server Makefile

.PHONY: help install test clean setup run verify

help: ## Show this help message
	@echo "OpenShift MCP Server - Available Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	pip install -r requirements.txt

setup: ## Set up environment and configuration
	python tools/scripts/setup_environment.py

test: ## Run all tests
	python -m pytest tests/ -v

test-unit: ## Run unit tests only
	python -m pytest tests/unit/ -v

test-integration: ## Run integration tests only
	python -m pytest tests/integration/ -v

test-manual: ## Run manual verification tests
	python tests/manual/test_manual_verification.py

test-query: ## Run query processing tests
	python tests/manual/test_manual_verification.py query

run: ## Run the MCP server
	python tools/scripts/run_server.py

verify: ## Run full verification
	python tests/manual/test_manual_verification.py

debug: ## Run debug scripts
	python tools/debug/test_discovery_config.py

clean: ## Clean up temporary files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".coverage" -delete

format: ## Format code with black
	black src/ tests/ scripts/

lint: ## Run linting checks
	flake8 src/ tests/ scripts/
	mypy src/

check: format lint test ## Run all checks (format, lint, test)

docker-build: ## Build Docker image
	docker build -t openshift-mcp-server .

docker-run: ## Run Docker container
	docker run --env-file .env -p 8000:8000 openshift-mcp-server 