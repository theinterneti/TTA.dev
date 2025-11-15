import redis.asyncio as redis

# Connect to Redis
redis_client = redis.from_url("redis://localhost")


async def enqueue_webhook(webhook_id: str, payload: bytes):
    """
    Enqueues a webhook payload into a Redis list.
    """
    await redis_client.lpush(f"webhook:{webhook_id}", payload)


async def dequeue_webhook(webhook_id: str) -> bytes | None:
    """
    Dequeues a webhook payload from a Redis list.
    """
    return await redis_client.rpop(f"webhook:{webhook_id}")
