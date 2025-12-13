# SupabasePrimitive

**Supabase database integration primitive (planned)**

---

## Overview

SupabasePrimitive is a **planned feature** for integrating Supabase database operations into TTA.dev workflows. This page documents the design and intended implementation.

**Status:** 🚧 Planned - Not yet implemented
**Package:** [[tta-dev-primitives]] (planned integration)
**Alternative:** Use direct Supabase client for now

---

## Planned Features

### Core Capabilities

1. **Query Execution** - Execute Supabase queries
2. **Real-time Subscriptions** - Subscribe to database changes
3. **Storage Operations** - File upload/download
4. **Authentication** - User auth integration
5. **Edge Functions** - Call Supabase edge functions

### Composability

```python
# Planned API
from tta_dev_primitives.database import SupabasePrimitive

# Query primitive
query_users = SupabasePrimitive(
    operation="select",
    table="users",
    filters={"status": "active"}
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

### Using Supabase Client Directly

Until SupabasePrimitive is implemented, use the Supabase client directly:

```python
from tta_dev_primitives import WorkflowPrimitive, WorkflowContext
from supabase import create_client, Client

class CustomSupabasePrimitive(WorkflowPrimitive[dict, dict]):
    """Custom Supabase primitive."""

    def __init__(self, supabase_url: str, supabase_key: str):
        super().__init__()
        self.client: Client = create_client(supabase_url, supabase_key)

    async def _execute_impl(
        self,
        data: dict,
        context: WorkflowContext
    ) -> dict:
        """Query Supabase."""

        # Query database
        response = self.client.table(data["table"]) \
            .select("*") \
            .eq("status", "active") \
            .execute()

        return {
            "data": response.data,
            "count": len(response.data)
        }

# Use custom primitive
supabase = CustomSupabasePrimitive(
    supabase_url="https://your-project.supabase.co",
    supabase_key="your-anon-key"
)

workflow = validate >> supabase >> process
```

---

## Planned API Design

### Query Operations

```python
# SELECT
select_primitive = SupabasePrimitive(
    operation="select",
    table="users",
    columns=["id", "name", "email"],
    filters={"status": "active"},
    order_by=("created_at", "desc"),
    limit=100
)

# INSERT
insert_primitive = SupabasePrimitive(
    operation="insert",
    table="users",
    data={"name": "John", "email": "john@example.com"}
)

# UPDATE
update_primitive = SupabasePrimitive(
    operation="update",
    table="users",
    filters={"id": 123},
    data={"status": "inactive"}
)

# DELETE
delete_primitive = SupabasePrimitive(
    operation="delete",
    table="users",
    filters={"id": 123}
)
```

### Real-time Subscriptions

```python
# Subscribe to changes (planned)
subscription_primitive = SupabasePrimitive(
    operation="subscribe",
    table="messages",
    event="INSERT",
    callback=handle_new_message
)

# Use in workflow
workflow = (
    setup_subscription >>
    subscription_primitive >>
    process_events
)
```

### Storage Operations

```python
# Upload file (planned)
upload_primitive = SupabasePrimitive(
    operation="storage_upload",
    bucket="avatars",
    file_path="user-123/avatar.jpg"
)

# Download file (planned)
download_primitive = SupabasePrimitive(
    operation="storage_download",
    bucket="avatars",
    file_path="user-123/avatar.jpg"
)
```

---

## Integration Patterns

### RAG with Supabase Vector Store

```python
# Planned: RAG workflow with Supabase pgvector
from tta_dev_primitives.database import SupabasePrimitive

# Store embeddings
store_embedding = SupabasePrimitive(
    operation="vector_insert",
    table="embeddings",
    vector_column="embedding",
    metadata_columns=["text", "source"]
)

# Search similar vectors
search_similar = SupabasePrimitive(
    operation="vector_search",
    table="embeddings",
    vector_column="embedding",
    limit=5
)

# RAG workflow
rag_workflow = (
    generate_query_embedding >>
    search_similar >>
    retrieve_documents >>
    generate_response
)
```

### User Authentication Flow

```python
# Planned: Auth integration
signup_user = SupabasePrimitive(
    operation="auth_signup",
    provider="email"
)

login_user = SupabasePrimitive(
    operation="auth_login",
    provider="email"
)

# Auth workflow
auth_workflow = (
    validate_credentials >>
    login_user >>
    generate_session
)
```

---

## Configuration (Planned)

### Environment Variables

```bash
# .env file
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-key
```

### Primitive Configuration

```python
# Planned configuration
supabase_config = {
    "url": os.getenv("SUPABASE_URL"),
    "key": os.getenv("SUPABASE_ANON_KEY"),
    "options": {
        "schema": "public",
        "auto_refresh_token": True,
        "persist_session": True
    }
}

supabase_primitive = SupabasePrimitive(**supabase_config)
```

---

## Error Handling (Planned)

### Retry on Transient Failures

```python
from tta_dev_primitives.recovery import RetryPrimitive

# Wrap Supabase operations with retry
reliable_query = RetryPrimitive(
    primitive=supabase_query,
    max_retries=3,
    backoff_strategy="exponential"
)

workflow = validate >> reliable_query >> process
```

### Fallback to Cache

```python
from tta_dev_primitives.recovery import FallbackPrimitive
from tta_dev_primitives.performance import CachePrimitive

# Cache Supabase queries
cached_query = CachePrimitive(
    primitive=supabase_query,
    ttl_seconds=300
)

# Fallback chain: query → cached → default
resilient_query = FallbackPrimitive(
    primary=supabase_query,
    fallbacks=[cached_query, default_response]
)
```

---

## Testing (Planned)

### Mocking Supabase Operations

```python
import pytest
from tta_dev_primitives.testing import MockPrimitive

@pytest.mark.asyncio
async def test_supabase_workflow():
    """Test workflow with mocked Supabase."""

    # Mock Supabase primitive
    mock_supabase = MockPrimitive(
        return_value={
            "data": [
                {"id": 1, "name": "Test User"}
            ],
            "count": 1
        }
    )

    workflow = validate >> mock_supabase >> process

    result = await workflow.execute(
        {"query": "test"},
        WorkflowContext()
    )

    assert mock_supabase.call_count == 1
    assert result["count"] == 1
```

---

## Migration Guide

### From Direct Client to SupabasePrimitive

```python
# Before: Direct client usage
async def query_users(data: dict, context: WorkflowContext) -> dict:
    from supabase import create_client

    client = create_client(url, key)
    response = client.table("users").select("*").execute()

    return {"users": response.data}

# After: Using SupabasePrimitive (when available)
query_users = SupabasePrimitive(
    operation="select",
    table="users",
    columns="*"
)

workflow = validate >> query_users >> process
```

---

## Observability (Planned)

### Automatic Metrics

```python
# Planned: Automatic metrics collection
# - supabase_queries_total (counter)
# - supabase_query_duration_seconds (histogram)
# - supabase_errors_total (counter by error type)
# - supabase_connection_pool_size (gauge)

# Use in workflow - metrics collected automatically
workflow = validate >> supabase_query >> process
```

---

## Alternatives Until Implementation

### 1. Direct Supabase Client

```python
from supabase import create_client

client = create_client(url, key)

async def query_data(data: dict, context: WorkflowContext) -> dict:
    response = client.table("users").select("*").execute()
    return {"data": response.data}
```

### 2. Custom Wrapper Primitive

See "Current Workaround" section above for full example.

### 3. Generic Database Primitive

```python
# Use generic database primitive (if available)
from tta_dev_primitives.database import DatabasePrimitive

db_primitive = DatabasePrimitive(
    connection_string="postgresql://...",
    query="SELECT * FROM users WHERE status = 'active'"
)
```

---

## Contributing

Interested in implementing SupabasePrimitive?

1. **Review design:** Check [[TTA.dev/Architecture/Database Primitives]]
2. **Discuss approach:** Open GitHub issue for discussion
3. **Follow patterns:** See [[Custom Primitives Guide]]
4. **Add tests:** 100% coverage required
5. **Submit PR:** Include examples and docs

---

## Related Primitives

- [[SQLitePrimitive]] - SQLite database primitive (also planned)
- [[PostgreSQLPrimitive]] - PostgreSQL primitive (planned)
- [[DatabasePrimitive]] - Generic database primitive (planned)

---

## Related Patterns

- [[TTA.dev/Patterns/Database Integration]] - Database patterns
- [[TTA.dev/Patterns/Caching]] - Cache database queries
- [[TTA.dev/Patterns/Error Handling]] - Handle database errors

---

## Related Examples

- [[TTA.dev/Examples/Database Workflow]] - Database workflow examples (when available)
- [[TTA.dev/Examples/RAG Workflow]] - RAG with vector search

---

## External Resources

- [Supabase Documentation](https://supabase.com/docs)
- [Supabase Python Client](https://github.com/supabase-community/supabase-py)
- [Supabase Vector Search](https://supabase.com/docs/guides/ai/vector-columns)

---

**Status:** 🚧 Planned Feature
**Priority:** Medium
**Target Release:** TBD
**Tracking:** [[TTA.dev/Roadmap]]


---
**Logseq:** [[TTA.dev/_archive/Nested_copies/Framework/Logseq/Pages/Supabaseprimitive]]
