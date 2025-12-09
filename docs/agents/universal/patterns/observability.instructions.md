---
description: 'Observability patterns - see what your app is doing when it goes viral'
applyTo: '**/*.py'
agents: ['copilot', 'cline', 'augment', 'roo', 'cursor', 'aider']
---

# Observability Patterns

> When your app goes viral at 2am and something breaks, you need to **see** what's happening.

## The Vibe Coder's Dilemma

```
You: *posts app on Twitter*
App: *goes viral*
You: *checks phone at 2am* "Why is it broken??"
You: *adds print statements everywhere*
You: *still can't figure it out*
```

**Observability = knowing what's happening without adding print statements**

## Three Pillars (Keep It Simple)

### 1. Traces - "What happened?"

See the journey of each request through your app:

```python
from tta_dev_primitives.observability import InstrumentedPrimitive

class MyAPICall(InstrumentedPrimitive):
    """Automatically creates traces - no extra code needed."""

    async def _execute_impl(self, data, context):
        # Your code here
        # TTA.dev automatically records:
        # - Start time
        # - Duration
        # - Success/failure
        # - Input/output (optional)
        return result
```

### 2. Metrics - "How much?"

Numbers over time:
- How many requests?
- How fast are responses?
- How many errors?

```python
# Primitives export Prometheus metrics automatically
# Just run the metrics server:
# uv run python -m tta_dev_primitives.metrics --port 9464
```

### 3. Logs - "What exactly?"

Structured logs that you can actually search:

```python
from tta_dev_primitives import WorkflowContext

context = WorkflowContext(
    workflow_id="user-request-123",
    metadata={"user_id": "abc", "feature": "chat"}
)

# All logs automatically include context
# {"workflow_id": "user-request-123", "user_id": "abc", ...}
```

## Quick Setup

### Zero Config (Just Works)

```python
from tta_dev_primitives import WorkflowContext
from tta_dev_primitives.observability import InstrumentedPrimitive

# Use InstrumentedPrimitive instead of WorkflowPrimitive
# That's it. You get tracing for free.
```

### See Your Traces

```bash
# Start Jaeger (trace viewer) with Docker
docker run -d --name jaeger \
  -p 16686:16686 \
  -p 4317:4317 \
  jaegertracing/all-in-one:latest

# Open http://localhost:16686
# See all your traces!
```

### See Your Metrics

```bash
# Metrics are exported on port 9464 by default
curl http://localhost:9464/metrics

# Or use Grafana for dashboards
docker run -d --name grafana -p 3000:3000 grafana/grafana
```

## When Things Go Wrong

### Scenario: App is slow

**Without observability:**
```
You: "It's slow"
You: *adds print statements*
You: "The database is slow? The API is slow? IDK"
```

**With observability:**
```
You: *opens Jaeger*
You: "Oh, the OpenAI call takes 8 seconds"
You: *adds CachePrimitive*
You: "Fixed!"
```

### Scenario: Random errors

**Without observability:**
```
User: "It broke"
You: "What did you do?"
User: "I just clicked the button"
You: *can't reproduce* *gives up*
```

**With observability:**
```
You: *searches traces for errors*
You: "Ah, rate limited by Stripe API at 10:42pm"
You: *adds RetryPrimitive*
You: "Fixed!"
```

## Correlation IDs (The Magic)

Every request gets a unique ID that flows through your entire app:

```python
context = WorkflowContext(workflow_id="req-abc-123")

# This ID appears in:
# - All traces
# - All logs
# - All metrics
# - Error reports

# User reports a bug? Ask for the workflow_id
# Find EVERYTHING about that request instantly
```

## What to Monitor

### Day 1 (Vibing)
- Nothing. Just build.

### First Users
- Error rate (are things breaking?)
- Response time (is it slow?)

### Growing
- API costs (OpenAI bill getting big?)
- Cache hit rate (is caching working?)

### Going Viral
- Full dashboards
- Alerting (PagerDuty/Discord webhooks)
- Cost tracking per feature

## Quick Reference

| Question | Look At | Tool |
|----------|---------|------|
| "Why is it slow?" | Traces | Jaeger |
| "How many errors?" | Metrics | Grafana |
| "What happened to user X?" | Logs + Traces | Search by workflow_id |
| "How much is OpenAI costing?" | Metrics | Cost dashboard |

## Anti-Patterns

```python
# ❌ Print debugging in production
print(f"DEBUG: {data}")  # Gets lost in noise

# ❌ No correlation
logger.info("Request started")  # Which request??

# ❌ Logging sensitive data
logger.info(f"API key: {api_key}")  # Security nightmare

# ❌ No error context
except Exception as e:
    logger.error("Error")  # WHAT error? WHERE?
```

## The Payoff

When your app goes viral:

| Without Observability | With Observability |
|----------------------|-------------------|
| "It's broken somewhere" | "Line 42 in api.py failed" |
| "Users say it's slow" | "P99 latency is 3.2s" |
| "I think we're getting rate limited?" | "Stripe rate limit hit 47 times today" |
| *panic at 2am* | *fix it in 5 minutes* |

---

**Remember:** Observability is insurance. You don't need it until you REALLY need it. TTA.dev makes it easy to add when you're ready.
