"""Integration primitives for KB automation.

These primitives handle creating and updating KB content.
"""

from pathlib import Path

from tta_dev_primitives import WorkflowContext
from tta_dev_primitives.observability import InstrumentedPrimitive


class CreateJournalEntry(InstrumentedPrimitive[dict, dict]):
    """Create or update journal entry for TODO tracking.

    Input:
        {
            "date": str,              # Journal date (YYYY-MM-DD or YYYY_MM_DD)
            "content": str,           # Entry content
            "section": str,           # Section name (optional)
        }

    Output:
        {
            "success": bool,
            "file_path": str,
            "created": bool           # True if new, False if updated
        }
    """

    def __init__(self):
        """Initialize CreateJournalEntry primitive."""
        super().__init__(name="create_journal_entry")

    async def _execute_impl(
        self,
        input_data: dict,
        context: WorkflowContext,
    ) -> dict:
        """Create journal entry with TODOs."""
        date_str = input_data["date"]
        todos = input_data.get("todos", [])
        output_dir = input_data.get("output_dir")

        # Determine journal path
        if output_dir:
            journal_dir = Path(output_dir)
        else:
            # Default to logseq/journals
            workspace_root = Path.cwd()
            journal_dir = workspace_root / "logseq" / "journals"

        journal_dir.mkdir(parents=True, exist_ok=True)
        journal_path = journal_dir / f"{date_str}.md"

        # Format journal entry
        lines = []

        # Header
        lines.append(f"# {self._format_date_header(date_str)}")
        lines.append("")

        # TODOs section
        if todos:
            lines.append("## 🔧 Code TODOs (Auto-generated)")
            lines.append("")

            for todo in todos:
                # Main TODO line
                message = todo.get("message", todo.get("todo_text", "Unknown TODO"))
                lines.append(f"- TODO {message} #dev-todo")

                # Properties
                if "type" in todo:
                    lines.append(f"  type:: {todo['type']}")
                if "priority" in todo:
                    lines.append(f"  priority:: {todo['priority']}")
                if "package" in todo:
                    lines.append(f"  package:: {todo['package']}")

                # Source location
                file_path = todo.get("file", "unknown")
                line_num = todo.get("line_number", "?")
                lines.append(f"  source:: {file_path}:{line_num}")

                # Suggested KB links
                for link in todo.get("suggested_links", []):
                    lines.append(f"  related:: [[{link}]]")

                lines.append("")  # Blank line between TODOs

        # Write to file
        content = "\n".join(lines)
        journal_path.write_text(content, encoding="utf-8")

        return {
            "path": str(journal_path),
            "todos_written": len(todos),
            "date": date_str,
        }

    def _format_date_header(self, date_str: str) -> str:
        """Format date string as readable header.

        Converts YYYY_MM_DD to "Month DD, YYYY" format.
        """
        try:
            from datetime import datetime

            # Parse YYYY_MM_DD or YYYY-MM-DD
            date_str_normalized = date_str.replace("_", "-")
            date_obj = datetime.strptime(date_str_normalized, "%Y-%m-%d")
            return date_obj.strftime("%B %d, %Y")
        except Exception:
            # Fallback to original string
            return date_str


class UpdateKBPage(InstrumentedPrimitive[dict, dict]):
    """Update KB page with new content.

    Input:
        {
            "page_name": str,         # Page name (with or without .md)
            "content": str,           # New content or section to add
            "mode": str,              # "append" | "prepend" | "replace"
        }

    Output:
        {
            "success": bool,
            "file_path": str,
            "created": bool           # True if new page
        }
    """

    def __init__(self):
        """Initialize UpdateKBPage primitive."""
        super().__init__(name="update_kb_page")

    async def _execute_impl(
        self,
        input_data: dict,
        context: WorkflowContext,
    ) -> dict:
        """Update KB page (stub implementation)."""
        # TODO: Implement KB page updates
        raise NotImplementedError("UpdateKBPage not yet implemented")


class GenerateReport(InstrumentedPrimitive[dict, dict]):
    """Generate markdown report from data.

    Input:
        {
            "data": dict,             # Report data
            "template": str,          # Template name or custom template
            "output_path": str,       # Output file path (optional)
        }

    Output:
        {
            "success": bool,
            "report": str,            # Generated markdown
            "file_path": str,         # Output path (if provided)
        }
    """

    def __init__(self):
        """Initialize GenerateReport primitive."""
        super().__init__(name="generate_report")

    async def _execute_impl(
        self,
        input_data: dict,
        context: WorkflowContext,
    ) -> dict:
        """Generate report (stub implementation)."""
        # TODO: Implement report generation
        raise NotImplementedError("GenerateReport not yet implemented")
