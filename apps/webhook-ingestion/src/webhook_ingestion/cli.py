#!/usr/bin/env python3

import argparse
import uuid


def create(args):
    """
    Create a new inbound webhook.
    """
    webhook_id = f"whk_{uuid.uuid4().hex}"
    secret = f"whsec_{uuid.uuid4().hex}"

    # In a real application, this would store the webhook configuration
    # in a database. For now, we will just print it.
    print("Webhook Created!")
    print(f"  Name: {args.name}")
    print(f"  ID: {webhook_id}")
    print(f"  URL: https://api.tta.dev/hooks/catch/{webhook_id}")
    print(f"  Secret: {secret}")
    print(f"  Event Name: {args.event_name}")
    print(f"  Target Workflow: {args.target_workflow}")


def main():
    parser = argparse.ArgumentParser(description="Webhook Ingestion CLI")
    subparsers = parser.add_subparsers(dest="command")

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

    args = parser.parse_args()
    if args.command:
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
