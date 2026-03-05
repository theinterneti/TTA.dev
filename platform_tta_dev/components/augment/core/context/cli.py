#!/usr/bin/env python3
"""

# Logseq: [[TTA.dev/Platform_tta_dev/Components/Augment/Core/Context/Cli]]
CLI tool for managing AI conversation contexts.

Usage:
    python cli.py new [session-id]           # Create new session
    python cli.py list                       # List all sessions
    python cli.py show <session-id>          # Show session summary
    python cli.py load <session-id>          # Load session (for continuation)
    python cli.py add <session-id> <message> # Add message to session
    python cli.py save <session-id>          # Save session
"""

import argparse
from datetime import UTC, datetime
from pathlib import Path

from conversation_manager import AIConversationContextManager, create_tta_session


def cmd_new(args):
    """Create a new session."""
    session_id = args.session_id
    if not session_id:
        session_id = f"tta-dev-{datetime.now(UTC).strftime('%Y%m%d-%H%M%S')}"

    manager, session_id = create_tta_session(session_id)

    # Save immediately
    manager.save_session(session_id)


def cmd_list(args):
    """List all sessions."""
    manager = AIConversationContextManager()
    sessions = manager.list_sessions()

    if not sessions:
        return

    for session_id in sorted(sessions, reverse=True):
        session_file = Path(f".augment/context/sessions/{session_id}.json")

        # Load to get details
        try:
            context = manager.load_session(session_file)
            len(context.messages)

        except Exception:
            pass


def cmd_show(args):
    """Show session summary."""
    session_id = args.session_id

    manager = AIConversationContextManager()
    session_file = Path(f".augment/context/sessions/{session_id}.json")

    if not session_file.exists():
        cmd_list(args)
        return

    context = manager.load_session(session_file)

    # Show recent messages
    for msg in context.messages[-5:]:
        {"system": "⚙️", "user": "👤", "assistant": "🤖"}.get(msg.role, "💬")

        content_preview = msg.content[:100].replace("\n", " ")
        if len(msg.content) > 100:
            content_preview += "..."

        if msg.metadata:
            pass


def cmd_load(args):
    """Load session for continuation."""
    session_id = args.session_id

    manager = AIConversationContextManager()
    session_file = Path(f".augment/context/sessions/{session_id}.json")

    if not session_file.exists():
        return

    manager.load_session(session_file)


def cmd_add(args):
    """Add a message to session."""
    session_id = args.session_id
    message = args.message
    role = args.role
    importance = args.importance

    manager = AIConversationContextManager()
    session_file = Path(f".augment/context/sessions/{session_id}.json")

    if not session_file.exists():
        return

    # Load session
    manager.load_session(session_file)

    # Add message
    manager.add_message(
        session_id=session_id, role=role, content=message, importance=importance
    )

    # Save
    manager.save_session(session_id)

    # Show updated summary


def cmd_save(args):
    """Save session."""
    session_id = args.session_id

    manager = AIConversationContextManager()
    session_file = Path(f".augment/context/sessions/{session_id}.json")

    if not session_file.exists():
        return

    # Load and save (to ensure consistency)
    manager.load_session(session_file)
    manager.save_session(session_id)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="AI Conversation Context Manager CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create new session
  python cli.py new tta-feature-xyz

  # List all sessions
  python cli.py list

  # Show session details
  python cli.py show tta-feature-xyz

  # Load session for continuation
  python cli.py load tta-feature-xyz

  # Add message to session
  python cli.py add tta-feature-xyz "Implement error recovery" --importance 0.9

  # Save session
  python cli.py save tta-feature-xyz
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # New command
    parser_new = subparsers.add_parser("new", help="Create new session")
    parser_new.add_argument(
        "session_id", nargs="?", help="Session ID (auto-generated if not provided)"
    )

    # List command
    subparsers.add_parser("list", help="List all sessions")

    # Show command
    parser_show = subparsers.add_parser("show", help="Show session summary")
    parser_show.add_argument("session_id", help="Session ID")

    # Load command
    parser_load = subparsers.add_parser("load", help="Load session for continuation")
    parser_load.add_argument("session_id", help="Session ID")

    # Add command
    parser_add = subparsers.add_parser("add", help="Add message to session")
    parser_add.add_argument("session_id", help="Session ID")
    parser_add.add_argument("message", help="Message content")
    parser_add.add_argument(
        "--role",
        default="user",
        choices=["user", "assistant", "system"],
        help="Message role",
    )
    parser_add.add_argument(
        "--importance", type=float, default=0.7, help="Importance score (0.0-1.0)"
    )

    # Save command
    parser_save = subparsers.add_parser("save", help="Save session")
    parser_save.add_argument("session_id", help="Session ID")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Dispatch to command handler
    commands = {
        "new": cmd_new,
        "list": cmd_list,
        "show": cmd_show,
        "load": cmd_load,
        "add": cmd_add,
        "save": cmd_save,
    }

    handler = commands.get(args.command)
    if handler:
        try:
            handler(args)
        except Exception:
            import traceback

            traceback.print_exc()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
