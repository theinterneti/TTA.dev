# API

**Tag page for API design, integration, and RESTful patterns**

---

## Overview

**API** in TTA.dev includes:
- 🌐 RESTful API patterns
- 🔌 API integration primitives
- 📡 HTTP client patterns
- 🔑 Authentication and authorization
- 📊 API observability

**Goal:** Seamless API integration with composable primitives.

**See:** [[TTA Primitives]], [[Examples]]

---

## Pages Tagged with #API

{{query (page-tags [[API]])}}

---

## API Integration

### 1. HTTP Client Primitive

**HTTP requests with retry and timeout:**

```python
import httpx
from tta_dev_primitives import WorkflowPrimitive, WorkflowContext
from tta_dev_primitives.recovery import RetryPrimitive, TimeoutPrimitive

class HTTPClientPrimitive(WorkflowPrimitive):
    """HTTP client for API calls."""

    def __init__(self, base_url: str, timeout: float = 30.0):
        super().__init__()
        self.base_url = base_url
        self.timeout = timeout

    async def _execute(self, data: dict, context: WorkflowContext) -> dict:
        """Execute HTTP request."""
        method = data.get("method", "GET")
        path = data.get("path", "/")
        headers = data.get("headers", {})
        params = data.get("params", {})
        json_data = data.get("json")

        url = f"{self.base_url}{path}"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=json_data
            )
            response.raise_for_status()

            return {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "data": response.json() if response.content else None
            }
```

**With retry and timeout:**

```python
# Build resilient API client
api_client = HTTPClientPrimitive(base_url="https://api.example.com")

# Add timeout
timed_client = TimeoutPrimitive(
    primitive=api_client,
    timeout_seconds=30.0
)

# Add retry
resilient_client = RetryPrimitive(
    primitive=timed_client,
    max_retries=3,
    backoff_strategy="exponential"
)

# Use it
result = await resilient_client.execute(
    {
        "method": "POST",
        "path": "/users",
        "json": {"name": "Alice", "email": "alice@example.com"}
    },
    context
)
```

**See:** [[TTA Primitives/HTTPClientPrimitive]]

---

### 2. REST API Primitive

**RESTful resource operations:**

```python
class RESTAPIPrimitive(WorkflowPrimitive):
    """RESTful API operations."""

    def __init__(self, base_url: str, resource: str):
        super().__init__()
        self.base_url = base_url
        self.resource = resource
        self.client = HTTPClientPrimitive(base_url)

    async def _execute(self, data: dict, context: WorkflowContext) -> dict:
        """Execute REST operation."""
        operation = data.get("operation", "list")

        if operation == "list":
            # GET /resource
            return await self.client.execute(
                {"method": "GET", "path": f"/{self.resource}"},
                context
            )

        elif operation == "get":
            # GET /resource/:id
            resource_id = data["id"]
            return await self.client.execute(
                {"method": "GET", "path": f"/{self.resource}/{resource_id}"},
                context
            )

        elif operation == "create":
            # POST /resource
            return await self.client.execute(
                {
                    "method": "POST",
                    "path": f"/{self.resource}",
                    "json": data["body"]
                },
                context
            )

        elif operation == "update":
            # PUT /resource/:id
            resource_id = data["id"]
            return await self.client.execute(
                {
                    "method": "PUT",
                    "path": f"/{self.resource}/{resource_id}",
                    "json": data["body"]
                },
                context
            )

        elif operation == "delete":
            # DELETE /resource/:id
            resource_id = data["id"]
            return await self.client.execute(
                {"method": "DELETE", "path": f"/{self.resource}/{resource_id}"},
                context
            )

        raise ValueError(f"Unknown operation: {operation}")
```

**Usage:**

```python
# Create users API client
users_api = RESTAPIPrimitive(
    base_url="https://api.example.com",
    resource="users"
)

# List users
users = await users_api.execute(
    {"operation": "list"},
    context
)

# Create user
new_user = await users_api.execute(
    {
        "operation": "create",
        "body": {"name": "Bob", "email": "bob@example.com"}
    },
    context
)

# Update user
updated = await users_api.execute(
    {
        "operation": "update",
        "id": "123",
        "body": {"name": "Bob Smith"}
    },
    context
)
```

---

### 3. API Authentication

**Bearer token authentication:**

```python
class AuthenticatedAPIPrimitive(WorkflowPrimitive):
    """API client with authentication."""

    def __init__(self, base_url: str, token: str):
        super().__init__()
        self.base_url = base_url
        self.token = token

    async def _execute(self, data: dict, context: WorkflowContext) -> dict:
        """Execute authenticated request."""
        # Add authorization header
        headers = data.get("headers", {})
        headers["Authorization"] = f"Bearer {self.token}"

        data["headers"] = headers

        # Use HTTP client
        client = HTTPClientPrimitive(self.base_url)
        return await client.execute(data, context)
```

**OAuth2 flow:**

```python
class OAuth2APIPrimitive(WorkflowPrimitive):
    """API client with OAuth2."""

    def __init__(self, base_url: str, client_id: str, client_secret: str):
        super().__init__()
        self.base_url = base_url
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None

    async def _get_token(self) -> str:
        """Get or refresh access token."""
        if self.access_token:
            return self.access_token

        # Token endpoint
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/oauth/token",
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret
                }
            )
            response.raise_for_status()

            token_data = response.json()
            self.access_token = token_data["access_token"]
            return self.access_token

    async def _execute(self, data: dict, context: WorkflowContext) -> dict:
        """Execute OAuth2-authenticated request."""
        token = await self._get_token()

        headers = data.get("headers", {})
        headers["Authorization"] = f"Bearer {token}"
        data["headers"] = headers

        client = HTTPClientPrimitive(self.base_url)
        return await client.execute(data, context)
```

---

## API Patterns

### Pattern: Cached API Calls

**Cache expensive API calls:**

```python
from tta_dev_primitives.performance import CachePrimitive

async def cached_api_workflow():
    """API calls with caching."""
    # Base API client
    api = RESTAPIPrimitive(
        base_url="https://api.example.com",
        resource="products"
    )

    # Wrap with cache
    cached_api = CachePrimitive(
        primitive=api,
        ttl_seconds=3600,  # Cache for 1 hour
        max_size=1000,
        key_fn=lambda data, ctx: f"{data['operation']}:{data.get('id', 'all')}"
    )

    # Use cached version
    result = await cached_api.execute(
        {"operation": "list"},
        context
    )

    return result
```

**Benefits:**
- 30-50% API cost reduction
- 10-100x faster responses (cache hit)
- Reduced rate limiting
- Better user experience

---

### Pattern: Parallel API Calls

**Fetch from multiple endpoints:**

```python
from tta_dev_primitives import ParallelPrimitive

async def parallel_api_workflow():
    """Parallel API calls."""
    # Multiple API clients
    users_api = RESTAPIPrimitive(base_url="https://api.example.com", resource="users")
    products_api = RESTAPIPrimitive(base_url="https://api.example.com", resource="products")
    orders_api = RESTAPIPrimitive(base_url="https://api.example.com", resource="orders")

    # Parallel execution
    workflow = users_api | products_api | orders_api

    # Execute all concurrently
    results = await workflow.execute(
        {"operation": "list"},
        context
    )

    # Results: [users_data, products_data, orders_data]
    return {
        "users": results[0],
        "products": results[1],
        "orders": results[2]
    }
```

---

### Pattern: API Rate Limiting

**Respect rate limits:**

```python
import asyncio
from collections import deque
from time import time

class RateLimitedAPIPrimitive(WorkflowPrimitive):
    """API client with rate limiting."""

    def __init__(self, api: WorkflowPrimitive, max_requests: int, window_seconds: float):
        super().__init__()
        self.api = api
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = deque()

    async def _wait_if_needed(self):
        """Wait if rate limit reached."""
        now = time()

        # Remove old requests
        while self.requests and self.requests[0] < now - self.window_seconds:
            self.requests.popleft()

        # Check if rate limit reached
        if len(self.requests) >= self.max_requests:
            # Wait until oldest request expires
            wait_time = self.window_seconds - (now - self.requests[0])
            if wait_time > 0:
                await asyncio.sleep(wait_time)
                # Recursively check again
                return await self._wait_if_needed()

        # Record this request
        self.requests.append(now)

    async def _execute(self, data: dict, context: WorkflowContext) -> dict:
        """Execute with rate limiting."""
        await self._wait_if_needed()
        return await self.api.execute(data, context)
```

**Usage:**

```python
# Create rate-limited client
api = RESTAPIPrimitive(base_url="https://api.example.com", resource="users")
rate_limited_api = RateLimitedAPIPrimitive(
    api=api,
    max_requests=100,  # Max 100 requests
    window_seconds=60  # Per 60 seconds
)

# Automatically respects rate limits
result = await rate_limited_api.execute(data, context)
```

---

### Pattern: API Fallback

**Multiple API providers:**

```python
from tta_dev_primitives.recovery import FallbackPrimitive

async def multi_provider_api():
    """API with multiple providers."""
    # Primary provider
    primary_api = RESTAPIPrimitive(
        base_url="https://primary-api.com",
        resource="geocode"
    )

    # Fallback providers
    secondary_api = RESTAPIPrimitive(
        base_url="https://secondary-api.com",
        resource="geocode"
    )

    tertiary_api = RESTAPIPrimitive(
        base_url="https://tertiary-api.com",
        resource="geocode"
    )

    # Fallback chain
    workflow = FallbackPrimitive(
        primary=primary_api,
        fallbacks=[secondary_api, tertiary_api]
    )

    # Automatically tries fallbacks on failure
    result = await workflow.execute(
        {
            "operation": "get",
            "params": {"address": "1600 Amphitheatre Parkway"}
        },
        context
    )

    return result
```

---

## API Best Practices

### ✅ DO

**Use Proper HTTP Methods:**
```python
# ✅ Good: RESTful methods
GET    /users       # List users
GET    /users/123   # Get user
POST   /users       # Create user
PUT    /users/123   # Update user
DELETE /users/123   # Delete user

# ❌ Bad: Everything as POST
POST /getUsers
POST /createUser
POST /deleteUser
```

**Handle Errors Properly:**
```python
# ✅ Good: Proper error handling
try:
    response = await api.execute(data, context)
except httpx.HTTPStatusError as e:
    if e.response.status_code == 404:
        return {"error": "Resource not found"}
    elif e.response.status_code == 429:
        # Rate limit - retry after delay
        await asyncio.sleep(60)
        return await api.execute(data, context)
    else:
        raise
```

**Use Timeouts:**
```python
# ✅ Good: Always set timeouts
api = TimeoutPrimitive(
    primitive=http_client,
    timeout_seconds=30.0
)

# ❌ Bad: No timeout (hangs forever)
api = HTTPClientPrimitive(base_url=url)
```

---

### ❌ DON'T

**Don't Expose Secrets:**
```python
# ❌ Bad: Hardcoded API key
api_key = "sk_live_..."

# ✅ Good: Environment variable
import os
api_key = os.environ["API_KEY"]
```

**Don't Ignore Rate Limits:**
```python
# ❌ Bad: No rate limiting
for i in range(1000):
    await api.execute(data)  # Gets blocked!

# ✅ Good: Rate-limited client
rate_limited = RateLimitedAPIPrimitive(api, max_requests=100, window_seconds=60)
for i in range(1000):
    await rate_limited.execute(data)
```

---

## API Metrics

### Request Metrics

```promql
# Request rate
rate(api_requests_total[5m])

# Error rate
rate(api_errors_total[5m]) /
rate(api_requests_total[5m])

# Request duration P95
histogram_quantile(0.95, api_request_duration_seconds)

# Status code distribution
sum by (status_code) (api_requests_total)
```

**Targets:**
- Error rate: <1%
- P95 latency: <500ms
- Success rate: >99%

---

### Cache Metrics

```promql
# Cache hit rate
api_cache_hits_total /
(api_cache_hits_total + api_cache_misses_total)

# Cache evictions
rate(api_cache_evictions_total[5m])
```

**Targets:**
- Cache hit rate: >60%
- Eviction rate: <10/min

---

## API Documentation

### API Design Guidelines

**RESTful principles:**
1. Use nouns for resources (`/users`, not `/getUsers`)
2. Use HTTP methods correctly (GET, POST, PUT, DELETE)
3. Use proper status codes (200, 201, 404, 500)
4. Version your API (`/v1/users`)
5. Use pagination for lists
6. Include proper error messages
7. Document with OpenAPI/Swagger

**See:** [[TTA.dev/API Design Guide]]

---

### OpenAPI Specification

**Document APIs:**

```yaml
# openapi.yaml
openapi: 3.0.0
info:
  title: TTA.dev API
  version: 1.0.0

paths:
  /users:
    get:
      summary: List users
      responses:
        '200':
          description: List of users
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/User'

    post:
      summary: Create user
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/UserCreate'
      responses:
        '201':
          description: User created
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/User'

components:
  schemas:
    User:
      type: object
      properties:
        id:
          type: string
        name:
          type: string
        email:
          type: string
```

**See:** [[TTA.dev/OpenAPI Documentation]]

---

## Related Concepts

- [[TTA Primitives]] - API primitives
- [[Recovery]] - Error handling
- [[Performance]] - Caching patterns
- [[Examples]] - API examples
- [[Testing]] - API testing

---

## Documentation

- [[TTA Primitives/HTTPClientPrimitive]] - HTTP client (planned)
- [[TTA Primitives/RESTAPIPrimitive]] - REST client (planned)
- [[TTA.dev/API Design Guide]] - Design guidelines
- [[TTA.dev/OpenAPI Documentation]] - API documentation

---

**Tags:** #api #rest #http #integration #patterns #index-page

**Last Updated:** 2025-11-05
**Maintained by:** TTA.dev Team

- [[Project Hub]]

---
**Logseq:** [[TTA.dev/_archive/Nested_copies/Framework/Logseq/Pages/Api]]
