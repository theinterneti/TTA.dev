from typing import Any

import redis.asyncio as redis

# In a production environment, these settings would come from a config file or environment variables.
REDIS_HOST = "localhost"
REDIS_PORT = 6379


async def get_redis_client() -> redis.Redis:
    """
    Creates and returns a Redis client.
    """
    return redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)


async def store_webhook_config(config: dict[str, Any]) -> None:
    """
    Stores a webhook's configuration in Redis.
    The config is stored in a Hash under the key "webhooks:{webhook_id}".
    """
    redis_client = await get_redis_client()
    webhook_id = config["id"]
    await redis_client.hmset(f"webhooks:{webhook_id}", config)


async def get_webhook_config(webhook_id: str) -> dict[str, Any] | None:
    """
    Retrieves a webhook's configuration from Redis.
    """
    redis_client = await get_redis_client()
    config = await redis_client.hgetall(f"webhooks:{webhook_id}")
    if not config:
        return None
    return {key.decode("utf-8"): value.decode("utf-8") for key, value in config.items()}


async def delete_webhook_config(webhook_id: str) -> None:
    """
    Deletes a webhook's configuration from Redis.
    """
    redis_client = await get_redis_client()
    await redis_client.delete(f"webhooks:{webhook_id}")


async def list_webhook_configs() -> list[str]:
    """
    Lists all webhook IDs from Redis.
    """
    redis_client = await get_redis_client()
    keys = await redis_client.keys("webhooks:*")
    return [key.decode("utf-8").split(":")[1] for key in keys]
