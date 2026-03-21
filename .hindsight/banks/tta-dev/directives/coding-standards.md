---
category: directives
date: 2026-03-20
component: coding-standards
severity: critical
tags: [directive, standards, uv, ruff, sdd, todos]
---
# Directive: Coding Standards

## Non-negotiable rules

- **Package manager:** `uv` always. Never `pip`, never `poetry`.
- **Python:** 3.11+. `str | None` not `Optional[str]`. `dict[str, Any]` not `Dict`.
- **Linting:** `uv run ruff check . --fix` then `uv run ruff format .` before every commit.
- **Type checking:** `uvx pyright ttadev/` (basic mode, non-blocking in CI).
- **Testing:** pytest AAA pattern. 100% coverage for all new code. Never comment out tests.
- **Commits:** Conventional Commits — `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`.
- **Primitives:** Always use for workflows — RetryPrimitive not manual retry loops,
  TimeoutPrimitive not asyncio.wait_for, CachePrimitive not manual dicts.
- **State:** Pass via WorkflowContext, never globals.

## SDD mandate (non-negotiable)

No implementation code before a signed-off spec.
Workflow: `/specify` → `/plan` → `/tasks` → `/implement`

## TODO format (CI-blocking if wrong)

```markdown
- TODO <description> #dev-todo
  type:: <bug|implementation|refactor|documentation>
  priority:: <critical|high|medium|low>
  package:: <package-name>
```

---
**Created:** 2026-03-20
**Verified:** [x] Yes
