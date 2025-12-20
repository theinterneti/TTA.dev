---
applyTo:
  - pattern: "tests/**/*.py"
  - pattern: "**/*_test.py"
  - pattern: "**/*.spec.ts"
tags: ["testing", "quality-assurance", "coverage", "pytest", "playwright"]
description: "Testing requirements, coverage standards, and test organization guidelines for TTA"
---

# Testing Requirements

## Overview

This instruction set defines testing standards for TTA. All code must include comprehensive tests with minimum coverage thresholds based on component maturity.

## Coverage Thresholds

### By Component Maturity

| Stage | Threshold | Requirement |
|-------|-----------|-------------|
| Development | ≥60% | Active development |
| Staging | ≥70% | Pre-production validation |
| Production | ≥80% | Live deployment |
| Player-facing | ≥80% | Always (critical) |

### Coverage Calculation
```bash
# Generate coverage report
uvx pytest --cov=src --cov-report=html

# Check coverage threshold
uvx pytest --cov=src --cov-fail-under=70
```

## Test Organization

### Directory Structure
```
tests/
├── unit/                    # Fast, isolated unit tests
│   ├── test_models.py
│   ├── test_services.py
│   └── test_validators.py
├── integration/             # Tests with real services
│   ├── test_api_integration.py
│   ├── test_database_integration.py
│   └── test_workflow_integration.py
├── e2e/                     # End-to-end tests
│   ├── 01-authentication.spec.ts
│   ├── 02-gameplay.spec.ts
│   └── 03-session-management.spec.ts
└── conftest.py              # Shared fixtures
```

## Unit Testing

### AAA Pattern (Arrange-Act-Assert)

```python
import pytest
from src.services import PlayerService

def test_player_creation_success():
    """Test successful player creation."""
    # Arrange
    service = PlayerService()
    player_data = {
        "name": "Test Player",
        "email": "test@example.com"
    }

    # Act
    player = service.create_player(player_data)

    # Assert
    assert player.name == "Test Player"
    assert player.email == "test@example.com"
    assert player.id is not None
```

### Error Testing

```python
def test_player_creation_invalid_email():
    """Test player creation with invalid email."""
    service = PlayerService()

    with pytest.raises(ValueError, match="Invalid email"):
        service.create_player({"name": "Test", "email": "invalid"})
```

## Async Testing

### Async Fixtures

```python
import pytest_asyncio
import aioredis

@pytest_asyncio.fixture
async def redis_client():
    """Provide Redis client for tests."""
    client = await aioredis.from_url("redis://localhost:6379")
    yield client
    await client.close()

@pytest.mark.asyncio
async def test_redis_integration(redis_client):
    """Test Redis integration."""
    await redis_client.set("key", "value")
    value = await redis_client.get("key")
    assert value == b"value"
```

### Async Test Functions

```python
@pytest.mark.asyncio
async def test_workflow_execution():
    """Test async workflow execution."""
    result = await execute_workflow(
        player_id="test_player",
        input_text="Hello"
    )
    assert result.success
    assert result.response is not None
```

## Integration Testing

### Database Integration

```python
@pytest.mark.integration
@pytest.mark.neo4j
def test_player_persistence(neo4j_session):
    """Test player data persistence in Neo4j."""
    # Create player
    player = Player(name="Test", email="test@example.com")
    neo4j_session.create(player)

    # Retrieve player
    retrieved = neo4j_session.get(Player, player.id)
    assert retrieved.name == "Test"
```

### API Integration

```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_api_endpoint(client):
    """Test API endpoint."""
    response = await client.post(
        "/api/players",
        json={"name": "Test", "email": "test@example.com"}
    )
    assert response.status_code == 201
    assert response.json()["name"] == "Test"
```

## E2E Testing with Playwright

### Test Structure

```typescript
import { test, expect } from '@playwright/test';

test.describe('Player Authentication', () => {
  test('should login successfully', async ({ page }) => {
    // Navigate to login page
    await page.goto('/login');

    // Fill login form
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="password"]', 'password123');

    // Submit form
    await page.click('button:has-text("Login")');

    // Verify redirect to dashboard
    await expect(page).toHaveURL('/dashboard');
    await expect(page.locator('text=Welcome')).toBeVisible();
  });
});
```

### Best Practices

```typescript
// ✅ Correct: Use data-testid for reliable selectors
await page.click('[data-testid="submit-button"]');

// ❌ Incorrect: Fragile selectors
await page.click('button.btn.btn-primary.mt-2');

// ✅ Correct: Wait for elements
await expect(page.locator('text=Success')).toBeVisible();

// ❌ Incorrect: No waiting
const text = await page.textContent('text=Success');
```

## Pytest Markers

### Available Markers

```python
@pytest.mark.unit              # Unit test
@pytest.mark.integration       # Integration test
@pytest.mark.e2e               # End-to-end test
@pytest.mark.slow              # Slow test (>1 second)
@pytest.mark.neo4j             # Requires Neo4j
@pytest.mark.redis             # Requires Redis
@pytest.mark.asyncio           # Async test
@pytest.mark.player_experience # Player experience component
@pytest.mark.agent_orchestration # Agent orchestration component
```

### Running Specific Tests

```bash
# Run only unit tests
uvx pytest -m unit

# Run integration tests
uvx pytest -m integration

# Run tests requiring Redis
uvx pytest -m redis --redis

# Skip slow tests
uvx pytest -m "not slow"
```

## Code Review Checklist

- [ ] All new code has tests
- [ ] Coverage threshold met
- [ ] Tests follow AAA pattern
- [ ] Async tests use proper fixtures
- [ ] Error cases tested
- [ ] Edge cases covered
- [ ] Tests are deterministic
- [ ] No hardcoded test data
- [ ] Fixtures properly scoped
- [ ] Documentation updated

## Common Patterns

### Fixture Reuse

```python
@pytest.fixture
def player_data():
    """Provide test player data."""
    return {
        "name": "Test Player",
        "email": "test@example.com"
    }

def test_player_creation(player_data):
    """Test player creation."""
    player = create_player(player_data)
    assert player.name == player_data["name"]
```

### Mocking External Services

```python
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_ai_response_generation():
    """Test AI response generation with mocked API."""
    with patch('src.services.openrouter_client') as mock_client:
        mock_client.generate.return_value = "AI response"

        result = await generate_response("player input")
        assert result == "AI response"
```

## References

- Pytest Documentation: https://docs.pytest.org/
- Playwright Documentation: https://playwright.dev/
- Coverage.py: https://coverage.readthedocs.io/
- Testing Best Practices: https://testingpython.com/
