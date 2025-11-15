"""
Agentic Primitives - AI Conversation Context Management

Manage AI conversation context windows with automatic token counting and intelligent pruning.

Quick Start:
    from context import AIConversationContextManager

    # Create manager
    manager = AIConversationContextManager(max_tokens=8000)

    # Create session
    session_id = "my-session"
    manager.create_session(session_id)

    # Add messages
    manager.add_message(
        session_id=session_id,
        role="user",
        content="Hello",
        importance=0.9
    )

    # Save session
    manager.save_session(session_id)

For more details, see .augment/context/README.md
"""

from .conversation_manager import (
    AIConversationContextManager,
    ConversationContext,
    # Core classes
    ConversationMessage,
    # Helper function
    create_tta_session,
)

__all__ = [
    # Core classes
    "ConversationMessage",
    "ConversationContext",
    "AIConversationContextManager",
    # Helper
    "create_tta_session",
]

__version__ = "1.0.0"
