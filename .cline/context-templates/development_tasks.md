# Cline Task-Specific Context Templates

**Purpose:** Dynamic context injection based on current development task to provide more relevant TTA.dev tool suggestions

## Template 1: New Service Development

**When to Use:** Creating a new service, API, or microservice

**Trigger Phrases:**

- "Create a new service"
- "Build a new API"
- "Set up a microservice"
- "New service architecture"

**Context Template:**

```markdown
# New Service Development Context

## Recommended Primitives for New Services

**Start with these primitives for production-ready services:**

1. **CachePrimitive** - Cache expensive operations (LLM calls, DB queries)
2. **RetryPrimitive** - Handle transient failures with backoff
3. **TimeoutPrimitive** - Prevent hanging operations
4. **FallbackPrimitive** - High availability with provider fallbacks

**Example service architecture:**
```python
# Layer 1: Cache for cost optimization
cached = CachePrimitive(primitive=expensive_call, ttl_seconds=3600)

# Layer 2: Timeout for reliability
timed = TimeoutPrimitive(primitive=cached, timeout_seconds=30)

# Layer 3: Retry for resilience
retry = RetryPrimitive(primitive=timed, max_retries=3)

# Layer 4: Fallback for availability
reliable = FallbackPrimitive(primary=retry, fallbacks=[backup_api])

# Use with proper context
context = WorkflowContext(workflow_id="new-service")
result = await reliable.execute(data, context)
```

## Key Files for New Services

- `src/<service_name>/` - Service implementation
- `tests/test_<service_name>.py` - Unit tests
- `examples/<service_name>_demo.py` - Usage examples
- `pyproject.toml` - Dependencies

```

## Template 2: Performance Optimization

**When to Use:** Optimizing slow operations, reducing costs, improving response times

**Trigger Phrases:**
- "Optimize performance"
- "Reduce response time"
- "Speed up the system"
- "Improve latency"
- "Reduce costs"

**Context Template:**
```markdown
# Performance Optimization Context

## TTA.dev Performance Primitives

**For performance optimization, start with:**

1. **CachePrimitive** - 40-60% cost reduction, 100x faster cache hits
   - Use for: LLM calls, database queries, API responses
   - TTL: 1 hour for stable data, 5-15 minutes for dynamic data

2. **RouterPrimitive** - Route to fastest/cheapest available service
   - Use for: Multiple LLM providers, API endpoints
   - Criteria: response time, cost, quality

3. **MemoryPrimitive** - Hybrid memory with zero Redis setup
   - Use for: Conversation history, session data
   - Auto-upgrades to Redis when available

**Performance Pattern Example:**
```python
# Intelligent routing with cost optimization
service = RouterPrimitive(
    routes={
        "fast_cheap": cached_gpt35,      # Fast, cost-effective
        "quality": gpt4,                 # High quality, slower
        "backup": claude_sonnet         # Fallback option
    },
    router_fn=lambda data, ctx: "fast_cheap" if data.get("priority") == "normal" else "quality",
    default="fast_cheap"
)
```

## Monitoring Performance

- Use Prometheus metrics in primitives
- Monitor cache hit rates, response times
- Set up alerts for performance degradation

```

## Template 3: Error Handling & Resilience

**When to Use:** Improving reliability, handling failures, building fault-tolerant systems

**Trigger Phrases:**
- "Handle errors"
- "Make it resilient"
- "Deal with failures"
- "Add fault tolerance"
- "Prevent cascading failures"

**Context Template:**
```markdown
# Error Handling & Resilience Context

## TTA.dev Recovery Primitives

**For building resilient systems, use:**

1. **RetryPrimitive** - Automatic retry with smart backoff
   - Exponential backoff for rate limits
   - Linear backoff for quick recovery
   - Jitter to prevent thundering herd

2. **FallbackPrimitive** - Graceful degradation
   - Multiple provider fallbacks
   - Different capability levels
   - Automatic provider switching

3. **TimeoutPrimitive** - Circuit breaker pattern
   - Prevent hanging operations
   - Quick failure detection
   - Resource cleanup

4. **CompensationPrimitive** - Saga pattern
   - Distributed transaction rollback
   - Multi-step operation reversal
   - State consistency

**Resilience Pattern Example:**
```python
# Maximum resilience stack
resilient_service = (
    TimeoutPrimitive(timeout_seconds=30) >>  # Circuit breaker
    RetryPrimitive(max_retries=3, backoff="exponential") >>  # Retry with backoff
    FallbackPrimitive(primary=primary_api, fallbacks=[backup1, backup2]) >>  # Graceful degradation
    CompensationPrimitive(steps=[(step1, rollback1), (step2, rollback2)])  # Rollback capability
)
```

## Error Handling Best Practices

- Always use WorkflowContext for correlation IDs
- Log failures with context for debugging
- Choose appropriate retry strategies per failure type
- Monitor retry patterns and adjust thresholds

```

## Template 4: Multi-Agent Coordination

**When to Use:** Building workflows with multiple agents, complex orchestration, agent handoffs

**Trigger Phrases:**
- "Multi-agent workflow"
- "Agent coordination"
- "Complex orchestration"
- "Multiple agents working together"
- "Agent handoff"

**Context Template:**
```markdown
# Multi-Agent Coordination Context

## TTA.dev Orchestration Primitives

**For coordinating multiple agents:**

1. **SequentialPrimitive** - Chain agents in order (>>)
   ```python
   agent_workflow = agent1 >> agent2 >> agent3
   ```

2. **ParallelPrimitive** - Run agents concurrently (|)

   ```python
   parallel_agents = agent1 | agent2 | agent3
   ```

3. **DelegationPrimitive** - Orchestrator → Executor pattern

   ```python
   # Orchestrator plans, executor implements
   workflow = DelegationPrimitive(orchestrator=planner, executor=worker)
   ```

4. **RouterPrimitive** - Route tasks to appropriate agents

   ```python
   task_router = RouterPrimitive(
       routes={
           "planning": planner_agent,
           "coding": coder_agent,
           "testing": tester_agent
       },
       router_fn=classify_task
   )
   ```

## Cline ↔ Copilot Handoff Pattern

```python
# Clines handles complex research and planning
research_workflow = research_agent >> planning_agent

# Copilot handles quick implementation
implementation = implement_agent

# Combined workflow
full_pipeline = research_workflow >> implementation
```

## Agent State Management

- Use WorkflowContext for agent state
- Pass data between agents via composition
- Monitor agent performance independently
- Implement circuit breakers per agent type

```

## Template 5: Testing & Quality Assurance

**When to Use:** Writing tests, ensuring code quality, test-driven development

**Trigger Phrases:**
- "Add tests"
- "Write unit tests"
- "Test-driven development"
- "Ensure code quality"
- "Test coverage"

**Context Template:**
```markdown
# Testing & Quality Assurance Context

## TTA.dev Testing Primitives

**For comprehensive testing:**

1. **MockPrimitive** - Test workflows without external dependencies
   ```python
   from tta_dev_primitives.testing import MockPrimitive

   # Mock LLM calls in tests
   mock_llm = MockPrimitive(return_value={"text": "test response"})
   workflow = input_processor >> mock_llm >> validator
   ```

2. **Test patterns for primitives:**
   - Test success cases
   - Test failure cases
   - Test error handling
   - Test performance characteristics

**Test Example:**

```python
@pytest.mark.asyncio
async def test_retry_primitive():
    mock_api = MockPrimitive(side_effect=[APIError(), APIError(), {"result": "success"}])
    retry = RetryPrimitive(primitive=mock_api, max_retries=3)

    context = WorkflowContext(workflow_id="test")
    result = await retry.execute({}, context)

    assert result == {"result": "success"}
    assert mock_api.call_count == 3
```

## Quality Gates for TTA.dev

- **100% test coverage** for new code
- **Type hints** on all functions
- **Async/await** for I/O operations
- **Context passing** for tracing
- **Error handling** with specific exceptions
- **Documentation** with examples

```

## How to Use Context Templates

1. **Detection:** Cline identifies trigger phrases in user requests
2. **Loading:** Appropriate template is loaded based on detected task type
3. **Context Injection:** Template content is added to the conversation context
4. **Response:** Cline responds with task-specific primitive suggestions and examples

## Adding New Templates

To add a new template:

1. Create a new section in this file
2. Define trigger phrases that identify the task type
3. Write context with relevant primitives and examples
4. Include code examples specific to the task type
5. Add best practices and common patterns

---

**Note:** These templates are loaded dynamically based on the development task detected in cline's conversation, providing more targeted and relevant TTA.dev primitive suggestions.


---
**Logseq:** [[TTA.dev/.cline/Context-templates/Development_tasks]]
