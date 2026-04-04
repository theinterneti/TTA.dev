# TTA APM LangFuse

LangFuse APM integration for TTA.dev workflow primitives.

## Installation

```bash
uv pip install -e platform/apm/langfuse
```

## Quick Start

```python
from tta_apm_langfuse import LangFuseIntegration
from ttadev.primitives import SequentialPrimitive

# Option 1: Initialize from environment variables (recommended)
# Set LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY (and optionally LANGFUSE_HOST)
apm = LangFuseIntegration.from_env()

# Option 2: Initialize with explicit keys
apm = LangFuseIntegration(
    public_key="<langfuse-public-key>",
    secret_key="<langfuse-secret-key>",
    host="https://cloud.langfuse.com"
)

# Instrument primitives
workflow = SequentialPrimitive([step1, step2, step3])
instrumented = apm.instrument(workflow)

# Execute with automatic tracing
result = await instrumented.execute(data, context)
```

## Features

- Automatic tracing of primitive execution
- Parent/child trace relationships
- Input/output capture
- Duration metrics
- Error tracking
- LLM generation logging

## Configuration

Set environment variables (recommended approach — use `LangFuseIntegration.from_env()` in code):

```bash
export LANGFUSE_PUBLIC_KEY="pk-lf-..."   # required; get from https://cloud.langfuse.com
export LANGFUSE_SECRET_KEY="sk-lf-..."   # required
export LANGFUSE_HOST="https://cloud.langfuse.com"  # optional; defaults to cloud.langfuse.com
```

> **Tip:** Add these to `.env` (copy from `.env.example`) — never commit raw keys to version control.

> **Grafana / OTel Collector note:** The OTel Collector → Tempo → Grafana pipeline is **not**
> implemented in v0.2. Langfuse is the current APM integration. Grafana support is planned for a
> future release.

## Development

```bash
uv sync --all-extras
uv run pytest -v
```
