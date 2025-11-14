#!/usr/bin/env python3
"""
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
from datetime import datetime
from pathlib import Path

from conversation_manager import AIConversationContextManager, create_tta_session


def cmd_new(args):
    """Create a new session."""
    session_id = args.session_id
    if not session_id:
        session_id = f"tta-dev-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"

    manager, session_id = create_tta_session(session_id)

    print(f"✓ Created new session: {session_id}")
    print("\nArchitecture context loaded automatically.")
    print("\nTo add messages:")
    print(f"  python cli.py add {session_id} 'Your message here'")
    print("\nTo view summary:")
    print(f"  python cli.py show {session_id}")

    # Save immediately
    filepath = manager.save_session(session_id)
    print(f"\n✓ Session saved to: {filepath}")


def cmd_list(args):
    """List all sessions."""
    manager = AIConversationContextManager()
    sessions = manager.list_sessions()

    if not sessions:
        print("No sessions found.")
        print("\nCreate a new session:")
        print("  python cli.py new [session-id]")
        return

    print(f"Found {len(sessions)} session(s):\n")

    for session_id in sorted(sessions, reverse=True):
        session_file = Path(f".augment/context/sessions/{session_id}.json")

        # Load to get details
        try:
            context = manager.load_session(session_file)
            msg_count = len(context.messages)
            utilization = context.utilization

            print(f"  {session_id}")
            print(f"    Messages: {msg_count}")
            print(f"    Utilization: {utilization:.1%}")
            print(f"    File: {session_file}")
            print()
        except Exception as e:
            print(f"  {session_id} (error loading: {e})")
            print()


def cmd_show(args):
    """Show session summary."""
    session_id = args.session_id

    manager = AIConversationContextManager()
    session_file = Path(f".augment/context/sessions/{session_id}.json")

    if not session_file.exists():
        print(f"✗ Session not found: {session_id}")
        print("\nAvailable sessions:")
        cmd_list(args)
        return

    context = manager.load_session(session_file)

    print("=" * 60)
    print(f"Session: {session_id}")
    print("=" * 60)
    print()
    print(manager.get_context_summary(session_id))

    # Show recent messages
    print("\nRecent messages:")
    for msg in context.messages[-5:]:
        role_emoji = {"system": "⚙️", "user": "👤", "assistant": "🤖"}.get(
            msg.role, "💬"
        )

        content_preview = msg.content[:100].replace("\n", " ")
        if len(msg.content) > 100:
            content_preview += "..."

        print(f"\n{role_emoji} {msg.role.upper()} (importance={msg.importance})")
        print(f"  {content_preview}")

        if msg.metadata:
            print(f"  Metadata: {msg.metadata}")


def cmd_load(args):
    """Load session for continuation."""
    session_id = args.session_id

    manager = AIConversationContextManager()
    session_file = Path(f".augment/context/sessions/{session_id}.json")

    if not session_file.exists():
        print(f"✗ Session not found: {session_id}")
        return

    manager.load_session(session_file)

    print(f"✓ Loaded session: {session_id}")
    print()
    print(manager.get_context_summary(session_id))

    print("\n" + "=" * 60)
    print("Session Context Loaded")
    print("=" * 60)
    print("\nYou can now continue your AI conversation with full context.")
    print("\nTo add a message:")
    print(f"  python cli.py add {session_id} 'Your message here'")


def cmd_add(args):
    """Add a message to session."""
    session_id = args.session_id
    message = args.message
    role = args.role
    importance = args.importance

    manager = AIConversationContextManager()
    session_file = Path(f".augment/context/sessions/{session_id}.json")

    if not session_file.exists():
        print(f"✗ Session not found: {session_id}")
        return

    # Load session
    manager.load_session(session_file)

    # Add message
    manager.add_message(
        session_id=session_id, role=role, content=message, importance=importance
    )

    print(f"✓ Added {role} message to session: {session_id}")
    print(f"  Importance: {importance}")
    print(f"  Content: {message[:100]}{'...' if len(message) > 100 else ''}")

    # Save
    filepath = manager.save_session(session_id)
    print(f"\n✓ Session saved to: {filepath}")

    # Show updated summary
    print()
    print(manager.get_context_summary(session_id))


def cmd_save(args):
    """Save session."""
    session_id = args.session_id

    manager = AIConversationContextManager()
    session_file = Path(f".augment/context/sessions/{session_id}.json")

    if not session_file.exists():
        print(f"✗ Session not found: {session_id}")
        return

    # Load and save (to ensure consistency)
    manager.load_session(session_file)
    filepath = manager.save_session(session_id)

    print(f"✓ Session saved to: {filepath}")


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
        except Exception as e:
            print(f"✗ Error: {e}")
            import traceback

            traceback.print_exc()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
