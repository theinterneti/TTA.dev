import asyncio

from .redis_queue import dequeue_webhook


async def main():
    """
    Continuously dequeues and processes webhooks.
    """
    while True:
        # In a real application, you would have multiple workers
        # and a more robust way of handling webhook IDs.
        webhook = await dequeue_webhook("some_webhook_id")
        if webhook:
            print(f"Processing webhook: {webhook.decode('utf-8')}")
        else:
            # If the queue is empty, wait a bit before trying again.
            await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(main())
