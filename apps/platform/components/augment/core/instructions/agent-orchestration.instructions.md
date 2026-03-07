---
applyTo: "src/agent_orchestration/**/*.py"
description: "Agent Orchestration component patterns: multi-agent coordination, LangGraph workflows, tool design, error recovery"
---

# Agent Orchestration Component Instructions

## Component Overview

The Agent Orchestration component coordinates TTA's multi-agent system (IPA, WBA, NGA) using LangGraph workflows, manages tool invocation, and provides error recovery mechanisms.

**Responsibilities**:
- Multi-agent workflow coordination (IPA → WBA → NGA)
- LangGraph workflow management and state persistence
- Tool registration, discovery, and invocation
- Circuit breaker and error recovery
- Therapeutic safety validation

**Boundaries**:
- Does NOT manage player sessions (delegates to player experience)
- Does NOT generate narratives directly (delegates to NGA)
- DOES coordinate agent communication and workflow execution

## Architecture Patterns

### Multi-Agent Workflow (IPA → WBA → NGA)

```
User Input
    ↓
IPA (Input Processing Agent)
    ↓ (intent, entities, safety)
WBA (World Building Agent)
    ↓ (world state updates)
NGA (Narrative Generator Agent)
    ↓ (narrative response)
User Output
```

**Key Classes**:
- `LangGraphAgentOrchestrator` - LangGraph workflow integration
- `UnifiedAgentOrchestrator` - IPA/WBA/NGA coordination
- `AgentOrchestrationService` - Main service API
- `CircuitBreaker` - Error recovery and graceful degradation

### LangGraph State Management

```python
class AgentWorkflowState(TypedDict):
    """State structure for agent workflows."""
    messages: list[BaseMessage]
    player_id: str
    session_id: str
    user_input: str

    # Agent results
    ipa_result: dict[str, Any] | None
    wba_result: dict[str, Any] | None
    nga_result: dict[str, Any] | None

    # Context
    world_context: dict[str, Any]
    therapeutic_context: dict[str, Any]
    safety_level: str

    # Output
    narrative_response: str
    next_actions: list[str]
```

## Integration Points

### With LangGraph

```python
# Build workflow graph
workflow = StateGraph(AgentWorkflowState)

# Add agent nodes
workflow.add_node("ipa", self._run_ipa)
workflow.add_node("wba", self._run_wba)
workflow.add_node("nga", self._run_nga)

# Define edges
workflow.add_edge("ipa", "wba")
workflow.add_edge("wba", "nga")
workflow.add_edge("nga", END)

# Set entry point
workflow.set_entry_point("ipa")

# Compile workflow
self.workflow = workflow.compile()
```

### With Redis (State Persistence)

```python
# Persist workflow state
workflow_key = f"workflow:{workflow_id}"
await redis_client.setex(
    workflow_key, 3600, json.dumps(workflow_state)
)

# Retrieve workflow state
cached_state = await redis_client.get(workflow_key)
if cached_state:
    workflow_state = json.loads(cached_state)
```

### With Tool System

```python
# Register tool
await tool_registry.register_tool(
    name="analyze_sentiment",
    version="1.0.0",
    callable_fn=analyze_sentiment_fn,
    safety_flags=["therapeutic_safe"]
)

# Invoke tool
result = await tool_service.invoke_tool(
    tool_name="analyze_sentiment",
    version="1.0.0",
    arguments={"text": user_input}
)
```

## Common Patterns

### Agent Workflow Execution

```python
async def execute_workflow(
    self,
    user_input: str,
    player_id: str,
    session_id: str,
    world_context: dict[str, Any] | None = None,
    therapeutic_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Execute complete agent workflow."""
    # Initialize state
    initial_state: AgentWorkflowState = {
        "messages": [HumanMessage(content=user_input)],
        "player_id": player_id,
        "session_id": session_id,
        "user_input": user_input,
        "ipa_result": None,
        "wba_result": None,
        "nga_result": None,
        "world_context": world_context or {},
        "therapeutic_context": therapeutic_context or {},
        "safety_level": "safe",
        "workflow_id": str(uuid.uuid4()),
        "narrative_response": "",
        "next_actions": [],
    }

    try:
        # Execute workflow
        result = await self.workflow.ainvoke(initial_state)

        return {
            "success": True,
            "narrative": result["narrative_response"],
            "workflow_id": result.get("workflow_id"),
            "safety_level": result["safety_level"],
            "agent_results": {
                "ipa": result.get("ipa_result"),
                "wba": result.get("wba_result"),
                "nga": result.get("nga_result"),
            },
        }
    except Exception as e:
        logger.error(f"Workflow execution error: {e}", exc_info=True)
        return {
            "success": False,
            "narrative": "I'm having trouble processing that. Could you try again?",
            "error": str(e),
            "safety_level": "safe",
        }
```

### Circuit Breaker Pattern

```python
async def call_with_circuit_breaker(
    self, func: Callable[[], Awaitable[Any]], correlation_id: str | None = None
) -> Any:
    """Execute function through circuit breaker."""
    breaker = CircuitBreaker(
        name="agent_call",
        failure_threshold=3,
        timeout_seconds=60,
        redis_client=self.redis_client
    )

    try:
        result = await breaker.call(func, correlation_id)
        return result
    except CircuitBreakerOpenError:
        logger.warning("Circuit breaker open, using fallback")
        return await self._fallback_response()
    except Exception as e:
        logger.error(f"Circuit breaker call failed: {e}")
        raise
```

### Tool Invocation with Safety Validation

```python
async def invoke_tool_safely(
    self, tool_name: str, arguments: dict[str, Any]
) -> Any:
    """Invoke tool with safety validation."""
    # Get tool spec
    spec = await self.tool_registry.get_tool(tool_name)
    if not spec:
        raise ValueError(f"Tool not found: {tool_name}")

    # Validate safety flags
    if hasattr(self.policy, "validate_safety_flags"):
        self.policy.validate_safety_flags(spec.safety_flags)

    # Invoke tool
    try:
        result = await self.tool_service.invoke_tool(
            tool_name=tool_name,
            version=spec.version,
            arguments=arguments
        )
        return result
    except Exception as e:
        logger.error(f"Tool invocation failed: {e}")
        if self.on_error:
            return self.on_error(e, spec)
        raise
```

## Testing Requirements

### Coverage Thresholds

- **Workflow orchestration**: ≥75% coverage
- **Circuit breaker**: ≥80% coverage
- **Tool system**: ≥75% coverage

### Test Organization

```
tests/agent_orchestration/
├── unit/
│   ├── test_unified_orchestrator.py
│   ├── test_circuit_breaker.py
│   └── test_tool_invocation.py
├── integration/
│   ├── test_langgraph_workflow.py
│   ├── test_agent_coordination.py
│   └── test_redis_state_persistence.py
└── e2e/
    └── test_complete_workflow.py
```

### Test Patterns

```python
@pytest.mark.integration
async def test_agent_workflow_execution(redis_client):
    """Test complete IPA → WBA → NGA workflow."""
    orchestrator = LangGraphAgentOrchestrator(redis_client=redis_client)

    result = await orchestrator.execute_workflow(
        user_input="I'm feeling anxious",
        player_id="player-1",
        session_id="session-1"
    )

    assert result["success"] is True
    assert result["narrative"] != ""
    assert result["safety_level"] == "safe"
    assert result["agent_results"]["ipa"] is not None
```

## Examples

### Example 1: Agent Registration and Coordination

```python
class UnifiedAgentOrchestrator:
    """Coordinate IPA, WBA, and NGA agents."""

    def __init__(self, redis_client: aioredis.Redis):
        self.redis_client = redis_client

        # Initialize agent adapters
        self.ipa_adapter = IPAAdapter(retry_config=RetryConfig(max_retries=3))
        self.wba_adapter = WBAAdapter(retry_config=RetryConfig(max_retries=3))
        self.nga_adapter = NGAAdapter(retry_config=RetryConfig(max_retries=3))

        # Initialize safety service
        self.safety_service = get_global_safety_service()

    async def process_input(
        self, user_input: str, session_id: str
    ) -> dict[str, Any]:
        """Process user input through agent pipeline."""
        # Step 1: IPA - Parse and understand input
        ipa_result = await self.ipa_adapter.process(user_input, session_id)

        # Validate safety
        safety_level = await self.safety_service.validate(ipa_result)
        if safety_level == SafetyLevel.UNSAFE:
            return {"error": "Unsafe content detected"}

        # Step 2: WBA - Update world state
        wba_result = await self.wba_adapter.update_world(
            ipa_result["intent"], session_id
        )

        # Step 3: NGA - Generate narrative
        nga_result = await self.nga_adapter.generate_narrative(
            wba_result["world_state"], session_id
        )

        return {
            "narrative": nga_result["text"],
            "safety_level": safety_level.value,
            "agent_results": {
                "ipa": ipa_result,
                "wba": wba_result,
                "nga": nga_result,
            },
        }
```

### Example 2: Circuit Breaker State Management

```python
async def _record_failure(self) -> None:
    """Record failed operation and transition state if needed."""
    async with self._lock:
        self._metrics.failed_calls += 1
        self._metrics.last_failure_time = time.time()

        if self._state == CircuitBreakerState.CLOSED:
            self._failure_count += 1
            if self._failure_count >= self._config.failure_threshold:
                await self._transition_to_open()
        elif self._state == CircuitBreakerState.HALF_OPEN:
            # Any failure in half-open state transitions back to open
            await self._transition_to_open()

        await self._persist_state()
        await self._persist_metrics()
```

## Anti-Patterns

### Anti-Pattern: Blocking Operations in Async Workflows

**Problem**: Blocking calls freeze the event loop and prevent concurrent execution.

**Bad**:
```python
async def _run_agent(self, state: AgentWorkflowState) -> AgentWorkflowState:
    # Blocking synchronous call in async function!
    result = sync_agent_call(state["user_input"])
    state["agent_result"] = result
    return state
```

**Good**:
```python
async def _run_agent(self, state: AgentWorkflowState) -> AgentWorkflowState:
    # Use async call or run_in_executor for sync code
    result = await async_agent_call(state["user_input"])
    # OR: result = await asyncio.to_thread(sync_agent_call, state["user_input"])
    state["agent_result"] = result
    return state
```

## References

- [Agent Orchestration README](../../docs/AI_AGENT_ORCHESTRATION.md)
- [LangGraph Orchestrator](../../src/agent_orchestration/langgraph_orchestrator.py)
- [Unified Orchestrator](../../src/agent_orchestration/unified_orchestrator.py)
- [Circuit Breaker](../../src/agent_orchestration/circuit_breaker.py)
- [Tool Invocation Service](../../src/agent_orchestration/tools/invocation_service.py)

---

**Last Updated**: 2025-10-22
**Maintainer**: theinterneti


---
**Logseq:** [[TTA.dev/Platform_tta_dev/Components/Augment/Core/Instructions/Agent-orchestration.instructions]]
