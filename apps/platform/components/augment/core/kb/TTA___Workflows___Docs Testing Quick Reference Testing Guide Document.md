---
title: TTA Testing Quick Reference Guide
tags: #TTA
status: Active
repo: theinterneti/TTA
path: docs/testing/QUICK_REFERENCE_TESTING_GUIDE.md
created: 2025-11-01
updated: 2025-11-01
---
# [[TTA/Workflows/TTA Testing Quick Reference Guide]]

**For:** Solo Developer Daily Workflow
**Environment:** WSL2 (/dev/sdf)
**Last Updated:** 2025-10-03

---

## Quick Start

### Run All Tests (Fast)
```bash
# Unit tests only (< 1 minute)
uv run pytest -q
```

### Run Tests with Databases (Slow)
```bash
# Start databases first
docker-compose -f docker-compose.test.yml up -d neo4j redis

# Run integration tests (5-10 minutes)
uv run pytest -q --neo4j --redis

# Stop databases
docker-compose -f docker-compose.test.yml down -v
```

### Run E2E Tests
```bash
# Start frontend and mock API
cd tests/e2e/mocks && npm start &
cd src/player_experience/frontend && npm start &

# Run Playwright tests
npx playwright test

# Or run specific spec
npx playwright test tests/e2e/specs/auth.spec.ts
```

---

## Common Test Commands

### Python Tests (pytest)

```bash
# Run all unit tests
uv run pytest -q

# Run specific test file
uv run pytest tests/test_authentication.py -v

# Run specific test function
uv run pytest tests/test_authentication.py::test_login_with_valid_credentials -v

# Run tests matching pattern
uv run pytest -k "auth" -v

# Run with coverage
uv run pytest --cov=src --cov-report=html --cov-report=term-missing

# Run only Neo4j tests
uv run pytest -m neo4j

# Run only Redis tests
uv run pytest -m redis

# Run integration tests
uv run pytest -m integration

# Skip slow tests
uv run pytest -m "not slow"

# Run with verbose output
uv run pytest -v

# Run with extra verbose output (show all test names)
uv run pytest -vv

# Stop on first failure
uv run pytest -x

# Run last failed tests
uv run pytest --lf

# Run failed tests first, then others
uv run pytest --ff
```

### E2E Tests (Playwright)

```bash
# Run all E2E tests
npx playwright test

# Run specific spec
npx playwright test tests/e2e/specs/auth.spec.ts

# Run specific browser
npx playwright test --project=chromium
npx playwright test --project=firefox
npx playwright test --project=webkit

# Run in headed mode (see browser)
npx playwright test --headed

# Run in debug mode
npx playwright test --debug

# Run specific test by name
npx playwright test -g "user can login"

# Generate test report
npx playwright show-report

# Update snapshots
npx playwright test --update-snapshots
```

### Comprehensive Test Battery

```bash
# Quick validation (standard tests only)
python tests/comprehensive_battery/run_comprehensive_tests.py \
  --categories standard \
  --log-level WARNING

# Full comprehensive tests
python tests/comprehensive_battery/run_comprehensive_tests.py \
  --all \
  --detailed-report \
  --metrics \
  --output-dir ./test-results

# With specific categories
python tests/comprehensive_battery/run_comprehensive_tests.py \
  --categories standard adversarial \
  --max-concurrent 4
```

---

## Test Environment Setup

### Start Test Databases

```bash
# Start Neo4j and Redis
docker-compose -f docker-compose.test.yml up -d neo4j redis

# Check status
docker-compose -f docker-compose.test.yml ps

# View logs
docker-compose -f docker-compose.test.yml logs neo4j
docker-compose -f docker-compose.test.yml logs redis

# Stop databases
docker-compose -f docker-compose.test.yml down

# Stop and remove volumes (clean slate)
docker-compose -f docker-compose.test.yml down -v
```

### Start Full Test Environment

```bash
# Use the convenience script
./scripts/start-test-environment.sh

# Or manually:
docker-compose -f docker-compose.test.yml up -d
cd tests/e2e/mocks && npm start &
cd src/player_experience/frontend && npm start &
```

---

## Debugging Tests

### Python Tests

```bash
# Run with pdb debugger on failure
uv run pytest --pdb

# Run with pdb debugger on error
uv run pytest --pdbcls=IPython.terminal.debugger:TerminalPdb

# Show local variables on failure
uv run pytest -l

# Show full diff on assertion failures
uv run pytest -vv

# Capture output (print statements)
uv run pytest -s

# Show warnings
uv run pytest -W all
```

### E2E Tests

```bash
# Run in debug mode (pauses before each action)
npx playwright test --debug

# Run in headed mode (see browser)
npx playwright test --headed

# Run with trace (for debugging failures)
npx playwright test --trace on

# Show trace for failed test
npx playwright show-trace trace.zip

# Take screenshot on failure (automatic)
# Screenshots saved to test-results/

# Record video on failure (automatic)
# Videos saved to test-results/
```

---

## Coverage Reports

### Generate Coverage Report

```bash
# Run tests with coverage
uv run pytest --cov=src --cov-report=html --cov-report=term-missing

# Open HTML report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

### Coverage Targets

- **Overall:** 80%
- **Critical paths (auth, database):** 90%+
- **Frontend components:** 75%+

---

## Performance Testing

### Load Testing with Locust

```bash
# Start Locust web UI
cd testing/load_tests
locust -f locustfile.py

# Open browser to http://localhost:8089
# Configure users and spawn rate in UI

# Or run headless
locust -f locustfile.py \
  --headless \
  --users 100 \
  --spawn-rate 10 \
  --run-time 10m \
  --html=load-test-report.html
```

### Performance Benchmarks

```bash
# Run performance tests
uv run pytest tests/performance/ -v

# Run with benchmarking
uv run pytest --benchmark-only
```

---

## Continuous Integration

### Run PR Validation Locally

```bash
# Simulate PR validation workflow
uv run pytest -q -m "not neo4j and not redis and not integration"
uv run ruff check .
uv run mypy src/
```

### Run Main Branch Tests Locally

```bash
# Start databases
docker-compose -f docker-compose.test.yml up -d

# Run full test suite
uv run pytest -q --neo4j --redis --cov=src

# Run core E2E tests
npx playwright test \
  tests/e2e/specs/auth.spec.ts \
  tests/e2e/specs/dashboard.spec.ts \
  tests/e2e/specs/character-management.spec.ts \
  --project=chromium
```

---

## Troubleshooting

### Common Issues

#### "No module named 'src'"

**Solution:** Ensure you're in the project root and using `uv run`:
```bash
cd /home/thein/recovered-tta-storytelling
uv run pytest
```

#### "Connection refused" for Neo4j/Redis

**Solution:** Start databases:
```bash
docker-compose -f docker-compose.test.yml up -d neo4j redis
# Wait 10 seconds for startup
sleep 10
uv run pytest --neo4j --redis
```

#### Playwright browser not installed

**Solution:** Install browsers:
```bash
npx playwright install chromium firefox webkit --with-deps
```

#### Tests hanging or timing out

**Solution:** Increase timeout or check for deadlocks:
```bash
# Increase pytest timeout
uv run pytest --timeout=300

# Increase Playwright timeout
npx playwright test --timeout=60000
```

#### Flaky tests

**Solution:** Run tests multiple times to identify flakiness:
```bash
# Run test 10 times
uv run pytest tests/test_flaky.py --count=10

# Run until failure
uv run pytest tests/test_flaky.py --maxfail=1 --count=100
```

---

## Test Markers

### Available Markers

- `@pytest.mark.neo4j` - Requires Neo4j database
- `@pytest.mark.redis` - Requires Redis database
- `@pytest.mark.integration` - Integration test
- `@pytest.mark.slow` - Slow-running test
- `@pytest.mark.comprehensive` - Part of comprehensive test battery
- `@pytest.mark.mock_only` - Only runs in mock mode
- `@pytest.mark.real_services` - Requires real services

### Using Markers

```bash
# Run only Neo4j tests
uv run pytest -m neo4j

# Run only integration tests
uv run pytest -m integration

# Skip slow tests
uv run pytest -m "not slow"

# Run Neo4j OR Redis tests
uv run pytest -m "neo4j or redis"

# Run Neo4j AND Redis tests
uv run pytest -m "neo4j and redis"
```

---

## Best Practices

### Before Committing

```bash
# 1. Run unit tests
uv run pytest -q -m "not neo4j and not redis and not integration"

# 2. Run linting
uv run ruff check .

# 3. Run type checking
uv run mypy src/

# 4. If all pass, commit
git add .
git commit -m "feat: add new feature"
```

### Before Creating PR

```bash
# 1. Run full test suite
docker-compose -f docker-compose.test.yml up -d
uv run pytest -q --neo4j --redis --cov=src

# 2. Run core E2E tests
npx playwright test tests/e2e/specs/auth.spec.ts

# 3. Check coverage
# Ensure coverage meets targets (80% overall)

# 4. Create PR
git push origin feature-branch
```

### Daily Development Workflow

```bash
# Morning: Pull latest changes and run tests
git pull origin main
uv run pytest -q

# During development: Run relevant tests frequently
uv run pytest tests/test_my_feature.py -v

# Before lunch: Run integration tests
docker-compose -f docker-compose.test.yml up -d
uv run pytest -q --neo4j --redis

# End of day: Run full test suite
uv run pytest --cov=src --cov-report=html
```

---

## Useful Aliases

Add these to your `~/.bashrc` or `~/.zshrc`:

```bash
# TTA test aliases
alias tta-test="uv run pytest -q"
alias tta-test-all="uv run pytest -q --neo4j --redis"
alias tta-test-cov="uv run pytest --cov=src --cov-report=html"
alias tta-test-e2e="npx playwright test"
alias tta-db-start="docker-compose -f docker-compose.test.yml up -d neo4j redis"
alias tta-db-stop="docker-compose -f docker-compose.test.yml down -v"
alias tta-lint="uv run ruff check ."
alias tta-type="uv run mypy src/"
```

---

## Resources

- **Full Testing Strategy:** [[TTA/Workflows/TEST_COVERAGE_ANALYSIS|TEST_COVERAGE_ANALYSIS.md]]
- **GitHub Workflows:** [[TTA/Workflows/GITHUB_WORKFLOWS_RECOMMENDATIONS|GITHUB_WORKFLOWS_RECOMMENDATIONS.md]]
- **pytest Documentation:** https://docs.pytest.org/
- **Playwright Documentation:** https://playwright.dev/
- **Locust Documentation:** https://docs.locust.io/

---

**Quick Reference Version:** 1.0
**Last Updated:** 2025-10-03


---
**Logseq:** [[TTA.dev/Platform_tta_dev/Components/Augment/Core/Kb/Tta___workflows___docs testing quick reference testing guide document]]
