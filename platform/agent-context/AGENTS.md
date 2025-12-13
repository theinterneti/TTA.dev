# TTA (Therapeutic Text Adventure) - Universal Agent Context

**Universal Context Standard** - This file adheres to the standard adopted by various coding agents (GitHub Copilot, Claude, Auggie CLI). It is compiled from modular instructions to ensure portability and guarantee context coverage with minimal redundancy across the project.

## Project Overview

TTA is an AI-powered therapeutic text adventure platform that combines evidence-based mental health support with interactive storytelling. The system uses a multi-agent orchestration architecture with circuit breaker patterns, Redis-based message coordination, and Neo4j graph databases.

**Repository**: https://github.com/theinterneti/recovered-tta-storytelling
**Tech Stack**: Python 3.12+, FastAPI, Redis, Neo4j, React, Docker
**Architecture**: Multi-agent orchestration with circuit breaker patterns

## Core Architecture Patterns

### Multi-Agent Orchestration
- **Agent Types**: IPA (Input Processing), WBA (World Building), NGA (Narrative Generation)
- **Message Coordination**: Redis-based async messaging via `RedisMessageCoordinator`
- **Agent Registry**: Central registry with health monitoring and restart policies
- **Protocol Bridge**: Adapter pattern for real agent communication vs mock fallbacks

### Circuit Breaker Pattern
- **Implementation**: `src/agent_orchestration/circuit_breaker.py` with Redis persistence
- **States**: CLOSED → OPEN → HALF_OPEN with configurable thresholds
- **Usage**: Wrap agent calls with `CircuitBreaker.call()` for graceful degradation

### Error Recovery & Resilience
- **Retry Logic**: `retry_with_backoff()` with exponential backoff and jitter
- **Fallback Mechanisms**: Mock implementations when real agents unavailable
- **Agent Restart Policy**: Automatic restarts with backoff and circuit breaker protection

## Development Workflow

### Package Management
- **Tool**: `uv` (not pip/poetry) - use `uv sync --all-extras` for dependencies
- **Python**: 3.12+ required
- **Workspace Packages**: `tta-ai-framework`, `tta-narrative-engine`

### Component Maturity Workflow
Components progress through three maturity stages:
1. **Development**: Initial implementation, ≥70% coverage, ≥75% mutation score
2. **Staging**: Production-ready, ≥80% coverage, ≥80% mutation score
3. **Production**: Battle-tested, ≥85% coverage, ≥85% mutation score

**Promotion Process**:
```bash
# Promote component to staging
python scripts/workflow/spec_to_production.py \
    --spec specs/my_component.md \
    --component my_component \
    --target staging

# Promote component to production
python scripts/workflow/spec_to_production.py \
    --spec specs/my_component.md \
    --component my_component \
    --target production
```

### Testing Strategy

**Test Pyramid**:
- **Unit Tests** (70%): `tests/unit/` - Individual functions/classes in isolation
- **Integration Tests** (20%): `tests/integration/` - Component interactions
- **E2E Tests** (10%): `tests/e2e/` - Complete user workflows with Playwright

**Comprehensive Test Battery**:
- **Standard Tests**: Unit, integration, E2E
- **Adversarial Tests**: Edge cases, error conditions
- **Load/Stress Tests**: Performance under load
- **Data Pipeline Tests**: Data integrity and consistency
- **Dashboard Tests**: UI/UX validation

**Mock Fallbacks** (automatic):
- **Redis**: Falls back to in-memory mock
- **Neo4j**: Falls back to in-memory graph
- **OpenRouter**: Falls back to mock responses
- **External APIs**: Falls back to mock data

**Test Markers**:
```python
@pytest.mark.redis  # Requires Redis
@pytest.mark.neo4j  # Requires Neo4j
@pytest.mark.integration  # Integration test
@pytest.mark.slow  # Slow-running test
@pytest.mark.adversarial  # Edge case test
```

**Testing Patterns**:
- **AAA Pattern**: Arrange-Act-Assert structure
- **Pytest Fixtures**: Reusable test setup
- **Mocking**: Use `unittest.mock` for external dependencies
- **Async Testing**: `pytest-asyncio` with `@pytest.mark.asyncio`

## Code Conventions

### SOLID Principles
- **Single Responsibility**: Each class/function has one reason to change
- **Open-Closed**: Extend behavior through composition, not modification
- **Liskov Substitution**: Subtypes must be substitutable for base types
- **Interface Segregation**: Clients depend only on interfaces they use
- **Dependency Inversion**: Depend on abstractions, not concrete implementations

### File Size Limits
- **Soft Limit**: 300-400 lines (consider splitting)
- **Hard Limit**: 1,000 lines (MUST split - blocks staging promotion)
- **Statement Limit**: 500 executable statements (MUST split)

### Import Patterns
```python
# Agent orchestration imports
from .models import AgentId, AgentMessage, AgentType, OrchestrationRequest
from .circuit_breaker import CircuitBreaker, CircuitBreakerOpenError
from .messaging import MessageResult, QueueMessage
```

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

## Key Directories

### Core Components
- `src/agent_orchestration/` - Multi-agent coordination, circuit breakers, messaging
- `src/components/gameplay_loop/` - Core gameplay mechanics and narrative engine
- `src/player_experience/` - User-facing APIs and frontend services
- `src/common/` - Shared utilities, models, and configuration

### Testing & Quality
- `tests/conftest.py` - Fixtures with automatic mock fallbacks
- `tests/comprehensive_battery/` - Production-like test scenarios
- `pyproject.toml` - UV-based dependency management

### Configuration
- `.env.example` - Required env vars (OPENROUTER_API_KEY, NEO4J_URI, REDIS_URL)
- `docker/compose/` - Environment-specific Docker configurations
  - `docker-compose.base.yml` - Base services (shared across all environments)
  - `docker-compose.dev.yml` - Development overrides
  - `docker-compose.test.yml` - Test/CI overrides
  - `docker-compose.prod.yml` - Production configuration
- `secrets/` - Externalized credentials (gitignored)
- `scripts/dev.sh` - Development workflow automation

### Agentic Primitives
- `.github/instructions/` - Modular instruction files with YAML frontmatter (NEW)
- `.github/chatmodes/` - Role-based chat modes with tool boundaries (NEW)
- `.github/prompts/` - Agentic workflow files for common tasks (NEW)
- `.github/specs/` - Specification templates for features/APIs/components (NEW)
- `.augment/` - Legacy structure (maintained for backward compatibility)
- `apm.yml` - Agent Package Manager configuration (NEW)

## Quality Gates

### Development → Staging
- Test coverage ≥70%
- Mutation score ≥75%
- Cyclomatic complexity ≤10
- File size ≤1,000 lines
- No critical security issues

### Staging → Production
- Test coverage ≥80%
- Mutation score ≥80%
- Cyclomatic complexity ≤8
- File size ≤800 lines
- All security issues resolved

## Common Commands

```bash
```bash
# Environment setup
uv sync --all-extras

# Quality checks
uv run ruff check src/ tests/ --fix
uv run ruff format src/ tests/
uv run pyright src/

# Testing
uv run pytest tests/unit/ --cov=src --cov-report=html
uv run pytest -m "redis or neo4j"
uv run playwright test

# Services
bash docker/scripts/tta-docker.sh dev up -d  # Start development services
python src/main.py start                       # TTA orchestrator

# Component promotion
python scripts/workflow/spec_to_production.py --spec specs/my_component.md --target staging
```
```

## MCP Server Integration

### Available MCP Servers
- **Context7** - Up-to-date documentation lookup for libraries/frameworks
- **Serena** - Code symbol search, memory management, architectural analysis
- **Redis MCP** - Direct Redis database operations and inspection
- **Neo4j MCP** - Graph database operations for narrative and world state
- **Playwright** - Web application testing in browser
- **Sequential Thinking** - Multi-step reasoning for complex procedures

### MCP Configuration
- **VS Code Settings**: `.vscode/settings.json` contains MCP server configurations
- **Docker MCP Images**: Available for Neo4j, PostgreSQL, Grafana, Prometheus
- **Environment Variables**: See `.env.example` for MCP_SERVER_* configurations

## AI Context Management

### Session Management
```bash
# Create new session
python .augment/context/cli.py new session-name

# Add message to session
python .augment/context/cli.py add session-name "message" --importance 1.0

# Show session
python .augment/context/cli.py show session-name
```

### Context Loading Strategy
- **Auto-load**: `.github/copilot-instructions.md`, `GEMINI.md`, `AGENTS.md`
- **Session Management**: Automatic context loading for TTA development
- **Max Context Tokens**: 100,000 tokens

## Agent Role Boundaries

### Architect
- **Focus**: System design, architecture decisions
- **Allowed Tools**: fetch, search, githubRepo, codebase-retrieval
- **Denied Tools**: editFiles, runCommands, deleteFiles
- **Use Case**: Planning, design reviews, architectural analysis

### Backend Developer
- **Focus**: Implementation, refactoring, bug fixes
- **Allowed Tools**: editFiles, runCommands, codebase-retrieval, testFailure
- **Denied Tools**: deleteFiles, deployProduction
- **Use Case**: Feature implementation, code refactoring

### QA Engineer
- **Focus**: Testing, quality assurance, coverage improvement
- **Allowed Tools**: editFiles, runCommands, testFailure, codebase-retrieval
- **Denied Tools**: deleteFiles, deployProduction
- **Use Case**: Test generation, coverage improvement, quality validation

### DevOps
- **Focus**: Deployment, infrastructure, Docker
- **Allowed Tools**: editFiles, runCommands, deployStaging, codebase-retrieval
- **Denied Tools**: deployProduction (requires explicit approval)
- **Use Case**: Infrastructure changes, deployment automation

## Common Workflows

### Feature Implementation
1. Review specification in `specs/`
2. Create AI context session
3. Design implementation
4. Implement with tests
5. Run quality gates
6. Promote to staging

### Bug Fix
1. Reproduce issue
2. Identify root cause
3. Implement fix
4. Add regression test
5. Validate fix
6. Update documentation

### Refactoring
1. Analyze current implementation
2. Identify improvement opportunities
3. Plan refactoring strategy
4. Execute changes incrementally
5. Validate with tests
6. Update documentation

## Best Practices

### Before Making Changes
1. **Understand the context**: Use codebase-retrieval to gather information
2. **Check dependencies**: Find all callers and call sites
3. **Review tests**: Understand existing test coverage
4. **Plan changes**: Break down into manageable steps

### During Implementation
1. **Follow SOLID principles**: Keep code modular and maintainable
2. **Write tests first**: TDD approach when possible
3. **Use circuit breakers**: Wrap external calls
4. **Handle errors gracefully**: Implement retry and fallback logic

### After Implementation
1. **Run quality gates**: Ensure all checks pass
2. **Update documentation**: Keep docs synchronized
3. **Review changes**: Self-review before committing
4. **Test thoroughly**: Unit, integration, and E2E tests

### When Refactoring
1. **Start small**: Make incremental changes
2. **Test first**: Ensure existing tests pass before refactoring
3. **Add tests**: Write tests for new code paths
4. **Document**: Update docstrings and comments
5. **Validate**: Run full test suite and quality gates

### When Adding Tests
1. **Follow AAA**: Arrange-Act-Assert pattern
2. **Use fixtures**: Reuse test setup via pytest fixtures
3. **Mock external**: Mock filesystem, database, API calls
4. **Test edge cases**: Cover error paths and boundary conditions
5. **Maintain 100% pass rate**: Never commit failing tests

## Important Notes

- **Package Manager**: Always use `uv`, never pip or poetry
- **Circuit Breakers**: Wrap all external service calls with circuit breakers
- **Error Handling**: Use retry logic with exponential backoff for transient failures
- **Testing**: Comprehensive test battery with mock fallbacks for external services
- **Documentation**: Keep GEMINI.md and AGENTS.md synchronized with project changes
- **Never commit secrets**: Use `.env` files (gitignored)
- **Maintain backward compatibility**: Existing tests must pass
- **Follow component maturity**: Respect quality gate thresholds

## Related Documentation

- **GEMINI.md** - Gemini CLI sub-agent context file
- **.github/copilot-instructions.md** - GitHub Copilot specific instructions
- **CLAUDE.md** - Claude-specific instructions and context
- **docs/development/** - Detailed development guides and workflows
- **specs/** - Component and feature specifications

---

**Last Updated**: 2025-10-26
**Status**: Active - Universal context standard for all AI agents


---
**Logseq:** [[TTA.dev/Platform/Agent-context/Agents]]
