---
description: 'Universal reliability patterns for any AI coding agent - makes your app scale-ready'
applyTo: '**/*.py'
agents: ['copilot', 'cline', 'augment', 'roo', 'cursor', 'aider']
---

# Universal Reliability Patterns

> These patterns work with **any** AI coding agent. Use them when your app needs to handle real traffic.

## When to Use This

You're vibing, building fast, shipping. That's great! But when:
- Your app starts getting users
- API calls sometimes fail
- You're worried about costs
- Things work locally but break in prod

...it's time for reliability patterns.

## Core Patterns

### 1. Retry with Backoff

**Problem:** External APIs fail randomly (rate limits, network blips, server errors)

**Pattern:**
```python
from tta_dev_primitives.recovery import RetryPrimitive

# Wrap any flaky operation
reliable_api = RetryPrimitive(
    primitive=your_api_call,
    max_retries=3,
    backoff_strategy="exponential",  # 1s, 2s, 4s
    jitter=True  # Prevents thundering herd
)
```

**When vibing:** `try/except` and hope for the best
**When scaling:** `RetryPrimitive` handles it automatically

### 2. Timeout Protection

**Problem:** API hangs forever, your whole app freezes

**Pattern:**
```python
from tta_dev_primitives.recovery import TimeoutPrimitive

# Never wait more than 10 seconds
protected_call = TimeoutPrimitive(
    primitive=potentially_slow_api,
    timeout_seconds=10.0,
    raise_on_timeout=True
)
```

**When vibing:** Infinite waits, frozen UIs
**When scaling:** Fail fast, show users something helpful

### 3. Caching (Save 💰)

**Problem:** Same API call over and over = expensive + slow

**Pattern:**
```python
from tta_dev_primitives.performance import CachePrimitive

# Don't call OpenAI for the same prompt twice
cached_llm = CachePrimitive(
    primitive=openai_call,
    ttl_seconds=3600,  # Cache for 1 hour
    max_size=1000      # Keep last 1000 results
)
```

**When vibing:** Each request = API call = $$$
**When scaling:** 40-60% cost reduction typical

### 4. Fallback Chain

**Problem:** Primary service goes down, your app dies

**Pattern:**
```python
from tta_dev_primitives.recovery import FallbackPrimitive

# If GPT-4 fails, try Claude, then Gemini
resilient_llm = FallbackPrimitive(
    primary=gpt4_call,
    fallbacks=[claude_call, gemini_call, local_llm]
)
```

**When vibing:** Single point of failure
**When scaling:** 99.9% uptime with graceful degradation

### 5. Circuit Breaker

**Problem:** Downstream service is failing, you keep hammering it

**Pattern:**
```python
from tta_dev_primitives.recovery import CircuitBreakerPrimitive

# Stop calling if it's broken
protected_service = CircuitBreakerPrimitive(
    primitive=external_service,
    failure_threshold=5,     # 5 failures = open circuit
    recovery_timeout=60,     # Wait 60s before retry
)
```

**When vibing:** Keep retrying dead services
**When scaling:** Fail fast, recover automatically

## Composition (The Magic)

Chain patterns together:

```python
# Production-ready API call in 4 lines
reliable_api = (
    CachePrimitive(ttl=300) >>          # Cache first
    TimeoutPrimitive(seconds=10) >>     # Then timeout
    RetryPrimitive(max_retries=3) >>    # Then retry
    your_api_call                       # Finally call
)
```

## Quick Reference

| Problem | Primitive | One-liner |
|---------|-----------|-----------|
| Random failures | `RetryPrimitive` | `RetryPrimitive(api, max_retries=3)` |
| Slow responses | `TimeoutPrimitive` | `TimeoutPrimitive(api, seconds=10)` |
| High costs | `CachePrimitive` | `CachePrimitive(api, ttl=3600)` |
| Service outages | `FallbackPrimitive` | `FallbackPrimitive(primary, [backup])` |
| Cascade failures | `CircuitBreakerPrimitive` | `CircuitBreakerPrimitive(api, threshold=5)` |

## Anti-Patterns (Don't Do This)

```python
# ❌ Manual retry loop
for i in range(3):
    try:
        result = api_call()
        break
    except:
        time.sleep(i)

# ❌ Bare except
try:
    result = api_call()
except:
    pass  # Silent failure = debugging nightmare

# ❌ No timeout
response = requests.get(url)  # Could hang forever

# ❌ No caching on repeated calls
for item in items:
    result = expensive_api(item)  # Same item = same cost
```

## When to Add These

1. **Day 1 (Vibing):** Skip it, just build
2. **First users:** Add `CachePrimitive` to save money
3. **Growing:** Add `RetryPrimitive` for reliability
4. **Going viral:** Full stack: Cache → Timeout → Retry → Fallback

---

**Remember:** You can always add reliability later. Don't let it slow down your vibing phase. TTA.dev is here when you need to scale.


---
**Logseq:** [[TTA.dev/Docs/Agents/Universal/Patterns/Reliability.instructions]]
