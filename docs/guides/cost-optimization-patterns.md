# Cost Optimization Patterns for LLM Applications

**Production-Ready Patterns Using TTA.dev Primitives**

**Last Updated:** October 30, 2025

---

## 📖 Table of Contents

- [Overview](#overview)
- [Pattern 1: Cache + Router](#pattern-1-cache--router)
- [Pattern 2: Fallback (Paid → Free)](#pattern-2-fallback-paid--free)
- [Pattern 3: Budget-Aware Routing](#pattern-3-budget-aware-routing)
- [Pattern 4: Retry with Cost Control](#pattern-4-retry-with-cost-control)
- [Pattern 5: Multi-Model Orchestration](#pattern-5-multi-model-orchestration)
- [Real-World Examples](#real-world-examples)
- [Monitoring & Alerting](#monitoring--alerting)
- [Troubleshooting](#troubleshooting)

---

## Overview

This guide provides production-ready patterns for optimizing LLM costs using TTA.dev primitives. Each pattern includes:

- **Cost savings estimate** (percentage reduction)
- **Production-ready code** (copy-paste ready)
- **Real-world use cases**
- **Monitoring recommendations**

### Expected Savings

| Pattern | Cost Reduction | Complexity | Best For |
|---------|---------------|------------|----------|
| Cache + Router | 30-50% | Low | High-volume, repetitive queries |
| Fallback (Paid → Free) | 20-40% | Medium | Non-critical workloads |
| Budget-Aware Routing | Variable | High | Cost-sensitive applications |
| Retry with Cost Control | 5-10% | Low | All applications |
| **Multi-Model Orchestration** | **80-95%** | **Medium** | **Orchestrator + executor pattern** |

**Combined Impact:** Using all 5 patterns together can reduce costs by **80-95%** while maintaining quality.

---

## Pattern 1: Cache + Router

**Cost Reduction:** 30-50%
**Complexity:** Low
**Best For:** Applications with repetitive queries or similar inputs

### How It Works

1. **Cache Layer:** Stores results of expensive LLM calls (30-40% cache hit rate typical)
2. **Router Layer:** Routes simple queries to cheap models, complex queries to expensive models

### Production Code

```python
from tta_dev_primitives.integrations import OpenAIPrimitive, OllamaPrimitive
from tta_dev_primitives.core.routing import RouterPrimitive
from tta_dev_primitives.performance.cache import CachePrimitive
from tta_dev_primitives.core.base import WorkflowContext

# Step 1: Define model primitives
gpt4o = OpenAIPrimitive(model="gpt-4o")  # $2.50/1M input, $10/1M output
gpt4o_mini = OpenAIPrimitive(model="gpt-4o-mini")  # $0.15/1M input, $0.60/1M output
llama_local = OllamaPrimitive(model="llama3.2:8b")  # Free, local

# Step 2: Add caching to expensive models
cached_gpt4o = CachePrimitive(
    primitive=gpt4o,
    cache_key_fn=lambda data, ctx: f"gpt4o:{data.get('prompt', '')[:100]}",
    ttl_seconds=3600,  # 1 hour cache
    max_size=1000
)

cached_gpt4o_mini = CachePrimitive(
    primitive=gpt4o_mini,
    cache_key_fn=lambda data, ctx: f"mini:{data.get('prompt', '')[:100]}",
    ttl_seconds=3600,
    max_size=2000
)

# Step 3: Route based on complexity
def route_by_complexity(data: dict, context: WorkflowContext) -> str:
    """Route to appropriate model based on query complexity."""
    prompt = data.get("prompt", "")

    # Simple heuristics (customize for your use case)
    if len(prompt) < 100:
        return "local"  # Free
    elif len(prompt) < 500:
        return "mini"  # Cheap
    else:
        return "premium"  # Expensive but high quality

router = RouterPrimitive(
    routes={
        "local": llama_local,  # Free
        "mini": cached_gpt4o_mini,  # Cheap + cached
        "premium": cached_gpt4o  # Expensive + cached
    },
    router_fn=route_by_complexity,
    default="mini"
)

# Step 4: Execute
context = WorkflowContext(workflow_id="cost-optimized-workflow")
result = await router.execute({"prompt": "Your query here"}, context)
```

### Cost Analysis

**Before optimization:**
- 10K requests/day
- All using GPT-4o
- Cost: $165/day = $4,950/month

**After optimization:**
- 30% cache hits (3K requests saved)
- 40% routed to GPT-4o-mini (4K requests)
- 20% routed to local (2K requests, free)
- 10% routed to GPT-4o (1K requests)

**New cost:**
- GPT-4o: 1K requests × $0.0165 = $16.50/day
- GPT-4o-mini: 4K requests × $0.00075 = $3.00/day
- Local: Free
- **Total: $19.50/day = $585/month**
- **Savings: $4,365/month (88% reduction!)**

### Monitoring

```python
from tta_dev_primitives.observability import get_enhanced_metrics_collector

collector = get_enhanced_metrics_collector()

# Track cache hit rate
cache_metrics = collector.get_all_metrics("cached_gpt4o")
print(f"Cache hit rate: {cache_metrics['cache_hit_rate']:.1%}")

# Track routing distribution
router_metrics = collector.get_all_metrics("router")
print(f"Route distribution: {router_metrics['route_counts']}")
```

---

## Pattern 2: Fallback (Paid → Free)

**Cost Reduction:** 20-40%
**Complexity:** Medium
**Best For:** Non-critical workloads, graceful degradation scenarios

### How It Works

1. **Primary:** Use paid model for best quality
2. **Fallback:** If primary fails or budget exceeded, use free model
3. **Result:** Maintain availability while controlling costs

### Production Code

```python
from tta_dev_primitives.integrations import OpenAIPrimitive, OllamaPrimitive
from tta_dev_primitives.recovery.fallback import FallbackPrimitive
from tta_dev_primitives.core.base import WorkflowContext

# Primary: Paid model (best quality)
primary = OpenAIPrimitive(model="gpt-4o")

# Fallback 1: Cheaper paid model
fallback1 = OpenAIPrimitive(model="gpt-4o-mini")

# Fallback 2: Free local model
fallback2 = OllamaPrimitive(model="llama3.2:8b")

# Create fallback chain
workflow = FallbackPrimitive(
    primary=primary,
    fallbacks=[fallback1, fallback2]
)

# Execute with automatic fallback
context = WorkflowContext(workflow_id="fallback-workflow")
try:
    result = await workflow.execute({"prompt": "Your query"}, context)
    print(f"Used model: {result.get('model_used')}")
except Exception as e:
    print(f"All models failed: {e}")
```

### Budget-Aware Fallback

```python
class BudgetAwareFallback(FallbackPrimitive):
    """Fallback that considers budget constraints."""

    def __init__(self, primary, fallbacks, daily_budget: float = 100.0):
        super().__init__(primary, fallbacks)
        self.daily_budget = daily_budget
        self.daily_spend = 0.0

    async def execute(self, input_data, context):
        # Check budget before using paid model
        if self.daily_spend >= self.daily_budget:
            # Budget exceeded, skip to free fallback
            context.metadata["budget_exceeded"] = True
            return await self.fallbacks[-1].execute(input_data, context)

        # Normal fallback logic
        result = await super().execute(input_data, context)

        # Track spending
        cost = result.get("cost", 0.0)
        self.daily_spend += cost

        return result

# Usage
workflow = BudgetAwareFallback(
    primary=OpenAIPrimitive(model="gpt-4o"),
    fallbacks=[
        OpenAIPrimitive(model="gpt-4o-mini"),
        OllamaPrimitive(model="llama3.2:8b")
    ],
    daily_budget=50.0  # $50/day limit
)
```

### Cost Analysis

**Scenario:** 10K requests/day, 20% failure rate on primary

**Before:**
- All requests to GPT-4o
- Cost: $165/day

**After:**
- 80% succeed on GPT-4o: 8K × $0.0165 = $132/day
- 15% fallback to GPT-4o-mini: 1.5K × $0.00075 = $1.13/day
- 5% fallback to local: Free
- **Total: $133.13/day = $3,994/month**
- **Savings: $956/month (19% reduction)**

---

## Pattern 3: Budget-Aware Routing

**Cost Reduction:** Variable (depends on budget)
**Complexity:** High
**Best For:** Cost-sensitive applications with strict budget constraints

### How It Works

1. **Track spending** in real-time
2. **Route to cheaper models** as budget is consumed
3. **Switch to free models** when budget exceeded

### Production Code

```python
from tta_dev_primitives.core.routing import RouterPrimitive
from tta_dev_primitives.core.base import WorkflowContext
from tta_dev_primitives.integrations import OpenAIPrimitive, OllamaPrimitive
from datetime import datetime, timedelta

class BudgetTracker:
    """Track daily spending and enforce budget limits."""

    def __init__(self, daily_budget: float):
        self.daily_budget = daily_budget
        self.daily_spend = 0.0
        self.last_reset = datetime.now()

    def reset_if_new_day(self):
        """Reset spending counter at midnight."""
        now = datetime.now()
        if now.date() > self.last_reset.date():
            self.daily_spend = 0.0
            self.last_reset = now

    def record_cost(self, cost: float):
        """Record a cost."""
        self.reset_if_new_day()
        self.daily_spend += cost

    def get_remaining_budget(self) -> float:
        """Get remaining budget for today."""
        self.reset_if_new_day()
        return max(0.0, self.daily_budget - self.daily_spend)

    def get_budget_utilization(self) -> float:
        """Get budget utilization (0.0 to 1.0)."""
        self.reset_if_new_day()
        return min(1.0, self.daily_spend / self.daily_budget)

# Initialize budget tracker
budget_tracker = BudgetTracker(daily_budget=100.0)  # $100/day

# Define models
gpt4o = OpenAIPrimitive(model="gpt-4o")
gpt4o_mini = OpenAIPrimitive(model="gpt-4o-mini")
llama_local = OllamaPrimitive(model="llama3.2:8b")

def budget_aware_router(data: dict, context: WorkflowContext) -> str:
    """Route based on remaining budget."""
    utilization = budget_tracker.get_budget_utilization()

    if utilization < 0.5:
        # <50% budget used: Use premium model
        return "premium"
    elif utilization < 0.8:
        # 50-80% budget used: Use mid-tier model
        return "mid"
    else:
        # >80% budget used: Use free model
        return "free"

router = RouterPrimitive(
    routes={
        "premium": gpt4o,
        "mid": gpt4o_mini,
        "free": llama_local
    },
    router_fn=budget_aware_router,
    default="free"
)

# Execute and track costs
context = WorkflowContext(workflow_id="budget-aware")
result = await router.execute({"prompt": "Your query"}, context)

# Record cost
cost = result.get("cost", 0.0)
budget_tracker.record_cost(cost)

print(f"Budget utilization: {budget_tracker.get_budget_utilization():.1%}")
print(f"Remaining budget: ${budget_tracker.get_remaining_budget():.2f}")
```

### Monitoring Dashboard

```python
def print_budget_dashboard(tracker: BudgetTracker):
    """Print budget status dashboard."""
    utilization = tracker.get_budget_utilization()
    remaining = tracker.get_remaining_budget()

    print("=" * 50)
    print("BUDGET DASHBOARD")
    print("=" * 50)
    print(f"Daily Budget:     ${tracker.daily_budget:.2f}")
    print(f"Spent Today:      ${tracker.daily_spend:.2f}")
    print(f"Remaining:        ${remaining:.2f}")
    print(f"Utilization:      {utilization:.1%}")
    print("=" * 50)

    if utilization > 0.9:
        print("⚠️  WARNING: Budget almost exhausted!")
    elif utilization > 0.7:
        print("⚠️  CAUTION: Budget 70% consumed")
    else:
        print("✅ Budget healthy")
```

---

## Pattern 4: Retry with Cost Control

**Cost Reduction:** 5-10%
**Complexity:** Low
**Best For:** All applications (prevents wasted API calls)

### How It Works

1. **Exponential backoff:** Avoid hammering failed endpoints
2. **Max retries:** Limit total attempts to prevent runaway costs
3. **Smart retry logic:** Only retry transient failures (not invalid inputs)

### Production Code

```python
from tta_dev_primitives.recovery.retry import RetryPrimitive
from tta_dev_primitives.integrations import OpenAIPrimitive

# Create retry wrapper
workflow = RetryPrimitive(
    primitive=OpenAIPrimitive(model="gpt-4o"),
    max_retries=3,
    backoff_strategy="exponential",
    initial_delay=1.0,  # Start with 1s delay
    max_delay=30.0,  # Cap at 30s
    retry_on_exceptions=(TimeoutError, ConnectionError)  # Only retry transient errors
)

# Execute with automatic retry
context = WorkflowContext(workflow_id="retry-workflow")
result = await workflow.execute({"prompt": "Your query"}, context)
```

### Cost Analysis

**Before:**
- 10K requests/day
- 10% failure rate
- No retry → 1K failed requests wasted
- Cost: $165/day + $16.50 wasted = $181.50/day

**After:**
- 10K requests/day
- 10% initial failure rate
- 80% succeed on retry (800 recovered)
- Only 200 truly failed
- Cost: $165/day + $1.32 retry cost = $166.32/day
- **Savings: $15.18/day = $455/month (8% reduction)**

---

## Pattern 5: Multi-Model Orchestration

**Cost Reduction:** 80-95%
**Complexity:** Medium
**Best For:** Applications where an orchestrator can delegate tasks to specialized models

### How It Works

Multi-model orchestration uses a high-quality orchestrator model (e.g., Claude Sonnet 4.5) to analyze tasks and delegate execution to appropriate free flagship models. The orchestrator handles planning and validation (small token usage), while free models handle bulk execution (large token usage).

**Key Insight:** Most AI applications spend 80%+ of tokens on execution, not planning. By delegating execution to free models, you can achieve 80-95% cost reduction while maintaining quality.

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Orchestrator Model                        │
│              (Claude Sonnet 4.5 - Paid)                     │
│                                                              │
│  1. Analyze task requirements                               │
│  2. Classify complexity                                     │
│  3. Select best executor model                              │
│  4. Validate output quality                                 │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ├─────────────┬─────────────┬──────────────┐
                   ▼             ▼             ▼              ▼
         ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
         │  Gemini Pro │ │ DeepSeek R1 │ │  Groq Llama │ │ HuggingFace │
         │   (FREE)    │ │   (FREE)    │ │   (FREE)    │ │   (FREE)    │
         │             │ │             │ │             │ │             │
         │ General     │ │ Complex     │ │ Ultra-fast  │ │ Model       │
         │ Purpose     │ │ Reasoning   │ │ Inference   │ │ Variety     │
         └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘
```

### Implementation

**Step 1: Create Task Classifier**

```python
from tta_dev_primitives.orchestration import TaskClassifierPrimitive
from tta_dev_primitives.core.base import WorkflowContext

# Create classifier
classifier = TaskClassifierPrimitive(prefer_free=True)

# Classify task
context = WorkflowContext(workflow_id="classify-demo")
request = TaskClassifierRequest(
    task_description="Summarize this article in 3 bullet points",
    user_preferences={"prefer_free": True}
)
classification = await classifier.execute(request, context)

print(f"Recommended: {classification.recommended_model}")
print(f"Reasoning: {classification.reasoning}")
print(f"Cost: ${classification.estimated_cost}")
```

**Step 2: Create Delegation Primitive**

```python
from tta_dev_primitives.orchestration import DelegationPrimitive
from tta_dev_primitives.integrations import (
    GoogleAIStudioPrimitive,
    GroqPrimitive,
    OpenRouterPrimitive
)

# Create delegation primitive with executors
delegation = DelegationPrimitive(
    executor_primitives={
        "gemini-2.5-pro": GoogleAIStudioPrimitive(model="gemini-2.5-pro"),
        "llama-3.3-70b-versatile": GroqPrimitive(model="llama-3.3-70b-versatile"),
        "deepseek/deepseek-r1:free": OpenRouterPrimitive(model="deepseek/deepseek-r1:free")
    }
)

# Delegate task
request = DelegationRequest(
    task_description="Summarize article",
    executor_model="gemini-2.5-pro",
    messages=[{"role": "user", "content": "Summarize: [article text]"}]
)
response = await delegation.execute(request, context)

print(f"Executor: {response.executor_model}")
print(f"Cost: ${response.cost}")  # $0.00 (FREE!)
```

**Step 3: Create Multi-Model Workflow**

```python
from tta_dev_primitives.orchestration import MultiModelWorkflow

# Create workflow with automatic routing
workflow = MultiModelWorkflow(
    executor_primitives={
        "gemini-2.5-pro": GoogleAIStudioPrimitive(),
        "llama-3.3-70b-versatile": GroqPrimitive(),
        "deepseek/deepseek-r1:free": OpenRouterPrimitive()
    },
    prefer_free=True
)

# Execute task (automatic classification + delegation)
request = MultiModelRequest(
    task_description="Analyze renewable energy benefits",
    messages=[{"role": "user", "content": "Analyze: [content]"}],
    user_preferences={"prefer_free": True},
    validate_output=True
)
response = await workflow.execute(request, context)

print(f"Executor: {response.executor_model}")
print(f"Complexity: {response.classification['complexity']}")
print(f"Cost: ${response.cost}")
print(f"Validation: {'Passed' if response.validation_passed else 'Failed'}")
```

### Orchestration Patterns

#### Pattern A: Claude Plans → Free Models Execute

**Use Case:** Research, analysis, content generation

```python
# Claude's role: Analyze requirements and create execution plan
claude_plan = """
Task: Research renewable energy from 3 perspectives
Sub-tasks:
1. Environmental benefits → Gemini Pro
2. Economic impact → DeepSeek R1
3. Technical challenges → Groq (Llama 3.3 70B)
"""

# Execute sub-tasks in parallel with free models
tasks = [
    DelegationRequest(
        task_description="Environmental benefits",
        executor_model="gemini-2.5-pro",
        messages=[{"role": "user", "content": "Explain environmental benefits..."}]
    ),
    DelegationRequest(
        task_description="Economic impact",
        executor_model="deepseek/deepseek-r1:free",
        messages=[{"role": "user", "content": "Analyze economic impact..."}]
    ),
    DelegationRequest(
        task_description="Technical challenges",
        executor_model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": "Describe technical challenges..."}]
    )
]

# Execute in parallel
responses = await asyncio.gather(*[delegation.execute(task, context) for task in tasks])

# Claude's role: Aggregate and validate results
# Total cost: ~$0.01 (Claude planning) + $0.00 (free execution) = $0.01
# vs. $0.50 (Claude for everything) = 98% savings
```

#### Pattern B: Claude Validates → Free Model Outputs

**Use Case:** Quality assurance, fact-checking

```python
# Free model executes
gemini_response = await delegation.execute(
    DelegationRequest(
        task_description="Generate summary",
        executor_model="gemini-2.5-pro",
        messages=[{"role": "user", "content": "Summarize: [content]"}]
    ),
    context
)

# Claude validates (small token usage)
validation_prompt = f"""
Validate this summary for accuracy and completeness:
{gemini_response.content}

Original content: [content]
"""

# Cost: $0.00 (Gemini) + $0.005 (Claude validation) = $0.005
# vs. $0.05 (Claude for everything) = 90% savings
```

### Cost Analysis

**Scenario:** AI content generation tool (10K requests/day)

| Approach | Model | Tokens/Request | Cost/1M Tokens | Daily Cost | Monthly Cost |
|----------|-------|----------------|----------------|------------|--------------|
| **All Claude** | Claude Sonnet 4.5 | 2,000 | $3.00 | $60.00 | $1,800 |
| **All Gemini** | Gemini Pro (free) | 2,000 | $0.00 | $0.00 | $0.00 |
| **Orchestration** | Claude (plan) + Gemini (execute) | 200 + 1,800 | $3.00 + $0.00 | $6.00 | $180 |

**Cost Savings:**
- Orchestration vs. All Claude: **90% reduction** ($1,800 → $180/month)
- Orchestration vs. All Gemini: **Quality maintained** (Claude planning ensures quality)

### When to Use Multi-Model Orchestration

✅ **Use When:**
- Tasks can be decomposed into planning + execution
- Execution is the bulk of token usage (80%+)
- Quality requirements vary by sub-task
- You have access to free flagship models

❌ **Don't Use When:**
- Tasks require single-model consistency
- Planning overhead exceeds execution cost
- Real-time latency is critical (orchestration adds ~100ms)
- Tasks are too simple to benefit from orchestration

### Monitoring

Track these metrics for orchestration workflows:

```python
# Add to observability
context.data["orchestration_metrics"] = {
    "orchestrator_tokens": 200,
    "executor_tokens": 1800,
    "orchestrator_cost": 0.006,
    "executor_cost": 0.0,
    "total_cost": 0.006,
    "cost_savings_vs_all_paid": 0.90,  # 90% savings
    "executor_model": "gemini-2.5-pro",
    "classification": "moderate"
}
```

### Troubleshooting

**Issue: Orchestrator overhead too high**
- Solution: Batch multiple tasks in single orchestration call
- Example: Plan 10 tasks at once instead of 1 at a time

**Issue: Free model quality insufficient**
- Solution: Use fallback chain with paid model as last resort
- Example: Gemini → DeepSeek → Claude (if both free models fail)

**Issue: Latency increased**
- Solution: Use parallel execution for independent sub-tasks
- Example: Execute 3 sub-tasks in parallel instead of sequential

---

## Real-World Examples

### Example 1: AI Code Assistant (High Volume)

**Scenario:** Code completion tool with 50K requests/day

**Requirements:**
- Low latency (<500ms)
- High quality for complex code
- Budget: $200/month

**Solution:**

```python
from tta_dev_primitives.integrations import OpenAIPrimitive, OllamaPrimitive
from tta_dev_primitives.core.routing import RouterPrimitive
from tta_dev_primitives.performance.cache import CachePrimitive
from tta_dev_primitives.recovery.retry import RetryPrimitive

# Step 1: Cache layer (40% hit rate expected)
cached_gpt4o_mini = CachePrimitive(
    primitive=OpenAIPrimitive(model="gpt-4o-mini"),
    cache_key_fn=lambda data, ctx: f"code:{data.get('code_context', '')[:200]}",
    ttl_seconds=1800,  # 30 min cache (code changes frequently)
    max_size=5000
)

# Step 2: Local model for simple completions
llama_code = OllamaPrimitive(model="codellama:7b")

# Step 3: Router (route simple to local, complex to cloud)
def route_code_completion(data: dict, context):
    code_length = len(data.get("code_context", ""))
    complexity = data.get("complexity", "simple")

    if complexity == "simple" or code_length < 100:
        return "local"  # Free, fast
    else:
        return "cloud"  # Cached, high quality

router = RouterPrimitive(
    routes={
        "local": llama_code,
        "cloud": cached_gpt4o_mini
    },
    router_fn=route_code_completion,
    default="local"
)

# Step 4: Retry wrapper (prevent wasted calls)
workflow = RetryPrimitive(
    primitive=router,
    max_retries=2,
    backoff_strategy="exponential"
)
```

**Results:**
- 60% routed to local (30K requests, free)
- 40% routed to cloud (20K requests)
  - 40% cache hits (8K requests saved)
  - 12K actual API calls
- **Cost:** 12K × $0.00075 = $9/month
- **Savings:** $191/month vs budget (95% under budget!)

---

### Example 2: Customer Support Chatbot

**Scenario:** Customer support with 10K conversations/day

**Requirements:**
- High quality responses
- 24/7 availability
- Budget: $500/month

**Solution:**

```python
from tta_dev_primitives.integrations import OpenAIPrimitive, AnthropicPrimitive
from tta_dev_primitives.recovery.fallback import FallbackPrimitive
from tta_dev_primitives.performance.cache import CachePrimitive

# Primary: Claude Sonnet (best for customer support)
primary = CachePrimitive(
    primitive=AnthropicPrimitive(model="claude-3-5-sonnet-20241022"),
    cache_key_fn=lambda data, ctx: f"support:{data.get('question', '')[:100]}",
    ttl_seconds=7200,  # 2 hour cache (FAQs repeat)
    max_size=2000
)

# Fallback: GPT-4o-mini (cheaper, still good quality)
fallback = OpenAIPrimitive(model="gpt-4o-mini")

workflow = FallbackPrimitive(
    primary=primary,
    fallbacks=[fallback]
)
```

**Results:**
- 30% cache hits (3K requests saved)
- 7K requests to Claude Sonnet: 7K × $0.018 = $126/day
- 0 fallbacks (Claude very reliable)
- **Cost:** $126/day = $3,780/month
- **Over budget!** Need to optimize further...

**Optimization:**

```python
# Add budget-aware routing
def support_router(data: dict, context):
    # Route simple questions to GPT-4o-mini
    question = data.get("question", "").lower()
    simple_keywords = ["hours", "location", "contact", "price"]

    if any(kw in question for kw in simple_keywords):
        return "simple"  # Use cheaper model
    else:
        return "complex"  # Use premium model

router = RouterPrimitive(
    routes={
        "simple": OpenAIPrimitive(model="gpt-4o-mini"),
        "complex": primary  # Cached Claude
    },
    router_fn=support_router,
    default="simple"
)
```

**New Results:**
- 50% routed to GPT-4o-mini: 5K × $0.00075 = $3.75/day
- 50% routed to Claude (30% cache hits): 3.5K × $0.018 = $63/day
- **Cost:** $66.75/day = $2,002/month
- **Savings:** $1,778/month (47% reduction, now under budget!)

---

### Example 3: Gemini Pro → Flash Downgrade Issue

**Problem:** User reports Gemini unexpectedly downgrading from Pro to Flash before hitting rate limits

**Root Cause:** Google's API may downgrade based on:
1. **Context window usage** (not just request count)
2. **Token throughput** (tokens/minute, not requests/minute)
3. **Concurrent requests** (too many simultaneous requests)

**Solution:**

```python
from tta_dev_primitives.integrations import GoogleGeminiPrimitive
from tta_dev_primitives.recovery.timeout import TimeoutPrimitive
from tta_dev_primitives.recovery.retry import RetryPrimitive

# Step 1: Add timeout to prevent long-running requests
gemini_pro = TimeoutPrimitive(
    primitive=GoogleGeminiPrimitive(model="gemini-2.5-pro"),
    timeout_seconds=30.0  # Prevent runaway context usage
)

# Step 2: Add retry with backoff (avoid concurrent request spikes)
workflow = RetryPrimitive(
    primitive=gemini_pro,
    max_retries=3,
    backoff_strategy="exponential",
    initial_delay=2.0  # Spread out requests
)

# Step 3: Monitor token usage
from tta_dev_primitives.observability import get_enhanced_metrics_collector

collector = get_enhanced_metrics_collector()

async def execute_with_monitoring(prompt: str):
    context = WorkflowContext(workflow_id="gemini-monitor")
    result = await workflow.execute({"prompt": prompt}, context)

    # Check token usage
    metrics = collector.get_all_metrics("gemini_pro")
    tokens_used = metrics.get("total_tokens", 0)

    if tokens_used > 1_000_000:  # Approaching limit
        print("⚠️  WARNING: High token usage, consider switching to Flash")

    return result
```

**Monitoring Script:**

```python
import asyncio
from datetime import datetime, timedelta

class GeminiUsageTracker:
    """Track Gemini usage to prevent unexpected downgrades."""

    def __init__(self):
        self.hourly_tokens = 0
        self.hourly_requests = 0
        self.last_reset = datetime.now()

    def reset_if_new_hour(self):
        now = datetime.now()
        if now - self.last_reset > timedelta(hours=1):
            self.hourly_tokens = 0
            self.hourly_requests = 0
            self.last_reset = now

    def record_request(self, tokens: int):
        self.reset_if_new_hour()
        self.hourly_tokens += tokens
        self.hourly_requests += 1

    def should_throttle(self) -> bool:
        """Check if we should throttle requests."""
        self.reset_if_new_hour()

        # Gemini Pro limits (approximate)
        MAX_TOKENS_PER_HOUR = 500_000
        MAX_REQUESTS_PER_HOUR = 1000

        if self.hourly_tokens > MAX_TOKENS_PER_HOUR * 0.8:
            return True  # 80% of token limit
        if self.hourly_requests > MAX_REQUESTS_PER_HOUR * 0.8:
            return True  # 80% of request limit

        return False

# Usage
tracker = GeminiUsageTracker()

async def safe_gemini_call(prompt: str):
    if tracker.should_throttle():
        print("⚠️  Throttling: Switching to Gemini Flash")
        # Use Flash instead
        flash = GoogleGeminiPrimitive(model="gemini-2.5-flash")
        result = await flash.execute({"prompt": prompt}, context)
    else:
        # Use Pro
        result = await workflow.execute({"prompt": prompt}, context)
        tracker.record_request(result.get("tokens_used", 0))

    return result
```

---

## Monitoring & Alerting

### Essential Metrics to Track

```python
from tta_dev_primitives.observability import get_enhanced_metrics_collector

collector = get_enhanced_metrics_collector()

# 1. Cost metrics
cost_metrics = collector.get_all_metrics("llm_workflow")
print(f"Total cost: ${cost_metrics['cost']['total_cost']:.2f}")
print(f"Cost savings: ${cost_metrics['cost']['total_savings']:.2f}")

# 2. Cache hit rate
cache_metrics = collector.get_all_metrics("cached_llm")
print(f"Cache hit rate: {cache_metrics['cache_hit_rate']:.1%}")

# 3. Route distribution
router_metrics = collector.get_all_metrics("router")
print(f"Route counts: {router_metrics['route_counts']}")

# 4. Error rate
error_rate = 1 - (cost_metrics['successful_requests'] / cost_metrics['total_requests'])
print(f"Error rate: {error_rate:.1%}")
```

### Alerting Thresholds

```python
def check_alerts(metrics: dict):
    """Check metrics and trigger alerts."""

    # Alert 1: High cost
    if metrics['cost']['total_cost'] > 100.0:  # $100/day
        send_alert("💰 COST ALERT: Daily spend exceeds $100")

    # Alert 2: Low cache hit rate
    if metrics.get('cache_hit_rate', 0) < 0.2:  # <20%
        send_alert("📊 CACHE ALERT: Hit rate below 20%")

    # Alert 3: High error rate
    error_rate = 1 - (metrics['successful_requests'] / metrics['total_requests'])
    if error_rate > 0.1:  # >10%
        send_alert("⚠️  ERROR ALERT: Error rate above 10%")

    # Alert 4: Budget exceeded
    if metrics['cost']['total_cost'] > metrics.get('daily_budget', float('inf')):
        send_alert("🚨 BUDGET ALERT: Daily budget exceeded!")

def send_alert(message: str):
    """Send alert (implement your notification method)."""
    print(f"ALERT: {message}")
    # TODO: Send to Slack, email, PagerDuty, etc.
```

---

## Troubleshooting

### Issue 1: Cache Hit Rate Too Low

**Symptoms:** Cache hit rate <20%, not seeing expected cost savings

**Causes:**
1. Cache key function too specific (includes timestamps, random IDs)
2. TTL too short (cache expires before reuse)
3. Max size too small (cache evicting entries too quickly)

**Solutions:**

```python
# ❌ Bad: Cache key includes timestamp
cache_key_fn=lambda data, ctx: f"{data['prompt']}:{datetime.now()}"

# ✅ Good: Cache key only includes stable data
cache_key_fn=lambda data, ctx: f"{data['prompt'][:200]}"

# ❌ Bad: TTL too short
ttl_seconds=60  # 1 minute

# ✅ Good: TTL matches usage pattern
ttl_seconds=3600  # 1 hour for typical queries

# ❌ Bad: Max size too small
max_size=10

# ✅ Good: Max size based on memory budget
max_size=1000  # ~10MB for typical LLM responses
```

---

### Issue 2: Unexpected Model Downgrades (Gemini Pro → Flash)

**Symptoms:** Gemini Pro requests return Flash-quality responses

**Causes:**
1. Token throughput limit exceeded (not request count)
2. Concurrent request limit exceeded
3. Context window usage too high

**Solutions:**

```python
# Solution 1: Add request throttling
import asyncio

class RequestThrottler:
    def __init__(self, max_concurrent: int = 5):
        self.semaphore = asyncio.Semaphore(max_concurrent)

    async def execute(self, primitive, data, context):
        async with self.semaphore:
            return await primitive.execute(data, context)

throttler = RequestThrottler(max_concurrent=5)

# Solution 2: Monitor token usage
tracker = GeminiUsageTracker()  # See Example 3 above

# Solution 3: Explicit model selection
gemini_pro = GoogleGeminiPrimitive(
    model="gemini-2.5-pro",
    # Explicitly set model in every request
    model_kwargs={"model": "gemini-2.5-pro"}
)
```

---

### Issue 3: Budget Exceeded Unexpectedly

**Symptoms:** Costs higher than expected, budget alerts firing

**Causes:**
1. No retry limits (infinite retries on failures)
2. No budget tracking (no visibility into spending)
3. Routing logic not working (all requests to expensive model)

**Solutions:**

```python
# Solution 1: Add retry limits
workflow = RetryPrimitive(
    primitive=expensive_llm,
    max_retries=3,  # Limit retries
    backoff_strategy="exponential"
)

# Solution 2: Add budget tracking
budget_tracker = BudgetTracker(daily_budget=100.0)

# Solution 3: Test routing logic
def test_routing():
    test_cases = [
        ({"prompt": "short"}, "local"),
        ({"prompt": "a" * 500}, "mini"),
        ({"prompt": "a" * 1000}, "premium")
    ]

    for data, expected_route in test_cases:
        actual_route = route_by_complexity(data, WorkflowContext())
        assert actual_route == expected_route, f"Expected {expected_route}, got {actual_route}"

    print("✅ Routing logic tests passed")

test_routing()
```

---

## 📚 Related Documentation

- **LLM Cost Guide:** [llm-cost-guide.md](llm-cost-guide.md) - Free vs paid model comparison
- **LLM Selection Guide:** [llm-selection-guide.md](llm-selection-guide.md) - Decision matrix for choosing LLMs
- **PRIMITIVES_CATALOG.md:** [../../PRIMITIVES_CATALOG.md](../../PRIMITIVES_CATALOG.md) - Complete primitive reference

### Implementation References

- **CachePrimitive:** [`platform/primitives/src/tta_dev_primitives/performance/cache.py`](../../platform/primitives/src/tta_dev_primitives/performance/cache.py)
- **RouterPrimitive:** [`platform/primitives/src/tta_dev_primitives/core/routing.py`](../../platform/primitives/src/tta_dev_primitives/core/routing.py)
- **FallbackPrimitive:** [`platform/primitives/src/tta_dev_primitives/recovery/fallback.py`](../../platform/primitives/src/tta_dev_primitives/recovery/fallback.py)
- **RetryPrimitive:** [`platform/primitives/src/tta_dev_primitives/recovery/retry.py`](../../platform/primitives/src/tta_dev_primitives/recovery/retry.py)

---

**Last Updated:** October 30, 2025
**For:** Production AI Applications
**Maintained by:** TTA.dev Team

**💡 Pro Tip:** Combine all 4 patterns for maximum cost savings (50-70% reduction typical)
