"""Cross-reference builder - analyzes code ↔ KB relationships.

This tool builds bidirectional cross-references between code and KB pages.

Composes primitives:
    ParseLogseqPages >> ExtractCodeReferences >> AnalyzeReferences >> GenerateReport

Usage:
    builder = CrossReferenceBuilder(kb_path="logseq", code_path="packages")
    result = await builder.build()
"""

import re
from pathlib import Path
from typing import Any

from tta_dev_primitives import WorkflowContext
from tta_dev_primitives.observability import InstrumentedPrimitive
from tta_dev_primitives.performance import CachePrimitive

from ..core.code_primitives import ScanCodebase
from ..core.kb_primitives import ParseLogseqPages


class ExtractCodeReferences(InstrumentedPrimitive[dict, dict]):
    """Extract code file references from KB pages.

    Looks for:
    - File paths in code blocks
    - Explicit file references [filename](path)
    - Package mentions
    """

    def __init__(self) -> None:
        super().__init__(name="extract_code_references")
        # Pattern for code file references
        self.file_patterns = [
            re.compile(r"`([a-zA-Z0-9_/\-]+\.py)`"),  # `path/to/file.py`
            re.compile(r"\[([^\]]+)\]\(([^)]+\.py)\)"),  # [text](path/to/file.py)
            re.compile(
                r"packages/([a-zA-Z0-9_\-]+/[^\s]+\.py)"
            ),  # packages/pkg/file.py
        ]

    async def _execute_impl(self, input_data: dict, context: WorkflowContext) -> dict:
        """Extract code references from KB pages."""
        pages = input_data.get("pages", [])
        kb_to_code: dict[str, list[str]] = {}

        for page in pages:
            page_title = page["title"]
            content = page["content"]

            code_refs = []

            # Try each pattern
            for pattern in self.file_patterns:
                matches = pattern.findall(content)
                if matches:
                    # Handle tuple results from groups
                    for match in matches:
                        if isinstance(match, tuple):
                            if len(match) > 1:
                                code_refs.append(match[1])
                            elif len(match) > 0:
                                code_refs.append(match[0])
                        else:
                            code_refs.append(match)

            if code_refs:
                kb_to_code[page_title] = list(set(code_refs))  # Deduplicate

        return {"kb_to_code": kb_to_code, "pages": pages}


class ExtractKBReferences(InstrumentedPrimitive[dict, dict]):
    """Extract KB page references from code files.

    Looks for:
    - Docstring references to KB pages
    - Comments mentioning KB pages
    - See also: [[Page Name]] style references
    """

    def __init__(self) -> None:
        super().__init__(name="extract_kb_references")
        # Pattern for KB page references in code
        self.kb_patterns = [
            re.compile(r"\[\[([^\]]+)\]\]"),  # [[Page Name]]
            re.compile(r"See:?\s+([A-Z][a-zA-Z0-9/_\-\s]+\.md)"),  # See: path/Page.md
            re.compile(r"KB:\s+([A-Z][a-zA-Z0-9/_\-\s]+)"),  # KB: Page Name
        ]

    async def _execute_impl(self, input_data: dict, context: WorkflowContext) -> dict:
        """Extract KB references from code files."""
        files = input_data.get("files", [])
        code_to_kb: dict[str, list[str]] = {}

        for file_path in files:
            try:
                content = Path(file_path).read_text(encoding="utf-8")
                kb_refs = []

                for pattern in self.kb_patterns:
                    matches = pattern.findall(content)
                    kb_refs.extend(matches)

                if kb_refs:
                    code_to_kb[str(file_path)] = list(set(kb_refs))  # Deduplicate

            except Exception:
                continue  # Skip files that can't be read

        return {"code_to_kb": code_to_kb, "files": files}


class AnalyzeCrossReferences(InstrumentedPrimitive[dict, dict]):
    """Analyze bidirectional cross-references and find missing links."""

    def __init__(self) -> None:
        super().__init__(name="analyze_cross_references")

    async def _execute_impl(self, input_data: dict, context: WorkflowContext) -> dict:
        """Analyze cross-references."""
        kb_to_code = input_data.get("kb_to_code", {})
        code_to_kb = input_data.get("code_to_kb", {})
        all_files = input_data.get("files", [])  # All scanned files

        # Find missing references
        missing: list[dict] = []

        # Check if code files mentioned in KB exist
        all_kb_code_refs = set()
        for refs in kb_to_code.values():
            all_kb_code_refs.update(refs)

        all_code_files = set(code_to_kb.keys())

        # Find code files mentioned in KB but not found
        for code_ref in all_kb_code_refs:
            # Check if this reference exists in any form
            found = any(code_ref in str(f) for f in all_code_files)
            if not found:
                missing.append(
                    {
                        "type": "code_missing",
                        "reference": code_ref,
                        "suggestion": f"Code file {code_ref} is mentioned in KB but may not exist",
                    }
                )

        # Find KB pages mentioned in code but potentially not existing
        all_code_kb_refs = set()
        for refs in code_to_kb.values():
            all_code_kb_refs.update(refs)

        # KB page titles from input
        kb_pages = {page["title"] for page in input_data.get("pages", [])}

        for kb_ref in all_code_kb_refs:
            if kb_ref not in kb_pages and not any(
                kb_ref in title for title in kb_pages
            ):
                missing.append(
                    {
                        "type": "kb_missing",
                        "reference": kb_ref,
                        "suggestion": f"KB page '{kb_ref}' is mentioned in code but may not exist",
                    }
                )

        # Calculate statistics
        stats = {
            "total_kb_pages": len(input_data.get("pages", [])),
            "total_code_files": len(all_files),
            "kb_pages_with_code_refs": len(kb_to_code),
            "code_files_with_kb_refs": len(code_to_kb),
            "total_missing_refs": len(missing),
        }

        return {
            "kb_to_code": kb_to_code,
            "code_to_kb": code_to_kb,
            "missing_references": missing,
            "stats": stats,
        }


class CrossReferenceBuilder:
    """Build code ↔ KB cross-references.

    Workflow:
        1. ParseLogseqPages - Parse all KB pages
        2. ScanCodebase - Find all code files
        3. ExtractCodeReferences - Find code refs in KB
        4. ExtractKBReferences - Find KB refs in code
        5. AnalyzeCrossReferences - Build bidirectional mapping

    Example:
        ```python
        from tta_kb_automation import CrossReferenceBuilder

        builder = CrossReferenceBuilder(
            kb_path="logseq",
            code_path="packages"
        )

        result = await builder.build()
        print(f"Found {result['stats']['kb_pages_with_code_refs']} KB pages with code refs")
        ```
    """

    def __init__(
        self,
        kb_path: Path,
        code_path: Path,
        use_cache: bool = True,
        exclude_patterns: list[str] | None = None,
    ):
        """Initialize CrossReferenceBuilder.

        Args:
            kb_path: Path to KB directory
            code_path: Path to codebase directory
            use_cache: Enable caching (default: True)
            exclude_patterns: Patterns to exclude from code scan (None = use defaults)
        """
        self.kb_path = kb_path
        self.code_path = code_path
        self.use_cache = use_cache
        self.exclude_patterns = exclude_patterns

        self._build_workflow()

    def _build_workflow(self) -> None:
        """Build cross-reference workflow using primitive composition."""
        # Step 1: Parse KB pages
        parse_kb = ParseLogseqPages(kb_path=self.kb_path)

        # Step 2: Extract code references from KB
        extract_code_refs = ExtractCodeReferences()

        # Step 3: Scan codebase
        scan_code = ScanCodebase()

        # Step 4: Extract KB references from code
        extract_kb_refs = ExtractKBReferences()

        # Step 5: Analyze cross-references
        analyze = AnalyzeCrossReferences()

        # Build workflow
        # We'll use a custom orchestration since we need to merge results
        self._parse_kb = parse_kb
        self._extract_code_refs = extract_code_refs
        self._scan_code = scan_code
        self._extract_kb_refs = extract_kb_refs
        self._analyze = analyze

        # Add caching if enabled
        if self.use_cache:
            self._parse_kb = CachePrimitive(
                primitive=self._parse_kb,
                cache_key_fn=lambda d, c: str(self.kb_path),
                ttl_seconds=600.0,  # 10 minutes
            )
            self._scan_code = CachePrimitive(
                primitive=self._scan_code,
                cache_key_fn=lambda d, c: str(self.code_path),
                ttl_seconds=600.0,
            )

    async def build(self) -> dict[str, Any]:
        """Build cross-references.

        Returns:
            dict with keys:
                - kb_to_code: Dict[str, List[str]] - KB page -> code files
                - code_to_kb: Dict[str, List[str]] - code file -> KB pages
                - missing_references: List of missing references
                - stats: Statistics about cross-references
                - report: Human-readable markdown report
        """
        context = WorkflowContext(workflow_id="cross_reference_builder")

        # Step 1: Parse KB
        kb_result = await self._parse_kb.execute({}, context)

        # Step 2: Extract code refs from KB
        kb_refs = await self._extract_code_refs.execute(kb_result, context)

        # Step 3: Scan codebase
        scan_input: dict[str, Any] = {"root_path": str(self.code_path)}
        if self.exclude_patterns is not None:
            scan_input["exclude_patterns"] = self.exclude_patterns

        code_result = await self._scan_code.execute(scan_input, context)

        # Step 4: Extract KB refs from code
        code_refs = await self._extract_kb_refs.execute(code_result, context)

        # Step 5: Merge and analyze
        merged = {
            "kb_to_code": kb_refs["kb_to_code"],
            "code_to_kb": code_refs["code_to_kb"],
            "pages": kb_result["pages"],
            "files": code_result.get("files", []),  # Pass all scanned files
        }

        result = await self._analyze.execute(merged, context)

        # Add report
        result["report"] = self._generate_report(result)

        return result

    def _generate_report(self, result: dict[str, Any]) -> str:
        """Generate human-readable markdown report."""
        stats = result.get("stats", {})
        kb_to_code = result.get("kb_to_code", {})
        code_to_kb = result.get("code_to_kb", {})
        missing = result.get("missing_references", [])

        lines = [
            "# Cross-Reference Analysis Report",
            "",
            "## Summary",
            "",
            f"- **Total KB Pages:** {stats.get('total_kb_pages', 0)}",
            f"- **Total Code Files:** {stats.get('total_code_files', 0)}",
            f"- **KB Pages with Code References:** {stats.get('kb_pages_with_code_refs', 0)}",
            f"- **Code Files with KB References:** {stats.get('code_files_with_kb_refs', 0)}",
            f"- **Missing References:** {stats.get('total_missing_refs', 0)}",
            "",
        ]

        if kb_to_code:
            lines.extend(
                [
                    "## KB → Code References",
                    "",
                    "KB pages that reference code files:",
                    "",
                ]
            )
            for page, files in sorted(kb_to_code.items()):
                lines.append(f"### {page}")
                for file in files:
                    lines.append(f"- `{file}`")
                lines.append("")

        if code_to_kb:
            lines.extend(
                [
                    "## Code → KB References",
                    "",
                    "Code files that reference KB pages:",
                    "",
                ]
            )
            for file, pages in sorted(code_to_kb.items()):
                lines.append(f"### `{Path(file).name}`")
                lines.append(f"*Full path: {file}*")
                lines.append("")
                for page in pages:
                    lines.append(f"- [[{page}]]")
                lines.append("")

        if missing:
            lines.extend(
                [
                    "## ⚠️ Missing References",
                    "",
                    "References that may need attention:",
                    "",
                ]
            )
            for ref in missing:
                ref_type = ref["type"]
                reference = ref["reference"]
                suggestion = ref["suggestion"]
                lines.append(f"- **{ref_type}**: `{reference}`")
                lines.append(f"  - {suggestion}")
                lines.append("")

        lines.extend(
            [
                "## Recommendations",
                "",
                "1. **Review missing references** - Check if referenced files/pages exist",
                "2. **Add documentation links** - Link code files to relevant KB pages",
                "3. **Update KB pages** - Add code file references where appropriate",
                "4. **Maintain consistency** - Keep cross-references up to date",
            ]
        )

        return "\n".join(lines)
