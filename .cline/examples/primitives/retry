# RetryPrimitive Examples for Cline

**Purpose:** Learn how to implement resilient retry patterns with TTA.dev's RetryPrimitive

## Example 1: Retry Unreliable API Calls

**When to Use:** External APIs occasionally fail and you need automatic retry with backoff

**Cline Prompt Example:**

```
This API call to our payment processor sometimes fails due to network issues.
Add automatic retry with exponential backoff to handle transient failures.
```

**Expected Implementation:**

```python
from tta_dev_primitives.recovery import RetryPrimitive
from tta_dev_primitives import WorkflowContext
import asyncio

class PaymentService:
    def __init__(self):
        # Retry payment API calls with exponential backoff
        self.reliable_payment_api = RetryPrimitive(
            primitive=self._call_payment_api,
            max_retries=3,
            backoff_strategy="exponential",
            initial_delay=1.0,  # Start with 1 second
            max_delay=30.0,     # Cap at 30 seconds
            jitter=True         # Add random delay to prevent thundering herd
        )

    async def process_payment(self, payment_data: dict) -> dict:
        context = WorkflowContext(
            workflow_id="payment-service",
            metadata={"amount": payment_data.get("amount", 0)}
        )
        return await self.reliable_payment_api.execute(payment_data, context)

    async def _call_payment_api(self, data: dict) -> dict:
        # Your actual payment API call implementation
        # This might raise APIError, NetworkError, etc.
        pass
```

## Example 2: Database Connection Retry

**When to Use:** Database connections occasionally timeout or become unavailable

**Cline Prompt Example:**

```
The database connection sometimes times out under load.
Implement retry logic to handle connection failures automatically.
```

**Expected Implementation:**

```python
from tta_dev_primitives.recovery import RetryPrimitive
from tta_dev_primitives import WorkflowContext
import aiosqlite

class DatabaseService:
    def __init__(self):
        # Retry database operations with fixed backoff for quick recovery
        self.cached_query = RetryPrimitive(
            primitive=self._execute_query,
            max_retries=5,
            backoff_strategy="linear",
            initial_delay=0.5,  # Start with 500ms
            multiplier=1.5,     # Increase by 50% each retry
            jitter=True
        )

    async def query_users(self, user_id: str) -> dict:
        context = WorkflowContext(
            workflow_id="db-service",
            metadata={"table": "users", "user_id": user_id}
        )
        return await self.cached_query.execute(
            {"query": "SELECT * FROM users WHERE id = ?", "params": [user_id]},
            context
        )

    async def _execute_query(self, data: dict) -> dict:
        # Your actual database query implementation
        async with aiosqlite.connect("users.db") as db:
            cursor = await db.execute(data["query"], data["params"])
            row = await cursor.fetchone()
            return dict(row) if row else {}
```

## Example 3: LLM API with Rate Limiting

**When to Use:** LLM APIs have rate limits and occasional server errors

**Cline Prompt Example:**

```
This OpenAI API call sometimes hits rate limits or server errors.
Add smart retry logic that respects rate limits and handles different error types.
```

**Expected Implementation:**

```python
from tta_dev_primitives.recovery import RetryPrimitive
from tta_dev_primitives import WorkflowContext
from tta_dev_primitives.exceptions import (
    RateLimitError,
    ServerError,
    AuthenticationError
)

class LLMService:
    def __init__(self):
        # Smart retry for LLM API calls
        self.cached_llm_call = RetryPrimitive(
            primitive=self._call_openai,
            max_retries=4,
            backoff_strategy="exponential",
            initial_delay=2.0,  # Start with 2 seconds for rate limits
            max_delay=60.0,     # Cap at 1 minute
            jitter=True,
            # Retry on specific exceptions
            retry_on_exceptions=[RateLimitError, ServerError],
            # Don't retry on these
            no_retry_exceptions=[AuthenticationError]
        )

    async def generate_text(self, prompt: str) -> str:
        context = WorkflowContext(
            workflow_id="llm-service",
            metadata={"model": "gpt-4", "prompt_length": len(prompt)}
        )
        result = await self.cached_llm_call.execute(
            {"prompt": prompt, "model": "gpt-4"},
            context
        )
        return result["text"]

    async def _call_openai(self, data: dict) -> dict:
        # Your actual OpenAI API call implementation
        # Should raise specific exceptions for different error types
        pass
```

## Example 4: File Upload with Chunk Retry

**When to Use:** Large file uploads can fail in the middle and need to resume

**Cline Prompt Example:**

```
File uploads to S3 sometimes fail mid-upload due to network issues.
Implement chunked upload with retry to handle partial failures.
```

**Expected Implementation:**

```python
from tta_dev_primitives.recovery import RetryPrimitive
from tta_dev_primitives import WorkflowContext
import aiofiles

class FileUploadService:
    def __init__(self):
        # Retry file upload operations
        self.reliable_upload = RetryPrimitive(
            primitive=self._upload_chunk,
            max_retries=3,
            backoff_strategy="exponential",
            initial_delay=1.0,
            max_delay=30.0,
            jitter=True
        )

    async def upload_file(self, file_path: str, s3_key: str) -> dict:
        context = WorkflowContext(
            workflow_id="upload-service",
            metadata={"file_path": file_path, "s3_key": s3_key}
        )

        # Read file in chunks
        async with aiofiles.open(file_path, 'rb') as f:
            chunk_size = 1024 * 1024  # 1MB chunks
            chunk_num = 0

            while True:
                chunk = await f.read(chunk_size)
                if not chunk:
                    break

                # Upload chunk with retry
                result = await self.reliable_upload.execute({
                    "chunk": chunk,
                    "chunk_num": chunk_num,
                    "s3_key": s3_key
                }, context)

                chunk_num += 1

        return {"status": "uploaded", "chunks": chunk_num}

    async def _upload_chunk(self, data: dict) -> dict:
        # Your actual S3 upload implementation
        pass
```

## Example 5: Email Sending with Retry

**When to Use:** Email services occasionally fail but messages are important

**Cline Prompt Example:**

```
Email sending sometimes fails due to spam filters or server issues.
Implement retry with different strategies to ensure important emails get through.
```

**Expected Implementation:**

```python
from tta_dev_primitives.recovery import RetryPrimitive
from tta_dev_primitives import WorkflowContext

class EmailService:
    def __init__(self):
        # Retry email sending with different providers as fallback
        self.reliable_email = RetryPrimitive(
            primitive=self._send_email,
            max_retries=3,
            backoff_strategy="linear",
            initial_delay=5.0,  # Longer delays for email
            multiplier=2.0,     # Double the delay each time
            jitter=True
        )

    async def send_important_email(self, to: str, subject: str, body: str) -> dict:
        context = WorkflowContext(
            workflow_id="email-service",
            metadata={"to": to, "subject": subject}
        )

        return await self.reliable_email.execute({
            "to": to,
            "subject": subject,
            "body": body,
            "priority": "high"
        }, context)

    async def _send_email(self, data: dict) -> dict:
        # Your actual email sending implementation
        # Try primary provider, then fallback providers
        pass
```

## Cline Detection Patterns

**RetryPrimitive Indicators:**

- "sometimes fails"
- "occasionally unavailable"
- "transient failures"
- "rate limits"
- "connection timeouts"
- "network issues"
- "retry logic"
- "handle failures"

**Cline's Response Strategy:**

1. Identify the operation that can fail
2. Assess the failure pattern (network, rate limit, etc.)
3. Choose appropriate backoff strategy:
   - `exponential` for rate limits and server errors
   - `linear` for quick recovery scenarios
   - `fixed` for simple retry scenarios
4. Configure appropriate retry count and delays
5. Add context tracking for observability

## Backoff Strategy Guidelines

**Use `exponential` when:**

- Rate limiting (e.g., API rate limits)
- Server overload scenarios
- Need to avoid thundering herd

**Use `linear` when:**

- Quick recovery scenarios
- Database connection issues
- Simple network failures

**Use `fixed` when:**

- Simple retry scenarios
- Predictable failure patterns

## Common Mistakes to Avoid

❌ **Wrong:** No retry strategy

```python
# Too simple
try:
    result = api_call()
except Exception:
    result = api_call()  # Just try twice
```

✅ **Right:** Proper retry with backoff

```python
# Robust retry strategy
reliable_call = RetryPrimitive(
    primitive=api_call,
    max_retries=3,
    backoff_strategy="exponential"
)
```

❌ **Wrong:** Retry everything

```python
# Should not retry authentication errors
retry = RetryPrimitive(primitive=api_call, max_retries=5)
```

✅ **Right:** Specific exception handling

```python
# Only retry transient failures
retry = RetryPrimitive(
    primitive=api_call,
    max_retries=3,
    retry_on_exceptions=[NetworkError, ServerError],
    no_retry_exceptions=[AuthenticationError]
)
```

---

**Next Steps:** When cline detects failure-prone operations, it should automatically suggest RetryPrimitive with appropriate backoff strategy and exception handling.
