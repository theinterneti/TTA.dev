# L0 Runtime Agent Roster

TTA.dev contains 7 specialist L0 runtime dev agents defined in `ttadev/agents/`.
These agents operate **on this repository** — they are tools for building TTA.dev, not
player-facing agents for the TTA product.

## Agent roster

| Agent | Role | Module | Handoff keywords |
|---|---|---|---|
| `developer` | Senior Python Developer | `developer.py` | — (default) |
| `devops` | DevOps / Platform Engineer | `devops.py` | deploy, infrastructure, docker, ci/cd |
| `security` | Application Security Engineer | `security.py` | security, vulnerability, injection, xss |
| `git` | Git Operations Specialist | `git.py` | commit, branch, merge, rebase |
| `github` | GitHub Workflow Specialist | `github.py` | pull request, pr, release, review |
| `qa` | Senior QA / Test Engineer | `qa.py` | test, coverage, quality, regression |
| `performance` | Performance Engineer | `performance.py` | performance, latency, throughput, profile |

## How routing works

`AgentRouter` (in `ttadev/agents/router.py`) picks the specialist based on keyword
matching in the task text. The `DeveloperAgent` is the fallback when no specialist
matches.

Each agent carries `handoff_triggers` — if the task text matches keyword sets,
the router hands off to the appropriate specialist.

See `ttadev/agents/spec.py` for the `HandoffTrigger` dataclass.

## AgentSpec pattern (how agents are defined)

Each agent is a frozen `AgentSpec` dataclass:

```python
DEVELOPER_SPEC = AgentSpec(
    name="developer",
    role="Senior Python Developer",
    system_prompt="...",
    tools=[AgentTool("read_file", "...", ToolRule.ALWAYS), ...],
    handoff_triggers=[HandoffTrigger(condition=..., target_agent="security", reason="...")],
    quality_gates=[QualityGate(name="response_not_empty", check=..., error_message="...")],
    task_profile=TaskProfile(task=TASK_CODING, complexity=COMPLEXITY_COMPLEX),
)
```

See [runtime/l0-agent-spec.md](./l0-agent-spec.md) for how to add or modify agents.

## Preferred invocation pattern

```python
from ttadev.agents import DeveloperAgent
from ttadev.primitives.llm import ModelRouterPrimitive

router = ModelRouterPrimitive(...)
agent = DeveloperAgent.with_router(router)   # Preferred — dynamic model selection
# NOT: DeveloperAgent(model="gpt-4o")        # Hardcodes model

result = await agent.execute(task, ctx)
```

## Quality gates

Every agent has a `response_not_empty` quality gate. Agents raising `QualityGateError`
signal that the result is unusable — the caller should retry or escalate.

## Registry

All agents auto-register with `_global_registry` (via module-level `_global_registry.register(spec)`)
so `AgentRouter` can discover them without explicit registration calls.
