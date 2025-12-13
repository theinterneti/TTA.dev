---
applyTo:
  - "tests/**"
  - "src/**/test_*.py"
  - "conftest.py"
  - "pytest.ini"
tags: ['testing']
description: "Mandatory testing standards for TTA's Comprehensive Test Battery. Applies to test, testing, pytest, coverage, test battery, unit test, and integration test code."
priority: 8
category: "testing"
---

# Comprehensive Test Battery Instructions

This file enforces mandatory testing standards by applying guidelines only to test files. Instructions specify goals like maintaining an 85% mutation score or structuring unit tests according to TTA's Comprehensive Test Battery.

## Testing Philosophy

### Test Pyramid
- **Unit Tests (70%)**: Fast, isolated, focused on single units
- **Integration Tests (20%)**: Test component interactions
- **E2E Tests (10%)**: Test complete user workflows

### Quality Metrics
- **Development**: ≥70% coverage, ≥75% mutation score
- **Staging**: ≥80% coverage, ≥80% mutation score
- **Production**: ≥85% coverage, ≥85% mutation score

## Test Organization

### Directory Structure
```
tests/
├── unit/                    # Unit tests (fast, isolated)
│   ├── agent_orchestration/
│   ├── components/
│   └── player_experience/
├── integration/             # Integration tests (component interactions)
│   ├── redis/
│   ├── neo4j/
│   └── api/
├── e2e/                     # End-to-end tests (complete workflows)
│   ├── authentication/
│   ├── gameplay/
│   └── narrative/
├── comprehensive_battery/   # Production-like test scenarios
│   ├── standard/
│   ├── adversarial/
│   ├── load_stress/
│   ├── data_pipeline/
│   └── dashboard/
└── conftest.py             # Shared fixtures
```

### Test Naming Conventions
```python
# Unit tests
def test_circuit_breaker_opens_after_threshold():
    """Test that circuit breaker opens after failure threshold"""
    pass

# Integration tests
def test_redis_message_coordinator_sends_and_receives():
    """Test Redis message coordination end-to-end"""
    pass

# E2E tests
def test_complete_gameplay_session():
    """Test complete gameplay session from login to narrative generation"""
    pass
```

## Unit Testing Patterns

### Test Structure (AAA Pattern)
```python
def test_agent_processes_input_successfully():
    # Arrange
    agent = InputProcessingAgent()
    user_input = "I want to explore the forest"

    # Act
    result = agent.process(user_input)

    # Assert
    assert result.intent == "explore"
    assert result.location == "forest"
    assert result.confidence > 0.8
```

### Mocking External Dependencies
```python
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_agent_with_mocked_llm():
    # Mock external LLM call
    with patch('src.ai_components.llm_client.LLMClient.generate') as mock_generate:
        mock_generate.return_value = "Mocked response"

        agent = NarrativeGenerationAgent()
        result = await agent.generate_narrative("user input")

        assert result == "Mocked response"
        mock_generate.assert_called_once()
```

### Parameterized Tests
```python
@pytest.mark.parametrize("input,expected", [
    ("explore forest", "explore"),
    ("talk to NPC", "interact"),
    ("check inventory", "inventory"),
])
def test_intent_detection(input, expected):
    agent = InputProcessingAgent()
    result = agent.detect_intent(input)
    assert result == expected
```

## Integration Testing Patterns

### Database Integration Tests
```python
@pytest.mark.neo4j
@pytest.mark.asyncio
async def test_player_state_persistence(neo4j_session):
    # Create player
    player_id = "test-player-123"
    player_state = {"health": 100, "location": "forest"}

    # Save to Neo4j
    await save_player_state(neo4j_session, player_id, player_state)

    # Retrieve from Neo4j
    retrieved_state = await get_player_state(neo4j_session, player_id)

    # Verify
    assert retrieved_state == player_state
```

### Redis Integration Tests
```python
@pytest.mark.redis
@pytest.mark.asyncio
async def test_message_coordination(redis_client):
    coordinator = RedisMessageCoordinator(redis_client)

    # Send message
    await coordinator.send_message(
        queue="test_queue",
        message={"data": "test"},
        ttl=60
    )

    # Receive message
    message = await coordinator.receive_message(
        queue="test_queue",
        timeout=5
    )

    assert message["data"] == "test"
```

### API Integration Tests
```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_api_authentication_flow(test_client):
    # Login
    response = await test_client.post("/api/auth/login", json={
        "username": "test_user",
        "password": "test_password"  # pragma: allowlist secret
    })

    assert response.status_code == 200
    assert "access_token" in response.json()  # pragma: allowlist secret

    # Access protected endpoint
    token = response.json()["access_token"]
    response = await test_client.get(
        "/api/player/profile",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
```

## E2E Testing Patterns

### Playwright E2E Tests
```python
@pytest.mark.e2e
def test_complete_gameplay_session(page):
    # Login
    page.goto("http://localhost:3000/login")
    page.fill("#username", "test_user")
    page.fill("#password", "test_password")
    page.click("button[type=submit]")

    # Wait for dashboard
    page.wait_for_selector("#dashboard")

    # Start gameplay
    page.click("#start-game")
    page.wait_for_selector("#game-interface")

    # Send input
    page.fill("#user-input", "explore the forest")
    page.click("#send-button")

    # Wait for narrative response
    page.wait_for_selector(".narrative-response")

    # Verify response
    response = page.text_content(".narrative-response")
    assert len(response) > 0
```

## Comprehensive Test Battery

### Standard Tests
```python
@pytest.mark.standard
def test_basic_functionality():
    """Test basic functionality works as expected"""
    pass
```

### Adversarial Tests
```python
@pytest.mark.adversarial
def test_handles_malformed_input():
    """Test system handles malformed input gracefully"""
    agent = InputProcessingAgent()

    # Test with various malformed inputs
    malformed_inputs = [
        "",  # Empty string
        " " * 10000,  # Very long whitespace
        "🔥" * 1000,  # Many emojis
        "<script>alert('xss')</script>",  # XSS attempt
    ]

    for input in malformed_inputs:
        result = agent.process(input)
        assert result is not None
        assert not result.contains_error
```

### Load/Stress Tests
```python
@pytest.mark.load
@pytest.mark.asyncio
async def test_concurrent_requests():
    """Test system handles concurrent requests"""
    import asyncio

    async def make_request():
        agent = NarrativeGenerationAgent()
        return await agent.generate_narrative("test input")

    # Make 100 concurrent requests
    tasks = [make_request() for _ in range(100)]
    results = await asyncio.gather(*tasks)

    # Verify all succeeded
    assert len(results) == 100
    assert all(r is not None for r in results)
```

### Data Pipeline Tests
```python
@pytest.mark.data_pipeline
def test_data_integrity():
    """Test data integrity through pipeline"""
    # Create test data
    input_data = {"user_id": "123", "input": "test"}

    # Process through pipeline
    processed = process_input(input_data)
    stored = store_data(processed)
    retrieved = retrieve_data(stored.id)

    # Verify integrity
    assert retrieved.user_id == input_data["user_id"]
    assert retrieved.input == input_data["input"]
```

## Fixtures and Mocks

### Automatic Mock Fallbacks
```python
# conftest.py
@pytest.fixture
def redis_client():
    """Redis client with automatic mock fallback"""
    try:
        client = redis.Redis.from_url(REDIS_URL)
        client.ping()
        return client
    except redis.ConnectionError:
        # Fall back to mock
        return MockRedis()

@pytest.fixture
async def neo4j_session():
    """Neo4j session with automatic mock fallback"""
    try:
        driver = AsyncGraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        async with driver.session() as session:
            yield session
    except Exception:
        # Fall back to mock
        yield MockNeo4jSession()
```

## Mutation Testing

### Mutation Score Requirements
- **Development**: ≥75% mutation score
- **Staging**: ≥80% mutation score
- **Production**: ≥85% mutation score

### Running Mutation Tests
```bash
# Run mutation tests
uv run cosmic-ray run --config cosmic-ray.toml

# Generate mutation report
uv run cosmic-ray report --config cosmic-ray.toml
```

### Improving Mutation Score
```python
# BAD: Test doesn't catch mutations
def test_add():
    assert add(2, 2) == 4

# GOOD: Test catches mutations
def test_add():
    assert add(2, 2) == 4
    assert add(0, 0) == 0
    assert add(-1, 1) == 0
    assert add(100, 200) == 300
```

## Test Markers

### Available Markers
```python
@pytest.mark.redis        # Requires Redis
@pytest.mark.neo4j        # Requires Neo4j
@pytest.mark.integration  # Integration test
@pytest.mark.e2e          # End-to-end test
@pytest.mark.slow         # Slow-running test
@pytest.mark.adversarial  # Adversarial test
@pytest.mark.load         # Load/stress test
@pytest.mark.standard     # Standard test
@pytest.mark.data_pipeline # Data pipeline test
```

### Running Specific Tests
```bash
# Run only unit tests
uv run pytest tests/unit/

# Run only Redis tests
uv run pytest -m redis

# Run integration tests excluding slow tests
uv run pytest -m "integration and not slow"
```

## Best Practices

### Test Independence
- Each test should be independent
- Tests should not depend on execution order
- Clean up resources after each test

### Test Coverage
- Aim for high coverage, but focus on quality
- Test edge cases and error conditions
- Test both happy path and failure scenarios

### Test Performance
- Keep unit tests fast (<100ms each)
- Use mocks for external dependencies
- Run slow tests separately

### Test Maintainability
- Use descriptive test names
- Keep tests simple and focused
- Avoid test duplication

## References

- **pytest Documentation**: https://docs.pytest.org/
- **Playwright Documentation**: https://playwright.dev/python/
- **Mutation Testing**: https://cosmic-ray.readthedocs.io/
- **Test Fixtures**: `tests/conftest.py`

---

**Last Updated**: 2025-10-26
**Status**: Active - Comprehensive test battery standards


---
**Logseq:** [[TTA.dev/Platform/Agent-context/.github/Instructions/Testing-battery.instructions]]
