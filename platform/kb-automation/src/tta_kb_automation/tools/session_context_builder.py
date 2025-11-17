"""Session context builder - generates synthetic context for agents.

This tool aggregates relevant KB pages, code files, TODOs, and tests
to provide comprehensive context from minimal input.

Example:
    builder = SessionContextBuilder(kb_path="logseq", code_path="packages")
    context = await builder.build_context(topic="CachePrimitive")
"""

import re
from pathlib import Path
from typing import Any

from tta_dev_primitives import WorkflowContext
from tta_dev_primitives.observability import InstrumentedPrimitive

from ..core import (
    AnalyzeCodeStructure,
    ExtractTODOs,
    ParseDocstrings,
    ParseLogseqPages,
    ScanCodebase,
)


class RankByRelevance(InstrumentedPrimitive[dict, dict]):
    """Rank items by relevance to a topic."""

    def __init__(self, topic: str, max_results: int = 10) -> None:
        super().__init__(name="rank_by_relevance")
        self.topic = topic.lower()
        self.max_results = max_results

    async def _execute_impl(self, input_data: dict, context: WorkflowContext) -> dict:
        """Rank items by relevance score."""
        items = input_data.get("items", [])

        scored_items = []
        for item in items:
            score = self._calculate_relevance(item)
            scored_items.append({"item": item, "score": score})

        # Sort by score descending
        scored_items.sort(key=lambda x: x["score"], reverse=True)

        # Take top N
        top_items = scored_items[: self.max_results]

        return {
            "ranked_items": [x["item"] for x in top_items],
            "scores": [x["score"] for x in top_items],
            "total_scored": len(items),
        }

    def _calculate_relevance(self, item: Any) -> float:
        """Calculate relevance score (0.0 to 1.0)."""
        score = 0.0

        # Check different fields depending on item type
        text_to_search = ""

        if isinstance(item, dict):
            # KB page or code file
            text_to_search = " ".join(
                [
                    str(item.get("title", "")),
                    str(item.get("content", ""))[:1000],  # First 1000 chars
                    str(item.get("path", "")),
                    " ".join(item.get("tags", [])),
                ]
            )
        elif isinstance(item, (str, Path)):
            text_to_search = str(item)
        else:
            text_to_search = str(item)

        text_to_search = text_to_search.lower()

        # Exact match in title/path = highest score
        if self.topic in text_to_search:
            score += 1.0

        # Word boundary match (e.g., "cache" matches "CachePrimitive")
        topic_words = re.split(r"[ _\-]", self.topic)
        for word in topic_words:
            if word and word in text_to_search:
                score += 0.3

        # Fuzzy match (each character present)
        if all(char in text_to_search for char in self.topic):
            score += 0.1

        return min(score, 1.0)  # Cap at 1.0


class SessionContextBuilder:
    """Build synthetic session context for agents.

    Aggregates relevant KB pages, code files, TODOs, and tests to provide
    comprehensive context from minimal input (just a topic name).

    Usage:
        builder = SessionContextBuilder(kb_path="logseq", code_path="packages")
        context = await builder.build_context(topic="CachePrimitive")
    """

    def __init__(
        self,
        kb_path: str | Path = "logseq",
        code_path: str | Path = "packages",
        max_kb_pages: int = 5,
        max_code_files: int = 10,
        max_todos: int = 20,
        max_tests: int = 10,
    ):
        """Initialize Session Context Builder.

        Args:
            kb_path: Path to Logseq KB root (default: "logseq")
            code_path: Path to code root (default: "packages")
            max_kb_pages: Maximum KB pages to include (default: 5)
            max_code_files: Maximum code files to include (default: 10)
            max_todos: Maximum TODOs to include (default: 20)
            max_tests: Maximum test files to include (default: 10)
        """
        self.kb_path = Path(kb_path)
        self.code_path = Path(code_path)
        self.max_kb_pages = max_kb_pages
        self.max_code_files = max_code_files
        self.max_todos = max_todos
        self.max_tests = max_tests

    async def build_context(
        self,
        topic: str,
        include_kb: bool = True,
        include_code: bool = True,
        include_todos: bool = True,
        include_tests: bool = True,
    ) -> dict:
        """Build synthetic context for topic.

        Args:
            topic: Topic or feature name to build context for
            include_kb: Include KB pages (default: True)
            include_code: Include code files (default: True)
            include_todos: Include TODOs (default: True)
            include_tests: Include test files (default: True)

        Returns:
            Dictionary with:
            - topic: str - The topic name
            - kb_pages: List[dict] - Relevant KB pages with excerpts
            - code_files: List[dict] - Relevant code files with summaries
            - todos: List[dict] - Relevant TODOs
            - tests: List[dict] - Relevant test files
            - related_topics: List[str] - Related topics found
            - summary: str - Human-readable summary
        """
        context_parts = {"topic": topic, "related_topics": []}

        workflow_context = WorkflowContext(
            workflow_id=f"session_context_{topic.lower().replace(' ', '_')}"
        )

        # 1. Find relevant KB pages
        if include_kb:
            kb_pages = await self._find_relevant_kb_pages(topic, workflow_context)
            context_parts["kb_pages"] = kb_pages

            # Extract related topics from KB pages
            for page in kb_pages:
                related = self._extract_related_topics(page)
                context_parts["related_topics"].extend(related)

        # 2. Find relevant code files
        if include_code:
            code_files = await self._find_relevant_code_files(topic, workflow_context)
            context_parts["code_files"] = code_files

        # 3. Find relevant TODOs
        if include_todos:
            todos = await self._find_relevant_todos(topic, workflow_context)
            context_parts["todos"] = todos

        # 4. Find relevant tests
        if include_tests:
            tests = await self._find_relevant_tests(topic, workflow_context)
            context_parts["tests"] = tests

        # Deduplicate related topics
        context_parts["related_topics"] = list(set(context_parts["related_topics"]))

        # Generate summary
        context_parts["summary"] = self._generate_summary(context_parts)

        return context_parts

    async def _find_relevant_kb_pages(self, topic: str, context: WorkflowContext) -> list[dict]:
        """Find KB pages relevant to topic."""
        # Parse all KB pages
        parser = ParseLogseqPages(kb_path=self.kb_path)
        parse_result = await parser.execute({}, context)
        pages = parse_result["pages"]

        # Rank by relevance
        ranker = RankByRelevance(topic=topic, max_results=self.max_kb_pages)
        rank_result = await ranker.execute({"items": pages}, context)

        # Format for output
        formatted = []
        for page in rank_result["ranked_items"]:
            excerpt = self._extract_excerpt(page["content"], topic, max_chars=300)
            formatted.append(
                {
                    "path": str(page["path"]),
                    "title": page["title"],
                    "excerpt": excerpt,
                    "tags": page.get("tags", []),
                    "is_journal": page.get("is_journal", False),
                }
            )

        return formatted

    async def _find_relevant_code_files(self, topic: str, context: WorkflowContext) -> list[dict]:
        """Find code files relevant to topic."""
        # Scan codebase
        # ScanCodebase expects its inputs via the execute() payload (root_path),
        # not via the constructor. Provide the code_path as 'root_path'.
        scanner = ScanCodebase()
        scan_result = await scanner.execute({"root_path": str(self.code_path)}, context)
        files = scan_result["files"]

        # Rank by relevance
        ranker = RankByRelevance(topic=topic, max_results=self.max_code_files)
        rank_result = await ranker.execute({"items": files}, context)

        # Parse docstrings for ranked files
        formatted = []
        for file_path in rank_result["ranked_items"]:
            parser = ParseDocstrings()
            # Parse the single file by passing it as a one-item 'files' list
            doc_result = await parser.execute({"files": [str(file_path)]}, context)

            # ParseDocstrings returns a list of docstring entries; extract module/class/function info
            doc_entries = doc_result.get("docstrings", [])

            module_entry = next(
                (
                    d
                    for d in doc_entries
                    if d.get("type") == "module" and d.get("file") == str(file_path)
                ),
                None,
            )

            class_entries = [
                d
                for d in doc_entries
                if d.get("type") == "class" and d.get("file") == str(file_path)
            ]
            func_entries = [
                d
                for d in doc_entries
                if d.get("type") == "function" and d.get("file") == str(file_path)
            ]

            summary = module_entry.get("docstring", "") if module_entry else ""
            if not summary and class_entries:
                summary = class_entries[0].get("docstring", "")

            formatted.append(
                {
                    "path": str(file_path),
                    "summary": summary[:500] if summary else "No docstring",
                    "classes": [c.get("name") for c in class_entries],
                    "functions": [f.get("name") for f in func_entries],
                }
            )

        return formatted

    async def _find_relevant_todos(self, topic: str, context: WorkflowContext) -> list[dict]:
        """Find TODOs relevant to topic."""
        # Scan for TODOs in code
        scanner = ScanCodebase()
        scan_result = await scanner.execute(
            {"root_path": str(self.code_path), "include_tests": False}, context
        )
        files = scan_result["files"]

        all_todos = []
        extractor = ExtractTODOs()

        # Extract TODOs from each file
        for file_path in files:
            try:
                result = await extractor.execute({"file_path": Path(file_path)}, context)
                for todo in result["todos"]:
                    # Add relevance check
                    if topic.lower() in todo["text"].lower():
                        all_todos.append(todo)
            except Exception:
                # Skip files that can't be parsed
                continue

        # Sort by relevance (simple text match for now)
        all_todos.sort(key=lambda t: topic.lower() in t["text"].lower(), reverse=True)

        return all_todos[: self.max_todos]

    async def _find_relevant_tests(self, topic: str, context: WorkflowContext) -> list[dict]:
        """Find test files relevant to topic."""
        # Scan for test files
        scanner = ScanCodebase()
        scan_result = await scanner.execute(
            {
                "root_path": str(self.code_path),
                "include_tests": True,
                "exclude_patterns": ["**/src/**"],  # Only get tests/
            },
            context,
        )
        test_files = [f for f in scan_result["files"] if "test" in str(f).lower()]

        # Rank by relevance
        ranker = RankByRelevance(topic=topic, max_results=self.max_tests)
        rank_result = await ranker.execute({"items": test_files}, context)

        # Analyze test structure
        formatted = []
        for test_path in rank_result["ranked_items"]:
            analyzer = AnalyzeCodeStructure()
            analysis = await analyzer.execute({"files": [str(test_path)]}, context)

            test_functions = [
                name for name in analysis.get("functions", []) if name.startswith("test_")
            ]

            formatted.append(
                {
                    "path": str(test_path),
                    "test_count": len(test_functions),
                    "test_names": test_functions[:5],  # First 5 tests
                }
            )

        return formatted

    def _extract_related_topics(self, kb_page: dict) -> list[str]:
        """Extract related topics from KB page (from [[links]] and #tags)."""
        related = []

        # Add linked pages
        related.extend(kb_page.get("links", []))

        # Add tags
        related.extend(kb_page.get("tags", []))

        return [topic for topic in related if len(topic) > 2]  # Filter very short

    def _extract_excerpt(self, content: str, topic: str, max_chars: int = 300) -> str:
        """Extract relevant excerpt from content around topic mention."""
        topic_lower = topic.lower()
        content_lower = content.lower()

        # Find first occurrence of topic
        idx = content_lower.find(topic_lower)

        if idx == -1:
            # Topic not found, return start of content
            return content[:max_chars].strip() + "..."

        # Extract around topic mention
        # Try to show some chars before topic, but keep total at max_chars
        chars_before = min(100, max_chars // 2)
        start = max(0, idx - chars_before)
        actual_chars_before = idx - start
        # Remaining budget for topic + chars after
        remaining = max_chars - actual_chars_before
        end = min(len(content), idx + remaining)

        excerpt = content[start:end].strip()

        # Add ellipsis if truncated
        if start > 0:
            excerpt = "..." + excerpt
        if end < len(content):
            excerpt = excerpt + "..."

        return excerpt

    def _generate_summary(self, context_parts: dict) -> str:
        """Generate human-readable summary of context."""
        topic = context_parts["topic"]
        lines = [f"# Session Context: {topic}", ""]

        kb_pages = context_parts.get("kb_pages", [])
        code_files = context_parts.get("code_files", [])
        todos = context_parts.get("todos", [])
        tests = context_parts.get("tests", [])
        related = context_parts.get("related_topics", [])

        lines.append(f"**Found {len(kb_pages)} relevant KB pages**")
        lines.append(f"**Found {len(code_files)} relevant code files**")
        lines.append(f"**Found {len(todos)} relevant TODOs**")
        lines.append(f"**Found {len(tests)} relevant test files**")
        lines.append("")

        if related:
            lines.append(f"**Related topics:** {', '.join(related[:10])}")
            lines.append("")

        if kb_pages:
            lines.append("## KB Pages")
            for page in kb_pages[:3]:
                lines.append(f"- **{page['title']}**")
                lines.append(f"  {page['excerpt'][:100]}...")
            lines.append("")

        if code_files:
            lines.append("## Code Files")
            for file in code_files[:3]:
                lines.append(f"- `{file['path']}`")
                if file["summary"]:
                    lines.append(f"  {file['summary'][:100]}...")
            lines.append("")

        return "\n".join(lines)
