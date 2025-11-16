#!/usr/bin/env python3

import argparse
import asyncio
import uuid

from .config import (
    delete_webhook_config,
    get_webhook_config,
    list_webhook_configs,
    store_webhook_config,
)


def create(args):
    """
    Create a new inbound webhook and store its configuration in Redis.
    """
    webhook_id = f"whk_{uuid.uuid4().hex}"
    secret = f"whsec_{uuid.uuid4().hex}"

    config = {
        "id": webhook_id,
        "name": args.name,
        "secret": secret,
        "event_name": args.event_name,
        "target_workflow": args.target_workflow,
    }

    asyncio.run(store_webhook_config(config))

    print("Webhook Created!")
    print(f"  Name: {args.name}")
    print(f"  ID: {webhook_id}")
    print(f"  URL: https://api.tta.dev/hooks/catch/{webhook_id}")
    print(f"  Secret: {secret}")
    print(f"  Event Name: {args.event_name}")
    print(f"  Target Workflow: {args.target_workflow}")


def list_webhooks(args):
    """
    List all registered webhooks.
    """
    webhook_ids = asyncio.run(list_webhook_configs())
    if not webhook_ids:
        print("No webhooks found.")
        return

    print("Registered Webhooks:")
    for webhook_id in webhook_ids:
        config = asyncio.run(get_webhook_config(webhook_id))
        if config:
            print(f"  - ID: {config['id']}, Name: {config['name']}")


def delete(args):
    """
    Delete a webhook by its ID.
    """
    asyncio.run(delete_webhook_config(args.id))
    print(f"Webhook {args.id} deleted.")


def main():
    parser = argparse.ArgumentParser(description="Webhook Ingestion CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Create command
    create_parser = subparsers.add_parser("create", help="Create a new inbound webhook")
    create_parser.add_argument("--name", required=True, help="The name of the webhook.")
    create_parser.add_argument(
        "--event-name",
        required=True,
        help="The name of the event to trigger the webhook.",
    )
    create_parser.add_argument(
        "--target-workflow", required=True, help="The name of the workflow to trigger."
    )
    create_parser.set_defaults(func=create)

    # List command
    list_parser = subparsers.add_parser("list", help="List all registered webhooks")
    list_parser.set_defaults(func=list_webhooks)

    # Delete command
    delete_parser = subparsers.add_parser("delete", help="Delete a webhook by ID")
    delete_parser.add_argument(
        "--id", required=True, help="The ID of the webhook to delete."
    )
    delete_parser.set_defaults(func=delete)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
