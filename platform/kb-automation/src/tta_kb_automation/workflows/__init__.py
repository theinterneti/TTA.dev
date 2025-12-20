"""High-level workflows composing multiple tools.

These workflows provide complete automation pipelines for common tasks:

- validate_kb_links: Check KB link integrity
- sync_code_todos: Bridge code TODOs to KB journals
- build_cross_references: Analyze code ↔ KB relationships
- build_session_context: Generate agent context from minimal input
- document_feature: Auto-document code features in KB
- pre_commit_validation: Run all KB checks before commits
"""

from pathlib import Path
from typing import Any

from tta_dev_primitives import WorkflowContext

from tta_kb_automation.core.code_primitives import (
    AnalyzeCodeStructure,
    ExtractTODOs,
    ParseDocstrings,
    ScanCodebase,
)
from tta_kb_automation.core.intelligence_primitives import SuggestKBLinks
from tta_kb_automation.core.kb_primitives import ParseLogseqPages
from tta_kb_automation.tools.cross_reference_builder import CrossReferenceBuilder
from tta_kb_automation.tools.link_validator import LinkValidator
from tta_kb_automation.tools.session_context_builder import SessionContextBuilder
from tta_kb_automation.tools.todo_sync import TODOSync


async def validate_kb_links(kb_path: str) -> dict[str, Any]:
    """Validate all links in KB.

    Uses the LinkValidator tool which composes:
        ParseLogseqPages >> ExtractLinks >> (ValidateLinks | FindOrphanedPages)

    Args:
        kb_path: Path to Logseq KB root

    Returns:
        Validation results with:
        - broken_links: List of broken [[Page]] links
        - orphaned_pages: List of pages with no incoming links
        - valid_links: List of valid links
        - total_pages: Total number of pages parsed
        - summary: Human-readable summary
        - report: Markdown report

    Example:
        >>> result = await validate_kb_links("logseq")
        >>> print(result["summary"])
        Validated 45 pages
        ✅ 120 valid links
        ❌ 3 broken links
        🔍 2 orphaned pages
    """
    validator = LinkValidator(kb_path=kb_path)
    return await validator.validate()


async def sync_code_todos(code_path: str, kb_path: str | None = None) -> dict[str, Any]:
    """Sync code TODOs to journal entries.

    Uses the TODOSync tool which composes:
        ScanCodebase >> ExtractTODOs >> Router >> (ClassifyTODO | SuggestKBLinks)
        >> CreateJournalEntry

    Args:
        code_path: Path to code root to scan for TODOs
        kb_path: Path to Logseq KB root (optional, uses default if not provided)

    Returns:
        Sync results with:
        - todos_created: Number of journal entries created
        - todos_processed: Total TODOs processed
        - journal_path: Path to created journal file

    Example:
        >>> result = await sync_code_todos("platform/primitives/src")
        >>> print(f"Created {result['todos_created']} journal entries")
    """
    sync = TODOSync()
    result = await sync.scan_and_create(paths=[code_path])
    return result


async def build_cross_references(kb_path: str, code_path: str) -> dict[str, Any]:
    """Build code ↔ KB cross-references.

    Uses the CrossReferenceBuilder tool which composes:
        (ParseLogseqPages | ScanCodebase) >> ExtractCodeReferences
        >> ExtractKBReferences >> AnalyzeCrossReferences

    Args:
        kb_path: Path to Logseq KB root
        code_path: Path to code root

    Returns:
        Cross-reference mappings with:
        - kb_to_code: Dict mapping KB pages to referenced code files
        - code_to_kb: Dict mapping code files to referenced KB pages
        - missing_references: List of broken references
        - stats: Statistics about the cross-references
        - suggestions: List of suggested new cross-references

    Example:
        >>> result = await build_cross_references("logseq", "platform")
        >>> print(f"Found {len(result['kb_to_code'])} KB pages with code refs")
    """
    builder = CrossReferenceBuilder(kb_path=kb_path, code_path=code_path)
    result = await builder.build()

    # Enhance with suggestions using SuggestKBLinks
    context = WorkflowContext(workflow_id="build_cross_references")
    linker = SuggestKBLinks()

    # Extract TODOs to suggest KB links for
    scanner = ScanCodebase()
    code_data = await scanner.execute({"root_path": code_path}, context)

    extractor = ExtractTODOs()
    todo_data = await extractor.execute({"files": code_data["files"]}, context)

    # Suggest KB links for each TODO
    suggestions = []
    for todo in todo_data.get("todos", [])[:20]:  # Limit to first 20 for performance
        link_result = await linker.execute(
            {"todo": todo, "context": todo.get("context_before", [])}, context
        )
        if link_result.get("links"):
            suggestions.append(
                {
                    "file": todo["file"],
                    "line": todo["line_number"],
                    "todo": todo["todo_text"],
                    "suggested_kb_pages": link_result["links"],
                }
            )

    result["suggestions"] = suggestions
    return result


async def build_session_context(
    topic: str,
    kb_path: str,
    code_path: str,
) -> dict[str, Any]:
    """Build synthetic session context for topic.

    Uses the SessionContextBuilder tool which aggregates:
    - Relevant KB pages (ranked by relevance)
    - Relevant code files (with docstrings)
    - Related TODOs
    - Related test files

    This workflow provides comprehensive context from minimal input,
    enabling agents to understand a feature/topic without manual research.

    Args:
        topic: Topic or feature name (e.g., "CachePrimitive", "retry patterns")
        kb_path: Path to Logseq KB root
        code_path: Path to code root

    Returns:
        Aggregated context with:
        - topic: The requested topic
        - kb_pages: List of relevant KB pages with excerpts
        - code_files: List of relevant code files with summaries
        - todos: List of related TODOs
        - tests: List of related test files
        - related_topics: List of related topics discovered
        - summary: Human-readable summary

    Example:
        >>> ctx = await build_session_context("CachePrimitive", "logseq", "platform")
        >>> print(ctx["summary"])
        Topic: CachePrimitive
        Found: 3 KB pages, 5 code files, 2 TODOs, 4 tests
        Related topics: LRU, TTL, performance, memoization
    """
    builder = SessionContextBuilder(
        kb_path=kb_path,
        code_path=code_path,
        max_kb_pages=10,
        max_code_files=15,
        max_todos=25,
        max_tests=15,
    )
    return await builder.build_context(topic=topic)


async def document_feature(
    feature_name: str,
    code_path: str,
    kb_path: str,
) -> dict[str, Any]:
    """Document a feature in KB.

    Analyzes code to extract documentation and creates/updates KB pages.

    Workflow:
        1. ScanCodebase - Find files related to feature
        2. ParseDocstrings - Extract docstrings and examples
        3. AnalyzeCodeStructure - Understand dependencies
        4. Generate KB page content
        5. Write to KB

    Args:
        feature_name: Name of feature to document (e.g., "CachePrimitive")
        code_path: Path to code root
        kb_path: Path to Logseq KB root

    Returns:
        Documentation results with:
        - created_pages: List of KB pages created
        - updated_pages: List of KB pages updated
        - code_files_analyzed: Number of code files analyzed
        - docstrings_extracted: Number of docstrings found
        - examples_extracted: Number of examples found

    Example:
        >>> result = await document_feature("RetryPrimitive", "platform", "logseq")
        >>> print(f"Created pages: {result['created_pages']}")
    """
    context = WorkflowContext(workflow_id=f"document_feature_{feature_name}")

    # Step 1: Scan codebase for relevant files
    scanner = ScanCodebase()
    code_data = await scanner.execute({"root_path": code_path}, context)

    # Filter files related to feature
    feature_lower = feature_name.lower()
    relevant_files = [f for f in code_data["files"] if feature_lower in f.lower()]

    if not relevant_files:
        # Broaden search - look for any partial match
        feature_parts = feature_lower.replace("primitive", "").replace("_", "")
        relevant_files = [f for f in code_data["files"] if feature_parts in f.lower()]

    # Step 2: Parse docstrings
    doc_parser = ParseDocstrings()
    docstrings_data = await doc_parser.execute({"files": relevant_files}, context)

    # Step 3: Analyze structure
    analyzer = AnalyzeCodeStructure()
    structure_data = await analyzer.execute(
        {"files": relevant_files, "include_dependencies": True}, context
    )

    # Step 4: Generate KB page content
    kb_content = _generate_feature_kb_page(
        feature_name=feature_name,
        docstrings=docstrings_data.get("docstrings", []),
        structure=structure_data,
        files=relevant_files,
    )

    # Step 5: Write to KB
    kb_path_obj = Path(kb_path)
    pages_dir = kb_path_obj / "pages"
    pages_dir.mkdir(parents=True, exist_ok=True)

    # Create page filename (handle special characters)
    page_filename = feature_name.replace("/", "___").replace(" ", "_") + ".md"
    page_path = pages_dir / page_filename

    # Check if updating or creating
    created = not page_path.exists()
    page_path.write_text(kb_content, encoding="utf-8")

    return {
        "created_pages": [str(page_path)] if created else [],
        "updated_pages": [] if created else [str(page_path)],
        "code_files_analyzed": len(relevant_files),
        "docstrings_extracted": len(docstrings_data.get("docstrings", [])),
        "examples_extracted": sum(
            1 for d in docstrings_data.get("docstrings", []) if d.get("examples")
        ),
        "feature_name": feature_name,
        "page_path": str(page_path),
    }


def _generate_feature_kb_page(
    feature_name: str,
    docstrings: list[dict],
    structure: dict,
    files: list[str],
) -> str:
    """Generate KB page content for a feature."""
    lines = [
        f"# {feature_name}",
        "",
        "tags:: #auto-generated #feature #dev-todo",
        "",
        "## Overview",
        "",
    ]

    # Add main docstring if found
    main_docstring = None
    for doc in docstrings:
        if feature_name.lower() in doc.get("name", "").lower():
            main_docstring = doc
            break

    if main_docstring:
        lines.append(main_docstring.get("docstring", "No documentation found."))
    else:
        lines.append(f"Documentation for {feature_name}.")
    lines.append("")

    # Add source files section
    lines.extend(
        [
            "## Source Files",
            "",
        ]
    )
    for f in files[:10]:  # Limit to 10 files
        lines.append(f"- `{f}`")
    lines.append("")

    # Add classes/functions section
    classes = structure.get("classes", [])
    functions = structure.get("functions", [])

    if classes:
        lines.extend(
            [
                "## Classes",
                "",
            ]
        )
        for cls in classes[:10]:
            lines.append(f"- **{cls.get('name', 'Unknown')}**")
            if cls.get("docstring"):
                lines.append(f"  - {cls['docstring'][:100]}...")
        lines.append("")

    if functions:
        lines.extend(
            [
                "## Functions",
                "",
            ]
        )
        for func in functions[:10]:
            lines.append(f"- `{func.get('name', 'Unknown')}()`")
        lines.append("")

    # Add dependencies section
    dependencies = structure.get("dependencies", [])
    if dependencies:
        lines.extend(
            [
                "## Dependencies",
                "",
            ]
        )
        for dep in dependencies[:15]:
            lines.append(f"- {dep}")
        lines.append("")

    # Add related pages section
    lines.extend(
        [
            "## Related",
            "",
            "- [[TTA Primitives]]",
            "- [[TTA.dev Architecture]]",
            "",
            "---",
            "*Auto-generated by tta-kb-automation*",
        ]
    )

    return "\n".join(lines)


async def pre_commit_validation(
    kb_path: str,
    code_path: str,
) -> dict[str, Any]:
    """Run pre-commit KB validation checks.

    Combines multiple validation workflows:
    1. Link validation (broken links, orphaned pages)
    2. TODO sync check (unsynced TODOs)
    3. Cross-reference integrity

    This workflow is designed to run as a pre-commit hook to ensure
    KB quality before commits.

    Args:
        kb_path: Path to Logseq KB root
        code_path: Path to code root

    Returns:
        Validation results with:
        - passed: bool - Overall pass/fail
        - link_validation: Dict with link check results
        - todo_check: Dict with TODO sync status
        - cross_ref_check: Dict with cross-reference issues
        - issues: List of all issues found
        - summary: Human-readable summary

    Example:
        >>> result = await pre_commit_validation("logseq", "platform")
        >>> if not result["passed"]:
        ...     print("Issues found:", result["summary"])
        ...     for issue in result["issues"]:
        ...         print(f"  - {issue}")
    """
    issues: list[str] = []

    # 1. Validate KB links
    link_result = await validate_kb_links(kb_path)

    broken_count = link_result.get("total_broken", 0)
    orphaned_count = link_result.get("total_orphaned", 0)

    if broken_count > 0:
        issues.append(f"❌ {broken_count} broken links found")
        for link in link_result.get("broken_links", [])[:5]:
            issues.append(f"   - {link['source']} -> [[{link['target']}]]")

    if orphaned_count > 0:
        issues.append(f"🔍 {orphaned_count} orphaned pages found")

    # 2. Check for unsynced TODOs
    context = WorkflowContext(workflow_id="pre_commit_validation")
    scanner = ScanCodebase()
    code_data = await scanner.execute({"root_path": code_path}, context)

    extractor = ExtractTODOs()
    todo_data = await extractor.execute({"files": code_data["files"]}, context)

    todo_count = todo_data.get("total_todos", 0)
    todo_check = {
        "total_todos_in_code": todo_count,
        "files_with_todos": todo_data.get("files_with_todos", 0),
    }

    if todo_count > 50:  # Warning threshold
        issues.append(f"⚠️ {todo_count} TODOs in codebase (consider syncing to KB)")

    # 3. Build cross-references (lightweight check)
    xref_builder = CrossReferenceBuilder(kb_path=kb_path, code_path=code_path)
    xref_result = await xref_builder.build()

    missing_refs = len(xref_result.get("missing_references", []))
    cross_ref_check = {
        "missing_references": missing_refs,
        "kb_pages_with_code_refs": xref_result.get("stats", {}).get("kb_pages_with_code_refs", 0),
    }

    if missing_refs > 0:
        issues.append(f"⚠️ {missing_refs} missing cross-references")
        for ref in xref_result.get("missing_references", [])[:3]:
            issues.append(f"   - {ref.get('reference', 'unknown')}: {ref.get('suggestion', '')}")

    # Generate summary
    passed = len(issues) == 0
    if passed:
        summary = "✅ All pre-commit checks passed!"
    else:
        summary = f"❌ Pre-commit validation failed with {len(issues)} issue(s)"

    return {
        "passed": passed,
        "link_validation": {
            "broken_links": broken_count,
            "orphaned_pages": orphaned_count,
            "valid_links": link_result.get("total_valid", 0),
        },
        "todo_check": todo_check,
        "cross_ref_check": cross_ref_check,
        "issues": issues,
        "summary": summary,
    }


__all__ = [
    # Workflows
    "validate_kb_links",
    "sync_code_todos",
    "build_cross_references",
    "build_session_context",
    "document_feature",
    "pre_commit_validation",
    # Re-exported primitives for convenience
    "AnalyzeCodeStructure",
    "ExtractTODOs",
    "ScanCodebase",
    "SuggestKBLinks",
    "TODOSync",
]
