# Testing Patterns

**Purpose:** Capture successful test patterns, strategies, and best practices discovered during TTA development.

**Last Updated:** 2025-10-20

---

## Async Testing with pytest-asyncio

### Pattern: Async Test Functions

**Use Case:** Testing async functions and coroutines

**Pattern:**
```python
import pytest

@pytest.mark.asyncio
async def test_async_operation():
    """Test async functionality."""
    result = await async_function()
    assert result is not None
```

**Key Points:**
- Always use `@pytest.mark.asyncio` decorator
- Use `async def` for test functions
- Use `await` for async calls
- Ensure `pytest-asyncio` is installed

**Common Mistake:**
```python
# ❌ Wrong: Missing @pytest.mark.asyncio
async def test_async_operation():
    result = await async_function()
```

**Correct:**
```python
# ✅ Correct: With decorator
@pytest.mark.asyncio
async def test_async_operation():
    result = await async_function()
```

---

## Fixture Usage

### Pattern: Shared Test Fixtures

**Use Case:** Reusable test setup across multiple tests

**Pattern:**
```python
# In tests/conftest.py
import pytest

@pytest.fixture
def redis_client():
    """Redis client for testing."""
    client = create_redis_client()
    yield client
    client.close()

# In test file
def test_with_redis(redis_client):
    """Test using Redis fixture."""
    redis_client.set("key", "value")
    assert redis_client.get("key") == "value"
```

**Benefits:**
- Reduces code duplication
- Ensures proper cleanup
- Centralizes test setup

**Available Fixtures (TTA):**
- `redis_client`: Redis client
- `neo4j_session`: Neo4j session
- `mock_agent`: Mock AI agent
- `mock_player`: Mock player
- `game_session`: Active game session

---

## Parametrized Tests

### Pattern: Testing Multiple Scenarios

**Use Case:** Test same logic with different inputs

**Pattern:**
```python
import pytest

@pytest.mark.parametrize("input,expected", [
    ("hello", "HELLO"),
    ("world", "WORLD"),
    ("", ""),
    ("MiXeD", "MIXED"),
])
def test_uppercase(input, expected):
    """Test uppercase conversion."""
    assert uppercase(input) == expected
```

**Benefits:**
- Reduces test code duplication
- Tests multiple scenarios efficiently
- Clear test case documentation

**Advanced Pattern:**
```python
@pytest.mark.parametrize("age,valid,reason", [
    (17, False, "too_young"),
    (18, True, "valid"),
    (25, True, "valid"),
    (150, False, "too_old"),
])
def test_age_validation(age, valid, reason):
    """Test age validation with reasons."""
    result = validate_age(age)
    assert result.valid == valid
    if not valid:
        assert result.reason == reason
```

---

## Mocking External Dependencies

### Pattern: Mock API Calls

**Use Case:** Test code that calls external APIs without making real calls

**Pattern:**
```python
from unittest.mock import Mock, patch

def test_with_mock_api():
    """Test with mocked API."""
    mock_api = Mock()
    mock_api.get_data.return_value = {"status": "success"}

    result = process_api_data(mock_api)

    assert result["status"] == "success"
    mock_api.get_data.assert_called_once()

@patch('module.external_api_call')
def test_with_patch(mock_api_call):
    """Test with patched external call."""
    mock_api_call.return_value = {"data": "test"}

    result = function_that_calls_api()

    assert result["data"] == "test"
```

**Benefits:**
- Fast tests (no network calls)
- Deterministic results
- Test error conditions easily

---

## Testing Exceptions

### Pattern: Verify Error Handling

**Use Case:** Ensure functions raise expected exceptions

**Pattern:**
```python
import pytest

def test_raises_exception():
    """Test that function raises expected exception."""
    with pytest.raises(ValueError, match="Invalid input"):
        process_invalid_input("bad_data")

def test_exception_details():
    """Test exception message and attributes."""
    with pytest.raises(ValueError) as exc_info:
        raise_custom_error()

    assert "Expected error message" in str(exc_info.value)
    assert exc_info.value.code == "INVALID_INPUT"
```

**Benefits:**
- Validates error handling
- Ensures proper exception types
- Verifies error messages

---

## Integration Testing

### Pattern: Database Integration Tests

**Use Case:** Test complete database operations

**Pattern:**
```python
@pytest.mark.integration
def test_redis_neo4j_integration(redis_client, neo4j_session):
    """Test Redis and Neo4j integration."""
    # Store session in Redis
    session_id = "session123"
    redis_client.set(f"session:{session_id}", "active")

    # Create narrative graph in Neo4j
    neo4j_session.run(
        "CREATE (s:Session {id: $id})",
        id=session_id
    )

    # Verify integration
    assert redis_client.get(f"session:{session_id}") == "active"
    result = neo4j_session.run(
        "MATCH (s:Session {id: $id}) RETURN s",
        id=session_id
    )
    assert result.single() is not None
```

**Benefits:**
- Tests real database interactions
- Validates data persistence
- Catches integration issues

**Markers:**
```python
@pytest.mark.integration  # Integration test
@pytest.mark.e2e          # End-to-end test
@pytest.mark.slow         # Slow test
```

---

## Test Organization

### Pattern: Arrange-Act-Assert (AAA)

**Use Case:** Clear test structure

**Pattern:**
```python
def test_user_registration():
    """Test user registration flow."""
    # Arrange: Set up test data
    user_data = {
        "username": "testuser",
        "email": "test@example.com"
    }
    mock_db = MockDatabase()

    # Act: Execute functionality
    result = register_user(user_data, mock_db)

    # Assert: Verify outcome
    assert result.success is True
    assert result.user_id is not None
    assert mock_db.users_count() == 1
```

**Benefits:**
- Clear test structure
- Easy to understand
- Maintainable

---

## Coverage Optimization

### Pattern: Focus on Critical Paths

**Use Case:** Achieve high coverage efficiently

**Strategy:**
1. **Test public APIs first** (highest value)
2. **Test error conditions** (often missed)
3. **Test edge cases** (boundary conditions)
4. **Test integration points** (component interactions)

**Example:**
```python
# 1. Test public API
def test_public_api():
    """Test main functionality."""
    result = public_function("input")
    assert result == "expected"

# 2. Test error conditions
def test_error_handling():
    """Test error cases."""
    with pytest.raises(ValueError):
        public_function(None)

# 3. Test edge cases
@pytest.mark.parametrize("input,expected", [
    ("", ""),           # Empty input
    ("a", "A"),         # Single character
    ("x" * 1000, ...),  # Large input
])
def test_edge_cases(input, expected):
    """Test boundary conditions."""
    assert public_function(input) == expected

# 4. Test integration
@pytest.mark.integration
def test_integration():
    """Test component interaction."""
    result = integrated_function()
    assert result.success
```

---

## Test Data Management

### Pattern: Fixture-Based Test Data

**Use Case:** Reusable, consistent test data

**Pattern:**
```python
# In tests/conftest.py
@pytest.fixture
def sample_user():
    """Sample user data."""
    return {
        "id": "user123",
        "username": "testuser",
        "email": "test@example.com",
        "preferences": {"theme": "dark"}
    }

@pytest.fixture
def sample_conversation():
    """Sample conversation history."""
    return [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"},
    ]

# In test file
def test_with_sample_data(sample_user, sample_conversation):
    """Test using sample data."""
    result = process_user(sample_user, sample_conversation)
    assert result is not None
```

**Benefits:**
- Consistent test data
- Easy to maintain
- Reduces duplication

---

## Cleanup and Teardown

### Pattern: Automatic Cleanup

**Use Case:** Ensure tests clean up after themselves

**Pattern:**
```python
@pytest.fixture
def temp_database():
    """Temporary database for testing."""
    db = create_test_database()
    yield db
    db.cleanup()  # Automatic cleanup

def test_with_cleanup(temp_database):
    """Test with automatic cleanup."""
    temp_database.insert("test_data")
    assert temp_database.count() == 1
    # Cleanup happens automatically
```

**Benefits:**
- No manual cleanup needed
- Tests don't affect each other
- Prevents resource leaks

---

## Performance Testing

### Pattern: Benchmark Critical Operations

**Use Case:** Ensure performance requirements are met

**Pattern:**
```python
import time

def test_performance():
    """Test operation performance."""
    start = time.time()

    result = expensive_operation()

    duration = time.time() - start

    assert result is not None
    assert duration < 1.0  # Must complete in <1 second
```

**Advanced Pattern:**
```python
import pytest

@pytest.mark.benchmark
def test_benchmark(benchmark):
    """Benchmark operation."""
    result = benchmark(expensive_operation)
    assert result is not None
```

---

## Common Testing Mistakes

### Mistake 1: Testing Implementation Details

**❌ Wrong:**
```python
def test_internal_method():
    """Test private method."""
    obj = MyClass()
    assert obj._internal_method() == "value"
```

**✅ Correct:**
```python
def test_public_behavior():
    """Test public API behavior."""
    obj = MyClass()
    assert obj.public_method() == "expected"
```

### Mistake 2: Tests Depending on Order

**❌ Wrong:**
```python
def test_step_1():
    global state
    state = "initialized"

def test_step_2():
    # Depends on test_step_1 running first
    assert state == "initialized"
```

**✅ Correct:**
```python
@pytest.fixture
def initialized_state():
    return "initialized"

def test_step_1(initialized_state):
    assert initialized_state == "initialized"

def test_step_2(initialized_state):
    assert initialized_state == "initialized"
```

### Mistake 3: Using sleep() for Timing

**❌ Wrong:**
```python
def test_async_operation():
    start_async_operation()
    time.sleep(1)  # Wait for completion
    assert operation_complete()
```

**✅ Correct:**
```python
@pytest.mark.asyncio
async def test_async_operation():
    await async_operation()
    assert operation_complete()
```

---

## Test Markers

### Pattern: Categorize Tests

**Use Case:** Run specific test subsets

**Pattern:**
```python
import pytest

@pytest.mark.unit
def test_unit_functionality():
    """Unit test."""
    pass

@pytest.mark.integration
def test_integration_functionality():
    """Integration test."""
    pass

@pytest.mark.e2e
def test_e2e_functionality():
    """End-to-end test."""
    pass

@pytest.mark.slow
def test_slow_operation():
    """Slow test."""
    pass
```

**Usage:**
```bash
# Run only unit tests
uvx pytest -m unit

# Run integration and e2e tests
uvx pytest -m "integration or e2e"

# Skip slow tests
uvx pytest -m "not slow"
```

---

## TTA-Specific Patterns

### Pattern: Testing Agent Orchestration

```python
@pytest.mark.asyncio
async def test_agent_orchestration(mock_agent, redis_client):
    """Test agent orchestration flow."""
    orchestrator = AgentOrchestrator(redis_client)
    orchestrator.register_agent("agent1", mock_agent)

    result = await orchestrator.execute_workflow("test_workflow")

    assert result.success is True
    assert len(result.agent_responses) > 0
```

### Pattern: Testing Player Experience

```python
def test_player_interaction(mock_player, game_session):
    """Test player interaction flow."""
    player = create_player(mock_player)

    response = player.take_action("explore", game_session)

    assert response.action_type == "explore"
    assert response.narrative_update is not None
```

---

## Resources

### Documentation
- Testing Instructions: `.augment/instructions/testing.instructions.md`
- Pytest Documentation: https://docs.pytest.org/
- pytest-asyncio: https://pytest-asyncio.readthedocs.io/

### Code
- Test Fixtures: `tests/conftest.py`
- Unit Tests: `tests/test_*.py`
- Integration Tests: `tests/integration/`
- E2E Tests: `tests/e2e/`

---

**Note:** This file should be updated with new testing patterns as they are discovered and validated.
