# Speckit Days 8-9: TasksPrimitive Implementation Plan

**Status:** Planning Phase
**Estimated Effort:** 12-16 hours
**Target Completion:** November 5-6, 2025
**Target Coverage:** 90%+ (30-35 tests)

---

## 🎯 Objective

Implement **TasksPrimitive** to convert implementation plans into concrete, actionable tasks suitable for task management systems (Jira, Linear, GitHub Issues, etc.).

**Core Flow:**
```
plan.md + data-model.md
    ↓
TasksPrimitive
    ↓
tasks.md (ordered, dependency-aware, ticket-ready)
```

---

## 📋 Requirements

### Input Format

**Required:**
- `plan_path: str` - Path to plan.md file (from PlanPrimitive)

**Optional:**
- `data_model_path: str | None` - Path to data-model.md (if available)
- `output_format: str` - Output format ("markdown" | "json" | "jira" | "linear" | "github")
- `ticket_template: dict | None` - Custom ticket template
- `include_effort: bool` - Include effort estimates in tasks (default: True)
- `identify_critical_path: bool` - Highlight critical path tasks (default: True)
- `group_parallel_work: bool` - Identify parallel work streams (default: True)

### Output Format

**Returns:**
```python
{
    "tasks_path": str,                          # Path to tasks.md (or .json)
    "tasks": list[Task],                        # List of Task objects
    "critical_path": list[str],                 # Task IDs on critical path
    "parallel_streams": dict[str, list[str]],   # Parallelizable task groups
    "total_effort": {                           # Total effort estimate
        "story_points": int,
        "hours": float
    }
}
```

**Task Object:**
```python
@dataclass
class Task:
    id: str                          # Unique task ID (e.g., "T-001")
    title: str                       # Task title
    description: str                 # Detailed description
    phase: str                       # Implementation phase
    dependencies: list[str]          # Task IDs this depends on
    story_points: int | None         # Effort estimate (SP)
    hours: float | None              # Effort estimate (hours)
    priority: str                    # "critical", "high", "medium", "low"
    tags: list[str]                  # Tags (e.g., ["backend", "api", "database"])
    acceptance_criteria: list[str]   # Success criteria
    is_critical_path: bool           # On critical path?
    parallel_group: str | None       # Parallel work stream ID
```

---

## 🏗️ Technical Design

### Class Structure

```python
from tta_dev_primitives.observability import InstrumentedPrimitive
from dataclasses import dataclass
from typing import Any
from pathlib import Path

@dataclass
class Task:
    """Represents a single implementation task."""
    id: str
    title: str
    description: str
    phase: str
    dependencies: list[str]
    story_points: int | None = None
    hours: float | None = None
    priority: str = "medium"
    tags: list[str] = field(default_factory=list)
    acceptance_criteria: list[str] = field(default_factory=list)
    is_critical_path: bool = False
    parallel_group: str | None = None

class TasksPrimitive(InstrumentedPrimitive[dict[str, Any], dict[str, Any]]):
    """Break implementation plan into concrete, ordered tasks."""

    def __init__(
        self,
        output_dir: str = ".",
        output_format: str = "markdown",
        include_effort: bool = True,
        identify_critical_path: bool = True,
        group_parallel_work: bool = True,
    ):
        super().__init__(name="tasks_primitive")
        self.output_dir = Path(output_dir)
        self.output_format = output_format
        self.include_effort = include_effort
        self.identify_critical_path = identify_critical_path
        self.group_parallel_work = group_parallel_work
        self.output_dir.mkdir(parents=True, exist_ok=True)
```

### Key Methods

#### 1. `_parse_plan_file(plan_path: Path) -> dict[str, Any]`
**Purpose:** Extract phases, requirements, and effort from plan.md

**Logic:**
- Read plan.md file
- Extract sections: Implementation Phases, Dependencies, Effort Estimate
- Parse each phase's requirements
- Return structured plan data

**Returns:**
```python
{
    "phases": [
        {
            "name": "Business Logic Implementation",
            "requirements": ["Implement LRU eviction", "Add TTL expiration"],
            "hours": 66.0
        },
        ...
    ],
    "dependencies": [...],
    "total_effort": {"story_points": 12, "hours": 92.0}
}
```

#### 2. `_parse_data_model(data_model_path: Path) -> dict[str, Any]`
**Purpose:** Extract entities and relationships from data-model.md

**Logic:**
- Read data-model.md if exists
- Parse entity definitions
- Extract relationships
- Return structured data model

**Returns:**
```python
{
    "entities": ["User", "CacheEntry", "Session"],
    "relationships": [
        {"from": "User", "to": "Session", "type": "one-to-many"}
    ]
}
```

#### 3. `_generate_tasks(plan: dict, data_model: dict) -> list[Task]`
**Purpose:** Break phases into concrete tasks

**Logic:**
- Iterate through plan phases
- For each requirement, create 1-3 tasks
- Generate unique task IDs (T-001, T-002, ...)
- Add phase context to each task
- Include data model tasks if entities present
- Add test tasks for each feature

**Task Generation Rules:**
- **Implementation tasks:** One per major requirement
- **Database tasks:** One per entity (if data model exists)
- **API tasks:** One per endpoint mentioned
- **Test tasks:** Unit + integration for each feature
- **Documentation tasks:** One per major feature

**Example:**
```python
Requirement: "Implement LRU eviction policy"
→ Tasks:
  - T-001: "Implement LRU data structure"
  - T-002: "Add eviction logic on cache full"
  - T-003: "Add unit tests for LRU eviction"
```

#### 4. `_order_tasks(tasks: list[Task]) -> list[Task]`
**Purpose:** Order tasks by dependencies

**Logic:**
- Build dependency graph
- Perform topological sort
- Detect circular dependencies (error if found)
- Return ordered task list

**Algorithm:** Kahn's algorithm (topological sort)

#### 5. `_identify_critical_path(tasks: list[Task]) -> list[str]`
**Purpose:** Find longest dependency chain (critical path)

**Logic:**
- Build dependency graph with effort estimates
- Calculate earliest start time for each task
- Calculate latest finish time for each task
- Tasks with slack time = 0 are on critical path
- Return list of critical task IDs

**Critical Path Definition:** Sequence of tasks that determines minimum project duration

#### 6. `_identify_parallel_streams(tasks: list[Task]) -> dict[str, list[str]]`
**Purpose:** Group tasks that can be done in parallel

**Logic:**
- Identify tasks with no shared dependencies
- Group by common characteristics (phase, tags)
- Assign parallel group IDs (P-001, P-002, ...)
- Return mapping of group ID to task IDs

**Example:**
```python
{
    "P-001": ["T-005", "T-006", "T-007"],  # Backend API tasks
    "P-002": ["T-010", "T-011"],           # Frontend tasks
}
```

#### 7. `_generate_tasks_md(tasks: list[Task], ...) -> str`
**Purpose:** Create tasks.md markdown file

**Structure:**
```markdown
# Implementation Tasks

**Project:** [Feature Name]
**Generated:** 2025-11-04
**Total Tasks:** 15
**Total Effort:** 12 SP (92 hours)

## Summary

- Critical Path: 8 tasks (60 hours)
- Parallel Work Streams: 3 groups
- Dependencies: 12 task dependencies

## Task List

### Phase 1: Business Logic Implementation (66h)

#### T-001: Implement LRU data structure [CRITICAL PATH]
**Priority:** High
**Effort:** 3 SP (21h)
**Dependencies:** None
**Tags:** backend, data-structure, core

**Description:**
Implement least-recently-used (LRU) cache eviction policy...

**Acceptance Criteria:**
- [ ] LRU data structure implemented
- [ ] O(1) get and put operations
- [ ] Proper eviction on capacity reached
- [ ] Thread-safe implementation

**Parallel Group:** None (sequential)

---

#### T-002: Add TTL-based expiration
**Priority:** High
**Effort:** 2 SP (15h)
**Dependencies:** T-001
**Tags:** backend, time-based, core

...
```

#### 8. `_generate_json(tasks: list[Task], ...) -> str`
**Purpose:** Export as JSON for API consumption

**Structure:**
```json
{
  "metadata": {
    "project": "Feature Name",
    "generated_at": "2025-11-04T10:30:00Z",
    "total_tasks": 15,
    "total_effort": {"story_points": 12, "hours": 92.0}
  },
  "tasks": [
    {
      "id": "T-001",
      "title": "Implement LRU data structure",
      "description": "...",
      "phase": "Business Logic Implementation",
      "dependencies": [],
      "story_points": 3,
      "hours": 21.0,
      "priority": "high",
      "tags": ["backend", "data-structure", "core"],
      "acceptance_criteria": [...],
      "is_critical_path": true,
      "parallel_group": null
    },
    ...
  ],
  "critical_path": ["T-001", "T-003", ...],
  "parallel_streams": {
    "P-001": ["T-005", "T-006"]
  }
}
```

#### 9. `_generate_jira_tickets(tasks: list[Task], ...) -> str`
**Purpose:** Format for Jira import (CSV)

**Structure:**
```csv
Summary,Description,Issue Type,Priority,Story Points,Labels,Linked Issues
"T-001: Implement LRU data structure","Detailed description...","Story","High",3,"backend,data-structure,core","blocks T-002"
```

#### 10. `_generate_linear_tickets(tasks: list[Task], ...) -> str`
**Purpose:** Format for Linear import (CSV)

**Structure:**
```csv
Title,Description,Priority,Estimate,Labels,Blocked by
"T-001: Implement LRU data structure","...","1",21,"backend,data-structure,core",""
```

#### 11. `_generate_github_issues(tasks: list[Task], ...) -> str`
**Purpose:** Format for GitHub Issues (JSON)

**Structure:**
```json
[
  {
    "title": "T-001: Implement LRU data structure",
    "body": "...",
    "labels": ["backend", "data-structure", "core", "critical-path"],
    "milestone": "Phase 1: Business Logic"
  }
]
```

---

## 🧪 Test Plan

### Test Coverage Target: 90%+ (30-35 tests)

### Test File: `test_tasks_primitive.py`

#### Test Class 1: TestTasksPrimitiveInitialization (3 tests)
- `test_init_with_defaults` - Default configuration
- `test_init_with_custom_parameters` - Custom output dir/format/options
- `test_creates_output_directory` - Auto-creates missing directories

#### Test Class 2: TestPlanParsing (4 tests)
- `test_parse_valid_plan_file` - Extracts phases and requirements
- `test_parse_plan_with_effort` - Includes effort estimates
- `test_parse_plan_missing_file_raises_error` - FileNotFoundError
- `test_parse_plan_invalid_format` - Handles malformed plan.md

#### Test Class 3: TestDataModelParsing (3 tests)
- `test_parse_data_model_file` - Extracts entities and relationships
- `test_parse_data_model_missing_file_returns_none` - Graceful handling
- `test_data_model_entities_extracted` - Entity list correct

#### Test Class 4: TestTaskGeneration (5 tests)
- `test_generate_basic_tasks` - Creates tasks from phases
- `test_tasks_include_database_tasks` - Data model entities → tasks
- `test_tasks_include_test_tasks` - Test tasks auto-generated
- `test_task_ids_unique` - No duplicate task IDs
- `test_task_descriptions_detailed` - Descriptions are comprehensive

#### Test Class 5: TestTaskOrdering (4 tests)
- `test_order_tasks_by_dependencies` - Topological sort works
- `test_order_detects_circular_dependencies` - Raises error on cycle
- `test_order_preserves_phase_grouping` - Phase order maintained
- `test_independent_tasks_in_any_order` - No fixed order for independent tasks

#### Test Class 6: TestCriticalPathIdentification (3 tests)
- `test_identify_critical_path_basic` - Finds longest path
- `test_critical_path_with_effort` - Uses effort estimates
- `test_critical_path_disabled` - Respects configuration flag

#### Test Class 7: TestParallelStreamIdentification (3 tests)
- `test_identify_parallel_streams` - Groups independent tasks
- `test_parallel_streams_by_phase` - Groups by phase
- `test_parallel_streams_disabled` - Respects configuration flag

#### Test Class 8: TestTicketGeneration (4 tests)
- `test_generate_markdown_tasks` - tasks.md creation
- `test_generate_json_format` - JSON export
- `test_generate_jira_csv` - Jira import format
- `test_generate_linear_csv` - Linear import format

#### Test Class 9: TestOutputFormatting (3 tests)
- `test_markdown_content_structure` - Proper sections in tasks.md
- `test_json_schema_valid` - Valid JSON structure
- `test_csv_format_parseable` - CSV can be parsed

#### Test Class 10: TestFullExecution (3 tests)
- `test_execute_basic_tasks_generation` - End-to-end execution
- `test_execute_with_data_model` - Includes entity tasks
- `test_execute_overrides_output_format` - Custom format works

#### Test Class 11: TestObservability (2 tests)
- `test_execute_creates_span` - OpenTelemetry span creation
- `test_workflow_context_propagation` - Context propagates

---

## 📚 Examples Plan

### Example File: `speckit_tasks_example.py` (5 examples)

#### Example 1: Basic Task Generation
**Purpose:** Generate tasks.md from simple plan.md

**Input:**
- plan.md (LRU cache feature with 3 phases)
- No data model

**Output:**
```
✅ Tasks generated successfully!
   Tasks file: examples/tasks_output/tasks.md
   Total tasks: 12
   Critical path: 6 tasks (48 hours)
   Parallel streams: 2 groups

📋 Task Breakdown:
   - Implementation: 8 tasks (66h)
   - Testing: 3 tasks (16h)
   - Documentation: 1 task (10h)
```

#### Example 2: Task Ordering with Dependencies
**Purpose:** Demonstrate dependency resolution and ordering

**Input:**
- Complex plan with inter-phase dependencies
- Show how tasks are ordered

**Output:**
```
✅ Tasks ordered by dependencies!

📊 Execution Order:
   1. T-001: Database schema (no deps) → 8h
   2. T-002: API endpoints (needs T-001) → 12h
   3. T-003: Business logic (needs T-001, T-002) → 20h
   ...

⚠️ Critical Path (5 tasks, 48h):
   T-001 → T-002 → T-003 → T-008 → T-012
```

#### Example 3: Multiple Output Formats
**Purpose:** Export to markdown, JSON, Jira, Linear

**Output:**
```
✅ Generated in multiple formats:
   - Markdown: examples/tasks_output/tasks.md
   - JSON: examples/tasks_output/tasks.json
   - Jira CSV: examples/tasks_output/tasks_jira.csv
   - Linear CSV: examples/tasks_output/tasks_linear.csv
   - GitHub JSON: examples/tasks_output/tasks_github.json

📦 Ready for import into:
   - Jira: Use CSV import
   - Linear: Use CSV import
   - GitHub: Use gh CLI or API
```

#### Example 4: Complete Workflow (Specify → Clarify → Validate → Plan → Tasks)
**Purpose:** End-to-end Speckit demonstration

**Workflow:**
1. SpecifyPrimitive: Requirement → spec.md
2. ClarifyPrimitive: Refine spec
3. ValidationGatePrimitive: Approve spec
4. PlanPrimitive: spec.md → plan.md
5. **TasksPrimitive: plan.md → tasks.md**

**Output:**
```
🎯 Complete Speckit workflow finished!
   Requirement → Spec → Clarify → Validate → Plan → Tasks

📁 Generated artifacts:
   - spec.md: Detailed specification (80% coverage)
   - plan.md: Implementation plan (3 phases, 12 SP)
   - tasks.md: Concrete tasks (15 tasks, ordered)

✅ Ready for implementation!
```

#### Example 5: Parallel Work Streams
**Purpose:** Identify tasks that can be done concurrently

**Output:**
```
✅ Parallel work streams identified!

🔀 Stream 1 (Backend): 4 tasks (can run in parallel)
   - T-002: User authentication
   - T-003: Session management
   - T-004: Cache implementation
   - T-005: Rate limiting

🔀 Stream 2 (Frontend): 3 tasks (can run in parallel)
   - T-009: Login UI
   - T-010: Dashboard UI
   - T-011: Settings UI

🔀 Stream 3 (Testing): 2 tasks (can run in parallel)
   - T-013: Unit tests
   - T-014: Integration tests

💡 Benefit: 30% time reduction with parallel execution
```

---

## 📅 Implementation Timeline

### Phase 1: Planning (1-2 hours) - CURRENT
- [x] Create this planning document
- [ ] Review with stakeholders (if applicable)
- [ ] Finalize technical approach

### Phase 2: Core Implementation (4-6 hours)
- [ ] Create `tasks_primitive.py` skeleton
- [ ] Implement `_parse_plan_file()`
- [ ] Implement `_parse_data_model()`
- [ ] Implement `_generate_tasks()`
- [ ] Implement `_order_tasks()` (topological sort)
- [ ] Implement `_identify_critical_path()`
- [ ] Implement `_identify_parallel_streams()`
- [ ] Implement `_generate_tasks_md()`

### Phase 3: Export Formats (1-2 hours)
- [ ] Implement `_generate_json()`
- [ ] Implement `_generate_jira_tickets()`
- [ ] Implement `_generate_linear_tickets()`
- [ ] Implement `_generate_github_issues()`

### Phase 4: Testing (3-4 hours)
- [ ] Create `test_tasks_primitive.py` skeleton
- [ ] Write initialization tests (3)
- [ ] Write parsing tests (7)
- [ ] Write task generation tests (5)
- [ ] Write ordering tests (4)
- [ ] Write critical path tests (3)
- [ ] Write parallel streams tests (3)
- [ ] Write output format tests (7)
- [ ] Write observability tests (2)
- [ ] Achieve 90%+ coverage

### Phase 5: Examples (2-3 hours)
- [ ] Create `speckit_tasks_example.py` skeleton
- [ ] Implement Example 1 (basic)
- [ ] Implement Example 2 (dependencies)
- [ ] Implement Example 3 (multiple formats)
- [ ] Implement Example 4 (complete workflow)
- [ ] Implement Example 5 (parallel streams)
- [ ] Verify all examples run successfully

### Phase 6: Documentation (2-3 hours)
- [ ] Create `SPECKIT_DAY8_9_COMPLETE.md`
- [ ] Update journal with completion status
- [ ] Update package exports (`__init__.py`)
- [ ] Run full test suite verification
- [ ] Fix any linting/test issues

---

## 🎯 Success Criteria

### Must Have
- [ ] TasksPrimitive implemented (~500-700 lines)
- [ ] 90%+ test coverage achieved
- [ ] 30-35 comprehensive tests passing
- [ ] 5 working examples demonstrating all features
- [ ] Zero linting errors
- [ ] Full integration with PlanPrimitive verified

### Should Have
- [ ] Multiple output formats working (markdown, JSON, Jira, Linear, GitHub)
- [ ] Critical path identification accurate
- [ ] Parallel work streams identified correctly
- [ ] Task ordering handles complex dependencies
- [ ] Effort estimates propagated from plan

### Nice to Have
- [ ] Custom ticket templates support
- [ ] Advanced dependency visualization
- [ ] Time-based scheduling (earliest/latest start dates)
- [ ] Resource allocation hints

---

## 🔗 Integration Points

### Inputs (From Previous Primitives)
- **PlanPrimitive** → `plan.md` file
  - Contains: Phases, requirements, effort estimates, dependencies
  - Location: Specified by `plan_path` parameter
- **PlanPrimitive** → `data-model.md` file (optional)
  - Contains: Entities, attributes, relationships
  - Location: Specified by `data_model_path` parameter

### Outputs (For Downstream Consumers)
- **Task Management Systems** → Import tasks
  - Jira: CSV import
  - Linear: CSV import
  - GitHub Issues: gh CLI or API
  - Custom: JSON consumption
- **Project Planning Tools** → Gantt charts, timelines
  - Critical path for scheduling
  - Parallel streams for resource allocation
- **Development Teams** → Implementation guide
  - tasks.md as development checklist
  - Ordered by dependencies for efficient execution

---

## 🚨 Risk Assessment

### High Risk
- **Dependency Cycles:** Need robust circular dependency detection
  - Mitigation: Use Kahn's algorithm with cycle detection
- **Complex Parsing:** plan.md format may vary
  - Mitigation: Flexible parser with error handling

### Medium Risk
- **Effort Estimation:** Propagating from plan may be imprecise
  - Mitigation: Allow manual override per task
- **Critical Path Calculation:** Algorithm complexity
  - Mitigation: Use standard CPM (Critical Path Method) algorithm

### Low Risk
- **Output Formatting:** Different systems have different formats
  - Mitigation: Template-based generation with defaults

---

## 📝 Notes

### Assumptions
- plan.md follows format from PlanPrimitive
- Task breakdown is 1-3 tasks per requirement
- Dependencies are explicitly stated or inferred from phase order
- Effort estimates are optional but recommended

### Design Decisions
- **Task ID Format:** "T-001", "T-002", ... (3-digit padding)
- **Parallel Group Format:** "P-001", "P-002", ... (for clarity)
- **Default Output:** Markdown (tasks.md) - most human-readable
- **Dependency Format:** List of task IDs (simple reference)

### Future Enhancements (Post Day 8-9)
- [ ] Gantt chart generation (visual timeline)
- [ ] Resource assignment recommendations
- [ ] Time-based scheduling (calendar dates)
- [ ] Task templates for common patterns
- [ ] Integration with actual task management APIs (not just export)
- [ ] Task progress tracking (% complete)
- [ ] Burndown chart data generation

---

## 🔍 Reference Materials

### Algorithms to Implement
1. **Topological Sort (Kahn's Algorithm):**
   - Used for: Task ordering by dependencies
   - Complexity: O(V + E) where V=tasks, E=dependencies
   - Handles: Cycle detection

2. **Critical Path Method (CPM):**
   - Used for: Identifying critical path
   - Steps: Calculate ES/LS/EF/LF times, find slack=0
   - Complexity: O(V + E)

3. **Parallel Stream Detection:**
   - Used for: Grouping independent tasks
   - Approach: Find tasks with no shared dependencies
   - Complexity: O(V²) worst case

### External Format References
- **Jira CSV Format:** [Atlassian CSV Import Docs]
- **Linear CSV Format:** [Linear Import Guide]
- **GitHub Issues JSON:** [GitHub API - Issues]

---

## ✅ Pre-Implementation Checklist

- [x] Planning document created
- [x] Technical design approved
- [x] Test plan defined
- [x] Examples planned
- [x] Success criteria established
- [ ] Review completed (if applicable)
- [ ] Ready to begin implementation

---

**Document Version:** 1.0
**Created:** November 4, 2025
**Author:** GitHub Copilot (Autonomous Agent)
**Status:** Planning Complete - Ready for Implementation
**Next:** Begin Phase 2 (Core Implementation)
