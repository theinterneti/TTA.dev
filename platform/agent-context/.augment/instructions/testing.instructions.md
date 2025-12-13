---
applyTo: "tests/**/*.py"
description: "pytest patterns, fixtures, markers, and testing conventions for TTA"
---
# TTA Testing Instructions

Testing guidelines and patterns for the TTA (Therapeutic Text Adventure) platform using pytest, pytest-asyncio, and Playwright.

## pytest Patterns

### Async Fixtures

**ALWAYS use `@pytest_asyncio.fixture` for async fixtures:**

```python
import pytest_asyncio
import redis.asyncio as aioredis

@pytest_asyncio.fixture
async def redis_client(redis_container):
    """Provide async Redis client for tests."""
    client = aioredis.from_url(redis_container)
    try:
        await client.ping()
        yield client
    finally:
        await client.aclose()
```

**Common mistake**: Using `@pytest.fixture` for async fixtures causes warnings and test failures.

### Parametrize

Use `@pytest.mark.parametrize` for testing multiple scenarios:

```python
@pytest.mark.parametrize("input_text,expected_safe", [
    ("Hello, how are you?", True),
    ("I'm feeling anxious", True),
    ("Harmful content", False),
])
async def test_safety_validation(input_text, expected_safe, safety_validator):
    """Test safety validation with various inputs."""
    result = await safety_validator.validate_text(input_text)
    assert result.safe == expected_safe
```

### Test Markers

Use markers to categorize tests:

```python
import pytest

@pytest.mark.integration
@pytest.mark.redis
async def test_redis_session_persistence(redis_client):
    """Test session persistence in Redis."""
    await redis_client.set("session:123", "data")
    result = await redis_client.get("session:123")
    assert result == "data"

@pytest.mark.slow
@pytest.mark.neo4j
async def test_story_graph_traversal(neo4j_driver):
    """Test story graph traversal (slow test)."""
    # Complex graph traversal logic
    pass
```

**Available markers**:
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.redis` - Requires Redis database
- `@pytest.mark.neo4j` - Requires Neo4j database
- `@pytest.mark.slow` - Tests taking >1 second
- `@pytest.mark.comprehensive` - Comprehensive test battery
- `@pytest.mark.mock_only` - Only runs in mock mode
- `@pytest.mark.real_services` - Requires real services

## Common Fixtures

### Redis Fixtures

```python
# From tests/conftest.py

@pytest_asyncio.fixture
async def redis_client(redis_container):
    """Async Redis client for async repository tests."""
    import redis.asyncio as aioredis

    client = aioredis.from_url(redis_container)
    try:
        await client.ping()
        yield client
    finally:
        await client.aclose()

@pytest.fixture
def redis_client_sync(redis_container):
    """Synchronous Redis client for simple integration tests."""
    import redis

    client = redis.from_url(redis_container)
    try:
        client.ping()
        yield client
    finally:
        client.close()
```

### Neo4j Fixtures

```python
# From tests/conftest.py

@pytest.fixture
def mock_neo4j_driver():
    """Provide a simple mock Neo4j driver/session for unit tests."""
    from unittest.mock import AsyncMock, Mock

    mock_driver = Mock()
    mock_session_ctx = Mock()
    mock_driver.session.return_value = mock_session_ctx

    # Mock session methods
    mock_session = Mock()
    mock_session.run = Mock(return_value=Mock(single=Mock(return_value=None)))
    mock_session.close = AsyncMock()
    mock_session_ctx.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session_ctx.__aexit__ = AsyncMock(return_value=None)

    return mock_driver
```

### Mock Service Fixtures

```python
@pytest.fixture
def mock_workflow_manager():
    """Mock WorkflowManager for testing."""
    from unittest.mock import Mock

    manager = Mock()
    manager.register_workflow = Mock(return_value=(True, None))
    manager.execute_workflow = Mock(
        return_value=(
            OrchestrationResponse(
                response_text="Test response",
                updated_context={"memory": {"test": "data"}},
                workflow_metadata={"workflow_name": "test", "run_id": "test-123"},
            ),
            "test-run-123",
            None,
        )
    )
    return manager
```

## Test Organization

### Directory Structure

```
tests/
├── unit/                      # Unit tests (isolated, fast)
│   ├── ai_components/
│   └── model_management/
├── integration/               # Integration tests (component interactions)
│   ├── conftest.py           # Integration-specific fixtures
│   └── test_*.py
├── e2e/                       # End-to-end tests (Playwright)
│   ├── fixtures/
│   ├── page-objects/
│   └── specs/
├── agent_orchestration/       # Component-specific tests
├── primitives/                # Primitive tests (error recovery, context, metrics)
└── conftest.py               # Global fixtures
```

### Test Naming Conventions

**Pattern**: `test_<function>_<scenario>_<expected_result>`

**Examples**:
- `test_validate_text_safe_content_returns_true`
- `test_redis_connection_timeout_raises_error`
- `test_workflow_execution_invalid_input_returns_error`

## Coverage Requirements

### Maturity Stage Thresholds

- **Development → Staging**: ≥70% test coverage
- **Staging → Production**: ≥80% test coverage
- **Player-facing features**: ≥80% coverage (always)

### Running Coverage

```bash
# Run with coverage report
uvx pytest tests/ --cov=src/ --cov-report=term

# Generate HTML coverage report
uvx pytest tests/ --cov=src/ --cov-report=html

# Check coverage for specific component
uvx pytest tests/agent_orchestration/ --cov=src/agent_orchestration --cov-report=term
```
```

## Test Examples

### Example 1: Async Service Test

```python
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock

@pytest_asyncio.fixture
async def player_service(redis_client):
    """Provide PlayerService with real Redis client."""
    service = PlayerService(redis_client)
    yield service
    # Cleanup
    await redis_client.flushdb()

@pytest.mark.integration
@pytest.mark.redis
async def test_save_player_state_persists_to_redis(player_service, redis_client):
    """Test that player state is persisted to Redis."""
    player_id = "player-123"
    state = PlayerState(player_id=player_id, current_scene="intro", emotional_state={"calm": 0.8})

    await player_service.save_state(player_id, state)

    # Verify persistence
    saved_data = await redis_client.hgetall(f"player:{player_id}")
    assert saved_data["current_scene"] == "intro"
```

### Example 2: Parametrized Test

```python
@pytest.mark.parametrize("error_type,should_retry", [
    (ConnectionError("timeout"), True),
    (ValueError("invalid input"), False),
    (Exception("rate limit"), True),
])
def test_error_classification(error_type, should_retry):
    """Test error classification for retry logic."""
    from scripts.primitives.error_recovery import classify_error, should_retry as check_retry

    category, severity = classify_error(error_type)
    result = check_retry(error_type, attempt=0, max_retries=3)

    assert result == should_retry
```

### Example 3: Mock-Based Unit Test

```python
from unittest.mock import AsyncMock, Mock, patch

@pytest.fixture
def mock_openrouter_client():
    """Mock OpenRouter API client."""
    client = Mock()
    client.generate = AsyncMock(return_value="Generated narrative text")
    return client

async def test_narrative_generation_calls_openrouter(mock_openrouter_client):
    """Test that narrative generation calls OpenRouter API."""
    generator = NarrativeGenerator(openrouter_client=mock_openrouter_client)

    result = await generator.generate("Player enters the forest")

    mock_openrouter_client.generate.assert_called_once()
    assert result == "Generated narrative text"
```

### Example 4: Integration Test with Cleanup

```python
@pytest.mark.integration
@pytest.mark.neo4j
async def test_story_graph_creation(neo4j_driver):
    """Test story graph creation in Neo4j."""
    async with neo4j_driver.session() as session:
        # Create test data
        await session.run(
            "CREATE (s:Scene {id: $id, name: $name})",
            id="scene-1", name="Forest Entrance"
        )

        # Verify creation
        result = await session.run(
            "MATCH (s:Scene {id: $id}) RETURN s.name AS name",
            id="scene-1"
        )
        record = await result.single()
        assert record["name"] == "Forest Entrance"

        # Cleanup
        await session.run("MATCH (s:Scene {id: $id}) DELETE s", id="scene-1")
```

### Example 5: Circuit Breaker Test

```python
from scripts.primitives.error_recovery import CircuitBreaker, CircuitBreakerState

def test_circuit_breaker_opens_after_failures():
    """Test circuit breaker opens after consecutive failures."""
    breaker = CircuitBreaker(failure_threshold=3, timeout_seconds=60)

    # Record failures
    for _ in range(3):
        breaker.record_failure()

    assert breaker.state == CircuitBreakerState.OPEN
    assert breaker.is_open is True
```

## Anti-Patterns

### Anti-Pattern 1: Using `@pytest.fixture` for Async Fixtures

**Problem**: Async fixtures must use `@pytest_asyncio.fixture`.

**Bad**:
```python
@pytest.fixture  # Wrong decorator!
async def redis_client():
    client = await aioredis.from_url("redis://localhost")
    yield client
    await client.close()
```

**Good**:
```python
import pytest_asyncio

@pytest_asyncio.fixture  # Correct decorator
async def redis_client():
    client = await aioredis.from_url("redis://localhost")
    yield client
    await client.close()
```

### Anti-Pattern 2: Missing Test Cleanup

**Problem**: Tests leave data in databases, causing test pollution.

**Bad**:
```python
async def test_save_player(redis_client):
    await redis_client.set("player:123", "data")
    # No cleanup - data persists!
```

**Good**:
```python
async def test_save_player(redis_client):
    try:
        await redis_client.set("player:123", "data")
        # Test assertions
    finally:
        await redis_client.delete("player:123")  # Cleanup
```

### Anti-Pattern 3: Hardcoded Test Data

**Problem**: Hardcoded values make tests brittle and unclear.

**Bad**:
```python
async def test_player_creation():
    player = await create_player("player-123", "John", 25)
    assert player.id == "player-123"  # Magic values
```

**Good**:
```python
@pytest.fixture
def test_player_data():
    return {
        "player_id": "test-player-123",
        "name": "Test Player",
        "age": 25
    }

async def test_player_creation(test_player_data):
    player = await create_player(**test_player_data)
    assert player.id == test_player_data["player_id"]
```

## References

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio Documentation](https://pytest-asyncio.readthedocs.io/)
- [TTA Testing Guide](../../docs/testing/QUICK_REFERENCE_TESTING_GUIDE.md)
- [Integration Test Summary](../agent_orchestration/INTEGRATION_TEST_SUMMARY.md)

---

**Last Updated**: 2025-10-22
**Maintainer**: theinterneti


---
**Logseq:** [[TTA.dev/Platform/Agent-context/.augment/Instructions/Testing.instructions]]
