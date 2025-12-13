# Stable

**Tag page for production-ready, stable features and components**

---

## Overview

**Stable** features in TTA.dev are production-ready components that have:
- ✅ 100% test coverage
- ✅ Comprehensive documentation
- ✅ Real-world usage validation
- ✅ Stable API (no breaking changes)
- ✅ Active maintenance

**Stability Guarantee:** Stable features follow semantic versioning and maintain backward compatibility within major versions.

**See:** [[Production]], [[TTA.dev/Best Practices]]

---

## Stable Components

### Core Primitives (Stable)

All core workflow primitives are production-ready:

**Composition Primitives:**
- [[WorkflowPrimitive]] - Base class for all primitives ✅
- [[TTA Primitives/SequentialPrimitive]] - Sequential execution ✅
- [[TTA Primitives/ParallelPrimitive]] - Parallel execution ✅
- [[TTA Primitives/ConditionalPrimitive]] - Conditional branching ✅
- [[TTA Primitives/RouterPrimitive]] - Dynamic routing ✅

**Recovery Primitives:**
- [[TTA Primitives/RetryPrimitive]] - Retry with backoff ✅
- [[TTA Primitives/FallbackPrimitive]] - Graceful degradation ✅
- [[TTA Primitives/TimeoutPrimitive]] - Circuit breaker ✅
- [[TTA Primitives/CompensationPrimitive]] - Saga pattern ✅
- [[TTA Primitives/CircuitBreakerPrimitive]] - Prevent cascade failures ✅

**Performance Primitives:**
- [[TTA Primitives/CachePrimitive]] - LRU cache with TTL ✅
- [[TTA Primitives/MemoryPrimitive]] - Conversational memory ✅

**Testing Primitives:**
- [[TTA Primitives/MockPrimitive]] - Testing and mocking ✅

**See:** [[Primitive]], [[PRIMITIVES_CATALOG]]

---

## Stable Packages

### Production-Ready Packages

**tta-dev-primitives** ✅
- Status: Stable (v1.x)
- Test Coverage: 95%+
- Documentation: Complete
- Usage: Production-validated

**tta-observability-integration** ✅
- Status: Stable (v1.x)
- Test Coverage: 90%+
- Documentation: Complete
- OpenTelemetry integration

**universal-agent-context** ✅
- Status: Stable (v1.x)
- Test Coverage: 90%+
- Documentation: Complete
- Agent coordination

**See:** [[TTA.dev/Packages]]

---

## Pages Tagged with #Stable

{{query (page-tags [[Stable]])}}

---

## Stability Criteria

### What Makes a Feature Stable?

**1. Testing Requirements**
- ✅ 100% line coverage
- ✅ Unit tests for all paths
- ✅ Integration tests
- ✅ Error case testing
- ✅ Performance benchmarks

**2. Documentation Requirements**
- ✅ API documentation
- ✅ Usage examples
- ✅ Best practices guide
- ✅ Migration guide (if applicable)
- ✅ AGENTS.md instructions

**3. Validation Requirements**
- ✅ Code review approved
- ✅ Real-world usage (dogfooding)
- ✅ Performance validated
- ✅ Security reviewed
- ✅ Accessibility checked (if UI)

**4. Maintenance Requirements**
- ✅ Active maintainer assigned
- ✅ Issue triage process
- ✅ Version compatibility documented
- ✅ Deprecation policy defined

---

## Stability Levels

### Level 1: Core Stable

**Highest stability guarantee**
- No breaking changes in major version
- Long-term support (LTS)
- Critical bug fixes prioritized
- Security updates expedited

**Examples:**
- [[WorkflowPrimitive]] base class
- [[TTA Primitives/SequentialPrimitive]]
- [[TTA Primitives/ParallelPrimitive]]

---

### Level 2: Feature Stable

**Production-ready, may evolve**
- Stable API within minor version
- New features added in minor versions
- Deprecation notices for changes
- Migration paths provided

**Examples:**
- [[TTA Primitives/CachePrimitive]]
- [[TTA Primitives/RouterPrimitive]]
- [[TTA Primitives/RetryPrimitive]]

---

### Level 3: Package Stable

**Entire package is stable**
- All APIs documented and tested
- Version compatibility matrix
- Upgrade guides available
- Support policy defined

**Examples:**
- [[tta-dev-primitives]] package
- [[tta-observability-integration]] package

---

## Using Stable Features

### Recommended for Production

**Stable features are safe for production use:**

```python
# ✅ All these primitives are production-ready
from tta_dev_primitives import (
    SequentialPrimitive,      # Stable
    ParallelPrimitive,        # Stable
    WorkflowContext,          # Stable
)
from tta_dev_primitives.recovery import (
    RetryPrimitive,           # Stable
    FallbackPrimitive,        # Stable
    TimeoutPrimitive,         # Stable
)
from tta_dev_primitives.performance import (
    CachePrimitive,           # Stable
    MemoryPrimitive,          # Stable
)

# Build production workflows with confidence
workflow = (
    TimeoutPrimitive(timeout_seconds=30) >>
    RetryPrimitive(max_retries=3) >>
    CachePrimitive(ttl_seconds=3600) >>
    FallbackPrimitive(
        primary=expensive_operation,
        fallbacks=[cheap_operation, cached_response]
    )
)
```

---

## Version Compatibility

### Semantic Versioning

**Stable features follow semver:**

- **Major version (1.0.0 → 2.0.0)**: Breaking changes allowed
- **Minor version (1.0.0 → 1.1.0)**: New features, backward compatible
- **Patch version (1.0.0 → 1.0.1)**: Bug fixes, backward compatible

**Example:**
```python
# tta-dev-primitives v1.x.x
from tta_dev_primitives import SequentialPrimitive

# Guaranteed to work for all v1.x versions
workflow = step1 >> step2 >> step3
```

---

## Migration from Experimental

### Promotion Process

**When experimental features become stable:**

1. **Announcement**: Release notes describe promotion
2. **API Finalization**: API locked for major version
3. **Documentation Update**: Move from experimental to stable docs
4. **Migration Guide**: Provide upgrade path if API changed
5. **Deprecation**: Mark experimental version as deprecated

**See:** [[Experimental]]

---

## Stability Guarantees

### What We Guarantee

**For Stable Features:**

✅ **API Stability**: No breaking changes within major version
✅ **Backward Compatibility**: Existing code continues to work
✅ **Bug Fixes**: Critical bugs fixed promptly
✅ **Security Updates**: Security issues addressed quickly
✅ **Documentation**: Maintained and up-to-date
✅ **Support**: Community and maintainer support available

---

### What We Don't Guarantee

❌ **Feature Freeze**: New features may be added (minor versions)
❌ **Performance**: May change as optimization improves
❌ **Internal Implementation**: Internals may change (not part of API)
❌ **Dependencies**: Dependency versions may update (within constraints)

---

## Reporting Issues

### For Stable Features

**If you find issues with stable features:**

1. **Check Documentation**: Ensure correct usage
2. **Search Issues**: Check if already reported
3. **Create Issue**: Use GitHub issue template
4. **Provide Details**:
   - Version numbers
   - Code example
   - Expected vs actual behavior
   - Error messages

**Priority:** Stable feature bugs are prioritized for fixes

**See:** [[CONTRIBUTING]]

---

## Best Practices

### ✅ DO

**Use Stable Features for Production:**
```python
# Good: Stable features for production
from tta_dev_primitives import SequentialPrimitive
workflow = step1 >> step2 >> step3
```

**Pin Major Versions:**
```toml
# pyproject.toml
[dependencies]
tta-dev-primitives = "^1.0.0"  # Lock to v1.x
```

**Read Release Notes:**
- Check CHANGELOG before upgrading
- Test in staging before production
- Review migration guides

**Follow Deprecation Notices:**
- Migrate away from deprecated APIs
- Use provided alternatives
- Plan upgrades in advance

---

### ❌ DON'T

**Don't Mix Stable and Experimental:**
```python
# Risky: Mixing stability levels
from tta_dev_primitives import SequentialPrimitive  # Stable
from experimental_package import NewFeature        # Experimental

# Better: Keep separate or accept risk
```

**Don't Rely on Internal APIs:**
```python
# Bad: Using private APIs
workflow._internal_state  # ❌ Not guaranteed

# Good: Use public APIs
workflow.execute(data, context)  # ✅ Stable
```

**Don't Skip Testing After Upgrades:**
```python
# Bad: Blindly upgrade in production
# Good: Test in staging first
```

---

## Monitoring Stability

### Metrics for Stable Features

**Track stability in production:**

```promql
# Error rate (should be < 0.1%)
stable_primitive_errors_total / stable_primitive_executions_total

# Success rate (should be > 99.9%)
stable_primitive_success_total / stable_primitive_executions_total

# Performance (should be consistent)
histogram_quantile(0.95, stable_primitive_duration_seconds)
```

**See:** [[TTA.dev/Observability]]

---

## Stable Patterns

### Production-Ready Patterns

**Resilient LLM Pipeline:**
```python
# All stable components
llm_workflow = (
    TimeoutPrimitive(timeout_seconds=30) >>
    RetryPrimitive(max_retries=3) >>
    CachePrimitive(ttl_seconds=3600) >>
    FallbackPrimitive(
        primary=gpt4,
        fallbacks=[claude, gemini, cached]
    )
)
```

**High-Performance Data Pipeline:**
```python
# All stable components
data_pipeline = (
    CachePrimitive(fetch_data, ttl_seconds=300) >>
    (process_text | process_images | process_metadata) >>
    CachePrimitive(aggregate, ttl_seconds=600)
)
```

**See:** [[Production]], [[TTA.dev/Patterns]]

---

## Support Policy

### Stable Feature Support

**Long-Term Support (LTS):**
- Major version: 2 years minimum
- Minor version: Until next major
- Patch version: Until next minor

**Community Support:**
- GitHub Discussions
- Issue tracking
- Documentation

**Enterprise Support:**
- Priority bug fixes
- Security patches
- Migration assistance

---

## Related Concepts

- [[Experimental]] - Experimental features
- [[Production]] - Production deployment
- [[Testing]] - Testing strategies
- [[TTA.dev/Best Practices]] - Best practices
- [[CONTRIBUTING]] - Contributing guide

---

## Documentation

- [[PRIMITIVES_CATALOG]] - Stable primitive reference
- [[AGENTS]] - Agent instructions
- [[GETTING_STARTED]] - Getting started guide
- [[README]] - Project overview
- [[CHANGELOG]] - Version history

---

**Tags:** #stable #production #reliability #quality #mature #index-page

**Last Updated:** 2025-11-05
**Maintained by:** TTA.dev Team

- [[Project Hub]]

---
**Logseq:** [[TTA.dev/_archive/Nested_copies/Framework/Logseq/Pages/Stable]]
