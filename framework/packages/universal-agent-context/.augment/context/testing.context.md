# Context: Testing

**Purpose:** Quick reference for testing commands, patterns, fixtures, and best practices in TTA development.

**When to Use:** When writing tests, running test suites, debugging test failures, or improving test coverage.

---

## Quick Test Commands

### Run All Tests
```bash
# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run with coverage
uv run pytest --cov=src --cov-report=term-missing

# Run specific test file
uv run pytest tests/context/test_memory_loading.py

# Run specific test function
uv run pytest tests/context/test_memory_loading.py::test_discover_memories
```

### Run Tests by Marker
```bash
# Run only unit tests
uv run pytest -m unit

# Run only integration tests
uv run pytest -m integration

# Run only async tests
uv run pytest -m asyncio

# Skip slow tests
uv run pytest -m "not slow"

# Run multiple markers
uv run pytest -m "unit and not slow"
```

### Run Tests by Component
```bash
# Run agent orchestration tests
uv run pytest tests/agent_orchestration/

# Run player experience tests
uv run pytest tests/player_experience/

# Run narrative engine tests
uv run pytest tests/narrative_engine/

# Run context management tests
uv run pytest tests/context/
```

### Coverage Commands
```bash
# Generate coverage report
uv run pytest --cov=src --cov-report=term-missing

# Generate HTML coverage report
uv run pytest --cov=src --cov-report=html
# Open htmlcov/index.html in browser

# Check coverage threshold
uv run pytest --cov=src --cov-fail-under=70

# Coverage for specific component
uv run pytest tests/agent_orchestration/ \
    --cov=src/agent_orchestration \
    --cov-report=term-missing
```

---

## Test Fixtures

### Common Fixtures

#### Redis Fixtures
```python
import pytest
import redis.asyncio as redis

@pytest.fixture
async def redis_client():
    """Async Redis client for testing."""
    client = redis.from_url("redis://localhost:6379/0")
    yield client
    await client.flushdb()  # Clean up after test
    await client.close()

@pytest.fixture
async def redis_with_data(redis_client):
    """Redis client with test data."""
    await redis_client.set("test:key", "test:value")
    yield redis_client
```

#### Neo4j Fixtures
```python
@pytest.fixture
async def neo4j_driver():
    """Neo4j driver for testing."""
    driver = AsyncGraphDatabase.driver(
        "bolt://localhost:7687",
        auth=("neo4j", "password")
    )
    yield driver
    # Clean up test data
    async with driver.session() as session:
        await session.run("MATCH (n:TestNode) DETACH DELETE n")
    await driver.close()
```

#### FastAPI Fixtures
```python
from fastapi.testclient import TestClient

@pytest.fixture
def client():
    """FastAPI test client."""
    from src.main import app
    return TestClient(app)

@pytest.fixture
async def async_client():
    """Async FastAPI test client."""
    from httpx import AsyncClient
    from src.main import app

    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
```

#### Mock Fixtures
```python
from unittest.mock import AsyncMock, MagicMock

@pytest.fixture
def mock_ai_provider():
    """Mock AI provider for testing."""
    provider = AsyncMock()
    provider.generate.return_value = "Mock AI response"
    return provider

@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    client = MagicMock()
    client.get.return_value = b'{"key": "value"}'
    client.set.return_value = True
    return client
```

### Fixture Scopes
```python
# Function scope (default) - new instance per test
@pytest.fixture(scope="function")
def function_fixture():
    return "new instance per test"

# Class scope - new instance per test class
@pytest.fixture(scope="class")
def class_fixture():
    return "new instance per class"

# Module scope - new instance per module
@pytest.fixture(scope="module")
def module_fixture():
    return "new instance per module"

# Session scope - one instance for entire test session
@pytest.fixture(scope="session")
def session_fixture():
    return "one instance for all tests"
```

---

## Test Markers

### Built-in Markers
```python
import pytest

# Mark test as async
@pytest.mark.asyncio
async def test_async_function():
    result = await async_function()
    assert result is not None

# Skip test
@pytest.mark.skip(reason="Not implemented yet")
def test_future_feature():
    pass

# Skip test conditionally
@pytest.mark.skipif(sys.version_info < (3, 11), reason="Requires Python 3.11+")
def test_python_311_feature():
    pass

# Expected to fail
@pytest.mark.xfail(reason="Known bug")
def test_known_bug():
    assert buggy_function() == expected_value

# Parametrize test
@pytest.mark.parametrize("input,expected", [
    (1, 2),
    (2, 4),
    (3, 6),
])
def test_double(input, expected):
    assert double(input) == expected
```

### Custom Markers
```python
# Define in pytest.ini or conftest.py
# markers =
#     unit: Unit tests
#     integration: Integration tests
#     slow: Slow tests (>1 second)

# Use custom markers
@pytest.mark.unit
def test_unit_function():
    assert add(1, 2) == 3

@pytest.mark.integration
async def test_integration_redis():
    result = await redis_client.get("key")
    assert result is not None

@pytest.mark.slow
def test_slow_operation():
    result = expensive_computation()
    assert result is not None
```

---

## Test Patterns

### Pattern 1: Arrange-Act-Assert (AAA)
```python
def test_user_creation():
    # Arrange - Set up test data
    user_data = {"name": "Alice", "email": "alice@example.com"}

    # Act - Perform the action
    user = create_user(user_data)

    # Assert - Verify the result
    assert user.name == "Alice"
    assert user.email == "alice@example.com"
    assert user.id is not None
```

### Pattern 2: Async Testing
```python
@pytest.mark.asyncio
async def test_async_redis_operation(redis_client):
    # Arrange
    key = "test:key"
    value = "test:value"

    # Act
    await redis_client.set(key, value)
    result = await redis_client.get(key)

    # Assert
    assert result.decode() == value
```

### Pattern 3: Exception Testing
```python
def test_invalid_input_raises_error():
    with pytest.raises(ValueError, match="Invalid input"):
        process_data(invalid_data)

@pytest.mark.asyncio
async def test_async_exception():
    with pytest.raises(ConnectionError):
        await connect_to_invalid_server()
```

### Pattern 4: Mocking
```python
from unittest.mock import patch, AsyncMock

def test_with_mock():
    with patch('module.function') as mock_func:
        mock_func.return_value = "mocked value"
        result = call_function_that_uses_module()
        assert result == "mocked value"
        mock_func.assert_called_once()

@pytest.mark.asyncio
async def test_async_mock():
    with patch('module.async_function', new_callable=AsyncMock) as mock_func:
        mock_func.return_value = "mocked value"
        result = await call_async_function()
        assert result == "mocked value"
```

### Pattern 5: Parametrized Tests
```python
@pytest.mark.parametrize("input,expected", [
    ("hello", "HELLO"),
    ("world", "WORLD"),
    ("", ""),
])
def test_uppercase(input, expected):
    assert input.upper() == expected

@pytest.mark.parametrize("user_type,permissions", [
    ("admin", ["read", "write", "delete"]),
    ("user", ["read", "write"]),
    ("guest", ["read"]),
])
def test_user_permissions(user_type, permissions):
    user = create_user(user_type)
    assert user.permissions == permissions
```

---

## Common Test Issues

### Issue 1: Async Test Not Running

**Symptoms:**
- `RuntimeWarning: coroutine was never awaited`
- Test passes but doesn't actually run

**Solution:**
```python
# ❌ Wrong - Missing @pytest.mark.asyncio
async def test_async_function():
    result = await async_function()
    assert result is not None

# ✅ Correct - Add marker
@pytest.mark.asyncio
async def test_async_function():
    result = await async_function()
    assert result is not None
```

### Issue 2: Fixture Not Found

**Symptoms:**
- `fixture 'fixture_name' not found`

**Solution:**
```python
# Ensure fixture is defined in conftest.py or same file
# conftest.py
import pytest

@pytest.fixture
def my_fixture():
    return "fixture value"

# test_file.py
def test_with_fixture(my_fixture):
    assert my_fixture == "fixture value"
```

### Issue 3: Import Errors in Tests

**Symptoms:**
- `ModuleNotFoundError: No module named 'src'`

**Solution:**
```bash
# Use uv run to ensure correct environment
uv run pytest tests/

# Or add src to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:${PWD}/src"
pytest tests/
```

---

## Best Practices

### DO:
✅ Write tests before or alongside code (TDD)
✅ Use descriptive test names (`test_user_creation_with_valid_data`)
✅ Follow AAA pattern (Arrange-Act-Assert)
✅ Test edge cases and error conditions
✅ Use fixtures for common setup
✅ Mock external dependencies
✅ Aim for >70% coverage (staging), >80% (production)
✅ Run tests before committing

### DON'T:
❌ Test implementation details
❌ Write tests that depend on each other
❌ Use sleep() for timing (use proper async/await)
❌ Commit failing tests
❌ Skip writing tests for "simple" code
❌ Test third-party library code
❌ Use production data in tests

---

## Resources

### TTA Documentation
- Testing Patterns: `.augment/memory/successful-patterns/testing-patterns.memory.md`
- Test Failures: `.augment/memory/implementation-failures/test-failures.memory.md`
- Quality Gates: `scripts/workflow/quality_gates.py`

### External Resources
- pytest: https://docs.pytest.org/
- pytest-asyncio: https://pytest-asyncio.readthedocs.io/
- pytest-cov: https://pytest-cov.readthedocs.io/
- unittest.mock: https://docs.python.org/3/library/unittest.mock.html

---

**Note:** Good tests are fast, isolated, repeatable, and self-validating. Write tests that give you confidence to refactor and deploy.
