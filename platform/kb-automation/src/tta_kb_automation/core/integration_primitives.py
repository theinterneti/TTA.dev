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
            "kb_path": str,           # KB root path (optional, default: "logseq")
        }

    Output:
        {
            "success": bool,
            "file_path": str,
            "created": bool           # True if new page
        }
    """

    def __init__(self, kb_path: str | Path = "logseq"):
        """Initialize UpdateKBPage primitive."""
        super().__init__(name="update_kb_page")
        self.kb_path = Path(kb_path)

    async def _execute_impl(
        self,
        input_data: dict,
        context: WorkflowContext,
    ) -> dict:
        """Update KB page with content."""
        page_name = input_data["page_name"]
        content = input_data["content"]
        mode = input_data.get("mode", "append")
        kb_path = Path(input_data.get("kb_path", self.kb_path))

        # Ensure page name has .md extension
        if not page_name.endswith(".md"):
            page_name = page_name + ".md"

        # Handle hierarchical page names (TTA.dev/Feature -> TTA.dev___Feature.md)
        safe_name = page_name.replace("/", "___")
        page_path = kb_path / "pages" / safe_name

        # Ensure directory exists
        page_path.parent.mkdir(parents=True, exist_ok=True)

        # Check if page exists
        created = not page_path.exists()

        if created or mode == "replace":
            # Create new or replace entirely
            page_path.write_text(content, encoding="utf-8")
        elif mode == "append":
            # Append to existing
            existing = page_path.read_text(encoding="utf-8")
            page_path.write_text(existing + "\n" + content, encoding="utf-8")
        elif mode == "prepend":
            # Prepend to existing
            existing = page_path.read_text(encoding="utf-8")
            page_path.write_text(content + "\n" + existing, encoding="utf-8")
        else:
            raise ValueError(
                f"Invalid mode: {mode}. Use 'append', 'prepend', or 'replace'"
            )

        return {
            "success": True,
            "file_path": str(page_path),
            "created": created,
            "mode": mode,
        }


class GenerateReport(InstrumentedPrimitive[dict, dict]):
    """Generate markdown report from data.

    Input:
        {
            "data": dict,             # Report data
            "template": str,          # Template name: "validation", "todos", "cross_refs", "custom"
            "output_path": str,       # Output file path (optional)
            "title": str,             # Report title (optional)
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
        """Generate markdown report from data."""
        from datetime import datetime

        data = input_data["data"]
        template = input_data.get("template", "custom")
        output_path = input_data.get("output_path")
        title = input_data.get("title", "Report")

        # Generate report based on template
        if template == "validation":
            report = self._generate_validation_report(data, title)
        elif template == "todos":
            report = self._generate_todos_report(data, title)
        elif template == "cross_refs":
            report = self._generate_cross_refs_report(data, title)
        else:
            report = self._generate_custom_report(data, title)

        # Add timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        report = f"<!-- Generated: {timestamp} -->\n\n{report}"

        # Write to file if output path provided
        file_path = None
        if output_path:
            file_path = Path(output_path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(report, encoding="utf-8")

        return {
            "success": True,
            "report": report,
            "file_path": str(file_path) if file_path else None,
        }

    def _generate_validation_report(self, data: dict, title: str) -> str:
        """Generate link validation report."""
        lines = [
            f"# {title}",
            "",
            "## Summary",
            "",
            f"- **Total Pages**: {data.get('total_pages', 0)}",
            f"- **Valid Links**: {data.get('total_valid', 0)}",
            f"- **Broken Links**: {data.get('total_broken', 0)}",
            f"- **Orphaned Pages**: {data.get('total_orphaned', 0)}",
            "",
        ]

        # Broken links section
        broken = data.get("broken_links", [])
        if broken:
            lines.extend(["## Broken Links", ""])
            for link in broken[:50]:  # Limit to 50
                lines.append(
                    f"- `{link.get('source', '?')}` → [[{link.get('target', '?')}]]"
                )
            lines.append("")

        # Orphaned pages section
        orphaned = data.get("orphaned_pages", [])
        if orphaned:
            lines.extend(["## Orphaned Pages", ""])
            for page in orphaned[:50]:
                lines.append(f"- {page}")
            lines.append("")

        return "\n".join(lines)

    def _generate_todos_report(self, data: dict, title: str) -> str:
        """Generate TODOs report."""
        lines = [
            f"# {title}",
            "",
            "## Summary",
            "",
            f"- **Total TODOs**: {data.get('total_todos', 0)}",
            f"- **Files with TODOs**: {data.get('files_with_todos', 0)}",
            "",
            "## TODOs by File",
            "",
        ]

        todos = data.get("todos", [])
        by_file: dict[str, list] = {}
        for todo in todos:
            f = todo.get("file", "unknown")
            by_file.setdefault(f, []).append(todo)

        for file, file_todos in by_file.items():
            lines.append(f"### `{file}`")
            lines.append("")
            for t in file_todos:
                lines.append(
                    f"- Line {t.get('line_number', '?')}: {t.get('todo_text', '?')}"
                )
            lines.append("")

        return "\n".join(lines)

    def _generate_cross_refs_report(self, data: dict, title: str) -> str:
        """Generate cross-references report."""
        lines = [
            f"# {title}",
            "",
            "## Statistics",
            "",
        ]

        stats = data.get("stats", {})
        lines.extend(
            [
                f"- **KB Pages**: {stats.get('total_kb_pages', 0)}",
                f"- **Code Files**: {stats.get('total_code_files', 0)}",
                f"- **KB → Code References**: {stats.get('kb_pages_with_code_refs', 0)}",
                f"- **Code → KB References**: {stats.get('code_files_with_kb_refs', 0)}",
                "",
            ]
        )

        # Missing references
        missing = data.get("missing_references", [])
        if missing:
            lines.extend(["## Missing References", ""])
            for ref in missing[:30]:
                lines.append(f"- {ref.get('type', '?')}: `{ref.get('reference', '?')}`")
                if ref.get("suggestion"):
                    lines.append(f"  - {ref['suggestion']}")
            lines.append("")

        return "\n".join(lines)

    def _generate_custom_report(self, data: dict, title: str) -> str:
        """Generate generic report from dict data."""
        import json

        lines = [
            f"# {title}",
            "",
            "## Data",
            "",
            "```json",
            json.dumps(data, indent=2, default=str),
            "```",
        ]

        return "\n".join(lines)
