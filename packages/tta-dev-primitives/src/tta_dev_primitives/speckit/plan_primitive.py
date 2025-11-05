"""Plan primitive for generating implementation plans from validated specifications.

Part of the Speckit system (Days 6-7 of 25).
"""

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from tta_dev_primitives import WorkflowContext
from tta_dev_primitives.observability.instrumented_primitive import (
    InstrumentedPrimitive,
)


@dataclass
class Phase:
    """Implementation phase in the plan."""

    number: int
    name: str
    description: str
    requirements: list[str]
    estimated_hours: float
    dependencies: list[str] | None = None


@dataclass
class ArchitectureDecision:
    """Architecture decision record (ADR)."""

    decision: str
    rationale: str
    alternatives: list[str]
    tradeoffs: str


@dataclass
class DataModel:
    """Data model entity definition."""

    name: str
    attributes: dict[str, str]  # attribute_name -> type
    relationships: list[str]
    description: str


class PlanPrimitive(InstrumentedPrimitive[dict[str, Any], dict[str, Any]]):
    """Generate implementation plans from validated specifications.

    Converts validated spec files into structured implementation plans with:
    - Ordered implementation phases
    - Data model definitions
    - Architecture decision records
    - Effort estimates
    - Dependency identification

    Input Schema:
        {
            "spec_path": str,  # Path to validated spec file
            "output_dir": str,  # Optional, directory for output files
            "architecture_context": dict,  # Optional, existing architecture info
            "team_capacity": dict  # Optional, team size and sprint info
        }

    Output Schema:
        {
            "plan_path": str,  # Path to generated plan.md
            "data_model_path": str | None,  # Path to data-model.md if generated
            "phases": list[dict],  # List of implementation phases
            "architecture_decisions": list[dict],  # List of ADRs
            "effort_estimate": dict | None,  # Effort estimation if enabled
            "dependencies": list[dict]  # List of dependencies
        }
    """

    def __init__(
        self,
        output_dir: str = "./output",
        max_phases: int = 5,
        include_data_models: bool = True,
        include_architecture_decisions: bool = True,
        estimate_effort: bool = True,
    ) -> None:
        """Initialize plan primitive.

        Args:
            output_dir: Directory for output files (plan.md, data-model.md)
            max_phases: Maximum number of implementation phases
            include_data_models: Whether to extract and generate data models
            include_architecture_decisions: Whether to generate ADRs
            estimate_effort: Whether to estimate effort (story points, hours)
        """
        super().__init__(name="plan_primitive")
        self.output_dir = Path(output_dir)
        self.max_phases = max_phases
        self.include_data_models = include_data_models
        self.include_architecture_decisions = include_architecture_decisions
        self.estimate_effort = estimate_effort

        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def _execute_impl(
        self, input_data: dict[str, Any], context: WorkflowContext
    ) -> dict[str, Any]:
        """Generate implementation plan from validated spec.

        Args:
            input_data: Input containing spec_path and optional config
            context: Workflow context for tracing

        Returns:
            Dictionary with plan_path, data_model_path, phases, etc.

        Raises:
            FileNotFoundError: If spec_path doesn't exist
            ValueError: If spec parsing fails
        """
        spec_path = Path(input_data["spec_path"])
        if not spec_path.exists():
            raise FileNotFoundError(f"Spec file not found: {spec_path}")

        # Override output_dir if provided in input
        output_dir = Path(input_data.get("output_dir", self.output_dir))
        output_dir.mkdir(parents=True, exist_ok=True)

        # 1. Parse spec file
        spec_content = await self._parse_spec(spec_path)

        # 2. Generate implementation phases
        phases = await self._generate_phases(spec_content)

        # 3. Extract data models (if enabled)
        data_models: list[DataModel] = []
        if self.include_data_models:
            data_models = await self._extract_data_models(spec_content)

        # 4. Generate architecture decisions (if enabled)
        arch_decisions: list[ArchitectureDecision] = []
        if self.include_architecture_decisions:
            arch_decisions = await self._generate_architecture_decisions(
                spec_content, input_data.get("architecture_context", {})
            )

        # 5. Estimate effort (if enabled)
        effort: dict[str, Any] | None = None
        if self.estimate_effort:
            effort = await self._estimate_effort(phases, data_models)

        # 6. Identify dependencies
        dependencies = await self._identify_dependencies(
            phases, data_models, input_data.get("architecture_context", {})
        )

        # 7. Generate plan.md
        plan_path = await self._generate_plan_md(
            output_dir,
            spec_content,
            phases,
            data_models,
            arch_decisions,
            effort,
            dependencies,
        )

        # 8. Generate data-model.md (if data models exist)
        data_model_path: Path | None = None
        if data_models:
            data_model_path = await self._generate_data_model_md(
                output_dir, data_models
            )

        return {
            "plan_path": str(plan_path),
            "data_model_path": str(data_model_path) if data_model_path else None,
            "phases": [self._phase_to_dict(p) for p in phases],
            "architecture_decisions": [
                self._decision_to_dict(d) for d in arch_decisions
            ],
            "effort_estimate": effort,
            "dependencies": dependencies,
        }

    async def _parse_spec(self, spec_path: Path) -> dict[str, Any]:
        """Parse spec file into structured data.

        Args:
            spec_path: Path to spec file

        Returns:
            Dictionary with spec sections and metadata

        Raises:
            ValueError: If spec is malformed
        """
        content = spec_path.read_text(encoding="utf-8")

        # Extract title (first # header)
        title = "Untitled"
        for line in content.splitlines():
            if line.startswith("# "):
                title = line[2:].strip()
                break

        # Extract sections by headers
        sections: dict[str, str] = {}
        current_section = None
        current_content: list[str] = []

        for line in content.splitlines():
            if line.startswith("## "):
                # Save previous section
                if current_section:
                    sections[current_section] = "\n".join(current_content).strip()
                # Start new section
                current_section = line[3:].strip()
                current_content = []
            elif current_section:
                current_content.append(line)

        # Save last section
        if current_section:
            sections[current_section] = "\n".join(current_content).strip()

        return {
            "title": title,
            "sections": sections,
            "path": str(spec_path),
        }

    async def _generate_phases(self, spec_content: dict[str, Any]) -> list[Phase]:
        """Break spec into implementation phases.

        Args:
            spec_content: Parsed spec content

        Returns:
            List of Phase objects
        """
        sections = spec_content["sections"]

        # Extract features/requirements
        features = sections.get("Features", "").splitlines()
        requirements = sections.get("Requirements", "").splitlines()
        acceptance_criteria = sections.get("Acceptance Criteria", "").splitlines()

        # Combine all requirements
        all_requirements = [
            line.strip()
            for line in features + requirements + acceptance_criteria
            if line.strip() and not line.strip().startswith("[CLARIFY]")
        ]

        # Simple phase generation: group requirements into logical phases
        # Phase 1: Data Model (any requirements mentioning data/model/entity)
        # Phase 2: Business Logic (core functionality)
        # Phase 3: API/Interface (endpoints, UI)
        # Phase 4: Integration (external services)
        # Phase 5: Testing & Deployment

        data_requirements = [
            r
            for r in all_requirements
            if any(
                keyword in r.lower()
                for keyword in ["data", "model", "entity", "schema", "database"]
            )
        ]

        api_requirements = [
            r
            for r in all_requirements
            if any(
                keyword in r.lower()
                for keyword in ["api", "endpoint", "route", "interface", "ui"]
            )
        ]

        integration_requirements = [
            r
            for r in all_requirements
            if any(
                keyword in r.lower()
                for keyword in [
                    "integration",
                    "external",
                    "service",
                    "third-party",
                ]
            )
        ]

        # Remaining are business logic
        categorized = set(
            data_requirements + api_requirements + integration_requirements
        )
        logic_requirements = [r for r in all_requirements if r not in categorized]

        phases: list[Phase] = []

        if data_requirements:
            phases.append(
                Phase(
                    number=1,
                    name="Data Model Setup",
                    description="Define data models, schemas, and database structure",
                    requirements=data_requirements,
                    estimated_hours=len(data_requirements) * 4.0,
                    dependencies=None,
                )
            )

        if logic_requirements:
            phases.append(
                Phase(
                    number=len(phases) + 1,
                    name="Business Logic Implementation",
                    description="Implement core business logic and functionality",
                    requirements=logic_requirements,
                    estimated_hours=len(logic_requirements) * 6.0,
                    dependencies=["Phase 1"] if phases else None,
                )
            )

        if api_requirements:
            phases.append(
                Phase(
                    number=len(phases) + 1,
                    name="API & Interface Development",
                    description="Build API endpoints and user interfaces",
                    requirements=api_requirements,
                    estimated_hours=len(api_requirements) * 5.0,
                    dependencies=[f"Phase {len(phases)}"] if phases else None,
                )
            )

        if integration_requirements:
            phases.append(
                Phase(
                    number=len(phases) + 1,
                    name="External Integration",
                    description="Integrate with external services and APIs",
                    requirements=integration_requirements,
                    estimated_hours=len(integration_requirements) * 8.0,
                    dependencies=[f"Phase {len(phases)}"] if phases else None,
                )
            )

        # Always add testing & deployment phase
        phases.append(
            Phase(
                number=len(phases) + 1,
                name="Testing & Deployment",
                description="Comprehensive testing and production deployment",
                requirements=[
                    "Unit tests for all components",
                    "Integration tests",
                    "End-to-end tests",
                    "Production deployment",
                ],
                estimated_hours=16.0,
                dependencies=[f"Phase {len(phases)}"] if phases else None,
            )
        )

        # Limit to max_phases
        return phases[: self.max_phases]

    async def _extract_data_models(
        self, spec_content: dict[str, Any]
    ) -> list[DataModel]:
        """Extract data models from spec requirements.

        Args:
            spec_content: Parsed spec content

        Returns:
            List of DataModel objects
        """
        # Simple extraction: look for entity mentions
        sections = spec_content["sections"]
        requirements = sections.get("Requirements", "") + sections.get("Features", "")

        models: list[DataModel] = []

        # Look for entity patterns like "User", "Post", "Comment"
        # This is a simplified heuristic - real implementation would be more sophisticated
        common_entities = [
            "User",
            "Post",
            "Comment",
            "Product",
            "Order",
            "Article",
            "Event",
        ]

        for entity in common_entities:
            if entity.lower() in requirements.lower():
                models.append(
                    DataModel(
                        name=entity,
                        attributes={
                            "id": "UUID",
                            "created_at": "DateTime",
                            "updated_at": "DateTime",
                        },
                        relationships=[],
                        description=f"{entity} entity from requirements",
                    )
                )

        return models

    async def _generate_architecture_decisions(
        self, spec_content: dict[str, Any], arch_context: dict[str, Any]
    ) -> list[ArchitectureDecision]:
        """Generate architecture decision records.

        Args:
            spec_content: Parsed spec content
            arch_context: Existing architecture context

        Returns:
            List of ArchitectureDecision objects
        """
        decisions: list[ArchitectureDecision] = []

        # Example decisions based on common patterns
        tech_stack = arch_context.get("tech_stack", [])

        if not tech_stack or "python" in [t.lower() for t in tech_stack]:
            decisions.append(
                ArchitectureDecision(
                    decision="Use Python with FastAPI for backend",
                    rationale="Fast development, strong typing, async support",
                    alternatives=["Node.js + Express", "Go + Gin"],
                    tradeoffs="Python may be slower than Go, but development speed is prioritized",
                )
            )

        # Database decision
        if not any("database" in t.lower() for t in tech_stack):
            decisions.append(
                ArchitectureDecision(
                    decision="Use PostgreSQL for relational data",
                    rationale="ACID compliance, complex queries, proven reliability",
                    alternatives=["MongoDB", "MySQL"],
                    tradeoffs="Requires schema management, but provides data integrity",
                )
            )

        return decisions

    async def _estimate_effort(
        self, phases: list[Phase], data_models: list[DataModel]
    ) -> dict[str, Any]:
        """Estimate effort for implementation.

        Args:
            phases: List of implementation phases
            data_models: List of data models

        Returns:
            Dictionary with story_points, hours, confidence
        """
        total_hours = sum(p.estimated_hours for p in phases)

        # Simple story point heuristic: 1 SP = 8 hours
        story_points = round(total_hours / 8)

        # Confidence decreases with complexity
        confidence = 0.9 if len(phases) <= 3 else 0.7 if len(phases) <= 5 else 0.5

        return {
            "story_points": story_points,
            "hours": total_hours,
            "confidence": confidence,
            "breakdown": {
                "phases": len(phases),
                "data_models": len(data_models),
            },
        }

    async def _identify_dependencies(
        self,
        phases: list[Phase],
        data_models: list[DataModel],
        arch_context: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Identify implementation dependencies.

        Args:
            phases: List of implementation phases
            data_models: List of data models
            arch_context: Existing architecture context

        Returns:
            List of dependency dictionaries
        """
        dependencies: list[dict[str, Any]] = []

        # Check for external dependencies
        existing_patterns = arch_context.get("existing_patterns", [])

        if "Auth" not in existing_patterns and "auth" not in str(arch_context).lower():
            dependencies.append(
                {
                    "type": "external",
                    "name": "Authentication service",
                    "blocker": True,
                    "description": "User authentication required before implementation",
                }
            )

        # Internal dependencies (phase ordering)
        for i, phase in enumerate(phases):
            if i > 0:
                dependencies.append(
                    {
                        "type": "internal",
                        "name": f"Phase {phase.number}: {phase.name}",
                        "blocker": False,
                        "description": f"Depends on completion of Phase {i}",
                    }
                )

        return dependencies

    async def _generate_plan_md(
        self,
        output_dir: Path,
        spec_content: dict[str, Any],
        phases: list[Phase],
        data_models: list[DataModel],
        arch_decisions: list[ArchitectureDecision],
        effort: dict[str, Any] | None,
        dependencies: list[dict[str, Any]],
    ) -> Path:
        """Generate plan.md file.

        Args:
            output_dir: Output directory
            spec_content: Parsed spec content
            phases: Implementation phases
            data_models: Data models
            arch_decisions: Architecture decisions
            effort: Effort estimate
            dependencies: Dependencies

        Returns:
            Path to generated plan.md
        """
        title = spec_content["title"]
        timestamp = datetime.now(UTC).isoformat()

        # Build plan content
        content_parts = [
            f"# Implementation Plan: {title}",
            "",
            f"**Generated:** {timestamp}",
        ]

        if effort:
            content_parts.extend(
                [
                    f"**Estimated Effort:** {effort['story_points']} SP / {effort['hours']:.0f} hours",
                    f"**Confidence:** {effort['confidence']:.1%}",
                ]
            )

        content_parts.extend(
            [
                f"**Phases:** {len(phases)}",
                "",
                "---",
                "",
            ]
        )

        # Overview
        content_parts.extend(
            [
                "## Overview",
                "",
                spec_content.get("sections", {}).get(
                    "Overview", "No overview provided"
                ),
                "",
            ]
        )

        # Architecture Decisions
        if arch_decisions:
            content_parts.extend(["## Architecture Decisions", ""])
            for i, decision in enumerate(arch_decisions, 1):
                content_parts.extend(
                    [
                        f"### Decision {i}: {decision.decision}",
                        "",
                        f"**Rationale:** {decision.rationale}",
                        "",
                        f"**Alternatives Considered:** {', '.join(decision.alternatives)}",
                        "",
                        f"**Tradeoffs:** {decision.tradeoffs}",
                        "",
                    ]
                )

        # Implementation Phases
        content_parts.extend(["## Implementation Phases", ""])
        for phase in phases:
            content_parts.extend(
                [
                    f"### Phase {phase.number}: {phase.name}",
                    "",
                    f"**Description:** {phase.description}",
                    "",
                    f"**Estimated Hours:** {phase.estimated_hours:.0f}",
                    "",
                ]
            )

            if phase.dependencies:
                content_parts.extend(
                    [
                        f"**Dependencies:** {', '.join(phase.dependencies)}",
                        "",
                    ]
                )

            content_parts.extend(["**Requirements:**", ""])
            for req in phase.requirements:
                content_parts.append(f"- {req}")
            content_parts.append("")

        # Dependencies
        if dependencies:
            content_parts.extend(["## Dependencies", ""])
            for dep in dependencies:
                blocker_str = " **(BLOCKER)**" if dep["blocker"] else ""
                content_parts.extend(
                    [
                        f"- **{dep['name']}** ({dep['type']}){blocker_str}",
                        f"  - {dep['description']}",
                        "",
                    ]
                )

        # Data Models (summary)
        if data_models:
            content_parts.extend(
                [
                    "## Data Models",
                    "",
                    "See [`data-model.md`](./data-model.md) for complete data model definitions.",
                    "",
                    f"**Entities:** {', '.join(m.name for m in data_models)}",
                    "",
                ]
            )

        # Write plan.md
        plan_path = output_dir / "plan.md"
        plan_path.write_text("\n".join(content_parts), encoding="utf-8")

        return plan_path

    async def _generate_data_model_md(
        self, output_dir: Path, data_models: list[DataModel]
    ) -> Path:
        """Generate data-model.md file.

        Args:
            output_dir: Output directory
            data_models: List of data models

        Returns:
            Path to generated data-model.md
        """
        timestamp = datetime.now(UTC).isoformat()

        content_parts = [
            "# Data Model",
            "",
            f"**Generated:** {timestamp}",
            f"**Entities:** {len(data_models)}",
            "",
            "---",
            "",
            "## Entity Definitions",
            "",
        ]

        for model in data_models:
            content_parts.extend(
                [
                    f"### {model.name}",
                    "",
                    model.description,
                    "",
                    "**Attributes:**",
                    "",
                ]
            )

            for attr_name, attr_type in model.attributes.items():
                content_parts.append(f"- `{attr_name}`: {attr_type}")

            if model.relationships:
                content_parts.extend(["", "**Relationships:**", ""])
                for rel in model.relationships:
                    content_parts.append(f"- {rel}")

            content_parts.append("")

        # Write data-model.md
        data_model_path = output_dir / "data-model.md"
        data_model_path.write_text("\n".join(content_parts), encoding="utf-8")

        return data_model_path

    def _phase_to_dict(self, phase: Phase) -> dict[str, Any]:
        """Convert Phase to dictionary."""
        return asdict(phase)

    def _decision_to_dict(self, decision: ArchitectureDecision) -> dict[str, Any]:
        """Convert ArchitectureDecision to dictionary."""
        return asdict(decision)
