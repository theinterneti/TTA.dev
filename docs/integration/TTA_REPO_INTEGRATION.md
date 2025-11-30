# TTA Repository Integration Guide

**Safe integration patterns for using TTA.dev primitives with theinterneti/TTA**

This guide covers how to safely integrate TTA.dev's development primitives, observability layer, and agent configurations into the main TTA repository.

---

## Overview

TTA.dev provides three integration points:

| Package | Purpose | Integration Method |
|---------|---------|-------------------|
| `tta-dev-primitives` | Workflow patterns | Git submodule or pip install |
| `tta-observability-integration` | APM & metrics | Git submodule or pip install |
| `universal-agent-context` | AI assistant configs | Copy templates |

---

## Integration Options

### Option 1: Git Submodule (Recommended for Development)

```bash
# In the TTA repository
cd /path/to/TTA

# Add TTA.dev as a submodule
git submodule add https://github.com/theinterneti/TTA.dev packages/tta-dev

# Initialize submodule
git submodule update --init --recursive

# Install packages in development mode
cd packages/tta-dev/packages/tta-dev-primitives
uv pip install -e .
```

**Pros:**
- Always have latest development version
- Easy to contribute back fixes
- Full source access for debugging

**Cons:**
- Requires submodule management
- Needs synchronization across team

### Option 2: Direct Install (Recommended for Production)

```bash
# Install from GitHub
uv pip install git+https://github.com/theinterneti/TTA.dev#subdirectory=packages/tta-dev-primitives
uv pip install git+https://github.com/theinterneti/TTA.dev#subdirectory=packages/tta-observability-integration
```

**Pros:**
- Clean dependency management
- Version pinning possible
- No submodule complexity

**Cons:**
- Need to wait for releases for fixes

### Option 3: Copy Agent Context Only

If you only need the AI assistant configurations:

```bash
# Copy agent configurations to TTA repo
cp -r TTA.dev/packages/universal-agent-context/.github/ TTA/
cp -r TTA.dev/packages/universal-agent-context/.augment/ TTA/
cp TTA.dev/packages/universal-agent-context/AGENTS.md TTA/
cp TTA.dev/packages/universal-agent-context/CLAUDE.md TTA/
```

---

## Safe Integration Patterns

### 1. Wrap TTA Code with Primitives

Instead of modifying TTA code directly, wrap it with primitives:

```python
# In TTA: existing agent code
async def generate_narrative(prompt: str, context: dict) -> str:
    # Existing TTA logic
    ...

# Wrap with TTA.dev primitives for reliability
from tta_dev_primitives import (
    LambdaPrimitive,
    RetryPrimitive,
    TimeoutPrimitive,
    CachePrimitive,
    WorkflowContext
)
from tta_dev_primitives.recovery.retry import RetryStrategy

# Create wrapped workflow
narrative_workflow = CachePrimitive(
    primitive=TimeoutPrimitive(
        primitive=RetryPrimitive(
            primitive=LambdaPrimitive(
                lambda data, ctx: generate_narrative(data["prompt"], data["context"])
            ),
            strategy=RetryStrategy(max_retries=3)
        ),
        timeout_seconds=30.0
    ),
    cache_key_fn=lambda d, c: f"narrative:{hash(d['prompt'])}",
    ttl_seconds=3600.0
)

# Use in TTA
async def safe_generate_narrative(prompt: str, context: dict) -> str:
    ctx = WorkflowContext(workflow_id="narrative-gen")
    result = await narrative_workflow.execute(
        {"prompt": prompt, "context": context},
        ctx
    )
    return result
```

### 2. Add Observability Without Code Changes

```python
# Initialize observability early in TTA's startup
from observability_integration import initialize_observability

def setup_tta():
    # Initialize APM before anything else
    initialize_observability(
        service_name="tta-main",
        enable_prometheus=True,
        prometheus_port=9464
    )

    # Rest of TTA initialization...
```

### 3. Use Router for Multi-Model Support

```python
from tta_dev_primitives import RouterPrimitive, LambdaPrimitive

# TTA's existing model calls
async def call_openai(data, ctx):
    # Existing OpenAI integration
    ...

async def call_anthropic(data, ctx):
    # Existing Anthropic integration
    ...

async def call_local(data, ctx):
    # Local model fallback
    ...

# Create intelligent router
model_router = RouterPrimitive(
    routes={
        "openai": LambdaPrimitive(call_openai),
        "anthropic": LambdaPrimitive(call_anthropic),
        "local": LambdaPrimitive(call_local),
    },
    router_fn=lambda data, ctx: ctx.metadata.get("preferred_model", "local"),
    default="local"
)
```

---

## Directory Structure After Integration

```
TTA/
├── .github/                    # GitHub Copilot instructions
│   ├── copilot-instructions.md
│   └── instructions/           # Path-specific instructions
├── .augment/                   # Augment CLI configs
├── .cline/                     # Cline configs
├── .cursor/                    # Cursor configs
├── AGENTS.md                   # Universal agent instructions
├── CLAUDE.md                   # Claude-specific instructions
├── packages/
│   └── tta-dev/                # TTA.dev submodule (if using Option 1)
│       └── packages/
│           ├── tta-dev-primitives/
│           ├── tta-observability-integration/
│           └── universal-agent-context/
├── src/
│   └── tta/                    # Main TTA code
│       ├── agents/
│       ├── workflows/          # Primitive-wrapped workflows
│       └── observability/      # APM setup
└── tests/
```

---

## Testing the Integration

### 1. Run the Integration Demo

```bash
# From TTA.dev root
cd packages/tta-dev-primitives
uv run python ../../scripts/integration_demo.py
```

Expected output: All 5 demos should pass.

### 2. Verify Observability

```python
# test_observability.py
import asyncio
from tta_dev_primitives import LambdaPrimitive, WorkflowContext
from observability_integration import initialize_observability

async def test_integration():
    # Setup
    initialize_observability(
        service_name="tta-test",
        enable_prometheus=True
    )

    # Create simple workflow
    workflow = LambdaPrimitive(lambda d, c: {"status": "ok"})
    ctx = WorkflowContext(workflow_id="test")

    # Execute
    result = await workflow.execute({}, ctx)

    assert result["status"] == "ok"
    print("✅ Integration test passed")

asyncio.run(test_integration())
```

### 3. Check Metrics

After running workflows, check Prometheus metrics:

```bash
curl http://localhost:9464/metrics
```

---

## Keeping Packages Loosely Coupled

### Principles

1. **No Hard Dependencies**: TTA should work without TTA.dev (graceful degradation)
2. **Interface-Based**: Use protocols/ABCs at boundaries
3. **Optional Enhancement**: TTA.dev adds reliability, doesn't change behavior

### Example: Optional Primitive Wrapping

```python
# In TTA's code
try:
    from tta_dev_primitives import CachePrimitive, TimeoutPrimitive
    PRIMITIVES_AVAILABLE = True
except ImportError:
    PRIMITIVES_AVAILABLE = False

def create_workflow(base_func):
    """Wrap function with primitives if available, otherwise return as-is."""
    if not PRIMITIVES_AVAILABLE:
        return base_func

    from tta_dev_primitives import LambdaPrimitive, WorkflowContext

    wrapped = CachePrimitive(
        primitive=TimeoutPrimitive(
            primitive=LambdaPrimitive(base_func),
            timeout_seconds=30.0
        ),
        cache_key_fn=lambda d, c: str(d),
        ttl_seconds=3600.0
    )

    async def enhanced(data):
        ctx = WorkflowContext()
        return await wrapped.execute(data, ctx)

    return enhanced
```

---

## Troubleshooting

### Import Errors

```bash
# Ensure packages are installed
uv pip list | grep tta

# If missing, install
uv pip install -e packages/tta-dev/packages/tta-dev-primitives
```

### Metrics Not Showing

```python
# Check APM initialization
from observability_integration import get_tracer, get_meter

tracer = get_tracer(__name__)
meter = get_meter(__name__)

print(f"Tracer: {tracer}")  # Should not be None
print(f"Meter: {meter}")    # Should not be None
```

### Cache Not Working

```python
# Check cache stats
workflow = CachePrimitive(...)
stats = workflow.get_stats()
print(f"Hits: {stats['hits']}, Misses: {stats['misses']}")
```

---

## Next Steps

1. **Start Small**: Wrap one TTA workflow with primitives
2. **Add Observability**: Initialize APM in TTA's main entry point
3. **Copy Agent Configs**: Set up AI assistant instructions
4. **Expand Gradually**: Add more primitive wrappers as needed
5. **Monitor**: Watch metrics for performance improvements

---

## Support

- **Issues**: [TTA.dev Issues](https://github.com/theinterneti/TTA.dev/issues)
- **Discussions**: [TTA.dev Discussions](https://github.com/theinterneti/TTA.dev/discussions)
- **Documentation**: See `docs/` in TTA.dev repository
