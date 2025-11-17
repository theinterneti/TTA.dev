# Context: Performance Optimization

**Purpose:** Performance optimization guidance for TTA components

**When to Use:**
- Slow response times
- High latency
- Resource bottlenecks
- Scaling issues
- Database performance problems

---

## Performance Optimization Workflow

### 1. Measure First

**Goal:** Identify actual bottlenecks

**Principle:** "Premature optimization is the root of all evil" - Donald Knuth

**Steps:**
1. Define performance requirements
2. Measure current performance
3. Identify bottlenecks
4. Optimize bottlenecks
5. Measure improvement

**Tools:**
```python
# Time function execution
import time

start = time.time()
result = await slow_function()
duration = time.time() - start
print(f"Execution time: {duration:.2f}s")

# Profile code
import cProfile
cProfile.run('slow_function()')

# Use TTA observability
from scripts.primitives.dev_metrics import track_execution

@track_execution("function_name")
async def my_function():
    # Function implementation
    pass
```

---

### 2. Set Performance Targets

**TTA Performance Requirements:**

**API Response Times:**
- **P50:** <200ms (median)
- **P95:** <500ms (95th percentile)
- **P99:** <1000ms (99th percentile)

**Database Operations:**
- **Redis:** <10ms per operation
- **Neo4j:** <100ms per query

**AI Provider:**
- **Timeout:** 30s
- **Retry:** 3 attempts with exponential backoff

---

## Common Performance Optimizations

### 1. Database Optimization

#### A. Redis Optimization

**Use Connection Pooling:**
```python
# ❌ Bad: Create connection per request
async def get_session(session_id: str):
    redis = await create_redis_connection()
    data = await redis.get(f"session:{session_id}")
    await redis.close()
    return data

# ✅ Good: Use connection pool
class SessionRepository:
    def __init__(self, redis_pool: ConnectionPool):
        self.redis = Redis(connection_pool=redis_pool)
    
    async def get_session(self, session_id: str):
        return await self.redis.get(f"session:{session_id}")
```

**Use Pipelining:**
```python
# ❌ Bad: Multiple round trips
async def get_multiple_sessions(session_ids: list[str]):
    sessions = []
    for session_id in session_ids:
        data = await redis.get(f"session:{session_id}")
        sessions.append(data)
    return sessions

# ✅ Good: Single round trip with pipeline
async def get_multiple_sessions(session_ids: list[str]):
    async with redis.pipeline() as pipe:
        for session_id in session_ids:
            pipe.get(f"session:{session_id}")
        return await pipe.execute()
```

**Use Caching:**
```python
# ✅ Good: Cache frequently accessed data
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_ai_model_config(model_name: str) -> dict:
    """Get AI model configuration (cached)."""
    # Expensive operation
    return load_model_config(model_name)
```

---

#### B. Neo4j Optimization

**Use Indexes:**
```cypher
-- Create indexes for frequently queried properties
CREATE INDEX session_id IF NOT EXISTS FOR (n:NarrativeNode) ON (n.session_id);
CREATE INDEX user_id IF NOT EXISTS FOR (s:Session) ON (s.user_id);
CREATE INDEX timestamp IF NOT EXISTS FOR (n:NarrativeNode) ON (n.timestamp);
```

**Optimize Queries:**
```python
# ❌ Bad: Fetch all nodes then filter in Python
def get_recent_narrative(session_id: str):
    result = neo4j.run(
        "MATCH (n:NarrativeNode {session_id: $session_id}) RETURN n",
        session_id=session_id
    )
    nodes = [record["n"] for record in result]
    return sorted(nodes, key=lambda n: n["timestamp"], reverse=True)[:10]

# ✅ Good: Filter and limit in database
def get_recent_narrative(session_id: str, limit: int = 10):
    result = neo4j.run(
        "MATCH (n:NarrativeNode {session_id: $session_id}) "
        "RETURN n "
        "ORDER BY n.timestamp DESC "
        "LIMIT $limit",
        session_id=session_id,
        limit=limit
    )
    return [record["n"] for record in result]
```

**Use Query Parameters:**
```python
# ❌ Bad: String concatenation (slow + SQL injection risk)
query = f"MATCH (n:NarrativeNode {{session_id: '{session_id}'}}) RETURN n"
result = neo4j.run(query)

# ✅ Good: Parameterized query
result = neo4j.run(
    "MATCH (n:NarrativeNode {session_id: $session_id}) RETURN n",
    session_id=session_id
)
```

---

### 2. Async Optimization

**Use Concurrent Execution:**
```python
# ❌ Bad: Sequential execution
async def get_session_data(session_id: str):
    session = await get_session(session_id)
    narrative = await get_narrative(session_id)
    user = await get_user(session.user_id)
    return session, narrative, user

# ✅ Good: Concurrent execution
async def get_session_data(session_id: str):
    session_task = get_session(session_id)
    narrative_task = get_narrative(session_id)
    
    session, narrative = await asyncio.gather(session_task, narrative_task)
    user = await get_user(session.user_id)
    
    return session, narrative, user
```

**Avoid Blocking Operations:**
```python
# ❌ Bad: Blocking in async function
async def process_data(data: str):
    result = expensive_sync_operation(data)  # Blocks event loop!
    return result

# ✅ Good: Run in executor
import asyncio
from concurrent.futures import ThreadPoolExecutor

executor = ThreadPoolExecutor(max_workers=4)

async def process_data(data: str):
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(executor, expensive_sync_operation, data)
    return result
```

---

### 3. AI Provider Optimization

**Use Streaming:**
```python
# ❌ Bad: Wait for complete response
async def get_ai_response(prompt: str) -> str:
    response = await ai_provider.generate(prompt)  # Wait 10-30s
    return response

# ✅ Good: Stream response
async def stream_ai_response(prompt: str):
    async for chunk in ai_provider.stream(prompt):
        yield chunk  # Return chunks as they arrive
```

**Implement Caching:**
```python
# ✅ Good: Cache AI responses
class AIProviderWithCache:
    def __init__(self, provider: AIProvider, redis: Redis):
        self.provider = provider
        self.redis = redis
    
    async def generate(self, prompt: str) -> str:
        # Check cache
        cache_key = f"ai_response:{hash(prompt)}"
        cached = await self.redis.get(cache_key)
        if cached:
            return cached
        
        # Generate and cache
        response = await self.provider.generate(prompt)
        await self.redis.setex(cache_key, 3600, response)  # Cache 1 hour
        return response
```

**Use Rate Limiting:**
```python
# ✅ Good: Rate limiting with error recovery
from scripts.primitives.error_recovery import with_retry, RetryConfig

class RateLimitedAIProvider:
    def __init__(self, provider: AIProvider, max_requests_per_minute: int = 60):
        self.provider = provider
        self.max_requests = max_requests_per_minute
        self.requests = []
    
    @with_retry(RetryConfig(max_retries=3, base_delay=1.0))
    async def generate(self, prompt: str) -> str:
        # Rate limiting logic
        await self._wait_if_needed()
        
        try:
            response = await self.provider.generate(prompt)
            self.requests.append(time.time())
            return response
        except RateLimitError:
            # Wait and retry
            await asyncio.sleep(60)
            raise
    
    async def _wait_if_needed(self):
        now = time.time()
        # Remove requests older than 1 minute
        self.requests = [t for t in self.requests if now - t < 60]
        
        if len(self.requests) >= self.max_requests:
            wait_time = 60 - (now - self.requests[0])
            await asyncio.sleep(wait_time)
```

---

### 4. Memory Optimization

**Use Generators:**
```python
# ❌ Bad: Load all data into memory
def get_all_sessions(user_id: str) -> list[Session]:
    sessions = []
    for session_id in get_session_ids(user_id):
        session = get_session(session_id)
        sessions.append(session)
    return sessions

# ✅ Good: Use generator
def get_all_sessions(user_id: str):
    for session_id in get_session_ids(user_id):
        yield get_session(session_id)
```

**Limit Result Sets:**
```python
# ❌ Bad: Fetch unlimited results
def get_narrative_history(session_id: str):
    return neo4j.run(
        "MATCH (n:NarrativeNode {session_id: $session_id}) RETURN n",
        session_id=session_id
    ).data()

# ✅ Good: Limit results
def get_narrative_history(session_id: str, limit: int = 100):
    return neo4j.run(
        "MATCH (n:NarrativeNode {session_id: $session_id}) "
        "RETURN n "
        "ORDER BY n.timestamp DESC "
        "LIMIT $limit",
        session_id=session_id,
        limit=limit
    ).data()
```

---

## Performance Testing

### 1. Load Testing

**Goal:** Verify system handles expected load

**Tools:**
```bash
# Install locust
uv add --dev locust

# Create load test
# tests/load/locustfile.py
from locust import HttpUser, task, between

class TTAUser(HttpUser):
    wait_time = between(1, 3)
    
    @task
    def create_session(self):
        self.client.post("/api/v1/sessions", json={"user_id": "test_user"})
    
    @task(3)
    def player_action(self):
        self.client.post(
            "/api/v1/sessions/test_session/actions",
            json={"type": "explore", "parameters": {}}
        )

# Run load test
locust -f tests/load/locustfile.py --host=http://localhost:8000
```

---

### 2. Profiling

**CPU Profiling:**
```python
import cProfile
import pstats

# Profile function
profiler = cProfile.Profile()
profiler.enable()

await slow_function()

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(20)  # Top 20 functions
```

**Memory Profiling:**
```python
from memory_profiler import profile

@profile
async def memory_intensive_function():
    # Function implementation
    pass
```

---

## Performance Monitoring

### 1. Metrics Collection

**Use TTA Observability:**
```python
from scripts.primitives.dev_metrics import track_execution, ExecutionMetric

@track_execution("api_endpoint")
async def api_endpoint():
    # Automatically tracks execution time
    pass

# View metrics
python scripts/primitives/dev_metrics.py
```

**Custom Metrics:**
```python
import time

class PerformanceMonitor:
    def __init__(self):
        self.metrics = []
    
    async def track(self, name: str, func, *args, **kwargs):
        start = time.time()
        try:
            result = await func(*args, **kwargs)
            duration = time.time() - start
            self.metrics.append({
                "name": name,
                "duration": duration,
                "success": True
            })
            return result
        except Exception as e:
            duration = time.time() - start
            self.metrics.append({
                "name": name,
                "duration": duration,
                "success": False,
                "error": str(e)
            })
            raise
```

---

### 2. Alerting

**Set Performance Alerts:**
```python
# Alert if response time > threshold
async def check_performance(duration: float, threshold: float = 1.0):
    if duration > threshold:
        logger.warning(f"Slow operation: {duration:.2f}s (threshold: {threshold}s)")
        # Send alert (email, Slack, etc.)
```

---

## TTA-Specific Optimizations

### 1. Session State Optimization

**Use Redis for Fast Access:**
```python
# ✅ Good: Cache session state in Redis
class SessionRepository:
    async def get_session(self, session_id: str) -> Session:
        # Try Redis first (fast)
        cached = await self.redis.get(f"session:{session_id}")
        if cached:
            return Session.parse_raw(cached)
        
        # Fallback to Neo4j (slower)
        result = self.neo4j.run(
            "MATCH (s:Session {id: $id}) RETURN s",
            id=session_id
        )
        session = Session.from_neo4j(result.single()["s"])
        
        # Cache for next time
        await self.redis.setex(f"session:{session_id}", 3600, session.json())
        return session
```

---

### 2. Narrative Graph Optimization

**Limit Graph Traversal:**
```python
# ❌ Bad: Traverse entire graph
def get_narrative_context(session_id: str):
    result = neo4j.run(
        "MATCH path = (start:NarrativeNode {session_id: $session_id})-[:NEXT*]->(end) "
        "RETURN path",
        session_id=session_id
    )
    return result.data()

# ✅ Good: Limit traversal depth
def get_narrative_context(session_id: str, depth: int = 5):
    result = neo4j.run(
        "MATCH path = (start:NarrativeNode {session_id: $session_id})-[:NEXT*1..$depth]->(end) "
        "RETURN path "
        "ORDER BY length(path) DESC "
        "LIMIT 1",
        session_id=session_id,
        depth=depth
    )
    return result.data()
```

---

## Resources

### TTA Documentation
- Observability: `scripts/primitives/dev_metrics.py`
- Error Recovery: `scripts/primitives/error_recovery.py`

### External Resources
- Python Performance: https://docs.python.org/3/library/profile.html
- Redis Performance: https://redis.io/docs/management/optimization/
- Neo4j Performance: https://neo4j.com/docs/cypher-manual/current/query-tuning/

---

**Note:** Always measure before and after optimization to verify improvement.

