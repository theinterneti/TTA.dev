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
make watch                  # Continuous testing during development (fast, fail-fast)
make watch-cov              # Continuous testing with live coverage (before committing)
make test                   # Full one-shot run with coverage
uv run ruff format .        # Format code
uv run ruff check . --fix   # Lint code
```

## Python Standards

- Python 3.11+ required
- Type hints: `str | None` not `Optional[str]`
- Dicts: `dict[str, Any]` not `Dict[str, Any]`
- Type check: `uvx pyright ttadev/` (basic mode)

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

## Security

- Never log secrets (even partially)
- URL validation: use `urlparse()`, not substring checks
- Run `uv run ruff check . --fix` and review for secrets before committing

## Quick Reference

| Task | Command |
|------|---------|
| Install deps | `uv sync --all-extras` |
| Watch tests (TDD loop) | `make watch` |
| Watch with coverage | `make watch-cov` |
| Full test run | `make test` |
| Format | `uv run ruff format .` |
| Lint | `uv run ruff check . --fix` |
| Type check | `uvx pyright ttadev/` |
| Validate TODOs | `uv run python scripts/validate-todos.py` |
| All checks | Run format, lint, typecheck, test, validate-todos in sequence |

## L0 Developer Control Plane

The first L0 slice is already in the repo:

- `ttadev/control_plane/` for task/run/lease state
- `ttadev/cli/control.py` for `tta control ...`
- `ttadev/primitives/mcp_server/server.py` for MCP access to the current task/run lifecycle

If you are asked to improve agent management, do **not** create a second queue,
run ledger, or lease model in another package. Extend this L0 surface.

### Highest-priority follow-up work

1. use the current L0 surface to prove one documented, repeatable multi-agent workflow
2. deepen approval/policy/review workflows only where that workflow needs richer coordination
3. strengthen ownership and telemetry attribution so active workflow steps can be explained clearly
4. connect more agent-facing surfaces to the existing L0 state instead of creating parallel coordination systems

## Hindsight Memory

Hindsight MCP server is available at `http://localhost:8888/mcp/`. Use it deliberately.

**Session start** — before any non-trivial task:
1. Recall from `adam-global` (cross-project directives and user preferences)
2. Recall from `tta-dev` (TTA.dev architecture, decisions, known failures, patterns)

**During work** — after completing significant tasks:
- Retain cross-project patterns → `adam-global`
- Retain TTA.dev-specific decisions, failures, and patterns → `tta-dev`

**Rules:**
- Use `document_id` for evolving notes (same ID = upsert, prevents duplicates)
- Include a `context` label when retaining
- Never retain secrets, tokens, or credentials
- If Hindsight is unavailable, say so and continue without pretending recall happened

## Documentation

- [AGENTS.md](../AGENTS.md) - Quick reference for agents
- [PRIMITIVES_CATALOG.md](../PRIMITIVES_CATALOG.md) - Complete primitive API
- [GETTING_STARTED.md](../GETTING_STARTED.md) - Setup guide
