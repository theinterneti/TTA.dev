---
applyTo: "**/*.py"
description: "Project-wide coding standards, architecture principles, and quality requirements for TTA"
---
# TTA Global Development Instructions

Project-wide coding standards, architecture principles, and quality requirements for the TTA (Therapeutic Text Adventure) platform.

## Architecture Principles

### SOLID Principles

- **Single Responsibility Principle (SRP)**: Each class/function has one reason to change. Split files when they exceed 300-400 lines or handle multiple concerns.
- **Open-Closed Principle (OCP)**: Extend behavior through composition and inheritance, not modification. Use dependency injection for flexibility.
- **Liskov Substitution Principle (LSP)**: Subtypes must be substitutable for base types without breaking functionality.
- **Interface Segregation Principle (ISP)**: Clients depend only on interfaces they use. Create focused, minimal interfaces.
- **Dependency Inversion Principle (DIP)**: Depend on abstractions (protocols, ABCs), not concrete implementations.

### Layered Architecture

Follow Onion/Clean Architecture pattern:
- **Domain Layer**: Core business logic, no external dependencies
- **Application Layer**: Use cases, orchestration, workflows
- **Infrastructure Layer**: External integrations (Redis, Neo4j, OpenRouter)
- **Presentation Layer**: FastAPI endpoints, API models

### File Size Limits

- **Soft Limit**: 300-400 lines (consider splitting)
- **Hard Limit**: 1,000 lines (MUST split - blocks staging promotion)
- **Statement Limit**: 500 executable statements (MUST split)

## Testing Requirements

### Coverage Thresholds

- **Development → Staging**: ≥70% test coverage
- **Staging → Production**: ≥80% test coverage
- **Player-facing features**: ≥80% coverage (always)

### Test Organization

- **Unit tests**: `tests/unit/` - Test individual functions/classes in isolation
- **Integration tests**: `tests/integration/` - Test component interactions
- **E2E tests**: `tests/e2e/` - Test complete user workflows with Playwright

### pytest Markers

Use markers to categorize tests:
```python
@pytest.mark.player_experience  # Player experience component
@pytest.mark.agent_orchestration  # Agent orchestration component
@pytest.mark.narrative_engine  # Narrative engine component
@pytest.mark.slow  # Tests that take >1 second
@pytest.mark.integration  # Integration tests
```

### Async Fixtures

Always use `@pytest_asyncio.fixture` for async fixtures:
```python
import pytest_asyncio

@pytest_asyncio.fixture
async def redis_client():
    """Provide Redis client for tests."""
    client = await aioredis.from_url("redis://localhost:6379")
    yield client
    await client.close()
```

## Code Style

### Naming Conventions

- **Functions/Variables**: `snake_case` (e.g., `process_user_input`, `player_state`)
- **Classes**: `PascalCase` (e.g., `PlayerStateRepository`, `NarrativeGenerator`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `MAX_RETRIES`, `DEFAULT_TIMEOUT`)
- **Private members**: Prefix with `_` (e.g., `_internal_method`, `_cache`)

### Docstrings

Use Google-style docstrings for all public APIs:
```python
async def process_input(player_id: str, input_text: str) -> ProcessedInput:
    """Process player input through therapeutic validation.

    Args:
        player_id: Unique identifier for the player
        input_text: Raw text input from the player

    Returns:
        ProcessedInput: Validated and enriched input data

    Raises:
        ValidationError: If input fails therapeutic safety checks
        PlayerNotFoundError: If player_id doesn't exist
    """
```

### Type Hints

Required for all public APIs, recommended for internal code:
```python
from typing import Optional, Dict, List
from dataclasses import dataclass

@dataclass
class PlayerState:
    player_id: str
    current_scene: str
    emotional_state: Dict[str, float]
    progress: Optional[Dict[str, Any]] = None
```

## Common Patterns

### Error Handling with Retry

Use exponential backoff for transient failures:
```python
from packages.tta-ai-framework.src.tta_ai.orchestration.adapters import with_retry, RetryConfig

retry_config = RetryConfig(
    max_retries=3,
    base_delay=1.0,
    exponential_base=2.0,
    max_delay=10.0,
    jitter=True
)

@with_retry(retry_config)
async def call_external_api(endpoint: str) -> dict:
    """Call external API with automatic retry."""
    async with httpx.AsyncClient() as client:
        response = await client.get(endpoint)
        response.raise_for_status()
        return response.json()
```

### Circuit Breaker Pattern

Prevent cascading failures:
```python
from packages.tta-ai-framework.src.tta_ai.orchestration.circuit_breaker_registry import CircuitBreakerRegistry

registry = CircuitBreakerRegistry()
breaker = registry.get_or_create("openrouter_api")

async def generate_narrative(prompt: str) -> str:
    """Generate narrative with circuit breaker protection."""
    if breaker.is_open:
        raise ServiceUnavailableError("OpenRouter API circuit breaker is open")

    try:
        result = await openrouter_client.generate(prompt)
        breaker.record_success()
        return result
    except Exception as e:
        breaker.record_failure()
        raise
```

### Dependency Injection

Use FastAPI's dependency injection for services:
```python
from fastapi import Depends
from typing import Annotated

async def get_redis_client() -> aioredis.Redis:
    """Provide Redis client as dependency."""
    client = await aioredis.from_url("redis://localhost:6379")
    try:
        yield client
    finally:
        await client.close()

RedisClient = Annotated[aioredis.Redis, Depends(get_redis_client)]

@app.post("/player/{player_id}/state")
async def save_player_state(
    player_id: str,
    state: PlayerState,
    redis: RedisClient
) -> dict:
    """Save player state using injected Redis client."""
    await redis.hset(f"player:{player_id}", mapping=state.dict())
    return {"status": "saved"}
```

## Integration Points

### Redis

- **Session State**: Player sessions, temporary data (TTL: 1 hour)
- **Caching**: LLM responses, computed results (TTL: varies)
- **Pub/Sub**: Real-time events, agent coordination
- **Key Patterns**: `player:{id}`, `session:{id}`, `cache:{key}`

### Neo4j

- **Story Graphs**: Narrative structure, scene relationships
- **Character Relationships**: Character interactions, emotional bonds
- **World State**: Persistent world knowledge, quest progress
- **Query Pattern**: Use parameterized queries to prevent injection

### LangGraph

- **Workflow Orchestration**: Multi-agent coordination (IPA → WBA → NGA)
- **State Management**: Workflow state persistence in Redis
- **Error Recovery**: Automatic retry and fallback strategies

## Quality Gates

### Linting (ruff)

All code must pass ruff checks:
```bash
uvx ruff check src/ tests/
uvx ruff format src/ tests/
```

### Type Checking (pyright)

All code must pass type checking:
```bash
uvx pyright src/
```

### Security (detect-secrets)

No secrets in code:
```bash
uvx detect-secrets scan --baseline .secrets.baseline
```

## Anti-Patterns

### Anti-Pattern 1: Mixing Concerns (Violates SRP)

**Problem**: Combining persistence, validation, and business logic in one class.

**Bad**:
```python
class PlayerManager:
    """Handles EVERYTHING related to players."""

    async def save_player(self, player: Player) -> None:
        # Validation
        if not player.name:
            raise ValueError("Name required")
        # Business logic
        player.score = self._calculate_score(player)
        # Persistence
        await self.redis.hset(f"player:{player.id}", mapping=player.dict())
```

**Good**:
```python
class PlayerValidator:
    """Validates player data."""
    def validate(self, player: Player) -> None:
        if not player.name:
            raise ValueError("Name required")

class PlayerScoreCalculator:
    """Calculates player scores."""
    def calculate(self, player: Player) -> int:
        return sum(player.achievements) * 10

class PlayerRepository:
    """Persists player data."""
    async def save(self, player: Player) -> None:
        await self.redis.hset(f"player:{player.id}", mapping=player.dict())
```

### Anti-Pattern 2: Missing Async/Await

**Problem**: Blocking I/O in async functions.

**Bad**:
```python
async def get_player_data(player_id: str) -> dict:
    # Blocking call in async function!
    response = requests.get(f"https://api.example.com/player/{player_id}")
    return response.json()
```

**Good**:
```python
async def get_player_data(player_id: str) -> dict:
    # Non-blocking async call
    async with httpx.AsyncClient() as client:
        response = await client.get(f"https://api.example.com/player/{player_id}")
        return response.json()
```

## References

- [Component Maturity Workflow](../../docs/development/COMPONENT_MATURITY_WORKFLOW.md)
- [Phase 1 Architecture](../../src/agent_orchestration/PHASE1_ARCHITECTURE.md)
- [Integrated Workflow](../rules/integrated-workflow.md)
- [File Size Limits](../rules/avoid-long-files.md)

---

**Last Updated**: 2025-10-22
**Maintainer**: theinterneti


---
**Logseq:** [[TTA.dev/Platform/Agent-context/.augment/Instructions/Global.instructions]]
