---
title: Mutation Testing CI/CD Integration Guide
tags: #TTA
status: Active
repo: theinterneti/TTA
path: docs/testing/MUTATION_TESTING_CICD_GUIDE.md
created: 2025-11-01
updated: 2025-11-01
---
# [[TTA/Workflows/Mutation Testing CI/CD Integration Guide]]

**Date:** 2025-10-11
**Status:** ✅ Active
**Workflow:** `.github/workflows/mutation-testing.yml`

---

## Overview

This guide explains how to use the automated mutation testing CI/CD pipeline for the TTA Model Management services.

### What is Mutation Testing?

Mutation testing validates test quality by introducing small changes (mutations) to the code and verifying that tests catch these changes. A high mutation score indicates robust tests that effectively detect bugs.

### Services Covered

1. **ModelSelector** - Model selection and routing logic
2. **FallbackHandler** - Fallback and failover mechanisms
3. **PerformanceMonitor** - Performance metrics and monitoring

---

## CI/CD Workflow

### Automatic Execution

The mutation testing workflow runs automatically:
- **Schedule:** Every Sunday at 2:00 AM UTC
- **Duration:** ~90-120 minutes for all three services
- **Threshold:** Fails if mutation score drops below 85%

### Manual Execution

You can manually trigger the workflow from GitHub Actions:

1. Go to **Actions** → **Mutation Testing**
2. Click **Run workflow**
3. Select service to test:
   - `all` - Test all three services (default)
   - `model-selector` - Test only ModelSelector
   - `fallback-handler` - Test only FallbackHandler
   - `performance-monitor` - Test only PerformanceMonitor
4. Click **Run workflow**

---

## Running Mutation Testing Locally

### Prerequisites

```bash
# Ensure you have uv installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install project dependencies
uv sync --all-extras

# Install cosmic-ray
uv add --dev cosmic-ray
```

### Run for a Single Service

#### ModelSelector

```bash
# Create configuration
cat > cosmic-ray-model-selector.toml << EOF
[cosmic-ray]
module-path = "src/components/model_management/services/model_selector.py"
timeout = 10.0
excluded-modules = []
test-command = "uv run pytest tests/unit/model_management/services/test_model_selector_properties.py tests/unit/model_management/services/test_model_selector_concrete.py -x -q --tb=no -p no:warnings"

[cosmic-ray.distributor]
name = "local"
EOF

# Initialize and execute
uv run cosmic-ray init cosmic-ray-model-selector.toml session-model-selector.sqlite
uv run cosmic-ray exec cosmic-ray-model-selector.toml session-model-selector.sqlite

# Generate reports
uv run cr-report session-model-selector.sqlite
uv run cr-html session-model-selector.sqlite > model-selector-report.html
```

#### FallbackHandler

```bash
# Create configuration
cat > cosmic-ray-fallback.toml << EOF
[cosmic-ray]
module-path = "src/components/model_management/services/fallback_handler.py"
timeout = 10.0
excluded-modules = []
test-command = "uv run pytest tests/unit/model_management/services/test_fallback_handler_properties.py tests/unit/model_management/services/test_fallback_handler_concrete.py -x -q --tb=no -p no:warnings"

[cosmic-ray.distributor]
name = "local"
EOF

# Initialize and execute
uv run cosmic-ray init cosmic-ray-fallback.toml session-fallback.sqlite
uv run cosmic-ray exec cosmic-ray-fallback.toml session-fallback.sqlite

# Generate reports
uv run cr-report session-fallback.sqlite
uv run cr-html session-fallback.sqlite > fallback-handler-report.html
```

#### PerformanceMonitor

```bash
# Create configuration
cat > cosmic-ray-performance.toml << EOF
[cosmic-ray]
module-path = "src/components/model_management/services/performance_monitor.py"
timeout = 10.0
excluded-modules = []
test-command = "uv run pytest tests/unit/model_management/services/test_performance_monitor_properties.py tests/unit/model_management/services/test_performance_monitor_concrete.py -x -q --tb=no -p no:warnings"

[cosmic-ray.distributor]
name = "local"
EOF

# Initialize and execute
uv run cosmic-ray init cosmic-ray-performance.toml session-performance.sqlite
uv run cosmic-ray exec cosmic-ray-performance.toml session-performance.sqlite

# Generate reports
uv run cr-report session-performance.sqlite
uv run cr-html session-performance.sqlite > performance-monitor-report.html
```

### Run All Services

```bash
# Use the convenience script (if available)
./scripts/run-mutation-tests.sh

# Or run each service sequentially
for service in model-selector fallback performance; do
    echo "Testing $service..."
    # Run commands from above for each service
done
```

---

## Interpreting Results

### Mutation Score

The mutation score represents the percentage of mutations that were detected (killed) by tests:

- **100%** 🏆 - Perfect! All mutations killed
- **95-99%** ✅ - Excellent test coverage
- **85-94%** ⚠️ - Good, but room for improvement
- **<85%** ❌ - Insufficient test coverage (CI fails)

### Report Sections

#### Text Report (`cr-report`)

```
total jobs: 519
complete: 519 (100.00%)
surviving mutants: 0 (0.00%)
```

- **total jobs:** Number of mutations generated
- **complete:** Mutations that were tested
- **surviving mutants:** Mutations not caught by tests (lower is better)

#### HTML Report (`cr-html`)

The HTML report provides:
- Visual representation of mutation results
- Line-by-line mutation details
- Specific mutations that survived (if any)
- Mutation operators used

### Accessing Reports in CI

1. Go to the workflow run in GitHub Actions
2. Scroll to **Artifacts** section
3. Download mutation reports:
   - `mutation-report-model-selector`
   - `mutation-report-fallback-handler`
   - `mutation-report-performance-monitor`
4. Extract and open the HTML file in a browser

---

## Maintaining Mutation Tests

### When Mutation Score Drops

If the CI fails due to low mutation score:

1. **Download the HTML report** from CI artifacts
2. **Identify surviving mutants:**
   - Look for mutations marked as "survived"
   - Note the line numbers and mutation types
3. **Add targeted tests:**
   - Create concrete value tests for uncovered logic
   - Ensure tests validate specific calculations
   - Use hardcoded expected values
4. **Re-run locally** to verify improvements
5. **Commit and push** updated tests

### Adding Tests for New Code

When adding new code to monitored services:

1. **Write property-based tests** for general behavior
2. **Write concrete value tests** for specific calculations
3. **Run mutation testing locally** before committing
4. **Ensure 95%+ mutation score** for new code
5. **Update documentation** if needed

### Best Practices

1. **Hardcode expected values** in concrete tests
   ```python
   # ✅ Good
   assert stats["total_tokens"] == 300  # 50 + 100 + 150

   # ❌ Bad (recalculates, won't catch calculation bugs)
   assert stats["total_tokens"] == sum([50, 100, 150])
   ```

2. **Test edge cases explicitly**
   ```python
   def test_empty_list_returns_zero():
       result = calculate_percentile([])
       assert result == 0.0
   ```

3. **Use approximate comparisons for floats**
   ```python
   assert abs(result - 0.9833333333333333) < 1e-10
   ```

4. **Cover all code paths**
   - Test both success and failure cases
   - Test boundary conditions
   - Test default values

---

## Troubleshooting

### Workflow Fails with Timeout

**Cause:** Mutation testing takes longer than 60 minutes per service

**Solution:**
1. Check if tests are hanging
2. Increase timeout in workflow (max 120 minutes)
3. Optimize test execution speed

### Mutation Score Extraction Fails

**Cause:** Report format changed or parsing error

**Solution:**
1. Check the text report manually
2. Update the grep pattern in workflow
3. Verify cosmic-ray version compatibility

### Dependencies Not Installing

**Cause:** Cache issues or dependency conflicts

**Solution:**
1. Clear GitHub Actions cache
2. Update `uv.lock` file
3. Verify `pyproject.toml` dependencies

### Tests Pass Locally but Fail in CI

**Cause:** Environment differences

**Solution:**
1. Check Python version matches (3.12)
2. Verify all dependencies are in `pyproject.toml`
3. Run tests in clean virtual environment locally

---

## Configuration Reference

### Workflow Configuration

```yaml
env:
  PYTHON_VERSION: '3.12'
  MUTATION_SCORE_THRESHOLD: 85
```

- **PYTHON_VERSION:** Python version to use
- **MUTATION_SCORE_THRESHOLD:** Minimum acceptable mutation score (%)

### Cosmic Ray Configuration

```toml
[cosmic-ray]
module-path = "path/to/module.py"
timeout = 10.0
excluded-modules = []
test-command = "uv run pytest ..."

[cosmic-ray.distributor]
name = "local"
```

- **module-path:** Python module to mutate
- **timeout:** Max seconds per mutation test
- **test-command:** Command to run tests
- **distributor:** Execution strategy (local for CI)

---

## Performance Metrics

### Expected Execution Times

| Service | Mutations | Execution Time | Status |
|---------|-----------|----------------|--------|
| ModelSelector | 534 | ~45-60 min | ✅ |
| FallbackHandler | 352 | ~30-45 min | ✅ |
| PerformanceMonitor | 519 | ~45-60 min | ✅ |
| **Total** | **1,405** | **~120-180 min** | ✅ |

### Optimization Tips

1. **Use caching** - GitHub Actions caches uv dependencies
2. **Run in parallel** - Services run as separate jobs
3. **Limit test scope** - Only run relevant tests
4. **Optimize test speed** - Use `-x` flag to fail fast

---

## Related Documentation

- [[TTA/Workflows/MUTATION_TESTING_GUIDE|Mutation Testing Guide]] - Comprehensive guide
- [[TTA/Workflows/MUTATION_TESTING_COMPLETE_SUMMARY|ModelSelector Results]] - Detailed results
- [[TTA/Workflows/FALLBACK_HANDLER_MUTATION_RESULTS|FallbackHandler Results]] - Detailed results
- [[TTA/Workflows/PERFORMANCE_MONITOR_MUTATION_RESULTS|PerformanceMonitor Results]] - Detailed results
- [[TTA/Workflows/NEXT_STEPS_IMPLEMENTATION_PLAN|Implementation Plan]] - Project plan

---

## Support

For questions or issues:
1. Check this guide and related documentation
2. Review existing mutation test examples
3. Consult the team lead or senior developers
4. Create an issue in the project repository

---

**Last Updated:** 2025-10-11
**Maintained By:** TTA Development Team


---
**Logseq:** [[TTA.dev/Platform_tta_dev/Components/Augment/Core/Kb/Tta___workflows___docs testing mutation testing cicd guide document]]
