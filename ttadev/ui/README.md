# TTA.dev Batteries-Included Observability Dashboard

**Status: ✅ OPERATIONAL**

Real-time observability dashboard built using TTA.dev's own primitives to prove they work in production.

## Features

- 🔄 **Real-time Updates**: WebSocket-based live metrics
- 🛡️ **Fault Tolerant**: Built with CircuitBreaker + Retry primitives
- 📊 **Production Ready**: REST API + health checks
- 🎨 **Beautiful UI**: Clean, modern dashboard
- 🚀 **Self-Hosting**: TTA.dev uses TTA.dev primitives

## Quick Start

```bash
# From tta-dev directory
uv run python ui/observability_server.py
```

Then open http://localhost:8000 in your browser.

## Architecture

The observability server demonstrates TTA.dev's batteries-included approach:

```python
# Metrics fetcher built with TTA.dev primitives
metrics_workflow = CircuitBreakerPrimitive(
    RetryPrimitive(
        LambdaPrimitive(fetch_live_metrics),
        strategy=RetryStrategy(max_retries=3, backoff_base=2.0),
    ),
    config=CircuitBreakerConfig(
        failure_threshold=5,
        recovery_timeout=30.0,
    ),
)
```

## Endpoints

- `GET /` - Web dashboard
- `GET /api/metrics` - REST API for metrics
- `GET /health` - Health check
- `WS /ws` - WebSocket for real-time updates

## What This Proves

✅ TTA.dev primitives are production-ready
✅ Composition works (CircuitBreaker + Retry + Lambda)
✅ Async workflows handle real traffic
✅ Self-hosting: TTA.dev builds itself

## Next Steps

- [ ] Connect to real OpenTelemetry traces
- [ ] Add trace visualization
- [ ] Auto-discover new primitives as they're built
- [ ] Add metrics persistence
