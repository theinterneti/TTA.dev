# SQLitePrimitive

**SQLite database integration primitive (planned)**

---

## Overview

SQLitePrimitive is a **planned feature** for integrating SQLite database operations into TTA.dev workflows. This lightweight database primitive is ideal for local development, testing, and embedded applications.

**Status:** 🚧 Planned - Not yet implemented
**Package:** [[tta-dev-primitives]] (planned integration)
**Alternative:** Use sqlite3 or sqlalchemy for now

---

## Planned Features

### Core Capabilities

1. **Query Execution** - Execute SQL queries
2. **Transaction Management** - ACID transactions
3. **Schema Management** - Create/modify tables
4. **Batch Operations** - Efficient bulk inserts
5. **Connection Pooling** - Manage connections

### Composability

```python
# Planned API
from tta_dev_primitives.database import SQLitePrimitive

# Query primitive
query_users = SQLitePrimitive(
    database="app.db",
    query="SELECT * FROM users WHERE status = ?",
    params=["active"]
)

# Use in workflow
workflow = (
    validate_input >>
    query_users >>
    process_results >>
    format_output
)
```

---

## Current Workaround

### Using sqlite3 Directly

Until SQLitePrimitive is implemented, use sqlite3 directly:

```python
import sqlite3
from tta_dev_primitives import WorkflowPrimitive, WorkflowContext

class CustomSQLitePrimitive(WorkflowPrimitive[dict, dict]):
    """Custom SQLite primitive."""

    def __init__(self, database: str):
        super().__init__()
        self.database = database

    async def _execute_impl(
        self,
        data: dict,
        context: WorkflowContext
    ) -> dict:
        """Execute SQLite query."""

        conn = sqlite3.connect(self.database)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            # Execute query
            cursor.execute(data["query"], data.get("params", []))

            # Fetch results
            if data["query"].strip().upper().startswith("SELECT"):
                results = [dict(row) for row in cursor.fetchall()]
                return {"data": results, "count": len(results)}
            else:
                conn.commit()
                return {"rows_affected": cursor.rowcount}

        finally:
            conn.close()

# Use custom primitive
sqlite = CustomSQLitePrimitive(database="app.db")

workflow = validate >> sqlite >> process
```

### Using SQLAlchemy

```python
from sqlalchemy import create_engine, text
from tta_dev_primitives import WorkflowPrimitive, WorkflowContext

class SQLAlchemySQLitePrimitive(WorkflowPrimitive[dict, dict]):
    """SQLite primitive using SQLAlchemy."""

    def __init__(self, database: str):
        super().__init__()
        self.engine = create_engine(f"sqlite:///{database}")

    async def _execute_impl(
        self,
        data: dict,
        context: WorkflowContext
    ) -> dict:
        """Execute query with SQLAlchemy."""

        with self.engine.connect() as conn:
            result = conn.execute(
                text(data["query"]),
                data.get("params", {})
            )

            if result.returns_rows:
                rows = [dict(row) for row in result]
                return {"data": rows, "count": len(rows)}
            else:
                conn.commit()
                return {"rows_affected": result.rowcount}
```

---

## Planned API Design

### Query Operations

```python
# SELECT
select_primitive = SQLitePrimitive(
    database="app.db",
    query="SELECT * FROM users WHERE status = ?",
    params=["active"]
)

# INSERT
insert_primitive = SQLitePrimitive(
    database="app.db",
    query="INSERT INTO users (name, email) VALUES (?, ?)",
    params=["John Doe", "john@example.com"]
)

# UPDATE
update_primitive = SQLitePrimitive(
    database="app.db",
    query="UPDATE users SET status = ? WHERE id = ?",
    params=["inactive", 123]
)

# DELETE
delete_primitive = SQLitePrimitive(
    database="app.db",
    query="DELETE FROM users WHERE id = ?",
    params=[123]
)
```

### Transaction Management

```python
# Planned: Transaction primitive
from tta_dev_primitives.database import SQLiteTransaction

with SQLiteTransaction(database="app.db") as transaction:
    workflow = (
        insert_user >>
        create_profile >>
        send_notification
    )

    # All operations in transaction
    result = await workflow.execute(data, context)

    # Auto-commit on success, rollback on error
```

### Batch Operations

```python
# Planned: Batch insert
batch_insert = SQLitePrimitive(
    database="app.db",
    query="INSERT INTO users (name, email) VALUES (?, ?)",
    batch=True
)

# Use with multiple records
data = {
    "records": [
        ["Alice", "alice@example.com"],
        ["Bob", "bob@example.com"],
        ["Charlie", "charlie@example.com"]
    ]
}

result = await batch_insert.execute(data, context)
# Result: {"rows_affected": 3}
```

---

## Integration Patterns

### Local Cache with SQLite

```python
# Planned: Use SQLite as local cache
from tta_dev_primitives.database import SQLitePrimitive

# Check cache
check_cache = SQLitePrimitive(
    database="cache.db",
    query="SELECT result FROM cache WHERE key = ?",
    params_from_data=["cache_key"]
)

# Store in cache
store_cache = SQLitePrimitive(
    database="cache.db",
    query="INSERT OR REPLACE INTO cache (key, result, expires_at) VALUES (?, ?, ?)"
)

# Workflow with cache
workflow = (
    check_cache >>
    ConditionalPrimitive(
        condition=lambda d, c: d.get("data"),
        then_primitive=return_cached,
        else_primitive=(
            compute_result >>
            store_cache >>
            return_result
        )
    )
)
```

### Embedding Storage

```python
# Planned: Store embeddings in SQLite
store_embedding = SQLitePrimitive(
    database="embeddings.db",
    query="""
        INSERT INTO embeddings (text, embedding, metadata)
        VALUES (?, ?, ?)
    """
)

# Search embeddings (with vector extension)
search_embeddings = SQLitePrimitive(
    database="embeddings.db",
    query="""
        SELECT text, metadata,
               vector_distance(embedding, ?) as distance
        FROM embeddings
        ORDER BY distance
        LIMIT ?
    """
)
```

---

## Configuration (Planned)

### Database Configuration

```python
# Planned configuration
sqlite_config = {
    "database": "app.db",
    "options": {
        "check_same_thread": False,  # For threading
        "timeout": 10.0,              # Connection timeout
        "isolation_level": "DEFERRED" # Transaction isolation
    }
}

sqlite_primitive = SQLitePrimitive(**sqlite_config)
```

### Connection Pooling

```python
# Planned: Connection pool
from tta_dev_primitives.database import SQLitePool

pool = SQLitePool(
    database="app.db",
    min_size=2,
    max_size=10,
    timeout=30.0
)

sqlite_primitive = SQLitePrimitive(pool=pool)
```

---

## Error Handling (Planned)

### Retry on Lock Timeout

```python
from tta_dev_primitives.recovery import RetryPrimitive

# SQLite can have lock contention
reliable_write = RetryPrimitive(
    primitive=sqlite_write,
    max_retries=5,
    backoff_strategy="exponential",
    initial_delay=0.1  # Short delay for SQLite
)

workflow = validate >> reliable_write >> confirm
```

### Fallback to In-Memory

```python
from tta_dev_primitives.recovery import FallbackPrimitive

# Primary: File-based SQLite
primary_db = SQLitePrimitive(database="app.db")

# Fallback: In-memory SQLite
fallback_db = SQLitePrimitive(database=":memory:")

resilient_db = FallbackPrimitive(
    primary=primary_db,
    fallbacks=[fallback_db]
)
```

---

## Testing (Planned)

### Testing with In-Memory Database

```python
import pytest
from tta_dev_primitives import WorkflowContext

@pytest.fixture
async def test_db():
    """Create test database."""
    db = SQLitePrimitive(database=":memory:")

    # Setup schema
    await db.execute({
        "query": """
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                name TEXT,
                email TEXT UNIQUE
            )
        """
    }, WorkflowContext())

    return db

@pytest.mark.asyncio
async def test_sqlite_workflow(test_db):
    """Test workflow with SQLite."""

    # Insert test data
    insert = SQLitePrimitive(
        database=":memory:",
        query="INSERT INTO users (name, email) VALUES (?, ?)",
        params=["Test User", "test@example.com"]
    )

    workflow = validate >> insert >> verify

    result = await workflow.execute({"test": "data"}, WorkflowContext())

    assert result["rows_affected"] == 1
```

---

## Migration Guide

### From sqlite3 to SQLitePrimitive

```python
# Before: Direct sqlite3 usage
async def query_users(data: dict, context: WorkflowContext) -> dict:
    import sqlite3

    conn = sqlite3.connect("app.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE status = ?", ["active"])
    results = cursor.fetchall()
    conn.close()

    return {"users": results}

# After: Using SQLitePrimitive (when available)
query_users = SQLitePrimitive(
    database="app.db",
    query="SELECT * FROM users WHERE status = ?",
    params=["active"]
)

workflow = validate >> query_users >> process
```

---

## Observability (Planned)

### Automatic Metrics

```python
# Planned: Automatic metrics collection
# - sqlite_queries_total (counter by query type)
# - sqlite_query_duration_seconds (histogram)
# - sqlite_errors_total (counter by error type)
# - sqlite_connection_pool_size (gauge)
# - sqlite_database_size_bytes (gauge)

# Use in workflow - metrics collected automatically
workflow = validate >> sqlite_query >> process
```

---

## Use Cases

### 1. Local Development

```python
# Use SQLite for local dev, PostgreSQL for production
if os.getenv("ENV") == "production":
    db = PostgreSQLPrimitive(connection_string=prod_url)
else:
    db = SQLitePrimitive(database="dev.db")

workflow = validate >> db >> process
```

### 2. Embedded Applications

```python
# Desktop app with embedded database
app_db = SQLitePrimitive(
    database=os.path.expanduser("~/.myapp/data.db")
)

workflow = (
    load_user_settings >>
    app_db >>
    apply_preferences
)
```

### 3. Testing

```python
# In-memory database for tests
test_db = SQLitePrimitive(database=":memory:")

# Fast, isolated tests
@pytest.mark.asyncio
async def test_workflow():
    result = await workflow.execute(data, context)
    assert result["success"]
```

### 4. Edge Computing

```python
# SQLite for edge devices
edge_db = SQLitePrimitive(
    database="/data/edge.db"
)

# Sync to cloud periodically
workflow = (
    collect_sensor_data >>
    edge_db >>
    sync_to_cloud
)
```

---

## Performance Tips (Planned)

### 1. Use Write-Ahead Logging

```python
# Planned: WAL mode for better concurrency
sqlite_config = {
    "database": "app.db",
    "pragma": {
        "journal_mode": "WAL",
        "synchronous": "NORMAL"
    }
}
```

### 2. Batch Inserts

```python
# Planned: Batch operations
batch_insert = SQLitePrimitive(
    database="app.db",
    query="INSERT INTO logs (message, timestamp) VALUES (?, ?)",
    batch=True,
    batch_size=1000  # Insert 1000 at a time
)
```

### 3. Index Optimization

```python
# Planned: Index creation
create_index = SQLitePrimitive(
    database="app.db",
    query="CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)"
)
```

---

## Alternatives Until Implementation

### 1. Direct sqlite3

```python
import sqlite3

conn = sqlite3.connect("app.db")
cursor = conn.cursor()
cursor.execute("SELECT * FROM users")
results = cursor.fetchall()
conn.close()
```

### 2. SQLAlchemy

```python
from sqlalchemy import create_engine

engine = create_engine("sqlite:///app.db")
with engine.connect() as conn:
    result = conn.execute("SELECT * FROM users")
    rows = result.fetchall()
```

### 3. Custom Wrapper Primitive

See "Current Workaround" section above for full examples.

---

## Contributing

Interested in implementing SQLitePrimitive?

1. **Review design:** Check [[TTA.dev/Architecture/Database Primitives]]
2. **Discuss approach:** Open GitHub issue for discussion
3. **Follow patterns:** See [[Custom Primitives Guide]]
4. **Add tests:** 100% coverage required (use :memory: database)
5. **Submit PR:** Include examples and docs

---

## Related Primitives

- [[SupabasePrimitive]] - Supabase database primitive (also planned)
- [[PostgreSQLPrimitive]] - PostgreSQL primitive (planned)
- [[DatabasePrimitive]] - Generic database primitive (planned)

---

## Related Patterns

- [[TTA.dev/Patterns/Database Integration]] - Database patterns
- [[TTA.dev/Patterns/Caching]] - Cache with SQLite
- [[TTA.dev/Patterns/Error Handling]] - Handle database errors

---

## Related Examples

- [[TTA.dev/Examples/Database Workflow]] - Database workflow examples (when available)
- [[TTA.dev/Examples/Local Cache]] - SQLite caching patterns

---

## External Resources

- [SQLite Documentation](https://www.sqlite.org/docs.html)
- [Python sqlite3 Module](https://docs.python.org/3/library/sqlite3.html)
- [SQLAlchemy SQLite](https://docs.sqlalchemy.org/en/20/dialects/sqlite.html)

---

**Status:** 🚧 Planned Feature
**Priority:** Medium
**Target Release:** TBD
**Tracking:** [[TTA.dev/Roadmap]]


---
**Logseq:** [[TTA.dev/Logseq/Pages/Sqliteprimitive]]
