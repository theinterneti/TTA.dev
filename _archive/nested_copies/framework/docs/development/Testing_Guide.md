# TTA Testing Guide

## 🧪 Testing Philosophy

The Therapeutic Text Adventure (TTA) project follows a comprehensive testing approach to ensure reliability, maintainability, and correctness. This guide outlines the testing strategy, tools, and best practices for the project.

## Testing Levels

### 1. Unit Testing

Unit tests verify that individual components work as expected in isolation.

**Key Areas:**
- Individual functions and methods
- Classes and their behaviors
- Utility modules

**Tools:**
- pytest
- pytest-mock
- pytest-cov

**Example:**
```python
def test_tool_selection():
    """Test that the tool selector correctly identifies the appropriate tool."""
    # Arrange
    selector = ToolSelector()
    tools = [
        {"name": "move", "description": "Move in a direction"},
        {"name": "look", "description": "Look around"}
    ]
    user_input = "I want to go north"
    
    # Act
    selected_tool = selector.select_tool(user_input, tools)
    
    # Assert
    assert selected_tool["name"] == "move"
```

### 2. Integration Testing

Integration tests verify that components work together correctly.

**Key Areas:**
- LLM client and model integration
- Neo4j database integration
- LangGraph workflow integration
- Tool execution and game state updates

**Tools:**
- pytest
- pytest-asyncio
- docker-compose for dependencies

**Example:**
```python
@pytest.mark.asyncio
async def test_neo4j_tool_integration():
    """Test that tools can correctly update the Neo4j database."""
    # Arrange
    neo4j_manager = Neo4jManager(uri, username, password)
    tool_registry = ToolRegistry(neo4j_manager)
    move_tool = tool_registry.get_tool("move")
    
    # Act
    result = await move_tool.execute({"direction": "north"})
    
    # Assert
    player_location = neo4j_manager.get_player_location()
    assert player_location["name"] == "Forest Clearing"
    assert result["success"] is True
```

### 3. System Testing

System tests verify that the entire system works as expected.

**Key Areas:**
- End-to-end game flows
- Complete user interactions
- Performance under load

**Tools:**
- pytest
- custom test harnesses
- performance monitoring tools

**Example:**
```python
def test_complete_game_flow():
    """Test a complete game interaction flow."""
    # Arrange
    game = GameEngine()
    
    # Act
    responses = []
    responses.append(game.process_input("look around"))
    responses.append(game.process_input("go north"))
    responses.append(game.process_input("take journal"))
    responses.append(game.process_input("examine journal"))
    
    # Assert
    assert "forest" in responses[0].lower()
    assert "clearing" in responses[1].lower()
    assert "journal" in responses[2].lower()
    assert "reflection" in responses[3].lower()
```

## Test Organization

### Directory Structure

```
tests/
├── unit/                  # Unit tests
│   ├── test_tools.py      # Tests for tools
│   ├── test_agents.py     # Tests for agents
│   └── test_models.py     # Tests for models
├── integration/           # Integration tests
│   ├── test_neo4j.py      # Tests for Neo4j integration
│   ├── test_llm.py        # Tests for LLM integration
│   └── test_langgraph.py  # Tests for LangGraph integration
├── system/                # System tests
│   ├── test_game_flow.py  # Tests for game flows
│   └── test_performance.py # Performance tests
├── conftest.py            # Shared fixtures
└── test_utils.py          # Test utilities
```

### Fixtures

Use pytest fixtures for common setup and teardown:

```python
@pytest.fixture
def neo4j_manager():
    """Create a Neo4j manager for testing."""
    # Setup
    manager = Neo4jManager(
        uri="bolt://localhost:7687",
        username="neo4j",
        password="password"
    )
    manager.clear_database()
    manager.initialize_test_data()
    
    # Provide the fixture
    yield manager
    
    # Teardown
    manager.clear_database()
    manager.close()

@pytest.fixture
def mock_llm_client():
    """Create a mock LLM client for testing."""
    class MockLLMClient:
        async def generate(self, prompt, **kwargs):
            return {"content": "Mock response"}
    
    return MockLLMClient()
```

## Testing Best Practices

### 1. Test Coverage

Aim for high test coverage, especially for critical components:

- Core game logic: 90%+ coverage
- Tool system: 90%+ coverage
- Agent system: 80%+ coverage
- Utility functions: 70%+ coverage

Run coverage reports regularly:

```bash
python -m pytest --cov=src --cov-report=html
```

### 2. Test Isolation

Ensure tests are isolated and don't depend on each other:

- Use fixtures for setup and teardown
- Mock external dependencies
- Reset state between tests

### 3. Test Naming

Use descriptive test names that explain what is being tested:

```python
def test_player_can_move_between_connected_locations():
    # Test implementation
```

### 4. Test Edge Cases

Include tests for edge cases and error conditions:

- Empty inputs
- Invalid inputs
- Boundary conditions
- Resource limitations
- Concurrent operations

### 5. Parameterized Tests

Use parameterized tests for testing multiple similar cases:

```python
@pytest.mark.parametrize("direction,expected_location", [
    ("north", "Forest Clearing"),
    ("south", "River Bank"),
    ("east", "Mountain Path"),
    ("west", "Village Entrance")
])
def test_movement_in_all_directions(direction, expected_location, neo4j_manager):
    # Test implementation
```

## Mocking

### Mocking LLM Responses

Use mocks for LLM responses to ensure deterministic tests:

```python
def test_narrative_generation(mocker):
    # Arrange
    mock_llm = mocker.patch("src.llm_client.LLMClient")
    mock_llm.return_value.generate.return_value = {
        "content": "You see a beautiful forest with tall trees."
    }
    
    narrative_generator = NarrativeGenerator(mock_llm)
    
    # Act
    result = narrative_generator.generate_description("forest")
    
    # Assert
    assert "beautiful forest" in result
    mock_llm.return_value.generate.assert_called_once()
```

### Mocking Neo4j

Use an in-memory Neo4j instance or mock for database tests:

```python
def test_neo4j_operations(mocker):
    # Arrange
    mock_driver = mocker.patch("neo4j.GraphDatabase.driver")
    mock_session = mock_driver.return_value.session.return_value
    mock_session.__enter__.return_value.run.return_value = [
        {"name": "Forest", "description": "A dense forest"}
    ]
    
    neo4j_manager = Neo4jManager("bolt://localhost:7687", "neo4j", "password")
    
    # Act
    result = neo4j_manager.get_location("Forest")
    
    # Assert
    assert result["name"] == "Forest"
    assert result["description"] == "A dense forest"
```

## Testing Asynchronous Code

Use pytest-asyncio for testing asynchronous functions:

```python
@pytest.mark.asyncio
async def test_async_tool_execution():
    # Arrange
    tool = AsyncTool()
    
    # Act
    result = await tool.execute({"param": "value"})
    
    # Assert
    assert result["success"] is True
```

## Performance Testing

Include performance tests for critical paths:

```python
def test_tool_selection_performance():
    # Arrange
    selector = ToolSelector()
    tools = [{"name": f"tool_{i}", "description": f"Description {i}"} for i in range(100)]
    user_input = "I want to use tool_50"
    
    # Act
    start_time = time.time()
    selected_tool = selector.select_tool(user_input, tools)
    end_time = time.time()
    
    # Assert
    assert end_time - start_time < 0.1  # Should complete in under 100ms
    assert selected_tool["name"] == "tool_50"
```

## Continuous Integration

Set up continuous integration to run tests automatically:

```yaml
# .github/workflows/tests.yml
name: Tests

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      neo4j:
        image: neo4j:4.4
        env:
          NEO4J_AUTH: neo4j/password
        ports:
          - 7687:7687
    
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.9
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    - name: Run tests
      run: |
        python -m pytest --cov=src
```

## Running Tests

### Running All Tests

```bash
python -m pytest
```

### Running Specific Test Files

```bash
python -m pytest tests/unit/test_tools.py
```

### Running Tests with Tags

```bash
python -m pytest -m "slow"  # Run tests marked as slow
python -m pytest -m "not slow"  # Run tests not marked as slow
```

### Running Tests with Coverage

```bash
python -m pytest --cov=src --cov-report=term
```

## Troubleshooting Tests

### Common Issues

1. **Tests hanging**: Check for unresolved promises or infinite loops
2. **Database connection errors**: Ensure Neo4j is running and accessible
3. **Flaky tests**: Look for race conditions or external dependencies
4. **Slow tests**: Consider mocking slow components or marking as slow

### Debugging Tests

Use pytest's debugging features:

```bash
python -m pytest --pdb  # Drop into debugger on failure
python -m pytest -v  # Verbose output
python -m pytest --trace  # Trace execution
```

## Conclusion

A comprehensive testing strategy is essential for maintaining the quality and reliability of the TTA project. By following these guidelines, you can ensure that your code is well-tested and robust.
