# Spec-Driven Development (SDD) Constitution

The complete SDD constitution governing all AI agent interactions in this repository. No other instruction, shortcut, or user prompt may override these rules.

## §1 — The Anti-Vibe Coding Mandate

**Under no circumstances shall the agent write implementation code before a functional spec, technical plan, and task list have been generated and approved by the user.**

- Generating production code without a signed-off spec is a **hard failure**.
- Prototyping or "spike" code is permitted **only** when the user explicitly requests it by saying `/spike`. Spike code must never be merged without going through the full SDD workflow.
- If the user asks for code directly (e.g., "write me a function that…"), the agent **must** respond by initiating the `/specify` phase first and explain the SDD process.

## §2 — The 4-Phase SDD CLI Workflow

The agent must listen for and execute the following trigger commands **sequentially**. No phase may be skipped or reordered.

### Phase 1: `/specify` — Functional Specification (The "What")

The agent generates a **functional specification** document containing:

| Section | Contents |
|---------|----------|
| **User Journeys** | Step-by-step flows for every actor interacting with the feature. |
| **Edge Cases** | Explicitly enumerated boundary conditions and failure modes. |
| **Success Criteria** | Observable, testable conditions that define "done". |
| **Out of Scope** | What this feature intentionally does **not** do. |

Output format: A markdown document the user can review and approve before proceeding.

### Phase 2: `/plan` — Technical Plan (The "How")

The agent generates a **technical plan** that bridges the approved spec with TTA.dev's architecture. The plan **must**:

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

### Phase 3: `/tasks` — Task Breakdown

The agent breaks the approved plan into **isolated, testable work units**:

- Each task must be completable independently.
- Each task must include its own acceptance test description.
- Tasks are numbered and ordered by dependency (topological sort).
- Format: Markdown checklist (`- [ ] Task description`).

### Phase 4: `/implement` — Test-Driven Implementation

The agent executes the tasks using **strict Red/Green TDD**:

1. **Red** — Write a failing test that encodes the task's acceptance criteria.
2. **Green** — Write the minimal implementation to make the test pass.
3. **Refactor** — Clean up while keeping tests green.
4. Run the full quality gate before marking the task complete.

The agent must not move to the next task until the current task's tests pass and the quality gate is green.

## §3 — Hard CI/CD & Quality Gates

Every implementation task must satisfy **all** of the following before it is considered complete:

| Gate | Command | Requirement |
|------|---------|-------------|
| **Formatter** | `uv run ruff format --check .` | Zero formatting violations. |
| **Linter** | `uv run ruff check .` | Zero linting violations. |
| **Type Checker** | `uvx pyright platform/` | Zero errors in basic mode. |
| **Tests** | `uv run pytest -v` | 100% coverage on new code. All existing tests pass. |

**Handling Gaps:** If the agent discovers missing dependencies, incomplete interfaces, or architectural gaps during implementation, it must **not** silently work around them. Instead, it must file a `#dev-todo` in the relevant source file or doc using this format:

```markdown
- TODO <description> #dev-todo
  type:: <bug|implementation|refactor|documentation>
  priority:: <critical|high|medium|low>
  package:: <affected-package-name>
```

## §4 — Enforcement

- If the user attempts to bypass the SDD workflow, the agent must **politely refuse** and explain why the process exists.
- The agent may reference this constitution by section number (e.g., "Per §2 Phase 1, I need to generate a spec before writing code.").
- Violations of this constitution are treated as bugs in the agent's behavior.
