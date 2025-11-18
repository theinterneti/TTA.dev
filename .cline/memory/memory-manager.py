#!/usr/bin/env python3
"""
Memory Management System for TTA.dev Agent Primitives

This module provides conversation persistence, pattern storage, and retrieval
for Cline's agentic workflow system. It integrates with Logseq for long-term
knowledge persistence and provides intelligent pattern matching for development tasks.
"""

import hashlib
import json
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass
class Conversation:
    """Represents a conversation session with metadata."""

    session_id: str
    persona: str
    workflow_type: str
    start_time: datetime
    end_time: datetime | None = None
    success: bool = False
    tags: list[str] = field(default_factory=list)
    summary: str | None = None
    key_insights: list[str] = field(default_factory=list)


@dataclass
class Pattern:
    """Represents a reusable development pattern."""

    id: str
    name: str
    category: str
    description: str
    tags: list[str]
    usage_count: int = 0
    last_used: datetime | None = None
    created_at: datetime = field(default_factory=datetime.now)
    code_template: str | None = None
    validation_tests: list[str] = field(default_factory=list)
    complexity_score: int = 1  # 1-5 scale


class MemoryManager:
    """Manages conversation persistence and pattern libraries."""

    def __init__(self):
        self.memory_dir = Path(".cline/memory")
        self.memory_dir.mkdir(exist_ok=True)

        # Setup databases
        self.conversations_db = self.memory_dir / "conversations.db"
        self.patterns_db = self.memory_dir / "patterns.db"

        # Initialize databases
        self._init_conversations_db()
        self._init_patterns_db()

        # Pre-load common patterns
        self._load_common_patterns()

    def _init_conversations_db(self):
        """Initialize conversations database."""
        with sqlite3.connect(self.conversations_db) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    session_id TEXT PRIMARY KEY,
                    persona TEXT NOT NULL,
                    workflow_type TEXT NOT NULL,
                    start_time TEXT NOT NULL,
                    end_time TEXT,
                    success INTEGER DEFAULT 0,
                    tags TEXT,  -- JSON array
                    summary TEXT,
                    key_insights TEXT  -- JSON array
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    role TEXT NOT NULL,  -- user, assistant, system
                    content TEXT NOT NULL,
                    metadata TEXT,  -- JSON
                    FOREIGN KEY(session_id) REFERENCES conversations(session_id)
                )
            """)

    def _init_patterns_db(self):
        """Initialize patterns database."""
        with sqlite3.connect(self.patterns_db) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS patterns (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    category TEXT NOT NULL,
                    description TEXT NOT NULL,
                    tags TEXT NOT NULL,  -- JSON array
                    usage_count INTEGER DEFAULT 0,
                    last_used TEXT,
                    created_at TEXT NOT NULL,
                    code_template TEXT,
                    validation_tests TEXT,  -- JSON array
                    complexity_score INTEGER DEFAULT 1
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS pattern_usage (
                    id INTEGER PRIMARY KEY,
                    pattern_id TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    used_at TEXT NOT NULL,
                    success INTEGER DEFAULT 0,
                    feedback TEXT,
                    FOREIGN KEY(pattern_id) REFERENCES patterns(id)
                )
            """)

    def _load_common_patterns(self):
        """Load common development patterns."""
        common_patterns = [
            {
                "id": "sequential_primitive_workflow",
                "name": "Sequential Workflow",
                "category": "workflow",
                "description": "Chain operations in sequence using >> operator",
                "tags": ["workflow", "sequential", "composition"],
                "code_template": """
workflow = step1 >> step2 >> step3 >> output_formatter
result = await workflow.execute(context, input_data)
""",
                "validation_tests": [
                    "check_sequence_execution",
                    "test_error_propagation",
                ],
                "complexity_score": 1,
            },
            {
                "id": "parallel_primitive_workflow",
                "name": "Parallel Workflow",
                "category": "workflow",
                "description": "Execute operations in parallel using | operator",
                "tags": ["workflow", "parallel", "composition", "performance"],
                "code_template": """
workflow = branch1 | branch2 | branch3
results = await workflow.execute(context, input_data)
""",
                "validation_tests": [
                    "check_parallel_execution",
                    "test_result_aggregation",
                ],
                "complexity_score": 2,
            },
            {
                "id": "retry_primitive_pattern",
                "name": "Retry Pattern",
                "category": "recovery",
                "description": "Handle transient failures with exponential backoff",
                "tags": ["recovery", "retry", "reliability"],
                "code_template": """
from tta_dev_primitives.recovery import RetryPrimitive

reliable_workflow = RetryPrimitive(
    primitive=unreliable_operation,
    max_retries=3,
    backoff_strategy="exponential"
)
result = await reliable_workflow.execute(context, data)
""",
                "validation_tests": ["test_retry_logic", "test_backoff_strategy"],
                "complexity_score": 1,
            },
            {
                "id": "cache_primitive_pattern",
                "name": "Cache Pattern",
                "category": "performance",
                "description": "Cache expensive operations with TTL",
                "tags": ["performance", "caching", "optimization"],
                "code_template": """
from tta_dev_primitives.performance import CachePrimitive

cached_operation = CachePrimitive(
    primitive=expensive_llm_call,
    ttl_seconds=3600,  # 1 hour
    max_size=1000
)
result = await cached_operation.execute(context, input_data)
""",
                "validation_tests": [
                    "test_cache_hit",
                    "test_cache_expiry",
                    "test_cache_size_limit",
                ],
                "complexity_score": 1,
            },
            {
                "id": "router_primitive_pattern",
                "name": "Router Pattern",
                "category": "routing",
                "description": "Route to different workflows based on conditions",
                "tags": ["routing", "conditional", "decision"],
                "code_template": """
from tta_dev_primitives import RouterPrimitive

router = RouterPrimitive(routes={
    "fast": gpt4_mini_workflow,
    "complex": gpt4_workflow,
    "local": llama_local_workflow
})
result = await router.execute(context, query_data)
""",
                "validation_tests": ["test_routing_logic", "test_fallback_routing"],
                "complexity_score": 2,
            },
            {
                "id": "iterative_code_generation",
                "name": "Iterative Code Generation",
                "category": "code_generation",
                "description": "Generate and validate code iteratively",
                "tags": ["codegen", "iteration", "validation", "e2b"],
                "code_template": """
class IterativeCodeGenerator:
    def __init__(self):
        self.code_executor = CodeExecutionPrimitive()
        self.max_attempts = 3

    async def generate_working_code(self, requirement: str, context):
        for attempt in range(self.max_attempts):
            # Generate code
            code = await llm_generate_code(requirement, previous_errors)

            # Validate execution
            result = await self.code_executor.execute({"code": code}, context)
            if result["success"]:
                return {"code": code, "output": result["logs"]}

            previous_errors = result["error"]
""",
                "validation_tests": ["test_code_execution", "test_error_handling"],
                "complexity_score": 3,
            },
        ]

        # Insert patterns into database
        with sqlite3.connect(self.patterns_db) as conn:
            for pattern in common_patterns:
                try:
                    conn.execute(
                        """
                        INSERT OR REPLACE INTO patterns
                        (id, name, category, description, tags, usage_count, created_at, code_template, validation_tests, complexity_score)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            pattern["id"],
                            pattern["name"],
                            pattern["category"],
                            pattern["description"],
                            json.dumps(pattern["tags"]),
                            0,
                            datetime.now().isoformat(),
                            pattern.get("code_template"),
                            json.dumps(pattern.get("validation_tests", [])),
                            pattern.get("complexity_score", 1),
                        ),
                    )
                    conn.commit()
                except Exception as e:
                    print(f"Warning: Failed to insert pattern {pattern['id']}: {e}")

    def start_conversation(
        self, persona: str, workflow_type: str, tags: list[str] = None
    ) -> str:
        """Start a new conversation session."""
        session_id = hashlib.md5(
            f"{persona}{workflow_type}{datetime.now().isoformat()}".encode()
        ).hexdigest()[:8]

        with sqlite3.connect(self.conversations_db) as conn:
            conn.execute(
                """
                INSERT INTO conversations (session_id, persona, workflow_type, start_time, tags)
                VALUES (?, ?, ?, ?, ?)
            """,
                (
                    session_id,
                    persona,
                    workflow_type,
                    datetime.now().isoformat(),
                    json.dumps(tags or []),
                ),
            )
            conn.commit()

        return session_id

    def end_conversation(
        self,
        session_id: str,
        success: bool = False,
        summary: str = None,
        key_insights: list[str] = None,
    ):
        """End a conversation session."""
        with sqlite3.connect(self.conversations_db) as conn:
            conn.execute(
                """
                UPDATE conversations
                SET end_time = ?, success = ?, summary = ?, key_insights = ?
                WHERE session_id = ?
            """,
                (
                    datetime.now().isoformat(),
                    1 if success else 0,
                    summary,
                    json.dumps(key_insights or []),
                    session_id,
                ),
            )
            conn.commit()

    def add_message(
        self, session_id: str, role: str, content: str, metadata: dict = None
    ):
        """Add a message to a conversation."""
        with sqlite3.connect(self.conversations_db) as conn:
            conn.execute(
                """
                INSERT INTO messages (session_id, timestamp, role, content, metadata)
                VALUES (?, ?, ?, ?, ?)
            """,
                (
                    session_id,
                    datetime.now().isoformat(),
                    role,
                    content,
                    json.dumps(metadata or {}),
                ),
            )
            conn.commit()

    def record_pattern_usage(
        self,
        pattern_id: str,
        session_id: str,
        success: bool = False,
        feedback: str = None,
    ):
        """Record usage of a pattern."""
        with sqlite3.connect(self.patterns_db) as conn:
            # Update usage count
            conn.execute(
                """
                UPDATE patterns
                SET usage_count = usage_count + 1, last_used = ?
                WHERE id = ?
            """,
                (datetime.now().isoformat(), pattern_id),
            )

            # Record usage instance
            conn.execute(
                """
                INSERT INTO pattern_usage (pattern_id, session_id, used_at, success, feedback)
                VALUES (?, ?, ?, ?, ?)
            """,
                (
                    pattern_id,
                    session_id,
                    datetime.now().isoformat(),
                    1 if success else 0,
                    feedback,
                ),
            )

            conn.commit()

    def find_similar_patterns(
        self, query_description: str, limit: int = 5
    ) -> list[dict]:
        """Find patterns similar to the query description."""
        query_lower = query_description.lower()

        patterns = []
        with sqlite3.connect(self.patterns_db) as conn:
            cursor = conn.execute("""
                SELECT id, name, category, description, tags, usage_count, complexity_score, code_template
                FROM patterns ORDER BY usage_count DESC, complexity_score ASC
            """)

            for row in cursor.fetchall():
                pattern = {
                    "id": row[0],
                    "name": row[1],
                    "category": row[2],
                    "description": row[3],
                    "tags": json.loads(row[4]),
                    "usage_count": row[5],
                    "complexity_score": row[6],
                    "code_template": row[7],
                }

                # Simple relevance scoring
                score = 0
                for tag in pattern["tags"]:
                    if tag.lower() in query_lower:
                        score += 10

                for word in query_lower.split():
                    if word in pattern["description"].lower():
                        score += 5
                    if word in pattern["name"].lower():
                        score += 3

                if score > 0:
                    pattern["relevance_score"] = score
                    patterns.append(pattern)

        # Sort by relevance score and return top matches
        patterns.sort(key=lambda x: x["relevance_score"], reverse=True)
        return patterns[:limit]

    def get_recent_conversations(self, limit: int = 10) -> list[dict]:
        """Get recent conversation summaries."""
        with sqlite3.connect(self.conversations_db) as conn:
            cursor = conn.execute(
                """
                SELECT session_id, persona, workflow_type, start_time, success, summary, tags
                FROM conversations
                ORDER BY start_time DESC
                LIMIT ?
            """,
                (limit,),
            )

            conversations = []
            for row in cursor.fetchall():
                conversations.append(
                    {
                        "session_id": row[0],
                        "persona": row[1],
                        "workflow_type": row[2],
                        "start_time": row[3],
                        "success": bool(row[4]),
                        "summary": row[5],
                        "tags": json.loads(row[6]),
                    }
                )

            return conversations

    def get_popular_patterns(self, limit: int = 10) -> list[dict]:
        """Get most popular patterns."""
        with sqlite3.connect(self.patterns_db) as conn:
            cursor = conn.execute(
                """
                SELECT id, name, category, description, usage_count, complexity_score
                FROM patterns
                ORDER BY usage_count DESC, complexity_score ASC
                LIMIT ?
            """,
                (limit,),
            )

            patterns = []
            for row in cursor.fetchall():
                patterns.append(
                    {
                        "id": row[0],
                        "name": row[1],
                        "category": row[2],
                        "description": row[3],
                        "usage_count": row[4],
                        "complexity_score": row[5],
                    }
                )

            return patterns

    def export_to_logseq(self, logseq_vault_path: str):
        """Export patterns and conversations to Logseq for long-term knowledge persistence."""
        vault_path = Path(logseq_vault_path) / "pages"
        vault_path.mkdir(exist_ok=True)

        # Export patterns
        patterns_page = vault_path / "TTA.dev_Memory_Patterns.md"
        with patterns_page.open("w", encoding="utf-8") as f:
            f.write("# TTA.dev Memory Patterns\n\n")
            f.write("Auto-exported from Cline memory system.\n\n")

            for pattern in self.get_popular_patterns(50):
                f.write(f"## {pattern['name']}\n\n")
                f.write(f"**Category:** {pattern['category']}\n\n")
                f.write(f"**Usage:** {pattern['usage_count']} times\n\n")
                f.write(f"**Complexity:** {pattern['complexity_score']}/5\n\n")
                f.write(f"**Description:** {pattern['description']}\n\n")

                pattern_detail = self.get_pattern_detail(pattern["id"])
                if pattern_detail and pattern_detail.get("code_template"):
                    f.write("### Template\n\n```python\n")
                    f.write(pattern_detail["code_template"].strip())
                    f.write("\n```\n\n")

                f.write("---\n\n")

        # Export conversation insights
        insights_page = vault_path / "TTA.dev_Conversation_Insights.md"
        with insights_page.open("w", encoding="utf-8") as f:
            f.write("# TTA.dev Conversation Insights\n\n")
            f.write("Key learnings from development sessions.\n\n")

            recent = self.get_recent_conversations(20)
            for conv in recent:
                if conv["summary"]:
                    f.write(f"## Session {conv['session_id'][:8]}\n\n")
                    f.write(f"**Persona:** {conv['persona']}\n\n")
                    f.write(f"**Workflow:** {conv['workflow_type']}\n\n")
                    f.write(f"**Success:** {'✅' if conv['success'] else '❌'}\n\n")
                    f.write(f"{conv['summary']}\n\n")
                    f.write("---\n\n")

    def get_pattern_detail(self, pattern_id: str) -> dict | None:
        """Get detailed information about a pattern."""
        with sqlite3.connect(self.patterns_db) as conn:
            cursor = conn.execute(
                """
                SELECT * FROM patterns WHERE id = ?
            """,
                (pattern_id,),
            )

            row = cursor.fetchone()
            if row:
                return {
                    "id": row[0],
                    "name": row[1],
                    "category": row[2],
                    "description": row[3],
                    "tags": json.loads(row[4]),
                    "usage_count": row[5],
                    "last_used": row[6],
                    "created_at": row[7],
                    "code_template": row[8],
                    "validation_tests": json.loads(row[9]),
                    "complexity_score": row[10],
                }
        return None


# Global memory manager instance
memory_manager = MemoryManager()


# Convenience functions
def start_conversation(persona: str, workflow_type: str, tags: list[str] = None) -> str:
    """Start a new conversation session."""
    return memory_manager.start_conversation(persona, workflow_type, tags)


def end_conversation(
    session_id: str,
    success: bool = False,
    summary: str = None,
    key_insights: list[str] = None,
):
    """End a conversation session."""
    memory_manager.end_conversation(session_id, success, summary, key_insights)


def find_similar_patterns(query: str, limit: int = 5) -> list[dict]:
    """Find patterns similar to the query."""
    return memory_manager.find_similar_patterns(query, limit)


def get_recent_conversations(limit: int = 10) -> list[dict]:
    """Get recent conversation summaries."""
    return memory_manager.get_recent_conversations(limit)


def record_pattern_usage(
    pattern_id: str, session_id: str, success: bool = False, feedback: str = None
):
    """Record usage of a pattern."""
    memory_manager.record_pattern_usage(pattern_id, session_id, success, feedback)


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "search":
            if len(sys.argv) > 2:
                query = " ".join(sys.argv[2:])
                patterns = find_similar_patterns(query)
                for pattern in patterns:
                    print(f"📋 {pattern['name']} ({pattern['category']})")
                    print(f"   {pattern['description']}")
                    print(
                        f"   Relevance: {pattern.get('relevance_score', 0)}, Usage: {pattern['usage_count']}"
                    )
                    print()
            else:
                print("Usage: python memory-manager.py search <query>")

        elif command == "recent":
            conversations = get_recent_conversations()
            for conv in conversations:
                print(
                    f"💬 {conv['session_id'][:8]} - {conv['persona']} - {conv['workflow_type']}"
                )
                if conv["summary"]:
                    print(f"   {conv['summary'][:100]}...")
                print()

        elif command == "patterns":
            patterns = memory_manager.get_popular_patterns()
            for pattern in patterns:
                print(f"📋 {pattern['name']} - Used {pattern['usage_count']} times")

        elif command == "export":
            if len(sys.argv) > 2:
                logseq_path = sys.argv[2]
                memory_manager.export_to_logseq(logseq_path)
                print(f"Exported to Logseq vault: {logseq_path}")
            else:
                print("Usage: python memory-manager.py export <logseq-vault-path>")

        else:
            print("Commands: search <query>, recent, patterns, export <path>")

    else:
        print("TTA.dev Memory Manager")
        print(f"Conversations DB: {memory_manager.conversations_db}")
        print(f"Patterns DB: {memory_manager.patterns_db}")
        print(f"Loaded {len(memory_manager.get_popular_patterns())} patterns")
