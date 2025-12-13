# Speckit Days 6-7: PlanPrimitive Implementation Plan

**Goal:** Generate implementation plans from validated specifications

**Timeline:** 2 days (Days 6-7 of 25-day Speckit implementation)

**Status:** 🚧 Planning

---

## Overview

**PlanPrimitive** converts validated specification files into structured implementation plans. It breaks down requirements into ordered phases, identifies data models, documents architecture decisions, and estimates effort.

### Inputs

```python
{
    "spec_path": "path/to/validated.spec.md",
    "output_dir": "path/to/output/",
    "architecture_context": {  # Optional
        "existing_patterns": [...],
        "tech_stack": [...],
        "constraints": [...]
    },
    "team_capacity": {  # Optional
        "available_devs": 3,
        "sprint_length_days": 14
    }
}
```

### Outputs

```python
{
    "plan_path": "path/to/plan.md",
    "data_model_path": "path/to/data-model.md",
    "architecture_decisions": [
        {
            "decision": "Use PostgreSQL for relational data",
            "rationale": "Complex relationships between entities",
            "alternatives": ["MongoDB", "DynamoDB"],
            "tradeoffs": "..."
        }
    ],
    "effort_estimate": {
        "story_points": 21,
        "hours": 168,
        "confidence": 0.7
    },
    "dependencies": [
        {"type": "external", "name": "Auth service", "blocker": true},
        {"type": "internal", "name": "User model", "blocker": false}
    ],
    "phases": [
        {
            "number": 1,
            "name": "Data Model Setup",
            "tasks_count": 5,
            "estimated_hours": 40
        }
    ]
}
```

---

## Implementation Strategy

### Phase 1: Core Planning (Day 6)

**Goal:** Basic plan generation from validated specs

**Tasks:**

1. **Create PlanPrimitive class** (2 hours)
   - Extend `InstrumentedPrimitive[dict, dict]`
   - Define input/output schemas
   - Implement `_execute_impl()` skeleton
   - Add initialization with config

2. **Parse spec file** (2 hours)
   - Read validated spec.md
   - Extract sections (Features, Requirements, Acceptance Criteria)
   - Parse [CLARIFY] markers (should be minimal after validation)
   - Extract technical requirements

3. **Generate implementation phases** (3 hours)
   - Break requirements into logical phases
   - Order phases by dependencies
   - Assign requirements to phases
   - Generate phase descriptions

4. **Create plan.md output** (2 hours)
   - Template-based generation
   - Include phase breakdown
   - Add acceptance criteria per phase
   - Format with markdown headers

5. **Basic tests** (3 hours)
   - Test initialization
   - Test spec parsing
   - Test phase generation
   - Test plan.md creation
   - Target: 80% coverage

**Deliverables (Day 6):**
- ✅ PlanPrimitive implementation (basic)
- ✅ plan.md generation working
- ✅ Basic test suite (80% coverage)

### Phase 2: Data Models & Architecture (Day 7)

**Goal:** Add data model extraction and architecture decisions

**Tasks:**

1. **Data model extraction** (3 hours)
   - Identify entities from requirements
   - Extract attributes and types
   - Identify relationships
   - Generate data-model.md

2. **Architecture decisions** (2 hours)
   - Identify technical choices (database, cache, queue, etc.)
   - Generate decision records
   - Document rationale and tradeoffs
   - Add to plan output

3. **Effort estimation** (2 hours)
   - Count requirements
   - Estimate complexity per requirement
   - Generate story points
   - Add confidence score

4. **Dependency identification** (2 hours)
   - Identify external dependencies
   - Identify internal dependencies
   - Flag blockers
   - Add to plan output

5. **Comprehensive tests** (3 hours)
   - Test data model extraction
   - Test architecture decisions
   - Test effort estimation
   - Test dependency identification
   - Target: 90%+ coverage

6. **Examples** (2 hours)
   - Basic plan generation
   - Plan with data models
   - Plan with architecture decisions
   - Complete workflow example (Specify → Clarify → Validate → Plan)

**Deliverables (Day 7):**
- ✅ Data model extraction working
- ✅ Architecture decisions documented
- ✅ Effort estimation functional
- ✅ Dependency identification working
- ✅ Comprehensive test suite (90%+ coverage)
- ✅ Working examples (4 scenarios)

---

## Technical Design

### Class Structure

```python
from tta_dev_primitives import InstrumentedPrimitive, WorkflowContext
from dataclasses import dataclass
from pathlib import Path

@dataclass
class Phase:
    """Implementation phase."""
    number: int
    name: str
    description: str
    requirements: list[str]
    estimated_hours: float
    dependencies: list[str] = None

@dataclass
class ArchitectureDecision:
    """Architecture decision record."""
    decision: str
    rationale: str
    alternatives: list[str]
    tradeoffs: str

@dataclass
class DataModel:
    """Data model entity."""
    name: str
    attributes: dict[str, str]  # name -> type
    relationships: list[str]
    description: str

class PlanPrimitive(InstrumentedPrimitive[dict, dict]):
    """Generate implementation plans from validated specs."""

    def __init__(
        self,
        output_dir: str = "./output",
        max_phases: int = 5,
        include_data_models: bool = True,
        include_architecture_decisions: bool = True,
        estimate_effort: bool = True
    ):
        super().__init__(name="plan_primitive")
        self.output_dir = Path(output_dir)
        self.max_phases = max_phases
        self.include_data_models = include_data_models
        self.include_architecture_decisions = include_architecture_decisions
        self.estimate_effort = estimate_effort

    async def _execute_impl(
        self,
        input_data: dict,
        context: WorkflowContext
    ) -> dict:
        """Generate implementation plan from validated spec."""

        # 1. Parse spec file
        spec_content = await self._parse_spec(input_data["spec_path"])

        # 2. Generate phases
        phases = await self._generate_phases(spec_content)

        # 3. Extract data models (if enabled)
        data_models = []
        if self.include_data_models:
            data_models = await self._extract_data_models(spec_content)

        # 4. Generate architecture decisions (if enabled)
        arch_decisions = []
        if self.include_architecture_decisions:
            arch_decisions = await self._generate_architecture_decisions(
                spec_content,
                input_data.get("architecture_context", {})
            )

        # 5. Estimate effort (if enabled)
        effort = None
        if self.estimate_effort:
            effort = await self._estimate_effort(phases, data_models)

        # 6. Identify dependencies
        dependencies = await self._identify_dependencies(
            phases,
            data_models,
            input_data.get("architecture_context", {})
        )

        # 7. Generate plan.md
        plan_path = await self._generate_plan_md(
            phases,
            data_models,
            arch_decisions,
            effort,
            dependencies
        )

        # 8. Generate data-model.md (if data models exist)
        data_model_path = None
        if data_models:
            data_model_path = await self._generate_data_model_md(data_models)

        return {
            "plan_path": str(plan_path),
            "data_model_path": str(data_model_path) if data_model_path else None,
            "phases": [self._phase_to_dict(p) for p in phases],
            "architecture_decisions": [self._decision_to_dict(d) for d in arch_decisions],
            "effort_estimate": effort,
            "dependencies": dependencies
        }

    async def _parse_spec(self, spec_path: str) -> dict:
        """Parse spec file into structured data."""
        pass

    async def _generate_phases(self, spec_content: dict) -> list[Phase]:
        """Break spec into implementation phases."""
        pass

    async def _extract_data_models(self, spec_content: dict) -> list[DataModel]:
        """Extract data models from requirements."""
        pass

    async def _generate_architecture_decisions(
        self,
        spec_content: dict,
        arch_context: dict
    ) -> list[ArchitectureDecision]:
        """Generate architecture decision records."""
        pass

    async def _estimate_effort(
        self,
        phases: list[Phase],
        data_models: list[DataModel]
    ) -> dict:
        """Estimate effort for implementation."""
        pass

    async def _identify_dependencies(
        self,
        phases: list[Phase],
        data_models: list[DataModel],
        arch_context: dict
    ) -> list[dict]:
        """Identify implementation dependencies."""
        pass

    async def _generate_plan_md(
        self,
        phases: list[Phase],
        data_models: list[DataModel],
        arch_decisions: list[ArchitectureDecision],
        effort: dict,
        dependencies: list[dict]
    ) -> Path:
        """Generate plan.md file."""
        pass

    async def _generate_data_model_md(
        self,
        data_models: list[DataModel]
    ) -> Path:
        """Generate data-model.md file."""
        pass
```

### Templates

#### plan.md Template

```markdown
# Implementation Plan: {title}

**Generated:** {timestamp}
**Estimated Effort:** {story_points} SP / {hours} hours
**Phases:** {phase_count}

---

## Overview

{overview}

## Architecture Decisions

{architecture_decisions}

## Implementation Phases

{phases}

## Dependencies

{dependencies}

## Acceptance Criteria

{acceptance_criteria}

## Risks & Mitigation

{risks}
```

#### data-model.md Template

```markdown
# Data Model: {title}

**Generated:** {timestamp}
**Entities:** {entity_count}

---

## Entity Definitions

{entities}

## Relationships

{relationships}

## Schema SQL (PostgreSQL)

{sql_schema}

## Schema JSON (NoSQL)

{json_schema}
```

---

## Test Coverage Plan

### Test Classes

1. **TestPlanPrimitiveInitialization**
   - Test default initialization
   - Test custom configuration
   - Test output directory creation

2. **TestSpecParsing**
   - Test valid spec parsing
   - Test invalid spec handling
   - Test missing spec file
   - Test malformed spec

3. **TestPhaseGeneration**
   - Test basic phase breakdown
   - Test phase ordering
   - Test phase dependencies
   - Test max_phases limit

4. **TestDataModelExtraction**
   - Test entity identification
   - Test attribute extraction
   - Test relationship detection
   - Test optional data models

5. **TestArchitectureDecisions**
   - Test decision generation
   - Test architecture context usage
   - Test decision formatting
   - Test optional decisions

6. **TestEffortEstimation**
   - Test story point calculation
   - Test hour estimation
   - Test confidence score
   - Test optional estimation

7. **TestDependencyIdentification**
   - Test external dependencies
   - Test internal dependencies
   - Test blocker flagging

8. **TestPlanGeneration**
   - Test plan.md creation
   - Test plan formatting
   - Test complete plan structure

9. **TestDataModelGeneration**
   - Test data-model.md creation
   - Test SQL schema generation
   - Test JSON schema generation

10. **TestObservability**
    - Test span creation
    - Test metric recording
    - Test context propagation

**Target Coverage:** 90%+

---

## Example Scenarios

### Example 1: Basic Plan Generation

```python
from tta_dev_primitives.speckit import PlanPrimitive
from tta_dev_primitives import WorkflowContext

plan = PlanPrimitive(
    output_dir="./plans",
    include_data_models=True,
    include_architecture_decisions=True
)

result = await plan.execute({
    "spec_path": "./specs/feature.spec.md",
    "output_dir": "./plans"
}, WorkflowContext())

print(f"Plan generated: {result['plan_path']}")
print(f"Phases: {len(result['phases'])}")
print(f"Effort: {result['effort_estimate']['story_points']} SP")
```

### Example 2: Plan with Architecture Context

```python
result = await plan.execute({
    "spec_path": "./specs/api.spec.md",
    "architecture_context": {
        "existing_patterns": ["REST API", "PostgreSQL", "Redis Cache"],
        "tech_stack": ["Python", "FastAPI", "SQLAlchemy"],
        "constraints": ["Must support 10k RPS", "99.9% uptime"]
    },
    "team_capacity": {
        "available_devs": 3,
        "sprint_length_days": 14
    }
}, WorkflowContext())
```

### Example 3: Complete Workflow

```python
from tta_dev_primitives.speckit import (
    SpecifyPrimitive,
    ClarifyPrimitive,
    ValidationGatePrimitive,
    PlanPrimitive
)

# Specify
specify_result = await specify.execute({...}, context)

# Clarify
clarify_result = await clarify.execute({...}, context)

# Validate
validation_result = await validation_gate.execute({...}, context)

# Wait for approval (external process)
# ...

# Plan
plan_result = await plan.execute({
    "spec_path": validation_result["artifacts"][0],
    "architecture_context": {...}
}, context)

print(f"Plan: {plan_result['plan_path']}")
print(f"Data Model: {plan_result['data_model_path']}")
```

### Example 4: Minimal Plan (No Extras)

```python
minimal_plan = PlanPrimitive(
    include_data_models=False,
    include_architecture_decisions=False,
    estimate_effort=False
)

result = await minimal_plan.execute({
    "spec_path": "./specs/simple.spec.md"
}, WorkflowContext())

# Only generates phases and plan.md
```

---

## Success Criteria

### Day 6 Success Criteria

- ✅ PlanPrimitive class implemented
- ✅ Spec parsing functional
- ✅ Phase generation working
- ✅ plan.md generation functional
- ✅ 80%+ test coverage
- ✅ Basic example working

### Day 7 Success Criteria

- ✅ Data model extraction working
- ✅ Architecture decisions documented
- ✅ Effort estimation functional
- ✅ Dependency identification working
- ✅ 90%+ test coverage
- ✅ 4 examples demonstrating all features
- ✅ Complete workflow example (Specify → Clarify → Validate → Plan)

---

## Integration Points

### Input from ValidationGatePrimitive

```python
validation_result = {
    "approved": True,
    "artifacts": ["./specs/validated.spec.md"],
    "feedback": "LGTM - proceed with planning",
    "validation_results": {...}
}

# Use validated spec for planning
plan_result = await plan.execute({
    "spec_path": validation_result["artifacts"][0]
}, context)
```

### Output to TasksPrimitive (Days 8-9)

```python
plan_result = {
    "plan_path": "./plans/feature.plan.md",
    "phases": [
        {"number": 1, "name": "Data Model", "requirements": [...]},
        {"number": 2, "name": "API Endpoints", "requirements": [...]}
    ]
}

# Use plan for task breakdown
tasks_result = await tasks.execute({
    "plan_path": plan_result["plan_path"],
    "phases": plan_result["phases"]
}, context)
```

---

## Risks & Mitigation

### Risk 1: Complex Spec Parsing

**Risk:** Specs may have inconsistent formats or ambiguous requirements

**Mitigation:**
- Start with well-formed examples from ClarifyPrimitive
- Add robust parsing with error handling
- Provide clear error messages for malformed specs
- Use [CLARIFY] marker detection (should be minimal after validation)

### Risk 2: Phase Ordering

**Risk:** Determining optimal phase order may be complex

**Mitigation:**
- Use simple dependency heuristics (data → business logic → API → UI)
- Allow manual phase ordering in future versions
- Document phase ordering logic clearly
- Test with various spec types

### Risk 3: Data Model Extraction

**Risk:** Extracting entities from natural language may miss relationships

**Mitigation:**
- Start with explicit entity mentions
- Look for relationship keywords (has, belongs to, references)
- Allow manual data model refinement
- Phase 2: Use LLM for smarter extraction

### Risk 4: Effort Estimation

**Risk:** Estimating effort accurately is notoriously difficult

**Mitigation:**
- Use simple heuristics (requirements count, complexity markers)
- Provide confidence scores
- Allow manual adjustment
- Track actual vs estimated for calibration

---

## Timeline

**Day 6 (8 hours):**
- 09:00-11:00: Create PlanPrimitive class + spec parsing
- 11:00-14:00: Phase generation logic
- 14:00-16:00: plan.md generation
- 16:00-19:00: Basic tests

**Day 7 (8 hours):**
- 09:00-12:00: Data model extraction + architecture decisions
- 12:00-14:00: Effort estimation + dependency identification
- 14:00-17:00: Comprehensive tests
- 17:00-19:00: Examples + documentation

---

## Next Steps After Days 6-7

**Days 8-9: TasksPrimitive**
- Input: plan.md + phases
- Output: tasks.md with ordered task list
- Features: dependency ordering, effort per task, ticket formatting

**Day 10: Integration Example**
- Complete 5-primitive workflow
- End-to-end demonstration
- Error handling showcase
- Real-world use case

---

**Status:** 🚧 Ready to begin Day 6 implementation
**Estimated Completion:** End of Day 7
**Dependencies:** Day 5 (ValidationGatePrimitive) ✅ Complete


---
**Logseq:** [[TTA.dev/_archive/Speckit-planning/Speckit_day6_7_plan]]
