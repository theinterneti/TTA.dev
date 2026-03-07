# Context: Integration Testing

**Purpose:** Integration testing and component interaction guidance for TTA development

**When to Use:**
- Testing component interactions
- Validating database integration
- Testing API endpoints
- Verifying end-to-end flows
- Preparing for staging deployment

---

## Integration Testing Principles

### 1. Test Real Interactions
- Use real databases (Redis, Neo4j)
- Test actual API calls
- Verify complete workflows
- Avoid excessive mocking

### 2. Isolation
- Each test is independent
- Clean up after tests
- Use test databases
- Reset state between tests

### 3. Realistic Scenarios
- Test real user workflows
- Use realistic data
- Test error conditions
- Verify edge cases

---

## TTA Integration Test Organization

### Test Structure
```
tests/
├── test_*.py              # Unit tests
├── integration/           # Integration tests
│   ├── conftest.py       # Integration fixtures
│   ├── test_session_integration.py
│   ├── test_narrative_integration.py
│   └── test_agent_integration.py
└── e2e/                  # End-to-end tests
    ├── conftest.py
    └── test_gameplay_e2e.py
```

### Test Markers
```python
# Mark integration tests
@pytest.mark.integration
async def test_session_persistence():
    pass

# Mark E2E tests
@pytest.mark.e2e
async def test_complete_gameplay():
    pass

# Run only integration tests
# uv run pytest tests/integration/ -v -m integration
```

---

## Integration Test Fixtures

### Database Fixtures

**Redis Fixture:**
```python
# tests/integration/conftest.py
import pytest
from redis.asyncio import Redis

@pytest.fixture
async def redis_client():
    """Redis client for integration testing."""
    client = Redis(
        host="localhost",
        port=6379,
        db=1,  # Use test database
        decode_responses=True
    )

    yield client

    # Cleanup
    await client.flushdb()
    await client.close()
```

**Neo4j Fixture:**
```python
from neo4j import GraphDatabase

@pytest.fixture
def neo4j_session():
    """Neo4j session for integration testing."""
    driver = GraphDatabase.driver(
        "neo4j://localhost:7687",
        auth=("neo4j", "test_password")
    )
    session = driver.session(database="test")

    yield session

    # Cleanup
    session.run("MATCH (n) DETACH DELETE n")
    session.close()
    driver.close()
```

**Combined Database Fixture:**
```python
@pytest.fixture
async def db_clients(redis_client, neo4j_session):
    """Combined database clients."""
    return {
        "redis": redis_client,
        "neo4j": neo4j_session
    }
```

---

## Integration Test Patterns

### 1. Session Integration Tests

**Test Session Creation and Persistence:**
```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_session_creation_and_persistence(redis_client, neo4j_session):
    """Test session is created and persisted to both databases."""
    # Arrange
    user_id = "test_user_123"
    session_repo = SessionRepository(redis_client, neo4j_session)

    # Act
    session = await session_repo.create(user_id)

    # Assert - Redis
    cached = await redis_client.get(f"session:{session.id}")
    assert cached is not None
    cached_session = Session.parse_raw(cached)
    assert cached_session.user_id == user_id

    # Assert - Neo4j
    result = neo4j_session.run(
        "MATCH (s:Session {id: $id}) RETURN s",
        id=session.id
    )
    neo4j_session_data = result.single()
    assert neo4j_session_data is not None
    assert neo4j_session_data["s"]["user_id"] == user_id
```

**Test Session Retrieval:**
```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_session_retrieval(redis_client, neo4j_session):
    """Test session can be retrieved from cache and database."""
    # Arrange
    session_repo = SessionRepository(redis_client, neo4j_session)
    original_session = await session_repo.create("test_user")

    # Act - First retrieval (from Redis)
    retrieved_session_1 = await session_repo.get(original_session.id)

    # Clear Redis cache
    await redis_client.delete(f"session:{original_session.id}")

    # Act - Second retrieval (from Neo4j)
    retrieved_session_2 = await session_repo.get(original_session.id)

    # Assert
    assert retrieved_session_1.id == original_session.id
    assert retrieved_session_2.id == original_session.id
    assert retrieved_session_1.user_id == retrieved_session_2.user_id
```

---

### 2. Narrative Integration Tests

**Test Narrative Node Creation:**
```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_narrative_node_creation(neo4j_session):
    """Test narrative node is created in graph database."""
    # Arrange
    narrative_repo = NarrativeRepository(neo4j_session)
    session_id = "test_session_123"
    content = "You enter a dark forest..."

    # Act
    node = await narrative_repo.create_node(session_id, content)

    # Assert
    result = neo4j_session.run(
        "MATCH (n:NarrativeNode {id: $id}) RETURN n",
        id=node.id
    )
    retrieved_node = result.single()
    assert retrieved_node is not None
    assert retrieved_node["n"]["content"] == content
    assert retrieved_node["n"]["session_id"] == session_id
```

**Test Narrative Chain:**
```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_narrative_chain(neo4j_session):
    """Test narrative nodes are linked in sequence."""
    # Arrange
    narrative_repo = NarrativeRepository(neo4j_session)
    session_id = "test_session_123"

    # Act - Create chain of nodes
    node1 = await narrative_repo.create_node(session_id, "First node")
    node2 = await narrative_repo.create_node(session_id, "Second node", previous_id=node1.id)
    node3 = await narrative_repo.create_node(session_id, "Third node", previous_id=node2.id)

    # Assert - Verify chain
    result = neo4j_session.run(
        "MATCH path = (start:NarrativeNode {id: $start_id})-[:NEXT*]->(end:NarrativeNode {id: $end_id}) "
        "RETURN length(path) as chain_length",
        start_id=node1.id,
        end_id=node3.id
    )
    chain = result.single()
    assert chain is not None
    assert chain["chain_length"] == 2  # 2 relationships between 3 nodes
```

---

### 3. Agent Orchestration Integration Tests

**Test Complete Turn Processing:**
```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_agent_turn_processing(redis_client, neo4j_session):
    """Test complete turn processing with all components."""
    # Arrange
    session_repo = SessionRepository(redis_client, neo4j_session)
    narrative_repo = NarrativeRepository(neo4j_session)
    ai_provider = MockAIProvider()  # Use mock for AI

    orchestrator = AgentOrchestrator(
        session_repo=session_repo,
        narrative_repo=narrative_repo,
        ai_provider=ai_provider
    )

    # Create session
    session = await session_repo.create("test_user")

    # Act
    user_input = "I explore the forest"
    response = await orchestrator.process_turn(session.id, user_input)

    # Assert - Response generated
    assert response is not None
    assert len(response) > 0

    # Assert - Session updated in Redis
    updated_session = await session_repo.get(session.id)
    assert updated_session.turn_count == 1

    # Assert - Narrative node created in Neo4j
    history = await narrative_repo.get_history(session.id)
    assert len(history) == 1
    assert history[0].content == response
```

---

### 4. API Integration Tests

**Test API Endpoint:**
```python
from fastapi.testclient import TestClient
from src.main import app

@pytest.mark.integration
def test_create_session_endpoint(redis_client, neo4j_session):
    """Test session creation via API endpoint."""
    # Arrange
    client = TestClient(app)

    # Act
    response = client.post(
        "/api/v1/sessions",
        json={"user_id": "test_user"}
    )

    # Assert - Response
    assert response.status_code == 200
    session_data = response.json()
    assert session_data["user_id"] == "test_user"
    assert "id" in session_data

    # Assert - Database persistence
    session_id = session_data["id"]
    cached = redis_client.get(f"session:{session_id}")
    assert cached is not None
```

---

## Error Handling Integration Tests

### Test Database Connection Errors

```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_redis_connection_error_recovery():
    """Test error recovery when Redis is unavailable."""
    # Arrange
    invalid_redis = Redis(host="invalid_host", port=9999)
    session_repo = SessionRepository(invalid_redis, neo4j_session)

    # Act & Assert
    with pytest.raises(ConnectionError):
        await session_repo.create("test_user")
```

### Test Transaction Rollback

```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_transaction_rollback_on_error(neo4j_session):
    """Test transaction is rolled back on error."""
    # Arrange
    narrative_repo = NarrativeRepository(neo4j_session)

    # Act - Simulate error during transaction
    with pytest.raises(ValueError):
        async with narrative_repo.transaction():
            await narrative_repo.create_node("session1", "Node 1")
            await narrative_repo.create_node("session1", "Node 2")
            raise ValueError("Simulated error")

    # Assert - No nodes created (transaction rolled back)
    result = neo4j_session.run("MATCH (n:NarrativeNode) RETURN count(n) as count")
    count = result.single()["count"]
    assert count == 0
```

---

## Performance Integration Tests

### Test Response Time

```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_session_creation_performance(redis_client, neo4j_session):
    """Test session creation meets performance requirements."""
    import time

    # Arrange
    session_repo = SessionRepository(redis_client, neo4j_session)

    # Act
    start = time.time()
    session = await session_repo.create("test_user")
    duration = time.time() - start

    # Assert - Should complete in < 100ms
    assert duration < 0.1, f"Session creation took {duration:.3f}s (expected < 0.1s)"
```

---

## Integration Test Best Practices

### 1. Use Test Databases
```python
# ✅ Good: Separate test database
@pytest.fixture
async def redis_client():
    client = Redis(db=1)  # Test database
    yield client
    await client.flushdb()

# ❌ Bad: Use production database
@pytest.fixture
async def redis_client():
    client = Redis(db=0)  # Production database!
    yield client
```

### 2. Clean Up After Tests
```python
# ✅ Good: Cleanup in fixture
@pytest.fixture
async def redis_client():
    client = Redis(db=1)
    yield client
    await client.flushdb()  # Clean up
    await client.close()

# ❌ Bad: No cleanup
@pytest.fixture
async def redis_client():
    client = Redis(db=1)
    yield client
    # No cleanup - state persists!
```

### 3. Test Realistic Scenarios
```python
# ✅ Good: Realistic scenario
@pytest.mark.integration
async def test_complete_gameplay_session():
    """Test complete gameplay session with multiple turns."""
    session = await create_session("user123")

    # Turn 1
    response1 = await process_turn(session.id, "I explore the forest")
    assert "forest" in response1.lower()

    # Turn 2
    response2 = await process_turn(session.id, "I look around")
    assert len(response2) > 0

    # Verify history
    history = await get_narrative_history(session.id)
    assert len(history) == 2

# ❌ Bad: Unrealistic scenario
@pytest.mark.integration
async def test_session_exists():
    """Test session exists."""
    session = await create_session("user123")
    assert session is not None
```

---

## Resources

### TTA Documentation
- Testing Instructions: `.augment/instructions/testing.instructions.md`
- Testing Patterns: `.augment/memory/testing-patterns.memory.md`
- Quality Gates: `.augment/instructions/quality-gates.instructions.md`

### External Resources
- pytest: https://docs.pytest.org/
- pytest-asyncio: https://pytest-asyncio.readthedocs.io/
- FastAPI Testing: https://fastapi.tiangolo.com/tutorial/testing/

---

**Note:** Integration tests should be run before staging deployment to ensure all components work together correctly.


---
**Logseq:** [[TTA.dev/Platform_tta_dev/Components/Augment/Core/Context/Integration.context]]
