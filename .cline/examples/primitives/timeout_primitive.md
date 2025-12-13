# TimeoutPrimitive Examples for Cline

**Purpose:** Learn how to implement timeout handling with TTA.dev's TimeoutPrimitive for preventing hanging operations and ensuring reliable user experiences

## Example 1: Circuit Breaker Pattern for API Resilience

**When to Use:** Your API service is slow or unreliable, and you need to prevent cascading failures

**Cline Prompt Example:**

```
My external API service sometimes becomes very slow and hangs my application.
Implement a circuit breaker pattern to prevent cascading failures.
```

**Expected Implementation:**

```python
from tta_dev_primitives.recovery import TimeoutPrimitive
from tta_dev_primitives.core.base import WorkflowContext
import aiohttp
import asyncio

class CircuitBreakerTimeout:
    def __init__(self, timeout_seconds: float = 30.0):
        # Circuit breaker pattern with timeout
        self.timeout = TimeoutPrimitive(
            primitive=self._api_call,
            timeout_seconds=timeout_seconds,
            track_timeouts=True  # Track timeout occurrences
        )
        self.circuit_state = "closed"  # closed, open, half-open
        self.failure_count = 0
        self.failure_threshold = 5

    async def call_api(self, url: str, data: dict) -> dict:
        context = WorkflowContext(
            workflow_id="api-resilience",
            metadata={"url": url, "timeout": self.timeout.timeout_seconds}
        )

        # Check circuit state
        if self.circuit_state == "open":
            if self.failure_count >= self.failure_threshold:
                return {"error": "Circuit breaker is open", "fallback": True}

        try:
            result = await self.timeout.execute(data, context)
            if self.circuit_state == "open":
                # Reset on success
                self.circuit_state = "closed"
                self.failure_count = 0
            return result

        except Exception as e:
            self.failure_count += 1
            if self.failure_count >= self.failure_threshold:
                self.circuit_state = "open"
            return {"error": str(e), "circuit_breaker": True}

    async def _api_call(self, data: dict) -> dict:
        # Your actual API call with timeout protection
        timeout = aiohttp.ClientTimeout(total=self.timeout.timeout_seconds)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post("https://api.example.com/endpoint", json=data) as response:
                return await response.json()
```

**Cline's Learning Pattern:**

- Identifies hanging API operations
- Combines TimeoutPrimitive with circuit breaker logic
- Uses proper timeout tracking for monitoring
- Includes graceful degradation when circuit is open
- Proper WorkflowContext for tracing and debugging

## Example 2: LLM Call Timeouts with Graceful Degradation

**When to Use:** LLM services can be slow or unresponsive, and you need to provide fallback responses

**Cline Prompt Example:**

```
My LLM service sometimes takes too long to respond.
Add timeout handling with graceful degradation to cached or simplified responses.
```

**Expected Implementation:**

```python
from tta_dev_primitives.recovery import TimeoutPrimitive, FallbackPrimitive
from tta_dev_primitives.core.base import WorkflowContext
from tta_dev_primitives.performance import CachePrimitive

class LLMTimeoutService:
    def __init__(self):
        # Cache for fast responses
        self.cached_llm = CachePrimitive(
            primitive=self._cached_llm_call,
            ttl_seconds=3600,  # 1 hour cache
            max_size=1000
        )

        # Timeout with fallback
        self.timed_llm = TimeoutPrimitive(
            primitive=self.cached_llm,
            timeout_seconds=30.0,  # 30 second timeout
            fallback=self._fallback_response
        )

    async def generate_response(self, prompt: str, context_data: dict) -> dict:
        context = WorkflowContext(
            workflow_id="llm-generation",
            metadata={
                "prompt_length": len(prompt),
                "timeout": 30.0,
                "has_cache": True
            }
        )

        try:
            result = await self.timed_llm.execute(
                {"prompt": prompt, **context_data},
                context
            )
            result["response_type"] = "llm_with_timeout"
            return result

        except Exception as e:
            # Final fallback
            return {
                "response": "I apologize, but I'm experiencing high load. Please try again.",
                "response_type": "timeout_fallback",
                "error": str(e)
            }

    async def _cached_llm_call(self, data: dict) -> dict:
        # Simulate LLM call
        await asyncio.sleep(5)  # Simulate slow LLM
        return {"response": f"Generated response for: {data['prompt']}"}

    async def _fallback_response(self, data: dict) -> dict:
        # Quick simplified response
        return {
            "response": f"Quick response: {data['prompt'][:100]}...",
            "response_type": "timeout_fallback",
            "note": "Generated with timeout fallback"
        }
```

**Cline's Learning Pattern:**

- Identifies slow LLM operations
- Combines CachePrimitive, TimeoutPrimitive, and FallbackPrimitive
- Uses hierarchical fallback strategy
- Proper timeout and caching configuration
- Context tracking for monitoring response types

## Example 3: Database Connection Timeouts

**When to Use:** Database queries can hang due to locks, large datasets, or network issues

**Cline Prompt Example:**

```
My database queries are sometimes taking too long to execute.
Implement timeout handling to prevent query hanging.
```

**Expected Implementation:**

```python
from tta_dev_primitives.recovery import TimeoutPrimitive
from tta_dev_primitives.core.base import WorkflowContext
import aiosqlite
import asyncio

class DatabaseTimeoutService:
    def __init__(self, db_path: str):
        self.db_path = db_path
        # Query timeout for slow operations
        self.query_timeout = TimeoutPrimitive(
            primitive=self._execute_query,
            timeout_seconds=10.0,  # 10 second max query time
            track_timeouts=True
        )
        # Connection timeout
        self.connection_timeout = TimeoutPrimitive(
            primitive=self._connect_and_query,
            timeout_seconds=5.0,  # 5 second connection timeout
            track_timeouts=True
        )

    async def safe_query(self, query: str, params: dict | None = None) -> dict:
        context = WorkflowContext(
            workflow_id="db-query",
            metadata={
                "query_type": "select" if "SELECT" in query.upper() else "other",
                "has_params": params is not None
            }
        )

        try:
            # Try connection with timeout first
            result = await self.connection_timeout.execute(
                {"query": query, "params": params or {}},
                context
            )
            return result

        except Exception as e:
            return {
                "error": "Query timeout",
                "message": str(e),
                "query": query,
                "timed_out": True
            }

    async def safe_execute(self, query: str, params: dict | None = None) -> dict:
        context = WorkflowContext(
            workflow_id="db-execute",
            metadata={"query": query, "timeout": 10.0}
        )

        return await self.query_timeout.execute(
            {"query": query, "params": params or {}},
            context
        )

    async def _connect_and_query(self, data: dict) -> dict:
        async with aiosqlite.connect(self.db_path) as db:
            # Set connection timeout
            await db.execute("PRAGMA busy_timeout = 5000")  # 5 second busy timeout

            query = data["query"]
            params = data["params"]

            if params:
                cursor = await db.execute(query, tuple(params.values()))
            else:
                cursor = await db.execute(query)

            if "SELECT" in query.upper():
                rows = await cursor.fetchall()
                columns = [description[0] for description in cursor.description]
                return {"rows": [dict(zip(columns, row)) for row in rows]}
            else:
                await db.commit()
                return {"affected_rows": cursor.rowcount}

    async def _execute_query(self, data: dict) -> dict:
        # Same as above but with different timeout
        return await self._connect_and_query(data)
```

**Cline's Learning Pattern:**

- Identifies database operation timeout needs
- Uses different timeout periods for connection vs query operations
- Sets database-specific timeout configurations
- Tracks timeout patterns for optimization
- Proper error handling and response formatting

## Example 4: Webhook Processing Timeouts

**When to Use:** Webhook handlers need to process quickly to avoid timeouts from external services

**Cline Prompt Example:**

```
My webhook endpoint sometimes takes too long to process and causes timeouts.
Implement timeout handling for webhook processing with quick responses.
```

**Expected Implementation:**

```python
from tta_dev_primitives.recovery import TimeoutPrimitive
from tta_dev_primitives.core.base import WorkflowContext
import asyncio
import json

class WebhookTimeoutProcessor:
    def __init__(self):
        # Fast webhook processing with timeout
        self.webhook_timeout = TimeoutPrimitive(
            primitive=self._process_webhook,
            timeout_seconds=8.0,  # 8 second max processing time
            fallback=self._quick_response
        )

        # Background processing for long tasks
        self.background_processor = TimeoutPrimitive(
            primitive=self._background_task,
            timeout_seconds=300.0,  # 5 minute background timeout
            track_timeouts=True
        )

    async def handle_webhook(self, webhook_data: dict, headers: dict) -> dict:
        context = WorkflowContext(
            workflow_id="webhook-processing",
            metadata={
                "webhook_source": headers.get("X-Webhook-Source", "unknown"),
                "event_type": webhook_data.get("event", "unknown")
            }
        )

        try:
            # Process webhook with timeout
            result = await self.webhook_timeout.execute(webhook_data, context)
            result["processing_status"] = "completed"
            return result

        except Exception as e:
            # Even if processing fails, return success to webhook sender
            return {
                "status": "received",
                "message": "Webhook received, processing asynchronously",
                "webhook_id": webhook_data.get("id"),
                "processing_status": "async",
                "error": str(e)
            }

    async def _process_webhook(self, data: dict) -> dict:
        event_type = data.get("event", "unknown")

        if event_type == "payment_succeeded":
            return await self._handle_payment_webhook(data)
        elif event_type == "user_created":
            return await self._handle_user_webhook(data)
        else:
            return await self._handle_generic_webhook(data)

    async def _handle_payment_webhook(self, data: dict) -> dict:
        # Simulate payment processing
        await asyncio.sleep(2)  # Simulate payment verification

        # Send to background for additional processing
        await self.background_processor.execute(
            {"type": "payment_async", "data": data},
            WorkflowContext(workflow_id="background-payment")
        )

        return {
            "status": "processed",
            "payment_id": data.get("payment_id"),
            "amount": data.get("amount")
        }

    async def _handle_user_webhook(self, data: dict) -> dict:
        # Quick user processing
        await asyncio.sleep(1)
        return {
            "status": "user_processed",
            "user_id": data.get("user_id")
        }

    async def _handle_generic_webhook(self, data: dict) -> dict:
        # Minimal processing for unknown events
        return {
            "status": "received",
            "event_type": data.get("event"),
            "processed_at": "immediate"
        }

    async def _quick_response(self, data: dict) -> dict:
        # Fallback for timeout - return immediately
        return {
            "status": "received",
            "message": "Webhook received, queued for processing",
            "processing": "async"
        }

    async def _background_task(self, data: dict) -> dict:
        # Background processing with longer timeout
        task_type = data.get("type")
        if task_type == "payment_async":
            # Simulate additional payment processing
            await asyncio.sleep(30)
            return {"background_task": "payment_async_completed"}
        return {"background_task": "completed"}
```

**Cline's Learning Pattern:**

- Identifies webhook processing timeout requirements
- Uses short timeouts for webhook responses
- Implements background processing for long tasks
- Provides quick fallback responses to prevent webhook sender timeouts
- Proper event type handling and processing strategies

## Cline Detection Patterns

**TimeoutPrimitive Indicators:**

- "operation hanging"
- "too slow to respond"
- "prevent timeouts"
- "circuit breaker"
- "graceful degradation"
- "database query taking too long"
- "API calls timing out"
- "webhook processing timeout"

**Cline's Response Strategy:**

1. Identify timeout-prone operations
2. Suggest appropriate timeout values based on operation type
3. Combine with fallbacks for graceful degradation
4. Add timeout tracking for monitoring
5. Use proper WorkflowContext for correlation

## Common Mistakes to Avoid

❌ **Wrong:** No timeout or too aggressive timeout

```python
# No timeout - can hang forever
workflow = my_primitive  # Dangerous!

# Too aggressive - never gives operation chance
workflow = TimeoutPrimitive(primitive=my_primitive, timeout_seconds=0.1)
```

✅ **Right:** Appropriate timeout with fallback

```python
# Reasonable timeout with fallback
workflow = TimeoutPrimitive(
    primitive=my_primitive,
    timeout_seconds=30.0,  # 30 seconds
    fallback=quick_response
)
```

❌ **Wrong:** No timeout tracking

```python
# Can't monitor timeout patterns
workflow = TimeoutPrimitive(primitive=my_primitive, timeout_seconds=30.0)
```

✅ **Right:** Track timeouts for optimization

```python
# Track timeouts for analysis
workflow = TimeoutPrimitive(
    primitive=my_primitive,
    timeout_seconds=30.0,
    track_timeouts=True  # Monitor patterns
)
```

---

**Next Steps:** When cline detects timeout-related patterns, it should automatically suggest TimeoutPrimitive with appropriate configuration and complementary primitives (caching, retry, fallback) based on the specific use case.


---
**Logseq:** [[TTA.dev/.cline/Examples/Primitives/Timeout_primitive]]
