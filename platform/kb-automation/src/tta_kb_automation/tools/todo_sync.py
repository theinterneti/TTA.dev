"""TODO Sync Tool - Bridge code comments and KB journal entries.

This tool scans Python codebases for TODO comments and creates structured
Logseq journal entries with proper properties and linking.
"""

from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any

from tta_dev_primitives import WorkflowContext
from tta_dev_primitives.core import RouterPrimitive
from tta_dev_primitives.observability import InstrumentedPrimitive

from ..core.code_primitives import ExtractTODOs, ScanCodebase
from ..core.integration_primitives import CreateJournalEntry
from ..core.intelligence_primitives import ClassifyTODO, SuggestKBLinks


class FunctionPrimitive(InstrumentedPrimitive[dict, dict]):
    """Wrapper to convert a function into a WorkflowPrimitive."""

    def __init__(self, name: str, func: Callable[[dict, WorkflowContext], Any]) -> None:
        """Initialize with a function."""
        super().__init__(name=name)
        self._func = func

    async def _execute_impl(self, input_data: dict, context: WorkflowContext) -> dict:
        """Execute the wrapped function."""
        return await self._func(input_data, context)


class TODOSync:
    """Sync code TODOs to Logseq journal entries.

    Workflow:
        1. ScanCodebase - Find all Python files
        2. ExtractTODOs - Parse TODO comments with context
        3. RouterPrimitive - Route each TODO for classification
        4. ClassifyTODO - Determine type, priority, package
        5. SuggestKBLinks - Find relevant KB pages
        6. CreateJournalEntry - Format and write to journal

    Example:
        ```python
        from tta_kb_automation import TODOSync

        sync = TODOSync()
        result = await sync.scan_and_create(
            paths=["packages/tta-dev-primitives/src"],
            journal_date="2025-11-03"
        )

        print(f"Created {result['todos_created']} journal entries")
        ```
    """

    def __init__(self) -> None:
        """Initialize TODO sync tool with primitive composition."""
        # Phase 1: Scan and extract
        self._scanner = ScanCodebase()
        self._extractor = ExtractTODOs()

        # Phase 2: Classify and enhance (routing for complex TODOs)
        self._classifier = ClassifyTODO()
        self._linker = SuggestKBLinks()

        # Phase 3: Create journal entries
        self._journal_writer = CreateJournalEntry()

        # Router for intelligent TODO processing
        # Wrap methods as primitives
        self._simple_processor = FunctionPrimitive(
            "simple_todo_processor", self._process_simple_todo
        )
        self._complex_processor = FunctionPrimitive(
            "complex_todo_processor", self._process_complex_todo
        )

        self._todo_router = RouterPrimitive(
            routes={
                "simple": self._simple_processor,
                "complex": self._complex_processor,
            },
            router_fn=self._route_todo,
        )

    def _route_todo(self, todo: dict, context: WorkflowContext) -> str:
        """Route TODO to simple or complex processing.

        Simple: Clear, single-file, no cross-cutting concerns
        Complex: Architectural, multi-file, needs classification
        """
        # Handle both "message" and "todo_text" keys for compatibility
        message = todo.get("message", todo.get("todo_text", "")).lower()

        # Complex indicators
        if any(
            keyword in message
            for keyword in [
                "architecture",
                "refactor",
                "integration",
                "distributed",
                "observability",
                "performance",
            ]
        ):
            return "complex"

        # Check if spans multiple concerns (look for AND/OR)
        if any(word in message for word in [" and ", " or ", "multiple"]):
            return "complex"

        # Default to simple
        return "simple"

    async def _process_simple_todo(self, todo: dict, context: WorkflowContext) -> dict:
        """Process simple TODO with basic classification."""
        # Normalize TODO structure (handle both "message" and "todo_text")
        if "todo_text" in todo and "message" not in todo:
            todo["message"] = todo["todo_text"]

        # Infer type from TODO category
        type_mapping = {
            "TODO": "implementation",
            "FIXME": "bugfix",
            "HACK": "refactoring",
            "NOTE": "documentation",
            "XXX": "investigation",
        }

        # Infer priority from urgency keywords
        message = todo.get("message", "").lower()
        if any(word in message for word in ["urgent", "critical", "asap", "blocker"]):
            priority = "high"
        elif any(word in message for word in ["later", "someday", "nice to have"]):
            priority = "low"
        else:
            priority = "medium"

        # Infer package from file path
        file_path = Path(todo.get("file", "unknown.py"))
        package = self._extract_package_from_path(file_path)

        return {
            **todo,
            "type": type_mapping.get(todo.get("type", "TODO"), "implementation"),
            "priority": priority,
            "package": package,
            "suggested_links": [],  # No KB links for simple TODOs
        }

    async def _process_complex_todo(self, todo: dict, context: WorkflowContext) -> dict:
        """Process complex TODO with full classification and linking."""
        # Normalize TODO structure (handle both "message" and "todo_text")
        if "todo_text" in todo and "message" not in todo:
            todo["message"] = todo["todo_text"]

        # Use classifier primitive
        classification = await self._classifier.execute(
            {"todo": todo, "file_path": todo["file"]}, context
        )

        # Use linker primitive
        links = await self._linker.execute(
            {"todo": todo, "context": todo.get("context_before", [])}, context
        )

        return {
            **todo,
            "type": classification.get("type", "implementation"),
            "priority": classification.get("priority", "medium"),
            "package": classification.get(
                "package", self._extract_package_from_path(Path(todo["file"]))
            ),
            "suggested_links": links.get("links", []),
        }

    def _extract_package_from_path(self, file_path: Path) -> str:
        """Extract package name from file path.

        Looks for packages/*/src pattern or falls back to first directory.
        """
        parts = file_path.parts

        # Try to find packages/NAME/src pattern
        try:
            if "packages" in parts:
                idx = parts.index("packages")
                if idx + 1 < len(parts):
                    return parts[idx + 1]
        except (ValueError, IndexError):
            pass

        # Fallback: use first directory after root
        if len(parts) > 1:
            return parts[1]

        return "unknown"

    async def scan_and_create(
        self,
        paths: list[str],
        journal_date: str | None = None,
        include_tests: bool = False,
        context_lines: int = 2,
        dry_run: bool = False,
        output_dir: str | None = None,
    ) -> dict[str, Any]:
        """Scan code for TODOs and create journal entries.

        Args:
            paths: List of paths to scan (files or directories)
            journal_date: Date for journal in YYYY-MM-DD format (default: today)
            include_tests: Whether to scan test files (default: False)
            context_lines: Lines of context to capture (default: 2)
            dry_run: If True, don't create journal files (just return data)
            output_dir: Custom output directory for journal files (for testing)

        Returns:
            {
                "todos_found": int,
                "todos_created": int,
                "journal_path": str,
                "todos": List[dict]  # Enhanced TODOs with classification
            }
        """
        context = WorkflowContext()

        # Use today's date if not specified
        if journal_date is None:
            journal_date = datetime.now().strftime("%Y-%m-%d")

        all_todos = []

        # Phase 1: Scan and extract from each path
        for path in paths:
            # Scan for Python files
            scan_result = await self._scanner.execute(
                {"root_path": path, "include_tests": include_tests}, context
            )

            if scan_result["total_files"] == 0:
                continue

            # Extract TODOs
            extract_result = await self._extractor.execute(
                {
                    "files": scan_result["files"],
                    "include_context": True,
                    "context_lines": context_lines,
                },
                context,
            )

            all_todos.extend(extract_result["todos"])

        # Phase 2: Process each TODO through router
        enhanced_todos = []
        for todo in all_todos:
            # Route to simple or complex processing
            enhanced = await self._todo_router.execute(todo, context)
            enhanced_todos.append(enhanced)

        # Phase 3: Create journal entries (unless dry_run)
        journal_path = f"logseq/journals/{journal_date.replace('-', '_')}.md"

        if not dry_run:
            journal_input = {
                "date": journal_date,
                "todos": enhanced_todos,
            }
            if output_dir:
                journal_input["output_dir"] = output_dir

            journal_result = await self._journal_writer.execute(journal_input, context)
            journal_path = journal_result.get("path", journal_path)

        return {
            "todos_found": len(all_todos),
            "todos_created": len(enhanced_todos) if not dry_run else 0,
            "journal_path": journal_path,
            "todos": enhanced_todos,
        }

    def format_todo_entry(self, todo: dict) -> str:
        """Format a single TODO as Logseq journal entry.

        This is a convenience method for generating the markdown format.
        The actual journal writing is handled by CreateJournalEntry primitive.
        """
        lines = []

        # Main TODO line
        lines.append(f"- TODO {todo['message']} #dev-todo")

        # Properties
        lines.append(f"  type:: {todo.get('type', 'implementation')}")
        lines.append(f"  priority:: {todo.get('priority', 'medium')}")

        if "package" in todo:
            lines.append(f"  package:: {todo['package']}")

        # Source location
        file_path = todo["file"]
        line_num = todo.get("line_number", "?")
        lines.append(f"  source:: {file_path}:{line_num}")

        # Context (if available)
        if todo.get("context_before") or todo.get("context_after"):
            lines.append(f'  context:: "{todo["message"]}"')

        # Suggested KB links
        for link in todo.get("suggested_links", []):
            lines.append(f"  related:: [[{link}]]")

        return "\n".join(lines)
