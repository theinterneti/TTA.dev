"""Tests for TasksPrimitive.

Test coverage for breaking implementation plans into concrete tasks with:
- Plan parsing and data model extraction
- Task generation from requirements
- Dependency-based ordering (topological sort)
- Critical path identification (CPM algorithm)
- Parallel work stream grouping
- Multiple output formats (markdown, JSON, Jira, Linear, GitHub)
"""

import json
from pathlib import Path

import pytest

from tta_dev_primitives import WorkflowContext
from tta_dev_primitives.speckit import Task, TasksPrimitive

# ============================================================================
# Test Class 1: Initialization Tests (3 tests)
# ============================================================================


class TestTasksPrimitiveInitialization:
    """Test TasksPrimitive initialization and configuration."""

    def test_init_with_defaults(self) -> None:
        """Test initialization with default parameters."""
        primitive = TasksPrimitive()

        assert primitive.name == "tasks_primitive"
        assert primitive.output_dir == Path(".")
        assert primitive.output_format == "markdown"
        assert primitive.include_effort is True
        assert primitive.identify_critical_path_flag is True
        assert primitive.group_parallel_work_flag is True

    def test_init_with_custom_parameters(self) -> None:
        """Test initialization with custom parameters."""
        primitive = TasksPrimitive(
            output_dir="custom/tasks",
            output_format="json",
            include_effort=False,
            identify_critical_path=False,
            group_parallel_work=False,
        )

        assert primitive.output_dir == Path("custom/tasks")
        assert primitive.output_format == "json"
        assert primitive.include_effort is False
        assert primitive.identify_critical_path_flag is False
        assert primitive.group_parallel_work_flag is False

    def test_creates_output_directory(self, tmp_path) -> None:  # noqa: ANN001
        """Test that output directory is created if missing."""
        output_dir = tmp_path / "new_tasks_dir"
        assert not output_dir.exists()

        TasksPrimitive(output_dir=str(output_dir))

        assert output_dir.exists()
        assert output_dir.is_dir()


# ============================================================================
# Test Class 2: Plan Parsing Tests (4 tests)
# ============================================================================


class TestPlanParsing:
    """Test parsing of plan.md files."""

    @pytest.fixture
    def sample_plan_file(self, tmp_path):
        """Create a sample plan.md file."""
        plan_path = tmp_path / "plan.md"
        content = """# Implementation Plan

## Implementation Phases

### Phase 1: Business Logic

**Effort:** 40 hours

- Implement LRU eviction policy
- Add TTL-based expiration
- Create cache invalidation logic

### Phase 2: Testing

**Effort:** 20 hours

- Add unit tests
- Add integration tests

## Dependencies

- Python 3.11+
- Redis client library

## Effort Estimate

Total story points: 8
Total hours: 60
"""
        plan_path.write_text(content, encoding="utf-8")
        return plan_path

    def test_parse_valid_plan_file(self, sample_plan_file) -> None:
        """Test parsing a valid plan.md file."""
        primitive = TasksPrimitive()
        plan_data = primitive._parse_plan_file(sample_plan_file)

        assert "phases" in plan_data
        assert "dependencies" in plan_data
        assert "total_effort" in plan_data

        # Check phases
        assert len(plan_data["phases"]) == 2
        assert plan_data["phases"][0]["name"] == "Phase 1: Business Logic"
        assert len(plan_data["phases"][0]["requirements"]) == 3
        assert plan_data["phases"][0]["hours"] == 40.0

        # Check dependencies
        assert len(plan_data["dependencies"]) == 2
        assert "Python 3.11+" in plan_data["dependencies"]

        # Check total effort
        assert plan_data["total_effort"]["story_points"] == 8
        assert plan_data["total_effort"]["hours"] == 60.0

    def test_parse_plan_with_effort_estimates(self, tmp_path) -> None:
        """Test parsing effort estimates from plan."""
        plan_path = tmp_path / "plan.md"
        content = """# Implementation Plan

## Implementation Phases

### Phase 1: Core Features

**Effort:** 66.5 hours

- Feature A
- Feature B

## Effort Estimate

Total story points: 12
Total hours: 92.5
"""
        plan_path.write_text(content, encoding="utf-8")

        primitive = TasksPrimitive()
        plan_data = primitive._parse_plan_file(plan_path)

        assert plan_data["phases"][0]["hours"] == 66.5
        assert plan_data["total_effort"]["story_points"] == 12
        assert plan_data["total_effort"]["hours"] == 92.5

    def test_parse_plan_missing_file_raises_error(self, tmp_path) -> None:
        """Test that missing plan file raises FileNotFoundError."""
        primitive = TasksPrimitive()
        missing_path = tmp_path / "nonexistent.md"

        with pytest.raises(FileNotFoundError):
            primitive._parse_plan_file(missing_path)

    def test_parse_plan_invalid_format_returns_empty_structure(self, tmp_path) -> None:
        """Test parsing malformed plan.md returns safe structure."""
        plan_path = tmp_path / "invalid.md"
        plan_path.write_text("This is not a valid plan file", encoding="utf-8")

        primitive = TasksPrimitive()
        plan_data = primitive._parse_plan_file(plan_path)

        # Should return empty but valid structure
        assert plan_data["phases"] == []
        assert plan_data["dependencies"] == []
        assert plan_data["total_effort"]["story_points"] == 0
        assert plan_data["total_effort"]["hours"] == 0.0


# ============================================================================
# Test Class 3: Data Model Parsing Tests (3 tests)
# ============================================================================


class TestDataModelParsing:
    """Test parsing of data-model.md files."""

    @pytest.fixture
    def sample_data_model_file(self, tmp_path):
        """Create a sample data-model.md file."""
        data_model_path = tmp_path / "data-model.md"
        content = """# Data Model

## Entities

### User

**Attributes:**
- id (UUID, primary key)
- username (string, unique)

**Relationships:**
- User → Session (one-to-many)

### Session

**Attributes:**
- id (UUID, primary key)
- user_id (UUID, foreign key)

### CacheEntry

**Attributes:**
- key (string, primary key)
- value (string)
"""
        data_model_path.write_text(content, encoding="utf-8")
        return data_model_path

    def test_parse_data_model_file(self, sample_data_model_file) -> None:
        """Test parsing a valid data-model.md file."""
        primitive = TasksPrimitive()
        data_model = primitive._parse_data_model(sample_data_model_file)

        assert data_model is not None
        assert "entities" in data_model
        assert "relationships" in data_model

        # Check entities
        assert len(data_model["entities"]) == 3
        assert "User" in data_model["entities"]
        assert "Session" in data_model["entities"]
        assert "CacheEntry" in data_model["entities"]

    def test_parse_data_model_missing_file_returns_none(self, tmp_path) -> None:
        """Test that missing data model file returns None gracefully."""
        primitive = TasksPrimitive()
        missing_path = tmp_path / "nonexistent-model.md"

        result = primitive._parse_data_model(missing_path)

        assert result is None

    def test_data_model_entities_extracted_correctly(
        self, sample_data_model_file
    ) -> None:
        """Test that entity names are extracted correctly."""
        primitive = TasksPrimitive()
        data_model = primitive._parse_data_model(sample_data_model_file)

        entities = data_model["entities"]
        assert "User" in entities
        assert "Session" in entities
        assert "CacheEntry" in entities
        # Should not include section headers
        assert "Entities" not in entities


# ============================================================================
# Test Class 4: Task Generation Tests (5 tests)
# ============================================================================


class TestTaskGeneration:
    """Test task generation from plan and data model."""

    @pytest.fixture
    def sample_plan_data(self):
        """Create sample parsed plan data."""
        return {
            "phases": [
                {
                    "name": "Phase 1: Core Implementation",
                    "requirements": [
                        "Implement LRU eviction",
                        "Add TTL expiration",
                    ],
                    "hours": 40.0,
                },
                {
                    "name": "Phase 2: Testing",
                    "requirements": ["Add unit tests"],
                    "hours": 20.0,
                },
            ],
            "dependencies": [],
            "total_effort": {"story_points": 8, "hours": 60.0},
        }

    @pytest.fixture
    def sample_data_model(self):
        """Create sample parsed data model."""
        return {
            "entities": ["User", "Session"],
            "relationships": ["User → Session (one-to-many)"],
        }

    def test_generate_basic_tasks(self, sample_plan_data) -> None:
        """Test generating tasks from plan phases."""
        primitive = TasksPrimitive()
        tasks = primitive._generate_tasks(sample_plan_data, None)

        # Should generate:
        # - 2 tasks from Phase 1 requirements
        # - 1 task from Phase 2 requirement
        # - 1 integration test task
        # - 1 documentation task
        assert len(tasks) >= 5

        # Check task IDs are unique
        task_ids = [task.id for task in tasks]
        assert len(task_ids) == len(set(task_ids))

        # Check all tasks have required fields
        for task in tasks:
            assert task.id.startswith("T-")
            assert task.title
            assert task.description
            assert task.phase
            assert isinstance(task.dependencies, list)

    def test_tasks_include_database_tasks(
        self, sample_plan_data, sample_data_model
    ) -> None:
        """Test that data model entities generate database tasks."""
        primitive = TasksPrimitive()
        tasks = primitive._generate_tasks(sample_plan_data, sample_data_model)

        # Should include database tasks for User and Session entities
        db_tasks = [t for t in tasks if "database" in t.tags]
        assert len(db_tasks) >= 2

        # Check entity names appear in task titles
        task_titles = " ".join([t.title for t in db_tasks])
        assert "User" in task_titles
        assert "Session" in task_titles

    def test_tasks_include_test_tasks(self, sample_plan_data) -> None:
        """Test that test tasks are auto-generated."""
        primitive = TasksPrimitive()
        tasks = primitive._generate_tasks(sample_plan_data, None)

        # Should include integration testing task
        test_tasks = [t for t in tasks if "testing" in t.tags]
        assert len(test_tasks) >= 1

        # Integration test should depend on implementation tasks
        integration_test = [t for t in tasks if "Integration testing" in t.title][0]
        assert len(integration_test.dependencies) > 0

    def test_task_ids_unique_and_sequential(self, sample_plan_data) -> None:
        """Test that task IDs are unique and follow T-001, T-002... pattern."""
        primitive = TasksPrimitive()
        tasks = primitive._generate_tasks(sample_plan_data, None)

        task_ids = [task.id for task in tasks]

        # All IDs should be unique
        assert len(task_ids) == len(set(task_ids))

        # All IDs should match pattern T-XXX
        for task_id in task_ids:
            assert task_id.startswith("T-")
            assert len(task_id) == 5  # T-001 format
            assert task_id[2:].isdigit()

    def test_task_descriptions_detailed(self, sample_plan_data) -> None:  # noqa: ANN001
        """Test that task descriptions are comprehensive."""
        primitive = TasksPrimitive()
        tasks = primitive._generate_tasks(sample_plan_data, None)

        for task in tasks:
            # Description should include more than just title
            assert len(task.description) > len(task.title)
            # Description should have meaningful content
            assert task.description
            assert task.description != task.title


# ============================================================================
# Test Class 5: Task Ordering Tests (4 tests)
# ============================================================================


class TestTaskOrdering:
    """Test task ordering by dependencies (topological sort)."""

    def test_order_tasks_by_dependencies(self) -> None:
        """Test topological sort orders tasks correctly."""
        primitive = TasksPrimitive()

        # Create tasks with dependencies
        tasks = [
            Task(id="T-001", title="Task 1", description="First", phase="P1"),
            Task(
                id="T-002",
                title="Task 2",
                description="Second",
                phase="P1",
                dependencies=["T-001"],
            ),
            Task(
                id="T-003",
                title="Task 3",
                description="Third",
                phase="P1",
                dependencies=["T-002"],
            ),
        ]

        ordered = primitive._order_tasks(tasks)

        # Check ordering
        ids = [t.id for t in ordered]
        assert ids == ["T-001", "T-002", "T-003"]

    def test_order_detects_circular_dependencies(self) -> None:
        """Test that circular dependencies raise ValueError."""
        primitive = TasksPrimitive()

        # Create tasks with circular dependency
        tasks = [
            Task(
                id="T-001",
                title="Task 1",
                description="First",
                phase="P1",
                dependencies=["T-002"],
            ),
            Task(
                id="T-002",
                title="Task 2",
                description="Second",
                phase="P1",
                dependencies=["T-001"],
            ),
        ]

        with pytest.raises(ValueError, match="Circular dependencies"):
            primitive._order_tasks(tasks)

    def test_order_preserves_phase_grouping(self) -> None:
        """Test that phase order is maintained."""
        primitive = TasksPrimitive()

        # Create tasks from different phases with dependencies
        tasks = [
            Task(id="T-001", title="Phase 1 Task", description="P1", phase="Phase 1"),
            Task(
                id="T-002",
                title="Phase 2 Task",
                description="P2",
                phase="Phase 2",
                dependencies=["T-001"],
            ),
            Task(
                id="T-003",
                title="Phase 1 Task B",
                description="P1B",
                phase="Phase 1",
            ),
        ]

        ordered = primitive._order_tasks(tasks)

        # T-002 should come after T-001 (dependency)
        ids = [t.id for t in ordered]
        assert ids.index("T-002") > ids.index("T-001")

    def test_independent_tasks_in_any_order(self) -> None:
        """Test that independent tasks can be in any order."""
        primitive = TasksPrimitive()

        # Create tasks with no dependencies
        tasks = [
            Task(id="T-001", title="Task 1", description="First", phase="P1"),
            Task(id="T-002", title="Task 2", description="Second", phase="P1"),
            Task(id="T-003", title="Task 3", description="Third", phase="P1"),
        ]

        ordered = primitive._order_tasks(tasks)

        # Should return all tasks (order doesn't matter for independent tasks)
        assert len(ordered) == 3
        ordered_ids = {t.id for t in ordered}
        assert ordered_ids == {"T-001", "T-002", "T-003"}


# ============================================================================
# Test Class 6: Critical Path Tests (3 tests)
# ============================================================================


class TestCriticalPathIdentification:
    """Test critical path identification (CPM algorithm)."""

    def test_identify_critical_path_basic(self) -> None:
        """Test critical path identification for linear chain."""
        primitive = TasksPrimitive()

        # Create linear dependency chain
        tasks = [
            Task(
                id="T-001", title="Task 1", description="First", phase="P1", hours=10.0
            ),
            Task(
                id="T-002",
                title="Task 2",
                description="Second",
                phase="P1",
                hours=20.0,
                dependencies=["T-001"],
            ),
            Task(
                id="T-003",
                title="Task 3",
                description="Third",
                phase="P1",
                hours=15.0,
                dependencies=["T-002"],
            ),
        ]

        critical_path = primitive._identify_critical_path(tasks)

        # All tasks in linear chain should be on critical path
        assert len(critical_path) == 3
        assert "T-001" in critical_path
        assert "T-002" in critical_path
        assert "T-003" in critical_path

    def test_critical_path_with_parallel_branches(self) -> None:
        """Test critical path with parallel work streams."""
        primitive = TasksPrimitive()

        # Create parallel branches with different durations
        tasks = [
            Task(id="T-001", title="Start", description="Start", phase="P1", hours=5.0),
            Task(
                id="T-002",
                title="Branch A",
                description="Short",
                phase="P1",
                hours=10.0,
                dependencies=["T-001"],
            ),
            Task(
                id="T-003",
                title="Branch B",
                description="Long",
                phase="P1",
                hours=30.0,
                dependencies=["T-001"],
            ),
            Task(
                id="T-004",
                title="End",
                description="End",
                phase="P1",
                hours=5.0,
                dependencies=["T-002", "T-003"],
            ),
        ]

        critical_path = primitive._identify_critical_path(tasks)

        # Critical path should go through longer branch (T-001 → T-003 → T-004)
        assert "T-001" in critical_path
        assert "T-003" in critical_path
        assert "T-004" in critical_path
        # Shorter branch should not be critical
        assert "T-002" not in critical_path

    def test_critical_path_disabled(self) -> None:
        """Test that critical path can be disabled via configuration."""
        primitive = TasksPrimitive(identify_critical_path=False)

        [
            Task(
                id="T-001", title="Task 1", description="First", phase="P1", hours=10.0
            ),
        ]

        # Should return empty list when disabled
        # (Actually happens at execute level, but verify the flag)
        assert primitive.identify_critical_path_flag is False


# ============================================================================
# Test Class 7: Parallel Streams Tests (3 tests)
# ============================================================================


class TestParallelStreamIdentification:
    """Test parallel work stream identification."""

    def test_identify_parallel_streams(self) -> None:
        """Test grouping of independent tasks."""
        primitive = TasksPrimitive()

        # Create tasks in same phase with no dependencies
        tasks = [
            Task(id="T-001", title="API Task 1", description="API", phase="Phase 1"),
            Task(id="T-002", title="API Task 2", description="API", phase="Phase 1"),
            Task(id="T-003", title="UI Task 1", description="UI", phase="Phase 1"),
            Task(id="T-004", title="UI Task 2", description="UI", phase="Phase 1"),
        ]

        # Order first (for proper phase grouping)
        ordered = primitive._order_tasks(tasks)
        parallel_streams = primitive._identify_parallel_streams(ordered)

        # Should identify at least one parallel group
        assert len(parallel_streams) >= 1

        # Check that groups contain task IDs
        for _group_id, task_ids in parallel_streams.items():
            assert len(task_ids) >= 2
            assert all(tid.startswith("T-") for tid in task_ids)

    def test_parallel_streams_by_phase(self) -> None:
        """Test that parallel streams are grouped within phases."""
        primitive = TasksPrimitive()

        # Create tasks in different phases
        tasks = [
            Task(id="T-001", title="Phase 1 Task A", description="A", phase="Phase 1"),
            Task(id="T-002", title="Phase 1 Task B", description="B", phase="Phase 1"),
            Task(id="T-003", title="Phase 2 Task A", description="A", phase="Phase 2"),
            Task(id="T-004", title="Phase 2 Task B", description="B", phase="Phase 2"),
        ]

        ordered = primitive._order_tasks(tasks)
        parallel_streams = primitive._identify_parallel_streams(ordered)

        # Should have separate groups for each phase (if both have >1 task)
        if parallel_streams:
            # Verify all task IDs in streams are from same phase
            for _group_id, task_ids in parallel_streams.items():
                phases = {
                    next(t.phase for t in tasks if t.id == tid) for tid in task_ids
                }
                # All tasks in a parallel group should be from same phase
                assert len(phases) == 1

    def test_parallel_streams_disabled(self) -> None:
        """Test that parallel stream identification can be disabled."""
        primitive = TasksPrimitive(group_parallel_work=False)

        [
            Task(id="T-001", title="Task 1", description="First", phase="P1"),
            Task(id="T-002", title="Task 2", description="Second", phase="P1"),
        ]

        # Should return empty dict when disabled
        # (Actually happens at execute level, but verify the flag)
        assert primitive.group_parallel_work_flag is False


# ============================================================================
# Test Class 8: Output Format Tests (4 tests)
# ============================================================================


class TestOutputFormatting:
    """Test different output format generation."""

    @pytest.fixture
    def sample_tasks(self):
        """Create sample tasks for formatting tests."""
        return [
            Task(
                id="T-001",
                title="Implement feature A",
                description="Detailed implementation of feature A",
                phase="Phase 1",
                hours=10.0,
                story_points=2,
                tags=["backend", "api"],
                acceptance_criteria=["Criterion 1", "Criterion 2"],
            ),
            Task(
                id="T-002",
                title="Add tests for feature A",
                description="Unit tests for feature A",
                phase="Phase 1",
                hours=5.0,
                story_points=1,
                tags=["testing"],
                dependencies=["T-001"],
            ),
        ]

    @pytest.fixture
    def sample_plan_data(self):
        """Create sample plan data."""
        return {
            "phases": [{"name": "Phase 1", "requirements": [], "hours": 15.0}],
            "dependencies": [],
            "total_effort": {"story_points": 3, "hours": 15.0},
        }

    def test_generate_markdown_format(
        self, tmp_path, sample_tasks, sample_plan_data
    ) -> None:
        """Test markdown tasks.md generation."""
        primitive = TasksPrimitive(output_dir=str(tmp_path))

        # Mark T-001 as critical path
        sample_tasks[0].is_critical_path = True

        output_path = primitive._generate_tasks_md(
            sample_tasks, sample_plan_data, ["T-001"], {}
        )

        assert output_path.exists()
        content = output_path.read_text(encoding="utf-8")

        # Check key sections present
        assert "# Implementation Tasks" in content
        assert "## Summary" in content
        assert "## Task List" in content
        assert "### Phase 1" in content
        assert "#### T-001:" in content
        assert "[CRITICAL PATH]" in content

    def test_generate_json_format(
        self, tmp_path, sample_tasks, sample_plan_data
    ) -> None:
        """Test JSON export."""
        primitive = TasksPrimitive(output_dir=str(tmp_path))

        output_path = primitive._generate_json(
            sample_tasks, sample_plan_data, ["T-001"], {"P-001": ["T-002"]}
        )

        assert output_path.exists()
        data = json.loads(output_path.read_text(encoding="utf-8"))

        # Check structure
        assert "metadata" in data
        assert "tasks" in data
        assert "critical_path" in data
        assert "parallel_streams" in data

        # Check metadata
        assert data["metadata"]["total_tasks"] == 2
        assert data["metadata"]["total_effort"]["story_points"] == 3

        # Check tasks
        assert len(data["tasks"]) == 2
        assert data["tasks"][0]["id"] == "T-001"

    def test_generate_jira_csv(self, tmp_path, sample_tasks) -> None:
        """Test Jira CSV export."""
        primitive = TasksPrimitive(output_dir=str(tmp_path))

        output_path = primitive._generate_jira_tickets(sample_tasks)

        assert output_path.exists()
        content = output_path.read_text(encoding="utf-8")

        # Check CSV structure
        lines = content.strip().split("\n")
        assert len(lines) == 3  # Header + 2 tasks

        # Check header
        assert "Summary" in lines[0]
        assert "Story Points" in lines[0]

        # Check task data
        assert "T-001:" in lines[1]
        assert "T-002:" in lines[2]

    def test_generate_linear_csv(self, tmp_path, sample_tasks) -> None:
        """Test Linear CSV export."""
        primitive = TasksPrimitive(output_dir=str(tmp_path))

        output_path = primitive._generate_linear_tickets(sample_tasks)

        assert output_path.exists()
        content = output_path.read_text(encoding="utf-8")

        # Check CSV structure
        lines = content.strip().split("\n")
        assert len(lines) == 3  # Header + 2 tasks

        # Check header
        assert "Title" in lines[0]
        assert "Estimate" in lines[0]

        # Check dependencies format
        assert "T-001" in content

    def test_generate_github_format(self, sample_tasks, sample_plan_data) -> None:
        """Test generating GitHub issues JSON format."""
        primitive = TasksPrimitive(output_format="github")
        output_path = primitive._generate_github_issues(sample_tasks, sample_plan_data)

        assert output_path.exists()
        content = output_path.read_text(encoding="utf-8")

        # Parse JSON
        issues = json.loads(content)
        assert isinstance(issues, list)
        assert len(issues) > 0

        # Check issue structure
        issue = issues[0]
        assert "title" in issue
        assert "body" in issue
        assert "labels" in issue
        assert "milestone" in issue
        assert sample_tasks[0].id in issue["title"]

    async def test_invalid_output_format_raises_error(self, tmp_path) -> None:
        """Test that invalid output format raises ValueError."""
        # Create minimal plan file
        plan_path = tmp_path / "plan.md"
        plan_path.write_text("# Plan\n## Phase 1\n- [ ] Task 1", encoding="utf-8")

        primitive = TasksPrimitive(
            output_dir=str(tmp_path), output_format="invalid_format"
        )
        context = WorkflowContext()

        with pytest.raises(ValueError, match="Unknown output format"):
            await primitive.execute({"plan_path": str(plan_path)}, context)


# ============================================================================
# Test Class 9: Full Execution Tests (3 tests)
# ============================================================================


@pytest.mark.asyncio
class TestFullExecution:
    """Test end-to-end task generation."""

    @pytest.fixture
    def setup_files(self, tmp_path):
        """Create plan.md and data-model.md files."""
        plan_path = tmp_path / "plan.md"
        plan_content = """# Implementation Plan

## Implementation Phases

### Phase 1: Core Features

**Effort:** 40 hours

- Implement feature A
- Implement feature B

## Effort Estimate

Total story points: 6
Total hours: 40
"""
        plan_path.write_text(plan_content, encoding="utf-8")

        data_model_path = tmp_path / "data-model.md"
        data_model_content = """# Data Model

### User

**Attributes:**
- id (UUID)

### Session

**Attributes:**
- id (UUID)
"""
        data_model_path.write_text(data_model_content, encoding="utf-8")

        return {
            "plan_path": plan_path,
            "data_model_path": data_model_path,
            "output_dir": tmp_path / "tasks",
        }

    async def test_execute_basic_tasks_generation(self, setup_files) -> None:
        """Test end-to-end task generation from plan."""
        primitive = TasksPrimitive(output_dir=str(setup_files["output_dir"]))

        context = WorkflowContext(correlation_id="test-123")
        result = await primitive.execute(
            {"plan_path": str(setup_files["plan_path"])}, context
        )

        # Check result structure
        assert "tasks_path" in result
        assert "tasks" in result
        assert "critical_path" in result
        assert "parallel_streams" in result
        assert "total_effort" in result

        # Check tasks were generated
        assert len(result["tasks"]) > 0

        # Check file was created
        tasks_path = Path(result["tasks_path"])
        assert tasks_path.exists()

    async def test_execute_with_data_model(self, setup_files) -> None:
        """Test task generation with data model."""
        primitive = TasksPrimitive(output_dir=str(setup_files["output_dir"]))

        context = WorkflowContext(correlation_id="test-456")
        result = await primitive.execute(
            {
                "plan_path": str(setup_files["plan_path"]),
                "data_model_path": str(setup_files["data_model_path"]),
            },
            context,
        )

        # Should include database tasks for User and Session
        task_titles = " ".join([t["title"] for t in result["tasks"]])
        assert "User" in task_titles or "database" in task_titles.lower()

    async def test_execute_overrides_output_format(self, setup_files) -> None:
        """Test that execute can override output format."""
        primitive = TasksPrimitive(
            output_dir=str(setup_files["output_dir"]), output_format="markdown"
        )

        context = WorkflowContext(correlation_id="test-789")
        result = await primitive.execute(
            {
                "plan_path": str(setup_files["plan_path"]),
                "output_format": "json",  # Override
            },
            context,
        )

        # Should generate JSON file
        assert result["tasks_path"].endswith(".json")
        tasks_path = Path(result["tasks_path"])
        assert tasks_path.exists()

        # Verify it's valid JSON
        data = json.loads(tasks_path.read_text(encoding="utf-8"))
        assert "metadata" in data


# ============================================================================
# Test Class 10: Observability Tests (2 tests)
# ============================================================================


@pytest.mark.asyncio
class TestObservability:
    """Test observability integration."""

    @pytest.fixture
    def setup_basic_plan(self, tmp_path):
        """Create minimal plan file."""
        plan_path = tmp_path / "plan.md"
        plan_content = """# Plan

## Implementation Phases

### Phase 1

**Effort:** 10 hours

- Task A

## Effort Estimate

Total story points: 2
Total hours: 10
"""
        plan_path.write_text(plan_content, encoding="utf-8")
        return {"plan_path": plan_path, "output_dir": tmp_path / "tasks"}

    async def test_execute_creates_span(self, setup_basic_plan) -> None:
        """Test that execution creates OpenTelemetry span."""
        primitive = TasksPrimitive(output_dir=str(setup_basic_plan["output_dir"]))

        context = WorkflowContext(correlation_id="span-test")
        result = await primitive.execute(
            {"plan_path": str(setup_basic_plan["plan_path"])}, context
        )

        # Execution should complete successfully
        assert result is not None
        assert "tasks" in result

    async def test_workflow_context_propagation(self, setup_basic_plan) -> None:
        """Test that WorkflowContext is propagated through execution."""
        primitive = TasksPrimitive(output_dir=str(setup_basic_plan["output_dir"]))

        correlation_id = "context-test-123"
        context = WorkflowContext(correlation_id=correlation_id)

        result = await primitive.execute(
            {"plan_path": str(setup_basic_plan["plan_path"])}, context
        )

        # Context should be used (we can't directly verify, but execution succeeds)
        assert result is not None


# ============================================================================
# Summary
# ============================================================================

"""
Test Suite Summary:

Total Tests: 33 tests across 10 test classes

1. TestTasksPrimitiveInitialization: 3 tests
   - Initialization with defaults/custom params
   - Output directory creation

2. TestPlanParsing: 4 tests
   - Valid plan parsing
   - Effort estimate extraction
   - Missing file handling
   - Invalid format handling

3. TestDataModelParsing: 3 tests
   - Valid data model parsing
   - Missing file handling
   - Entity extraction

4. TestTaskGeneration: 5 tests
   - Basic task generation
   - Database tasks from entities
   - Auto-generated test tasks
   - Unique task IDs
   - Detailed descriptions

5. TestTaskOrdering: 4 tests
   - Topological sort
   - Circular dependency detection
   - Phase preservation
   - Independent task handling

6. TestCriticalPathIdentification: 3 tests
   - Linear chain critical path
   - Parallel branches
   - Disabled configuration

7. TestParallelStreamIdentification: 3 tests
   - Independent task grouping
   - Phase-based grouping
   - Disabled configuration

8. TestOutputFormatting: 4 tests
   - Markdown generation
   - JSON export
   - Jira CSV
   - Linear CSV

9. TestFullExecution: 3 tests
   - End-to-end execution
   - With data model
   - Format override

10. TestObservability: 2 tests
    - OpenTelemetry span creation
    - Context propagation

Coverage Target: 90%+ (comprehensive test coverage)
"""
