"""KB-focused primitives for parsing and validating Logseq knowledge base.

These primitives handle:
- Parsing Logseq markdown files
- Extracting [[Wiki Links]]
- Validating link targets exist
- Finding orphaned pages
"""

import re
from pathlib import Path
from typing import Any

from tta_dev_primitives import WorkflowContext
from tta_dev_primitives.observability import InstrumentedPrimitive


class ParseLogseqPages(InstrumentedPrimitive[dict[str, Any], dict[str, Any]]):
    """Parse Logseq markdown pages from filesystem.

    Input: {"kb_path": "logseq/"}
    Output: {"pages": [{
        "path": Path,
        "title": str,
        "content": str,
        "links": list[str],
        "tags": list[str]
    }]}
    """

    def __init__(self, kb_path: Path | str = "logseq") -> None:
        super().__init__(name="parse_logseq_pages")
        self.kb_path = Path(kb_path)

    async def _execute_impl(
        self, input_data: dict[str, Any], context: WorkflowContext
    ) -> dict[str, Any]:
        """Parse all markdown pages in Logseq KB."""
        pages_dir = self.kb_path / "pages"
        journals_dir = self.kb_path / "journals"

        pages = []

        # Parse pages/
        if pages_dir.exists():
            for page_file in pages_dir.glob("*.md"):
                parsed = await self._parse_page(page_file)
                pages.append(parsed)

        # Parse journals/
        if journals_dir.exists():
            for journal_file in journals_dir.glob("*.md"):
                parsed = await self._parse_page(journal_file)
                parsed["is_journal"] = True
                pages.append(parsed)

        return {"pages": pages, "total_pages": len(pages), "kb_path": str(self.kb_path)}

    async def _parse_page(self, path: Path) -> dict[str, Any]:
        """Parse a single markdown page."""
        content = path.read_text(encoding="utf-8")

        # Extract title (from filename)
        title = path.stem.replace("___", "/").replace("_", " ")

        # Extract [[Wiki Links]]
        wiki_links = re.findall(r"\[\[([^\]]+)\]\]", content)

        # Extract #tags
        tags = re.findall(r"#([\w-]+)", content)

        return {
            "path": path,
            "title": title,
            "content": content,
            "links": list(set(wiki_links)),
            "tags": list(set(tags)),
            "is_journal": False,
        }


class ExtractLinks(InstrumentedPrimitive[dict[str, Any], dict[str, Any]]):
    """Extract all [[Wiki Links]] from parsed pages.

    Input: {"pages": [...]}
    Output: {"links": [{
        "source": str,
        "target": str,
        "line": int
    }]}
    """

    def __init__(self) -> None:
        super().__init__(name="extract_links")

    async def _execute_impl(
        self, input_data: dict[str, Any], context: WorkflowContext
    ) -> dict[str, Any]:
        """Extract all links from pages."""
        pages = input_data.get("pages", [])

        all_links = []

        for page in pages:
            source = page["title"]
            content = page["content"]

            # Find [[links]] with line numbers
            lines = content.split("\n")
            for line_num, line in enumerate(lines, start=1):
                for match in re.finditer(r"\[\[([^\]]+)\]\]", line):
                    target = match.group(1)
                    all_links.append(
                        {
                            "source": source,
                            "target": target,
                            "line": line_num,
                            "source_path": str(page["path"]),
                        }
                    )

        return {
            "links": all_links,
            "total_links": len(all_links),
            "pages": pages,  # Pass through for next primitive
        }


class ValidateLinks(InstrumentedPrimitive[dict[str, Any], dict[str, Any]]):
    """Validate that [[Wiki Links]] point to existing pages.

    Input: {"links": [...], "pages": [...]}
    Output: {"broken_links": [...], "valid_links": [...]}
    """

    def __init__(self) -> None:
        super().__init__(name="validate_links")

    async def _execute_impl(
        self, input_data: dict[str, Any], context: WorkflowContext
    ) -> dict[str, Any]:
        """Validate all links against existing pages."""
        links = input_data.get("links", [])
        pages = input_data.get("pages", [])

        # Build set of valid page titles
        valid_titles = {page["title"] for page in pages}

        broken_links = []
        valid_links = []

        for link in links:
            target = link["target"]

            if target in valid_titles:
                valid_links.append(link)
            else:
                broken_links.append(link)

        return {
            "broken_links": broken_links,
            "valid_links": valid_links,
            "total_broken": len(broken_links),
            "total_valid": len(valid_links),
            "pages": pages,  # Pass through
        }


class FindOrphanedPages(InstrumentedPrimitive[dict[str, Any], dict[str, Any]]):
    """Find pages that have no incoming links.

    Input: {"pages": [...], "links": [...]}
    Output: {"orphaned_pages": [...]}
    """

    def __init__(self) -> None:
        super().__init__(name="find_orphaned_pages")

    async def _execute_impl(
        self, input_data: dict[str, Any], context: WorkflowContext
    ) -> dict[str, Any]:
        """Find pages with no incoming links."""
        pages = input_data.get("pages", [])
        links = input_data.get("links", [])

        # Build set of pages that have incoming links
        linked_pages = {link["target"] for link in links}

        # Find orphaned pages
        orphaned = []
        for page in pages:
            title = page["title"]

            # Skip journals (they're inherently orphaned)
            if page.get("is_journal"):
                continue

            # Skip index/root pages
            if title in {"Index", "Contents", "README"}:
                continue

            if title not in linked_pages:
                orphaned.append(
                    {
                        "title": title,
                        "path": str(page["path"]),
                        "tags": page.get("tags", []),
                    }
                )

        return {
            "orphaned_pages": orphaned,
            "total_orphaned": len(orphaned),
            **input_data,  # Pass through all input
        }
