# TTA.dev Multi-Agent Coordination

> **Universal entry point for all AI agents working in this repository**

## Before You Begin

Start the observability dashboard (idempotent — safe to run if already running):

```bash
uv run python -m ttadev.observability
```

Dashboard: **http://localhost:8000** — shows live primitive usage, sessions, and the CGC code graph.
This gives you and the developer real-time visibility into all workflow executions during your session.

---

## What is TTA.dev?

A Python monorepo providing composable workflow primitives, observability, and multi-agent coordination for building reliable AI applications.

---

## Quick Reference

| Agent | Use For | Location |
|-------|---------|----------|
| **Backend Engineer** | Python primitives, APIs, workflows | [.github/agents/backend-engineer.agent.md](.github/agents/backend-engineer.agent.md) |
| **Frontend Engineer** | React UI, TypeScript components | [.github/agents/frontend-engineer.agent.md](.github/agents/frontend-engineer.agent.md) |
| **DevOps Engineer** | CI/CD, infrastructure, deployment | [.github/agents/devops-engineer.agent.md](.github/agents/devops-engineer.agent.md) |
| **Testing Specialist** | Tests, QA, validation | [.github/agents/testing-specialist.agent.md](.github/agents/testing-specialist.agent.md) |
| **Observability Expert** | Monitoring, metrics, traces | [.github/agents/observability-expert.agent.md](.github/agents/observability-expert.agent.md) |
| **Data Scientist** | Analytics, ML, research | [.github/agents/data-scientist.agent.md](.github/agents/data-scientist.agent.md) |
| **Architect** | System design, patterns | [.github/agents/architect.agent.md](.github/agents/architect.agent.md) |

---

## Repository Structure

```
TTA.dev/
├── ttadev/                 # Main Python package
│   ├── primitives/         # Core workflow primitives (Backend Engineer)
│   │   ├── core/           # Base classes, WorkflowContext, LambdaPrimitive
│   │   ├── recovery/       # Retry, Timeout, CircuitBreaker, Fallback
│   │   ├── integrations/   # Ollama, Groq, OpenRouter, Anthropic
│   │   └── mcp_server/     # 43-tool MCP server for coding agents
│   ├── agents/             # Role-based agent system (specs, registry, router)
│   ├── observability/      # OpenTelemetry + local observability server
│   ├── workflows/          # LLM provider chain, feature_dev workflow
│   ├── cli/                # `tta` CLI subcommands
│   ├── control_plane/      # L0 task/run/lease state (JSON-backed)
│   └── skills/             # Skill registry utilities
├── tests/                  # Test suite (unit + integration)
├── docs/                   # Architecture guides, agent docs
├── examples/               # Runnable demo scripts
├── scripts/                # Automation and utility scripts
└── .github/
    ├── agents/             # Custom agent definitions
    ├── skills/             # Multi-agent workflow skills
    └── workflows/          # CI/CD pipelines (DevOps Engineer)
```

---

## Agent Skills (Multi-Agent Workflows)

Coordinated workflows involving multiple agents:

| Skill | Agents | Duration | Use |
|-------|--------|----------|-----|
| [package-release](.github/skills/package-release/SKILL.md) | Backend → Testing → DevOps | ~30 min | Release to PyPI |
| [feature-development](.github/skills/feature-development/SKILL.md) | Backend → Frontend → Testing | 4-6 hr | Full-stack features |
| [incident-response](.github/skills/incident-response/SKILL.md) | DevOps + Observability | Variable | Production emergencies |

### Single-Agent Skills

Load these for specific tasks:

| Skill | Agent | When to Use |
|-------|-------|-------------|
| [build-test-verify](.claude/skills/build-test-verify/SKILL.md) | Any | Building, testing, linting |
| [git-commit](.claude/skills/git-commit/SKILL.md) | Any | Making git commits |
| [create-pull-request](.claude/skills/create-pull-request/SKILL.md) | Any | Creating PRs |
| [core-conventions](.claude/skills/core-conventions/SKILL.md) | Backend Engineer | Python code standards |
| [self-review-checklist](.claude/skills/self-review-checklist/SKILL.md) | Any | Pre-merge review |
| [sdd-workflow](.claude/skills/sdd-workflow/SKILL.md) | Backend Engineer | SDD feature process |

---

## Agent Coordination

### Communication Protocols

**1. API Contract Handoff (Backend → Frontend)**
- Backend creates API, shares OpenAPI schema
- Frontend generates TypeScript types
- Both work from shared contract

**2. Quality Gate (Testing → All)**
- Testing validates all code changes
- Blocks release if quality gates fail
- 80%+ coverage, all tests pass, CI green

**3. Deployment Handoff (DevOps → Observability)**
- DevOps deploys infrastructure
- Observability configures monitoring
- Both verify system health

### When to Use Each Agent

| Task Type | Primary Agent | Supporting Agents |
|-----------|--------------|-------------------|
| Add primitive | Backend Engineer | Testing Specialist |
| Build API | Backend Engineer | Testing Specialist |
| Add UI component | Frontend Engineer | Testing Specialist |
| Fix CI pipeline | DevOps Engineer | - |
| Troubleshoot issue | Observability Expert | DevOps Engineer |
| Analyze data | Data Scientist | - |
| System design | Architect | All (for input) |

---

## L0 Control Plane Status

The first local L0 slice now exists in:

- `ttadev/control_plane/` — JSON-backed task, run, and lease state
- `ttadev/cli/control.py` — `tta control task ...` and `tta control run ...`
- `ttadev/primitives/mcp_server/server.py` — MCP tools for the current task/run lifecycle

Interpret this as the beginning of a **developer-agent control plane** for Claude,
Copilot, Cline, and future coding agents.

Current rule: **extend this L0 surface instead of creating parallel task/run
systems elsewhere in the repo.**

### L0 Continuation Priorities

When working on L0 from inside `TTA.dev`, prefer this order:

1. use the current L0 surface to prove one documented, repeatable multi-agent workflow
2. deepen approval/policy/review workflows only where that workflow needs richer coordination
3. strengthen ownership and telemetry attribution so active workflow steps can be explained clearly
4. connect more agent-facing surfaces to the existing L0 state instead of creating parallel coordination models

### Repository TODOs

All four L0 phase-1 items are complete as of 2026-03-27:
- Items 1–3: multi-agent workflow proof, gate deepening, OTel trace attribution
- Item 4: MCP workflow progression tools (`control_start_workflow`, `control_mark_workflow_step_running`, `control_record_workflow_step_result`, `control_record_workflow_gate_outcome`, `control_mark_workflow_step_failed`) plus `tta control workflow start` CLI command

The L0 surface is ready to run a documented multi-agent workflow end-to-end.

---

## Deep Reference Guides

Load only when agent or skill instructions are insufficient:

| Guide | Content |
|-------|---------|
| [testing-architecture](docs/agent-guides/testing-architecture.md) | Testing standards, MockPrimitive, CI pipeline |
| [primitives-patterns](docs/agent-guides/primitives-patterns.md) | All primitives, composition, recovery patterns |
| [python-standards](docs/agent-guides/python-standards.md) | Type hints, naming, imports, docstrings |
| [observability-integration](docs/agent-guides/observability-integration.md) | OpenTelemetry, metrics, tracing |

---

## Boundary Rules

**All Agents:**
- ✅ Write docs to `docs/kb-exports/`
- ❌ Never create .md files in project root unless explicitly requested
- ✅ Follow quality gates (ruff, pyright, pytest)
- ❌ Never commit secrets or credentials

**Cross-repo TTA edits — mandatory procedure:**
- ❌ Never edit `~/Repos/TTA` directly — the local TTA agent owns that directory
- ✅ To push changes to TTA: clone to a temp path, commit + push, then delete

```bash
git clone https://github.com/theinterneti/TTA /tmp/TTA-copilot
# make changes inside /tmp/TTA-copilot
cd /tmp/TTA-copilot && git add -A && git commit -m "..." && git push
rm -rf /tmp/TTA-copilot
```

**Territory-Specific:**
- Backend Engineer: ✅ `platform/**/*.py`, ❌ `apps/frontend/**`
- Frontend Engineer: ✅ `apps/frontend/**`, ❌ `platform/**/*.py`
- DevOps Engineer: ✅ `.github/workflows/**`, ❌ source code
- Testing Specialist: ✅ `tests/**`, ❌ infrastructure
- Observability Expert: ✅ `monitoring/**`, ❌ business logic

---

## Standards

### Code Quality (All Agents)

```bash
uv run ruff format .        # Format
uv run ruff check . --fix   # Lint
uvx pyright platform/       # Type check
make watch                  # Continuous testing during development (fast, fail-fast)
make watch-cov              # Continuous testing with live coverage (before committing)
make test                   # Full one-shot run with coverage
```

### Test Status (No MCP needed)

`TEST_STATUS.md` is auto-generated at the repo root after every pytest run.
Read it to know the current test state without running anything:

```bash
cat TEST_STATUS.md
```

It is gitignored (local only) and kept perpetually fresh by `make watch`.
If it doesn't exist yet, run `make test` once to generate it.

### Testing (Testing Specialist enforces)

- 80% minimum coverage (100% on new code)
- AAA pattern (Arrange, Act, Assert)
- Use `MockPrimitive` for mocking
- `@pytest.mark.asyncio` for async tests

### Documentation

- Google-style docstrings
- Update README when features change
- Document decisions in repo docs or Hindsight
- Keep CHANGELOG.md current
- When touching L0, update the shared handoff guidance in `AGENTS.md`, `CLAUDE.md`, and `.github/copilot-instructions.md`

---

## MCP Server Configuration

Native MCP servers available to agents: [.mcp/config.json](.mcp/config.json)

**Core Servers:**
- **context7**: Library documentation
- **codegraphcontext**: Code graph analysis and repository context
- **e2b**: Secure sandboxed code execution
- **github**: Repository operations
- **playwright**: Browser automation
- **grafana**: Monitoring and metrics
- **gitmcp**: Git operations
- **hindsight**: Long-term memory and recall
- **serena**: Code analysis
- **sequential-thinking**: Problem decomposition

---

---

## Getting Started

### Invoke an Agent

```bash
@backend-engineer "create CircuitBreakerPrimitive"
@frontend-engineer "add user profile page"
@testing-specialist "validate quality gates"
```

### Use a Skill

```bash
@backend-engineer use skill "package-release"
@backend-engineer use skill "feature-development"
@devops-engineer use skill "incident-response"
```

### View Agent Capabilities

```bash
cat .github/agents/backend-engineer.agent.md
ls .github/skills/
```

---

## Examples

**Create an agent with task-aware model routing (preferred):**
```python
from ttadev.agents import DeveloperAgent
from ttadev.primitives.llm import ModelRouterPrimitive

router = ModelRouterPrimitive(...)           # configure tiers once
agent  = DeveloperAgent.with_router(router)  # auto-selects model via TaskProfile
result = await agent.execute(task, ctx)
```
> `DeveloperAgent.with_router(router)` is the preferred pattern over `DeveloperAgent(model=...)`.
> Each concrete agent carries a `default_task_profile`; `with_router()` wires them together
> via `ModelRouterChatAdapter`. See [llm-provider-strategy](docs/agent-guides/llm-provider-strategy.md)
> and [PRIMITIVES_CATALOG § ModelRouterChatAdapter](PRIMITIVES_CATALOG.md) for details.

**Add Primitive:**
```
@backend-engineer "Create RateLimitPrimitive with sliding window algorithm"
→ Design, implement, test, document
```

**Build Feature:**
```
@backend-engineer use skill "feature-development"
→ Backend API → Frontend UI → Testing validation
```

**Handle Incident:**
```
@devops-engineer use skill "incident-response"
→ Detect → Investigate → Mitigate → Resolve → Postmortem
```

---

## Related Documentation

- [Contributing Guide](CONTRIBUTING.md)
- [Getting Started](GETTING_STARTED.md)
- [Primitives Catalog](PRIMITIVES_CATALOG.md)
- [Vibe Coding Guide](VIBE_CODING.md)
---

**Version:** 2.0.0
**Last Updated:** 2026-03-18
**Status:** Active
