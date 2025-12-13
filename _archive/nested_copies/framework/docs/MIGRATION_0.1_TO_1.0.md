# Migration Guide: 0.1.x → 1.0.0

**Upgrading TTA.dev from 0.1.x to 1.0.0**

**Last Updated:** November 7, 2025

---

## Overview

Version 1.0.0 is the first production-ready release of TTA.dev. This guide helps you upgrade from 0.1.x with minimal friction.

**Good News:** Most changes are **additions** rather than breaking changes. If you're using core primitives, your code will continue to work with minimal updates.

---

## 🎯 Quick Migration Checklist

- [ ] Update package versions to 1.0.0
- [ ] Update import statements for adaptive primitives
- [ ] Review new adaptive primitives features
- [ ] Check observability integration (if using)
- [ ] Run tests to verify compatibility
- [ ] Optional: Adopt new features (adaptive primitives, ACE framework, memory primitives)

---

## 📦 Version Updates

### Update Package Versions

```bash
# If using pip
pip install --upgrade tta-dev-primitives==1.0.0
pip install --upgrade tta-observability-integration==1.0.0
pip install --upgrade universal-agent-context==1.0.0

# If using uv (recommended)
uv add tta-dev-primitives@1.0.0
uv add tta-observability-integration@1.0.0
uv add universal-agent-context@1.0.0
```

---

## 🔄 Import Path Changes

### Adaptive Primitives (NEW)

**Before (0.1.x):** Adaptive primitives were not available.

**After (1.0.0):** Import from main adaptive module:

```python
# ✅ RECOMMENDED (1.0.0)
from tta_dev_primitives.adaptive import (
    AdaptiveRetryPrimitive,
    AdaptiveFallbackPrimitive,
    AdaptiveCachePrimitive,
    LogseqStrategyIntegration,
    LearningMode,
)

# ⚠️ ALSO WORKS but verbose
from tta_dev_primitives.adaptive.retry import AdaptiveRetryPrimitive
from tta_dev_primitives.adaptive.fallback import AdaptiveFallbackPrimitive
```

### Core Primitives (UNCHANGED)

No changes required for core primitives:

```python
# ✅ STILL WORKS (no changes needed)
from tta_dev_primitives import (
    WorkflowPrimitive,
    SequentialPrimitive,
    ParallelPrimitive,
    WorkflowContext,
)
from tta_dev_primitives.recovery import (
    RetryPrimitive,
    FallbackPrimitive,
    TimeoutPrimitive,
)
from tta_dev_primitives.performance import CachePrimitive
```

---

## 🆕 New Features You Can Adopt

### 1. Adaptive/Self-Improving Primitives

**What:** Primitives that automatically learn and optimize themselves.

**When to adopt:** If you have services with:
- Variable reliability (intermittent failures)
- Different behavior across environments (production vs staging)
- Need for automatic optimization without manual tuning

**Example Migration:**

**Before (0.1.x) - Manual retry:**

```python
from tta_dev_primitives.recovery import RetryPrimitive

# Manual configuration - you pick the parameters
api_with_retry = RetryPrimitive(
    primitive=unstable_api,
    max_retries=3,  # Manually chosen
    backoff_strategy="exponential",
    initial_delay=1.0,  # Manually tuned
)
```

**After (1.0.0) - Adaptive retry:**

```python
from tta_dev_primitives.adaptive import AdaptiveRetryPrimitive, LogseqStrategyIntegration

# Automatic learning - it figures out optimal parameters!
logseq = LogseqStrategyIntegration("my_api_service")
api_with_adaptive_retry = AdaptiveRetryPrimitive(
    target_primitive=unstable_api,
    logseq_integration=logseq,
    enable_auto_persistence=True,  # Saves strategies to knowledge base
)

# Use it - learning happens automatically
result = await api_with_adaptive_retry.execute(data, context)

# Check what it learned
print(api_with_adaptive_retry.strategies)
```

**Benefits:**
- ✅ Automatic parameter optimization
- ✅ Context-aware strategies (different per environment)
- ✅ Knowledge base integration for strategy sharing
- ✅ Zero manual tuning required

**When NOT to migrate:**
- ❌ Service is perfectly stable (no failures)
- ❌ Single environment only (no variation to learn from)
- ❌ You need deterministic behavior for testing

### 2. Memory Primitives (Conversational Memory)

**What:** Hybrid conversational memory with zero-setup fallback.

**When to adopt:** If you're building:
- Multi-turn conversational agents
- Workflows requiring context across operations
- Personalization based on interaction history

**Example:**

```python
from tta_dev_primitives.performance import MemoryPrimitive

# Zero-setup mode (no Docker/Redis required)
memory = MemoryPrimitive(max_size=100)

# Store conversation turns
await memory.add("user_1", {"role": "user", "content": "What is a primitive?"})
await memory.add("assistant_1", {"role": "assistant", "content": "A primitive is..."})

# Search conversation history
results = await memory.search("primitive")

# Optional: Upgrade to Redis for persistence
memory_persistent = MemoryPrimitive(
    redis_url="redis://localhost:6379",
    enable_redis=True
)
# Same API, enhanced backend - automatic fallback if Redis unavailable
```

### 3. ACE Framework (AI Code Generation)

**What:** Zero-cost AI code generation with E2B validation.

**When to adopt:** If you need:
- Automated test generation
- Code snippet validation
- AI-assisted development

**Example:**

```python
from tta_dev_primitives.ace import GeneratorAgent, ReflectorAgent

# Generate code using LLM
generator = GeneratorAgent()
code = await generator.generate_code(requirement="Create a retry function")

# Validate in E2B sandbox
reflector = ReflectorAgent()
result = await reflector.validate_code(code)

if result["success"]:
    print("Generated code works!")
```

**Cost:** $0 using Google Gemini 2.0 Flash Experimental (free tier) + E2B free tier.

### 4. Enhanced Observability

**What:** Automatic OpenTelemetry + Prometheus integration.

**When to adopt:** If you need:
- Production metrics and tracing
- Real-time monitoring
- Cost optimization tracking

**Example:**

```python
from observability_integration import initialize_observability
from observability_integration.primitives import RouterPrimitive, CachePrimitive

# Initialize observability
initialize_observability(
    service_name="my-app",
    enable_prometheus=True  # Metrics on port 9464
)

# Use enhanced primitives (automatic metrics)
workflow = (
    input_step >>
    RouterPrimitive(routes={"fast": llm1, "quality": llm2}) >>  # Route selection metrics
    CachePrimitive(expensive_op, ttl_seconds=3600) >>  # Hit/miss rate metrics
    output_step
)
```

**Benefits:**
- 30-40% cost reduction via Cache + Router
- Real-time metrics in Prometheus/Grafana
- Distributed tracing across workflows

---

## 🔍 Breaking Changes

### None!

**Good news:** Version 1.0.0 has **no breaking changes** from 0.1.x.

All existing code using core primitives will continue to work without modification. The changes are:

- ✅ **Additions:** New adaptive primitives, ACE framework, memory primitives
- ✅ **Improvements:** Better import paths, enhanced observability
- ✅ **Fixes:** Export issues resolved (LogseqStrategyIntegration now available)

---

## 🧪 Testing Your Migration

### 1. Run Your Existing Test Suite

```bash
# Should pass without changes
uv run pytest -v
```

### 2. Verify Imports

```python
# Test that your imports still work
from tta_dev_primitives import WorkflowPrimitive, SequentialPrimitive
from tta_dev_primitives.recovery import RetryPrimitive
from tta_dev_primitives.performance import CachePrimitive

# Test new imports (if adopting adaptive primitives)
from tta_dev_primitives.adaptive import AdaptiveRetryPrimitive

print("✅ All imports successful!")
```

### 3. Run Integration Tests

If you have integration tests with TTA.dev primitives:

```bash
# Run integration tests
uv run pytest tests/integration/ -v
```

---

## 📊 Gradual Migration Strategy

You don't have to migrate everything at once! Here's a recommended approach:

### Phase 1: Update Versions (Week 1)

1. Update package versions
2. Run existing tests
3. Fix any import issues (should be minimal/none)
4. Deploy to staging

### Phase 2: Adopt Observability (Week 2)

1. Add `tta-observability-integration` package
2. Initialize observability in your application
3. Use enhanced primitives (RouterPrimitive, CachePrimitive)
4. Set up Prometheus/Grafana dashboards
5. Monitor cost reduction

### Phase 3: Try Adaptive Primitives (Week 3-4)

1. Identify 1-2 unstable services
2. Replace RetryPrimitive with AdaptiveRetryPrimitive
3. Let it learn for a week
4. Review learned strategies in Logseq
5. Expand to more services

### Phase 4: Explore ACE Framework (Month 2)

1. Try ACE for test generation
2. Validate generated code in E2B sandbox
3. Compare with manual test writing
4. Adopt for routine test generation

---

## 🆘 Troubleshooting

### Import Error: "cannot import name 'AdaptiveRetryPrimitive'"

**Cause:** Package version not updated.

**Solution:**

```bash
uv add tta-dev-primitives@1.0.0
# or
pip install --upgrade tta-dev-primitives==1.0.0
```

### Import Error: "cannot import name 'LogseqStrategyIntegration'"

**Cause:** Old cached package.

**Solution:**

```bash
# Clear Python cache
rm -rf __pycache__ .pytest_cache
uv sync --all-extras
```

### Tests Failing After Upgrade

**Cause:** Possible version mismatch between packages.

**Solution:**

```bash
# Ensure all TTA.dev packages are at 1.0.0
uv pip list | grep tta-

# Update all together
uv add tta-dev-primitives@1.0.0 tta-observability-integration@1.0.0 universal-agent-context@1.0.0
```

### Observability Metrics Not Appearing

**Cause:** Observability not initialized.

**Solution:**

```python
from observability_integration import initialize_observability

# Initialize before using primitives
initialize_observability(
    service_name="my-app",
    enable_prometheus=True
)
```

---

## 📚 Additional Resources

### Documentation

- **CHANGELOG.md** - Complete list of changes
- **ADAPTIVE_PRIMITIVES_VERIFICATION_COMPLETE.md** - Adaptive primitives verification
- **ACE_COMPLETE_JOURNEY_SUMMARY.md** - ACE framework details
- **GETTING_STARTED.md** - Quick start guide with new patterns

### Examples

- `examples/auto_learning_demo.py` - Adaptive primitives demo
- `examples/verify_adaptive_primitives.py` - Verification suite
- `examples/production_adaptive_demo.py` - Production simulation

### Support

- **GitHub Issues:** <https://github.com/theinterneti/TTA.dev/issues>
- **Discussions:** <https://github.com/theinterneti/TTA.dev/discussions>
- **Documentation:** `docs/` directory

---

## ✅ Post-Migration Checklist

After migrating to 1.0.0, verify:

- [ ] All tests passing
- [ ] Imports updated (if using adaptive primitives)
- [ ] Observability metrics flowing (if enabled)
- [ ] No regressions in production
- [ ] Performance improvements observed (if using adaptive primitives)
- [ ] Knowledge base integration working (if using LogseqStrategyIntegration)
- [ ] Documentation updated for your team

---

## 🎉 Welcome to 1.0.0!

You're now on the first production-ready release of TTA.dev with:

- ✅ Self-improving adaptive primitives
- ✅ Zero-cost AI code generation
- ✅ Comprehensive observability
- ✅ 574 tests with 95%+ coverage
- ✅ Production-validated reliability

**Next Steps:**

1. ⭐ Star the repo: <https://github.com/theinterneti/TTA.dev>
2. 📖 Read the docs: [`docs/`](docs/)
3. 🧪 Try adaptive primitives with your most unstable service
4. 📊 Set up observability dashboards
5. 🎓 Explore learning paths in Logseq

**Questions?** Open an issue or start a discussion on GitHub.

---

**Last Updated:** November 7, 2025
**Version:** 1.0.0
**Maintained by:** TTA.dev Team


---
**Logseq:** [[TTA.dev/_archive/Nested_copies/Framework/Docs/Migration_0.1_to_1.0]]
