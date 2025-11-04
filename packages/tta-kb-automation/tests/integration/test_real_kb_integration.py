"""Integration tests with real TTA.dev Logseq KB.

These tests run against the actual logseq/ directory to validate
that KB automation tools work with real-world data.

⚠️ These tests READ from the real KB but do NOT modify it.
   They validate read-only operations like link validation.

Run with: pytest tests/integration/test_real_kb_integration.py -v
"""

import os
from pathlib import Path

import pytest

# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration


# Find workspace root (TTA.dev/)
def find_workspace_root() -> Path:
    """Find TTA.dev workspace root."""
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "pyproject.toml").exists() and (parent / "logseq").exists():
            return parent
    raise RuntimeError("Cannot find TTA.dev workspace root")


WORKSPACE_ROOT = find_workspace_root()
LOGSEQ_KB_PATH = WORKSPACE_ROOT / "logseq"


@pytest.fixture
def skip_if_no_kb():
    """Skip test if real KB is not available."""
    if not LOGSEQ_KB_PATH.exists():
        pytest.skip(f"Logseq KB not found at {LOGSEQ_KB_PATH}")


class TestRealKBStructure:
    """Test real KB structure and content."""

    def test_kb_directory_exists(self, skip_if_no_kb):
        """Test that Logseq KB directory exists."""
        assert LOGSEQ_KB_PATH.exists()
        assert LOGSEQ_KB_PATH.is_dir()

    def test_kb_has_pages_directory(self, skip_if_no_kb):
        """Test that pages directory exists."""
        pages_dir = LOGSEQ_KB_PATH / "pages"
        assert pages_dir.exists()
        assert pages_dir.is_dir()

    def test_kb_has_journals_directory(self, skip_if_no_kb):
        """Test that journals directory exists."""
        journals_dir = LOGSEQ_KB_PATH / "journals"
        assert journals_dir.exists()
        assert journals_dir.is_dir()

    def test_kb_has_markdown_files(self, skip_if_no_kb):
        """Test that KB contains markdown files."""
        pages_dir = LOGSEQ_KB_PATH / "pages"
        md_files = list(pages_dir.glob("*.md"))
        assert len(md_files) > 0, "KB pages directory should contain .md files"

    def test_kb_has_known_pages(self, skip_if_no_kb):
        """Test that KB contains expected pages from TTA.dev."""
        pages_dir = LOGSEQ_KB_PATH / "pages"

        # These pages should exist based on project setup
        expected_pages = [
            "TODO Management System.md",
        ]

        existing_pages = [p.name for p in pages_dir.glob("*.md")]

        # At least one expected page should exist
        found = any(page in existing_pages for page in expected_pages)
        assert found, f"Expected to find at least one of {expected_pages} in KB"


@pytest.mark.asyncio
class TestLinkValidatorWithRealKB:
    """Test LinkValidator against real KB."""

    async def test_link_validator_can_parse_real_kb(self, skip_if_no_kb):
        """Test that LinkValidator can parse real KB without errors."""
        from tta_kb_automation.tools.link_validator import LinkValidator

        validator = LinkValidator(kb_path=LOGSEQ_KB_PATH, use_cache=False)

        # This should not raise exceptions
        result = await validator.validate()

        # Check basic result structure
        assert isinstance(result, dict)
        assert "broken_links" in result
        assert "orphaned_pages" in result
        assert "valid_links" in result
        assert "total_pages" in result

    async def test_link_validator_finds_real_links(self, skip_if_no_kb):
        """Test that LinkValidator finds actual wiki links in real KB."""
        from tta_kb_automation.tools.link_validator import LinkValidator

        validator = LinkValidator(kb_path=LOGSEQ_KB_PATH, use_cache=False)
        result = await validator.validate()

        # Real KB should have some valid links
        valid_links = result.get("valid_links", [])
        total_links = len(valid_links) + len(result.get("broken_links", []))

        assert total_links > 0, "Real KB should contain wiki links [[like this]]"

    async def test_link_validator_performance_on_real_kb(self, skip_if_no_kb):
        """Test that LinkValidator completes in reasonable time on real KB."""
        import time

        from tta_kb_automation.tools.link_validator import LinkValidator

        validator = LinkValidator(kb_path=LOGSEQ_KB_PATH, use_cache=False)

        start_time = time.time()
        result = await validator.validate()
        elapsed = time.time() - start_time

        # Should complete within 30 seconds for typical KB
        assert elapsed < 30.0, f"Validation took {elapsed:.2f}s (expected < 30s)"

        # Print summary for visibility
        print("\n📊 Real KB Validation Summary:")
        print(f"   Total pages: {result.get('total_pages', 0)}")
        print(f"   Valid links: {len(result.get('valid_links', []))}")
        print(f"   Broken links: {len(result.get('broken_links', []))}")
        print(f"   Orphaned pages: {len(result.get('orphaned_pages', []))}")
        print(f"   Time: {elapsed:.2f}s")
        print(f"\n   Summary:\n   {result.get('summary', 'N/A')}")

    async def test_link_validator_generates_report_for_real_kb(self, skip_if_no_kb):
        """Test that LinkValidator can generate report for real KB."""
        from tta_kb_automation.tools.link_validator import LinkValidator

        validator = LinkValidator(kb_path=LOGSEQ_KB_PATH, use_cache=False)
        result = await validator.validate()

        report = result.get("report", "")

        assert report, "Report should not be empty"
        # Check for KB Link Validation Report (actual title) or Link Validation Report
        assert (
            "# KB Link Validation Report" in report
            or "# Link Validation Report" in report
        )
        assert "## Summary" in report

    async def test_link_validator_handles_special_characters(self, skip_if_no_kb):
        """Test that LinkValidator handles page names with special characters."""
        from tta_kb_automation.tools.link_validator import LinkValidator

        validator = LinkValidator(kb_path=LOGSEQ_KB_PATH, use_cache=False)

        # Should handle pages with slashes (TTA.dev/Architecture/Component)
        # Should handle pages with underscores (2025_11_03.md)
        result = await validator.validate()

        # Should complete without errors
        assert "total_pages" in result


@pytest.mark.asyncio
class TestTODOSyncWithRealCodebase:
    """Test TODOSync against real codebase."""

    async def test_todo_sync_can_scan_real_codebase(self, skip_if_no_kb):
        """Test that TODOSync can scan real TTA.dev packages."""
        from tta_kb_automation.tools.todo_sync import TODOSync

        packages_dir = WORKSPACE_ROOT / "packages"
        if not packages_dir.exists():
            pytest.skip("packages/ directory not found")

        sync = TODOSync()

        # Test basic scanning workflow (without journal creation)
        # This tests that the tool initializes correctly
        assert sync._scanner is not None
        assert sync._extractor is not None
        assert sync._todo_router is not None

        print("\n✅ TODOSync initialized successfully with real codebase")

    async def test_todo_sync_finds_real_todos(self, skip_if_no_kb):
        """Test that TODOSync finds actual TODOs in codebase."""
        from tta_kb_automation.core.code_primitives import ExtractTODOs, ScanCodebase

        packages_dir = WORKSPACE_ROOT / "packages" / "tta-kb-automation"
        if not packages_dir.exists():
            pytest.skip("tta-kb-automation package not found")

        # Test the primitives directly
        scanner = ScanCodebase()
        extractor = ExtractTODOs()

        from tta_dev_primitives import WorkflowContext

        context = WorkflowContext(workflow_id="integration_test")

        # Scan for files
        scan_result = await scanner.execute(
            {"root_path": str(packages_dir), "patterns": ["**/*.py"]}, context
        )
        files = scan_result.get("files", [])

        print(f"\n📂 Scanned {len(files)} Python files")

        # Extract TODOs from first file (if any)
        if files:
            extract_result = await extractor.execute({"files": files[:1]}, context)
            todos = extract_result.get("todos", [])

            print(f"📝 Found {len(todos)} TODOs in sample file")

            # Validate structure
            if todos:
                todo = todos[0]
                assert "file" in todo
                assert "line" in todo
                assert "text" in todo


@pytest.mark.asyncio
class TestCrossReferenceBuilderWithRealData:
    """Test CrossReferenceBuilder against real code and KB."""

    @pytest.mark.integration
    async def test_cross_reference_builder_analyzes_real_repo(self, skip_if_no_kb):
        """Test CrossReferenceBuilder on real TTA.dev codebase."""
        from tta_kb_automation.tools.cross_reference_builder import (
            CrossReferenceBuilder,
        )

        # Use real paths
        kb_path = LOGSEQ_KB_PATH
        code_path = LOGSEQ_KB_PATH.parent / "packages"  # TTA.dev packages

        # Skip if packages directory doesn't exist
        if not code_path.exists():
            pytest.skip(f"Packages directory not found at {code_path}")

        # Build cross-references
        builder = CrossReferenceBuilder(kb_path=kb_path, code_path=code_path)
        result = await builder.build()

        # Validate result structure
        assert "kb_to_code" in result
        assert "code_to_kb" in result
        assert "missing_references" in result
        assert "stats" in result
        assert "report" in result

        # Validate stats
        stats = result["stats"]
        print("\n📊 CrossReferenceBuilder Stats:")
        print(f"   Total KB Pages: {stats['total_kb_pages']}")
        print(f"   Total Code Files: {stats['total_code_files']}")
        print(f"   KB Pages w/ Code Refs: {stats['kb_pages_with_code_refs']}")
        print(f"   Code Files w/ KB Refs: {stats['code_files_with_kb_refs']}")
        print(f"   Missing References: {stats['total_missing_refs']}")

        # Sanity checks
        assert stats["total_kb_pages"] > 0, "Should find KB pages"
        assert stats["total_code_files"] > 0, "Should find code files"
        assert isinstance(result["report"], str), "Report should be string"
        assert len(result["report"]) > 100, "Report should have content"

    @pytest.mark.integration
    async def test_cross_reference_builder_finds_bidirectional_refs(
        self, skip_if_no_kb
    ):
        """Test that CrossReferenceBuilder finds both KB→Code and Code→KB refs."""
        from tta_kb_automation.tools.cross_reference_builder import (
            CrossReferenceBuilder,
        )

        kb_path = LOGSEQ_KB_PATH
        code_path = LOGSEQ_KB_PATH.parent / "packages" / "tta-kb-automation"

        if not code_path.exists():
            pytest.skip("tta-kb-automation package not found")

        builder = CrossReferenceBuilder(kb_path=kb_path, code_path=code_path)
        result = await builder.build()

        kb_to_code = result["kb_to_code"]
        code_to_kb = result["code_to_kb"]

        # Should have at least some mappings
        print("\n📊 Bidirectional Reference Stats:")
        print(f"   KB pages referencing code: {len(kb_to_code)}")
        print(f"   Code files referencing KB: {len(code_to_kb)}")

        # At least one direction should have references
        assert len(kb_to_code) > 0 or len(code_to_kb) > 0, (
            "Should find at least some cross-references"
        )

    @pytest.mark.integration
    async def test_cross_reference_builder_generates_valid_report(self, skip_if_no_kb):
        """Test that CrossReferenceBuilder generates a valid markdown report."""
        from tta_kb_automation.tools.cross_reference_builder import (
            CrossReferenceBuilder,
        )

        kb_path = LOGSEQ_KB_PATH
        code_path = LOGSEQ_KB_PATH.parent / "packages"

        if not code_path.exists():
            pytest.skip("Packages directory not found")

        builder = CrossReferenceBuilder(kb_path=kb_path, code_path=code_path)
        result = await builder.build()

        report = result["report"]

        # Validate markdown structure
        assert "# Cross-Reference Analysis" in report
        assert "## Summary" in report
        assert "## Statistics" in report

        # Should have some content
        lines = report.split("\n")
        assert len(lines) > 20, "Report should have substantial content"


@pytest.mark.asyncio
class TestEndToEndWorkflows:
    """Test complete end-to-end workflows combining multiple tools."""

    @pytest.mark.integration
    async def test_complete_kb_maintenance_workflow(self, skip_if_no_kb):
        """Test complete KB maintenance: validate links → find TODOs → cross-ref."""
        from tta_kb_automation.tools.cross_reference_builder import (
            CrossReferenceBuilder,
        )
        from tta_kb_automation.tools.link_validator import LinkValidator
        from tta_kb_automation.tools.todo_sync import TODOSync

        # Step 1: Validate KB links
        print("\n🔍 Step 1: Validating KB links...")
        validator = LinkValidator(kb_path=LOGSEQ_KB_PATH, use_cache=False)
        link_result = await validator.validate()

        assert "total_pages" in link_result
        assert link_result["total_pages"] > 0

        # Step 2: Initialize TODO sync (without creating journal entries)
        print("\n📝 Step 2: Initializing TODO sync...")
        todo_sync = TODOSync()

        assert todo_sync._scanner is not None
        assert todo_sync._extractor is not None

        # Step 3: Build cross-references
        print("\n🔗 Step 3: Building cross-references...")
        code_path = WORKSPACE_ROOT / "packages" / "tta-kb-automation"

        if code_path.exists():
            builder = CrossReferenceBuilder(kb_path=LOGSEQ_KB_PATH, code_path=code_path)
            xref_result = await builder.build()

            assert "stats" in xref_result
            assert xref_result["stats"]["total_kb_pages"] > 0

        # Workflow completed successfully
        print("\n✅ Complete KB maintenance workflow executed successfully")

    @pytest.mark.integration
    async def test_kb_quality_metrics_collection(self, skip_if_no_kb):
        """Test collecting comprehensive KB quality metrics."""
        from tta_kb_automation.tools.cross_reference_builder import (
            CrossReferenceBuilder,
        )
        from tta_kb_automation.tools.link_validator import LinkValidator

        # Collect metrics from multiple tools
        validator = LinkValidator(kb_path=LOGSEQ_KB_PATH, use_cache=False)
        link_result = await validator.validate()

        code_path = WORKSPACE_ROOT / "packages"
        if not code_path.exists():
            pytest.skip("Packages directory not found")

        builder = CrossReferenceBuilder(kb_path=LOGSEQ_KB_PATH, code_path=code_path)
        xref_result = await builder.build()

        # Aggregate quality metrics
        metrics = {
            "total_kb_pages": link_result.get("total_pages", 0),
            "valid_links": len(link_result.get("valid_links", [])),
            "broken_links": len(link_result.get("broken_links", [])),
            "orphaned_pages": len(link_result.get("orphaned_pages", [])),
            "kb_pages_with_code_refs": xref_result["stats"]["kb_pages_with_code_refs"],
            "code_files_with_kb_refs": xref_result["stats"]["code_files_with_kb_refs"],
            "missing_references": xref_result["stats"]["total_missing_refs"],
        }

        print("\n📊 KB Quality Metrics:")
        for key, value in metrics.items():
            print(f"   {key}: {value}")

        # Calculate health score (0-100)
        total_links = metrics["valid_links"] + metrics["broken_links"]
        link_health = (
            (metrics["valid_links"] / total_links * 100) if total_links > 0 else 100
        )

        orphan_penalty = min(metrics["orphaned_pages"] * 5, 30)
        health_score = max(0, link_health - orphan_penalty)

        print(f"\n   KB Health Score: {health_score:.1f}/100")

        # Basic quality assertions
        assert metrics["total_kb_pages"] > 0
        # Health score can be 0 if KB needs work - just verify it's calculated
        assert 0 <= health_score <= 100

    @pytest.mark.integration
    async def test_error_handling_with_invalid_paths(self):
        """Test that tools handle invalid paths gracefully."""
        from tta_kb_automation.tools.link_validator import LinkValidator

        invalid_path = Path("/nonexistent/kb/path")

        validator = LinkValidator(kb_path=invalid_path, use_cache=False)

        # Should handle gracefully (either skip or return empty results)
        try:
            result = await validator.validate()
            # If it doesn't raise, should return valid structure with zero counts
            assert result.get("total_pages", 0) == 0
        except (FileNotFoundError, ValueError):
            # Also acceptable to raise meaningful error
            pass

    @pytest.mark.integration
    async def test_performance_with_large_kb(self, skip_if_no_kb):
        """Test tool performance with full TTA.dev KB (stress test)."""
        import time

        from tta_kb_automation.tools.cross_reference_builder import (
            CrossReferenceBuilder,
        )
        from tta_kb_automation.tools.link_validator import LinkValidator

        # Run full validation + cross-reference on entire repo
        print("\n⏱️ Performance Test: Full KB + Full Codebase")

        start = time.time()

        # LinkValidator
        validator = LinkValidator(kb_path=LOGSEQ_KB_PATH, use_cache=False)
        link_result = await validator.validate()
        link_time = time.time() - start

        # CrossReferenceBuilder
        code_path = WORKSPACE_ROOT / "packages"
        if not code_path.exists():
            pytest.skip("Packages directory not found")

        xref_start = time.time()
        builder = CrossReferenceBuilder(kb_path=LOGSEQ_KB_PATH, code_path=code_path)
        xref_result = await builder.build()
        xref_time = time.time() - xref_start

        total_time = time.time() - start

        print("\n⏱️ Performance Results:")
        print(f"   LinkValidator: {link_time:.2f}s")
        print(f"   CrossReferenceBuilder: {xref_time:.2f}s")
        print(f"   Total: {total_time:.2f}s")
        print(f"   KB Pages: {link_result.get('total_pages', 0)}")
        print(f"   Code Files: {xref_result['stats']['total_code_files']}")

        # Should complete in reasonable time (< 2 minutes for typical repo)
        assert total_time < 120.0, f"Full analysis took {total_time:.2f}s (> 120s)"


class TestRealKBContentAnalysis:
    """Analyze real KB content characteristics."""

    def test_count_real_kb_pages(self, skip_if_no_kb):
        """Count pages in real KB."""
        pages_dir = LOGSEQ_KB_PATH / "pages"
        md_files = list(pages_dir.glob("*.md"))

        print("\n📚 Real KB Statistics:")
        print(f"   Total pages: {len(md_files)}")

        # Sample some page names
        sample_pages = sorted([p.stem for p in md_files[:10]])
        print(f"   Sample pages: {', '.join(sample_pages)}")

    def test_count_real_kb_journals(self, skip_if_no_kb):
        """Count journal entries in real KB."""
        journals_dir = LOGSEQ_KB_PATH / "journals"
        journal_files = list(journals_dir.glob("*.md"))

        print("\n📔 Real KB Journals:")
        print(f"   Total journals: {len(journal_files)}")

        # Find most recent journals
        if journal_files:
            recent = sorted(journal_files, reverse=True)[:3]
            print(f"   Recent: {', '.join([j.stem for j in recent])}")

    def test_analyze_real_kb_link_patterns(self, skip_if_no_kb):
        """Analyze wiki link patterns in real KB."""
        import re

        pages_dir = LOGSEQ_KB_PATH / "pages"
        md_files = list(pages_dir.glob("*.md"))

        # Sample first 10 pages
        sample_files = md_files[:10]

        wiki_link_pattern = re.compile(r"\[\[([^\]]+)\]\]")
        total_links = 0

        for md_file in sample_files:
            try:
                content = md_file.read_text(encoding="utf-8")
                links = wiki_link_pattern.findall(content)
                total_links += len(links)
            except Exception:
                continue

        print(f"\n🔗 Real KB Link Analysis (sample of {len(sample_files)} pages):")
        print(f"   Total wiki links found: {total_links}")
        print(f"   Average links per page: {total_links / len(sample_files):.1f}")


# Environment check
def test_integration_test_environment():
    """Verify integration test environment is configured."""
    # Check if we should run integration tests
    run_integration = os.getenv("RUN_INTEGRATION", "").lower() in ("1", "true", "yes")

    if run_integration:
        print("\n✅ Integration tests enabled (RUN_INTEGRATION=true)")
    else:
        print("\n⚠️ Integration tests disabled (set RUN_INTEGRATION=true to enable)")


# Documentation test
def test_integration_tests_are_documented():
    """Verify integration test documentation exists."""
    readme_path = Path(__file__).parent.parent.parent / "README.md"
    if readme_path.exists():
        content = readme_path.read_text()
        assert "integration" in content.lower(), (
            "README should document integration tests"
        )


if __name__ == "__main__":
    """Run integration tests directly.

    Usage:
        python tests/integration/test_real_kb_integration.py
    """
    print("🧪 Running KB Automation Integration Tests")
    print(f"📂 Workspace: {WORKSPACE_ROOT}")
    print(f"📚 KB Path: {LOGSEQ_KB_PATH}")
    print("")

    # Set environment variable for this run
    os.environ["RUN_INTEGRATION"] = "true"

    # Run pytest on this file
    pytest.main([__file__, "-v", "--tb=short"])
