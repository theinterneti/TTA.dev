"""Example: Memory-aware workflow with MemoryPrimitive.

This example shows how to use MemoryPrimitive for context-aware processing.
Works immediately without Docker, Redis, or any setup!

Run with: python examples/memory_workflow.py
"""

import asyncio
import logging
from datetime import datetime

from tta_dev_primitives.performance.memory import MemoryPrimitive, create_memory_key

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


async def main() -> None:
    """Demonstrate memory-aware workflow."""

    print("=" * 70)
    print("Memory-Aware Workflow Example")
    print("=" * 70)
    print()

    # Create memory primitive (works immediately, no setup!)
    print("📦 Initializing MemoryPrimitive (in-memory mode)...")
    memory = MemoryPrimitive(max_size=100)

    backend_info = memory.get_backend_info()
    print(f"✅ Backend: {backend_info['backend']}")
    print(f"✅ Fallback available: {backend_info['fallback_available']}")
    print()

    # Simulate a multi-turn conversation
    print("💬 Simulating multi-turn conversation with memory...")
    print("-" * 70)

    user_id = "user_123"
    session_id = "session_abc"

    # Turn 1: Store initial context
    turn1_key = create_memory_key(user_id, session_id, {"turn": 1})
    turn1_data = {
        "timestamp": datetime.now().isoformat(),
        "user_message": "What's the weather like?",
        "assistant_response": "I'll check the weather for you.",
        "intent": "weather_query",
    }

    await memory.add(turn1_key, turn1_data)
    print(f"Turn 1 stored: {turn1_data['user_message']}")

    # Turn 2: Store follow-up
    turn2_key = create_memory_key(user_id, session_id, {"turn": 2})
    turn2_data = {
        "timestamp": datetime.now().isoformat(),
        "user_message": "What about tomorrow?",
        "assistant_response": "Tomorrow will be sunny.",
        "intent": "weather_query_followup",
        "previous_context": "Discussed weather",
    }

    await memory.add(turn2_key, turn2_data)
    print(f"Turn 2 stored: {turn2_data['user_message']}")

    # Turn 3: New topic
    turn3_key = create_memory_key(user_id, session_id, {"turn": 3})
    turn3_data = {
        "timestamp": datetime.now().isoformat(),
        "user_message": "Tell me a joke",
        "assistant_response": "Why did the programmer quit? Too much debugging!",
        "intent": "entertainment",
    }

    await memory.add(turn3_key, turn3_data)
    print(f"Turn 3 stored: {turn3_data['user_message']}")
    print()

    # Retrieve specific turn
    print("🔍 Retrieving Turn 2...")
    retrieved = await memory.get(turn2_key)
    if retrieved:
        print(f"Found: {retrieved['user_message']}")
        print(f"Context: {retrieved.get('previous_context', 'None')}")
    print()

    # Search for weather-related memories
    print("🔎 Searching for 'weather' memories...")
    weather_memories = await memory.search("weather", limit=5)
    print(f"Found {len(weather_memories)} weather-related memories:")
    for i, mem in enumerate(weather_memories, 1):
        print(f"  {i}. {mem.get('user_message', 'N/A')}")
    print()

    # Store some task-specific memories
    print("📋 Storing task-specific memories...")
    task_contexts = [
        {"task": "summarize", "document": "report_2025.pdf"},
        {"task": "translate", "language": "Spanish"},
        {"task": "code_review", "file": "main.py"},
    ]

    for ctx in task_contexts:
        task_key = create_memory_key(user_id, session_id, ctx)
        task_data = {
            "timestamp": datetime.now().isoformat(),
            "context": ctx,
            "status": "completed",
        }
        await memory.add(task_key, task_data)
        print(f"  Stored: {ctx['task']}")
    print()

    # Check memory size
    print(f"📊 Total memories stored: {memory.size()}")
    print()

    # Search by task type
    print("🔎 Searching for 'code' related tasks...")
    code_tasks = await memory.search("code", limit=5)
    print(f"Found {len(code_tasks)} code-related tasks:")
    for task in code_tasks:
        ctx = task.get("context", {})
        print(f"  - Task: {ctx.get('task', 'N/A')}")
    print()

    # Demonstrate persistence (in-memory loses data on restart)
    print("⚠️  Note: In-memory mode does not persist across restarts")
    print("   To add persistence, use Redis (optional):")
    print("   memory = MemoryPrimitive(redis_url='redis://localhost:6379')")
    print()

    # Show upgrade path
    print("🚀 Upgrade Path:")
    print("   1. ✅ Start here: In-memory mode (zero setup)")
    print("   2. 📦 Add Redis when ready for persistence")
    print("   3. 🔍 Add RediSearch for semantic search")
    print("   Same API, gradual complexity!")
    print()

    print("=" * 70)
    print("✅ Example complete!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
