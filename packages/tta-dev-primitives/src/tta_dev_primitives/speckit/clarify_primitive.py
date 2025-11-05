"""ClarifyPrimitive - Iterative refinement through structured questions.

This primitive takes an incomplete specification and iteratively refines it
by generating targeted questions for underspecified sections, accepting answers,
and updating the specification until target coverage is reached.
"""

from pathlib import Path
from typing import Any

from tta_dev_primitives import WorkflowContext
from tta_dev_primitives.observability import InstrumentedPrimitive


class ClarifyPrimitive(InstrumentedPrimitive[dict[str, Any], dict[str, Any]]):
    """Refine specifications through iterative clarification.

    This primitive analyzes gaps in a specification, generates structured
    questions for each gap, accepts answers, and updates the spec accordingly.
    It continues iterating until target coverage is reached or max iterations.

    Args:
        max_iterations: Maximum clarification rounds (default: 3)
        target_coverage: Target coverage score to achieve (default: 0.9)
        questions_per_gap: Number of questions per gap (default: 2)

    Input:
        - spec_path (str): Path to specification file
        - gaps (list[str]): List of underspecified sections
        - current_coverage (float): Current coverage score
        - answers (dict[str, str], optional): Pre-provided answers

    Output:
        - updated_spec_path (str): Path to updated specification
        - final_coverage (float): Coverage after refinement
        - coverage_improvement (float): Change in coverage
        - iterations_used (int): Number of iterations performed
        - remaining_gaps (list[str]): Gaps still needing clarification
        - clarification_history (list[dict]): History of questions/answers
        - questions (list[dict], optional): Questions for next iteration

    Example:
        ```python
        clarify = ClarifyPrimitive(max_iterations=3, target_coverage=0.9)

        # Interactive mode (prompts for answers)
        result = await clarify.execute(
            {
                "spec_path": "docs/specs/feature.spec.md",
                "gaps": ["Problem Statement", "Data Model"],
                "current_coverage": 0.13
            },
            context=WorkflowContext(workflow_id="clarify-001")
        )

        # Batch mode (pre-provided answers)
        result = await clarify.execute(
            {
                "spec_path": "docs/specs/feature.spec.md",
                "gaps": ["Problem Statement"],
                "current_coverage": 0.13,
                "answers": {
                    "Problem Statement": "Users need faster response times..."
                }
            },
            context
        )

        print(f"Coverage: {result['current_coverage']:.1%} → {result['final_coverage']:.1%}")
        print(f"Improvement: +{result['coverage_improvement']:.1%}")
        ```
    """

    def __init__(
        self,
        max_iterations: int = 3,
        target_coverage: float = 0.9,
        questions_per_gap: int = 2,
    ) -> None:
        """Initialize ClarifyPrimitive.

        Args:
            max_iterations: Maximum clarification rounds
            target_coverage: Target coverage to achieve (0.0-1.0)
            questions_per_gap: Questions to generate per gap
        """
        super().__init__(name="ClarifyPrimitive")
        self.max_iterations = max_iterations
        self.target_coverage = target_coverage
        self.questions_per_gap = questions_per_gap

    async def _execute_impl(
        self,
        input_data: dict[str, Any],
        context: WorkflowContext,
    ) -> dict[str, Any]:
        """Execute iterative clarification.

        Args:
            input_data: Must contain spec_path, gaps, current_coverage
            context: Workflow execution context

        Returns:
            Dictionary with updated_spec_path, final_coverage, improvements, history

        Raises:
            ValueError: If required fields are missing
            FileNotFoundError: If spec_path doesn't exist
        """
        # Validate input
        spec_path = input_data.get("spec_path")
        if not spec_path:
            raise ValueError("spec_path is required")

        spec_file = Path(spec_path)
        if not spec_file.exists():
            raise FileNotFoundError(f"Specification not found: {spec_path}")

        gaps = input_data.get("gaps", [])
        current_coverage = input_data.get("current_coverage", 0.0)
        pre_answers = input_data.get("answers", {})

        # Initialize tracking
        iteration = 0
        clarification_history: list[dict[str, Any]] = []
        remaining_gaps = list(gaps)

        # Read initial spec
        spec_content = spec_file.read_text(encoding="utf-8")

        # Iterative refinement loop
        while iteration < self.max_iterations and remaining_gaps:
            # Check if target coverage reached
            if current_coverage >= self.target_coverage:
                break

            iteration += 1

            # Generate questions for gaps
            questions = self._generate_questions(remaining_gaps, spec_content)

            # Get answers (either from pre_answers or would prompt user in interactive mode)
            answers = self._get_answers(questions, pre_answers, iteration)

            # Update specification with answers
            spec_content = self._update_specification(spec_content, questions, answers, iteration)

            # Recalculate coverage and remaining gaps
            new_coverage, new_gaps = self._analyze_updated_spec(spec_content)

            # Record iteration
            clarification_history.append(
                {
                    "iteration": iteration,
                    "questions": questions,
                    "answers": answers,
                    "coverage_before": current_coverage,
                    "coverage_after": new_coverage,
                    "gaps_addressed": len(remaining_gaps) - len(new_gaps),
                }
            )

            # Update state
            current_coverage = new_coverage
            remaining_gaps = new_gaps

        # Write updated specification
        spec_file.write_text(spec_content, encoding="utf-8")

        # Calculate final metrics
        initial_coverage = input_data.get("current_coverage", 0.0)
        coverage_improvement = current_coverage - initial_coverage

        return {
            "updated_spec_path": str(spec_file),
            "final_coverage": current_coverage,
            "coverage_improvement": coverage_improvement,
            "iterations_used": iteration,
            "remaining_gaps": remaining_gaps,
            "clarification_history": clarification_history,
            "target_reached": current_coverage >= self.target_coverage,
        }

    def _generate_questions(self, gaps: list[str], spec_content: str) -> list[dict[str, Any]]:
        """Generate structured questions for each gap.

        Args:
            gaps: List of section names with gaps
            spec_content: Current specification content

        Returns:
            List of question dictionaries with section, question, and type
        """
        questions = []

        for gap in gaps[:5]:  # Limit to 5 gaps per iteration
            # Generate questions based on section type
            section_questions = self._get_questions_for_section(gap, spec_content)
            questions.extend(section_questions)

        return questions

    def _get_questions_for_section(self, section: str, spec_content: str) -> list[dict[str, Any]]:
        """Get targeted questions for specific section.

        Args:
            section: Section name
            spec_content: Current spec content

        Returns:
            List of question dictionaries for this section
        """
        # Template-based questions (Phase 1: no AI required)
        question_templates = {
            "Problem Statement": [
                {
                    "section": section,
                    "question": "What specific problem does this feature solve?",
                    "type": "open",
                    "hint": "Describe the pain point or gap in current functionality",
                },
                {
                    "section": section,
                    "question": "Who are the primary users affected by this problem?",
                    "type": "open",
                    "hint": "E.g., developers, end users, operators",
                },
            ],
            "Proposed Solution": [
                {
                    "section": section,
                    "question": "What is the high-level approach to solving this problem?",
                    "type": "open",
                    "hint": "Describe the solution strategy",
                },
            ],
            "Success Criteria": [
                {
                    "section": section,
                    "question": "What measurable outcomes define success?",
                    "type": "open",
                    "hint": "E.g., performance metrics, user satisfaction, test coverage",
                },
            ],
            "Functional Requirements": [
                {
                    "section": section,
                    "question": "What are the core functional requirements?",
                    "type": "open",
                    "hint": "List specific features and capabilities",
                },
            ],
            "Non-Functional Requirements": [
                {
                    "section": section,
                    "question": "What are the performance, security, and scalability requirements?",
                    "type": "open",
                    "hint": "E.g., latency < 100ms, supports 1000 RPS",
                },
            ],
            "Data Model": [
                {
                    "section": section,
                    "question": "What data structures or database schema are needed?",
                    "type": "open",
                    "hint": "Describe entities, relationships, and key fields",
                },
            ],
            "Component Design": [
                {
                    "section": section,
                    "question": "What are the main components and their responsibilities?",
                    "type": "open",
                    "hint": "List components and their interactions",
                },
            ],
            "API Changes": [
                {
                    "section": section,
                    "question": "What API endpoints or interfaces will be added/modified?",
                    "type": "open",
                    "hint": "List new or changed APIs with signatures",
                },
            ],
            "Dependencies": [
                {
                    "section": section,
                    "question": "What external libraries, services, or features does this depend on?",
                    "type": "open",
                    "hint": "List dependencies with versions if known",
                },
            ],
            "Risks": [
                {
                    "section": section,
                    "question": "What are the main technical or project risks?",
                    "type": "open",
                    "hint": "Consider complexity, unknowns, dependencies",
                },
            ],
            "Unit Tests": [
                {
                    "section": section,
                    "question": "What unit test scenarios should be covered?",
                    "type": "open",
                    "hint": "List test cases for core functionality",
                },
            ],
            "Integration Tests": [
                {
                    "section": section,
                    "question": "What integration test scenarios are needed?",
                    "type": "open",
                    "hint": "Test interactions between components",
                },
            ],
            "Performance Tests": [
                {
                    "section": section,
                    "question": "What performance characteristics need testing?",
                    "type": "open",
                    "hint": "E.g., load testing, stress testing, benchmarks",
                },
            ],
        }

        # Return questions for this section (or default questions if not mapped)
        return question_templates.get(
            section,
            [
                {
                    "section": section,
                    "question": f"Please provide details for the {section} section",
                    "type": "open",
                    "hint": "Add relevant information to complete this section",
                }
            ],
        )[: self.questions_per_gap]

    def _get_answers(
        self,
        questions: list[dict[str, Any]],
        pre_answers: dict[str, str],
        iteration: int,
    ) -> dict[str, str]:
        """Get answers to questions.

        Args:
            questions: List of questions
            pre_answers: Pre-provided answers dictionary
            iteration: Current iteration number

        Returns:
            Dictionary mapping section to answer
        """
        answers: dict[str, str] = {}

        # In batch mode, use pre-provided answers
        if pre_answers:
            for question in questions:
                section = question["section"]
                if section in pre_answers:
                    answers[section] = pre_answers[section]
                else:
                    # Use placeholder for missing answers
                    answers[section] = f"[CLARIFY in iteration {iteration + 1}]"
        else:
            # Interactive mode would prompt here
            # For now, use placeholders (will be enhanced in Phase 2)
            for question in questions:
                section = question["section"]
                answers[section] = f"[CLARIFY in iteration {iteration + 1}]"

        return answers

    def _update_specification(
        self,
        spec_content: str,
        questions: list[dict[str, Any]],
        answers: dict[str, str],
        iteration: int,
    ) -> str:
        """Update specification with answers.

        Args:
            spec_content: Current specification content
            questions: Questions asked
            answers: Answers provided
            iteration: Current iteration number

        Returns:
            Updated specification content
        """
        updated_content = spec_content

        # Update each section with answers
        for question in questions:
            section = question["section"]
            if section not in answers:
                continue

            answer = answers[section]

            # Only replace if answer is not a placeholder
            if answer.startswith("[CLARIFY"):
                continue

            # Find and replace [CLARIFY] in the section
            # Look for section header patterns
            section_patterns = [
                f"### {section}\n[CLARIFY]",
                f"### {section}\n- [CLARIFY]",
                f"## {section}\n[CLARIFY]",
            ]

            for pattern in section_patterns:
                if pattern in updated_content:
                    replacement = f"### {section}\n{answer}"
                    updated_content = updated_content.replace(pattern, replacement, 1)
                    break

        # Add clarification history entry
        history_marker = "## Clarification History\n\n*(No clarifications yet)*"
        if history_marker in updated_content:
            history_entry = f"""## Clarification History

### Iteration {iteration}

**Questions Asked:**
{self._format_questions(questions)}

**Answers Provided:**
{self._format_answers(answers)}
"""
            updated_content = updated_content.replace(history_marker, history_entry)
        else:
            # Append to existing history
            history_section = "## Clarification History\n"
            if history_section in updated_content:
                # Find end of clarification history
                validation_marker = "\n---\n\n## Validation"
                if validation_marker in updated_content:
                    idx = updated_content.index(validation_marker)
                    history_entry = f"""
### Iteration {iteration}

**Questions Asked:**
{self._format_questions(questions)}

**Answers Provided:**
{self._format_answers(answers)}
"""
                    updated_content = updated_content[:idx] + history_entry + updated_content[idx:]

        return updated_content

    def _format_questions(self, questions: list[dict[str, Any]]) -> str:
        """Format questions for history.

        Args:
            questions: List of question dictionaries

        Returns:
            Formatted question list
        """
        formatted = []
        for i, q in enumerate(questions, 1):
            formatted.append(f"{i}. **{q['section']}**: {q['question']}")
        return "\n".join(formatted)

    def _format_answers(self, answers: dict[str, str]) -> str:
        """Format answers for history.

        Args:
            answers: Dictionary of answers

        Returns:
            Formatted answer list
        """
        formatted = []
        for section, answer in answers.items():
            formatted.append(f"- **{section}**: {answer}")
        return "\n".join(formatted)

    def _analyze_updated_spec(self, spec_content: str) -> tuple[float, list[str]]:
        """Analyze updated specification for coverage and gaps.

        Args:
            spec_content: Updated specification content

        Returns:
            Tuple of (coverage_score, remaining_gaps)
        """
        # Count [CLARIFY] markers (same logic as SpecifyPrimitive)
        clarify_markers = spec_content.count("[CLARIFY]")

        # Total sections
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
        coverage = max(0.0, 1.0 - (clarify_markers / total_sections))

        # Identify remaining gaps
        gaps = []
        for section in sections:
            # Check if section has [CLARIFY]
            section_patterns = [f"### {section}", f"## {section}"]
            for pattern in section_patterns:
                if pattern in spec_content:
                    # Find content after header
                    start = spec_content.find(pattern)

                    # Find next section header to avoid looking too far ahead
                    next_section_idx = len(spec_content)
                    for next_pattern in ["###", "##", "---"]:
                        idx = spec_content.find(next_pattern, start + len(pattern))
                        if idx != -1 and idx < next_section_idx:
                            next_section_idx = idx

                    # Check only within this section's content
                    section_content = spec_content[start:next_section_idx]
                    if "[CLARIFY]" in section_content:
                        gaps.append(section)
                    break

        return coverage, gaps
