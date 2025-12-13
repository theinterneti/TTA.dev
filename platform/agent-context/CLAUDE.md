# TTA (Therapeutic Text Adventure) - Claude Agent Instructions

**Agent Instructions** - This file is specifically recognized and used by Anthropic Claude agents (or agents compatible with the standard). It provides Claude-specific guidance and context for working with the TTA codebase.

## Claude-Specific Capabilities

### Advanced Reasoning
Claude excels at:
- **Multi-step reasoning**: Breaking down complex problems into manageable steps
- **Code analysis**: Understanding architectural patterns and dependencies
- **Context synthesis**: Combining information from multiple sources
- **Error diagnosis**: Identifying root causes of failures

### Recommended Usage Patterns

#### For Complex Refactoring
Use Claude's extended context window (200K tokens) to:
1. Load entire component context
2. Analyze dependencies and call sites
3. Plan refactoring strategy
4. Execute changes with validation

#### For Architectural Decisions
Leverage Claude's reasoning for:
1. Evaluating design alternatives
2. Assessing trade-offs
3. Identifying potential issues
4. Recommending best practices

#### For Debugging
Use Claude's analytical capabilities to:
1. Reproduce issues systematically
2. Trace execution flow
3. Identify edge cases
4. Propose comprehensive fixes

## TTA-Specific Guidance

### Multi-Agent Orchestration
When working with TTA's agent orchestration:
- **Always use circuit breakers** for external agent calls
- **Implement retry logic** with exponential backoff
- **Provide fallback mechanisms** for graceful degradation
- **Monitor agent health** through the agent registry

### Circuit Breaker Pattern
```python
from src.agent_orchestration.circuit_breaker import CircuitBreaker, CircuitBreakerOpenError

# Wrap agent calls with circuit breaker
circuit_breaker = CircuitBreaker(
    name="agent_call",
    failure_threshold=5,
    recovery_timeout=60,
    half_open_max_calls=3
)

try:
    result = await circuit_breaker.call(agent_function, *args, **kwargs)
except CircuitBreakerOpenError:
    # Circuit is open, use fallback
    result = fallback_response()
```

### Redis Message Coordination
When working with Redis-based messaging:
- **Use RedisMessageCoordinator** for async message passing
- **Implement message TTL** to prevent stale messages
- **Handle connection failures** gracefully
- **Monitor queue depths** for performance issues

### Neo4j Graph Operations
When working with Neo4j:
- **Use parameterized queries** to prevent injection
- **Implement connection pooling** for performance
- **Handle transaction failures** with retry logic
- **Monitor query performance** with EXPLAIN

## Component Maturity Workflow

**See AGENTS.md** for complete maturity workflow, quality gates, and promotion process.

## Testing Strategy

**See AGENTS.md** for comprehensive test battery, mock fallbacks, test markers, and testing patterns.

## Code Quality Standards

**See AGENTS.md** for SOLID principles, file size limits, and quality gates.

## Error Handling Patterns

### Retry with Backoff
```python
from src.common.error_recovery import retry_with_backoff, RetryConfig

@retry_with_backoff(RetryConfig(max_retries=3, base_delay=1.0))
async def risky_operation():
    # Operation that may fail transiently
    pass
```

### Circuit Breaker
```python
from src.agent_orchestration.circuit_breaker import CircuitBreaker

circuit_breaker = CircuitBreaker(name="external_service")
result = await circuit_breaker.call(external_service_call)
```

### Fallback Mechanisms
```python
try:
    result = await primary_operation()
except Exception as e:
    logger.warning(f"Primary operation failed: {e}")
    result = fallback_operation()
```

## AI Context Management

**See AGENTS.md** for session management commands and importance scoring guidelines.

## MCP Server Integration

### Context7 for Documentation
Use Context7 to fetch up-to-date documentation:
```
Using Context7, show me latest FastAPI streaming patterns
```

### Serena for Code Navigation
Use Serena tools for code analysis:
- `find_symbol_Serena`: Locate architectural elements
- `get_symbols_overview_Serena`: Understand module organization
- `read_memory_Serena`: Retrieve design decisions
- `write_memory_Serena`: Store design decisions

### Sequential Thinking for Complex Tasks
Use Sequential Thinking for multi-step procedures:
- Component promotion workflows
- Complex refactoring tasks
- Migration procedures
- Debugging workflows

## Common Workflows

**See AGENTS.md** for common workflows (feature implementation, bug fix, refactoring).

## Development Commands

**See AGENTS.md** for common development commands (environment setup, quality checks, testing, services).

## Best Practices

**See AGENTS.md** for best practices (before/during/after implementation, refactoring, testing).

## Related Documentation

- **AGENTS.md** - Universal context for all AI agents
- **GEMINI.md** - Gemini CLI sub-agent context
- **.github/copilot-instructions.md** - GitHub Copilot instructions
- **docs/development/** - Detailed development guides
- **specs/** - Component and feature specifications

---

**Last Updated**: 2025-10-26
**Status**: Active - Claude-specific instructions and context


---
**Logseq:** [[TTA.dev/Platform/Agent-context/Claude]]
