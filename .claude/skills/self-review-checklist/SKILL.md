---
name: self-review-checklist
description: Use this skill before submitting code for review or merging a pull request. Covers a pre-merge checklist of common mistakes to catch.
---

### Self-Review Checklist (TTA.dev)

Run through this checklist before marking any task or PR as complete.

#### Code Quality

- [ ] All new functions have type annotations (`str | None`, not `Optional[str]`)
- [ ] All public functions have Google-style docstrings
- [ ] No manual retry/timeout/cache loops — use primitives
- [ ] State passed via `WorkflowContext`, not globals
- [ ] Import order: stdlib → third-party → local

#### Testing

- [ ] 100% coverage on new code
- [ ] Tests follow AAA pattern (Arrange-Act-Assert)
- [ ] Uses `MockPrimitive` for mocking (not real implementations)
- [ ] Uses `@pytest.mark.asyncio` on async tests
- [ ] Tests cover success, failure, and edge cases
- [ ] No external dependencies in tests (databases, APIs, filesystem)

#### Security

- [ ] No secrets or credentials in code
- [ ] No new `eval()`, `exec()`, or `subprocess.shell=True`
- [ ] URL validation uses `urlparse()`, not substring checks

#### Quality Gate

- [ ] `uv run ruff format --check .` — zero violations
- [ ] `uv run ruff check .` — zero violations
- [ ] `uvx pyright platform/` — zero errors
- [ ] `uv run pytest -v` — all tests pass

#### Documentation

- [ ] README updated if public API changed
- [ ] Code examples are copy-paste runnable
- [ ] Changed files have updated docstrings

#### Deep Reference

- Testing details: [`docs/agent-guides/testing-architecture.md`](../../docs/agent-guides/testing-architecture.md)
- Python standards: [`docs/agent-guides/python-standards.md`](../../docs/agent-guides/python-standards.md)
