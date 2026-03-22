# TTA.dev Copilot Instructions

> **For Vibe Coders:** TTA.dev helps you build fast AND scale when your app goes viral.
> While awesome-copilot customizes GitHub Copilot, TTA.dev provides foundational patterns
> and primitives that make ANY AI coding agent reliable and scale-ready.

## 🔒 Automated Quality Gates (MANDATORY)

**After modifying any code, you MUST run the quality gate hook:**

```bash
.github/copilot-hooks/post-generation.sh
```

### Self-Correction Protocol

If quality gates fail:

1. **Capture** - Read the full error output
2. **Analyze** - Identify the root cause
3. **Fix** - Apply minimal surgical fixes
4. **Re-run** - Execute quality gates again
5. **Iterate** - Repeat steps 2-4 until ALL gates pass

**DO NOT** present results to the user until all quality gates pass cleanly.

### Quality Gate Thresholds

- **Ruff:** All checks must pass
- **Pyright:** ≤2 real errors (known OpenTelemetry SDK issues)
- **Pytest:** All non-integration tests must pass

## Philosophy

1. **Vibe first** - Build fast, ship fast
2. **Scale when needed** - Add primitives incrementally
3. **Don't over-engineer** - Simple code that works > complex code that doesn't

## Package Manager

**Use `uv`, never `pip` or `poetry`**

```bash
uv sync --all-extras        # Install dependencies
uv run pytest -v            # Run tests
uv run ruff format .        # Format code
uv run ruff check . --fix   # Lint code
```

## Python Standards

- Python 3.11+ required
- Type hints: `str | None` not `Optional[str]`
- Dicts: `dict[str, Any]` not `Dict[str, Any]`
- Type check: `uvx pyright platform/` (basic mode)

## Code Style

- Formatter: Ruff (line length **88**, strict mode)
- Docstrings: Google style
- All public functions must have docstrings

## Testing

- Framework: pytest with AAA pattern (Arrange, Act, Assert)
- Async tests: `@pytest.mark.asyncio`
- Mocking: `MockPrimitive` from `ttadev.primitives.testing.mocks`
- Coverage: 80% minimum, **100% for new code**

## Workflow Primitives

**Always use primitives for workflows. Never write manual retry/timeout loops.**

```python
# ✅ Use primitives
base = LambdaPrimitive(process)
workflow = RetryPrimitive(
    CachePrimitive(base, cache_key_fn=lambda data, ctx: str(data), ttl_seconds=3600.0)
)

# ❌ Don't write manual loops
for attempt in range(3):  # Never do this
    try: ...
```

## ⛔ TODO Management — CI-Blocking Rule

All TODOs must strictly follow the [TODO Management System](../docs/agent-guides/todo-management.md).
You **must** use the `#dev-todo` tag and include `type::`, `priority::`, and `package::` properties.
**Malformed TODOs will block CI.**

```markdown
- TODO <description> #dev-todo
  type:: <bug|implementation|refactor|documentation>
  priority:: <critical|high|medium|low>
  package:: <package-name>
```

TODOs without all required properties will fail the `validate-todos` CI step.

## Security

- Never log secrets (even partially)
- URL validation: use `urlparse()`, not substring checks
- Run `uv run python scripts/security_scan.py` before committing

## Quick Reference

| Task | Command |
|------|---------|
| Install deps | `uv sync --all-extras` |
| Run tests | `uv run pytest -v` |
| Format | `uv run ruff format .` |
| Lint | `uv run ruff check . --fix` |
| Type check | `uvx pyright platform/` |
| Validate TODOs | `uv run python scripts/validate-todos.py` |
| All checks | Run format, lint, typecheck, test, validate-todos in sequence |

## Documentation

- [AGENTS.md](../AGENTS.md) - Quick reference for agents
- [PRIMITIVES_CATALOG.md](../PRIMITIVES_CATALOG.md) - Complete primitive API
- [GETTING_STARTED.md](../GETTING_STARTED.md) - Setup guide


---
**Logseq:** [[TTA.dev/.github/Copilot-instructions]]
