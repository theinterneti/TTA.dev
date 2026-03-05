---
name: build-test-verify
description: Use this skill when asked to build the project, run tests, lint the code, or verify that the TTA.dev platform is stable before committing.
---

### Build, Test, and Verify (TTA.dev)

Validate code changes to ensure they meet quality standards before committing.

#### Process

Execute the following commands in order. Do not skip steps.

1. **Format**: Apply Ruff formatting (100-char line length).
   ```bash
   uv run ruff format .
   ```

2. **Lint**: Run Ruff linter with auto-fix.
   ```bash
   uv run ruff check . --fix
   ```

3. **Type Check**: Run Pyright in basic mode.
   ```bash
   uvx pyright platform/
   ```

4. **Run Tests**: Execute the pytest suite (100% coverage required for new code).
   ```bash
   uv run pytest -v --tb=short -m "not integration and not slow and not external"
   ```

5. **Full coverage** (when adding new code):
   ```bash
   uv run pytest --cov=src --cov-report=html
   ```

#### Common Issues

- **Type errors**: Ensure all new functions have strict type annotations (`str | None`, not `Optional[str]`).
- **Test failures**: Fix the implementation, never comment out tests. Follow the AAA pattern (Arrange-Act-Assert).
- **Import errors**: Check import order — stdlib, third-party, local.
- **Quarantined tests**: Tests marked `@pytest.mark.quarantine` are auto-skipped unless explicitly selected with `-m quarantine`.

#### Deep Reference

For full testing patterns, markers, CI pipeline details, and MockPrimitive API, see [`docs/agent-guides/testing-architecture.md`](../../docs/agent-guides/testing-architecture.md).
