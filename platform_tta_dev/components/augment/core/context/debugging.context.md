# Context: Debugging

**Purpose:** Systematic debugging workflows and troubleshooting strategies for TTA development.

**When to Use:** When investigating bugs, errors, test failures, or unexpected behavior.

---

## Debugging Workflow

### 1. Reproduce the Issue

**Goal:** Reliably reproduce the bug

**Steps:**
1. Gather information about the bug
2. Identify steps to reproduce
3. Reproduce locally
4. Document reproduction steps

**Questions to Ask:**
- What were you doing when the error occurred?
- What did you expect to happen?
- What actually happened?
- Can you reproduce it consistently?
- What environment (dev/staging/production)?

**Example:**
```markdown
## Bug Report

**Description:** Session state not persisting after player action

**Steps to Reproduce:**
1. Create new session
2. Perform "explore" action
3. Check session state in Redis
4. Session state is empty

**Expected:** Session state should contain action history
**Actual:** Session state is empty
**Environment:** Development (local Docker)
```

---

### 2. Isolate the Problem

**Goal:** Narrow down the root cause

**Strategies:**

#### Binary Search
- Comment out half the code
- See if bug still occurs
- Repeat until isolated

#### Add Logging
```python
import logging

logger = logging.getLogger(__name__)

async def process_action(action: PlayerAction, session: Session):
    logger.info(f"Processing action: {action.type}")
    logger.debug(f"Session state before: {session.state}")

    result = await execute_action(action)
    logger.debug(f"Action result: {result}")

    await update_session(session, result)
    logger.debug(f"Session state after: {session.state}")

    return result
```

#### Use Debugger
```python
# Add breakpoint
import pdb; pdb.set_trace()

# Or use IDE debugger
# Set breakpoint in IDE and run in debug mode
```

#### Check Assumptions
```python
# Verify assumptions with assertions
assert session is not None, "Session should not be None"
assert session.user_id, "Session should have user_id"
assert redis_client.ping(), "Redis should be connected"
```

---

### 3. Analyze the Root Cause

**Goal:** Understand why the bug occurs

**Common Root Causes:**

#### Async/Await Issues
```python
# ❌ Wrong: Missing await
async def get_session(session_id: str):
    session = redis_client.get(f"session:{session_id}")  # Missing await!
    return session

# ✅ Correct: Proper await
async def get_session(session_id: str):
    session = await redis_client.get(f"session:{session_id}")
    return session
```

#### Race Conditions
```python
# ❌ Wrong: Race condition
async def update_session(session: Session):
    current = await redis_client.get(f"session:{session.id}")
    # Another request might update here!
    updated = merge_state(current, session)
    await redis_client.set(f"session:{session.id}", updated)

# ✅ Correct: Atomic update
async def update_session(session: Session):
    await redis_client.watch(f"session:{session.id}")
    current = await redis_client.get(f"session:{session.id}")
    updated = merge_state(current, session)
    await redis_client.multi()
    await redis_client.set(f"session:{session.id}", updated)
    await redis_client.execute()
```

#### Missing Error Handling
```python
# ❌ Wrong: No error handling
async def get_ai_response(prompt: str):
    response = await ai_provider.generate(prompt)
    return response

# ✅ Correct: Proper error handling
async def get_ai_response(prompt: str):
    try:
        response = await ai_provider.generate(prompt)
        return response
    except RateLimitError:
        logger.warning("Rate limit hit, using fallback")
        return await fallback_provider.generate(prompt)
    except AIProviderError as e:
        logger.error(f"AI provider error: {e}")
        raise
```

#### Type Mismatches
```python
# ❌ Wrong: Type mismatch
def process_data(data: dict):
    return data["items"][0]  # Assumes items is list

# ✅ Correct: Type checking
def process_data(data: dict):
    items = data.get("items", [])
    if not isinstance(items, list) or not items:
        raise ValueError("Invalid data: items must be non-empty list")
    return items[0]
```

---

### 4. Fix the Bug

**Goal:** Implement a proper fix

**Principles:**
- Fix the root cause, not symptoms
- Add tests to prevent regression
- Document the fix
- Consider impact on other code

**Example Fix:**
```python
# Before: Session state not persisting
async def process_action(action: PlayerAction, session: Session):
    result = await execute_action(action)
    session.state.update(result)  # ❌ Only updates in-memory
    return result

# After: Persist to Redis
async def process_action(
    action: PlayerAction,
    session: Session,
    redis_client: Redis
):
    result = await execute_action(action)
    session.state.update(result)

    # ✅ Persist to Redis
    await redis_client.set(
        f"session:{session.id}",
        json.dumps(session.state)
    )

    return result

# Add test to prevent regression
@pytest.mark.asyncio
async def test_action_persists_state(redis_client):
    """Test that action updates persist to Redis."""
    session = Session(id="test", user_id="user123", state={})
    action = PlayerAction(type="explore")

    await process_action(action, session, redis_client)

    # Verify state persisted
    persisted = await redis_client.get(f"session:{session.id}")
    assert persisted is not None
    state = json.loads(persisted)
    assert "explore" in state
```

---

### 5. Verify the Fix

**Goal:** Ensure the bug is fixed and no regressions

**Verification Steps:**
1. Run the reproduction steps - bug should be gone
2. Run all tests - no regressions
3. Run quality gates - all pass
4. Test edge cases
5. Deploy to staging and verify

**Example:**
```bash
# 1. Reproduce bug - should be fixed
python reproduce_bug.py

# 2. Run tests
uv run pytest tests/ -v

# 3. Run quality gates
python scripts/workflow/spec_to_production.py \
    --spec specs/component.md \
    --component component \
    --target staging

# 4. Test edge cases
uv run pytest tests/test_edge_cases.py -v

# 5. Deploy to staging
kubectl set image deployment/tta-api api=tta-api:v1.0.1 -n tta-staging
```

---

## Common TTA Debugging Scenarios

### Scenario 1: Redis Connection Issues

**Symptoms:**
- `ConnectionError: Error connecting to Redis`
- Tests fail with Redis errors
- Session state not persisting

**Debugging Steps:**
```bash
# 1. Check Redis is running
docker ps | grep redis

# 2. Test connection
redis-cli ping

# 3. Check connection string
echo $REDIS_URL

# 4. Test from Python
python -c "import redis; r = redis.from_url('redis://localhost:6379'); print(r.ping())"
```

**Common Fixes:**
- Start Redis: `docker-compose up -d redis`
- Fix connection string: `REDIS_URL=redis://localhost:6379`
- Check network: `docker network inspect tta_network`

---

### Scenario 2: Neo4j Query Errors

**Symptoms:**
- `Neo4jError: Invalid Cypher syntax`
- Query returns no results
- Transaction errors

**Debugging Steps:**
```python
# 1. Test query in Neo4j Browser
# Open http://localhost:7474
# Run query directly

# 2. Add logging
logger.debug(f"Running query: {query}")
logger.debug(f"Parameters: {parameters}")

# 3. Check query result
result = session.run(query, **parameters)
records = list(result)
logger.debug(f"Query returned {len(records)} records")

# 4. Verify data exists
# MATCH (n) RETURN count(n)
```

**Common Fixes:**
- Fix Cypher syntax
- Add missing indexes
- Check parameter names
- Verify data exists

---

### Scenario 3: Async Test Failures

**Symptoms:**
- `RuntimeError: Event loop is closed`
- `RuntimeWarning: coroutine was never awaited`
- Tests hang indefinitely

**Debugging Steps:**
```python
# 1. Check pytest-asyncio marker
@pytest.mark.asyncio  # ✅ Required for async tests
async def test_async_function():
    result = await async_function()
    assert result is not None

# 2. Check await usage
result = await async_function()  # ✅ Correct
result = async_function()  # ❌ Wrong - missing await

# 3. Check fixture scope
@pytest.fixture(scope="function")  # ✅ Correct for async
async def async_fixture():
    client = await create_client()
    yield client
    await client.close()
```

**Common Fixes:**
- Add `@pytest.mark.asyncio` decorator
- Add missing `await` keywords
- Fix fixture scope
- Use `pytest-asyncio` mode

---

### Scenario 4: Quality Gate Failures

**Symptoms:**
- Coverage below threshold
- Tests failing
- Linting errors
- Type checking errors

**Debugging Steps:**
```bash
# 1. Identify which gate failed
cat workflow_report_component.json | jq '.stage_results.testing.quality_gates'

# 2. Run specific gate locally
# Coverage
uv run pytest tests/component/ --cov=src/component --cov-report=term-missing

# Tests
uv run pytest tests/component/ -v

# Linting
uvx ruff check src/component/ tests/component/

# Type checking
uvx pyright src/component/

# 3. Fix issues
# ... make changes ...

# 4. Re-run gate
# ... run command again ...
```

**Common Fixes:**
- Add missing tests for coverage
- Fix failing tests
- Run `uvx ruff check --fix` for linting
- Add type hints for type checking

---

## Debugging Tools

### 1. Python Debugger (pdb)
```python
import pdb

def buggy_function():
    x = 10
    y = 20
    pdb.set_trace()  # Debugger will stop here
    result = x + y
    return result

# Commands:
# n - next line
# s - step into function
# c - continue
# p variable - print variable
# l - list code
# q - quit
```

### 2. Logging
```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Use logging
logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message")
logger.exception("Exception with traceback")
```

### 3. IDE Debugger
- **VS Code:** Set breakpoints, run in debug mode
- **PyCharm:** Set breakpoints, run in debug mode
- **Advantages:** Visual debugging, variable inspection, call stack

### 4. Print Debugging
```python
# Quick and dirty debugging
print(f"DEBUG: variable = {variable}")
print(f"DEBUG: type = {type(variable)}")
print(f"DEBUG: dir = {dir(variable)}")
```

---

## Best Practices

### DO:
✅ Reproduce the bug reliably
✅ Add logging to understand flow
✅ Write test to catch regression
✅ Fix root cause, not symptoms
✅ Document the fix
✅ Verify no regressions
✅ Use debugger for complex issues

### DON'T:
❌ Make random changes hoping to fix
❌ Skip writing regression test
❌ Fix symptoms without understanding root cause
❌ Commit debugging code (print statements, pdb)
❌ Ignore related issues
❌ Skip verification step

---

## Resources

### TTA Documentation
- Testing Patterns: `.augment/memory/testing-patterns.memory.md`
- Component Failures: `.augment/memory/component-failures.memory.md`
- Quality Gates: `.augment/memory/quality-gates.memory.md`

### External Resources
- Python Debugger: https://docs.python.org/3/library/pdb.html
- pytest: https://docs.pytest.org/
- Redis Debugging: https://redis.io/docs/manual/cli/
- Neo4j Debugging: https://neo4j.com/docs/cypher-manual/

---

**Note:** Systematic debugging saves time. Follow the workflow, document findings, and add tests to prevent regressions.


---
**Logseq:** [[TTA.dev/Platform_tta_dev/Components/Augment/Core/Context/Debugging.context]]
