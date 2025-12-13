# Database

**Tag page for database integration, primitives, and patterns**

---

## Overview

**Database** integration in TTA.dev includes:
- 🗄️ Database primitives (planned)
- 🔗 Connection management
- 💾 Data persistence patterns
- 🔍 Query optimization
- 🔄 Transaction handling

**Goal:** Seamless database integration with workflow primitives.

**See:** [[TTA Primitives]], [[Infrastructure]]

---

## Pages Tagged with #Database

{{query (page-tags [[Database]])}}

---

## Planned Database Support

### 1. Supabase Integration

**Supabase Primitive (Planned):**

```python
from tta_dev_primitives import WorkflowPrimitive, WorkflowContext
from supabase import create_client, Client

class SupabasePrimitive(WorkflowPrimitive):
    """Supabase database operations."""

    def __init__(self, url: str, key: str):
        super().__init__()
        self.client: Client = create_client(url, key)

    async def _execute(self, data: dict, context: WorkflowContext) -> dict:
        """Execute Supabase operation."""
        operation = data.get("operation", "select")
        table = data.get("table")

        if operation == "select":
            response = self.client.table(table).select("*").execute()
            return {"data": response.data}

        elif operation == "insert":
            response = self.client.table(table).insert(data["record"]).execute()
            return {"data": response.data}

        elif operation == "update":
            response = (
                self.client.table(table)
                .update(data["record"])
                .eq("id", data["id"])
                .execute()
            )
            return {"data": response.data}

        elif operation == "delete":
            response = self.client.table(table).delete().eq("id", data["id"]).execute()
            return {"success": True}

        raise ValueError(f"Unknown operation: {operation}")
```

**Use cases:**
- Real-time data subscriptions
- Row-level security
- PostgreSQL features
- Built-in auth

**See:** [[TTA.dev/Supabase Integration]] (planned)

---

### 2. SQLite Integration

**SQLite Primitive (Planned):**

```python
import aiosqlite
from tta_dev_primitives import WorkflowPrimitive, WorkflowContext

class SQLitePrimitive(WorkflowPrimitive):
    """SQLite database operations."""

    def __init__(self, db_path: str):
        super().__init__()
        self.db_path = db_path

    async def _execute(self, data: dict, context: WorkflowContext) -> dict:
        """Execute SQLite operation."""
        async with aiosqlite.connect(self.db_path) as db:
            operation = data.get("operation", "select")

            if operation == "select":
                async with db.execute(
                    data["query"],
                    data.get("params", ())
                ) as cursor:
                    rows = await cursor.fetchall()
                    return {"data": rows}

            elif operation in ("insert", "update", "delete"):
                await db.execute(data["query"], data.get("params", ()))
                await db.commit()
                return {"success": True, "rowcount": db.total_changes}

            raise ValueError(f"Unknown operation: {operation}")
```

**Use cases:**
- Local development
- Embedded databases
- Testing
- Single-file storage

**See:** [[TTA.dev/SQLite Integration]] (planned)

---

### 3. PostgreSQL Integration

**PostgreSQL Primitive (Planned):**

```python
import asyncpg
from tta_dev_primitives import WorkflowPrimitive, WorkflowContext

class PostgreSQLPrimitive(WorkflowPrimitive):
    """PostgreSQL database operations."""

    def __init__(self, dsn: str):
        super().__init__()
        self.dsn = dsn
        self.pool = None

    async def initialize(self):
        """Initialize connection pool."""
        self.pool = await asyncpg.create_pool(self.dsn)

    async def _execute(self, data: dict, context: WorkflowContext) -> dict:
        """Execute PostgreSQL operation."""
        if self.pool is None:
            await self.initialize()

        async with self.pool.acquire() as conn:
            operation = data.get("operation", "select")

            if operation == "select":
                rows = await conn.fetch(
                    data["query"],
                    *data.get("params", ())
                )
                return {"data": [dict(row) for row in rows]}

            elif operation in ("insert", "update", "delete"):
                result = await conn.execute(
                    data["query"],
                    *data.get("params", ())
                )
                return {"success": True, "status": result}

            elif operation == "transaction":
                async with conn.transaction():
                    results = []
                    for query in data["queries"]:
                        result = await conn.execute(
                            query["sql"],
                            *query.get("params", ())
                        )
                        results.append(result)
                return {"success": True, "results": results}

            raise ValueError(f"Unknown operation: {operation}")
```

**Use cases:**
- Production databases
- Complex queries
- ACID transactions
- Full PostgreSQL features

**See:** [[TTA.dev/PostgreSQL Integration]] (planned)

---

## Database Patterns

### Pattern: Database Workflow

**Complete database workflow:**

```python
async def database_workflow():
    """Database operations with error handling."""
    # Setup
    db = PostgreSQLPrimitive(dsn="postgresql://...")
    await db.initialize()

    # Workflow with retry
    workflow = RetryPrimitive(
        primitive=(
            validate_input >>
            db >>
            transform_result >>
            cache_result
        ),
        max_retries=3,
        backoff_strategy="exponential"
    )

    # Execute
    context = WorkflowContext(correlation_id="db-op-123")
    result = await workflow.execute(
        {
            "operation": "select",
            "query": "SELECT * FROM users WHERE active = $1",
            "params": (True,)
        },
        context
    )

    return result
```

---

### Pattern: Transaction Handling

**Multi-step transaction:**

```python
async def transfer_funds(from_account: str, to_account: str, amount: float):
    """Transfer funds between accounts."""
    db = PostgreSQLPrimitive(dsn="postgresql://...")

    workflow = db

    # Transaction workflow
    result = await workflow.execute(
        {
            "operation": "transaction",
            "queries": [
                {
                    "sql": "UPDATE accounts SET balance = balance - $1 WHERE id = $2",
                    "params": (amount, from_account)
                },
                {
                    "sql": "UPDATE accounts SET balance = balance + $1 WHERE id = $2",
                    "params": (amount, to_account)
                },
                {
                    "sql": "INSERT INTO transactions (from_account, to_account, amount) VALUES ($1, $2, $3)",
                    "params": (from_account, to_account, amount)
                }
            ]
        },
        WorkflowContext()
    )

    return result
```

---

### Pattern: Query Caching

**Cache expensive queries:**

```python
async def cached_database_query():
    """Database query with caching."""
    # Database primitive
    db = PostgreSQLPrimitive(dsn="postgresql://...")

    # Wrap with cache
    cached_db = CachePrimitive(
        primitive=db,
        ttl_seconds=3600,  # Cache for 1 hour
        max_size=1000,
        key_fn=lambda data, ctx: f"{data['query']}:{data.get('params', '')}"
    )

    # Use cached version
    result = await cached_db.execute(
        {
            "operation": "select",
            "query": "SELECT * FROM products WHERE category = $1",
            "params": ("electronics",)
        },
        context
    )

    return result
```

**Benefits:**
- Reduce database load
- Faster response times
- Lower costs
- Better scalability

---

## Database Best Practices

### ✅ DO

**Use Connection Pools:**
```python
# ✅ Good: Connection pool
pool = await asyncpg.create_pool(dsn)
async with pool.acquire() as conn:
    await conn.fetch("SELECT * FROM users")

# Reuses connections efficiently
```

**Use Parameterized Queries:**
```python
# ✅ Good: Parameterized
await conn.fetch(
    "SELECT * FROM users WHERE id = $1",
    user_id
)

# ❌ Bad: String formatting (SQL injection!)
await conn.fetch(
    f"SELECT * FROM users WHERE id = {user_id}"
)
```

**Handle Errors Gracefully:**
```python
# ✅ Good: Error handling
try:
    result = await db.execute(query)
except asyncpg.UniqueViolationError:
    # Handle duplicate key
    return {"error": "Record already exists"}
except asyncpg.PostgresError as e:
    # Handle other database errors
    logger.error(f"Database error: {e}")
    return {"error": "Database operation failed"}
```

---

### ❌ DON'T

**Don't Store Passwords in Code:**
```python
# ❌ Bad: Hardcoded credentials
dsn = "postgresql://user:password@localhost/db"

# ✅ Good: Environment variables
import os
dsn = os.environ["DATABASE_URL"]
```

**Don't Leave Connections Open:**
```python
# ❌ Bad: Connection leak
conn = await asyncpg.connect(dsn)
await conn.fetch("SELECT * FROM users")
# Forgot to close!

# ✅ Good: Context manager
async with pool.acquire() as conn:
    await conn.fetch("SELECT * FROM users")
# Automatically closed
```

---

## Database Metrics

### Query Performance

```promql
# Query duration P95
histogram_quantile(0.95, database_query_duration_seconds)

# Query rate
rate(database_queries_total[5m])

# Error rate
rate(database_errors_total[5m]) /
rate(database_queries_total[5m])

# Connection pool usage
database_pool_connections_active /
database_pool_connections_total
```

**Targets:**
- Query duration P95: <100ms
- Error rate: <1%
- Pool usage: 50-80%

---

## Current Database Usage

### MemoryPrimitive Storage

**In-memory and Redis storage:**

```python
from tta_dev_primitives.performance import MemoryPrimitive

# In-memory (default)
memory = MemoryPrimitive(max_size=1000)

# Redis (optional, graceful fallback)
memory = MemoryPrimitive(
    redis_url="redis://localhost:6379",
    enable_redis=True
)

# Same API, different backends
await memory.add("key", {"data": "value"})
result = await memory.get("key")
```

**See:** [[TTA Primitives/MemoryPrimitive]]

---

## Future Database Work

### Planned Primitives

**Coming soon:**
- ✅ MemoryPrimitive (Redis/in-memory) - **COMPLETED**
- 🚧 PostgreSQLPrimitive - In planning
- 🚧 SQLitePrimitive - In planning
- 🚧 SupabasePrimitive - In planning
- 🚧 TransactionPrimitive - In planning
- 🚧 MigrationPrimitive - In planning

**See:** [[TTA.dev/Roadmap]], [[TTA.dev/Database Roadmap]]

---

### Research Areas

**Investigating:**
- Vector databases (Qdrant, Weaviate)
- Time-series databases (TimescaleDB)
- Graph databases (Neo4j)
- Cache databases (Redis, Memcached)
- Document databases (MongoDB)

**See:** [[TTA.dev/Database Research]]

---

## Related Concepts

- [[TTA Primitives]] - Primitive patterns
- [[Performance]] - Performance primitives
- [[Infrastructure]] - Infrastructure setup
- [[Production]] - Production patterns
- [[Testing]] - Database testing

---

## Documentation

- [[TTA Primitives/MemoryPrimitive]] - Memory storage (current)
- [[TTA.dev/Database Roadmap]] - Future plans
- [[TTA.dev/Supabase Integration]] - Supabase guide (planned)
- [[TTA.dev/PostgreSQL Integration]] - PostgreSQL guide (planned)
- [[TTA.dev/SQLite Integration]] - SQLite guide (planned)

---

**Tags:** #database #persistence #storage #integration #primitives #index-page

**Last Updated:** 2025-11-05
**Maintained by:** TTA.dev Team

- [[Project Hub]]

---
**Logseq:** [[TTA.dev/_archive/Nested_copies/Framework/Logseq/Pages/Database]]
