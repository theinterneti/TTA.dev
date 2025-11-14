#!/usr/bin/env python3
"""
Example usage of AI Conversation Context Manager.

This demonstrates how to use the context manager for AI-assisted development
sessions in the TTA project.
"""

from conversation_manager import AIConversationContextManager, create_tta_session


def example_new_session():
    """Example: Starting a new development session."""
    print("=" * 60)
    print("Example 1: Starting a New Session")
    print("=" * 60)

    # Create a new session with TTA architecture context
    manager, session_id = create_tta_session("tta-agentic-primitives-2025-10-20")

    print(f"\nCreated session: {session_id}")
    print(manager.get_context_summary(session_id))

    # Add a feature request (high importance)
    manager.add_message(
        session_id=session_id,
        role="user",
        content="""
        I'd like to implement agentic primitives for TTA in two phases:

        Phase 1: Apply to development process (meta-level)
        - Context management for AI sessions
        - Error recovery in build scripts
        - Observability in development tools

        Phase 2: Apply to TTA application (product-level)
        - Context Window Manager in agent_orchestration/
        - Error Recovery Framework
        - Tool Execution Observability
        """,
        importance=1.0,
        metadata={
            "type": "feature_request",
            "phase": "planning",
            "components": ["agent_orchestration", "development_tools"],
        },
    )

    # Add AI response (normal importance)
    manager.add_message(
        session_id=session_id,
        role="assistant",
        content="""
        Excellent strategic thinking! Applying primitives to the development process first
        is brilliant - it lets us validate patterns in a low-risk environment before
        product integration.

        I'll create a comprehensive Phase 1 implementation plan...
        """,
        importance=0.7,
        metadata={"type": "response"},
    )

    # Add architectural decision (critical importance)
    manager.add_message(
        session_id=session_id,
        role="user",
        content="""
        Architectural Decision: We'll use hybrid pruning strategy for context management,
        combining recency and relevance scoring. This preserves both recent context and
        important historical decisions.
        """,
        importance=1.0,
        metadata={
            "type": "architectural_decision",
            "component": "context_management",
            "decision": "hybrid_pruning_strategy",
        },
    )

    print("\n" + manager.get_context_summary(session_id))

    # Save session
    filepath = manager.save_session(session_id)
    print(f"\nSession saved to: {filepath}")

    return manager, session_id


def example_continue_session():
    """Example: Continuing a previous session."""
    print("\n" + "=" * 60)
    print("Example 2: Continuing a Previous Session")
    print("=" * 60)

    manager = AIConversationContextManager()

    # List available sessions
    sessions = manager.list_sessions()
    print(f"\nAvailable sessions: {sessions}")

    if not sessions:
        print("No sessions found. Run example_new_session() first.")
        return

    # Load the most recent session
    session_file = f".augment/context/sessions/{sessions[0]}.json"
    context = manager.load_session(session_file)
    session_id = context.session_id

    print(f"\nLoaded session: {session_id}")
    print(manager.get_context_summary(session_id))

    # Continue the conversation
    manager.add_message(
        session_id=session_id,
        role="user",
        content="Let's start implementing Phase 1. What should we build first?",
        importance=0.8,
        metadata={"type": "task_request"},
    )

    manager.add_message(
        session_id=session_id,
        role="assistant",
        content="""
        I recommend starting with the AI Conversation Context Manager itself - it's
        the quickest win and we can use it immediately for this conversation!

        I'll create:
        1. .augment/context/conversation_manager.py - Core implementation
        2. .augment/rules/ai-context-management.md - Usage guidelines
        3. .augment/context/example_usage.py - This example file
        """,
        importance=0.7,
        metadata={"type": "implementation_plan"},
    )

    print("\n" + manager.get_context_summary(session_id))

    # Save updated session
    filepath = manager.save_session(session_id)
    print(f"\nSession updated and saved to: {filepath}")

    return manager, session_id


def example_context_pruning():
    """Example: Demonstrating context pruning."""
    print("\n" + "=" * 60)
    print("Example 3: Context Pruning")
    print("=" * 60)

    # Create a session with small context window for demonstration
    manager = AIConversationContextManager(max_tokens=500)
    session_id = "tta-pruning-demo"
    context = manager.create_session(session_id)

    print("\nCreated session with max_tokens=500")

    # Add system message (always preserved)
    manager.add_message(
        session_id=session_id,
        role="system",
        content="TTA Architecture: Multi-agent system with IPA, WBA, NGA",
        importance=1.0,
        metadata={"type": "architecture_context"},
    )

    # Add many messages to trigger pruning
    for i in range(20):
        importance = 1.0 if i % 5 == 0 else 0.5  # Every 5th message is important
        manager.add_message(
            session_id=session_id,
            role="user" if i % 2 == 0 else "assistant",
            content=f"Message {i}: This is a test message to demonstrate context pruning. "
            * 5,
            importance=importance,
            metadata={"message_number": i},
        )

        if i % 5 == 0:
            print(f"\nAfter message {i}:")
            print(manager.get_context_summary(session_id))

    print("\n" + "=" * 60)
    print("Final Context After Pruning:")
    print("=" * 60)
    print(manager.get_context_summary(session_id))

    # Show which messages were preserved
    context = manager.contexts[session_id]
    print("\nPreserved messages:")
    for msg in context.messages:
        msg_num = msg.metadata.get("message_number", "system")
        print(f"  - Message {msg_num} (importance={msg.importance}, role={msg.role})")

    return manager, session_id


def example_metadata_usage():
    """Example: Using metadata for organization."""
    print("\n" + "=" * 60)
    print("Example 4: Metadata Usage")
    print("=" * 60)

    manager, session_id = create_tta_session("tta-metadata-demo")

    # Add messages with rich metadata
    manager.add_message(
        session_id=session_id,
        role="user",
        content="Implement context window manager",
        importance=0.9,
        metadata={
            "type": "task_request",
            "component": "agent_orchestration",
            "phase": "phase1",
            "priority": "high",
            "estimated_days": 2,
        },
    )

    manager.add_message(
        session_id=session_id,
        role="user",
        content="Add error recovery to build scripts",
        importance=0.9,
        metadata={
            "type": "task_request",
            "component": "development_tools",
            "phase": "phase1",
            "priority": "high",
            "estimated_days": 2,
        },
    )

    manager.add_message(
        session_id=session_id,
        role="user",
        content="Create development metrics dashboard",
        importance=0.8,
        metadata={
            "type": "task_request",
            "component": "development_tools",
            "phase": "phase1",
            "priority": "medium",
            "estimated_days": 2,
        },
    )

    # Query messages by metadata
    context = manager.contexts[session_id]

    print("\nAll task requests:")
    task_requests = [
        msg for msg in context.messages if msg.metadata.get("type") == "task_request"
    ]
    for msg in task_requests:
        print(f"  - {msg.content[:50]}... (priority: {msg.metadata.get('priority')})")

    print("\nHigh priority tasks:")
    high_priority = [
        msg for msg in task_requests if msg.metadata.get("priority") == "high"
    ]
    for msg in high_priority:
        print(f"  - {msg.content[:50]}...")

    print("\nPhase 1 tasks:")
    phase1_tasks = [
        msg for msg in task_requests if msg.metadata.get("phase") == "phase1"
    ]
    print(f"  Total: {len(phase1_tasks)} tasks")
    total_days = sum(msg.metadata.get("estimated_days", 0) for msg in phase1_tasks)
    print(f"  Estimated duration: {total_days} days")

    return manager, session_id


def main():
    """Run all examples."""
    print("\n" + "=" * 60)
    print("AI Conversation Context Manager - Examples")
    print("=" * 60)

    # Example 1: New session
    manager1, session1 = example_new_session()

    # Example 2: Continue session
    example_continue_session()

    # Example 3: Context pruning
    example_context_pruning()

    # Example 4: Metadata usage
    example_metadata_usage()

    print("\n" + "=" * 60)
    print("Examples Complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Review saved sessions in .augment/context/sessions/")
    print("2. Try loading a session and continuing the conversation")
    print("3. Experiment with different importance scores and metadata")
    print("4. Integrate with your AI-assisted development workflow")


if __name__ == "__main__":
    main()
