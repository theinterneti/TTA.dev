"""Workflow Hub Generator Primitive.

This primitive generates WORKFLOW.md documentation from workflow profile definitions.
Similar to GenerateAgentsHubPrimitive but for workflow execution modes.

Example:
    >>> from tta_dev_primitives import GenerateWorkflowHubPrimitive
    >>> generator = GenerateWorkflowHubPrimitive()
    >>> generator.generate_workflow_hub()
    # Creates WORKFLOW.md in repository root
"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class WorkflowMode(str, Enum):
    """Workflow execution modes."""

    RAPID = "rapid"
    STANDARD = "standard"
    AUGSTER_RIGOROUS = "augster-rigorous"


@dataclass
class WorkflowStage:
    """Single stage in a workflow."""

    name: str
    description: str
    memory_layers: list[str]
    quality_gates: list[str]
    duration_estimate: str


@dataclass
class WorkflowProfile:
    """Complete workflow profile definition."""

    mode: WorkflowMode
    display_name: str
    use_case: str
    characteristics: list[str]
    stages: list[WorkflowStage]
    quality_gates: list[str]
    is_default: bool = False


class GenerateWorkflowHubPrimitive:
    """Generate WORKFLOW.md from workflow profiles.

    This primitive creates standardized workflow documentation that guides
    AI agents through different execution modes based on task context.

    Attributes:
        profiles_dir: Directory containing workflow profile definitions
        output_path: Path where WORKFLOW.md will be generated
        profiles: Loaded workflow profiles

    Example:
        >>> generator = GenerateWorkflowHubPrimitive()
        >>> generator.generate_workflow_hub()
        >>> # WORKFLOW.md created in repo root
    """

    def __init__(
        self,
        profiles_dir: str | Path | None = None,
        output_path: str | Path | None = None,
    ) -> None:
        """Initialize workflow hub generator.

        Args:
            profiles_dir: Directory with workflow profiles (default: .universal-instructions/workflows)
            output_path: Output file path (default: WORKFLOW.md in repo root)
        """
        self.profiles_dir = Path(profiles_dir or ".universal-instructions/workflows")
        self.output_path = Path(output_path or "WORKFLOW.md")
        self.profiles: dict[WorkflowMode, WorkflowProfile] = {}
        self._load_profiles()

    def _load_profiles(self) -> None:
        """Load workflow profiles from definitions.

        This creates hardcoded profiles based on WORKFLOW_PROFILES.md.
        Future: Could load from individual .workflow.md files.
        """
        # Rapid Mode Profile
        self.profiles[WorkflowMode.RAPID] = WorkflowProfile(
            mode=WorkflowMode.RAPID,
            display_name="Rapid Mode",
            use_case="Rapid prototyping, exploration, proof-of-concept",
            characteristics=[
                "Minimal validation",
                "Skip extensive documentation",
                "Fast iteration",
                "Accept higher risk",
                "Streamlined stages",
            ],
            stages=[
                WorkflowStage(
                    name="Understand",
                    description="Quick context gathering with minimal memory loading",
                    memory_layers=["Session Context"],
                    quality_gates=[],
                    duration_estimate="2-5 minutes",
                ),
                WorkflowStage(
                    name="Implement",
                    description="Direct implementation without decomposition",
                    memory_layers=["Session Context"],
                    quality_gates=[],
                    duration_estimate="10-20 minutes",
                ),
                WorkflowStage(
                    name="Quick Test",
                    description="Basic syntax check and manual testing",
                    memory_layers=["Session Context"],
                    quality_gates=["Syntax valid (ruff format)"],
                    duration_estimate="2-5 minutes",
                ),
            ],
            quality_gates=["Syntax valid (ruff format)"],
        )

        # Standard Mode Profile (DEFAULT)
        self.profiles[WorkflowMode.STANDARD] = WorkflowProfile(
            mode=WorkflowMode.STANDARD,
            display_name="Standard Mode",
            use_case="Regular development, feature implementation",
            characteristics=[
                "Balanced rigor",
                "Standard documentation",
                "Normal iteration speed",
                "Moderate risk acceptance",
                "Core stages with selective depth",
            ],
            stages=[
                WorkflowStage(
                    name="Understand",
                    description="Standard context gathering with recent memory loading",
                    memory_layers=[
                        "Session Context",
                        "Recent Cache",
                        "Top 5 Deep Memory",
                    ],
                    quality_gates=[],
                    duration_estimate="5-10 minutes",
                ),
                WorkflowStage(
                    name="Decompose",
                    description="Break down into components and identify dependencies",
                    memory_layers=["Session Context", "PAF Store"],
                    quality_gates=[],
                    duration_estimate="5-10 minutes",
                ),
                WorkflowStage(
                    name="Plan",
                    description="Create implementation plan and select approach",
                    memory_layers=["Session Context", "Deep Memory", "PAF Store"],
                    quality_gates=[],
                    duration_estimate="5-10 minutes",
                ),
                WorkflowStage(
                    name="Implement",
                    description="Follow plan with tests alongside",
                    memory_layers=["Session Context", "Cache Memory"],
                    quality_gates=["Format valid", "Lint passing"],
                    duration_estimate="20-40 minutes",
                ),
                WorkflowStage(
                    name="Validate",
                    description="Run linters, formatters, and tests",
                    memory_layers=["Session Context"],
                    quality_gates=[
                        "Format valid (ruff format)",
                        "Lint passing (ruff check)",
                        "Basic type hints present",
                        "Unit tests passing",
                    ],
                    duration_estimate="5-10 minutes",
                ),
            ],
            quality_gates=[
                "Format valid (ruff format)",
                "Lint passing (ruff check)",
                "Basic type hints present",
                "Unit tests passing",
            ],
            is_default=True,
        )

        # Augster-Rigorous Mode Profile
        self.profiles[WorkflowMode.AUGSTER_RIGOROUS] = WorkflowProfile(
            mode=WorkflowMode.AUGSTER_RIGOROUS,
            display_name="Augster-Rigorous Mode",
            use_case="Production-critical work, architectural decisions",
            characteristics=[
                "Maximum rigor",
                "Comprehensive documentation",
                "Thorough validation",
                "Minimal risk tolerance",
                "Full 6-stage workflow",
            ],
            stages=[
                WorkflowStage(
                    name="Understand",
                    description="Deep context gathering with full memory loading",
                    memory_layers=[
                        "Full Session History",
                        "Grouped Sessions",
                        "Cache (24h)",
                        "Top 20 Deep Memory",
                        "All Active PAFs",
                    ],
                    quality_gates=[],
                    duration_estimate="10-20 minutes",
                ),
                WorkflowStage(
                    name="Decompose",
                    description="Complete task decomposition with risk assessment",
                    memory_layers=["Session Context", "Deep Memory", "PAF Store"],
                    quality_gates=[],
                    duration_estimate="10-15 minutes",
                ),
                WorkflowStage(
                    name="Plan",
                    description="Detailed implementation plan with test and rollback strategies",
                    memory_layers=["Session Context", "Deep Memory", "PAF Store"],
                    quality_gates=["PAF compliance check"],
                    duration_estimate="15-20 minutes",
                ),
                WorkflowStage(
                    name="Implement",
                    description="Careful TDD implementation with continuous validation",
                    memory_layers=["Session Context", "Cache Memory", "Deep Memory"],
                    quality_gates=[
                        "Format valid",
                        "Lint passing",
                        "Type hints complete",
                    ],
                    duration_estimate="40-90 minutes",
                ),
                WorkflowStage(
                    name="Validate",
                    description="Comprehensive quality gates and security scan",
                    memory_layers=["Session Context", "PAF Store"],
                    quality_gates=[
                        "Format valid (ruff format)",
                        "Lint passing (ruff check)",
                        "Type checking passing (pyright)",
                        "All tests passing",
                        "Coverage ≥70% (PAF-QUAL-001)",
                        "File size ≤800 lines (PAF-QUAL-004)",
                        "Documentation complete",
                    ],
                    duration_estimate="10-20 minutes",
                ),
                WorkflowStage(
                    name="Reflect",
                    description="Capture learnings and update memories/PAFs",
                    memory_layers=["Deep Memory (write)", "PAF Store (write)"],
                    quality_gates=[],
                    duration_estimate="5-10 minutes",
                ),
            ],
            quality_gates=[
                "Format valid (ruff format)",
                "Lint passing (ruff check)",
                "Type checking passing (pyright)",
                "All tests passing",
                "Coverage ≥70%",
                "File size ≤800 lines",
                "Documentation complete",
                "Security scan passing",
            ],
        )

    def generate_workflow_hub(self) -> None:
        """Generate WORKFLOW.md file from loaded profiles.

        Creates a comprehensive workflow guide that AI agents can reference
        to determine appropriate execution mode and stage progression.

        Raises:
            ValueError: If no profiles are loaded
        """
        if not self.profiles:
            msg = "No workflow profiles loaded"
            raise ValueError(msg)

        content = self._generate_content()
        self.output_path.write_text(content, encoding="utf-8")

    def _generate_content(self) -> str:
        """Generate complete WORKFLOW.md content.

        Returns:
            Markdown content string
        """
        parts = [
            self._generate_header(),
            self._generate_overview(),
            self._generate_quick_reference(),
            self._generate_profile_details(),
            self._generate_mode_selection(),
            self._generate_memory_integration(),
            self._generate_examples(),
            self._generate_footer(),
        ]
        return "\n\n".join(parts)

    def _generate_header(self) -> str:
        """Generate document header."""
        return """# WORKFLOW - AI Agent Execution Modes

**Purpose**: Guide AI agents through different workflow execution modes based on task context and requirements.

**Last Updated**: 2025-01-28
**Status**: Active

---"""

    def _generate_overview(self) -> str:
        """Generate overview section."""
        default_mode = next((p for p in self.profiles.values() if p.is_default), None)
        default_name = default_mode.display_name if default_mode else "Standard Mode"

        return f"""## Overview

AI agents can execute tasks with varying levels of rigor depending on context:

- **Rapid Mode**: Fast prototyping with minimal validation
- **Standard Mode**: Regular development with balanced rigor ⭐ **DEFAULT**
- **Augster-Rigorous Mode**: Production-critical work with maximum validation

**Current Default**: {default_name}

The workflow mode determines:
- Number and depth of workflow stages
- Memory layers loaded at each stage
- Quality gates enforced
- Documentation requirements
- Risk tolerance"""

    def _generate_quick_reference(self) -> str:
        """Generate quick reference table."""
        table = "## Quick Reference\n\n"
        table += "| Mode | Stages | Duration | Quality Gates | Use Case |\n"
        table += "|------|--------|----------|---------------|----------|\n"

        for profile in self.profiles.values():
            stages_count = len(profile.stages)
            total_duration = self._estimate_total_duration(profile)
            gates_count = len(profile.quality_gates)
            use_case_short = profile.use_case.split(",")[0]

            default_marker = " ⭐" if profile.is_default else ""
            table += f"| **{profile.display_name}**{default_marker} | {stages_count} | {total_duration} | {gates_count} | {use_case_short} |\n"

        return table

    def _estimate_total_duration(self, profile: WorkflowProfile) -> str:
        """Estimate total workflow duration.

        Args:
            profile: Workflow profile

        Returns:
            Duration estimate string (e.g., "15-45 min")
        """
        # Simple heuristic: sum min and max from each stage
        total_min = 0
        total_max = 0

        for stage in profile.stages:
            # Parse "10-20 minutes" → (10, 20)
            parts = stage.duration_estimate.split("-")
            if len(parts) == 2:
                min_val = int(parts[0].strip())
                max_val = int(parts[1].split()[0].strip())
                total_min += min_val
                total_max += max_val

        return f"{total_min}-{total_max} min"

    def _generate_profile_details(self) -> str:
        """Generate detailed profile sections."""
        sections = ["## Workflow Profiles\n"]

        for profile in self.profiles.values():
            sections.append(self._generate_profile_section(profile))

        return "\n\n".join(sections)

    def _generate_profile_section(self, profile: WorkflowProfile) -> str:
        """Generate single profile section.

        Args:
            profile: Workflow profile to document

        Returns:
            Markdown section string
        """
        default_marker = " ⭐ **DEFAULT**" if profile.is_default else ""
        section = f"### {profile.display_name}{default_marker}\n\n"

        section += f"**Use Case**: {profile.use_case}\n\n"

        section += "**Characteristics**:\n\n"
        for char in profile.characteristics:
            section += f"- {char}\n"

        section += f"\n**Total Duration**: {self._estimate_total_duration(profile)}\n\n"

        section += "**Workflow Stages**:\n\n"
        for i, stage in enumerate(profile.stages, 1):
            section += f"{i}. **{stage.name}** ({stage.duration_estimate})\n"
            section += f"   - {stage.description}\n"
            section += f"   - Memory: {', '.join(stage.memory_layers)}\n"
            if stage.quality_gates:
                section += f"   - Gates: {', '.join(stage.quality_gates)}\n"
            section += "\n"

        section += "**Quality Gates**:\n\n"
        for gate in profile.quality_gates:
            section += f"- ✅ {gate}\n"

        return section

    def _generate_mode_selection(self) -> str:
        """Generate mode selection guidance."""
        return """## Selecting a Workflow Mode

### Automatic Mode Detection

The system can automatically select mode based on:

- **File patterns**: `*.test.py` → Standard, `src/core/*` → Augster-Rigorous
- **Task keywords**: "prototype" → Rapid, "production" → Augster-Rigorous
- **Component maturity**: Development → Rapid, Staging → Standard, Production → Augster-Rigorous

### Manual Mode Selection

```bash
# Via environment variable
export WORKFLOW_MODE="augster-rigorous"

# Via inline directive in task description
# workflow-mode: rapid
```

### In Code

```python
from tta_dev_primitives import WorkflowContext

context = WorkflowContext(
    workflow_id="feature-xyz",
    session_id="session-123",
    workflow_mode="augster-rigorous"  # Explicit mode
)
```"""

    def _generate_memory_integration(self) -> str:
        """Generate memory integration guidance."""
        return """## Memory Layer Integration

Each workflow mode uses different memory layers at different stages:

### 4-Layer Memory Architecture

1. **Session Context**: Current execution context (always loaded)
2. **Cache Memory**: Recent interactions (1-24 hours)
3. **Deep Memory**: Persistent patterns and learnings (vector search)
4. **PAF Store**: Permanent architectural facts (validation)

### Memory Loading by Mode

| Mode | Session | Cache | Deep | PAF |
|------|---------|-------|------|-----|
| Rapid | Current only | ❌ | ❌ | ❌ |
| Standard | Recent history | Last 1h | Top 5 | Active only |
| Augster-Rigorous | Full + grouped | Last 24h | Top 20 | All PAFs |

### Stage-Specific Memory Loading

Different stages may load different memory layers. See profile details above for stage-specific memory loading patterns."""

    def _generate_examples(self) -> str:
        """Generate usage examples."""
        return """## Examples

### Rapid Mode: Quick Prototype

```python
# Quick test of an idea - minimal validation
def rapid_prototype():
    \"\"\"Quick test - no extensive validation needed.\"\"\"
    result = do_something()
    print(result)  # Manual validation
    return result
```

### Standard Mode: Feature Implementation

```python
# Regular feature with standard quality gates
def standard_feature(data: dict) -> Result:
    \"\"\"Standard feature with normal quality gates.

    Args:
        data: Input data dictionary

    Returns:
        Result object with processed data
    \"\"\"
    processed = process_data(data)
    return Result(processed)

def test_standard_feature():
    \"\"\"Test for standard feature.\"\"\"
    result = standard_feature({"key": "value"})
    assert result.is_valid
```

### Augster-Rigorous Mode: Production Feature

```python
# Production-critical with comprehensive validation
class ProductionFeature:
    \"\"\"Production-critical feature with full rigor.

    Comprehensive documentation, full type coverage,
    security validation, and PAF compliance.
    \"\"\"

    def __init__(self, config: Config) -> None:
        \"\"\"Initialize with validated configuration.\"\"\"
        # Validate against PAFs
        paf = PAFMemoryPrimitive()
        # ... comprehensive validation

    def execute(self, data: SecureData) -> SecureResult:
        \"\"\"Execute with full validation.\"\"\"
        # Comprehensive implementation
        pass

# Comprehensive test suite (70%+ coverage)
class TestProductionFeature:
    def test_normal_case(self): ...
    def test_edge_cases(self): ...
    def test_security_constraints(self): ...
    def test_paf_compliance(self): ...
```"""

    def _generate_footer(self) -> str:
        """Generate document footer."""
        return """---

## References

- **PAF System**: `.universal-instructions/paf/PAFCORE.md`
- **Workflow Profiles**: `.universal-instructions/workflows/WORKFLOW_PROFILES.md`
- **Augster Workflow**: `.universal-instructions/augster-specific/workflows/axiomatic-workflow.md`
- **Memory System**: `docs/guides/SESSION_MEMORY_INTEGRATION_PLAN.md`

---

**Generated by**: GenerateWorkflowHubPrimitive
**Source**: `.universal-instructions/workflows/WORKFLOW_PROFILES.md`"""

    def get_profile(self, mode: WorkflowMode) -> WorkflowProfile | None:
        """Get workflow profile by mode.

        Args:
            mode: Workflow mode to retrieve

        Returns:
            Workflow profile or None if not found
        """
        return self.profiles.get(mode)

    def get_default_profile(self) -> WorkflowProfile | None:
        """Get default workflow profile.

        Returns:
            Default workflow profile or None
        """
        return next((p for p in self.profiles.values() if p.is_default), None)

    def summary(self) -> dict[str, int | str | list[str]]:
        """Get summary statistics.

        Returns:
            Dictionary with profile counts and default mode
        """
        default = self.get_default_profile()
        return {
            "total_profiles": len(self.profiles),
            "default_mode": default.mode.value if default else "none",
            "modes": [mode.value for mode in self.profiles.keys()],
        }
