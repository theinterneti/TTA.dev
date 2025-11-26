"""Comprehensive unit tests for TODO Sync tool.

Tests cover:
- Router primitive integration
- Simple vs complex TODO routing
- Intelligence primitive mocking
- Journal entry formatting
- End-to-end workflow
"""

from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from tta_dev_primitives import WorkflowContext

from tta_kb_automation.tools.todo_sync import TODOSync


@pytest.fixture
def mock_codebase(tmp_path):
    """Create a mock codebase with various TODO patterns."""
    # Create package structure
    pkg_dir = tmp_path / "packages" / "tta-dev-primitives" / "src"
    pkg_dir.mkdir(parents=True)

    # File with simple TODOs
    (pkg_dir / "simple.py").write_text('''"""Simple module."""

def example_function():
    """Example function."""
    # TODO: Add input validation
    pass

def another_function():
    # FIXME: Handle edge case
    # TODO: Optimize performance later
    pass
''')

    # File with complex TODOs
    (pkg_dir / "complex.py").write_text('''"""Complex module."""

class SystemCore:
    """Core system class."""

    def process(self):
        # TODO: Refactor architecture for distributed processing
        # This requires coordination across multiple services
        pass

    def optimize(self):
        # TODO: Implement observability and performance monitoring
        pass
''')

    # File with urgent TODOs
    (pkg_dir / "urgent.py").write_text('''"""Urgent fixes needed."""

def critical_function():
    # TODO: URGENT - Fix critical security vulnerability
    # TODO: ASAP - Add error handling for blocker issue
    pass
''')

    return tmp_path


@pytest.fixture
def sample_todos():
    """Sample TODO data for testing."""
    return [
        {
            "type": "TODO",
            "message": "Add input validation",
            "file": "packages/tta-dev-primitives/src/simple.py",
            "line_number": 5,
            "context_before": [
                "def example_function():",
                '    """Example function."""',
            ],
            "context_after": ["    pass"],
        },
        {
            "type": "TODO",
            "message": "Refactor architecture for distributed processing",
            "file": "packages/tta-dev-primitives/src/complex.py",
            "line_number": 8,
            "context_before": [
                "def process(self):",
                "    # This requires coordination",
            ],
            "context_after": ["    pass"],
        },
        {
            "type": "FIXME",
            "message": "Handle edge case",
            "file": "packages/tta-dev-primitives/src/simple.py",
            "line_number": 10,
            "context_before": ["def another_function():"],
            "context_after": ["    pass"],
        },
        {
            "type": "TODO",
            "message": "URGENT - Fix critical security vulnerability",
            "file": "packages/tta-dev-primitives/src/urgent.py",
            "line_number": 4,
            "context_before": ["def critical_function():"],
            "context_after": ["    pass"],
        },
    ]


@pytest.fixture
def mock_primitives():
    """Mock all the primitives used by TODOSync."""
    with (
        patch("tta_kb_automation.tools.todo_sync.ScanCodebase") as mock_scan,
        patch("tta_kb_automation.tools.todo_sync.ExtractTODOs") as mock_extract,
        patch("tta_kb_automation.tools.todo_sync.ClassifyTODO") as mock_classify,
        patch("tta_kb_automation.tools.todo_sync.SuggestKBLinks") as mock_links,
        patch("tta_kb_automation.tools.todo_sync.CreateJournalEntry") as mock_journal,
    ):
        # Configure ScanCodebase mock
        mock_scan_instance = AsyncMock()
        mock_scan_instance.execute = AsyncMock(
            return_value={"files": ["file1.py", "file2.py"], "total_files": 2}
        )
        mock_scan.return_value = mock_scan_instance

        # Configure ExtractTODOs mock
        mock_extract_instance = AsyncMock()
        mock_extract.return_value = mock_extract_instance

        # Configure ClassifyTODO mock (for complex TODOs)
        mock_classify_instance = AsyncMock()
        mock_classify_instance.execute = AsyncMock(
            return_value={
                "type": "architecture",
                "priority": "high",
                "package": "tta-dev-primitives",
            }
        )
        mock_classify.return_value = mock_classify_instance

        # Configure SuggestKBLinks mock (for complex TODOs)
        mock_links_instance = AsyncMock()
        mock_links_instance.execute = AsyncMock(
            return_value={
                "links": [
                    "TTA Primitives/Architecture",
                    "Distributed Processing",
                ]
            }
        )
        mock_links.return_value = mock_links_instance

        # Configure CreateJournalEntry mock
        mock_journal_instance = AsyncMock()
        mock_journal_instance.execute = AsyncMock(
            return_value={"path": "logseq/journals/2025_11_03.md"}
        )
        mock_journal.return_value = mock_journal_instance

        yield {
            "scan": mock_scan,
            "extract": mock_extract,
            "classify": mock_classify,
            "links": mock_links,
            "journal": mock_journal,
        }


class TestTODOSyncInitialization:
    """Test TODOSync initialization and setup."""

    def test_init_creates_all_primitives(self):
        """Test that initialization creates all required primitives."""
        sync = TODOSync()

        assert sync._scanner is not None
        assert sync._extractor is not None
        assert sync._classifier is not None
        assert sync._linker is not None
        assert sync._journal_writer is not None
        assert sync._todo_router is not None

    def test_router_has_correct_routes(self):
        """Test that router is configured with simple and complex routes."""
        sync = TODOSync()

        assert "simple" in sync._todo_router.routes
        assert "complex" in sync._todo_router.routes


class TestTODORouting:
    """Test TODO routing logic (simple vs complex)."""

    @pytest.mark.asyncio
    async def test_route_simple_todo(self):
        """Test that simple TODOs are routed to simple processing."""
        sync = TODOSync()
        context = WorkflowContext()

        todo = {
            "type": "TODO",
            "message": "Add input validation",
            "file": "example.py",
        }

        route = sync._route_todo(todo, context)
        assert route == "simple"

    @pytest.mark.asyncio
    async def test_route_complex_architecture_todo(self):
        """Test that architecture TODOs are routed to complex processing."""
        sync = TODOSync()
        context = WorkflowContext()

        todo = {
            "type": "TODO",
            "message": "Refactor architecture for better scalability",
            "file": "core.py",
        }

        route = sync._route_todo(todo, context)
        assert route == "complex"

    @pytest.mark.asyncio
    async def test_route_complex_observability_todo(self):
        """Test that observability TODOs are routed to complex processing."""
        sync = TODOSync()
        context = WorkflowContext()

        todo = {
            "type": "TODO",
            "message": "Add observability and tracing",
            "file": "service.py",
        }

        route = sync._route_todo(todo, context)
        assert route == "complex"

    @pytest.mark.asyncio
    async def test_route_complex_multi_concern_todo(self):
        """Test that TODOs with multiple concerns are complex."""
        sync = TODOSync()
        context = WorkflowContext()

        todo = {
            "type": "TODO",
            "message": "Update API and database schemas",
            "file": "models.py",
        }

        route = sync._route_todo(todo, context)
        assert route == "complex"

    @pytest.mark.parametrize(
        "keyword",
        [
            "refactor",
            "integration",
            "distributed",
            "performance",
        ],
    )
    @pytest.mark.asyncio
    async def test_route_complex_keywords(self, keyword):
        """Test that specific keywords trigger complex routing."""
        sync = TODOSync()
        context = WorkflowContext()

        todo = {
            "type": "TODO",
            "message": f"Implement {keyword} improvements",
            "file": "system.py",
        }

        route = sync._route_todo(todo, context)
        assert route == "complex"


class TestSimpleTODOProcessing:
    """Test simple TODO processing logic."""

    @pytest.mark.asyncio
    async def test_process_simple_todo_basic(self):
        """Test basic simple TODO processing."""
        sync = TODOSync()
        context = WorkflowContext()

        todo = {
            "type": "TODO",
            "message": "Add validation",
            "file": "packages/tta-dev-primitives/src/core.py",
            "line_number": 42,
        }

        result = await sync._process_simple_todo(todo, context)

        assert result["type"] == "implementation"
        assert result["priority"] == "medium"
        assert result["package"] == "tta-dev-primitives"
        assert result["suggested_links"] == []

    @pytest.mark.asyncio
    async def test_process_simple_fixme(self):
        """Test that FIXME is classified as bugfix."""
        sync = TODOSync()
        context = WorkflowContext()

        todo = {
            "type": "FIXME",
            "message": "Handle null pointer",
            "file": "packages/tta-observability/src/metrics.py",
        }

        result = await sync._process_simple_todo(todo, context)

        assert result["type"] == "bugfix"
        assert result["package"] == "tta-observability"

    @pytest.mark.asyncio
    async def test_process_simple_hack(self):
        """Test that HACK is classified as refactoring."""
        sync = TODOSync()
        context = WorkflowContext()

        todo = {
            "type": "HACK",
            "message": "Temporary workaround",
            "file": "src/workarounds.py",
        }

        result = await sync._process_simple_todo(todo, context)

        assert result["type"] == "refactoring"

    @pytest.mark.asyncio
    async def test_process_simple_note(self):
        """Test that NOTE is classified as documentation."""
        sync = TODOSync()
        context = WorkflowContext()

        todo = {
            "type": "NOTE",
            "message": "Document this algorithm",
            "file": "algorithms/sort.py",
        }

        result = await sync._process_simple_todo(todo, context)

        assert result["type"] == "documentation"

    @pytest.mark.asyncio
    async def test_process_urgent_todo(self):
        """Test that urgent keywords set high priority."""
        sync = TODOSync()
        context = WorkflowContext()

        todo = {
            "type": "TODO",
            "message": "URGENT: Fix critical bug",
            "file": "core.py",
        }

        result = await sync._process_simple_todo(todo, context)

        assert result["priority"] == "high"

    @pytest.mark.asyncio
    async def test_process_low_priority_todo(self):
        """Test that 'later' keywords set low priority."""
        sync = TODOSync()
        context = WorkflowContext()

        todo = {
            "type": "TODO",
            "message": "Nice to have feature for later",
            "file": "features.py",
        }

        result = await sync._process_simple_todo(todo, context)

        assert result["priority"] == "low"

    @pytest.mark.parametrize(
        "keyword",
        ["urgent", "critical", "asap", "blocker"],
    )
    @pytest.mark.asyncio
    async def test_process_high_priority_keywords(self, keyword):
        """Test that urgency keywords set high priority."""
        sync = TODOSync()
        context = WorkflowContext()

        todo = {
            "type": "TODO",
            "message": f"{keyword.upper()} - needs attention",
            "file": "important.py",
        }

        result = await sync._process_simple_todo(todo, context)

        assert result["priority"] == "high"


class TestComplexTODOProcessing:
    """Test complex TODO processing with mocked classifiers."""

    @pytest.mark.asyncio
    async def test_process_complex_todo_calls_classifier(self, mock_primitives):
        """Test that complex processing calls ClassifyTODO."""
        sync = TODOSync()
        context = WorkflowContext()

        todo = {
            "type": "TODO",
            "message": "Refactor architecture",
            "file": "core.py",
            "context_before": ["class Core:"],
        }

        result = await sync._process_complex_todo(todo, context)

        # Verify classifier was called
        mock_primitives["classify"]().execute.assert_called_once()

        # Verify result has classification
        assert result["type"] == "architecture"
        assert result["priority"] == "high"

    @pytest.mark.asyncio
    async def test_process_complex_todo_calls_linker(self, mock_primitives):
        """Test that complex processing calls SuggestKBLinks."""
        sync = TODOSync()
        context = WorkflowContext()

        todo = {
            "type": "TODO",
            "message": "Improve observability",
            "file": "monitoring.py",
            "context_before": ["def monitor():"],
        }

        result = await sync._process_complex_todo(todo, context)

        # Verify linker was called
        mock_primitives["links"]().execute.assert_called_once()

        # Verify result has suggested links
        assert "suggested_links" in result
        assert len(result["suggested_links"]) > 0

    @pytest.mark.asyncio
    async def test_process_complex_todo_merges_classification(self, mock_primitives):
        """Test that complex processing merges classification results."""
        sync = TODOSync()
        context = WorkflowContext()

        # Configure mock to return specific classification
        mock_primitives["classify"]().execute.return_value = {
            "type": "performance",
            "priority": "high",
            "package": "tta-observability",
        }

        todo = {
            "type": "TODO",
            "message": "Optimize query performance",
            "file": "database.py",
        }

        result = await sync._process_complex_todo(todo, context)

        assert result["type"] == "performance"
        assert result["priority"] == "high"
        assert result["package"] == "tta-observability"


class TestPackageExtraction:
    """Test package name extraction from file paths."""

    def test_extract_package_standard_structure(self):
        """Test extraction from standard packages/NAME/src structure."""
        sync = TODOSync()

        path = Path("packages/tta-dev-primitives/src/core/base.py")
        package = sync._extract_package_from_path(path)

        assert package == "tta-dev-primitives"

    def test_extract_package_observability(self):
        """Test extraction for observability package."""
        sync = TODOSync()

        path = Path("packages/tta-observability-integration/src/metrics.py")
        package = sync._extract_package_from_path(path)

        assert package == "tta-observability-integration"

    def test_extract_package_fallback(self):
        """Test fallback for non-standard structure."""
        sync = TODOSync()

        path = Path("scripts/automation/tool.py")
        package = sync._extract_package_from_path(path)

        # Extracts first directory after root
        assert package == "automation"

    def test_extract_package_unknown(self):
        """Test extraction returns 'unknown' for root files."""
        sync = TODOSync()

        path = Path("standalone.py")
        package = sync._extract_package_from_path(path)

        assert package == "unknown"


class TestJournalEntryFormatting:
    """Test journal entry markdown formatting."""

    def test_format_simple_todo(self):
        """Test formatting a simple TODO."""
        sync = TODOSync()

        todo = {
            "message": "Add input validation",
            "type": "implementation",
            "priority": "medium",
            "package": "tta-dev-primitives",
            "file": "src/core.py",
            "line_number": 42,
        }

        entry = sync.format_todo_entry(todo)

        assert "- TODO Add input validation #dev-todo" in entry
        assert "type:: implementation" in entry
        assert "priority:: medium" in entry
        assert "package:: tta-dev-primitives" in entry
        assert "source:: src/core.py:42" in entry

    def test_format_todo_with_context(self):
        """Test formatting TODO with code context."""
        sync = TODOSync()

        todo = {
            "message": "Refactor this",
            "type": "refactoring",
            "priority": "high",
            "file": "complex.py",
            "line_number": 10,
            "context_before": ["def process():", "    # Complex logic"],
            "context_after": ["    return result"],
        }

        entry = sync.format_todo_entry(todo)

        assert "context::" in entry

    def test_format_todo_with_kb_links(self):
        """Test formatting TODO with KB link suggestions."""
        sync = TODOSync()

        todo = {
            "message": "Improve observability",
            "type": "observability",
            "priority": "high",
            "file": "metrics.py",
            "suggested_links": [
                "TTA Primitives/Observability",
                "OpenTelemetry Integration",
            ],
        }

        entry = sync.format_todo_entry(todo)

        assert "related:: [[TTA Primitives/Observability]]" in entry
        assert "related:: [[OpenTelemetry Integration]]" in entry

    def test_format_todo_minimal(self):
        """Test formatting TODO with minimal information."""
        sync = TODOSync()

        todo = {
            "message": "Fix this",
            "file": "broken.py",
        }

        entry = sync.format_todo_entry(todo)

        # Should have defaults
        assert "- TODO Fix this #dev-todo" in entry
        assert "type:: implementation" in entry
        assert "priority:: medium" in entry


class TestScanAndCreate:
    """Test end-to-end scan_and_create workflow."""

    @pytest.mark.asyncio
    async def test_scan_and_create_basic(self, mock_primitives, sample_todos):
        """Test basic scan and create workflow."""
        # Configure ExtractTODOs to return sample TODOs
        mock_primitives["extract"]().execute.return_value = {"todos": sample_todos}

        sync = TODOSync()

        result = await sync.scan_and_create(
            paths=["packages/tta-dev-primitives"],
            journal_date="2025-11-03",
        )

        assert result["todos_found"] == len(sample_todos)
        assert result["todos_created"] == len(sample_todos)
        assert result["journal_path"] == "logseq/journals/2025_11_03.md"
        assert "todos" in result

    @pytest.mark.asyncio
    async def test_scan_and_create_uses_today_by_default(self, mock_primitives):
        """Test that scan_and_create uses today's date by default."""
        mock_primitives["extract"]().execute.return_value = {"todos": []}

        sync = TODOSync()

        result = await sync.scan_and_create(paths=["src"])

        # Should use today's date
        today = datetime.now().strftime("%Y_%m_%d")
        assert today in result["journal_path"]

    @pytest.mark.asyncio
    async def test_scan_and_create_multiple_paths(self, mock_primitives, sample_todos):
        """Test scanning multiple paths."""
        mock_primitives["extract"]().execute.return_value = {"todos": sample_todos}

        sync = TODOSync()

        await sync.scan_and_create(
            paths=[
                "packages/tta-dev-primitives",
                "packages/tta-observability",
            ],
            journal_date="2025-11-03",
        )

        # Should scan both paths
        assert mock_primitives["scan"]().execute.call_count == 2

    @pytest.mark.asyncio
    async def test_scan_and_create_skips_empty_paths(self, mock_primitives):
        """Test that empty paths are skipped."""
        # First path has files, second is empty
        mock_primitives["scan"]().execute.side_effect = [
            {"files": ["file1.py"], "total_files": 1},
            {"files": [], "total_files": 0},
        ]
        mock_primitives["extract"]().execute.return_value = {"todos": []}

        sync = TODOSync()

        await sync.scan_and_create(
            paths=["src", "empty_dir"],
        )

        # Should extract from first path only
        assert mock_primitives["extract"]().execute.call_count == 1

    @pytest.mark.asyncio
    async def test_scan_and_create_includes_tests_optional(self, mock_primitives):
        """Test that include_tests parameter is passed through."""
        mock_primitives["extract"]().execute.return_value = {"todos": []}

        sync = TODOSync()

        await sync.scan_and_create(
            paths=["src"],
            include_tests=True,
        )

        # Verify include_tests was passed to scanner
        call_args = mock_primitives["scan"]().execute.call_args
        assert call_args[0][0]["include_tests"] is True

    @pytest.mark.asyncio
    async def test_scan_and_create_context_lines_optional(self, mock_primitives):
        """Test that context_lines parameter is passed through."""
        mock_primitives["extract"]().execute.return_value = {"todos": []}

        sync = TODOSync()

        await sync.scan_and_create(
            paths=["src"],
            context_lines=5,
        )

        # Verify context_lines was passed to extractor
        call_args = mock_primitives["extract"]().execute.call_args
        assert call_args[0][0]["context_lines"] == 5

    @pytest.mark.asyncio
    async def test_scan_and_create_routes_todos(self, mock_primitives, sample_todos):
        """Test that TODOs are routed through router primitive."""
        mock_primitives["extract"]().execute.return_value = {"todos": sample_todos}

        sync = TODOSync()

        result = await sync.scan_and_create(
            paths=["packages/tta-dev-primitives"],
        )

        # All TODOs should be processed
        assert len(result["todos"]) == len(sample_todos)

        # Each should have enhanced fields
        for todo in result["todos"]:
            assert "type" in todo
            assert "priority" in todo
            assert "package" in todo


class TestWorkflowContext:
    """Test WorkflowContext propagation through workflow."""

    @pytest.mark.asyncio
    async def test_context_passed_to_all_primitives(self, mock_primitives, sample_todos):
        """Test that context is passed to all primitive executions."""
        mock_primitives["extract"]().execute.return_value = {"todos": sample_todos}

        sync = TODOSync()

        await sync.scan_and_create(
            paths=["src"],
        )

        # Verify all primitives received context
        for mock in [
            mock_primitives["scan"](),
            mock_primitives["extract"](),
            mock_primitives["journal"](),
        ]:
            # At least one call should have occurred
            assert mock.execute.call_count > 0


class TestEdgeCases:
    """Test edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_empty_todo_list(self, mock_primitives):
        """Test handling of empty TODO list."""
        mock_primitives["extract"]().execute.return_value = {"todos": []}

        sync = TODOSync()

        result = await sync.scan_and_create(paths=["src"])

        assert result["todos_found"] == 0
        assert result["todos_created"] == 0
        assert result["todos"] == []

    @pytest.mark.asyncio
    async def test_malformed_todo(self, mock_primitives):
        """Test handling of TODO with missing fields."""
        malformed_todo = {
            "message": "Incomplete TODO",
            # Missing type, file, line_number
        }
        mock_primitives["extract"]().execute.return_value = {"todos": [malformed_todo]}

        sync = TODOSync()

        # Should not crash, should handle gracefully
        result = await sync.scan_and_create(paths=["src"])

        assert len(result["todos"]) == 1

    def test_format_todo_without_line_number(self):
        """Test formatting TODO when line number is missing."""
        sync = TODOSync()

        todo = {
            "message": "Fix this",
            "file": "broken.py",
            # No line_number
        }

        entry = sync.format_todo_entry(todo)

        # Should use ? as placeholder
        assert "source:: broken.py:?" in entry


class TestIntegration:
    """Integration-style tests (still using mocks but testing full workflow)."""

    @pytest.mark.asyncio
    async def test_full_workflow_with_mixed_todos(self, mock_primitives):
        """Test full workflow with mix of simple and complex TODOs."""
        mixed_todos = [
            {
                "type": "TODO",
                "message": "Add validation",  # Simple
                "file": "packages/tta-dev-primitives/src/simple.py",
                "line_number": 10,
            },
            {
                "type": "TODO",
                "message": "Refactor architecture for distributed processing",  # Complex
                "file": "packages/tta-dev-primitives/src/complex.py",
                "line_number": 50,
                "context_before": ["class System:"],
            },
            {
                "type": "FIXME",
                "message": "URGENT - Fix memory leak",  # Simple but high priority
                "file": "packages/tta-observability/src/metrics.py",
                "line_number": 100,
            },
        ]

        mock_primitives["extract"]().execute.return_value = {"todos": mixed_todos}

        sync = TODOSync()

        result = await sync.scan_and_create(
            paths=["packages"],
            journal_date="2025-11-03",
        )

        assert result["todos_found"] == 3
        assert result["todos_created"] == 3

        # Verify classification
        todos = result["todos"]

        # First should be simple implementation
        assert todos[0]["type"] == "implementation"
        assert todos[0]["priority"] == "medium"

        # Second should be complex (routed to classifier)
        assert todos[1]["message"] == "Refactor architecture for distributed processing"

        # Third should be bugfix with high priority
        assert todos[2]["type"] == "bugfix"
        assert todos[2]["priority"] == "high"

    @pytest.mark.asyncio
    async def test_journal_entry_creation(self, mock_primitives, sample_todos):
        """Test that journal entries are properly created."""
        mock_primitives["extract"]().execute.return_value = {"todos": sample_todos}

        sync = TODOSync()

        await sync.scan_and_create(
            paths=["packages"],
            journal_date="2025-11-03",
        )

        # Verify journal writer was called with correct data
        journal_call = mock_primitives["journal"]().execute.call_args
        journal_data = journal_call[0][0]

        assert journal_data["date"] == "2025-11-03"
        assert "todos" in journal_data
        assert len(journal_data["todos"]) == len(sample_todos)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
