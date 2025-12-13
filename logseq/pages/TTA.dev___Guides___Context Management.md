# Context Management Guide

**Master WorkflowContext for observability and state management**

type:: Guide
audience:: intermediate-users
difficulty:: intermediate
estimated-time:: 15 minutes
status:: Complete
related:: [[TTA Primitives]], [[TTA.dev/Guides/Observability]], [[TTA.dev/Guides/First Workflow]]
prerequisites:: [[TTA.dev/Guides/Beginner Quickstart]]

---

## 🎯 What You'll Learn

- ✅ What WorkflowContext is and why it matters
- ✅ How to create and configure contexts
- ✅ Context propagation across primitives
- ✅ Using correlation IDs for tracing
- ✅ Managing metadata and state
- ✅ Best practices for production

---

## 📚 Understanding WorkflowContext

**WorkflowContext is the carrier of state and metadata across your workflow.**

Think of it as a "request context" that follows your data through every primitive:

```python
from tta_dev_primitives import WorkflowContext

context = WorkflowContext(
    correlation_id="request-12345",     # Track this request
    data={"user_id": "user-789"}        # Carry metadata
)
```

### Why Context Matters

| Without Context | With Context |
|----------------|--------------|
| ❌ No tracing across primitives | ✅ Full distributed tracing |
| ❌ Can't correlate logs | ✅ Logs linked by correlation_id |
| ❌ No request tracking | ✅ Track requests end-to-end |
| ❌ Hard to debug | ✅ Easy to trace issues |

---

## 🏗️ WorkflowContext Basics

### Creating a Context

```python
from tta_dev_primitives import WorkflowContext

# Minimal context
context = WorkflowContext()

# With correlation ID (recommended)
context = WorkflowContext(
    correlation_id="req-abc-123"
)

# With metadata
context = WorkflowContext(
    correlation_id="req-abc-123",
    data={
        "user_id": "user-789",
        "request_type": "analysis",
        "priority": "high"
    }
)
```

### Accessing Context Data

```python
class MyPrimitive(WorkflowPrimitive[dict, dict]):
    async def _execute_impl(self, input_data: dict, context: WorkflowContext) -> dict:
        # Read correlation ID
        correlation_id = context.correlation_id

        # Read metadata
        user_id = context.data.get("user_id")

        # Use in logging
        logger.info(
            "Processing request",
            extra={
                "correlation_id": correlation_id,
                "user_id": user_id
            }
        )

        return {"status": "processed"}
```

---

## 🔗 Context Propagation

Context automatically flows through your workflow:

```python
workflow = step1 >> step2 >> step3

# Context is passed to ALL primitives
context = WorkflowContext(correlation_id="req-001")
result = await workflow.execute(input_data, context)
```

### Propagation Flow

```
Input + Context
      ↓
   Step 1 (receives context)
      ↓
   Step 2 (same context)
      ↓
   Step 3 (same context)
      ↓
   Output
```

Every primitive in the chain receives the **same context object**.

---

## 🆔 Correlation IDs

Correlation IDs link related operations across your system.

### Generating Correlation IDs

```python
import uuid
from tta_dev_primitives import WorkflowContext

# UUID-based (recommended)
context = WorkflowContext(
    correlation_id=str(uuid.uuid4())
)
# Result: "a1b2c3d4-e5f6-7890-abcd-ef1234567890"

# Timestamp-based
import time
context = WorkflowContext(
    correlation_id=f"req-{int(time.time()*1000)}"
)
# Result: "req-1698765432100"

# Semantic
context = WorkflowContext(
    correlation_id=f"user-{user_id}-action-{action_type}-{timestamp}"
)
# Result: "user-789-action-query-1698765432"
```

### Using in FastAPI

```python
from fastapi import FastAPI, Request
from tta_dev_primitives import WorkflowContext
import uuid

app = FastAPI()

@app.post("/process")
async def process_request(request: Request, data: dict):
    # Generate or extract correlation ID
    correlation_id = request.headers.get(
        "X-Correlation-ID",
        str(uuid.uuid4())
    )

    # Create context
    context = WorkflowContext(
        correlation_id=correlation_id,
        data={
            "user_id": request.headers.get("X-User-ID"),
            "ip": request.client.host
        }
    )

    # Execute workflow
    result = await workflow.execute(data, context)

    # Return correlation ID in response
    return {
        "result": result,
        "correlation_id": correlation_id
    }
```

---

## 📊 Managing Metadata

Use `context.data` to carry metadata through your workflow.

### Common Metadata Patterns

```python
# User information
context = WorkflowContext(
    correlation_id="req-001",
    data={
        "user_id": "user-789",
        "user_email": "user@example.com",
        "user_role": "admin"
    }
)

# Request metadata
context = WorkflowContext(
    correlation_id="req-001",
    data={
        "request_type": "llm_query",
        "priority": "high",
        "timeout": 30.0,
        "retry_count": 0
    }
)

# Tenant information (multi-tenant apps)
context = WorkflowContext(
    correlation_id="req-001",
    data={
        "tenant_id": "tenant-123",
        "tenant_name": "Acme Corp",
        "subscription_tier": "premium"
    }
)
```

### Reading and Updating Metadata

```python
class MetadataAwarePrimitive(WorkflowPrimitive[dict, dict]):
    async def _execute_impl(self, input_data: dict, context: WorkflowContext) -> dict:
        # Read metadata
        user_id = context.data.get("user_id")
        priority = context.data.get("priority", "normal")

        # Update metadata (for next primitives)
        context.data["processed_by"] = self.__class__.__name__
        context.data["processed_at"] = datetime.now().isoformat()

        # Use metadata in logic
        if priority == "high":
            # Use faster model
            model = "gpt-4-turbo"
        else:
            model = "gpt-3.5-turbo"

        return {
            "user_id": user_id,
            "model_used": model,
            "result": "processed"
        }
```

---

## 🔍 Observability with Context

Context enables powerful observability patterns.

### Structured Logging

```python
import structlog
from tta_dev_primitives import WorkflowContext, WorkflowPrimitive

logger = structlog.get_logger(__name__)

class LoggingPrimitive(WorkflowPrimitive[dict, dict]):
    async def _execute_impl(self, input_data: dict, context: WorkflowContext) -> dict:
        # All logs include correlation ID
        logger.info(
            "primitive_started",
            correlation_id=context.correlation_id,
            user_id=context.data.get("user_id"),
            primitive=self.__class__.__name__
        )

        try:
            # Process
            result = {"status": "success"}

            logger.info(
                "primitive_completed",
                correlation_id=context.correlation_id,
                status="success"
            )

            return result

        except Exception as e:
            logger.error(
                "primitive_failed",
                correlation_id=context.correlation_id,
                error=str(e),
                exc_info=True
            )
            raise
```

### OpenTelemetry Integration

```python
from opentelemetry import trace
from tta_dev_primitives import WorkflowContext, WorkflowPrimitive

tracer = trace.get_tracer(__name__)

class TracedPrimitive(WorkflowPrimitive[dict, dict]):
    async def _execute_impl(self, input_data: dict, context: WorkflowContext) -> dict:
        # Create span with correlation ID
        with tracer.start_as_current_span(
            "traced_primitive",
            attributes={
                "correlation_id": context.correlation_id,
                "user_id": context.data.get("user_id"),
                "primitive": self.__class__.__name__
            }
        ) as span:
            # Process
            result = {"status": "success"}

            # Add events
            span.add_event("processing_started")

            # Add result attributes
            span.set_attribute("result_status", result["status"])

            return result
```

---

## 🎯 Production Patterns

### Pattern 1: Request-Scoped Context

Create new context for each HTTP request:

```python
from fastapi import FastAPI, Request
from tta_dev_primitives import WorkflowContext
import uuid

app = FastAPI()

@app.middleware("http")
async def add_correlation_id(request: Request, call_next):
    # Generate correlation ID
    correlation_id = str(uuid.uuid4())
    request.state.correlation_id = correlation_id

    # Add to response headers
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = correlation_id

    return response

@app.post("/process")
async def process(request: Request, data: dict):
    # Create request-scoped context
    context = WorkflowContext(
        correlation_id=request.state.correlation_id,
        data={
            "user_id": request.headers.get("X-User-ID"),
            "ip": request.client.host,
            "path": request.url.path
        }
    )

    # Execute workflow
    result = await workflow.execute(data, context)
    return result
```

### Pattern 2: Tenant Isolation

Use context for multi-tenant applications:

```python
class TenantAwarePrimitive(WorkflowPrimitive[dict, dict]):
    async def _execute_impl(self, input_data: dict, context: WorkflowContext) -> dict:
        # Extract tenant ID from context
        tenant_id = context.data.get("tenant_id")

        if not tenant_id:
            raise ValueError("Tenant ID required")

        # Use tenant-specific configuration
        config = await get_tenant_config(tenant_id)

        # Process with tenant isolation
        result = await process_for_tenant(input_data, config)

        return result
```

### Pattern 3: Error Context

Enrich errors with context:

```python
class ErrorEnrichedPrimitive(WorkflowPrimitive[dict, dict]):
    async def _execute_impl(self, input_data: dict, context: WorkflowContext) -> dict:
        try:
            return await self.process(input_data)
        except Exception as e:
            # Enrich error with context
            raise RuntimeError(
                f"Processing failed for correlation_id={context.correlation_id}, "
                f"user_id={context.data.get('user_id')}"
            ) from e
```

### Pattern 4: Context Inheritance

Child operations inherit parent context:

```python
async def parent_workflow(data: dict):
    # Parent context
    parent_context = WorkflowContext(
        correlation_id="parent-001",
        data={"source": "parent"}
    )

    # Child workflows inherit correlation ID
    child_context = WorkflowContext(
        correlation_id=parent_context.correlation_id,  # Same ID!
        data={
            **parent_context.data,
            "child_id": "child-001"
        }
    )

    # Both use same correlation ID for tracing
    parent_result = await parent_primitive.execute(data, parent_context)
    child_result = await child_primitive.execute(parent_result, child_context)

    return child_result
```

---

## 🔒 Security Considerations

### Don't Store Sensitive Data

```python
# ❌ BAD: Storing passwords in context
context = WorkflowContext(
    correlation_id="req-001",
    data={
        "password": "secret123",  # NEVER DO THIS
        "api_key": "key-xyz"      # NEVER DO THIS
    }
)

# ✅ GOOD: Store only IDs and references
context = WorkflowContext(
    correlation_id="req-001",
    data={
        "user_id": "user-789",       # OK
        "credential_ref": "cred-id"  # OK - reference, not value
    }
)
```

### Audit Logging

```python
class AuditedPrimitive(WorkflowPrimitive[dict, dict]):
    async def _execute_impl(self, input_data: dict, context: WorkflowContext) -> dict:
        # Log access with context
        await audit_log.record(
            event="data_access",
            user_id=context.data.get("user_id"),
            correlation_id=context.correlation_id,
            resource=input_data.get("resource_id"),
            timestamp=datetime.now()
        )

        return {"status": "success"}
```

---

## 🎓 Advanced Patterns

### Context Middleware

```python
class ContextEnrichmentPrimitive(WorkflowPrimitive[dict, dict]):
    """Enriches context before passing to next primitive."""

    async def _execute_impl(self, input_data: dict, context: WorkflowContext) -> dict:
        # Add system information
        context.data["hostname"] = socket.gethostname()
        context.data["timestamp"] = datetime.now().isoformat()

        # Add performance metadata
        context.data["start_time"] = time.time()

        return input_data

# Use as first primitive in workflow
workflow = (
    ContextEnrichmentPrimitive() >>
    actual_processing_primitive >>
    result_primitive
)
```

### Context Validation

```python
class ContextValidationPrimitive(WorkflowPrimitive[dict, dict]):
    """Validates required context fields."""

    def __init__(self, required_fields: list[str]):
        super().__init__()
        self.required_fields = required_fields

    async def _execute_impl(self, input_data: dict, context: WorkflowContext) -> dict:
        # Validate correlation ID
        if not context.correlation_id:
            raise ValueError("Correlation ID required")

        # Validate required metadata
        for field in self.required_fields:
            if field not in context.data:
                raise ValueError(f"Required context field missing: {field}")

        return input_data

# Use in workflow
workflow = (
    ContextValidationPrimitive(required_fields=["user_id", "tenant_id"]) >>
    processing_primitive
)
```

---

## ✅ Best Practices

### DO ✅

- Generate unique correlation IDs for each request
- Include correlation IDs in all logs and traces
- Use context for tenant isolation
- Store only non-sensitive metadata
- Propagate context through entire workflow
- Include correlation IDs in API responses

### DON'T ❌

- Store passwords or API keys in context
- Mutate context.data without documentation
- Create new contexts mid-workflow (breaks tracing)
- Use correlation IDs as authentication tokens
- Store large objects in context.data

---

## 🆘 Troubleshooting

### Issue: "Correlation ID not showing in logs"

```python
# Solution: Include correlation_id in logger.bind()
import structlog

logger = structlog.get_logger(__name__)

class MyPrimitive(WorkflowPrimitive[dict, dict]):
    async def _execute_impl(self, input_data: dict, context: WorkflowContext) -> dict:
        # Bind correlation ID to logger
        bound_logger = logger.bind(correlation_id=context.correlation_id)
        bound_logger.info("Processing started")  # Will include correlation_id

        return {"status": "success"}
```

### Issue: "Context data not accessible in primitive"

```python
# Solution: Access via context parameter, not global
class MyPrimitive(WorkflowPrimitive[dict, dict]):
    async def _execute_impl(self, input_data: dict, context: WorkflowContext) -> dict:
        # ✅ CORRECT: Access via parameter
        user_id = context.data.get("user_id")

        # ❌ WRONG: Don't use global context
        # user_id = global_context.data.get("user_id")

        return {"user_id": user_id}
```

---

## 📋 Checklist

Context management checklist:

- [ ] Unique correlation ID for each request
- [ ] Correlation ID in all logs
- [ ] Correlation ID in error messages
- [ ] Correlation ID in API responses
- [ ] Required metadata validated
- [ ] No sensitive data in context
- [ ] Context propagates through workflow
- [ ] OpenTelemetry integration configured
- [ ] Audit logging includes correlation IDs
- [ ] Documentation updated with context usage

---

## 🎯 Next Steps

### Learn More

- [[TTA.dev/Guides/Observability]] - Full observability setup
- [[TTA.dev/Guides/Error Handling Patterns]] - Error handling with context
- [[TTA Primitives]] - All primitives use context

### Related Topics

- OpenTelemetry tracing
- Structured logging
- Multi-tenant architecture
- Request correlation

---

**Last Updated:** October 31, 2025
**Difficulty:** Intermediate
**Estimated Time:** 15 minutes
**Prerequisites:** Beginner Quickstart

**Next Guide:** [[TTA.dev/Guides/Observability]]


---
**Logseq:** [[TTA.dev/Logseq/Pages/Tta.dev___guides___context management]]
