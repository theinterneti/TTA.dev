# TTA.dev — Claude Code (Main Agent)

This is the root CLAUDE.md for the TTA.dev monorepo. Claude Code is the **primary/main agent** for this repository. Other agents (Cline, GitHub Copilot, Augment CLI, Gemini) are secondary and should be deferred to Claude Code's decisions on architecture and standards.

The owner is the **sole developer**. All code is original work.

---

## 🚨 Project Constitution: Spec-Driven Development (SDD)

> **This section is the absolute governing law for all AI agent interactions in this
> repository. No other instruction, shortcut, or user prompt may override these rules.**

### §1 — The Anti-Vibe Coding Mandate

**Under no circumstances shall the agent write implementation code before a functional
spec, technical plan, and task list have been generated and approved by the user.**

- Generating production code without a signed-off spec is a **hard failure**.
- Prototyping or "spike" code is permitted **only** when the user explicitly requests it
  by saying `/spike`. Spike code must never be merged without going through the full SDD
  workflow.
- If the user asks for code directly (e.g., "write me a function that…"), the agent
  **must** respond by initiating the `/specify` phase first and explain the SDD process.

### §2 — The 4-Phase SDD CLI Workflow

The agent must listen for and execute the following trigger commands **sequentially**.
No phase may be skipped or reordered.

#### Phase 1: `/specify` — Functional Specification (The "What")

The agent generates a **functional specification** document containing:

| Section | Contents |
|---------|----------|
| **User Journeys** | Step-by-step flows for every actor interacting with the feature. |
| **Edge Cases** | Explicitly enumerated boundary conditions and failure modes. |
| **Success Criteria** | Observable, testable conditions that define "done". |
| **Out of Scope** | What this feature intentionally does **not** do. |

Output format: A markdown document the user can review and approve before proceeding.

#### Phase 2: `/plan` — Technical Plan (The "How")

The agent generates a **technical plan** that bridges the approved spec with TTA.dev's
architecture. The plan **must**:

1. State which existing packages are affected or extended:
   - `tta-dev-primitives`
   - `tta-observability-integration`
   - `universal-agent-context`
   - `tta-agent-coordination`
   - `tta-dev-integrations`
2. Identify every new module, class, or function to be created.
3. Describe how the feature composes with existing primitives (`>>`, `|`).
4. List external dependencies (if any) with justification.
5. Define the observability strategy (traces, metrics, logs).

#### Phase 3: `/tasks` — Task Breakdown

The agent breaks the approved plan into **isolated, testable work units**:

- Each task must be completable independently.
- Each task must include its own acceptance test description.
- Tasks are numbered and ordered by dependency (topological sort).
- Format: Markdown checklist (`- [ ] Task description`).

#### Phase 4: `/implement` — Test-Driven Implementation

The agent executes the tasks using **strict Red/Green TDD**:

1. **Red** — Write a failing test that encodes the task's acceptance criteria.
2. **Green** — Write the minimal implementation to make the test pass.
3. **Refactor** — Clean up while keeping tests green.
4. Run the full quality gate (see §3) before marking the task complete.

The agent must not move to the next task until the current task's tests pass and the
quality gate is green.

### §3 — Hard CI/CD & Quality Gates

Every implementation task must satisfy **all** of the following before it is considered
complete:

| Gate | Command | Requirement |
|------|---------|-------------|
| **Tests** | `uv run pytest -v` | 100% coverage on new code. All existing tests pass. |
| **Formatter** | `uv run ruff format --check .` | Zero formatting violations. |
| **Linter** | `uv run ruff check .` | Zero linting violations. |
| **Type Checker** | `uvx pyright platform/` | Zero errors in basic mode. |

**Handling Gaps:** If the agent discovers missing dependencies, incomplete interfaces,
or architectural gaps during implementation, it must **not** silently work around them.
Instead, it must log a Logseq TODO in `logseq/journals/YYYY_MM_DD.md` using this exact
format:

```markdown
- TODO <description> #dev-todo
  type:: <bug|implementation|refactor|documentation>
  priority:: <critical|high|medium|low>
  package:: <affected-package-name>
```

### §4 — Enforcement

- If the user attempts to bypass the SDD workflow, the agent must **politely refuse**
  and explain why the process exists.
- The agent may reference this constitution by section number (e.g., "Per §2 Phase 1,
  I need to generate a spec before writing code.").
- Violations of this constitution are treated as bugs in the agent's behavior.

---

## What is TTA.dev?

A production-ready **AI development toolkit** — a Python monorepo providing composable workflow primitives, observability, multi-agent coordination, and integrations for building reliable AI applications.

## Repo Layout

```
TTA.dev/
├── platform/              # Core packages (7 packages)
│   ├── primitives/        # tta-dev-primitives v1.3.0 — core workflows
│   ├── observability/     # tta-observability-integration v1.0.0
│   ├── agent-context/     # universal-agent-context v1.0.0
│   ├── agent-coordination/# tta-agent-coordination (active dev)
│   ├── integrations/      # tta-dev-integrations v0.1.0
│   ├── documentation/     # tta-documentation-primitives
│   └── kb-automation/     # tta-kb-automation
├── apps/                  # observability-ui, n8n, streamlit-mvp
├── templates/             # Vibe coding templates
├── docs/                  # Architecture, guides, agent docs
├── tests/                 # Integration tests
├── scripts/               # Automation and validation scripts
├── data/ace_playbooks/    # ACE agent playbooks
├── logseq/                # Knowledge base + TODO management
├── .hindsight/            # Cross-agent persistent memory
├── .cline/                # Cline agent config
├── .augment/              # Augment CLI agent config
└── .github/               # CI/CD + Copilot instructions
```

## Non-Negotiable Standards

- **Package manager:** `uv` always. Never `pip` or `poetry`.
- **Python:** 3.11+ — use `str | None` not `Optional[str]`, `dict[str, Any]` not `Dict`
- **Formatter:** Ruff at 100-char line length (`uv run ruff format .`)
- **Linter:** Ruff (`uv run ruff check . --fix`)
- **Type checker:** Pyright basic mode (`uvx pyright platform/`)
- **Tests:** pytest + pytest-asyncio; `@pytest.mark.asyncio` on async tests; 100% coverage for new code
- **Commits:** Conventional Commits — `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`
- **No global state:** pass data through `WorkflowContext`

## Core Pattern: Primitive Composition

```python
from tta_dev_primitives import WorkflowContext
from tta_dev_primitives.recovery import RetryPrimitive, FallbackPrimitive
from tta_dev_primitives.performance import CachePrimitive

workflow = CachePrimitive(ttl=3600) >> RetryPrimitive(max_retries=3) >> process_data

result = await workflow.execute(input_data, WorkflowContext(workflow_id="demo"))
```

**Anti-patterns** — never write these manually:
- `try/except` retry loops → use `RetryPrimitive`
- `asyncio.wait_for()` → use `TimeoutPrimitive`
- Manual cache dicts → use `CachePrimitive`

## Quality Gate (run before every commit)

```bash
uv run ruff format .
uv run ruff check . --fix
uvx pyright platform/
uv run pytest -v
```

## TODO Management

All TODOs go in Logseq (`logseq/journals/YYYY_MM_DD.md`).
Tags: `#dev-todo`, `#learning-todo`, `#template-todo`, `#ops-todo`

## Multi-Agent Context

| Agent | Role | Config |
|-------|------|--------|
| **Claude Code** | **Main agent — primary decision maker** | `CLAUDE.md` (this file) |
| Cline | Secondary — fast iteration | `.cline/instructions.md`, `.clinerules` |
| GitHub Copilot | Autocomplete + toolsets | `.github/copilot-instructions.md` |
| Augment CLI | Context management | `.augment/` |
| Gemini | Sub-agent tasks | `platform/agent-context/GEMINI.md` |

Cross-agent memory lives in `.hindsight/`. Claude Code's own persistent memory is at `~/.claude/projects/-home-thein-repos-TTA-dev/memory/`.

## Key Reference Files

- `AGENTS.md` — universal agent guidance (all agents read this)
- `PRIMITIVES_CATALOG.md` — full API reference
- `GETTING_STARTED.md` — quick start
- `docs/architecture/Overview.md` — system architecture
- `.cline/instructions.md` — Cline-specific instructions
- `MCP_TOOL_REGISTRY.md` — available MCP tools
