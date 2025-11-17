"""
Workflow to create a new Logseq page summarizing a development session.
"""

from pathlib import Path
from typing import Any

from tta_dev_primitives import WorkflowContext

from ..tools.session_context_builder import SessionContextBuilder


class CreateSessionPage:
    """
    A workflow to build a session context and create a Logseq page from it.
    """

    def __init__(
        self,
        kb_path: str | Path = "logseq",
        code_path: str | Path = "packages",
        output_dir: str | Path = "logseq/pages",
    ):
        self.kb_path = Path(kb_path)
        self.code_path = Path(code_path)
        self.output_dir = Path(output_dir)
        self.session_builder = SessionContextBuilder(kb_path=self.kb_path, code_path=self.code_path)

    async def run(self, topic: str) -> Path:
        """
        Runs the workflow to generate a session page for the given topic.

        Args:
            topic: The topic for the development session.

        Returns:
            The path to the newly created Logseq page.
        """
        WorkflowContext(
            workflow_id=f"create_session_page_{topic.lower().replace(' ', '_')}"
        )

        # 1. Build the context
        context = await self.session_builder.build_context(topic)

        # 2. Format the context as a Logseq page
        page_content = self._format_as_logseq_page(context)

        # 3. Write the page to a file
        page_title = f"Session Context___ {topic}.md"
        output_path = self.output_dir / page_title
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(page_content)

        return output_path

    def _format_as_logseq_page(self, context: dict[str, Any]) -> str:
        """
        Formats the context dictionary into a markdown string for Logseq.
        """
        topic = context["topic"]
        lines = [
            f"# Session Context: [[{topic}]]",
            "type:: [[Session Context]]",
            f"topic:: [[{topic}]]",
            "",
        ]

        if context.get("related_topics"):
            related_str = ", ".join(f"[[{t}]]" for t in context["related_topics"])
            lines.append(f"## Related Topics\n- {related_str}\n")

        if context.get("kb_pages"):
            lines.append("## 🧠 Knowledge Base Pages")
            for page in context["kb_pages"]:
                lines.append(f"- [[{page['title']}]]")
                lines.append(f"  - `src: {page['path']}`")
                lines.append(f"  - > {page['excerpt']}")
            lines.append("")

        if context.get("code_files"):
            lines.append("## 💻 Code Files")
            for file in context["code_files"]:
                lines.append(f"- `{file['path']}`")
                if file.get("classes"):
                    lines.append(f"  - **Classes**: {', '.join(file['classes'])}")
                if file.get("functions"):
                    lines.append(f"  - **Functions**: {', '.join(file['functions'])}")
                if file.get("summary"):
                    lines.append(f"  - **Summary**: {file['summary']}")
            lines.append("")

        if context.get("todos"):
            lines.append("## ✅ TODOs")
            for todo in context["todos"]:
                lines.append(f"- [ ] {todo['text']}")
                lines.append(f"  - `src: {todo['file_path']}:{todo['line_number']}`")
            lines.append("")

        if context.get("tests"):
            lines.append("## 🧪 Tests")
            for test in context["tests"]:
                lines.append(f"- `{test['path']}`")
                lines.append(f"  - **Test Count**: {test['test_count']}")
                if test.get("test_names"):
                    lines.append(f"  - **Tests**: {', '.join(test['test_names'])}")
            lines.append("")

        return "\n".join(lines)
