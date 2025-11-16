# Whiteboard - Testing Architecture

type:: Whiteboard
category:: [[TTA.dev/Architecture]]
status:: Active
created:: [[2025-11-03]]
related:: [[TTA.dev/Testing]], [[TTA.dev/Stage Guides/Testing Stage]]

---

## 🎯 Purpose

Visual architecture of TTA.dev's testing system showing:
- **Test pyramid** (Documentation → Unit → Integration → Slow)
- **Safety mechanisms** and opt-in flows
- **CI/CD job orchestration**
- **Resource management** patterns

**Context:** Created after November 3, 2025 testing infrastructure overhaul that prevented WSL crashes and established safe local development patterns.

---

## 📊 Test Pyramid Architecture

```text
                    ┌─────────────────────┐
                    │  Manual/Scheduled   │
                    │   (Developer Only)  │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │   Slow Tests 🐌      │
                    │  > 30s per test     │
                    │  @pytest.mark.slow  │
                    │  CI: Weekly         │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │ Integration Tests 🔗│
                    │  Ports, Services    │
                    │  300s timeout       │
                    │  RUN_INTEGRATION=true│
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │   Unit Tests ⚡     │
                    │  Fast, Isolated     │
                    │  60s timeout        │
                    │  DEFAULT locally    │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │ Documentation ✓ 📄  │
                    │  Static checks      │
                    │  Link validation    │
                    │  Instant feedback   │
                    └─────────────────────┘

         Frequency: ↑ High        Safety: ↑ Maximum
                    ↓ Low                 ↓ Requires Care
```

**Key Properties:**
- **Bottom** = Most frequent, safest, fastest
- **Top** = Least frequent, resource-intensive, slowest
- **Default local** = Unit tests only
- **Explicit opt-in** = Integration and above

---

## 🛡️ Safety Mechanism Flow

```text
Developer runs: pytest

                    ↓

        ┌───────────────────────┐
        │  pyproject.toml       │
        │  [tool.pytest.ini]    │
        │                       │
        │  • Default markers:   │
        │    -m 'not integration│
        │        and not slow'  │
        │  • Timeout: 60s/test  │
        │  • Max failures: 5    │
        └───────────┬───────────┘
                    ↓
        ┌───────────────────────┐
        │  Unit Tests Run       │
        │  ✅ Safe              │
        │  ✅ Fast              │
        │  ✅ No service starts │
        └───────────┬───────────┘
                    ↓
            Test Results
```

**Integration Path (Explicit):**

```text
Developer runs: RUN_INTEGRATION=true ./scripts/test_integration.sh

                    ↓

        ┌───────────────────────┐
        │  Check Environment    │
        │  Variable             │
        └───────────┬───────────┘
                    ↓
            Is RUN_INTEGRATION=true?
                    │
            ┌───────┴───────┐
            │               │
           No              Yes
            │               │
            ↓               ↓
    Show warning    ┌─────────────────┐
    Exit 1          │ Show resource   │
                    │ warning         │
                    │ (WSL alert)     │
                    └────────┬────────┘
                             ↓
                    ┌─────────────────┐
                    │ Run integration │
                    │ • 300s timeout  │
                    │ • Service starts│
                    │ • Port bindings │
                    └────────┬────────┘
                             ↓
                        Test Results
```

**Emergency Recovery:**

```text
Tests crash / hang

        ↓

./scripts/emergency_stop.sh

        ↓

┌─────────────────────────┐
│ Find stale processes:   │
│ • pytest                │
│ • uvicorn               │
│ • python (test servers) │
└───────────┬─────────────┘
            ↓
┌─────────────────────────┐
│ Kill processes          │
│ (with confirmation)     │
└───────────┬─────────────┘
            ↓
┌─────────────────────────┐
│ Free ports:             │
│ • 8001 (test server 1)  │
│ • 8002 (test server 2)  │
│ • ... (custom ports)    │
└───────────┬─────────────┘
            ↓
    System Clean ✅
```

---

## 🔄 CI/CD Job Orchestration

```text
GitHub Actions: tests-split.yml

                Pull Request
                      ↓
        ┌─────────────────────────────┐
        │  Trigger Split Test Jobs    │
        └─────────────┬───────────────┘
                      ↓
        ┌─────────────┴───────────────┐
        │                             │
        ↓                             ↓
┌───────────────┐          ┌───────────────────┐
│ Job 1: Quick  │          │ Job 2: Docs       │
│ Checks        │          │ Validation        │
│               │          │                   │
│ • Ruff format │          │ • Link checks     │
│ • Ruff lint   │          │ • Code blocks     │
│ • Pyright     │          │ • Frontmatter     │
│               │          │                   │
│ Runtime: ~30s │          │ Runtime: ~20s     │
└───────────────┘          └───────────────────┘
        │                             │
        └─────────────┬───────────────┘
                      ↓
        ┌─────────────────────────────┐
        │    Both pass?               │
        └─────────────┬───────────────┘
                      ↓
              ┌───────┴───────┐
              │               │
             No              Yes
              │               │
              ↓               ↓
      Fail fast      ┌────────────────┐
      (no further    │ Job 3: Unit    │
       jobs run)     │ Tests          │
                     │                │
                     │ • Fast tests   │
                     │ • 60s timeout  │
                     │ • Coverage     │
                     │                │
                     │ Runtime: ~2min │
                     └────────┬───────┘
                              ↓
                     ┌────────────────┐
                     │ Job 4: Integ   │
                     │ Tests          │
                     │                │
                     │ • Services     │
                     │ • 300s timeout │
                     │ • Separate     │
                     │   runner       │
                     │                │
                     │ Runtime: ~5min │
                     └────────┬───────┘
                              ↓
                        All Pass ✅
```

**Job Dependencies:**
- Quick Checks + Docs → **parallel** (no dependency)
- Unit Tests → **depends on** Quick Checks + Docs
- Integration Tests → **depends on** Unit Tests
- **Fail fast:** Stop pipeline at first failure

---

## 📦 Resource Consumption Patterns

```text
Test Type       CPU    Memory   Disk I/O   Network   Ports
─────────────────────────────────────────────────────────────
Documentation   Low    Low      Low        None      None
Unit Tests      Low    Low      Low        None      None
Integration     Med    Medium   Medium     Local     2-5
Slow Tests      High   High     High       External  Variable

WSL Safety Threshold
─────────────────────────────────────────────────────────────
Safe:           ✅     ✅       ✅         ✅        ✅
Caution:        ⚠️     ⚠️       ⚠️         ⚠️        ⚠️
Dangerous:      ❌     ❌       ❌         ❌        ❌
```

**Resource Guard Conditions:**

```python
# In test_integration.sh
if is_wsl; then
    show_warning("WSL detected: Resource intensive tests")
    show_warning("Memory usage may be high")
    show_warning("Consider using VS Code tasks with output monitoring")
fi

if ! check_env_var("RUN_INTEGRATION"); then
    exit_with_error("Set RUN_INTEGRATION=true to proceed")
fi
```

---

## 🎯 Test Markers & Usage

```text
Marker            Use Case                    Local?  CI?   Timeout
──────────────────────────────────────────────────────────────────
(no marker)       Unit test                   ✅ Yes  ✅ Yes  60s
@pytest.mark.unit Explicit unit               ✅ Yes  ✅ Yes  60s
@pytest.mark.integration Service/port tests   ⚠️ Opt  ✅ Yes  300s
@pytest.mark.slow Long-running (>30s)         ❌ No   ⚠️ Week 600s
@pytest.mark.external Requires API/creds      ❌ No   ⚠️ Sched 120s
```

**Example Test Code:**

```python
# Unit test (default, safe)
def test_cache_primitive_logic():
    cache = CachePrimitive(ttl=60)
    assert cache is not None

# Integration test (explicit opt-in)
@pytest.mark.integration
async def test_otel_backend_integration():
    # Starts services on ports 8001, 8002
    # Requires RUN_INTEGRATION=true locally
    ...

# Slow test (CI-only or scheduled)
@pytest.mark.slow
def test_large_dataset_processing():
    # > 30 seconds
    # Not run in standard CI
    ...
```

---

## 🔧 Script Orchestration

```text
Local Development Scripts
─────────────────────────────────────

./scripts/test_fast.sh
    ↓
    Excludes: integration, slow, external
    Includes: Unit tests only
    Timeout: 60s per test
    Max failures: 5
    Best for: Rapid feedback loop

RUN_INTEGRATION=true ./scripts/test_integration.sh
    ↓
    Includes: Integration tests
    Timeout: 300s per test
    Warnings: Resource usage, WSL alerts
    Best for: Pre-commit validation

./scripts/emergency_stop.sh
    ↓
    Kills: pytest, servers, stale processes
    Frees: Ports 8001, 8002, ...
    Best for: Recovery from crashes
```

---

## 📚 Documentation Testing Flow

```text
Markdown Documentation
        ↓
┌───────────────────┐
│ check_md.py       │
│                   │
│ Phase 1: Static   │
│ • Link validation │
│ • Code block check│
│ • Frontmatter     │
│                   │
│ Fast, Safe ✅     │
└─────────┬─────────┘
          ↓
    Always Run
          ↓
┌───────────────────┐
│ Phase 2: Extract  │
│ • Find ```python  │
│ • Parse code      │
│ • Identify type   │
│                   │
│ Analysis Only ✅  │
└─────────┬─────────┘
          ↓
    Optional (CI)
          ↓
┌───────────────────┐
│ Phase 3: Execute  │
│ • Run code blocks │
│ • Validate output │
│ • Check errors    │
│                   │
│ RUN_DOCS_CODE ⚠️  │
└───────────────────┘
```

---

## 🎓 Testing Best Practices (Agentic)

### For AI Agents Writing Tests

1. **Default to Unit Tests**
   ```python
   # ✅ Good - Fast, safe, isolated
   def test_primitive_composition():
       workflow = step1 >> step2
       assert isinstance(workflow, SequentialPrimitive)
   ```

2. **Mark Integration Tests Explicitly**
   ```python
   # ✅ Good - Clear marker, documented why
   @pytest.mark.integration
   async def test_prometheus_metrics_export():
       """Requires Prometheus running on port 9090."""
       ...
   ```

3. **Use Timeouts for Safety**
   ```python
   # ✅ Good - Explicit timeout for long operation
   @pytest.mark.timeout(120)
   async def test_llm_retry_cascade():
       ...
   ```

4. **Mock External Dependencies**
   ```python
   # ✅ Good - No external calls in unit tests
   from tta_dev_primitives.testing import MockPrimitive

   def test_workflow_with_llm():
       mock_llm = MockPrimitive(return_value={"output": "test"})
       workflow = router >> mock_llm >> processor
       ...
   ```

5. **Document Resource Requirements**
   ```python
   @pytest.mark.integration
   async def test_multi_service_coordination():
       """
       Requirements:
       - Docker running
       - Ports 8001-8003 available
       - 500MB+ memory

       WSL: Use RUN_INTEGRATION=true ./scripts/test_integration.sh
       """
       ...
   ```

---

## 🔗 Related Pages

- [[TTA.dev/Stage Guides/Testing Stage]] - Testing lifecycle guide
- [[TTA.dev/Best Practices/Testing]] - Testing best practices
- [[TTA.dev/Common Mistakes/Testing Antipatterns]] - What to avoid
- [[Whiteboard - TTA.dev Architecture Overview]] - Overall architecture
- [[TODO Management System]] - Track testing TODOs

---

## 💡 Key Insights

### Problem Space
- **WSL vulnerability** - Lower resource limits than native Linux
- **Service coordination** - Tests starting servers on ports
- **Resource consumption** - Memory, CPU, I/O can spike
- **Developer safety** - Need guardrails for local development

### Solution Architecture
- **Test pyramid** - Clear levels with different safety profiles
- **Explicit opt-in** - Dangerous operations require conscious choice
- **Timeout protection** - Every test has maximum runtime
- **Split CI** - Optimize job execution and fail fast
- **Emergency tools** - Recovery scripts for crashes

### Future Enhancements
- [ ] Add performance benchmarking tests
- [ ] Create test coverage dashboard
- [ ] Integrate with observability (trace test execution)
- [ ] Add mutation testing for quality verification
- [ ] Create test data generation primitives

---

**Last Updated:** November 3, 2025
**Status:** Active - Production Use
**Maintained by:** TTA.dev Team

- [[Project Hub]]