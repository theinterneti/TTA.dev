# Testing Quick Reference Card

**TL;DR: Use `./scripts/test_fast.sh` for daily development**

---

## Daily Development (Safe for WSL)

```bash
# Run fast unit tests (default, recommended)
./scripts/test_fast.sh

# VS Code: Ctrl+Shift+P → "🧪 Run Fast Tests (Unit Only)"
```

---

## Integration Testing (CI or Powerful Machines Only)

```bash
# Requires explicit opt-in
RUN_INTEGRATION=true ./scripts/test_integration.sh

# VS Code: Ctrl+Shift+P → "🧪 Run Integration Tests (Safe)"
```

⚠️ **WARNING**: May start servers, consume 1GB+ RAM, crash WSL

---

## Documentation Checks

```bash
# Validate markdown files
python scripts/docs/check_md.py --all

# VS Code: Ctrl+Shift+P → "📝 Check Markdown Docs"
```

---

## Emergency: Tests Crashed

```bash
# Kill stale processes and free ports
./scripts/emergency_stop.sh
```

---

## Coverage Report

```bash
# Generate HTML coverage report (unit tests only)
uv run pytest --cov=packages --cov-report=html -m "not integration and not slow"

# Open in browser
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

---

## Test Markers

```python
@pytest.mark.unit          # Fast, safe for local
@pytest.mark.integration   # Heavy, use in CI
@pytest.mark.slow          # > 30 seconds
@pytest.mark.external      # Needs network/APIs
```

---

## Common Issues

### Tests Hanging
```bash
# Ctrl+C then run
./scripts/emergency_stop.sh
```

### Import Errors
```bash
uv sync --all-extras
```

### Ports In Use (8001, 8002)
```bash
./scripts/emergency_stop.sh
# or manually
lsof -ti:8001,8002 | xargs kill -9
```

---

## Full Documentation

- **Testing Guide**: `docs/TESTING_GUIDE.md`
- **Markdown Checks**: `scripts/docs/README.md`
- **Implementation**: `docs/TESTING_METHODOLOGY_SUMMARY.md`
- **CI Config**: `.github/workflows/tests-split.yml`

---

**Remember**: Always run `./scripts/test_fast.sh` before committing!
