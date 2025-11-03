"""Link Validator Tool - Validates KB link integrity.

Composes primitives:
    ParseLogseqPages >> ExtractLinks >> (ValidateLinks | FindOrphanedPages) >> GenerateReport

Usage:
    validator = LinkValidator()
    result = await validator.validate()
"""

from pathlib import Path
from typing import Any

from tta_dev_primitives import WorkflowContext
from tta_dev_primitives.observability import InstrumentedPrimitive
from tta_dev_primitives.performance import CachePrimitive
from tta_dev_primitives.recovery import RetryPrimitive, RetryStrategy

from ..core.kb_primitives import (
    ExtractLinks,
    FindOrphanedPages,
    ParseLogseqPages,
    ValidateLinks,
)


class AggregateParallelResults(InstrumentedPrimitive[list[dict], dict]):
    """Aggregate results from parallel validation branches.

    ParallelPrimitive returns a list of results from each branch.
    This primitive merges them into a single dictionary.

    Input: [validate_result, orphans_result]
    Output: {broken_links, valid_links, orphaned_pages, total_*, pages}
    """

    def __init__(self) -> None:
        super().__init__(name="aggregate_parallel_results")

    async def _execute_impl(self, input_data: list[dict], context: WorkflowContext) -> dict:
        """Merge parallel validation results."""
        if not input_data or len(input_data) < 2:
            # Fallback for unexpected input
            return {}

        validate_result = input_data[0]  # From ValidateLinks
        orphans_result = input_data[1]  # From FindOrphanedPages

        # Merge results, preserving all keys
        merged = {
            **validate_result,  # broken_links, valid_links, total_broken, total_valid
            **orphans_result,  # orphaned_pages, total_orphaned
        }

        # Add total_pages if we have pages
        if "pages" in merged:
            merged["total_pages"] = len(merged["pages"])

        return merged


class LinkValidator:
    """Validates KB link integrity using primitive composition.

    Example:
        >>> validator = LinkValidator(kb_path="logseq/")
        >>> result = await validator.validate()
        >>> print(result["broken_links"])
        >>> print(result["orphaned_pages"])
    """

    def __init__(self, kb_path: Path | str = "logseq", use_cache: bool = True) -> None:
        """Initialize link validator.

        Args:
            kb_path: Path to Logseq knowledge base (default: "logseq/")
            use_cache: Enable caching for performance (default: True)
        """
        self.kb_path = Path(kb_path)
        self.use_cache = use_cache

        # Build workflow with primitives
        self._build_workflow()

    def _build_workflow(self) -> None:
        """Build validation workflow using primitive composition."""
        # Step 1: Parse all pages
        parse = ParseLogseqPages(kb_path=self.kb_path)

        # Step 2: Extract links
        extract = ExtractLinks()

        # Step 3: Parallel validation (validate + find orphans)
        validate = ValidateLinks()
        orphans = FindOrphanedPages()
        parallel_validation = validate | orphans

        # Step 4: Aggregate parallel results into single dict
        aggregate = AggregateParallelResults()

        # Compose workflow
        workflow = parse >> extract >> parallel_validation >> aggregate

        # Add retry for resilience
        workflow = RetryPrimitive(
            primitive=workflow,
            strategy=RetryStrategy(max_retries=2, backoff_base=1.0, jitter=False),
        )

        # Add caching if enabled
        if self.use_cache:
            workflow = CachePrimitive(
                primitive=workflow,
                cache_key_fn=lambda data, ctx: str(self.kb_path),
                ttl_seconds=300.0,  # 5 minutes
            )

        self.workflow = workflow

    async def validate(self) -> dict[str, Any]:
        """Run link validation.

        Returns:
            dict with keys:
                - broken_links: List of broken [[Page]] links
                - orphaned_pages: List of pages with no incoming links
                - valid_links: List of valid links
                - total_pages: Total number of pages parsed
                - summary: Human-readable summary
        """
        context = WorkflowContext(workflow_id="kb_link_validation")

        # Execute workflow
        result = await self.workflow.execute({}, context)

        # Add summary
        result["summary"] = self._generate_summary(result)

        return result

    def _generate_summary(self, result: dict[str, Any]) -> str:
        """Generate human-readable summary."""
        total_pages = result.get("total_pages", 0)
        broken_count = result.get("total_broken", 0)
        orphaned_count = result.get("total_orphaned", 0)
        valid_count = result.get("total_valid", 0)

        summary_lines = [
            f"Validated {total_pages} pages",
            f"✅ {valid_count} valid links",
            f"❌ {broken_count} broken links",
            f"🔍 {orphaned_count} orphaned pages",
        ]

        if broken_count == 0 and orphaned_count == 0:
            summary_lines.append("\n✨ KB is healthy!")
        else:
            summary_lines.append("\n⚠️ Issues found - see details above")

        return "\n".join(summary_lines)

    async def validate_and_report(
        self, output_path: Path | str = "kb_validation_report.md"
    ) -> None:
        """Validate KB and write report to file.

        Args:
            output_path: Path for report markdown file
        """
        result = await self.validate()

        # Generate markdown report
        report = self._generate_report(result)

        # Write to file
        output_path = Path(output_path)
        output_path.write_text(report, encoding="utf-8")

        print(f"Report written to: {output_path}")

    def _generate_report(self, result: dict[str, Any]) -> str:
        """Generate markdown report."""
        lines = [
            "# KB Link Validation Report",
            "",
            f"**Generated:** {result.get('timestamp', 'N/A')}",
            f"**KB Path:** {self.kb_path}",
            "",
            "## Summary",
            "",
            result["summary"],
            "",
        ]

        # Broken links section
        broken_links = result.get("broken_links", [])
        if broken_links:
            lines.extend(
                [
                    "## ❌ Broken Links",
                    "",
                    "| Source | Target | Line |",
                    "|--------|--------|------|",
                ]
            )
            for link in broken_links[:50]:  # Limit to 50
                source = link.get("source", "?")
                target = link.get("target", "?")
                line = link.get("line", "?")
                lines.append(f"| {source} | [[{target}]] | {line} |")

            if len(broken_links) > 50:
                lines.append(f"\n*... and {len(broken_links) - 50} more*")
            lines.append("")

        # Orphaned pages section
        orphaned = result.get("orphaned_pages", [])
        if orphaned:
            lines.extend(["## 🔍 Orphaned Pages", "", "Pages with no incoming links:", ""])
            for page in orphaned[:30]:  # Limit to 30
                title = page.get("title", "?")
                tags = page.get("tags", [])
                tag_str = f" ({', '.join(f'#{t}' for t in tags)})" if tags else ""
                lines.append(f"- [[{title}]]{tag_str}")

            if len(orphaned) > 30:
                lines.append(f"\n*... and {len(orphaned) - 30} more*")
            lines.append("")

        # Recommendations
        lines.extend(["## 💡 Recommendations", ""])

        if broken_links:
            lines.extend(
                [
                    "### Fix Broken Links",
                    "",
                    "1. Review broken links above",
                    "2. Either:",
                    "   - Create missing pages",
                    "   - Fix typos in link targets",
                    "   - Remove invalid links",
                    "",
                ]
            )

        if orphaned:
            lines.extend(
                [
                    "### Address Orphaned Pages",
                    "",
                    "1. Review orphaned pages above",
                    "2. Either:",
                    "   - Add links from related pages",
                    "   - Add to index/contents pages",
                    "   - Archive/delete if no longer needed",
                    "",
                ]
            )

        if not broken_links and not orphaned:
            lines.extend(["✨ **No action needed!** KB is healthy.", ""])

        return "\n".join(lines)
