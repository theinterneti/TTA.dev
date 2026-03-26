---
mode: 'agent'
tools: ['codebase', 'terminal']
description: 'Make your vibed app scale-ready before it goes viral'
agents: ['copilot', 'cline', 'augment', 'roo', 'cursor', 'aider']
---

# Make It Scale-Ready

You've vibed an app into existence. It works! Now you want to make sure it won't fall over when people start using it.

## Your Task

Analyze the codebase and add TTA.dev primitives to make it reliable and scale-ready.

## Priority Order

1. **Find the expensive stuff** - API calls, database queries, external services
2. **Add caching** - Don't pay twice for the same result
3. **Add timeouts** - Don't let anything hang forever
4. **Add retries** - Handle random failures gracefully
5. **Add fallbacks** - Have a backup plan

## Analysis Steps

### 1. Identify Risky Code

Look for patterns like:
```python
# 🎯 External API calls (expensive, can fail)
response = requests.get(external_url)
result = openai.chat.completions.create(...)

# 🎯 No error handling
data = api.fetch()  # What if it fails?

# 🎯 No timeout
response = slow_service.call()  # Could hang forever

# 🎯 Repeated expensive calls
for item in items:
    result = expensive_api(item)  # Same item called multiple times?
```

### 2. Prioritize by Impact

| Risk Level | Pattern | Action |
|------------|---------|--------|
| 🔴 Critical | OpenAI/Claude calls without caching | Add `CachePrimitive` |
| 🔴 Critical | API calls without timeout | Add `TimeoutPrimitive` |
| 🟡 High | External APIs without retry | Add `RetryPrimitive` |
| 🟡 High | Single provider dependency | Add `FallbackPrimitive` |
| 🟢 Medium | Database queries | Consider caching |

### 3. Apply Primitives

For each risky code path:

```python
from tta_dev_primitives.recovery import RetryPrimitive, TimeoutPrimitive
from tta_dev_primitives.performance import CachePrimitive

# Before: Risky
result = openai.chat.completions.create(...)

# After: Scale-ready
llm_workflow = (
    CachePrimitive(ttl=3600) >>      # Cache identical prompts
    TimeoutPrimitive(seconds=30) >>   # Don't hang
    RetryPrimitive(max_retries=3) >>  # Handle API blips
    openai_call_primitive
)
result = await llm_workflow.execute(data, context)
```

## Output Format

```markdown
## Scale-Ready Analysis

### 🔍 Identified Risks

| File | Line | Risk | Severity |
|------|------|------|----------|
| api.py | 42 | OpenAI call without caching | 🔴 Critical |
| fetch.py | 15 | No timeout on external API | 🔴 Critical |
| utils.py | 88 | No retry on flaky endpoint | 🟡 High |

### 💡 Recommended Changes

#### 1. api.py - Add caching to LLM calls

**Before:**
[current code]

**After:**
[improved code with primitives]

**Impact:** ~50% cost reduction, faster responses

#### 2. fetch.py - Add timeout protection

...

### 📊 Expected Improvements

- **Cost:** -40-60% (caching)
- **Reliability:** 99.9% uptime (retries + fallbacks)
- **Latency:** -30% average (caching)

### ⚡ Quick Wins (Do These First)

1. Add `CachePrimitive` to OpenAI calls
2. Add `TimeoutPrimitive` to all external APIs
3. Add `RetryPrimitive` to payment processing
```

## Remember

- Don't over-engineer during vibing phase
- Add primitives incrementally as you scale
- Start with caching (saves money!)
- Observability can wait until you have users

## Related

- [Reliability Patterns](../universal/patterns/reliability.instructions.md)
- [Observability Patterns](../universal/patterns/observability.instructions.md)
- [PRIMITIVES_CATALOG.md](../../PRIMITIVES_CATALOG.md)
