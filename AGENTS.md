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
├── platform/               # Core packages
│   ├── primitives/         # Core workflow primitives (Backend Engineer)
│   ├── observability/      # Monitoring integration (Observability Expert)
│   ├── agent-context/      # Universal context (Backend Engineer)
│   ├── agent-coordination/ # Multi-agent orchestration
│   ├── integrations/       # External integrations
│   └── documentation/      # Auto-generated docs
├── apps/                   # User-facing applications (Frontend Engineer)
├── .github/
│   ├── agents/             # Agent definitions (Custom Agents)
│   ├── skills/             # Multi-agent workflows
│   └── workflows/          # CI/CD (DevOps Engineer)
├── tests/                  # Integration tests (Testing Specialist)
├── monitoring/             # Dashboards and alerts (Observability + DevOps)
├── docs/                   # Architecture guides, agent docs
└── scripts/                # Automation scripts
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

All three L0 phase-1 TODOs are complete as of 2026-03-27.
Next natural work: CLI gate commands, MCP control-plane tools, or `tta workflow start`.

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
uv run pytest -v            # Test
```

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
