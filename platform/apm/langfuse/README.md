# TTA APM LangFuse

LangFuse APM integration for TTA.dev workflow primitives.

## Installation

```bash
uv pip install -e platform/apm/langfuse
```

## Quick Start

```python
from tta_apm_langfuse import LangFuseIntegration
from tta_dev_primitives import SequentialPrimitive

# Initialize integration
apm = LangFuseIntegration(
    public_key="pk_...",
    secret_key="sk_...",
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

Set environment variables:

```bash
export LANGFUSE_PUBLIC_KEY="pk_..."
export LANGFUSE_SECRET_KEY="sk_..."
export LANGFUSE_HOST="https://cloud.langfuse.com"
```

## Development

```bash
uv sync --all-extras
uv run pytest -v
```
