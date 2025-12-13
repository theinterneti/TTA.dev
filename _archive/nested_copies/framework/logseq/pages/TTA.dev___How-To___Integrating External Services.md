# How-To: Integrating External Services

type:: [[How-To]]
category:: [[Integration]]
difficulty:: [[Intermediate]]
estimated-time:: 45 minutes
target-audience:: [[Backend Developers]], [[Integration Engineers]], [[API Developers]]
primitives-used:: [[RetryPrimitive]], [[FallbackPrimitive]], [[TimeoutPrimitive]], [[CompensationPrimitive]]

---

## Overview

- id:: integrating-external-services-overview
  **Integrating external services** (APIs, databases, webhooks) requires careful error handling, retries, and fallback strategies. This guide shows you how to wrap external service calls with TTA.dev primitives to build resilient integrations that handle failures gracefully and maintain data consistency.

---

## Prerequisites

{{embed ((prerequisites-full))}}

**Should have read:**
- [[TTA.dev/Guides/Error Handling Patterns]] - Recovery strategies
- [[TTA.dev/How-To/Building Reliable AI Workflows]] - Reliability stack
- [[TTA.dev/Primitives/RetryPrimitive]] - Retry patterns
- [[TTA.dev/Primitives/CompensationPrimitive]] - Saga pattern

---

## Common Integration Patterns

### Pattern Overview

| Service Type | Primary Concern | Best Primitive | Example |
|--------------|----------------|----------------|---------|
| REST APIs | Transient failures | RetryPrimitive | OpenAI, Stripe |
| Databases | Connection pool | TimeoutPrimitive | PostgreSQL, MongoDB |
| Webhooks | Delivery guarantee | CompensationPrimitive | Slack, Discord |
| Message Queues | Ordering | SequentialPrimitive | RabbitMQ, Kafka |
| File Storage | Large uploads | ChunkedPrimitive | S3, GCS |

---

## Pattern 1: REST API Integration

### Basic REST API Call

```python
from tta_dev_primitives import WorkflowPrimitive, WorkflowContext
import httpx
from typing import Dict, Any

class OpenAIAPICall(WorkflowPrimitive[dict, dict]):
    """Call OpenAI API."""

    def __init__(self, api_key: str, model: str = "gpt-4"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.openai.com/v1"

    async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
        """Execute API call."""
        context.checkpoint("openai.api.start")

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "user", "content": input_data["prompt"]}
                        ],
                        "temperature": input_data.get("temperature", 0.7)
                    },
                    timeout=30.0
                )

                response.raise_for_status()
                data = response.json()

                context.checkpoint("openai.api.success")
                return {
                    "response": data["choices"][0]["message"]["content"],
                    "model": self.model,
                    "tokens": data["usage"]["total_tokens"]
                }

            except httpx.HTTPStatusError as e:
                context.checkpoint("openai.api.error")
                context.metadata["error_status"] = e.response.status_code

                if e.response.status_code == 429:
                    # Rate limit - should retry
                    raise Exception(f"Rate limited: {e}")
                elif e.response.status_code >= 500:
                    # Server error - should retry
                    raise Exception(f"Server error: {e}")
                else:
                    # Client error - should not retry
                    raise Exception(f"Client error: {e}")

            except httpx.TimeoutException as e:
                context.checkpoint("openai.api.timeout")
                raise Exception(f"Timeout: {e}")
```

### Add Retry for Resilience

```python
from tta_dev_primitives.recovery import RetryPrimitive

# Wrap with retry
resilient_api = RetryPrimitive(
    primitive=OpenAIAPICall(api_key="sk-..."),
    max_retries=3,
    backoff_strategy="exponential",
    initial_delay=1.0,
    max_delay=10.0,
    retry_exceptions=[
        httpx.TimeoutException,
        httpx.ConnectError,
        # Don't retry client errors (4xx except 429)
    ]
)

# Usage
context = WorkflowContext(correlation_id="req-123")
result = await resilient_api.execute(
    {"prompt": "Explain quantum computing"},
    context
)
```

### Add Timeout and Fallback

```python
from tta_dev_primitives.recovery import TimeoutPrimitive, FallbackPrimitive

class GPT35APICall(WorkflowPrimitive[dict, dict]):
    """Faster, cheaper fallback."""
    async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
        # Similar to OpenAIAPICall but with gpt-3.5-turbo
        return {"response": "Fallback response", "model": "gpt-3.5-turbo"}

# Build reliability stack
primary_with_timeout = TimeoutPrimitive(
    primitive=OpenAIAPICall(api_key="sk-...", model="gpt-4"),
    timeout_seconds=30.0
)

primary_with_retry = RetryPrimitive(
    primitive=primary_with_timeout,
    max_retries=3
)

fallback_with_timeout = TimeoutPrimitive(
    primitive=GPT35APICall(api_key="sk-..."),
    timeout_seconds=10.0
)

# Complete workflow
workflow = FallbackPrimitive(
    primary=primary_with_retry,
    fallbacks=[fallback_with_timeout]
)
```

---

## Pattern 2: Database Integration

### PostgreSQL Integration

```python
import asyncpg
from typing import Optional

class PostgreSQLQuery(WorkflowPrimitive[dict, list]):
    """Execute PostgreSQL query with connection pooling."""

    def __init__(
        self,
        dsn: str,
        min_pool_size: int = 10,
        max_pool_size: int = 20
    ):
        self.dsn = dsn
        self.pool: Optional[asyncpg.Pool] = None
        self.min_pool_size = min_pool_size
        self.max_pool_size = max_pool_size

    async def _ensure_pool(self):
        """Ensure connection pool exists."""
        if self.pool is None:
            self.pool = await asyncpg.create_pool(
                self.dsn,
                min_size=self.min_pool_size,
                max_size=self.max_pool_size,
                command_timeout=30.0
            )

    async def execute(self, input_data: dict, context: WorkflowContext) -> list:
        """Execute query."""
        await self._ensure_pool()

        context.checkpoint("db.query.start")
        query = input_data["query"]
        params = input_data.get("params", [])

        async with self.pool.acquire() as conn:
            try:
                result = await conn.fetch(query, *params)
                context.checkpoint("db.query.success")

                # Convert to list of dicts
                return [dict(row) for row in result]

            except asyncpg.PostgresError as e:
                context.checkpoint("db.query.error")
                context.metadata["error_code"] = e.sqlstate

                # Check if error is retryable
                if e.sqlstate in ['08000', '08003', '08006']:
                    # Connection errors - retry
                    raise Exception(f"Connection error: {e}")
                elif e.sqlstate == '40001':
                    # Serialization failure - retry
                    raise Exception(f"Serialization failure: {e}")
                else:
                    # Other errors - don't retry
                    raise Exception(f"Database error: {e}")

    async def close(self):
        """Close connection pool."""
        if self.pool:
            await self.pool.close()

# Usage with retry and timeout
db_query = PostgreSQLQuery(dsn="postgresql://user:pass@localhost/db")

with_timeout = TimeoutPrimitive(
    primitive=db_query,
    timeout_seconds=10.0  # Max 10s for query
)

with_retry = RetryPrimitive(
    primitive=with_timeout,
    max_retries=3,
    backoff_strategy="exponential"
)

# Execute
context = WorkflowContext()
users = await with_retry.execute(
    {
        "query": "SELECT * FROM users WHERE created_at > $1",
        "params": ["2025-01-01"]
    },
    context
)
```

### Database Transaction with Compensation

```python
from tta_dev_primitives.recovery import CompensationPrimitive

class CreateOrder(WorkflowPrimitive[dict, dict]):
    """Create order in database."""
    async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
        # Insert order
        order_id = await db.execute(
            "INSERT INTO orders (user_id, amount) VALUES ($1, $2) RETURNING id",
            input_data["user_id"],
            input_data["amount"]
        )
        return {**input_data, "order_id": order_id}

class DeleteOrder(WorkflowPrimitive[dict, dict]):
    """Compensation: Delete order."""
    async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
        await db.execute(
            "DELETE FROM orders WHERE id = $1",
            input_data["order_id"]
        )
        return input_data

class ChargePayment(WorkflowPrimitive[dict, dict]):
    """Charge payment via Stripe."""
    async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
        # Charge via Stripe API
        charge = await stripe.Charge.create(
            amount=input_data["amount"],
            currency="usd",
            source=input_data["payment_method"]
        )
        return {**input_data, "charge_id": charge.id}

class RefundPayment(WorkflowPrimitive[dict, dict]):
    """Compensation: Refund payment."""
    async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
        await stripe.Refund.create(charge=input_data["charge_id"])
        return input_data

# Build saga with compensation
order_saga = CompensationPrimitive(
    forward=CreateOrder(),
    compensation=DeleteOrder()
)

payment_saga = CompensationPrimitive(
    forward=ChargePayment(),
    compensation=RefundPayment()
)

# Chain sagas
checkout_workflow = order_saga >> payment_saga

# If payment fails, order is automatically deleted
try:
    result = await checkout_workflow.execute(order_data, context)
except Exception:
    # Compensation runs automatically - order deleted, payment refunded
    pass
```

---

## Pattern 3: Webhook Integration

### Reliable Webhook Delivery

```python
import hmac
import hashlib
from datetime import datetime

class WebhookDelivery(WorkflowPrimitive[dict, dict]):
    """Deliver webhook with signature verification."""

    def __init__(
        self,
        webhook_url: str,
        secret: str,
        max_retries: int = 3
    ):
        self.webhook_url = webhook_url
        self.secret = secret
        self.max_retries = max_retries

    def _sign_payload(self, payload: bytes) -> str:
        """Generate HMAC signature."""
        return hmac.new(
            self.secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()

    async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
        """Deliver webhook."""
        context.checkpoint("webhook.delivery.start")

        import json
        payload = json.dumps(input_data["data"]).encode()
        signature = self._sign_payload(payload)

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    self.webhook_url,
                    content=payload,
                    headers={
                        "Content-Type": "application/json",
                        "X-Webhook-Signature": signature,
                        "X-Webhook-Timestamp": str(int(datetime.now().timestamp())),
                        "X-Webhook-ID": context.correlation_id
                    },
                    timeout=10.0
                )

                if response.status_code in [200, 201, 204]:
                    context.checkpoint("webhook.delivery.success")
                    return {"status": "delivered", "response_code": response.status_code}
                elif response.status_code == 410:
                    # Endpoint gone - don't retry
                    context.checkpoint("webhook.delivery.endpoint_gone")
                    raise Exception("Webhook endpoint no longer exists")
                else:
                    # Other errors - retry
                    context.checkpoint("webhook.delivery.failed")
                    raise Exception(f"Webhook delivery failed: {response.status_code}")

            except httpx.TimeoutException:
                context.checkpoint("webhook.delivery.timeout")
                raise Exception("Webhook delivery timeout")

# Usage with retry and dead letter queue
webhook_delivery = WebhookDelivery(
    webhook_url="https://example.com/webhook",
    secret="webhook_secret_key"
)

# Retry with exponential backoff
with_retry = RetryPrimitive(
    primitive=webhook_delivery,
    max_retries=5,  # More retries for webhooks
    backoff_strategy="exponential",
    initial_delay=2.0,
    max_delay=300.0  # Max 5 minutes between retries
)

# Fallback to dead letter queue if all retries fail
class DeadLetterQueue(WorkflowPrimitive[dict, dict]):
    """Store failed webhooks for manual retry."""
    async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
        await redis.lpush("webhook_dlq", json.dumps(input_data))
        return {"status": "queued_for_retry"}

workflow = FallbackPrimitive(
    primary=with_retry,
    fallbacks=[DeadLetterQueue()]
)
```

### Webhook Receiver

```python
from fastapi import FastAPI, Request, HTTPException
import hmac
import hashlib

app = FastAPI()

class WebhookReceiver(WorkflowPrimitive[dict, dict]):
    """Receive and verify webhook."""

    def __init__(self, secret: str):
        self.secret = secret

    def verify_signature(
        self,
        payload: bytes,
        signature: str,
        timestamp: str
    ) -> bool:
        """Verify webhook signature."""
        # Check timestamp (prevent replay attacks)
        current_time = int(datetime.now().timestamp())
        webhook_time = int(timestamp)

        if abs(current_time - webhook_time) > 300:  # 5 minutes
            return False

        # Verify signature
        expected_signature = hmac.new(
            self.secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(expected_signature, signature)

    async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
        """Process webhook."""
        payload = input_data["payload"]
        signature = input_data["signature"]
        timestamp = input_data["timestamp"]

        # Verify signature
        if not self.verify_signature(payload, signature, timestamp):
            raise Exception("Invalid webhook signature")

        # Process webhook
        import json
        data = json.loads(payload)

        context.checkpoint("webhook.received")

        # Your business logic here
        result = await process_webhook_data(data)

        return {"status": "processed", "result": result}

@app.post("/webhook")
async def receive_webhook(request: Request):
    """Webhook endpoint."""
    payload = await request.body()
    signature = request.headers.get("X-Webhook-Signature")
    timestamp = request.headers.get("X-Webhook-Timestamp")
    webhook_id = request.headers.get("X-Webhook-ID")

    if not all([signature, timestamp, webhook_id]):
        raise HTTPException(status_code=400, detail="Missing webhook headers")

    # Process with primitive
    receiver = WebhookReceiver(secret="webhook_secret_key")
    context = WorkflowContext(correlation_id=webhook_id)

    try:
        result = await receiver.execute(
            {
                "payload": payload,
                "signature": signature,
                "timestamp": timestamp
            },
            context
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
```

---

## Pattern 4: Message Queue Integration

### RabbitMQ Producer

```python
import aio_pika
from typing import Optional

class RabbitMQPublisher(WorkflowPrimitive[dict, dict]):
    """Publish messages to RabbitMQ."""

    def __init__(
        self,
        amqp_url: str,
        exchange_name: str,
        routing_key: str
    ):
        self.amqp_url = amqp_url
        self.exchange_name = exchange_name
        self.routing_key = routing_key
        self.connection: Optional[aio_pika.Connection] = None
        self.channel: Optional[aio_pika.Channel] = None

    async def _ensure_connection(self):
        """Ensure connection exists."""
        if self.connection is None or self.connection.is_closed:
            self.connection = await aio_pika.connect_robust(self.amqp_url)
            self.channel = await self.connection.channel()
            self.exchange = await self.channel.declare_exchange(
                self.exchange_name,
                aio_pika.ExchangeType.TOPIC,
                durable=True
            )

    async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
        """Publish message."""
        await self._ensure_connection()

        context.checkpoint("rabbitmq.publish.start")

        import json
        message_body = json.dumps(input_data["data"])

        message = aio_pika.Message(
            body=message_body.encode(),
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            headers={
                "correlation_id": context.correlation_id,
                "timestamp": datetime.now().isoformat()
            }
        )

        try:
            await self.exchange.publish(
                message,
                routing_key=self.routing_key
            )

            context.checkpoint("rabbitmq.publish.success")
            return {"status": "published", "routing_key": self.routing_key}

        except Exception as e:
            context.checkpoint("rabbitmq.publish.error")
            raise Exception(f"Failed to publish: {e}")

    async def close(self):
        """Close connection."""
        if self.connection:
            await self.connection.close()

# Usage with retry
publisher = RabbitMQPublisher(
    amqp_url="amqp://guest:guest@localhost/",
    exchange_name="events",
    routing_key="user.created"
)

with_retry = RetryPrimitive(
    primitive=publisher,
    max_retries=3,
    backoff_strategy="exponential"
)
```

### RabbitMQ Consumer

```python
class RabbitMQConsumer(WorkflowPrimitive[dict, dict]):
    """Consume messages from RabbitMQ."""

    def __init__(
        self,
        amqp_url: str,
        queue_name: str,
        processor: WorkflowPrimitive
    ):
        self.amqp_url = amqp_url
        self.queue_name = queue_name
        self.processor = processor

    async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
        """Start consuming messages."""
        connection = await aio_pika.connect_robust(self.amqp_url)
        channel = await connection.channel()

        # Set QoS (prefetch count)
        await channel.set_qos(prefetch_count=10)

        queue = await channel.declare_queue(
            self.queue_name,
            durable=True
        )

        async def process_message(message: aio_pika.IncomingMessage):
            async with message.process():
                # Extract data
                import json
                data = json.loads(message.body.decode())

                # Create context from message headers
                msg_context = WorkflowContext(
                    correlation_id=message.headers.get("correlation_id", "unknown")
                )

                try:
                    # Process with primitive
                    result = await self.processor.execute(data, msg_context)
                    # Message auto-acked due to async with message.process()

                except Exception as e:
                    # Message will be requeued
                    raise e

        await queue.consume(process_message)

        # Keep running
        return {"status": "consuming"}
```

---

## Pattern 5: File Storage Integration

### S3 Upload with Chunking

```python
import aioboto3
from typing import BinaryIO

class S3Upload(WorkflowPrimitive[dict, dict]):
    """Upload file to S3 with multipart upload."""

    def __init__(
        self,
        bucket: str,
        aws_access_key_id: str,
        aws_secret_access_key: str,
        region: str = "us-east-1"
    ):
        self.bucket = bucket
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        self.region = region

    async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
        """Upload file."""
        context.checkpoint("s3.upload.start")

        file_path = input_data["file_path"]
        s3_key = input_data["s3_key"]

        session = aioboto3.Session(
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
            region_name=self.region
        )

        async with session.client("s3") as s3:
            try:
                # Upload with automatic multipart for large files
                with open(file_path, "rb") as f:
                    await s3.upload_fileobj(
                        f,
                        self.bucket,
                        s3_key,
                        ExtraArgs={
                            "Metadata": {
                                "uploaded_by": "tta-dev",
                                "correlation_id": context.correlation_id
                            }
                        }
                    )

                context.checkpoint("s3.upload.success")

                return {
                    "status": "uploaded",
                    "bucket": self.bucket,
                    "key": s3_key,
                    "url": f"s3://{self.bucket}/{s3_key}"
                }

            except Exception as e:
                context.checkpoint("s3.upload.error")
                raise Exception(f"S3 upload failed: {e}")

# Usage with retry and compensation
uploader = S3Upload(
    bucket="my-bucket",
    aws_access_key_id="...",
    aws_secret_access_key="..."
)

with_retry = RetryPrimitive(
    primitive=uploader,
    max_retries=3,
    backoff_strategy="exponential"
)

# Add compensation to delete on failure
class S3Delete(WorkflowPrimitive[dict, dict]):
    """Delete file from S3."""
    async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
        # Delete S3 object
        return {"status": "deleted"}

upload_saga = CompensationPrimitive(
    forward=with_retry,
    compensation=S3Delete()
)
```

---

## Error Handling Best Practices

### Retryable vs Non-Retryable Errors

```python
class RetryableError(Exception):
    """Error that should trigger retry."""
    pass

class NonRetryableError(Exception):
    """Error that should not retry."""
    pass

class SmartAPICall(WorkflowPrimitive[dict, dict]):
    """API call with smart error classification."""

    async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
        try:
            response = await api_call()
            return response

        except httpx.HTTPStatusError as e:
            status = e.response.status_code

            # Classify error
            if status == 429:
                # Rate limit - retry
                raise RetryableError(f"Rate limited: {e}")
            elif status >= 500:
                # Server error - retry
                raise RetryableError(f"Server error: {e}")
            elif status == 401:
                # Auth error - don't retry
                raise NonRetryableError(f"Authentication failed: {e}")
            elif status == 400:
                # Bad request - don't retry
                raise NonRetryableError(f"Invalid request: {e}")
            else:
                # Other 4xx - don't retry
                raise NonRetryableError(f"Client error: {e}")

# Use with selective retry
workflow = RetryPrimitive(
    primitive=SmartAPICall(),
    max_retries=3,
    retry_exceptions=[RetryableError]  # Only retry these
)
```

---

## Testing External Services

### Mock External Services

```python
from tta_dev_primitives.testing import MockPrimitive
import pytest

@pytest.mark.asyncio
async def test_api_integration_success():
    """Test successful API call."""

    # Mock API call
    mock_api = MockPrimitive(
        return_value={"response": "Success", "status": 200}
    )

    context = WorkflowContext()
    result = await mock_api.execute({"prompt": "test"}, context)

    assert result["status"] == 200
    assert mock_api.call_count == 1

@pytest.mark.asyncio
async def test_api_integration_with_retry():
    """Test retry on transient failure."""

    # Mock API to fail twice, then succeed
    mock_api = MockPrimitive(
        side_effect=[
            Exception("Timeout"),
            Exception("Timeout"),
            {"response": "Success", "status": 200}
        ]
    )

    # Wrap with retry
    workflow = RetryPrimitive(mock_api, max_retries=3)

    context = WorkflowContext()
    result = await workflow.execute({"prompt": "test"}, context)

    assert result["status"] == 200
    assert mock_api.call_count == 3  # Failed 2x, succeeded on 3rd

@pytest.mark.asyncio
async def test_database_transaction_rollback():
    """Test database transaction with rollback."""

    # Mock successful order creation
    mock_create_order = MockPrimitive(
        return_value={"order_id": "123"}
    )

    # Mock failing payment
    mock_charge_payment = MockPrimitive(
        side_effect=Exception("Payment declined")
    )

    # Mock order deletion (compensation)
    mock_delete_order = MockPrimitive(
        return_value={"status": "deleted"}
    )

    # Build saga
    order_saga = CompensationPrimitive(
        forward=mock_create_order,
        compensation=mock_delete_order
    )

    payment_saga = CompensationPrimitive(
        forward=mock_charge_payment,
        compensation=MockPrimitive(return_value={})
    )

    workflow = order_saga >> payment_saga

    # Execute (should fail and rollback)
    context = WorkflowContext()

    with pytest.raises(Exception):
        await workflow.execute({"amount": 100}, context)

    # Verify compensation ran
    assert mock_delete_order.call_count == 1
```

---

## Monitoring External Services

### Track Service Health

```python
from datetime import datetime, timedelta

class ServiceHealthTracker:
    """Track external service health metrics."""

    def __init__(self):
        self.metrics = {
            "total_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "total_latency_ms": 0,
            "errors_by_type": {}
        }
        self.recent_errors = []

    def record_success(self, latency_ms: float):
        """Record successful call."""
        self.metrics["total_calls"] += 1
        self.metrics["successful_calls"] += 1
        self.metrics["total_latency_ms"] += latency_ms

    def record_failure(self, error_type: str, error_message: str):
        """Record failed call."""
        self.metrics["total_calls"] += 1
        self.metrics["failed_calls"] += 1

        if error_type not in self.metrics["errors_by_type"]:
            self.metrics["errors_by_type"][error_type] = 0
        self.metrics["errors_by_type"][error_type] += 1

        self.recent_errors.append({
            "timestamp": datetime.now(),
            "type": error_type,
            "message": error_message
        })

        # Keep only last 100 errors
        self.recent_errors = self.recent_errors[-100:]

    def get_error_rate(self) -> float:
        """Get error rate percentage."""
        if self.metrics["total_calls"] == 0:
            return 0.0
        return (self.metrics["failed_calls"] / self.metrics["total_calls"]) * 100

    def get_avg_latency(self) -> float:
        """Get average latency in ms."""
        if self.metrics["successful_calls"] == 0:
            return 0.0
        return self.metrics["total_latency_ms"] / self.metrics["successful_calls"]

# Usage in primitive
class MonitoredAPICall(WorkflowPrimitive[dict, dict]):
    """API call with health tracking."""

    def __init__(self, tracker: ServiceHealthTracker):
        self.tracker = tracker

    async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
        start_time = time.time()

        try:
            result = await api_call()

            latency_ms = (time.time() - start_time) * 1000
            self.tracker.record_success(latency_ms)

            return result

        except Exception as e:
            self.tracker.record_failure(
                error_type=type(e).__name__,
                error_message=str(e)
            )
            raise e
```

---

## Next Steps

- **Add observability:** [[TTA.dev/Guides/Observability]]
- **Build reliability:** [[TTA.dev/How-To/Building Reliable AI Workflows]]
- **Deploy to production:** [[TTA.dev/Guides/Production Deployment]]

---

## Key Takeaways

1. **Classify errors** - Retry transient failures, fail fast on client errors
2. **Use timeouts** - Always set timeouts for external calls
3. **Add compensation** - Use sagas for multi-service transactions
4. **Monitor health** - Track error rates, latency, and failure types
5. **Test failures** - Mock external services and test error paths

**Remember:** External services will fail. Build resilience into your integrations from day one.

---

**Created:** [[2025-10-30]]
**Last Updated:** [[2025-10-30]]
**Estimated Time:** 45 minutes
**Difficulty:** [[Intermediate]]

- [[Project Hub]]

---
**Logseq:** [[TTA.dev/_archive/Nested_copies/Framework/Logseq/Pages/Tta.dev___how-to___integrating external services]]
