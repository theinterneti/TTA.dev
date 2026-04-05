# Observability Reference

## Stack

| Layer | Component | Location |
|---|---|---|
| Tracing | OpenTelemetry SDK | `ttadev/observability/` |
| Metrics | OTel metrics + Prometheus export | `ttadev/observability/metrics.py` |
| APM | Langfuse (LLM-specific tracing) | `ttadev/integrations/langfuse.py` |
| Local dashboard | `tta observe` / port 8000 | `ttadev/cli/observe.py` |
| Span primitives | `OTelSpanPrimitive`, `OTelMetricPrimitive` | `ttadev/primitives/observability/` |

## Instrumenting a primitive

Use `OTelSpanPrimitive` to wrap any primitive with automatic span creation:

```python
from ttadev.primitives.observability.span import OTelSpanPrimitive
from ttadev.primitives.core.base import LambdaPrimitive, WorkflowContext

async def call_api(data: dict, ctx: WorkflowContext) -> dict:
    return {"status": "ok"}

# Span wraps the primitive — no changes to call_api itself
instrumented = OTelSpanPrimitive(
    LambdaPrimitive(call_api),
    span_name="my_api_call",
    attributes={"service": "my-service"},
)
result = await instrumented.execute(data, ctx)
```

## Langfuse tracing (LLM calls)

```python
from ttadev.integrations.langfuse import tta_apm_langfuse

lf = tta_apm_langfuse.get_integration()
if lf:  # Graceful degradation — Langfuse may not be configured
    with lf.trace("my_llm_task") as trace:
        trace.log_model_call(
            model="gpt-4o-mini",
            prompt=prompt,
            response=response,
            duration_ms=elapsed,
        )
```

`ModelRouterPrimitive` and `UniversalLLMPrimitive` both emit Langfuse traces automatically.
Do not add manual tracing inside provider primitives — it is already handled.

## WorkflowContext correlation

Every primitive receives `WorkflowContext`. Use it to propagate a correlation ID:

```python
ctx = WorkflowContext(workflow_id="req-abc-123")
# This ID appears automatically in all OTel spans, Langfuse traces, and structured logs.

# Pass user-defined metadata
ctx.metadata["user_id"] = "u-42"
ctx.metadata["feature"] = "chat"
```

Structured logs from primitives automatically include `workflow_id` and any `metadata` keys.

## What NOT to do

```python
# ❌ print() in primitives — gets lost, no correlation
print(f"DEBUG: {data}")

# ❌ Logging sensitive values (API keys, tokens, PII)
logger.info(f"API key: {api_key}")

# ❌ Manual OTel setup inside business logic — use OTelSpanPrimitive
tracer = trace.get_tracer(__name__)
with tracer.start_as_current_span("my_span"): ...

# ❌ Creating a second Langfuse client — use get_integration()
from langfuse import Langfuse
lf = Langfuse(...)
```

## Running observability locally

```bash
# Start the local dashboard
uv run python -m ttadev.observability --port 8000
# Open http://localhost:8000 — shows primitive usage, sessions, traces

# Or via CLI
tta observe

# Langfuse local server (Docker)
docker compose -f docker/langfuse.yml up -d
# Open http://localhost:3000
```

## Environment variables

| Variable | Purpose | Default |
|---|---|---|
| `LANGFUSE_SECRET_KEY` | Langfuse auth | unset (tracing disabled) |
| `LANGFUSE_PUBLIC_KEY` | Langfuse auth | unset |
| `LANGFUSE_HOST` | Langfuse server URL | `https://cloud.langfuse.com` |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | OTel collector endpoint | unset |

Langfuse tracing degrades gracefully if keys are not set — primitives continue to work.

## Coverage requirement

The observability primitives and integration module require **100% test coverage** on new code.
Use `MockPrimitive` and `unittest.mock.patch` to avoid real OTel/Langfuse connections in tests.

See [testing.md](./testing.md) for test structure conventions.
