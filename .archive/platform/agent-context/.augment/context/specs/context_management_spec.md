# Primitive Specification: AI Conversation Context Management

**Version:** 1.0
**Status:** Stable
**Location:** `.augment/context/conversation_manager.py`

---

## Purpose

Manage AI conversation context windows with automatic token counting, intelligent pruning, and importance-based message retention to maintain high-quality AI assistance across long development sessions.

---

## Contract

### Inputs

#### `AIConversationContextManager` Constructor

**Parameters:**
- `max_tokens: int = 8000` - Maximum tokens per context window
- `sessions_dir: str = ".augment/context/sessions"` - Directory for session persistence

#### `create_session` Method

**Parameters:**
- `session_id: str` - Unique identifier for the session
- `max_tokens: int | None = None` - Override default max tokens

**Returns:** `ConversationContext` object

#### `add_message` Method

**Parameters:**
- `session_id: str` - Session identifier
- `role: str` - Message role ("user", "assistant", "system")
- `content: str` - Message content
- `importance: float = 1.0` - Importance score (0.0 to 1.0)
- `metadata: dict | None = None` - Optional metadata

**Returns:** None

**Side Effects:**
- Adds message to context
- Counts tokens using tiktoken
- Auto-prunes if context exceeds 80% capacity

#### `save_session` Method

**Parameters:**
- `session_id: str` - Session identifier
- `filepath: str | None = None` - Optional custom filepath

**Returns:** None

**Side Effects:**
- Writes session to JSON file

#### `load_session` Method

**Parameters:**
- `filepath: str` - Path to session JSON file

**Returns:** `ConversationContext` object

**Side Effects:**
- Loads session into memory
- Recreates context with all messages

### Outputs

#### Token Counting

**Guarantees:**
- Uses tiktoken (cl100k_base encoding) for accurate token counting
- Falls back to approximate counting (~4 chars/token) if tiktoken unavailable
- Counts tokens for each message individually
- Tracks total context tokens

#### Pruning Strategy

**Hybrid Pruning Algorithm:**

1. **Always Preserve:**
   - System messages (role="system")
   - High-importance messages (importance > 0.8)
   - Recent messages (last 5 messages)

2. **Prune When:**
   - Context exceeds 80% of max_tokens
   - New message would exceed capacity

3. **Pruning Order:**
   - Remove oldest, lowest-importance messages first
   - Never remove preserved messages
   - Continue until sufficient space available

**Guarantees:**
- Context never exceeds max_tokens
- Critical information preserved
- Recent context maintained
- Graceful degradation under pressure

#### Session Persistence

**Format:** JSON with ISO 8601 timestamps

**Structure:**
```json
{
  "session_id": "string",
  "messages": [
    {
      "role": "string",
      "content": "string",
      "timestamp": "ISO 8601",
      "importance": 0.0-1.0,
      "metadata": {}
    }
  ],
  "metadata": {}
}
```

**Guarantees:**
- Sessions persist across restarts
- Timestamps in UTC
- Metadata preserved
- Human-readable format

### Guarantees

1. **Token Limit Enforcement**
   - Context never exceeds max_tokens
   - Auto-pruning at 80% capacity
   - Graceful handling of large messages

2. **Importance-Based Retention**
   - High-importance messages (>0.8) always preserved
   - System messages always preserved
   - Recent messages (last 5) always preserved

3. **Accurate Token Counting**
   - Uses OpenAI's tiktoken when available
   - Fallback to approximate counting
   - Per-message and total token tracking

4. **Session Persistence**
   - Sessions saved to JSON files
   - Sessions loadable across restarts
   - Metadata preserved

5. **Thread Safety**
   - Single-threaded design (not thread-safe)
   - For multi-threaded use, add locking

---

## Usage Patterns

### Pattern 1: Basic Session Management

```python
from conversation_manager import AIConversationContextManager

# Create manager
manager = AIConversationContextManager(max_tokens=8000)

# Create session
session_id = "tta-feature-xyz-2025-10-20"
context = manager.create_session(session_id)

# Add messages
manager.add_message(
    session_id=session_id,
    role="system",
    content="TTA Architecture Context: ...",
    importance=1.0
)

manager.add_message(
    session_id=session_id,
    role="user",
    content="Implement feature X",
    importance=0.9
)

# Save session
manager.save_session(session_id)
```

### Pattern 2: Load and Continue Session

```python
# Load existing session
context = manager.load_session(".augment/context/sessions/tta-feature-xyz.json")

# Continue conversation
manager.add_message(
    session_id=context.session_id,
    role="user",
    content="Update feature X with Y",
    importance=0.9
)

# Save updated session
manager.save_session(context.session_id)
```

### Pattern 3: Importance Scoring

```python
# Architectural decisions (critical)
manager.add_message(
    session_id=session_id,
    role="user",
    content="We decided to use hybrid pruning strategy",
    importance=1.0,
    metadata={"type": "architectural_decision"}
)

# Task requests (very important)
manager.add_message(
    session_id=session_id,
    role="user",
    content="Implement error recovery framework",
    importance=0.9,
    metadata={"type": "task_request"}
)

# Implementation details (important)
manager.add_message(
    session_id=session_id,
    role="assistant",
    content="I'll create error_recovery.py with retry logic",
    importance=0.7,
    metadata={"type": "implementation"}
)

# General discussion (normal)
manager.add_message(
    session_id=session_id,
    role="user",
    content="Looks good",
    importance=0.5,
    metadata={"type": "acknowledgment"}
)
```

### Pattern 4: Context Summary

```python
# Get summary
summary = manager.get_context_summary(session_id)
print(summary)

# Output:
# Session: tta-feature-xyz-2025-10-20
# Messages: 15
# Tokens: 3,456/8,000
# Utilization: 43.2%
```

### Pattern 5: CLI Usage

```bash
# Create new session
python .augment/context/cli.py new tta-feature-xyz

# Add message
python .augment/context/cli.py add tta-feature-xyz "Implement feature X" --importance 0.9

# Show session
python .augment/context/cli.py show tta-feature-xyz

# List all sessions
python .augment/context/cli.py list
```

---

## Integration Points

### With Augment Agent

```markdown
# .augment/rules/ai-context-management.md

At start of AI session:
1. Load or create session
2. Add architecture context (importance=1.0)
3. Track important decisions
4. Save at end of session
```

### With Development Workflow

```python
# Track development decisions
def track_decision(decision: str):
    manager.add_message(
        session_id=current_session,
        role="user",
        content=decision,
        importance=1.0,
        metadata={"type": "decision"}
    )
```

### With Error Recovery

```python
from primitives.error_recovery import with_retry

@with_retry()
def save_context_with_retry(session_id):
    manager.save_session(session_id)
```

### With Observability

```python
from observability.dev_metrics import track_execution

@track_execution("context_save")
def save_context(session_id):
    manager.save_session(session_id)
```

---

## Performance Characteristics

### Time Complexity

- **add_message:** O(n) where n = number of messages (for pruning)
- **save_session:** O(n) where n = number of messages
- **load_session:** O(n) where n = number of messages
- **get_context_summary:** O(1)

### Space Complexity

- **Per Session:** O(max_tokens) - bounded by token limit
- **Per Message:** O(content_length + metadata_size)
- **Total:** O(num_sessions * max_tokens)

### Token Counting Performance

- **tiktoken:** ~1ms per message (fast)
- **Fallback:** ~0.1ms per message (very fast)

**Recommendation:** Install tiktoken for accurate counting

---

## Testing Considerations

### Unit Tests

```python
def test_pruning_preserves_important_messages():
    manager = AIConversationContextManager(max_tokens=100)
    session_id = "test"
    manager.create_session(session_id)

    # Add high-importance message
    manager.add_message(session_id, "user", "Important", importance=1.0)

    # Add many low-importance messages to trigger pruning
    for i in range(20):
        manager.add_message(session_id, "user", f"Message {i}", importance=0.5)

    # High-importance message should still be present
    context = manager.contexts[session_id]
    important_messages = [m for m in context.messages if m.importance == 1.0]
    assert len(important_messages) > 0
```

### Integration Tests

```python
def test_session_persistence():
    manager = AIConversationContextManager()
    session_id = "test-persistence"

    # Create and populate session
    manager.create_session(session_id)
    manager.add_message(session_id, "user", "Test message", importance=0.9)

    # Save session
    filepath = f".augment/context/sessions/{session_id}.json"
    manager.save_session(session_id, filepath)

    # Load session in new manager
    new_manager = AIConversationContextManager()
    loaded_context = new_manager.load_session(filepath)

    # Verify message preserved
    assert len(loaded_context.messages) == 1
    assert loaded_context.messages[0].content == "Test message"
    assert loaded_context.messages[0].importance == 0.9
```

---

## Phase 2 Considerations

When integrating into TTA application:

### Agent Conversation Context

```python
# Track agent-to-agent conversations
class AgentContextManager(AIConversationContextManager):
    def add_agent_message(self, agent_name: str, content: str, importance: float):
        self.add_message(
            session_id=self.current_session,
            role="assistant",
            content=f"[{agent_name}] {content}",
            importance=importance,
            metadata={"agent": agent_name}
        )
```

### User Session Context

```python
# Track user session context
def track_user_interaction(user_id: str, interaction: str):
    manager.add_message(
        session_id=f"user-{user_id}",
        role="user",
        content=interaction,
        importance=0.8,
        metadata={"user_id": user_id, "type": "interaction"}
    )
```

### Multi-Agent Orchestration

```python
# Maintain context across agent handoffs
class MultiAgentContext:
    def __init__(self):
        self.manager = AIConversationContextManager(max_tokens=16000)

    def handoff_context(self, from_agent: str, to_agent: str):
        # Transfer relevant context to next agent
        context = self.manager.get_context_summary(from_agent)
        self.manager.add_message(
            session_id=to_agent,
            role="system",
            content=f"Context from {from_agent}: {context}",
            importance=1.0
        )
```

### Distributed Context

```python
# Store context in Redis for distributed access
import redis

class DistributedContextManager(AIConversationContextManager):
    def __init__(self, redis_client):
        super().__init__()
        self.redis = redis_client

    def save_session(self, session_id: str):
        # Save to Redis instead of file
        context = self.contexts[session_id]
        self.redis.set(f"context:{session_id}", json.dumps(context))
```

---

## Limitations

1. **Not Thread-Safe**
   - Single-threaded design
   - Add locking for multi-threaded use

2. **No Distributed Coordination**
   - Sessions are per-process
   - For distributed systems, use Redis/database backend

3. **Token Counting Accuracy**
   - Depends on tiktoken availability
   - Fallback is approximate (~4 chars/token)

4. **No Compression**
   - Messages stored as-is
   - Consider compression for large contexts

5. **No Encryption**
   - Sessions stored in plain text
   - Add encryption for sensitive data

---

**Status:** Stable - Ready for production use
**Last Updated:** 2025-10-20
**Next Review:** Before Phase 2 integration
