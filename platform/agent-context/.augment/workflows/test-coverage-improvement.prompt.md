# Agentic Workflow: Test Coverage Improvement

**Purpose:** Systematically increase test coverage to meet component maturity thresholds
**Persona:** TTA.dev Expert Agent (High Reliability, Security First)
**Observability:** Langfuse Tracing Enabled

**Input Requirements:**
- Component name
- Current coverage percentage
- Target coverage threshold (60%/70%/80%)
- Target maturity stage (development/staging/production)

---

## Workflow Description

This workflow guides the systematic improvement of test coverage for a component, ensuring comprehensive testing while meeting TTA quality gate thresholds for component maturity progression.

**Key Principles:**
- **Full Observability:** All actions traced via Langfuse
- Focus on critical code paths first
- Write meaningful tests, not just coverage
- Use AAA pattern (Arrange-Act-Assert)
- Test behavior, not implementation
- Maintain test quality and readability

---

## Step-by-Step Process

### Step 1: Analyze Current Coverage

**Goal:** Understand current coverage and identify gaps

**Actions:**
1. Run coverage report with missing lines
2. Generate HTML coverage report
3. Identify uncovered code sections
4. Prioritize critical uncovered code
5. Categorize gaps (unit, integration, E2E)

**Observability Integration (Langfuse):**
```python
# Start trace for coverage improvement
from .hypertool.instrumentation.langfuse_integration import LangfuseIntegration

langfuse = LangfuseIntegration()
trace = langfuse.start_trace(
    name="test-coverage-improvement",
    persona="qa-engineer",
    chatmode="test-coverage"
)

# Log initial analysis
langfuse.create_generation(
    trace=trace,
    name="coverage-analysis",
    model="gemini-2.5-flash",
    prompt="Analyzing coverage gaps...",
    completion="Identified critical gaps in core logic."
)
```

**Tools:**
```bash
# Generate coverage report
uv run pytest tests/component_name/ \
    --cov=src/component_name \
    --cov-report=html \
    --cov-report=term-missing

# Open HTML report
open htmlcov/index.html

# View coverage summary
uv run pytest tests/component_name/ \
    --cov=src/component_name \
    --cov-report=term
```

**Analysis Questions:**
- What is current coverage percentage?
- What is target coverage threshold?
- Which files have lowest coverage?
- Which code paths are critical but untested?
- Are there any dead code sections?

**Output:**
```
Coverage Report:
Name                           Stmts   Miss  Cover   Missing
------------------------------------------------------------
src/component/core.py            100     40    60%   45-60, 75-90
src/component/utils.py            50     20    60%   30-40, 45-50
src/component/integration.py     80     50    38%   10-30, 50-80
------------------------------------------------------------
TOTAL                            230     110   52%

Target: 70% (staging)
Gap: 18% (need to cover ~41 more statements)
```

**AI Context Integration:**
```bash
# Create session for coverage improvement
python .augment/context/cli.py new coverage-improvement-component-2025-10-20

# Track initial analysis
python .augment/context/cli.py add coverage-improvement-component-2025-10-20 \
    "Coverage analysis: Current 52%, Target 70%, Gap 18%. Critical gaps: integration.py (38%)" \
    --importance 1.0
```

---

### Step 2: Prioritize Coverage Gaps

**Goal:** Identify which uncovered code to test first

**Prioritization Criteria:**
1. **Critical Business Logic:** Core functionality, high-risk areas
2. **Error Handling:** Exception paths, edge cases
3. **Integration Points:** Database operations, API calls
4. **Public APIs:** Exposed functions/methods
5. **Complex Logic:** Conditional branches, loops

**Priority Matrix:**
```
High Priority (Test First):
- Critical business logic (uncovered)
- Error handling paths (uncovered)
- Integration points (uncovered)
- Public API methods (uncovered)

Medium Priority (Test Second):
- Helper functions (uncovered)
- Validation logic (uncovered)
- Data transformations (uncovered)

Low Priority (Test Last):
- Trivial getters/setters
- Simple property access
- Logging statements
- Dead code (consider removing)
```

**Example Prioritization:**
```python
# HIGH PRIORITY: Critical business logic uncovered
async def process_narrative_branch(
    session_id: str,
    branch_id: str,
    redis: Redis,
    neo4j: Session
) -> NarrativeNode:
    """Process narrative branch selection."""
    # Lines 45-60 UNCOVERED - HIGH PRIORITY
    # This is core gameplay logic
    ...

# MEDIUM PRIORITY: Validation logic uncovered
def validate_player_action(action: PlayerAction) -> bool:
    """Validate player action."""
    # Lines 30-40 UNCOVERED - MEDIUM PRIORITY
    # Important but not critical path
    ...

# LOW PRIORITY: Simple getter uncovered
@property
def session_id(self) -> str:
    """Get session ID."""
    # Line 10 UNCOVERED - LOW PRIORITY
    return self._session_id
```

**Validation Criteria:**
- [ ] Critical code paths identified
- [ ] Priorities assigned
- [ ] Test plan created

**AI Context Integration:**
```bash
# Track prioritization
python .augment/context/cli.py add coverage-improvement-component-2025-10-20 \
    "Prioritized gaps: HIGH: process_narrative_branch, MEDIUM: validate_player_action" \
    --importance 0.9
```

---

### Step 3: Write Unit Tests for High Priority Gaps

**Goal:** Cover critical business logic with unit tests

**Actions:**
1. Write tests for high-priority uncovered code
2. Use AAA pattern (Arrange-Act-Assert)
3. Mock external dependencies
4. Test happy path and error cases
5. Use parametrized tests for multiple scenarios
6. Verify coverage increases

**Test Writing Guidelines:**
- One test per behavior
- Clear test names describing what is tested
- Arrange-Act-Assert structure
- Mock external dependencies (Redis, Neo4j, APIs)
- Test both success and failure cases

**Example Unit Tests:**
```python
import pytest
from unittest.mock import AsyncMock, Mock

@pytest.mark.asyncio
async def test_process_narrative_branch_success():
    """Test successful narrative branch processing."""
    # Arrange
    session_id = "session123"
    branch_id = "branch456"
    mock_redis = AsyncMock()
    mock_neo4j = Mock()

    # Mock Redis response
    mock_redis.get.return_value = '{"current_node": "node1"}'

    # Mock Neo4j response
    mock_result = Mock()
    mock_result.single.return_value = {"n": {"id": "node2", "content": "..."}}
    mock_neo4j.run.return_value = mock_result

    # Act
    result = await process_narrative_branch(
        session_id, branch_id, mock_redis, mock_neo4j
    )

    # Assert
    assert result.id == "node2"
    mock_redis.get.assert_called_once_with(f"session:{session_id}")
    mock_neo4j.run.assert_called_once()

@pytest.mark.asyncio
async def test_process_narrative_branch_invalid_session():
    """Test narrative branch processing with invalid session."""
    # Arrange
    session_id = "invalid"
    branch_id = "branch456"
    mock_redis = AsyncMock()
    mock_neo4j = Mock()

    # Mock Redis returns None (session not found)
    mock_redis.get.return_value = None

    # Act & Assert
    with pytest.raises(SessionNotFoundError):
        await process_narrative_branch(
            session_id, branch_id, mock_redis, mock_neo4j
        )

@pytest.mark.parametrize("branch_id,expected_node", [
    ("branch1", "node2"),
    ("branch2", "node3"),
    ("branch3", "node4"),
])
@pytest.mark.asyncio
async def test_process_narrative_branch_multiple_branches(
    branch_id, expected_node
):
    """Test narrative branch processing with different branches."""
    # Arrange
    session_id = "session123"
    mock_redis = AsyncMock()
    mock_neo4j = Mock()

    # Mock responses
    mock_redis.get.return_value = '{"current_node": "node1"}'
    mock_result = Mock()
    mock_result.single.return_value = {"n": {"id": expected_node}}
    mock_neo4j.run.return_value = mock_result

    # Act
    result = await process_narrative_branch(
        session_id, branch_id, mock_redis, mock_neo4j
    )

    # Assert
    assert result.id == expected_node
```

**Validation Criteria:**
- [ ] High-priority gaps covered
- [ ] Tests follow AAA pattern
- [ ] Both success and failure cases tested
- [ ] Coverage increased
- [ ] All tests pass

**Tools:**
```bash
# Run new tests
uv run pytest tests/component_name/test_new.py -v

# Check coverage increase
uv run pytest tests/component_name/ \
    --cov=src/component_name \
    --cov-report=term
```

**AI Context Integration:**
```bash
# Track unit test progress
python .augment/context/cli.py add coverage-improvement-component-2025-10-20 \
    "Unit tests added: process_narrative_branch (3 tests), coverage now 62%" \
    --importance 0.9
```

---

### Step 4: Write Integration Tests for Medium Priority Gaps

**Goal:** Cover integration points with real dependencies

**Actions:**
1. Write integration tests for database operations
2. Use real Redis and Neo4j test instances
3. Test data persistence and retrieval
4. Test transaction handling
5. Clean up test data after tests

**Integration Test Guidelines:**
- Use `@pytest.mark.integration` marker
- Use fixtures for database connections
- Test with real databases (not mocks)
- Clean up test data in teardown
- Test complete workflows

**Example Integration Tests:**
```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_narrative_branch_persistence(redis_client, neo4j_session):
    """Test narrative branch persists to databases."""
    # Arrange
    session_id = "session123"
    branch_id = "branch456"

    # Create initial session in Redis
    await redis_client.set(
        f"session:{session_id}",
        '{"current_node": "node1"}'
    )

    # Create nodes in Neo4j
    neo4j_session.run(
        "CREATE (n1:Node {id: 'node1'})-[:BRANCH {id: $branch_id}]->(n2:Node {id: 'node2'})",
        branch_id=branch_id
    )

    # Act
    result = await process_narrative_branch(
        session_id, branch_id, redis_client, neo4j_session
    )

    # Assert
    assert result.id == "node2"

    # Verify Redis updated
    session_data = await redis_client.get(f"session:{session_id}")
    assert "node2" in session_data

    # Verify Neo4j traversal recorded
    traversal = neo4j_session.run(
        "MATCH (s:Session {id: $session_id})-[:TRAVERSED]->(n:Node) RETURN n",
        session_id=session_id
    )
    assert traversal.single() is not None

    # Cleanup
    await redis_client.delete(f"session:{session_id}")
    neo4j_session.run("MATCH (n) WHERE n.id IN ['node1', 'node2'] DETACH DELETE n")

@pytest.mark.integration
@pytest.mark.asyncio
async def test_narrative_branch_transaction_rollback(redis_client, neo4j_session):
    """Test transaction rollback on error."""
    # Arrange
    session_id = "session123"
    branch_id = "invalid_branch"

    await redis_client.set(
        f"session:{session_id}",
        '{"current_node": "node1"}'
    )

    # Act & Assert
    with pytest.raises(BranchNotFoundError):
        await process_narrative_branch(
            session_id, branch_id, redis_client, neo4j_session
        )

    # Verify Redis not modified (transaction rolled back)
    session_data = await redis_client.get(f"session:{session_id}")
    assert "node1" in session_data  # Still at original node

    # Cleanup
    await redis_client.delete(f"session:{session_id}")
```

**Validation Criteria:**
- [ ] Integration points covered
- [ ] Tests use real databases
- [ ] Data persistence verified
- [ ] Transaction handling tested
- [ ] Test data cleaned up
- [ ] Coverage increased

**Tools:**
```bash
# Run integration tests
uv run pytest tests/integration/ -v -m integration

# Check coverage
uv run pytest tests/ \
    --cov=src/component_name \
    --cov-report=term
```

---

### Step 5: Verify Coverage Threshold Met

**Goal:** Confirm coverage meets target threshold

**Actions:**
1. Run full test suite with coverage
2. Generate coverage report
3. Verify coverage ≥ target threshold
4. Identify any remaining critical gaps
5. Write additional tests if needed

**Validation Criteria:**
- [ ] Coverage ≥ target threshold (60%/70%/80%)
- [ ] All tests pass
- [ ] Critical code paths covered
- [ ] No regressions introduced

**Tools:**
```bash
# Run full coverage check
uv run pytest tests/component_name/ \
    --cov=src/component_name \
    --cov-report=html \
    --cov-report=term

# Check if threshold met
uv run pytest tests/component_name/ \
    --cov=src/component_name \
    --cov-fail-under=70  # Fails if coverage < 70%
```

**Expected Output:**
```
Coverage Report:
Name                           Stmts   Miss  Cover
----------------------------------------------------
src/component/core.py            100     25    75%
src/component/utils.py            50     10    80%
src/component/integration.py     80     20    75%
----------------------------------------------------
TOTAL                            230     55    76%

✅ Coverage threshold met: 76% ≥ 70%
```

**AI Context Integration:**
```bash
# Track coverage achievement
python .augment/context/cli.py add coverage-improvement-component-2025-10-20 \
    "Coverage threshold met: 76% ≥ 70%. Added 15 unit tests, 5 integration tests." \
    --importance 1.0
```

---

### Step 6: Run Quality Gates

**Goal:** Validate all quality standards met

**Actions:**
1. Run full quality gate suite
2. Verify all gates pass
3. Fix any issues
4. Re-run until all pass

**Quality Gates:**
- [ ] Test coverage ≥ threshold
- [ ] All tests pass (100%)
- [ ] Linting clean (ruff)
- [ ] Type checking clean (pyright)
- [ ] Security scan clean (detect-secrets)

**Tools:**
```bash
# Run quality gates via workflow
python scripts/workflow/spec_to_production.py \
    --spec specs/component_name.md \
    --component component_name \
    --target staging

# Or run individually
uv run pytest tests/component_name/ --cov=src/component_name
uvx ruff check src/component_name/ tests/component_name/
uvx pyright src/component_name/
uvx detect-secrets scan src/component_name/
```

---

## Output/Deliverables

### Test Artifacts
- [ ] New unit tests (tests/)
- [ ] New integration tests (tests/integration/)
- [ ] Coverage report (htmlcov/)
- [ ] Test execution report

### Quality Reports
- [ ] Coverage ≥ target threshold
- [ ] All quality gates pass
- [ ] No regressions

### Documentation
- [ ] Test patterns documented
- [ ] Coverage improvements tracked

---

## Integration with Phase 1 Primitives

### AI Context Management
```bash
# Track coverage improvement journey
python .augment/context/cli.py add coverage-improvement-component-2025-10-20 \
    "Coverage improvement complete: 52% → 76%. Tests added: 20 total." \
    --importance 1.0
```

### Error Recovery
- Automatic retry for flaky tests
- Test isolation to prevent cascading failures

### Development Observability
- Coverage metrics tracked
- Test execution times recorded
- Dashboard shows coverage trends

---

## Resources

### TTA Documentation
- Testing Instructions: `.augment/instructions/testing.instructions.md`
- Testing Patterns: `.augment/memory/testing-patterns.memory.md`
- Quality Gates: `.augment/instructions/quality-gates.instructions.md`

### Related Workflows
- Quality Gate Fix: `.augment/workflows/quality-gate-fix.prompt.md`
- Feature Implementation: `.augment/workflows/feature-implementation.prompt.md`

---

**Note:** Focus on meaningful tests that verify behavior, not just increase coverage numbers.



---
**Logseq:** [[TTA.dev/Platform/Agent-context/.augment/Workflows/Test-coverage-improvement.prompt]]
