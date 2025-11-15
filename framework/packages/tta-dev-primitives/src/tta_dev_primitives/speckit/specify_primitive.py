"""SpecifyPrimitive - Transform requirements into formal specifications.

This primitive takes a high-level requirement and generates a structured
specification document following a standard template. It identifies
underspecified areas and calculates a coverage score.
"""

from pathlib import Path
from typing import Any

from tta_dev_primitives import WorkflowContext
from tta_dev_primitives.observability import InstrumentedPrimitive


class SpecifyPrimitive(InstrumentedPrimitive[dict[str, Any], dict[str, Any]]):
    """Transform high-level requirement into formal .spec.md specification.

    This primitive generates a structured specification document from a
    requirement string. It analyzes the requirement, identifies key components,
    and produces a specification that follows the TTA.dev template.

    Args:
        template_path: Path to specification template (optional)
        output_dir: Directory for generated specs (default: docs/specs/)
        min_coverage: Minimum coverage score to consider complete (default: 0.7)

    Input:
        - requirement (str): High-level feature description
        - context (dict): Project context (architecture, constraints, etc.)
        - feature_name (str, optional): Name for the spec file

    Output:
        - spec_path (str): Path to generated specification
        - coverage_score (float): Completeness score (0.0-1.0)
        - gaps (list[str]): Underspecified areas needing clarification
        - sections_completed (dict): Status of each template section

    Example:
        ```python
        specify = SpecifyPrimitive(output_dir="docs/specs")

        result = await specify.execute(
            {
                "requirement": "Add LRU cache with TTL to LLM pipeline",
                "context": {
                    "architecture": "microservices",
                    "tech_stack": ["Python", "Redis"],
                },
                "feature_name": "llm-cache"
            },
            context=WorkflowContext(workflow_id="feature-123")
        )

        print(f"Spec created: {result['spec_path']}")
        print(f"Coverage: {result['coverage_score']:.1%}")
        print(f"Gaps: {result['gaps']}")
        ```
    """

    def __init__(
        self,
        template_path: str | None = None,
        output_dir: str = "docs/specs",
        min_coverage: float = 0.7,
    ) -> None:
        """Initialize SpecifyPrimitive.

        Args:
            template_path: Path to custom template (uses default if None)
            output_dir: Directory for generated specifications
            min_coverage: Minimum coverage threshold (0.0-1.0)
        """
        super().__init__(name="SpecifyPrimitive")
        self.template_path = template_path
        self.output_dir = Path(output_dir)
        self.min_coverage = min_coverage

        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def _execute_impl(
        self,
        input_data: dict[str, Any],
        context: WorkflowContext,
    ) -> dict[str, Any]:
        """Execute specification generation.

        Args:
            input_data: Must contain "requirement" key with description
            context: Workflow execution context

        Returns:
            Dictionary with spec_path, coverage_score, gaps, sections_completed

        Raises:
            ValueError: If requirement is missing or empty
        """
        # Validate input
        requirement = input_data.get("requirement", "").strip()
        if not requirement:
            raise ValueError("requirement must be provided and non-empty")

        project_context = input_data.get("context", {})
        feature_name = input_data.get("feature_name", self._generate_feature_name(requirement))

        # Generate specification
        spec_content = self._generate_spec(requirement, project_context)

        # Calculate coverage
        coverage_score, gaps, sections_status = self._analyze_coverage(spec_content)

        # Write specification file
        spec_path = self.output_dir / f"{feature_name}.spec.md"
        spec_path.write_text(spec_content, encoding="utf-8")

        return {
            "spec_path": str(spec_path),
            "coverage_score": coverage_score,
            "gaps": gaps,
            "sections_completed": sections_status,
        }

    def _generate_feature_name(self, requirement: str) -> str:
        """Generate feature name from requirement text.

        Args:
            requirement: Feature requirement text

        Returns:
            Kebab-case feature name
        """
        # Simple implementation: take first 5 words, lowercase, replace spaces with hyphens
        words = requirement.lower().split()[:5]
        return "-".join(
            word.strip(".,!?") for word in words if word.isalnum() or word.strip(".,!?")
        )

    def _generate_spec(self, requirement: str, project_context: dict[str, Any]) -> str:
        """Generate specification content.

        Args:
            requirement: Feature requirement
            project_context: Project context information

        Returns:
            Specification content in markdown format
        """
        # Template-based generation (Phase 1: no AI required)
        sections = self._get_spec_template()

        # Fill in what we can from the requirement
        sections["overview"]["problem"] = self._extract_problem(requirement)
        sections["overview"]["solution"] = self._extract_solution(requirement)
        sections["requirements"]["functional"] = self._extract_functional_requirements(requirement)

        # Add project context
        if project_context:
            sections["architecture"]["context"] = str(project_context)

        # Render to markdown
        return self._render_spec_markdown(sections, requirement)

    def _get_spec_template(self) -> dict[str, Any]:
        """Get specification template structure.

        Returns:
            Template structure with sections
        """
        return {
            "overview": {
                "problem": "[CLARIFY]",
                "solution": "[CLARIFY]",
                "success_criteria": [],
            },
            "requirements": {
                "functional": [],
                "non_functional": [],
                "out_of_scope": [],
            },
            "architecture": {
                "components": [],
                "data_model": "[CLARIFY]",
                "api_changes": [],
                "context": "",
            },
            "implementation": {
                "phases": [],
                "dependencies": [],
                "risks": [],
            },
            "testing": {
                "unit_tests": "[CLARIFY]",
                "integration_tests": "[CLARIFY]",
                "performance_tests": "[CLARIFY]",
            },
        }

    def _extract_problem(self, requirement: str) -> str:
        """Extract problem statement from requirement.

        Args:
            requirement: Feature requirement

        Returns:
            Problem statement or [CLARIFY] marker
        """
        # Simple heuristic: if requirement starts with "Add" or "Implement", it's a solution
        # If it starts with "Users need" or "We need to", it might contain problem
        lower = requirement.lower()
        if any(
            lower.startswith(phrase)
            for phrase in ["users need", "we need to", "problem:", "issue:"]
        ):
            return requirement
        return "[CLARIFY]"

    def _extract_solution(self, requirement: str) -> str:
        """Extract proposed solution from requirement.

        Args:
            requirement: Feature requirement

        Returns:
            Proposed solution or [CLARIFY] marker
        """
        # If requirement describes a solution (starts with action verbs), use it
        lower = requirement.lower()
        if any(
            lower.startswith(verb) for verb in ["add", "implement", "create", "build", "integrate"]
        ):
            return requirement
        return "[CLARIFY]"

    def _extract_functional_requirements(self, requirement: str) -> list[str]:
        """Extract functional requirements from requirement text.

        Args:
            requirement: Feature requirement

        Returns:
            List of functional requirements
        """
        # Simple implementation: split by common separators
        separators = [" and ", ", ", "; ", " with ", " including "]
        parts = [requirement]

        for sep in separators:
            new_parts = []
            for part in parts:
                new_parts.extend(part.split(sep))
            parts = new_parts

        # Clean and return
        requirements = [part.strip() for part in parts if part.strip() and len(part) > 10]
        return requirements if requirements else ["[CLARIFY]"]

    def _render_spec_markdown(self, sections: dict[str, Any], requirement: str) -> str:
        """Render specification as markdown.

        Args:
            sections: Specification sections
            requirement: Original requirement

        Returns:
            Markdown formatted specification
        """
        md = f"""# Feature Specification: {requirement[:50]}...

**Status**: Draft
**Created**: {self._get_timestamp()}
**Last Updated**: {self._get_timestamp()}

---

## Overview

### Problem Statement
{sections["overview"]["problem"]}

### Proposed Solution
{sections["overview"]["solution"]}

### Success Criteria
{self._render_list(sections["overview"]["success_criteria"]) or "- [CLARIFY]"}

---

## Requirements

### Functional Requirements
{self._render_list(sections["requirements"]["functional"])}

### Non-Functional Requirements
{self._render_list(sections["requirements"]["non_functional"]) or "- [CLARIFY]"}

### Out of Scope
{self._render_list(sections["requirements"]["out_of_scope"]) or "- [CLARIFY]"}

---

## Architecture

### Component Design
{self._render_list(sections["architecture"]["components"]) or "[CLARIFY]"}

### Data Model
{sections["architecture"]["data_model"]}

### API Changes
{self._render_list(sections["architecture"]["api_changes"]) or "[CLARIFY]"}

{self._render_project_context(sections["architecture"]["context"])}

---

## Implementation Plan

### Phases
{self._render_list(sections["implementation"]["phases"]) or "- [CLARIFY]"}

### Dependencies
{self._render_list(sections["implementation"]["dependencies"]) or "- [CLARIFY]"}

### Risks
{self._render_list(sections["implementation"]["risks"]) or "- [CLARIFY]"}

---

## Testing Strategy

### Unit Tests
{sections["testing"]["unit_tests"]}

### Integration Tests
{sections["testing"]["integration_tests"]}

### Performance Tests
{sections["testing"]["performance_tests"]}

---

## Clarification History

*(No clarifications yet)*

---

## Validation

### Human Review Checklist
- [ ] Architecture aligns with project standards
- [ ] Test strategy is comprehensive
- [ ] Breaking changes are documented
- [ ] Dependencies are identified
- [ ] Risks have mitigations

### Approvals
- [ ] Technical Lead: (pending)
- [ ] Product Owner: (pending)
"""
        return md

    def _render_project_context(self, context: str) -> str:
        """Render project context section if present.

        Args:
            context: Project context string

        Returns:
            Formatted context section or empty string
        """
        if not context:
            return ""
        return f"### Project Context\n{context}\n"

    def _render_list(self, items: list[str]) -> str:
        """Render list items as markdown bullet points.

        Args:
            items: List of items

        Returns:
            Markdown formatted list
        """
        if not items:
            return ""
        return "\n".join(f"- {item}" for item in items)

    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format.

        Returns:
            ISO format timestamp string
        """
        from datetime import datetime

        return datetime.now().strftime("%Y-%m-%d")

    def _analyze_coverage(self, spec_content: str) -> tuple[float, list[str], dict[str, str]]:
        """Analyze specification coverage.

        Args:
            spec_content: Generated specification content

        Returns:
            Tuple of (coverage_score, gaps, sections_status)
        """
        # Count [CLARIFY] markers
        clarify_markers = spec_content.count("[CLARIFY]")

        # Count total sections
        sections = [
            "Problem Statement",
            "Proposed Solution",
            "Success Criteria",
            "Functional Requirements",
            "Non-Functional Requirements",
            "Out of Scope",
            "Component Design",
            "Data Model",
            "API Changes",
            "Phases",
            "Dependencies",
            "Risks",
            "Unit Tests",
            "Integration Tests",
            "Performance Tests",
        ]

        total_sections = len(sections)

        # Calculate coverage (inverse of clarify markers ratio)
        coverage_score = max(0.0, 1.0 - (clarify_markers / total_sections))

        # Identify gaps (sections with [CLARIFY])
        gaps = []
        sections_status = {}

        for section in sections:
            if f"### {section}" in spec_content or f"## {section}" in spec_content:
                # Find content after section header
                start_idx = spec_content.find(f"### {section}")
                if start_idx == -1:
                    start_idx = spec_content.find(f"## {section}")

                # Look for [CLARIFY] in next 500 characters
                end_idx = start_idx + 500
                section_content = spec_content[start_idx:end_idx]

                if "[CLARIFY]" in section_content:
                    gaps.append(section)
                    sections_status[section] = "incomplete"
                else:
                    sections_status[section] = "complete"
            else:
                sections_status[section] = "missing"

        return coverage_score, gaps, sections_status
