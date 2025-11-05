"""TasksPrimitive: Convert implementation plans into concrete, actionable tasks.

This primitive breaks down implementation plans into concrete tasks suitable for
task management systems (Jira, Linear, GitHub Issues, etc.).

Core functionality:
- Parse plan.md files from PlanPrimitive
- Generate concrete, actionable tasks
- Order tasks by dependencies (topological sort)
- Identify critical path (longest dependency chain)
- Group parallel work streams
- Export to multiple formats (markdown, JSON, Jira, Linear, GitHub)

Example usage:
    ```python
    from tta_dev_primitives.speckit import TasksPrimitive
    from tta_dev_primitives import WorkflowContext

    # Generate tasks from plan
    tasks_primitive = TasksPrimitive(
        output_dir="project/tasks",
        output_format="markdown"
    )

    context = WorkflowContext(correlation_id="proj-123")
    result = await tasks_primitive.execute({
        "plan_path": "project/plan.md",
        "data_model_path": "project/data-model.md"
    }, context)

    # result = {
    #     "tasks_path": "project/tasks/tasks.md",
    #     "tasks": [Task(...), Task(...), ...],
    #     "critical_path": ["T-001", "T-003", ...],
    #     "parallel_streams": {"P-001": ["T-005", "T-006"], ...},
    #     "total_effort": {"story_points": 12, "hours": 92.0}
    # }
    ```
"""

import csv
import io
import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from tta_dev_primitives import WorkflowContext
from tta_dev_primitives.observability import InstrumentedPrimitive


@dataclass
class Task:
    """Represents a single implementation task.

    Attributes:
        id: Unique task identifier (e.g., "T-001")
        title: Short task title
        description: Detailed task description
        phase: Implementation phase this task belongs to
        dependencies: List of task IDs this task depends on
        story_points: Effort estimate in story points (optional)
        hours: Effort estimate in hours (optional)
        priority: Task priority ("critical", "high", "medium", "low")
        tags: List of tags for categorization
        acceptance_criteria: List of success criteria
        is_critical_path: Whether task is on the critical path
        parallel_group: Parallel work stream ID (if applicable)
    """

    id: str
    title: str
    description: str
    phase: str
    dependencies: list[str] = field(default_factory=list)
    story_points: int | None = None
    hours: float | None = None
    priority: str = "medium"
    tags: list[str] = field(default_factory=list)
    acceptance_criteria: list[str] = field(default_factory=list)
    is_critical_path: bool = False
    parallel_group: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert task to dictionary for serialization."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "phase": self.phase,
            "dependencies": self.dependencies,
            "story_points": self.story_points,
            "hours": self.hours,
            "priority": self.priority,
            "tags": self.tags,
            "acceptance_criteria": self.acceptance_criteria,
            "is_critical_path": self.is_critical_path,
            "parallel_group": self.parallel_group,
        }


class TasksPrimitive(InstrumentedPrimitive[dict[str, Any], dict[str, Any]]):
    """Break implementation plan into concrete, ordered tasks.

    This primitive converts implementation plans into actionable tasks with:
    - Dependency-aware ordering (topological sort)
    - Critical path identification
    - Parallel work stream grouping
    - Multiple export formats (markdown, JSON, Jira, Linear, GitHub)

    Args:
        output_dir: Directory for output files (default: current directory)
        output_format: Output format ("markdown", "json", "jira", "linear", "github")
        include_effort: Include effort estimates in tasks (default: True)
        identify_critical_path: Calculate and mark critical path (default: True)
        group_parallel_work: Identify parallel work streams (default: True)

    Example:
        ```python
        primitive = TasksPrimitive(
            output_dir="project/tasks",
            output_format="markdown"
        )
        result = await primitive.execute({
            "plan_path": "project/plan.md"
        }, context)
        ```
    """

    def __init__(
        self,
        output_dir: str = ".",
        output_format: str = "markdown",
        include_effort: bool = True,
        identify_critical_path: bool = True,
        group_parallel_work: bool = True,
    ) -> None:
        """Initialize TasksPrimitive.

        Args:
            output_dir: Directory for output files
            output_format: Output format ("markdown", "json", "jira", "linear", "github")
            include_effort: Include effort estimates in tasks
            identify_critical_path: Calculate and mark critical path
            group_parallel_work: Identify parallel work streams
        """
        super().__init__(name="tasks_primitive")
        self.output_dir = Path(output_dir)
        self.output_format = output_format
        self.include_effort = include_effort
        self.identify_critical_path_flag = identify_critical_path
        self.group_parallel_work_flag = group_parallel_work

        # Create output directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def _execute_impl(
        self, input_data: dict[str, Any], context: WorkflowContext
    ) -> dict[str, Any]:
        """Execute task generation from plan.

        Args:
            input_data: Input containing:
                - plan_path: Path to plan.md file (required)
                - data_model_path: Path to data-model.md file (optional)
                - output_format: Override default output format (optional)
            context: Workflow context for tracing

        Returns:
            Dictionary containing:
                - tasks_path: Path to generated tasks file
                - tasks: List of Task objects
                - critical_path: List of task IDs on critical path
                - parallel_streams: Dict mapping group IDs to task IDs
                - total_effort: Total effort estimate (story_points, hours)

        Raises:
            FileNotFoundError: If plan_path doesn't exist
            ValueError: If circular dependencies detected
        """
        # Extract input parameters
        plan_path = Path(input_data["plan_path"])
        data_model_path = (
            Path(input_data["data_model_path"])
            if "data_model_path" in input_data
            else None
        )
        output_format = input_data.get("output_format", self.output_format)

        # Parse plan file
        plan_data = self._parse_plan_file(plan_path)

        # Parse data model if provided
        data_model_data = (
            self._parse_data_model(data_model_path) if data_model_path else None
        )

        # Generate tasks from plan
        tasks = self._generate_tasks(plan_data, data_model_data)

        # Order tasks by dependencies
        ordered_tasks = self._order_tasks(tasks)

        # Identify critical path
        critical_path = (
            self._identify_critical_path(ordered_tasks)
            if self.identify_critical_path_flag
            else []
        )

        # Mark critical path tasks
        critical_path_set = set(critical_path)
        for task in ordered_tasks:
            task.is_critical_path = task.id in critical_path_set

        # Identify parallel work streams
        parallel_streams = (
            self._identify_parallel_streams(ordered_tasks)
            if self.group_parallel_work_flag
            else {}
        )

        # Assign parallel groups to tasks
        for group_id, task_ids in parallel_streams.items():
            for task_id in task_ids:
                task = next((t for t in ordered_tasks if t.id == task_id), None)
                if task:
                    task.parallel_group = group_id

        # Calculate total effort
        total_story_points = sum(
            t.story_points for t in ordered_tasks if t.story_points
        )
        total_hours = sum(t.hours for t in ordered_tasks if t.hours)

        # Generate output based on format
        if output_format == "markdown":
            output_path = self._generate_tasks_md(
                ordered_tasks, plan_data, critical_path, parallel_streams
            )
        elif output_format == "json":
            output_path = self._generate_json(
                ordered_tasks, plan_data, critical_path, parallel_streams
            )
        elif output_format == "jira":
            output_path = self._generate_jira_tickets(ordered_tasks)
        elif output_format == "linear":
            output_path = self._generate_linear_tickets(ordered_tasks)
        elif output_format == "github":
            output_path = self._generate_github_issues(ordered_tasks, plan_data)
        else:
            raise ValueError(f"Unknown output format: {output_format}")

        # Return results
        return {
            "tasks_path": str(output_path),
            "tasks": [task.to_dict() for task in ordered_tasks],
            "critical_path": critical_path,
            "parallel_streams": parallel_streams,
            "total_effort": {
                "story_points": total_story_points,
                "hours": total_hours,
            },
        }

    def _parse_plan_file(self, plan_path: Path) -> dict[str, Any]:
        """Parse plan.md file to extract phases and requirements.

        Args:
            plan_path: Path to plan.md file

        Returns:
            Dictionary containing:
                - phases: List of phase dictionaries (name, requirements, hours)
                - dependencies: List of project dependencies
                - total_effort: Total effort estimate

        Raises:
            FileNotFoundError: If plan file doesn't exist
        """
        if not plan_path.exists():
            raise FileNotFoundError(f"Plan file not found: {plan_path}")

        content = plan_path.read_text(encoding="utf-8")
        lines = content.split("\n")

        phases = []
        dependencies = []
        total_story_points = 0
        total_hours = 0.0
        current_phase = None

        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # Parse phase headers (## Implementation Phases)
            if line.startswith("## Implementation Phases"):
                i += 1
                while i < len(lines):
                    line = lines[i].strip()
                    if line.startswith("###") and not line.startswith("####"):
                        # Phase header
                        phase_name = line.replace("###", "").strip()
                        current_phase = {
                            "name": phase_name,
                            "requirements": [],
                            "hours": 0.0,
                        }
                        phases.append(current_phase)
                    elif line.startswith("**Effort:**") and current_phase:
                        # Extract effort estimate
                        effort_str = line.replace("**Effort:**", "").strip()
                        if "hours" in effort_str:
                            try:
                                hours = float(
                                    effort_str.split("hours")[0].strip().split()[-1]
                                )
                                current_phase["hours"] = hours
                            except (ValueError, IndexError):
                                pass
                    elif line.startswith("-") and current_phase:
                        # Requirement line
                        requirement = line[1:].strip()
                        if requirement and not requirement.startswith("**"):
                            current_phase["requirements"].append(requirement)
                    elif line.startswith("## ") and not line.startswith(
                        "## Implementation"
                    ):
                        # End of phases section
                        break
                    i += 1
                continue

            # Parse dependencies section
            if line.startswith("## Dependencies"):
                i += 1
                while i < len(lines):
                    line = lines[i].strip()
                    if line.startswith("-"):
                        dependency = line[1:].strip()
                        if dependency:
                            dependencies.append(dependency)
                    elif line.startswith("## "):
                        break
                    i += 1
                continue

            # Parse effort estimate
            if line.startswith("## Effort Estimate"):
                i += 1
                while i < len(lines):
                    line = lines[i].strip()
                    if "story points" in line.lower():
                        try:
                            sp_str = line.split(":")[1].strip().split()[0]
                            total_story_points = int(sp_str)
                        except (ValueError, IndexError):
                            pass
                    elif "hours" in line.lower():
                        try:
                            hours_str = line.split(":")[1].strip().split()[0]
                            total_hours = float(hours_str)
                        except (ValueError, IndexError):
                            pass
                    elif line.startswith("## "):
                        break
                    i += 1
                continue

            i += 1

        return {
            "phases": phases,
            "dependencies": dependencies,
            "total_effort": {
                "story_points": total_story_points,
                "hours": total_hours,
            },
        }

    def _parse_data_model(self, data_model_path: Path) -> dict[str, Any] | None:
        """Parse data-model.md file to extract entities.

        Args:
            data_model_path: Path to data-model.md file

        Returns:
            Dictionary containing entities and relationships, or None if file doesn't exist
        """
        if not data_model_path.exists():
            return None

        content = data_model_path.read_text(encoding="utf-8")
        lines = content.split("\n")

        entities = []
        relationships = []
        current_entity = None

        for line in lines:
            line = line.strip()

            # Parse entity headers
            if line.startswith("### ") and not line.startswith("#### "):
                entity_name = line.replace("###", "").strip()
                if entity_name and not entity_name.startswith("Relationships"):
                    current_entity = entity_name
                    entities.append(entity_name)

            # Parse relationships
            if line.startswith("**Relationships:**") or (
                "→" in line and current_entity
            ):
                relationships.append(line)

        return {"entities": entities, "relationships": relationships}

    def _generate_tasks(
        self, plan_data: dict[str, Any], data_model_data: dict[str, Any] | None
    ) -> list[Task]:
        """Generate concrete tasks from plan and data model.

        Creates tasks for:
        - Implementation requirements (1 task per requirement)
        - Database entities (if data model provided)
        - Test coverage (unit + integration)
        - Documentation

        Args:
            plan_data: Parsed plan data from _parse_plan_file
            data_model_data: Parsed data model (optional)

        Returns:
            List of Task objects (unordered)
        """
        tasks = []
        task_counter = 1

        # Generate tasks from plan phases
        for phase in plan_data["phases"]:
            phase_name = phase["name"]
            requirements = phase["requirements"]
            phase_hours = phase["hours"]

            # Estimate effort per requirement
            req_count = len(requirements) if requirements else 1
            hours_per_req = phase_hours / req_count if req_count > 0 else 0

            for requirement in requirements:
                # Create implementation task
                task_id = f"T-{task_counter:03d}"
                task_counter += 1

                # Extract tags from requirement text
                tags = []
                req_lower = requirement.lower()
                if "api" in req_lower:
                    tags.append("backend")
                    tags.append("api")
                if "database" in req_lower or "db" in req_lower:
                    tags.append("backend")
                    tags.append("database")
                if "cache" in req_lower:
                    tags.append("backend")
                    tags.append("performance")
                if "ui" in req_lower or "frontend" in req_lower:
                    tags.append("frontend")
                if "test" in req_lower:
                    tags.append("testing")
                if "document" in req_lower:
                    tags.append("documentation")

                # Determine priority based on phase order
                phase_index = plan_data["phases"].index(phase)
                if phase_index == 0:
                    priority = "high"
                elif phase_index == len(plan_data["phases"]) - 1:
                    priority = "low"
                else:
                    priority = "medium"

                task = Task(
                    id=task_id,
                    title=requirement[:60] + "..."
                    if len(requirement) > 60
                    else requirement,
                    description=f"Implement: {requirement}\n\nPhase: {phase_name}",
                    phase=phase_name,
                    dependencies=[],
                    story_points=None,
                    hours=round(hours_per_req, 1) if hours_per_req > 0 else None,
                    priority=priority,
                    tags=tags if tags else ["implementation"],
                    acceptance_criteria=[
                        f"Implement {requirement.lower()}",
                        "Add unit tests",
                        "Code review completed",
                    ],
                )
                tasks.append(task)

        # Generate database tasks if data model provided
        if data_model_data and data_model_data.get("entities"):
            for entity in data_model_data["entities"]:
                task_id = f"T-{task_counter:03d}"
                task_counter += 1

                task = Task(
                    id=task_id,
                    title=f"Implement {entity} database model",
                    description=f"Create database model and migrations for {entity} entity.",
                    phase="Database Implementation",
                    dependencies=[],
                    story_points=1,
                    hours=6.0,
                    priority="high",
                    tags=["backend", "database", "models"],
                    acceptance_criteria=[
                        f"Create {entity} model class",
                        "Create database migration",
                        "Add model tests",
                    ],
                )
                tasks.append(task)

        # Add test task
        task_id = f"T-{task_counter:03d}"
        task_counter += 1
        all_impl_tasks = [t.id for t in tasks]
        task = Task(
            id=task_id,
            title="Integration testing",
            description="Comprehensive integration tests for all features.",
            phase="Testing",
            dependencies=all_impl_tasks,  # Depends on all implementation tasks
            story_points=2,
            hours=16.0,
            priority="high",
            tags=["testing", "integration"],
            acceptance_criteria=[
                "All features have integration tests",
                "90%+ test coverage achieved",
                "All tests passing",
            ],
        )
        tasks.append(task)

        # Add documentation task
        task_id = f"T-{task_counter:03d}"
        task = Task(
            id=task_id,
            title="Documentation",
            description="Create comprehensive documentation for all features.",
            phase="Documentation",
            dependencies=[all_impl_tasks[0]] if all_impl_tasks else [],
            story_points=1,
            hours=8.0,
            priority="medium",
            tags=["documentation"],
            acceptance_criteria=[
                "API documentation complete",
                "Usage examples added",
                "README updated",
            ],
        )
        tasks.append(task)

        return tasks

    def _order_tasks(self, tasks: list[Task]) -> list[Task]:
        """Order tasks using topological sort (Kahn's algorithm).

        Args:
            tasks: List of tasks to order

        Returns:
            Ordered list of tasks

        Raises:
            ValueError: If circular dependencies detected
        """
        # Build adjacency list and in-degree count
        task_map = {task.id: task for task in tasks}
        in_degree = {task.id: 0 for task in tasks}
        adjacency = {task.id: [] for task in tasks}

        for task in tasks:
            for dep_id in task.dependencies:
                if dep_id in task_map:
                    adjacency[dep_id].append(task.id)
                    in_degree[task.id] += 1

        # Kahn's algorithm
        queue = [task_id for task_id, degree in in_degree.items() if degree == 0]
        ordered = []

        while queue:
            # Sort queue to maintain deterministic ordering
            queue.sort()
            task_id = queue.pop(0)
            ordered.append(task_map[task_id])

            for neighbor_id in adjacency[task_id]:
                in_degree[neighbor_id] -= 1
                if in_degree[neighbor_id] == 0:
                    queue.append(neighbor_id)

        # Check for circular dependencies
        if len(ordered) != len(tasks):
            raise ValueError("Circular dependencies detected in task graph")

        return ordered

    def _identify_critical_path(self, tasks: list[Task]) -> list[str]:
        """Identify critical path using Critical Path Method (CPM).

        The critical path is the longest sequence of dependent tasks,
        determining the minimum project duration.

        Args:
            tasks: Ordered list of tasks

        Returns:
            List of task IDs on the critical path
        """
        if not tasks:
            return []

        # Calculate earliest start (ES) and earliest finish (EF) times
        es_times = {task.id: 0.0 for task in tasks}
        ef_times = {task.id: 0.0 for task in tasks}

        for task in tasks:
            # ES = max(EF of all dependencies)
            if task.dependencies:
                es_times[task.id] = max(
                    ef_times.get(dep_id, 0.0) for dep_id in task.dependencies
                )
            else:
                es_times[task.id] = 0.0

            # EF = ES + duration
            duration = task.hours if task.hours else 0.0
            ef_times[task.id] = es_times[task.id] + duration

        # Calculate latest start (LS) and latest finish (LF) times
        project_duration = max(ef_times.values()) if ef_times else 0.0
        ls_times = {task.id: 0.0 for task in tasks}
        lf_times = {task.id: project_duration for task in tasks}

        # Work backwards
        for task in reversed(tasks):
            # Find tasks that depend on this task
            dependents = [t for t in tasks if task.id in t.dependencies]

            if dependents:
                # LF = min(LS of all dependents)
                lf_times[task.id] = min(ls_times[t.id] for t in dependents)
            else:
                # No dependents, use project duration
                lf_times[task.id] = project_duration

            # LS = LF - duration
            duration = task.hours if task.hours else 0.0
            ls_times[task.id] = lf_times[task.id] - duration

        # Critical path = tasks with slack time = 0
        critical_path = []
        for task in tasks:
            slack = ls_times[task.id] - es_times[task.id]
            if abs(slack) < 0.01:  # Float comparison tolerance
                critical_path.append(task.id)

        return critical_path

    def _identify_parallel_streams(self, tasks: list[Task]) -> dict[str, list[str]]:
        """Identify groups of tasks that can be executed in parallel.

        Tasks can be parallelized if they have no shared dependencies
        and are in different phases or have different tags.

        Args:
            tasks: Ordered list of tasks

        Returns:
            Dictionary mapping parallel group IDs to lists of task IDs
        """
        if not tasks:
            return {}

        # Group tasks by phase
        phase_groups: dict[str, list[Task]] = {}
        for task in tasks:
            if task.phase not in phase_groups:
                phase_groups[task.phase] = []
            phase_groups[task.phase].append(task)

        parallel_streams = {}
        stream_counter = 1

        for _phase, phase_tasks in phase_groups.items():
            # Find tasks in this phase with no inter-dependencies
            independent_tasks = []
            for task in phase_tasks:
                # Check if task depends on other tasks in same phase
                phase_task_ids = {t.id for t in phase_tasks}
                has_phase_dependency = any(
                    dep_id in phase_task_ids for dep_id in task.dependencies
                )

                if not has_phase_dependency and len(phase_tasks) > 1:
                    independent_tasks.append(task)

            # Create parallel group if we have multiple independent tasks
            if len(independent_tasks) > 1:
                group_id = f"P-{stream_counter:03d}"
                stream_counter += 1
                parallel_streams[group_id] = [t.id for t in independent_tasks]

        return parallel_streams

    def _generate_tasks_md(
        self,
        tasks: list[Task],
        plan_data: dict[str, Any],
        critical_path: list[str],
        parallel_streams: dict[str, list[str]],
    ) -> Path:
        """Generate tasks.md markdown file.

        Args:
            tasks: Ordered list of tasks
            plan_data: Parsed plan data
            critical_path: List of critical path task IDs
            parallel_streams: Parallel work streams

        Returns:
            Path to generated tasks.md file
        """
        output_path = self.output_dir / "tasks.md"

        # Calculate totals
        total_story_points = sum(t.story_points for t in tasks if t.story_points)
        total_hours = sum(t.hours for t in tasks if t.hours)
        critical_hours = sum(
            t.hours for t in tasks if t.id in critical_path and t.hours
        )

        # Build markdown content
        lines = [
            "# Implementation Tasks\n",
            f"**Generated:** {datetime.now(UTC).strftime('%Y-%m-%d %H:%M UTC')}\n",
            f"**Total Tasks:** {len(tasks)}\n",
        ]

        if self.include_effort:
            lines.append(
                f"**Total Effort:** {total_story_points} SP ({total_hours:.1f} hours)\n"
            )

        lines.append("\n## Summary\n")
        lines.append(f"- **Total Tasks:** {len(tasks)}\n")

        if critical_path:
            lines.append(
                f"- **Critical Path:** {len(critical_path)} tasks ({critical_hours:.1f} hours)\n"
            )

        if parallel_streams:
            lines.append(
                f"- **Parallel Work Streams:** {len(parallel_streams)} groups\n"
            )

        dependency_count = sum(len(t.dependencies) for t in tasks)
        lines.append(f"- **Total Dependencies:** {dependency_count}\n")

        # Group tasks by phase
        lines.append("\n## Task List\n")
        current_phase = None

        for task in tasks:
            # Phase header
            if task.phase != current_phase:
                current_phase = task.phase
                phase_tasks = [t for t in tasks if t.phase == current_phase]
                phase_hours = sum(t.hours for t in phase_tasks if t.hours)
                lines.append(f"\n### {current_phase}")
                if self.include_effort and phase_hours > 0:
                    lines.append(f" ({phase_hours:.1f}h)")
                lines.append("\n")

            # Task header
            critical_marker = " [CRITICAL PATH]" if task.is_critical_path else ""
            lines.append(f"\n#### {task.id}: {task.title}{critical_marker}\n")

            # Task metadata
            lines.append(f"**Priority:** {task.priority.capitalize()}\n")

            if self.include_effort:
                effort_parts = []
                if task.story_points:
                    effort_parts.append(f"{task.story_points} SP")
                if task.hours:
                    effort_parts.append(f"{task.hours:.1f}h")
                if effort_parts:
                    lines.append(f"**Effort:** {' / '.join(effort_parts)}\n")

            if task.dependencies:
                deps_str = ", ".join(task.dependencies)
                lines.append(f"**Dependencies:** {deps_str}\n")
            else:
                lines.append("**Dependencies:** None\n")

            if task.tags:
                tags_str = ", ".join(task.tags)
                lines.append(f"**Tags:** {tags_str}\n")

            # Description
            lines.append(f"\n{task.description}\n")

            # Acceptance criteria
            if task.acceptance_criteria:
                lines.append("\n**Acceptance Criteria:**\n")
                for criterion in task.acceptance_criteria:
                    lines.append(f"- [ ] {criterion}\n")

            # Parallel group
            if task.parallel_group:
                lines.append(f"\n**Parallel Group:** {task.parallel_group}\n")

            lines.append("\n---\n")

        # Write to file
        output_path.write_text("".join(lines), encoding="utf-8")
        return output_path

    def _generate_json(
        self,
        tasks: list[Task],
        plan_data: dict[str, Any],
        critical_path: list[str],
        parallel_streams: dict[str, list[str]],
    ) -> Path:
        """Generate tasks.json file.

        Args:
            tasks: Ordered list of tasks
            plan_data: Parsed plan data
            critical_path: List of critical path task IDs
            parallel_streams: Parallel work streams

        Returns:
            Path to generated tasks.json file
        """
        output_path = self.output_dir / "tasks.json"

        # Calculate totals
        total_story_points = sum(t.story_points for t in tasks if t.story_points)
        total_hours = sum(t.hours for t in tasks if t.hours)

        # Build JSON structure
        data = {
            "metadata": {
                "generated_at": datetime.now(UTC).isoformat(),
                "total_tasks": len(tasks),
                "total_effort": {
                    "story_points": total_story_points,
                    "hours": total_hours,
                },
            },
            "tasks": [task.to_dict() for task in tasks],
            "critical_path": critical_path,
            "parallel_streams": parallel_streams,
        }

        # Write to file
        output_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return output_path

    def _generate_jira_tickets(self, tasks: list[Task]) -> Path:
        """Generate Jira import CSV file.

        Args:
            tasks: Ordered list of tasks

        Returns:
            Path to generated CSV file
        """
        output_path = self.output_dir / "tasks_jira.csv"

        # Build CSV data
        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow(
            [
                "Summary",
                "Description",
                "Issue Type",
                "Priority",
                "Story Points",
                "Labels",
                "Linked Issues",
            ]
        )

        # Tasks
        for task in tasks:
            summary = f"{task.id}: {task.title}"
            description = task.description
            issue_type = "Story"
            priority = task.priority.capitalize()
            story_points = task.story_points if task.story_points else ""
            labels = ",".join(task.tags) if task.tags else ""

            # Format dependencies as "blocks" relationships
            linked = ""
            if task.dependencies:
                linked = " AND ".join([f"blocks {dep}" for dep in task.dependencies])

            writer.writerow(
                [
                    summary,
                    description,
                    issue_type,
                    priority,
                    story_points,
                    labels,
                    linked,
                ]
            )

        # Write to file
        output_path.write_text(output.getvalue(), encoding="utf-8")
        return output_path

    def _generate_linear_tickets(self, tasks: list[Task]) -> Path:
        """Generate Linear import CSV file.

        Args:
            tasks: Ordered list of tasks

        Returns:
            Path to generated CSV file
        """
        output_path = self.output_dir / "tasks_linear.csv"

        # Build CSV data
        output = io.StringIO()
        writer = csv.writer(output)

        # Header (Linear format)
        writer.writerow(
            [
                "Title",
                "Description",
                "Priority",
                "Estimate",
                "Labels",
                "Blocked by",
            ]
        )

        # Tasks
        for task in tasks:
            title = f"{task.id}: {task.title}"
            description = task.description

            # Linear priority: 0=None, 1=Urgent, 2=High, 3=Medium, 4=Low
            priority_map = {"critical": "1", "high": "2", "medium": "3", "low": "4"}
            priority = priority_map.get(task.priority, "3")

            estimate = task.hours if task.hours else ""
            labels = ",".join(task.tags) if task.tags else ""
            blocked_by = ",".join(task.dependencies) if task.dependencies else ""

            writer.writerow(
                [
                    title,
                    description,
                    priority,
                    estimate,
                    labels,
                    blocked_by,
                ]
            )

        # Write to file
        output_path.write_text(output.getvalue(), encoding="utf-8")
        return output_path

    def _generate_github_issues(
        self, tasks: list[Task], plan_data: dict[str, Any]
    ) -> Path:
        """Generate GitHub Issues JSON file.

        Args:
            tasks: Ordered list of tasks
            plan_data: Parsed plan data

        Returns:
            Path to generated JSON file
        """
        output_path = self.output_dir / "tasks_github.json"

        # Build issues array
        issues = []
        for task in tasks:
            # Build issue body
            body_parts = [task.description]

            if task.acceptance_criteria:
                body_parts.append("\n## Acceptance Criteria\n")
                for criterion in task.acceptance_criteria:
                    body_parts.append(f"- [ ] {criterion}")

            if task.dependencies:
                body_parts.append("\n## Dependencies\n")
                for dep_id in task.dependencies:
                    body_parts.append(f"- Depends on #{dep_id}")

            if self.include_effort and (task.story_points or task.hours):
                body_parts.append("\n## Effort Estimate\n")
                if task.story_points:
                    body_parts.append(f"- Story Points: {task.story_points}")
                if task.hours:
                    body_parts.append(f"- Hours: {task.hours:.1f}")

            body = "\n".join(body_parts)

            # Build labels
            labels = list(task.tags) if task.tags else []
            if task.is_critical_path:
                labels.append("critical-path")
            labels.append(task.priority)

            # Create issue
            issue = {
                "title": f"{task.id}: {task.title}",
                "body": body,
                "labels": labels,
                "milestone": task.phase,
            }
            issues.append(issue)

        # Write to file
        output_path.write_text(json.dumps(issues, indent=2), encoding="utf-8")
        return output_path
