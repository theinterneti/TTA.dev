# How-To: Performance Tuning

type:: [[How-To]]
category:: [[Performance]]
difficulty:: [[Advanced]]
estimated-time:: 45 minutes
target-audience:: [[Performance Engineers]], [[Backend Developers]], [[DevOps]]
primitives-used:: [[ParallelPrimitive]], [[CachePrimitive]], [[RouterPrimitive]]

---

## Overview

- id:: performance-tuning-overview
  **Performance tuning** AI workflows involves profiling to identify bottlenecks, then applying optimization strategies like parallelization, caching, and intelligent routing. This guide shows you how to systematically analyze and optimize TTA.dev workflows to achieve 10-100x performance improvements.

---

## Prerequisites

{{embed ((prerequisites-full))}}

**Should have read:**
- [[TTA.dev/Guides/Workflow Composition]] - Composition patterns
- [[TTA.dev/Guides/Cost Optimization]] - Caching and routing
- [[TTA.dev/Primitives/ParallelPrimitive]] - Parallel execution
- [[TTA.dev/Primitives/CachePrimitive]] - Caching

**Should understand:**
- Async/await and concurrency
- Profiling and benchmarking
- Big-O notation basics

---

## Performance Optimization Workflow

### The Systematic Approach

```
1. Measure Baseline
   ↓
2. Profile to Find Bottlenecks
   ↓
3. Apply Targeted Optimizations
   ↓
4. Measure Again
   ↓
5. Repeat Until Goals Met
```

**Rule:** Never optimize without measuring first!

---

## Step 1: Measure Baseline Performance

### Add Performance Instrumentation

```python
from tta_dev_primitives import WorkflowPrimitive, WorkflowContext
import time
from dataclasses import dataclass

@dataclass
class PerformanceMetrics:
    """Performance metrics for a workflow."""
    total_time_ms: float
    steps: dict[str, float]  # step_name -> duration_ms
    cache_hits: int = 0
    cache_misses: int = 0
    api_calls: int = 0

class PerformanceTracker:
    """Track workflow performance."""

    def __init__(self):
        self.start_time = None
        self.step_times: dict[str, float] = {}
        self.current_step_start = None

    def start(self):
        """Start tracking."""
        self.start_time = time.time()

    def start_step(self, step_name: str):
        """Start tracking a step."""
        self.current_step_start = time.time()

    def end_step(self, step_name: str):
        """End tracking a step."""
        if self.current_step_start:
            duration = (time.time() - self.current_step_start) * 1000
            self.step_times[step_name] = duration

    def get_metrics(self) -> PerformanceMetrics:
        """Get performance metrics."""
        total_time = (time.time() - self.start_time) * 1000
        return PerformanceMetrics(
            total_time_ms=total_time,
            steps=self.step_times
        )

# Usage
async def benchmark_workflow():
    """Benchmark workflow performance."""
    tracker = PerformanceTracker()
    tracker.start()

    context = WorkflowContext()

    # Step 1: Input processing
    tracker.start_step("input_processing")
    input_data = await process_input(data, context)
    tracker.end_step("input_processing")

    # Step 2: LLM call
    tracker.start_step("llm_call")
    llm_result = await llm_primitive.execute(input_data, context)
    tracker.end_step("llm_call")

    # Step 3: Output formatting
    tracker.start_step("output_formatting")
    output = await format_output(llm_result, context)
    tracker.end_step("output_formatting")

    # Get metrics
    metrics = tracker.get_metrics()
    print(f"Total time: {metrics.total_time_ms:.2f}ms")
    for step, duration in metrics.steps.items():
        percentage = (duration / metrics.total_time_ms) * 100
        print(f"  {step}: {duration:.2f}ms ({percentage:.1f}%)")
```

### Baseline Metrics Example

```
Baseline Performance:
  Total time: 2,450ms
  Steps:
    input_processing: 50ms (2%)
    llm_call: 2,300ms (94%)  ← Bottleneck!
    output_formatting: 100ms (4%)
```

---

## Step 2: Profile to Find Bottlenecks

### Async Profiling

```python
import cProfile
import pstats
import asyncio
from io import StringIO

async def profile_workflow():
    """Profile async workflow."""
    profiler = cProfile.Profile()
    profiler.enable()

    # Run workflow
    await workflow.execute(data, context)

    profiler.disable()

    # Analyze results
    s = StringIO()
    ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
    ps.print_stats()

    print(s.getvalue())

# Alternative: Use py-spy for production profiling
# $ py-spy record -o profile.svg -- python app.py
```

### Identify Bottleneck Types

| Bottleneck Type | Symptoms | Solution |
|----------------|----------|----------|
| Sequential LLM calls | 90%+ time in LLM | Parallelize |
| Repeated queries | High latency, repeated patterns | Add caching |
| Expensive operations | Single slow step | Optimize algorithm |
| Network I/O | Time in API calls | Batch requests |
| Large data | Memory spikes | Stream/chunk data |

---

## Step 3: Apply Parallelization

### Pattern: Parallel Fan-Out

**Before (Sequential):**
```python
# Sequential - 3 LLM calls take 6 seconds (2s each)
workflow = step1 >> step2 >> step3

# Timeline:
# 0s ─── step1 ──→ 2s ─── step2 ──→ 4s ─── step3 ──→ 6s
```

**After (Parallel):**
```python
from tta_dev_primitives import ParallelPrimitive

# Parallel - 3 LLM calls take 2 seconds (run simultaneously)
workflow = step1 | step2 | step3

# Timeline:
# 0s ─┬─ step1 ──→ 2s
#     ├─ step2 ──→ 2s
#     └─ step3 ──→ 2s
# Result: 3x speedup!
```

### Real-World Example: Multi-Model Analysis

```python
from tta_dev_primitives import ParallelPrimitive, SequentialPrimitive

class GPT4Analysis(WorkflowPrimitive[str, dict]):
    """Analyze with GPT-4."""
    async def execute(self, input_data: str, context: WorkflowContext) -> dict:
        # Takes 2.5s
        return {"model": "gpt-4", "analysis": "..."}

class ClaudeAnalysis(WorkflowPrimitive[str, dict]):
    """Analyze with Claude."""
    async def execute(self, input_data: str, context: WorkflowContext) -> dict:
        # Takes 2.0s
        return {"model": "claude", "analysis": "..."}

class GeminiAnalysis(WorkflowPrimitive[str, dict]):
    """Analyze with Gemini."""
    async def execute(self, input_data: str, context: WorkflowContext) -> dict:
        # Takes 1.5s
        return {"model": "gemini", "analysis": "..."}

class ConsensusAggregator(WorkflowPrimitive[list, dict]):
    """Aggregate multiple analyses."""
    async def execute(self, input_data: list, context: WorkflowContext) -> dict:
        # Takes 0.1s
        return {"consensus": "aggregated_result"}

# Sequential: 2.5s + 2.0s + 1.5s + 0.1s = 6.1s
sequential = (
    GPT4Analysis() >>
    ClaudeAnalysis() >>
    GeminiAnalysis() >>
    ConsensusAggregator()
)

# Parallel: max(2.5s, 2.0s, 1.5s) + 0.1s = 2.6s
parallel_models = GPT4Analysis() | ClaudeAnalysis() | GeminiAnalysis()
parallel = parallel_models >> ConsensusAggregator()

# Result: 2.3x speedup (6.1s → 2.6s)
```

### Pattern: Parallel Map-Reduce

```python
from tta_dev_primitives import ParallelPrimitive

class ProcessItem(WorkflowPrimitive[dict, dict]):
    """Process single item."""
    async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
        # Process item (takes 1s)
        return {"processed": input_data}

class AggregateResults(WorkflowPrimitive[list, dict]):
    """Aggregate results."""
    async def execute(self, input_data: list, context: WorkflowContext) -> dict:
        # Aggregate (takes 0.1s)
        return {"total": len(input_data), "results": input_data}

# Process 10 items in parallel
processor = ParallelPrimitive([ProcessItem() for _ in range(10)])
aggregator = AggregateResults()

workflow = processor >> aggregator

# Sequential would take: 10 * 1s + 0.1s = 10.1s
# Parallel takes: 1s + 0.1s = 1.1s
# Result: 9.2x speedup!
```

---

## Step 4: Apply Caching

### Pattern: LRU Cache with TTL

```python
from tta_dev_primitives.performance import CachePrimitive

class ExpensiveLLMCall(WorkflowPrimitive[str, str]):
    """Expensive LLM call."""
    async def execute(self, input_data: str, context: WorkflowContext) -> str:
        # Expensive: 2s, $0.01
        return await call_gpt4(input_data)

# Without cache: Every call takes 2s and costs $0.01
workflow = ExpensiveLLMCall()

# With cache: First call 2s/$0.01, subsequent calls 1ms/$0.00
cached_workflow = CachePrimitive(
    primitive=ExpensiveLLMCall(),
    ttl_seconds=3600,  # 1 hour
    max_size=10000
)

# Benchmark with 100 queries (50% repeated):
# Without cache: 100 * 2s = 200s, $1.00
# With cache: 50 * 2s + 50 * 0.001s = 100s, $0.50
# Result: 2x speedup, 50% cost savings
```

### Cache Hit Rate Optimization

```python
class SmartCachePrimitive(WorkflowPrimitive[str, dict]):
    """Cache with intelligent key normalization."""

    def __init__(self, primitive: WorkflowPrimitive):
        self.primitive = primitive
        self.cache = CachePrimitive(
            primitive=primitive,
            ttl_seconds=3600,
            max_size=10000,
            key_fn=self._normalize_key
        )

    def _normalize_key(self, input_data: str, context: WorkflowContext) -> str:
        """Normalize input for better cache hits."""
        import re

        # Convert to lowercase
        normalized = input_data.lower()

        # Remove extra whitespace
        normalized = re.sub(r'\s+', ' ', normalized)

        # Remove punctuation
        normalized = re.sub(r'[^\w\s]', '', normalized)

        # Sort words (for unordered queries)
        words = sorted(normalized.split())
        normalized = ' '.join(words)

        return normalized

    async def execute(self, input_data: str, context: WorkflowContext) -> dict:
        return await self.cache.execute(input_data, context)

# Example:
# "What is Python?"
# "what is python"
# "python what is"
# All cache to same key → Higher hit rate!
```

### Multi-Level Cache

```python
from dataclasses import dataclass

@dataclass
class MultiLevelCache:
    """Multi-level caching strategy."""
    l1_in_memory: CachePrimitive
    l2_redis: CachePrimitive
    l3_database: CachePrimitive

class MultiLevelCachePrimitive(WorkflowPrimitive[str, dict]):
    """Primitive with multi-level cache."""

    async def execute(self, input_data: str, context: WorkflowContext) -> dict:
        # Try L1 (in-memory, ~1ms)
        result = await self.l1_cache.get(input_data)
        if result:
            context.checkpoint("cache.l1.hit")
            return result

        # Try L2 (Redis, ~10ms)
        result = await self.l2_cache.get(input_data)
        if result:
            context.checkpoint("cache.l2.hit")
            # Backfill L1
            await self.l1_cache.set(input_data, result)
            return result

        # Try L3 (Database, ~50ms)
        result = await self.l3_cache.get(input_data)
        if result:
            context.checkpoint("cache.l3.hit")
            # Backfill L2 and L1
            await self.l2_cache.set(input_data, result)
            await self.l1_cache.set(input_data, result)
            return result

        # Cache miss - execute expensive operation (2000ms)
        context.checkpoint("cache.miss")
        result = await self.expensive_operation(input_data)

        # Populate all cache levels
        await self.l1_cache.set(input_data, result)
        await self.l2_cache.set(input_data, result)
        await self.l3_cache.set(input_data, result)

        return result

# Performance:
# L1 hit: 1ms (best case)
# L2 hit: 10ms (good)
# L3 hit: 50ms (acceptable)
# Miss: 2000ms (worst case)
```

---

## Step 5: Apply Intelligent Routing

### Pattern: Complexity-Based Routing

```python
from tta_dev_primitives import RouterPrimitive

def route_by_complexity(input_data: dict, context: WorkflowContext) -> str:
    """Route based on query complexity."""
    query = input_data["query"]

    # Calculate complexity score
    score = 0

    # Length-based
    if len(query.split()) > 100:
        score += 0.4
    elif len(query.split()) > 50:
        score += 0.2

    # Keyword-based
    complex_keywords = ["analyze", "compare", "explain", "why", "how", "detailed"]
    if any(kw in query.lower() for kw in complex_keywords):
        score += 0.3

    # Code detection
    if "```" in query or "def " in query or "class " in query:
        score += 0.3

    # Route based on score
    if score >= 0.6:
        return "complex"  # GPT-4: 2.5s, $0.01
    elif score >= 0.3:
        return "medium"   # GPT-4 Turbo: 1.5s, $0.005
    else:
        return "simple"   # GPT-3.5: 0.8s, $0.0005

# Fast model for simple queries
fast_model = GPT35Primitive()  # 0.8s, $0.0005

# Balanced model for medium queries
balanced_model = GPT4TurboPrimitive()  # 1.5s, $0.005

# Quality model for complex queries
quality_model = GPT4Primitive()  # 2.5s, $0.01

# Router
router = RouterPrimitive(
    routes={
        "simple": fast_model,
        "medium": balanced_model,
        "complex": quality_model
    },
    route_selector=route_by_complexity
)

# Performance (assuming 70% simple, 20% medium, 10% complex):
# Average latency: 0.7*0.8 + 0.2*1.5 + 0.1*2.5 = 1.11s
# vs. Always quality: 2.5s
# Result: 2.25x speedup!

# Average cost: 0.7*$0.0005 + 0.2*$0.005 + 0.1*$0.01 = $0.00235
# vs. Always quality: $0.01
# Result: 4.26x cost savings!
```

---

## Step 6: Optimize Data Transfer

### Pattern: Streaming Large Responses

```python
from typing import AsyncIterator

class StreamingLLMPrimitive(WorkflowPrimitive[str, AsyncIterator[str]]):
    """Stream LLM response tokens."""

    async def execute(
        self,
        input_data: str,
        context: WorkflowContext
    ) -> AsyncIterator[str]:
        """Stream response tokens."""
        context.checkpoint("llm.stream.start")

        async for token in self._stream_tokens(input_data):
            yield token

        context.checkpoint("llm.stream.complete")

    async def _stream_tokens(self, prompt: str) -> AsyncIterator[str]:
        """Stream tokens from LLM."""
        # Simulate streaming
        async for chunk in llm_api.stream(prompt):
            yield chunk["token"]

# Usage
async def process_with_streaming():
    """Process streaming response."""
    streamer = StreamingLLMPrimitive()
    context = WorkflowContext()

    # Start receiving tokens immediately (low TTFB)
    async for token in streamer.execute("Explain quantum computing", context):
        # Process token as soon as it arrives
        print(token, end='', flush=True)

# Non-streaming: Wait 2.5s for full response
# Streaming: First token in 0.3s, complete in 2.5s
# Result: Perceived latency reduced by 8.3x!
```

### Pattern: Request Batching

```python
from typing import List
import asyncio

class BatchingPrimitive(WorkflowPrimitive[list[str], list[dict]]):
    """Batch multiple requests into one API call."""

    def __init__(self, batch_size: int = 10, batch_timeout: float = 0.1):
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout
        self.pending: List[str] = []

    async def execute(
        self,
        input_data: list[str],
        context: WorkflowContext
    ) -> list[dict]:
        """Batch and execute requests."""
        context.checkpoint("batch.start")

        # Batch requests
        batches = [
            input_data[i:i + self.batch_size]
            for i in range(0, len(input_data), self.batch_size)
        ]

        # Execute batches in parallel
        results = await asyncio.gather(*[
            self._execute_batch(batch, context)
            for batch in batches
        ])

        # Flatten results
        flattened = [item for batch in results for item in batch]

        context.checkpoint("batch.complete")
        return flattened

    async def _execute_batch(
        self,
        batch: list[str],
        context: WorkflowContext
    ) -> list[dict]:
        """Execute single batch."""
        # API call with multiple items
        return await api_call_batch(batch)

# Example: Process 100 items
# Without batching: 100 API calls = 100 * 0.5s = 50s
# With batching (10 per batch): 10 API calls = 10 * 0.5s = 5s
# Result: 10x speedup!
```

---

## Step 7: Database Optimization

### Pattern: Connection Pooling

```python
import asyncpg

class PooledDatabasePrimitive(WorkflowPrimitive[dict, list]):
    """Database queries with connection pooling."""

    def __init__(self, dsn: str):
        self.dsn = dsn
        self.pool = None

    async def _ensure_pool(self):
        """Ensure pool exists."""
        if self.pool is None:
            self.pool = await asyncpg.create_pool(
                self.dsn,
                min_size=10,    # Minimum connections
                max_size=20,    # Maximum connections
                command_timeout=5.0
            )

    async def execute(
        self,
        input_data: dict,
        context: WorkflowContext
    ) -> list:
        """Execute query with pooling."""
        await self._ensure_pool()

        context.checkpoint("db.query.start")

        # Acquire connection from pool (fast, ~1ms)
        async with self.pool.acquire() as conn:
            result = await conn.fetch(input_data["query"])

        context.checkpoint("db.query.complete")
        return [dict(row) for row in result]

# Without pooling: Create connection each time (~100ms overhead)
# With pooling: Reuse connections (~1ms overhead)
# Result: 100x faster connection acquisition!
```

---

## Performance Benchmarking

### Comprehensive Benchmark Suite

```python
import asyncio
import time
from typing import Callable

class PerformanceBenchmark:
    """Benchmark workflow performance."""

    def __init__(self, workflow: WorkflowPrimitive):
        self.workflow = workflow

    async def benchmark_latency(
        self,
        test_cases: list[dict],
        num_runs: int = 10
    ) -> dict:
        """Benchmark latency."""
        latencies = []

        for _ in range(num_runs):
            for test_case in test_cases:
                start = time.time()
                context = WorkflowContext()
                await self.workflow.execute(test_case, context)
                latency = (time.time() - start) * 1000
                latencies.append(latency)

        return {
            "min_ms": min(latencies),
            "max_ms": max(latencies),
            "avg_ms": sum(latencies) / len(latencies),
            "p50_ms": self._percentile(latencies, 50),
            "p95_ms": self._percentile(latencies, 95),
            "p99_ms": self._percentile(latencies, 99)
        }

    async def benchmark_throughput(
        self,
        test_case: dict,
        duration_seconds: int = 10
    ) -> dict:
        """Benchmark throughput."""
        start = time.time()
        completed = 0

        while time.time() - start < duration_seconds:
            context = WorkflowContext()
            await self.workflow.execute(test_case, context)
            completed += 1

        actual_duration = time.time() - start
        throughput = completed / actual_duration

        return {
            "requests_per_second": throughput,
            "total_requests": completed,
            "duration_seconds": actual_duration
        }

    def _percentile(self, values: list[float], percentile: int) -> float:
        """Calculate percentile."""
        sorted_values = sorted(values)
        index = int(len(sorted_values) * (percentile / 100))
        return sorted_values[index]

# Usage
benchmark = PerformanceBenchmark(workflow)

# Latency benchmark
latency_results = await benchmark.benchmark_latency(test_cases, num_runs=10)
print(f"P50 latency: {latency_results['p50_ms']:.2f}ms")
print(f"P95 latency: {latency_results['p95_ms']:.2f}ms")
print(f"P99 latency: {latency_results['p99_ms']:.2f}ms")

# Throughput benchmark
throughput_results = await benchmark.benchmark_throughput(test_case)
print(f"Throughput: {throughput_results['requests_per_second']:.2f} req/s")
```

---

## Optimization Checklist

### Before Optimizing

- [ ] Measure baseline performance
- [ ] Profile to identify bottlenecks
- [ ] Set clear performance goals
- [ ] Understand your traffic patterns

### Optimization Strategies

- [ ] **Parallelize** independent operations
- [ ] **Cache** expensive operations (target >50% hit rate)
- [ ] **Route** queries to appropriate models
- [ ] **Batch** multiple requests
- [ ] **Stream** large responses
- [ ] **Pool** database connections
- [ ] **Index** database queries

### After Optimizing

- [ ] Measure improved performance
- [ ] Verify correctness (no regressions)
- [ ] Monitor production metrics
- [ ] Document optimizations

---

## Common Performance Traps

### ❌ Trap 1: Premature Optimization

```python
# ❌ Bad - Optimizing before measuring
workflow = (
    CachePrimitive(
        ParallelPrimitive([
            CachePrimitive(step1),
            CachePrimitive(step2)
        ])
    )
)
# Complex but might not help!

# ✅ Good - Measure first, optimize bottlenecks
# 1. Run baseline: 5s total
# 2. Profile: step2 takes 4.5s (90%)
# 3. Optimize only step2
```

### ❌ Trap 2: Over-Parallelization

```python
# ❌ Bad - Parallelizing tiny operations
workflow = step1 | step2 | step3  # Each step: 10ms
# Overhead > benefit!

# ✅ Good - Parallelize expensive operations
workflow = expensive1 | expensive2 | expensive3  # Each step: 2000ms
# Clear win!
```

### ❌ Trap 3: Cache Everything

```python
# ❌ Bad - Caching low-value operations
cached_formatter = CachePrimitive(format_output)  # Takes 1ms
# Cache overhead > savings!

# ✅ Good - Cache expensive operations
cached_llm = CachePrimitive(gpt4_call)  # Takes 2000ms
# Clear win!
```

---

## Next Steps

- **Add observability:** [[TTA.dev/Guides/Observability]]
- **Optimize costs:** [[TTA.dev/Guides/Cost Optimization]]
- **Deploy optimized workflows:** [[TTA.dev/Guides/Production Deployment]]

---

## Key Takeaways

1. **Measure first** - Always profile before optimizing
2. **Parallelize** - Independent operations can run concurrently
3. **Cache** - Target >50% hit rate for meaningful impact
4. **Route intelligently** - Send queries to appropriate models
5. **Benchmark comprehensively** - Track P50, P95, P99 latencies

**Remember:** The fastest code is code that doesn't run. Cache, parallelize, route.

---

**Created:** [[2025-10-30]]
**Last Updated:** [[2025-10-30]]
**Estimated Time:** 45 minutes
**Difficulty:** [[Advanced]]
