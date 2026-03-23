# Agent Pre-Commit Checklist

**Use this checklist before creating PRs or committing code to TTA.dev**

---

## ✅ Code Quality

### Primitive Usage

- [ ] All sequential workflows use `SequentialPrimitive` or `>>` operator
- [ ] All parallel workflows use `ParallelPrimitive` or `|` operator
- [ ] Error handling uses `RetryPrimitive`, `FallbackPrimitive`, or `TimeoutPrimitive`
- [ ] Expensive operations wrapped in `CachePrimitive`
- [ ] Routing logic uses `RouterPrimitive` (not if/else chains)
- [ ] No direct usage of `asyncio.gather()`, `asyncio.create_task()`, or `asyncio.wait_for()`

### Code Standards

- [ ] All async operations use TTA.dev primitives (not manual asyncio orchestration)
- [ ] All workflows pass `WorkflowContext` for observability
- [ ] Type hints on all function signatures
- [ ] Docstrings explain which primitives are used and why
- [ ] No global variables for state (use `WorkflowContext` instead)
- [ ] Code follows Python 3.11+ syntax (`T | None` not `Optional[T]`)

---

## 🧪 Testing

### Test Coverage

- [ ] Unit tests for all new primitives/functions
- [ ] Unit tests use `MockPrimitive` from `ttadev.primitives.testing.mocks`
- [ ] Integration tests verify primitive composition
- [ ] Test coverage ≥ 90% for new code
- [ ] All tests pass: `uv run pytest -v`

### Test Quality

- [ ] Tests cover success cases
- [ ] Tests cover failure cases
- [ ] Tests cover edge cases
- [ ] Async tests use `@pytest.mark.asyncio`
- [ ] No flaky tests (run multiple times to verify)

---

## 📚 Documentation

### Code Documentation

- [ ] Docstrings on all public classes and functions
- [ ] Docstrings follow Google style guide
- [ ] Docstrings explain primitive composition patterns
- [ ] Type hints match docstring descriptions

### Project Documentation

- [ ] `CHANGELOG.md` updated with changes
- [ ] Examples added to `examples/` directory if new pattern
- [ ] Package README updated if public API changed
- [ ] Architecture docs updated if design changed

---

## 🔭 Observability

### Tracing

- [ ] All workflows use `WorkflowContext` for trace propagation
- [ ] Custom primitives extend `InstrumentedPrimitive`
- [ ] OpenTelemetry spans created for long-running operations
- [ ] Span names follow convention: `primitive_name.operation`

### Metrics

- [ ] Metrics tagged with primitive type
- [ ] Performance-critical paths instrumented
- [ ] Error rates tracked
- [ ] Cache hit rates tracked (if using `CachePrimitive`)

### Logging

- [ ] Structured logging used (not print statements)
- [ ] Log messages include context (correlation_id, trace_id)
- [ ] Log levels appropriate (DEBUG/INFO/WARNING/ERROR)
- [ ] No sensitive data in logs

---

## ✔️ Validation

### Automated Checks

Run these commands before committing:

```bash
# 1. Run the standard repo gate
.github/copilot-hooks/post-generation.sh

# 2. Validate TODO formatting when relevant
uv run python scripts/validate-todos.py

# 3. Optional deeper test run
uv run pytest -v --tb=short -m "not integration and not slow and not external"
```

### Manual Verification

- [ ] No `TODO` or `FIXME` comments in committed code
- [ ] No debug print statements
- [ ] No commented-out code blocks
- [ ] No merge conflict markers
- [ ] Files have proper line endings (LF, not CRLF)

---

## 🎯 Package-Area Checks

### ttadev (root package)

- [ ] New primitives extend `WorkflowPrimitive[...]` or `InstrumentedPrimitive[...]` as appropriate
- [ ] Workflow code lives under `ttadev/`
- [ ] Root package examples and docs stay aligned with `ttadev` imports
- [ ] Examples created in `examples/` directory
- [ ] Tests in `tests/` directory with 100% coverage

### tta-dev-integrations

- [ ] Standalone package changes stay scoped to `ttadev/integrations/`
- [ ] Dependency expectations remain explicit in `ttadev/integrations/pyproject.toml`
- [ ] API/client integration behavior is tested

### tta-skill-primitives

- [ ] Standalone package changes stay scoped to `ttadev/skills/`
- [ ] SKILL.md behavior stays aligned with current repo conventions
- [ ] Skill examples and metadata remain current

---

## 🚀 Pre-PR Checklist

Before opening a pull request:

- [ ] All checklist items above completed
- [ ] PR title follows conventional commits format
- [ ] PR description explains what/why
- [ ] PR links to related issues (if any)
- [ ] PR is against correct branch (main)
- [ ] No merge conflicts
- [ ] CI/CD checks passing (GitHub Actions)

---

## 📖 Reference Documentation

- **Primitives Catalog:** [`PRIMITIVES_CATALOG.md`](../PRIMITIVES_CATALOG.md)
- **Agent Instructions:** [`AGENTS.md`](../AGENTS.md)
- **Prompt Templates:** [`.github/prompts/triage-issue.prompt.md`](../.github/prompts/triage-issue.prompt.md)
- **Coding Standards:** [`docs/guides/development/CodingStandards.md`](../docs/guides/development/CodingStandards.md)
- **Testing Guide:** [`docs/agent-guides/testing-architecture.md`](../docs/agent-guides/testing-architecture.md)

---

## 🤖 For AI Agents

**This checklist is your validation layer.** Before finalizing any PR:

1. **Self-audit** against this checklist
2. **Run automated checks** (see Validation section)
3. **Reference in PR description:** "Verified against `.github/AGENT_CHECKLIST.md`"
4. **Document any exceptions** with clear justification

---

**Last Updated:** November 10, 2025
**Version:** 1.0
**Maintained by:** TTA.dev Team
