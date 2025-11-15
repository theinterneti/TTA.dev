# Context: Refactoring

**Purpose:** Code refactoring patterns and strategies for improving TTA codebase maintainability

**When to Use:**
- Improving code quality
- Reducing complexity
- Eliminating code smells
- Preparing for new features
- Fixing technical debt

---

## Refactoring Principles

### 1. Preserve Behavior
- **Goal:** Refactoring should not change functionality
- **Strategy:** Run tests before and after refactoring
- **Verification:** All tests pass, coverage maintained

### 2. Small Steps
- **Goal:** Make incremental changes
- **Strategy:** One refactoring at a time
- **Verification:** Commit after each successful refactoring

### 3. Test Coverage
- **Goal:** Ensure adequate test coverage before refactoring
- **Strategy:** Add tests if coverage < 60%
- **Verification:** Coverage ≥60% (dev), ≥70% (staging), ≥80% (production)

---

## Common Refactoring Patterns

### 1. Extract Function

**When to Use:**
- Function is too long (>50 lines)
- Code has multiple levels of abstraction
- Code is duplicated

**Example:**
```python
# Before: Long function with multiple responsibilities
async def process_player_action(session_id: str, action: dict):
    # Validate action
    if not action.get("type"):
        raise ValueError("Action type required")
    if action["type"] not in ["explore", "interact", "speak"]:
        raise ValueError("Invalid action type")
    
    # Get session
    redis = await create_redis_connection()
    session_data = await redis.get(f"session:{session_id}")
    if not session_data:
        raise ValueError("Session not found")
    session = Session.parse_raw(session_data)
    
    # Process action
    if action["type"] == "explore":
        result = await process_explore(session, action)
    elif action["type"] == "interact":
        result = await process_interact(session, action)
    else:
        result = await process_speak(session, action)
    
    # Update session
    session.last_action = action
    await redis.set(f"session:{session_id}", session.json())
    
    return result

# After: Extracted functions
async def validate_action(action: dict) -> None:
    """Validate player action."""
    if not action.get("type"):
        raise ValueError("Action type required")
    if action["type"] not in ["explore", "interact", "speak"]:
        raise ValueError("Invalid action type")

async def get_session(session_id: str) -> Session:
    """Get session from Redis."""
    redis = await create_redis_connection()
    session_data = await redis.get(f"session:{session_id}")
    if not session_data:
        raise ValueError("Session not found")
    return Session.parse_raw(session_data)

async def update_session(session_id: str, session: Session) -> None:
    """Update session in Redis."""
    redis = await create_redis_connection()
    await redis.set(f"session:{session_id}", session.json())

async def process_player_action(session_id: str, action: dict):
    """Process player action."""
    validate_action(action)
    session = await get_session(session_id)
    
    # Process action
    if action["type"] == "explore":
        result = await process_explore(session, action)
    elif action["type"] == "interact":
        result = await process_interact(session, action)
    else:
        result = await process_speak(session, action)
    
    session.last_action = action
    await update_session(session_id, session)
    
    return result
```

---

### 2. Extract Class

**When to Use:**
- Class has too many responsibilities
- Group of functions operate on same data
- Need better encapsulation

**Example:**
```python
# Before: Functions scattered across module
async def create_narrative_node(content: str, session_id: str):
    neo4j = create_neo4j_session()
    result = neo4j.run(
        "CREATE (n:NarrativeNode {content: $content, session_id: $session_id}) RETURN n",
        content=content,
        session_id=session_id
    )
    return result.single()["n"]

async def get_narrative_history(session_id: str):
    neo4j = create_neo4j_session()
    result = neo4j.run(
        "MATCH (n:NarrativeNode {session_id: $session_id}) RETURN n ORDER BY n.timestamp",
        session_id=session_id
    )
    return [record["n"] for record in result]

# After: Extracted class
class NarrativeRepository:
    """Repository for narrative operations."""
    
    def __init__(self, neo4j_session):
        self.neo4j = neo4j_session
    
    async def create_node(self, content: str, session_id: str) -> NarrativeNode:
        """Create narrative node."""
        result = self.neo4j.run(
            "CREATE (n:NarrativeNode {content: $content, session_id: $session_id}) RETURN n",
            content=content,
            session_id=session_id
        )
        return NarrativeNode.from_neo4j(result.single()["n"])
    
    async def get_history(self, session_id: str) -> list[NarrativeNode]:
        """Get narrative history for session."""
        result = self.neo4j.run(
            "MATCH (n:NarrativeNode {session_id: $session_id}) RETURN n ORDER BY n.timestamp",
            session_id=session_id
        )
        return [NarrativeNode.from_neo4j(record["n"]) for record in result]
```

---

### 3. Simplify Conditional

**When to Use:**
- Complex nested conditionals
- Multiple conditions checking same thing
- Difficult to understand logic

**Example:**
```python
# Before: Complex nested conditionals
def get_action_response(action_type: str, context: dict):
    if action_type == "explore":
        if context.get("location") == "forest":
            if context.get("time") == "night":
                return "You explore the dark forest..."
            else:
                return "You explore the forest..."
        else:
            return "You explore the area..."
    elif action_type == "interact":
        if context.get("target"):
            return f"You interact with {context['target']}..."
        else:
            return "You look around for something to interact with..."
    else:
        return "You perform the action..."

# After: Simplified with early returns and helper functions
def get_action_response(action_type: str, context: dict):
    """Get response for player action."""
    if action_type == "explore":
        return get_explore_response(context)
    elif action_type == "interact":
        return get_interact_response(context)
    else:
        return "You perform the action..."

def get_explore_response(context: dict) -> str:
    """Get response for explore action."""
    if context.get("location") != "forest":
        return "You explore the area..."
    
    if context.get("time") == "night":
        return "You explore the dark forest..."
    
    return "You explore the forest..."

def get_interact_response(context: dict) -> str:
    """Get response for interact action."""
    target = context.get("target")
    if not target:
        return "You look around for something to interact with..."
    
    return f"You interact with {target}..."
```

---

### 4. Replace Magic Numbers/Strings

**When to Use:**
- Hardcoded values appear multiple times
- Values have special meaning
- Need better maintainability

**Example:**
```python
# Before: Magic numbers and strings
def validate_session(session: Session):
    if len(session.id) < 10:
        raise ValueError("Invalid session ID")
    if session.max_turns > 100:
        raise ValueError("Too many turns")
    if session.status not in ["active", "paused", "completed"]:
        raise ValueError("Invalid status")

# After: Named constants
# Constants
MIN_SESSION_ID_LENGTH = 10
MAX_TURNS_LIMIT = 100

class SessionStatus:
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    
    @classmethod
    def all(cls):
        return [cls.ACTIVE, cls.PAUSED, cls.COMPLETED]

def validate_session(session: Session):
    """Validate session data."""
    if len(session.id) < MIN_SESSION_ID_LENGTH:
        raise ValueError("Invalid session ID")
    if session.max_turns > MAX_TURNS_LIMIT:
        raise ValueError("Too many turns")
    if session.status not in SessionStatus.all():
        raise ValueError("Invalid status")
```

---

### 5. Introduce Parameter Object

**When to Use:**
- Function has too many parameters (>5)
- Parameters are related
- Same parameters passed to multiple functions

**Example:**
```python
# Before: Too many parameters
async def create_session(
    user_id: str,
    max_turns: int,
    ai_provider: str,
    model: str,
    temperature: float,
    max_tokens: int,
    redis_client: Redis,
    neo4j_session: Session
):
    # Implementation
    pass

# After: Parameter object
from pydantic import BaseModel

class SessionConfig(BaseModel):
    """Configuration for session creation."""
    user_id: str
    max_turns: int
    ai_provider: str
    model: str
    temperature: float
    max_tokens: int

class DatabaseClients(BaseModel):
    """Database clients."""
    redis: Redis
    neo4j: Session
    
    class Config:
        arbitrary_types_allowed = True

async def create_session(
    config: SessionConfig,
    db: DatabaseClients
):
    """Create new session."""
    # Implementation
    pass
```

---

## Refactoring Workflow

### 1. Identify Code Smell

**Common Code Smells:**
- Long functions (>50 lines)
- Large classes (>300 lines)
- Duplicated code
- Complex conditionals
- Too many parameters
- Magic numbers/strings
- Poor naming

**Tools:**
```bash
# Check code complexity
uvx radon cc src/ -a

# Check maintainability
uvx radon mi src/

# Check linting issues
uvx ruff check src/
```

---

### 2. Write Tests (If Missing)

**Goal:** Ensure behavior is preserved

**Steps:**
1. Check current coverage
2. Add tests if coverage < 60%
3. Verify all tests pass

**Commands:**
```bash
# Check coverage
uv run pytest tests/ --cov=src/component --cov-report=term

# Add tests
# ... create test file ...

# Verify tests pass
uv run pytest tests/ -v
```

---

### 3. Refactor

**Steps:**
1. Make one refactoring change
2. Run tests
3. Commit if tests pass
4. Repeat

**Best Practices:**
- One refactoring at a time
- Run tests after each change
- Commit frequently
- Use descriptive commit messages

---

### 4. Verify

**Verification Checklist:**
- [ ] All tests pass
- [ ] Coverage maintained or improved
- [ ] Linting clean
- [ ] Type checking clean
- [ ] Code is more readable
- [ ] Complexity reduced

**Commands:**
```bash
# Run all checks
uv run pytest tests/ -v
uv run pytest tests/ --cov=src/ --cov-report=term
uvx ruff check src/
uvx pyright src/
```

---

## TTA-Specific Refactoring Scenarios

### Scenario 1: Refactor Agent Orchestration

**Goal:** Improve testability and maintainability

**Before:**
```python
# Monolithic orchestrator
class AgentOrchestrator:
    async def process_turn(self, session_id: str, user_input: str):
        # 200+ lines of mixed responsibilities
        pass
```

**After:**
```python
# Separated concerns
class AgentOrchestrator:
    def __init__(
        self,
        session_repo: SessionRepository,
        narrative_repo: NarrativeRepository,
        ai_provider: AIProvider
    ):
        self.session_repo = session_repo
        self.narrative_repo = narrative_repo
        self.ai_provider = ai_provider
    
    async def process_turn(self, session_id: str, user_input: str):
        session = await self.session_repo.get(session_id)
        context = await self.narrative_repo.get_context(session_id)
        response = await self.ai_provider.generate(user_input, context)
        await self.narrative_repo.add_node(session_id, response)
        return response
```

---

### Scenario 2: Refactor Database Access

**Goal:** Centralize database operations

**Before:**
```python
# Scattered database calls
async def get_user_sessions(user_id: str):
    redis = await create_redis_connection()
    keys = await redis.keys(f"session:{user_id}:*")
    sessions = []
    for key in keys:
        data = await redis.get(key)
        sessions.append(Session.parse_raw(data))
    return sessions
```

**After:**
```python
# Repository pattern
class SessionRepository:
    def __init__(self, redis: Redis):
        self.redis = redis
    
    async def get_user_sessions(self, user_id: str) -> list[Session]:
        """Get all sessions for user."""
        keys = await self.redis.keys(f"session:{user_id}:*")
        sessions = []
        for key in keys:
            data = await self.redis.get(key)
            sessions.append(Session.parse_raw(data))
        return sessions
```

---

## Resources

### TTA Documentation
- Global Instructions: `.augment/instructions/global.instructions.md`
- Testing Patterns: `.augment/memory/testing-patterns.memory.md`

### External Resources
- Refactoring Catalog: https://refactoring.com/catalog/
- Clean Code: https://www.oreilly.com/library/view/clean-code-a/9780136083238/

---

**Note:** Always run tests before and after refactoring to ensure behavior is preserved.

