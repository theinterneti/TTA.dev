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
- [ ] Unit tests use `MockPrimitive` from `tta_dev_primitives.testing`
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
# 1. Validate primitive usage
./scripts/validate-primitive-usage.sh

# 2. Format code
uv run ruff format .

# 3. Lint code
uv run ruff check . --fix

# 4. Type check
uvx pyright packages/

# 5. Run tests
uv run pytest -v
```

### Manual Verification

- [ ] No `TODO` or `FIXME` comments in committed code
- [ ] No debug print statements
- [ ] No commented-out code blocks
- [ ] No merge conflict markers
- [ ] Files have proper line endings (LF, not CRLF)

---

## 🎯 Package-Specific Checks

### tta-dev-primitives

- [ ] New primitives extend `WorkflowPrimitive[TInput, TOutput]`
- [ ] Primitives implement `_execute_impl()` method
- [ ] Primitives support `>>` and `|` operators
- [ ] Examples created in `examples/` directory
- [ ] Tests in `tests/` directory with 100% coverage

### tta-observability-integration

- [ ] OpenTelemetry integration tested
- [ ] Prometheus metrics validated
- [ ] Grafana dashboards updated (if applicable)
- [ ] Trace propagation verified

### universal-agent-context

- [ ] Agent context properly managed
- [ ] MCP server integration tested
- [ ] Multi-agent coordination validated

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
- **Prompt Templates:** [`.vscode/tta-prompts.md`](../.vscode/tta-prompts.md)
- **Coding Standards:** [`docs/development/CodingStandards.md`](../docs/development/CodingStandards.md)
- **Testing Guide:** [`packages/tta-dev-primitives/AGENTS.md#testing`](../packages/tta-dev-primitives/AGENTS.md)

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
