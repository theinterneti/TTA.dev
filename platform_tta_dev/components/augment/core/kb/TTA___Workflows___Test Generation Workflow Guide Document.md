---
title: OpenHands Test Generation Workflow Guide
tags: #TTA
status: Active
repo: theinterneti/TTA
path: TEST_GENERATION_WORKFLOW_GUIDE.md
created: 2025-10-26
updated: 2025-10-24
---
# [[TTA/Workflows/OpenHands Test Generation Workflow Guide]]

**Date:** 2025-10-24
**Status:** ✅ **PRODUCTION-READY**

---

## Quick Start

### 1. Verify Setup
```bash
# Verify .env file exists and API key is configured
grep OPENROUTER_API_KEY .env

# Validate infrastructure
uv run python scripts/validate_openhands_workflow.py
```

### 2. Generate Tests for Single Module
```bash
# Generate tests for adapters.py (already completed)
uv run python scripts/execute_test_generation.py

# Run generated tests
uv run pytest tests/test_adapters_generated_sample.py -v
```

### 3. Generate Tests for Multiple Modules
```bash
# Generate tests for protocol_bridge, capability_matcher, circuit_breaker
uv run python scripts/generate_tests_batch.py

# Run all generated tests
uv run pytest tests/test_*_generated*.py -v
```

---

## Workflow Overview

### Phase 1: Infrastructure Verification ✅
- OpenHands SDK client wrapper operational
- Free model registry loaded (11 models, 5 verified)
- Error recovery system configured
- Test generation service ready

### Phase 2: Environment Configuration ✅
- `.env` file automatically loaded
- OPENROUTER_API_KEY detected
- Configuration validated
- Ready for test generation

### Phase 3: Test Generation
- Create TestTaskSpecification for target module
- Initialize UnitTestGenerationService
- Execute generate_tests() with max_iterations=3
- Monitor model selection and error recovery

### Phase 4: Test Validation
- Verify syntax validity
- Check test execution
- Measure code coverage
- Assess code quality

### Phase 5: Integration
- Save generated tests to tests/ directory
- Run with pytest to verify execution
- Integrate into CI/CD pipeline

---

## Available Scripts

### 1. `scripts/validate_openhands_workflow.py`
**Purpose:** Validate infrastructure and configuration

**Usage:**
```bash
uv run python scripts/validate_openhands_workflow.py
```

**Output:**
- Infrastructure validation results
- Target module verification
- Ready/not ready status

### 2. `scripts/execute_test_generation.py`
**Purpose:** Generate tests for single module (adapters.py)

**Usage:**
```bash
uv run python scripts/execute_test_generation.py
```

**Output:**
- Test generation execution log
- Generated test file path
- Quality metrics

### 3. `scripts/execute_test_generation_demo.py`
**Purpose:** Demonstrate workflow with mock API key

**Usage:**
```bash
uv run python scripts/execute_test_generation_demo.py
```

**Output:**
- Workflow demonstration
- Model registry showcase
- Error recovery examples

### 4. `scripts/generate_tests_batch.py`
**Purpose:** Generate tests for multiple modules

**Usage:**
```bash
uv run python scripts/generate_tests_batch.py
```

**Output:**
- Batch generation report (JSON)
- Results for each module
- Summary statistics

---

## Target Modules

### 1. protocol_bridge.py
- **Lines:** 385
- **Current Coverage:** 0%
- **Target Coverage:** 70%
- **Classes:** ProtocolTranslator, MessageRouter
- **Status:** Ready for generation

### 2. capability_matcher.py
- **Lines:** 482
- **Current Coverage:** 0%
- **Target Coverage:** 70%
- **Classes:** CapabilityMatcher, CapabilityRegistry
- **Status:** Ready for generation

### 3. circuit_breaker.py
- **Lines:** 443
- **Current Coverage:** 21.79%
- **Target Coverage:** 70%
- **Classes:** CircuitBreaker, CircuitBreakerState
- **Status:** Ready for generation

---

## Model Selection Strategy

### Primary Model (Verified)
- **DeepSeek Chat** - 100% success rate
- Context: 64,000 tokens
- Latency: ~2-3 seconds

### Fallback Models (Verified)
1. **Mistral Small 3.2 24B** - 95% success rate
2. **Google Gemini 2.0 Flash** - 90% success rate
3. **DeepSeek R1 Qwen3 8B** - 85% success rate
4. **Meta Llama 4 Scout** - 80% success rate

### Error Recovery
- Automatic retry with exponential backoff
- Circuit breaker for persistent failures
- Mock fallback for graceful degradation

---

## Quality Metrics

### Coverage Targets
- **Minimum:** 70% code coverage
- **Target:** 80% code coverage
- **Excellent:** 90%+ code coverage

### Quality Scoring
- **Syntax Validity:** 100% required
- **Test Execution:** 100% required
- **Convention Compliance:** 100% required
- **Code Quality:** 80%+ target

### Test Categories
- Unit tests (basic functionality)
- Integration tests (component interaction)
- Edge cases (boundary conditions)
- Error handling (exception scenarios)

---

## Troubleshooting

### Issue: "OPENROUTER_API_KEY not found"
**Solution:** Verify `.env` file and API key
```bash
ls -la .env
grep OPENROUTER_API_KEY .env
```

### Issue: "Rate limit exceeded"
**Solution:** Wait and retry (automatic with exponential backoff)
```bash
# Check rate limit status
grep "rate_limit" batch_test_generation.log
```

### Issue: "Test generation timeout"
**Solution:** Increase timeout in TestTaskSpecification
```python
spec = TestTaskSpecification(
    target_file=Path("src/..."),
    timeout_seconds=900.0,  # Increase from 600
)
```

### Issue: "Low coverage percentage"
**Solution:** Review generated tests and improve
```bash
# Check coverage report
uv run pytest tests/test_*_generated.py --cov=src/agent_orchestration --cov-report=html
```

---

## CI/CD Integration

### GitHub Actions Setup

1. **Add Secret:**
   - Settings → Secrets and variables → Actions
   - Create: `OPENROUTER_API_KEY`

2. **Update Workflow:**
```yaml
- name: Generate Tests
  run: |
    uv run python scripts/generate_tests_batch.py

- name: Run Generated Tests
  run: |
    uv run pytest tests/test_*_generated*.py -v --cov
```

3. **Configure Coverage:**
```yaml
- name: Check Coverage
  run: |
    uv run pytest tests/ --cov=src/agent_orchestration --cov-fail-under=70
```

---

## Best Practices

1. **Always Load .env First**
   - All scripts automatically load `.env`
   - No manual environment variable setup needed

2. **Monitor Model Selection**
   - Check logs for model selection patterns
   - Track fallback chain activations

3. **Review Generated Tests**
   - Verify test quality before integration
   - Update tests as code evolves

4. **Run Tests Regularly**
   - Execute generated tests in CI/CD
   - Monitor coverage trends

5. **Document Changes**
   - Update test generation specs
   - Track coverage improvements

---

## Performance Metrics

### Generation Time
- **Per Module:** 2-5 minutes (depending on size)
- **Batch (3 modules):** 6-15 minutes
- **Parallel:** Can be optimized with async

### Coverage Achievement
- **Protocol Bridge:** Expected 70-80%
- **Capability Matcher:** Expected 70-80%
- **Circuit Breaker:** Expected 70-85%

### Quality Scores
- **Target:** 80+/100
- **Excellent:** 85+/100
- **Outstanding:** 90+/100

---

## Next Steps

1. **Generate Tests for Additional Modules**
   ```bash
   uv run python scripts/generate_tests_batch.py
   ```

2. **Integrate into CI/CD**
   - Update GitHub Actions workflow
   - Configure coverage thresholds
   - Set up automated test generation

3. **Monitor and Optimize**
   - Track generation success rates
   - Monitor model selection patterns
   - Optimize for faster generation

4. **Expand Coverage**
   - Generate tests for entire codebase
   - Implement parallel generation
   - Build test generation dashboard

---

## Related Documentation

- **API Key Fix:** `OPENROUTER_API_KEY_FIX.md`
- **Validation Report:** `END_TO_END_VALIDATION_REPORT.md`
- **Quality Assessment:** `TEST_QUALITY_ASSESSMENT.md`
- **Execution Report:** `TEST_EXECUTION_REPORT.md`

---

**Status:** ✅ PRODUCTION-READY
**Last Updated:** 2025-10-24
**Next Review:** After first batch generation


---
**Logseq:** [[TTA.dev/Platform_tta_dev/Components/Augment/Core/Kb/Tta___workflows___test generation workflow guide document]]
