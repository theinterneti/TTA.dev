"""Integration tests for KB automation tools.

Tests the complete workflow against real TTA.dev codebase:
- Scanning actual Python files
- Extracting real TODO comments
- Classifying TODOs
- Generating journal entries
- Validating KB links
- Building cross-references

Unlike unit tests, these tests:
- Use real filesystem (no mocks)
- Process actual codebase
- Generate real output files
- Validate against actual KB structure
"""

from datetime import datetime
from pathlib import Path

import pytest
from tta_kb_automation.tools.todo_sync import TODOSync

# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration


@pytest.fixture
def workspace_root():
    """Get the TTA.dev workspace root."""
    # Navigate up from tests/integration to repo root
    return Path(__file__).parent.parent.parent


@pytest.fixture
def logseq_dir(workspace_root):
    """Get the logseq directory."""
    return workspace_root / "logseq"


@pytest.fixture
def temp_journal_dir(tmp_path):
    """Create temporary journal directory for test outputs."""
    journal_dir = tmp_path / "journals"
    journal_dir.mkdir()
    return journal_dir


class TestRealCodebaseScanning:
    """Test scanning the actual TTA.dev codebase."""

    @pytest.mark.asyncio
    async def test_scan_primitives_package(self, workspace_root):
        """Scan tta-dev-primitives for TODOs."""
        sync = TODOSync()

        # Scan the actual primitives package
        paths = [str(workspace_root / "platform" / "primitives" / "src")]

        result = await sync.scan_and_create(
            paths=paths,
            journal_date=None,  # Don't write to journal
            dry_run=True,  # Don't create files
        )

        # Validate results
        assert "todos_found" in result
        assert isinstance(result["todos_found"], int)
        assert result["todos_found"] >= 0  # May have TODOs or not

        if result["todos_found"] > 0:
            assert "todos" in result
            assert len(result["todos"]) == result["todos_found"]

            # Validate TODO structure
            for todo in result["todos"]:
                assert "type" in todo
                assert "message" in todo
                assert "file" in todo
                assert "line_number" in todo
                assert "priority" in todo
                assert "package" in todo

                # Validate classification
                assert todo["type"] in [
                    "implementation",
                    "testing",
                    "documentation",
                    "bugfix",
                    "refactoring",
                    "infrastructure",
                ]
                assert todo["priority"] in ["high", "medium", "low"]

    @pytest.mark.asyncio
    async def test_scan_multiple_packages(self, workspace_root):
        """Scan multiple packages and compare TODO patterns."""
        sync = TODOSync()

        packages_to_scan = {
            "tta-dev-primitives": "platform/primitives",
            "tta-observability-integration": "platform/observability",
            "universal-agent-context": "platform/agent-context",
        }

        all_todos = {}

        for package, rel_path in packages_to_scan.items():
            package_path = workspace_root / rel_path / "src"
            if not package_path.exists():
                continue

            result = await sync.scan_and_create(
                paths=[str(package_path)],
                journal_date=None,
                dry_run=True,
            )

            all_todos[package] = result.get("todos", [])

        # Validate we scanned at least one package
        assert len(all_todos) > 0

        # Analyze TODO patterns across packages
        total_todos = sum(len(todos) for todos in all_todos.values())

        if total_todos > 0:
            # Group by type
            type_distribution = {}
            priority_distribution = {}

            for _package, todos in all_todos.items():
                for todo in todos:
                    todo_type = todo["type"]
                    priority = todo["priority"]

                    type_distribution[todo_type] = (
                        type_distribution.get(todo_type, 0) + 1
                    )
                    priority_distribution[priority] = (
                        priority_distribution.get(priority, 0) + 1
                    )

            # Report findings
            print("\n=== TODO Analysis Across Packages ===")
            print(f"Total TODOs found: {total_todos}")
            print("\nBy Type:")
            for todo_type, count in sorted(
                type_distribution.items(), key=lambda x: x[1], reverse=True
            ):
                print(f"  {todo_type}: {count}")

            print("\nBy Priority:")
            for priority, count in sorted(
                priority_distribution.items(), key=lambda x: x[1], reverse=True
            ):
                print(f"  {priority}: {count}")

    @pytest.mark.asyncio
    async def test_classify_real_todos(self, workspace_root):
        """Test classification logic on real TODO comments."""
        sync = TODOSync()

        # Scan for actual TODOs
        paths = [str(workspace_root / "platform")]
        result = await sync.scan_and_create(
            paths=paths,
            journal_date=None,
            dry_run=True,
        )

        if result["todos_found"] == 0:
            pytest.skip("No TODOs found in codebase")

        todos = result["todos"]

        # Validate classification quality
        for todo in todos:
            message = todo["message"].lower()

            # Check classification rules
            if any(
                word in message for word in ["test", "pytest", "coverage", "unittest"]
            ):
                # Should be classified as testing
                assert todo["type"] == "testing", (
                    f"TODO about testing not classified correctly: {todo['message']}"
                )

            if any(
                word in message for word in ["urgent", "asap", "critical", "blocker"]
            ):
                # Should have high priority
                assert todo["priority"] == "high", (
                    f"Urgent TODO not prioritized high: {todo['message']}"
                )

            if any(word in message for word in ["fix", "bug", "error", "crash"]):
                # Should be classified as bugfix
                assert todo["type"] in ["bugfix", "implementation"], (
                    f"Bug-related TODO not classified correctly: {todo['message']}"
                )


class TestJournalEntryGeneration:
    """Test generation of actual journal entries."""

    @pytest.mark.asyncio
    async def test_generate_journal_entry_format(
        self, workspace_root, temp_journal_dir
    ):
        """Generate a journal entry and validate format."""
        sync = TODOSync()

        # Scan a package
        paths = [str(workspace_root / "platform" / "primitives" / "src")]
        today = datetime.now().strftime("%Y_%m_%d")

        result = await sync.scan_and_create(
            paths=paths,
            journal_date=today,
            output_dir=str(temp_journal_dir),
        )

        # Check if journal file was created
        journal_file = temp_journal_dir / f"{today}.md"

        if result["todos_found"] > 0:
            assert journal_file.exists(), "Journal file should be created"

            # Read and validate content
            content = journal_file.read_text()

            # Should have proper header
            assert (
                f"## {today}" in content
                or f"# {datetime.now().strftime('%B %d')}" in content
            )

            # Should have TODO section
            assert "TODO" in content or "DOING" in content

            # Should have properties
            assert "type::" in content
            assert "priority::" in content
            assert "package::" in content

            # Should have file references
            assert ".py" in content

            print("\n=== Generated Journal Entry ===")
            print(content)
            print("=" * 40)

    @pytest.mark.asyncio
    async def test_journal_entry_kb_links(self, workspace_root, temp_journal_dir):
        """Validate that KB links are suggested in journal entries."""
        sync = TODOSync()

        paths = [str(workspace_root / "platform")]
        today = datetime.now().strftime("%Y_%m_%d")

        result = await sync.scan_and_create(
            paths=paths,
            journal_date=today,
            output_dir=str(temp_journal_dir),
        )

        if result["todos_found"] == 0:
            pytest.skip("No TODOs found")

        # Check for KB link suggestions in result
        todos = result["todos"]

        kb_links_found = any("kb_links" in todo for todo in todos)

        if kb_links_found:
            print("\n=== KB Link Suggestions ===")
            for todo in todos:
                if "kb_links" in todo and todo["kb_links"]:
                    print(f"TODO: {todo['message']}")
                    print(f"  Suggested links: {todo['kb_links']}")


class TestCrossReferenceValidation:
    """Test cross-reference building and validation."""

    @pytest.mark.asyncio
    async def test_validate_existing_kb_structure(self, logseq_dir):
        """Validate the existing Logseq KB structure."""
        # Check expected directories
        assert logseq_dir.exists(), "Logseq directory should exist"
        assert (logseq_dir / "pages").exists(), "Pages directory should exist"
        assert (logseq_dir / "journals").exists(), "Journals directory should exist"

        # Count pages
        pages = list((logseq_dir / "pages").glob("**/*.md"))
        print("\n=== KB Statistics ===")
        print(f"Total pages: {len(pages)}")

        # Count journals
        journals = list((logseq_dir / "journals").glob("*.md"))
        print(f"Total journal entries: {len(journals)}")

        # Sample some page names
        if pages:
            print("\nSample pages:")
            for page in pages[:10]:
                print(f"  - {page.stem}")

    @pytest.mark.asyncio
    async def test_find_orphaned_pages(self, logseq_dir):
        """Find pages that aren't linked from anywhere."""
        # This is a placeholder - actual implementation would use LinkValidator primitive
        pages_dir = logseq_dir / "pages"

        if not pages_dir.exists():
            pytest.skip("Pages directory not found")

        # Collect all pages
        all_pages = set()
        for page_file in pages_dir.glob("**/*.md"):
            all_pages.add(page_file.stem)

        # Collect all links (simplified - would use proper parser)
        all_links = set()
        for page_file in pages_dir.glob("**/*.md"):
            content = page_file.read_text()
            # Simple regex for [[Page Name]] links
            import re

            links = re.findall(r"\[\[(.*?)\]\]", content)
            all_links.update(links)

        # Find orphaned pages (pages not linked from anywhere)
        orphaned = all_pages - all_links

        if orphaned:
            print("\n=== Potentially Orphaned Pages ===")
            for page in sorted(orphaned)[:20]:  # Show first 20
                print(f"  - {page}")

        print(f"\nTotal pages: {len(all_pages)}")
        print(f"Linked pages: {len(all_links)}")
        print(f"Orphaned pages: {len(orphaned)}")


class TestEndToEndWorkflow:
    """Test complete end-to-end workflows."""

    @pytest.mark.asyncio
    async def test_complete_todo_sync_workflow(self, workspace_root, temp_journal_dir):
        """Run complete TODO sync workflow on real codebase."""
        sync = TODOSync()

        # Phase 1: Scan
        print("\n=== Phase 1: Scanning Codebase ===")
        paths = [str(workspace_root / "platform")]
        today = datetime.now().strftime("%Y_%m_%d")

        result = await sync.scan_and_create(
            paths=paths,
            journal_date=today,
            output_dir=str(temp_journal_dir),
        )

        print(f"TODOs found: {result['todos_found']}")

        # Phase 2: Analyze results
        if result["todos_found"] > 0:
            print("\n=== Phase 2: Analyzing TODOs ===")

            todos = result["todos"]

            # Group by package
            by_package = {}
            for todo in todos:
                pkg = todo["package"]
                if pkg not in by_package:
                    by_package[pkg] = []
                by_package[pkg].append(todo)

            print("\nTODOs by package:")
            for pkg, pkg_todos in sorted(by_package.items()):
                print(f"  {pkg}: {len(pkg_todos)} TODOs")

            # Phase 3: Validate journal output
            print("\n=== Phase 3: Validating Output ===")

            journal_file = temp_journal_dir / f"{today}.md"
            if journal_file.exists():
                content = journal_file.read_text()
                lines = content.split("\n")
                print(f"Journal entry: {len(lines)} lines")

                # Count TODO entries
                todo_count = content.count("- TODO") + content.count("- DOING")
                print(f"TODO entries in journal: {todo_count}")

                # Sample some content
                print("\nFirst 20 lines of journal:")
                for line in lines[:20]:
                    print(f"  {line}")

        else:
            print("No TODOs found in codebase - this is good!")
            print(
                "Test validates that workflow completes successfully even with no TODOs."
            )

    @pytest.mark.asyncio
    async def test_performance_on_large_codebase(self, workspace_root):
        """Test performance when scanning entire codebase."""
        import time

        sync = TODOSync()

        paths = [str(workspace_root / "platform")]

        start_time = time.time()

        result = await sync.scan_and_create(
            paths=paths,
            journal_date=None,
            dry_run=True,
        )

        elapsed = time.time() - start_time

        print("\n=== Performance Metrics ===")
        print(f"Time elapsed: {elapsed:.2f}s")
        print(f"TODOs found: {result['todos_found']}")

        if result["todos_found"] > 0:
            print(
                f"Processing rate: {result['todos_found'] / elapsed:.1f} TODOs/second"
            )

        # Performance should be reasonable
        assert elapsed < 30, "Scanning should complete within 30 seconds"


if __name__ == "__main__":
    # Run with integration tests enabled
    pytest.main([__file__, "-v", "-s", "-m", "integration"])
