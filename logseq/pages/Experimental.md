# Experimental

**Tag page for experimental features and preview functionality**

---

## Overview

**Experimental** features in TTA.dev are preview components that:
- ⚠️ May have incomplete testing
- ⚠️ API may change without notice
- ⚠️ Documentation may be partial
- ⚠️ Not recommended for production
- ✅ Available for feedback and testing

**Use at your own risk.** Experimental features are for early adopters and testing only.

**See:** [[Stable]], [[TTA.dev/Architecture]]

---

## Experimental Features

### Current Experimental Features

**Planned Database Primitives:**
- [[SupabasePrimitive]] - Supabase integration (planned) ⚠️
- [[SQLitePrimitive]] - SQLite integration (planned) ⚠️
- [[PostgreSQLPrimitive]] - PostgreSQL integration (planned) ⚠️

**Under Review Packages:**
- [[keploy-framework]] - API testing framework ⚠️
- [[python-pathway]] - Python analysis utilities ⚠️
- [[js-dev-primitives]] - JavaScript primitives (placeholder) ⚠️

**See:** [[TTA.dev/Packages]], [[TTA.dev Package Decisions]]

---

## Pages Tagged with #Experimental

{{query (page-tags [[Experimental]])}}

---

## Experimental Feature Criteria

### What Makes a Feature Experimental?

**1. Development Stage**
- 🚧 Active development
- 🚧 API not finalized
- 🚧 Testing incomplete
- 🚧 Documentation in progress
- 🚧 Performance not optimized

**2. Validation Status**
- ⏳ Limited real-world usage
- ⏳ Proof of concept complete
- ⏳ Waiting for user feedback
- ⏳ Architecture being validated

**3. Support Level**
- ⚠️ Best-effort support only
- ⚠️ May be deprecated without migration path
- ⚠️ Breaking changes possible
- ⚠️ Limited documentation

---

## Using Experimental Features

### Enable Experimental Features

**Explicit opt-in required:**

```python
# ⚠️ Experimental features require explicit import
from tta_dev_primitives.experimental import NewFeature

# Or use workarounds for planned features
from custom_primitives import CustomSupabasePrimitive
```

**Configuration:**
```toml
# pyproject.toml
[tool.tta-dev]
enable_experimental = true
experimental_features = ["database-primitives"]
```

---

### Experimental Feature Warnings

**Expect warnings in logs:**

```python
import logging
logger = logging.getLogger(__name__)

# Experimental features log warnings
logger.warning(
    "Using experimental feature",
    feature="SupabasePrimitive",
    stability="experimental"
)
```

---

## Feedback and Testing

### Help Us Improve

**If you use experimental features:**

1. **Provide Feedback**: Open GitHub issues
2. **Share Use Cases**: Describe your usage
3. **Report Bugs**: Help us find issues
4. **Suggest Improvements**: API and feature ideas

**Your feedback helps experimental features become stable!**

---

### Testing Experimental Features

**Recommended testing approach:**

```python
import pytest

@pytest.mark.experimental
@pytest.mark.asyncio
async def test_experimental_feature():
    """Test experimental database primitive."""
    # Test in isolated environment
    primitive = ExperimentalPrimitive()

    # Expect potential issues
    with pytest.warns(UserWarning):
        result = await primitive.execute(data, context)

    # Document behavior
    assert "result" in result
```

---

## Migration Path

### From Experimental to Stable

**Typical progression:**

1. **Experimental Release** (v0.x.x)
   - Preview API
   - Gather feedback
   - Iterate quickly

2. **Beta Release** (v0.9.x)
   - API stabilizing
   - Comprehensive testing
   - Documentation improving

3. **Release Candidate** (v1.0.0-rc)
   - API locked
   - Full testing
   - Complete documentation

4. **Stable Release** (v1.0.0)
   - Production-ready
   - Stability guarantees
   - Long-term support

**See:** [[Stable]]

---

### Breaking Changes

**Experimental features may break:**

```python
# Version 0.1.0
from experimental import NewPrimitive
primitive = NewPrimitive(param1="value")

# Version 0.2.0 - BREAKING CHANGE
from experimental import NewPrimitive
primitive = NewPrimitive(config={"param1": "value"})  # API changed

# No migration guide guaranteed for experimental
```

---

## Deprecation Policy

### Experimental Feature Deprecation

**Experimental features may be:**

1. **Promoted to Stable** - Becomes production-ready
2. **Deprecated** - Removed from codebase
3. **Archived** - Moved to separate package

**Notice Period:**
- Experimental: 0-30 days notice
- Beta: 60 days notice
- Stable: 180 days minimum

---

## Current Status

### Planned Database Primitives

**Status: Design Phase**

**SupabasePrimitive:**
- Status: 🚧 Planned
- Target: Q1 2026
- Workaround: Custom primitive available
- See: [[SupabasePrimitive]]

**SQLitePrimitive:**
- Status: 🚧 Planned
- Target: Q1 2026
- Workaround: Direct sqlite3 usage
- See: [[SQLitePrimitive]]

**PostgreSQLPrimitive:**
- Status: 🚧 Planned
- Target: Q2 2026
- Workaround: Custom primitive with SQLAlchemy
- See: [[PostgreSQLPrimitive]]

---

### Under Review Packages

**keploy-framework:**
- Status: ⚠️ Under review
- Decision Deadline: 2025-11-07
- Issue: No pyproject.toml, not in workspace
- See: [[keploy-framework]], [[TTA.dev Package Decisions]]

**python-pathway:**
- Status: ⚠️ Under review
- Decision Deadline: 2025-11-07
- Issue: Unclear use case
- See: [[python-pathway]], [[TTA.dev Package Decisions]]

**js-dev-primitives:**
- Status: 🚧 Placeholder only
- Decision Deadline: 2025-11-14
- Issue: Directory structure only, no implementation
- See: [[js-dev-primitives]], [[TTA.dev Package Decisions]]

---

## Best Practices

### ✅ DO

**Use for Testing and Feedback:**
```python
# Good: Testing experimental features in dev
if os.getenv("ENVIRONMENT") == "development":
    from experimental import NewFeature
    result = await NewFeature().execute(data, context)
```

**Isolate from Production:**
```python
# Good: Feature flag for experimental
if config.enable_experimental:
    workflow = experimental_workflow
else:
    workflow = stable_workflow
```

**Provide Feedback:**
- Open issues with usage details
- Share performance results
- Suggest API improvements

**Have Fallback Plans:**
```python
# Good: Fallback to stable alternative
try:
    from experimental import NewPrimitive
    primitive = NewPrimitive()
except ImportError:
    from stable import StablePrimitive
    primitive = StablePrimitive()
```

---

### ❌ DON'T

**Don't Use in Production:**
```python
# Bad: Experimental in production
workflow = experimental_primitive >> production_step  # ❌
```

**Don't Rely on API Stability:**
```python
# Bad: Assuming API won't change
# May break in next version
```

**Don't Skip Version Pinning:**
```toml
# Bad: Open-ended version
experimental-package = "*"  # ❌

# Good: Pin experimental versions
experimental-package = "==0.1.0"  # ✅
```

**Don't Expect Support:**
```python
# Bad: Expecting production-level support
# Experimental features have best-effort support
```

---

## Experimental API Patterns

### Workarounds for Planned Features

**Until database primitives are stable, use workarounds:**

**Supabase Workaround:**
```python
from tta_dev_primitives import WorkflowPrimitive
from supabase import create_client

class CustomSupabasePrimitive(WorkflowPrimitive):
    """Custom Supabase primitive."""

    def __init__(self, url: str, key: str):
        self.client = create_client(url, key)

    async def _execute_impl(self, context, input_data):
        # Your Supabase logic
        result = self.client.table("users").select("*").execute()
        return {"data": result.data}
```

**SQLite Workaround:**
```python
import sqlite3
from tta_dev_primitives import WorkflowPrimitive

class CustomSQLitePrimitive(WorkflowPrimitive):
    """Custom SQLite primitive."""

    def __init__(self, db_path: str):
        self.db_path = db_path

    async def _execute_impl(self, context, input_data):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(input_data["query"])
        result = cursor.fetchall()
        conn.close()
        return {"rows": result}
```

**See:** [[SupabasePrimitive]], [[SQLitePrimitive]]

---

## Contributing

### Help Make Features Stable

**Contribute to experimental features:**

1. **Test**: Use features and report issues
2. **Document**: Improve documentation
3. **Code**: Submit PRs with improvements
4. **Feedback**: Share use cases and requirements

**See:** [[CONTRIBUTING]]

---

## Monitoring Experimental Features

### Usage Tracking

```promql
# Track experimental feature usage
experimental_feature_usage_total{feature="database_primitives"}

# Monitor error rates
experimental_feature_errors_total{feature="database_primitives"}

# Performance baseline
experimental_feature_duration_seconds{feature="database_primitives"}
```

**See:** [[TTA.dev/Observability]]

---

## Related Concepts

- [[Stable]] - Production-ready features
- [[Production]] - Production deployment
- [[Testing]] - Testing strategies
- [[TTA.dev/Architecture]] - Architecture decisions
- [[TTA.dev Package Decisions]] - Package decisions

---

## Documentation

- [[TTA.dev/Packages]] - Package overview
- [[PRIMITIVES_CATALOG]] - Primitive catalog
- [[CONTRIBUTING]] - Contributing guide
- [[CHANGELOG]] - Version history

---

**Tags:** #experimental #preview #beta #under-development #feedback-wanted #index-page

**Last Updated:** 2025-11-05
**Maintained by:** TTA.dev Team
