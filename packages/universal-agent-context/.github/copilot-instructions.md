# TTA (Therapeutic Text Adventure) - Copilot Instructions

## Project Overview

TTA is an AI-powered therapeutic text adventure platform that combines evidence-based mental health support with interactive storytelling. The system uses a multi-agent orchestration architecture with circuit breaker patterns, Redis-based message coordination, and Neo4j graph databases.

## Architecture Patterns

### Multi-Agent Orchestration
- **Agent Types**: IPA (Input Processing), WBA (World Building), NGA (Narrative Generation)
- **Message Coordination**: Redis-based async messaging via `RedisMessageCoordinator`
- **Agent Registry**: Central registry with health monitoring and restart policies (`src/agent_orchestration/agents.py`)
- **Protocol Bridge**: Adapter pattern for real agent communication vs mock fallbacks

### Circuit Breaker Pattern
- **Implementation**: `src/agent_orchestration/circuit_breaker.py` with Redis persistence
- **States**: CLOSED → OPEN → HALF_OPEN with configurable thresholds
- **Usage**: Wrap agent calls with `CircuitBreaker.call()` for graceful degradation
- **Metrics**: Comprehensive failure tracking and observability integration

### Error Recovery & Resilience
- **Retry Logic**: `retry_with_backoff()` with exponential backoff and jitter
- **Fallback Mechanisms**: Mock implementations when real agents unavailable
- **Agent Restart Policy**: Automatic restarts with backoff and circuit breaker protection

## Development Workflow

### Package Management
- **Tool**: `uv` (not pip/poetry) - use `uv sync --all-extras` for dependencies
- **Python**: 3.12+ required, workspace packages: `tta-ai-framework`, `tta-narrative-engine`

### Testing Strategy
- **Comprehensive Battery**: `tests/comprehensive_battery/` with mock fallbacks
- **Categories**: Standard, Adversarial, Load/Stress, Data Pipeline, Dashboard
- **Markers**: `@pytest.mark.redis`, `@pytest.mark.neo4j`, `@pytest.mark.integration`
- **Mutation Tests**: 100% scores for ModelSelector, FallbackHandler, PerformanceMonitor

### Service Management
- **Docker Compose**: Consolidated architecture with base + environment overrides
  - Base: `docker/compose/docker-compose.base.yml`
  - Dev: `docker/compose/docker-compose.dev.yml`
  - Test: `docker/compose/docker-compose.test.yml`
  - Prod: `docker/compose/docker-compose.prod.yml`
- **Management Script**: `docker/scripts/tta-docker.sh` - Unified interface for all environments
- **Services**: Neo4j (7474/7687), Redis (6379), Grafana monitoring
- **Scripts**: `bash docker/scripts/tta-docker.sh <env> <command>` for common tasks

## Code Conventions

### Import Patterns
```python
# Agent orchestration imports
from .models import AgentId, AgentMessage, AgentType, OrchestrationRequest
from .circuit_breaker import CircuitBreaker, CircuitBreakerOpenError
from .messaging import MessageResult, QueueMessage
```

### Component Structure
- **Base Classes**: `WorkflowPrimitive` for composable operations
- **Database Managers**: `Neo4jGameplayManager`, `RedisMessageCoordinator`
- **Controllers**: Layer between API and business logic
- **Models**: Pydantic dataclasses in `models.py` files

### Error Handling
```python
# Use circuit breakers for external calls
try:
    result = await circuit_breaker.call(agent_function)
except CircuitBreakerOpenError:
    return fallback_response()

# Retry with exponential backoff
@with_retry(RetryConfig(max_retries=3))
async def risky_operation():
    pass
```

## Key Files & Directories

### Core Components
- `src/agent_orchestration/`: Multi-agent coordination, circuit breakers, messaging
- `src/components/gameplay_loop/`: Core gameplay mechanics and narrative engine
- `src/player_experience/`: User-facing APIs and frontend services
- `src/common/`: Shared utilities, models, and configuration

### Testing & Quality
- `tests/conftest.py`: Fixtures with automatic mock fallbacks
- `tests/comprehensive_battery/`: Production-like test scenarios
- `pyproject.toml`: UV-based dependency management with workspace packages

### Configuration
- `.env.example`: Required env vars (OPENROUTER_API_KEY, NEO4J_URI, REDIS_URL)
- `docker/compose/`: Environment-specific Docker configurations
- `secrets/`: Externalized credentials (gitignored, see `secrets/README.md`)
- `scripts/dev.sh`: Development workflow automation

## AI Context Integration

### Conversation Management
- **Context Manager**: `.augment/context/conversation_manager.py`
- **Session Management**: Automatic context loading for TTA development
- **CLI Tool**: `python .augment/context/cli.py` for session management

### Agentic Primitives
- **dev-primitives**: Meta-level development error recovery
- **tta-workflow-primitives**: Production workflow composition with observability
- **Retry Decorators**: `@with_retry()` and `@with_retry_async()`

### Chat Modes (`.augment/chatmodes/`)
Activate role-specific behavior patterns:
- **Architect** (`architect.chatmode.md`) - Design decisions, system architecture
- **Backend Dev** (`backend-dev.chatmode.md`) - Implementation patterns, refactoring
- **Frontend Dev** (`frontend-dev.chatmode.md`) - React components, UI patterns
- **DevOps** (`devops.chatmode.md`) - Deployment, infrastructure, Docker
- **QA Engineer** (`qa-engineer.chatmode.md`) - Testing strategies, coverage improvement

### Agentic Workflows (`.augment/workflows/`)
Structured multi-step procedures:
- **test-coverage-improvement** - Systematic coverage enhancement
- **component-promotion** - Maturity advancement workflow
- **bug-fix** - Structured debugging and remediation
- **refactoring** - Safe architectural changes with validation

### GEMINI.md Context File
Project root contains `GEMINI.md` with:
- Tech stack and architecture overview
- Component maturity workflow
- Current refactoring tasks and challenges
- Common commands and patterns
- Auto-loaded by Gemini CLI sub-agent

## MCP Server Integration

### Available MCP Servers
- **Context7** (`@upstash/context7-mcp`) - Up-to-date documentation lookup for libraries/frameworks
- **Sequential Thinking** - Multi-step reasoning for complex procedures
- **Playwright** - Web application testing in browser
- **Redis MCP** - Direct Redis database operations and inspection
- **Neo4j MCP** (Docker: `mcp/neo4j-memory`, `mcp/neo4j-data-modeling`) - Graph database operations
- **Grafana MCP** (Docker: `mcp/grafana`) - Monitoring and visualization tools
- **Serena** - Code symbol search, memory management, and architectural analysis

### MCP Server Usage Patterns
```python
# Context7: Fetch current documentation before implementing
# Example: "Using Context7, show me latest FastAPI streaming patterns"

# Sequential Thinking: Break down complex refactoring
# Use for multi-step orchestration changes, migration workflows

# Redis MCP: Inspect session state, debug cache issues
# Direct access to Redis keys for message coordination debugging

# Serena Tools:
# - find_symbol_Serena: Locate architectural elements
# - get_symbols_overview_Serena: Understand module organization
# - read_memory_Serena/write_memory_Serena: Track design decisions
```

### MCP Configuration
- **VS Code Settings**: `.vscode/settings.json` contains MCP server configurations
- **Docker MCP Images**: Available for Neo4j, PostgreSQL, Grafana, Prometheus
- **Environment Variables**: See `.env.example` for MCP_SERVER_* configurations

## Development Commands

```bash
# Environment setup
uv sync --all-extras

# Quality checks
uv run ruff check src/ tests/ --fix
uv run ruff format src/ tests/

# Testing
uv run pytest tests/unit/                    # Unit tests
uv run pytest -m "redis or neo4j"          # Database tests
uv run pytest --cov=src --cov-report=html  # Coverage

# Services
docker-compose -f docker/compose/docker-compose.base.yml \
               -f docker/compose/docker-compose.dev.yml up -d
python src/main.py start                    # TTA orchestrator

# Or use unified management script
bash docker/scripts/tta-docker.sh dev up -d

# Gemini CLI sub-agent (when available)
gemini "@{file} analyze this for testability"  # File injection
gemini "/memory show"                          # View project context
```

Focus on circuit breaker patterns, Redis-based messaging, and comprehensive error handling when working with agent orchestration. Always prefer `uv` over other Python package managers and ensure circuit breakers wrap external service calls. Leverage MCP servers (especially Context7 and Serena) for deep codebase understanding before making architectural changes.
