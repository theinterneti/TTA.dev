import asyncio
import logging

import httpx

from .config import get_redis_client, get_webhook_config
from .redis_queue import PROCESSING_QUEUE_PREFIX

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MAX_RETRIES = 5
INITIAL_BACKOFF_SECONDS = 1


async def dispatch_webhook(webhook_id: str, payload: bytes):
    """
    Dispatches a webhook to its configured target URL with retry logic.
    """
    config = await get_webhook_config(webhook_id)
    if not config or "target_workflow" not in config:
        logger.error(f"No target_workflow configured for webhook_id: {webhook_id}")
        return

    target_url = config["target_workflow"]

    async with httpx.AsyncClient() as client:
        for attempt in range(MAX_RETRIES):
            try:
                response = await client.post(
                    target_url,
                    content=payload,
                    headers={"Content-Type": "application/json"},
                )
                response.raise_for_status()
                logger.info(
                    f"Successfully dispatched webhook {webhook_id} to {target_url}"
                )
                return
            except httpx.HTTPStatusError as e:
                logger.warning(
                    f"Attempt {attempt + 1} failed for webhook {webhook_id} to {target_url}: {e.response.status_code}"
                )
                if e.response.status_code < 500:
                    # Don't retry on 4xx client errors
                    return
            except httpx.RequestError as e:
                logger.warning(
                    f"Attempt {attempt + 1} failed for webhook {webhook_id} to {target_url}: {e}"
                )

            backoff_time = INITIAL_BACKOFF_SECONDS * (2**attempt)
            await asyncio.sleep(backoff_time)

    logger.error(
        f"Failed to dispatch webhook {webhook_id} to {target_url} after {MAX_RETRIES} attempts."
    )


async def main():
    """
    Continuously dequeues and processes webhooks using a reliable queue pattern.
    """
    redis_client = await get_redis_client()
    logger.info("Webhook worker started...")

    while True:
        # Use RPOPLPUSH for a reliable queue pattern.
        # This atomically moves a message from the main queue to a processing queue.
        # If the worker crashes, the message remains in the processing queue and can be recovered.

        # For simplicity, we'll process one webhook at a time. A more advanced implementation
        # would dynamically discover all webhook queues.
        webhook_id_to_process = "whk_123"  # This would be discovered dynamically

        payload = await redis_client.rpoplpush(
            f"webhooks:queue:{webhook_id_to_process}",
            f"{PROCESSING_QUEUE_PREFIX}:{webhook_id_to_process}",
        )

        if payload:
            logger.info(f"Processing webhook for {webhook_id_to_process}...")
            await dispatch_webhook(webhook_id_to_process, payload)

            # Once successfully processed, remove the message from the processing queue.
            await redis_client.lrem(
                f"{PROCESSING_QUEUE_PREFIX}:{webhook_id_to_process}", 1, payload
            )
        else:
            # If the queue is empty, wait a bit before trying again.
            await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(main())
