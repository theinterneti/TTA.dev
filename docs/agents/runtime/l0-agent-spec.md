# L0 Agent Spec Reference

This document describes how to read, write, and modify `AgentSpec` definitions in `ttadev/agents/`.

## AgentSpec fields

```python
@dataclasses.dataclass(frozen=True)
class AgentSpec:
    name: str                              # Lowercase, unique. Used for routing + registry.
    role: str                              # Display name. Used in system_prompt and logs.
    system_prompt: str                     # Full system prompt for the LLM.
    tools: list[AgentTool]                 # Tools the agent can call.
    handoff_triggers: list[HandoffTrigger] # Keyword-based routing rules.
    quality_gates: list[QualityGate]       # Post-execution checks.
    task_profile: TaskProfile              # Model selection hint (task + complexity).
    default_policy: dict[str, Any] = {}    # Governance policy (allow/deny/gate).
```

## AgentTool

```python
@dataclasses.dataclass(frozen=True)
class AgentTool:
    name: str           # Tool identifier (must match MCP tool name or registered function)
    description: str    # Used in system_prompt so the LLM knows what tools it has
    rule: ToolRule      # ALWAYS | WHEN_INSTRUCTED | NEVER
```

`ToolRule.ALWAYS` = always available.
`ToolRule.WHEN_INSTRUCTED` = only when the task mentions the tool by name.
`ToolRule.NEVER` = blocked (used for governance overrides).

## HandoffTrigger

```python
@dataclasses.dataclass(frozen=True)
class HandoffTrigger:
    condition: Callable[[str], bool]   # Predicate on task text
    target_agent: str                  # Name of agent to hand off to
    reason: str                        # Human-readable explanation logged on handoff
```

Standard pattern using `_matches` from `_utils.py`:

```python
_SECURITY_KEYWORDS = frozenset(["security", "vulnerability", "injection", "xss"])

HandoffTrigger(
    condition=lambda task: _matches(task, _SECURITY_KEYWORDS),
    target_agent="security",
    reason="Task involves security analysis — routing to SecurityAgent.",
)
```

## QualityGate

```python
@dataclasses.dataclass(frozen=True)
class QualityGate:
    name: str
    check: Callable[[AgentResult], bool]   # Return True = PASS
    error_message: str                     # Logged and raised on failure
```

All agents include `response_not_empty` by default. Add custom gates for
domain-specific validity (e.g., "code must compile", "PR URL must be present").

## TaskProfile

```python
from ttadev.primitives.llm import TASK_CODING, TASK_GENERAL, COMPLEXITY_COMPLEX, COMPLEXITY_MODERATE

TaskProfile(task=TASK_CODING, complexity=COMPLEXITY_COMPLEX)
```

`ModelRouterPrimitive` uses `TaskProfile` to select the best available model for the agent's
role without hardcoding model names. See [dev/architecture.md](../dev/architecture.md) for
the router architecture.

## Adding a new agent

1. Create `ttadev/agents/<name>.py` following the pattern of `developer.py`
2. Define `<NAME>_SPEC = AgentSpec(...)` with all required fields
3. Define keyword sets for handoff triggers (frozenset, lowercase)
4. Register at module bottom: `_global_registry.register(<NAME>_SPEC)`
5. Export from `ttadev/agents/__init__.py`
6. Add a row to `docs/agents/runtime/l0-roster.md`
7. Write tests in `tests/agents/test_<name>_agent.py` — 100% coverage on new code

## Modifying an existing agent

- **System prompt change**: Update `system_prompt` in the spec. No registry changes needed.
- **Adding a tool**: Add to `tools` list. Update system prompt to describe it.
- **Adding a handoff trigger**: Add `HandoffTrigger` to `handoff_triggers`. Add keyword frozenset.
- **Changing task profile**: Update `task_profile`. `DeveloperAgent.with_router()` will pick up the new hints.

## Tests to write/update

```python
@pytest.mark.asyncio
async def test_security_handoff_triggers():
    """SecurityAgent spec should route injection-related tasks to security."""
    spec = DEVELOPER_SPEC
    task = "fix sql injection vulnerability in login endpoint"
    matched = [t for t in spec.handoff_triggers if t.condition(task)]
    assert any(t.target_agent == "security" for t in matched)
```
