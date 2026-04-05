# Composition Patterns — Deep Reference

Detailed patterns for complex TTA.dev primitive compositions.
The [SKILL.md](../SKILL.md) keeps the 1-turn quickstart; this file covers everything else.

---

## Sequential Data Passing

`SequentialPrimitive` (and `>>`) thread data through steps. Each step's **return value** becomes the next step's **input**. Use `ctx.state` when a downstream step needs data from a non-adjacent upstream step.

```python
import asyncio
from ttadev.primitives import (
    LambdaPrimitive, SequentialPrimitive, WorkflowContext,
)

# Step 1: parse raw text into a dict
parse = LambdaPrimitive(
    lambda raw, _: {"lines": raw.splitlines(), "count": raw.count("\n")}
)

# Step 2: filter short lines (receives parse's output dict)
filter_short = LambdaPrimitive(
    lambda d, _: {**d, "lines": [l for l in d["lines"] if len(l) > 3]}
)

# Step 3: join back to string
join = LambdaPrimitive(lambda d, _: "\n".join(d["lines"]))

pipeline = parse >> filter_short >> join
ctx      = WorkflowContext.root("text-pipeline")
result   = asyncio.run(pipeline.execute("hi\nhello\nworld\nok", ctx))
print(result)  # "hello\nworld"
```

---

## Parallel Fan-Out

`ParallelPrimitive` (and `|`) run two primitives **concurrently** with the same input. The result is `list[Output]` in left-to-right order.

```python
import asyncio
from ttadev.primitives import LambdaPrimitive, ParallelPrimitive, WorkflowContext

classify  = LambdaPrimitive(lambda text, _: "positive" if "good" in text else "neutral")
summarise = LambdaPrimitive(lambda text, _: text[:50])

fan_out = classify | summarise          # ParallelPrimitive under the hood
# or explicitly:
# fan_out = ParallelPrimitive([classify, summarise])

ctx     = WorkflowContext.root("fan-out")
results = asyncio.run(fan_out.execute("This is a good product.", ctx))
print(results)  # ["positive", "This is a good product."]
```

Combine fan-out with a merge step:

```python
merge = LambdaPrimitive(lambda results, _: {"label": results[0], "summary": results[1]})
full  = fan_out >> merge
out   = asyncio.run(full.execute("This is a good product.", ctx))
print(out)  # {"label": "positive", "summary": "This is a good product."}
```

---

## Circuit Breaker

Use `CircuitBreakerPrimitive` when you call an external service that may go down. The circuit opens after `failure_threshold` consecutive failures, immediately rejects calls for `recovery_timeout` seconds (OPEN), then allows one probe (HALF_OPEN), and closes again after `success_threshold` consecutive successes.

```python
import asyncio
from ttadev.primitives import LambdaPrimitive, WorkflowContext
from ttadev.primitives.recovery import (
    CircuitBreakerPrimitive,
    CircuitBreakerConfig,
    CircuitBreakerError,
)

async def call_api(payload: str, _ctx) -> str:
    # Replace with real HTTP call
    raise ConnectionError("service down")

api        = LambdaPrimitive(call_api)
cb_config  = CircuitBreakerConfig(
    failure_threshold=3,    # open after 3 consecutive failures
    recovery_timeout=30.0,  # wait 30 s before probing
    success_threshold=2,    # need 2 successes to close
)
protected  = CircuitBreakerPrimitive(api, config=cb_config)

ctx = WorkflowContext.root("cb-demo")
for i in range(5):
    try:
        result = asyncio.run(protected.execute(f"req-{i}", ctx))
    except CircuitBreakerError as e:
        print(f"Circuit open: {e}")
    except ConnectionError as e:
        print(f"Error (circuit counting): {e}")
```

### States

| State | Behaviour |
|-------|-----------|
| `CLOSED` | Normal — all calls pass through |
| `OPEN` | Fast-fail — raises `CircuitBreakerError` immediately |
| `HALF_OPEN` | One probe allowed; failure reopens; success counts toward close |

---

## Fallback Chain

`FallbackPrimitive` tries `primary`; on **any exception** it runs `fallback`. Compose multiple fallbacks by nesting:

```python
from ttadev.primitives import FallbackPrimitive, LambdaPrimitive, WorkflowContext
import asyncio

primary  = LambdaPrimitive(lambda x, _: (_ for _ in ()).throw(RuntimeError("primary down")))
backup   = LambdaPrimitive(lambda x, _: f"backup: {x}")
last_resort = LambdaPrimitive(lambda x, _: "default")

chain = FallbackPrimitive(
    FallbackPrimitive(primary, backup),
    last_resort,
)
ctx    = WorkflowContext.root("fallback-chain")
result = asyncio.run(chain.execute("payload", ctx))
print(result)  # "backup: payload"
```

---

## Retry + Timeout Composition

Wrap `TimeoutPrimitive` **outside** `RetryPrimitive` to cap total duration across all attempts, or **inside** to set a per-attempt limit:

```python
from ttadev.primitives import RetryPrimitive, TimeoutPrimitive, LambdaPrimitive

inner = LambdaPrimitive(some_slow_fn)

# Per-attempt timeout (2 s each), up to 3 attempts → max 6 s
per_attempt = RetryPrimitive(
    TimeoutPrimitive(inner, timeout_seconds=2.0),
    max_retries=3,
)

# Total budget timeout — fail entire retry stack after 5 s
total_budget = TimeoutPrimitive(
    RetryPrimitive(inner, max_retries=3),
    timeout_seconds=5.0,
)
```

---

## CachePrimitive with Custom Key

`CachePrimitive` memoises responses. Supply a `cache_key_fn(input, ctx) -> str` to control what is cached:

```python
import hashlib
from ttadev.primitives import CachePrimitive, LambdaPrimitive, WorkflowContext
import asyncio

slow_fn = LambdaPrimitive(lambda x, _: x.upper())  # imagine this is slow

def key_fn(data: str, ctx: WorkflowContext) -> str:
    return hashlib.md5(data.encode()).hexdigest()

cached = CachePrimitive(slow_fn, cache_key_fn=key_fn, ttl_seconds=60.0)

ctx = WorkflowContext.root("cache-demo")
r1  = asyncio.run(cached.execute("hello", ctx))   # computed
r2  = asyncio.run(cached.execute("hello", ctx))   # from cache
print(r1 == r2)  # True
```

---

## Implementing a Custom Primitive

Subclass `WorkflowPrimitive[Input, Output]` and implement `execute`:

```python
from ttadev.primitives import WorkflowPrimitive, WorkflowContext

class UpperCasePrimitive(WorkflowPrimitive[str, str]):
    """Converts input text to upper-case."""

    async def execute(self, input_data: str, context: WorkflowContext) -> str:
        context.state["last_input"] = input_data
        return input_data.upper()
```

Rules:
- Always `async def execute(self, input_data: T, context: WorkflowContext) -> U`
- Use `context.state` for cross-step communication
- Use `context.checkpoint(name)` for timing sub-steps
- Never store mutable state on `self` — primitives must be reentrant

---

## Full Complex Example

```python
import asyncio
from ttadev.primitives import (
    LambdaPrimitive, RetryPrimitive, TimeoutPrimitive,
    FallbackPrimitive, CachePrimitive, WorkflowContext,
)
from ttadev.primitives.recovery import CircuitBreakerPrimitive, CircuitBreakerConfig

# Primitives
validate = LambdaPrimitive(lambda x, _: x if x else ValueError("empty input"))
enrich   = LambdaPrimitive(lambda x, _: {"text": x, "length": len(x)})
notify   = LambdaPrimitive(lambda d, _: print(f"processed: {d}") or d)

# Compose
pipeline = (
    CachePrimitive(
        RetryPrimitive(
            TimeoutPrimitive(validate, timeout_seconds=2.0),
            max_retries=2,
        ),
        ttl_seconds=300,
    )
    >> enrich
    >> notify
)

ctx    = WorkflowContext.root("full-demo")
result = asyncio.run(pipeline.execute("hello", ctx))
print(result)  # {"text": "hello", "length": 5}
```
