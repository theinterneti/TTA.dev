# FallbackPrimitive Examples for Cline

**Purpose:** Learn how to implement graceful degradation with TTA.dev's FallbackPrimitive for high availability

## Example 1: LLM Provider Failover

**When to Use:** Multiple LLM providers where you want automatic failover to maintain service availability

**Cline Prompt Example:**

```
I need to implement high availability for my LLM service.
Add fallback to alternate providers if the primary one fails.
```

**Expected Implementation:**

```python
from tta_dev_primitives.recovery import FallbackPrimitive
from tta_dev_primitives import WorkflowContext

class HighAvailabilityLLMService:
    def __init__(self):
        # Primary: OpenAI GPT-4, Fallbacks: Claude, Gemini, Local
        self.reliable_llm = FallbackPrimitive(
            primary=self._call_openai_gpt4,
            fallbacks=[
                self._call_claude_sonnet,
                self._call_gemini_pro,
                self._call_local_llama
            ]
        )

    async def generate_text(self, prompt: str) -> str:
        context = WorkflowContext(
            workflow_id="llm-service",
            metadata={"model": "gpt4_primary", "prompt_length": len(prompt)}
        )
        result = await self.reliable_llm.execute({"prompt": prompt}, context)
        return result["text"]

    async def _call_openai_gpt4(self, data: dict) -> dict:
        # Primary provider - highest quality
        pass

    async def _call_claude_sonnet(self, data: dict) -> dict:
        # Fallback provider 1 - good quality
        pass

    async def _call_gemini_pro(self, data: dict) -> dict:
        # Fallback provider 2 - medium quality
        pass

    async def _call_local_llama(self, data: dict) -> dict:
        # Final fallback - lower quality but always available
        pass
```

## Example 2: Database with Read Replicas

**When to Use:** Database cluster with primary and read replicas for read scalability

**Cline Prompt Example:**

```
Set up read replica fallback for my database service.
If the primary database fails, fall back to read replicas.
```

**Expected Implementation:**

```python
from tta_dev_primitives.recovery import FallbackPrimitive
from tta_dev_primitives import WorkflowContext
import aiosqlite

class DatabaseService:
    def __init__(self):
        # Primary: write database, Fallbacks: read replicas
        self.reliable_read = FallbackPrimitive(
            primary=self._read_from_primary,
            fallbacks=[
                self._read_from_replica_1,
                self._read_from_replica_2
            ]
        )

    async def read_user_data(self, user_id: str) -> dict:
        context = WorkflowContext(
            workflow_id="db-service",
            metadata={"user_id": user_id, "operation": "read"}
        )
        return await self.reliable_read.execute(
            {"user_id": user_id, "query": "SELECT * FROM users WHERE id = ?"},
            context
        )

    async def _read_from_primary(self, data: dict) -> dict:
        # Primary database - most up-to-date
        async with aiosqlite.connect("primary.db") as db:
            return await self._execute_query(db, data)

    async def _read_from_replica_1(self, data: dict) -> dict:
        # Read replica 1 - slightly behind but good for reads
        async with aiosqlite.connect("replica1.db") as db:
            return await self._execute_query(db, data)

    async def _read_from_replica_2(self, data: dict) -> dict:
        # Read replica 2 - backup replica
        async with aiosqlite.connect("replica2.db") as db:
            return await self._execute_query(db, data)

    async def _execute_query(self, db, data: dict) -> dict:
        cursor = await db.execute(data["query"], [data["user_id"]])
        row = await cursor.fetchone()
        return dict(row) if row else {}
```

## Example 3: CDN with Fallback Sources

**When to Use:** Content delivery with multiple sources and automatic failover

**Cline Prompt Example:**

```
Implement CDN fallback for static content delivery.
If primary CDN fails, try secondary CDNs and finally the origin server.
```

**Expected Implementation:**

```python
from tta_dev_primitives.recovery import FallbackPrimitive
from tta_dev_primitives import WorkflowContext
import aiohttp

class ContentDeliveryService:
    def __init__(self):
        # Primary: Fastly CDN, Fallbacks: Cloudflare, AWS CloudFront, Origin
        self.reliable_content = FallbackPrimitive(
            primary=self._get_from_fastly,
            fallbacks=[
                self._get_from_cloudflare,
                self._get_from_cloudfront,
                self._get_from_origin
            ]
        )

    async def deliver_content(self, content_id: str) -> bytes:
        context = WorkflowContext(
            workflow_id="cdn-service",
            metadata={"content_id": content_id, "delivery_method": "cached"}
        )
        return await self.reliable_content.execute(
            {"content_id": content_id},
            context
        )

    async def _get_from_fastly(self, data: dict) -> bytes:
        # Primary CDN - fastest edge delivery
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://cdn.fastly.com/{data['content_id']}") as resp:
                return await resp.read()

    async def _get_from_cloudflare(self, data: dict) -> bytes:
        # Secondary CDN - good global coverage
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://cdn.cloudflare.com/{data['content_id']}") as resp:
                return await resp.read()

    async def _get_from_cloudfront(self, data: dict) -> bytes:
        # Tertiary CDN - AWS infrastructure
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://d123.cloudfront.net/{data['content_id']}") as resp:
                return await resp.read()

    async def _get_from_origin(self, data: dict) -> bytes:
        # Final fallback - origin server (slower but always available)
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://origin.example.com/{data['content_id']}") as resp:
                return await resp.read()
```

## Cline Detection Patterns

**FallbackPrimitive Indicators:**

- "high availability"
- "failover"
- "redundancy"
- "multiple providers"
- "backup service"
- "graceful degradation"
- "primary and secondary"

**Cline's Response Strategy:**

1. Identify the service that needs redundancy
2. List available providers/services in order of preference
3. Implement primary → fallback → emergency fallback chain
4. Add context tracking for which provider was used
5. Include monitoring and alerting for provider failures

## Best Practices

### Provider Ordering

**Best → Worst → Emergency:**

1. **Primary:** Highest quality, best performance
2. **Secondary:** Good quality, good performance
3. **Tertiary:** Acceptable quality, reliable
4. **Emergency:** Always available, manual fallback

### Performance Metrics

```python
# Track fallback usage and performance
from tta_dev_primitives import WorkflowContext

async def track_fallback_usage(self, data: dict, context: WorkflowContext):
    context.metadata.update({
        "fallback_used": True,
        "fallback_provider": "paypal",  # Which fallback was used
        "response_time_ms": 250,
        "success": True
    })
```

## Common Mistakes to Avoid

❌ **Wrong:** Same provider in primary and fallback

```python
# Both use same provider - no redundancy
reliable = FallbackPrimitive(
    primary=openai_gpt4,
    fallbacks=[openai_gpt4, openai_gpt35]  # Same vendor
)
```

✅ **Right:** Different providers for true redundancy

```python
# True vendor redundancy
reliable = FallbackPrimitive(
    primary=openai_gpt4,
    fallbacks=[claude_sonnet, gemini_pro, local_llama]  # Different vendors
)
```

---

**Next Steps:** When cline detects high availability needs, it should suggest FallbackPrimitive with appropriate provider ordering and emergency fallback strategy.
