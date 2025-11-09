"""Branch validation primitive for TTA narrative engine.

This module validates branching story choices for consistency, meaningfulness,
and alignment with characters and universe rules.
"""

from dataclasses import dataclass, field
from enum import Enum

from ..core import TTAContext, TTAPrimitive, ValidationError


class IssueSeverity(Enum):
    """Severity level of validation issues."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class ValidationIssue:
    """A validation issue found in a branch."""

    severity: IssueSeverity
    category: str  # "consistency", "meaningfulness", "character", "universe"
    message: str
    suggested_fix: str | None = None


@dataclass
class BranchProposal:
    """Input for branch validation."""

    universe_id: str
    branch_description: str
    choice_text: str
    affected_characters: list[str]
    timeline_context: list[str] = field(default_factory=list)  # Recent events
    universe_rules: dict[str, str] = field(default_factory=dict)
    parent_branch_id: str | None = None


@dataclass
class BranchValidation:
    """Output from branch validation."""

    is_valid: bool
    overall_score: float  # 0.0-1.0
    consistency_score: float
    meaningfulness_score: float
    character_alignment_score: float
    universe_rules_score: float
    issues: list[ValidationIssue]
    suggestions: list[str]
    dead_end_risk: float  # 0.0-1.0


class BranchValidatorPrimitive(TTAPrimitive[BranchProposal, BranchValidation]):
    """Validate branching narrative choices.

    This primitive:
    1. Checks consistency with established timeline
    2. Assesses meaningfulness of choices
    3. Validates character alignment
    4. Enforces universe rules
    5. Detects potential dead ends

    Features:
    - Multi-criteria validation
    - Severity-graded issues
    - Actionable suggestions
    - Dead-end detection
    - Rule enforcement
    """

    # Validation thresholds
    MIN_VALID_SCORE = 0.6
    MIN_CHOICE_LENGTH = 10
    MAX_CHOICE_LENGTH = 200

    def __init__(self, name: str = "BranchValidator") -> None:
        """Initialize branch validator.

        Args:
            name: Name for this primitive instance
        """
        super().__init__(name)
        # Track validated branches for consistency checks
        self._validated_branches: dict[str, BranchProposal] = {}

    async def execute(
        self,
        input_data: BranchProposal,
        context: TTAContext,
    ) -> BranchValidation:
        """Validate a branch proposal.

        Args:
            input_data: Branch proposal to validate
            context: Workflow context

        Returns:
            Validation result with scores and issues

        Raises:
            ValidationError: If proposal is invalid
        """
        # Validate input
        self._validate_proposal(input_data)

        # Collect validation issues
        issues: list[ValidationIssue] = []

        # Check consistency with timeline
        consistency_score, consistency_issues = self._check_consistency(input_data)
        issues.extend(consistency_issues)

        # Assess meaningfulness
        meaningfulness_score, meaningfulness_issues = self._check_meaningfulness(
            input_data
        )
        issues.extend(meaningfulness_issues)

        # Validate character alignment
        character_score, character_issues = self._check_character_alignment(input_data)
        issues.extend(character_issues)

        # Check universe rules
        universe_score, universe_issues = self._check_universe_rules(input_data)
        issues.extend(universe_issues)

        # Detect dead ends
        dead_end_risk = self._assess_dead_end_risk(input_data)

        # Calculate overall score
        overall_score = (
            consistency_score * 0.3
            + meaningfulness_score * 0.25
            + character_score * 0.25
            + universe_score * 0.2
        )

        # Determine if valid
        is_valid = overall_score >= self.MIN_VALID_SCORE and not any(
            issue.severity == IssueSeverity.ERROR for issue in issues
        )

        # Generate suggestions
        suggestions = self._generate_suggestions(issues, input_data)

        # Store validated branch
        if is_valid:
            branch_key = f"{input_data.universe_id}:{input_data.choice_text[:50]}"
            self._validated_branches[branch_key] = input_data

        return BranchValidation(
            is_valid=is_valid,
            overall_score=overall_score,
            consistency_score=consistency_score,
            meaningfulness_score=meaningfulness_score,
            character_alignment_score=character_score,
            universe_rules_score=universe_score,
            issues=issues,
            suggestions=suggestions,
            dead_end_risk=dead_end_risk,
        )

    def _validate_proposal(self, proposal: BranchProposal) -> None:
        """Validate proposal input.

        Args:
            proposal: Proposal to validate

        Raises:
            ValidationError: If proposal is invalid
        """
        if not proposal.universe_id:
            raise ValidationError("universe_id is required")

        if not proposal.branch_description:
            raise ValidationError("branch_description is required")

        if not proposal.choice_text:
            raise ValidationError("choice_text is required")

        if len(proposal.choice_text) < self.MIN_CHOICE_LENGTH:
            raise ValidationError(
                f"choice_text must be at least {self.MIN_CHOICE_LENGTH} characters"
            )

        if len(proposal.choice_text) > self.MAX_CHOICE_LENGTH:
            raise ValidationError(
                f"choice_text must be at most {self.MAX_CHOICE_LENGTH} characters"
            )

    def _check_consistency(
        self, proposal: BranchProposal
    ) -> tuple[float, list[ValidationIssue]]:
        """Check consistency with timeline context.

        Args:
            proposal: Branch to validate

        Returns:
            Tuple of (consistency_score, issues)
        """
        issues: list[ValidationIssue] = []
        score = 1.0

        # Check if choice references non-existent events
        choice_lower = proposal.choice_text.lower()
        for event in proposal.timeline_context:
            event_lower = event.lower()
            # Simple keyword check (in production, use NLP)
            if "after" in choice_lower and event_lower not in choice_lower:
                # Choice might reference events not in timeline
                continue

        # Check for temporal paradoxes
        if "before" in choice_lower and "after" in choice_lower:
            issues.append(
                ValidationIssue(
                    severity=IssueSeverity.WARNING,
                    category="consistency",
                    message="Choice contains temporal ambiguity (before/after)",
                    suggested_fix="Clarify temporal sequence in choice text",
                )
            )
            score -= 0.2

        # Check if contradicts parent branch
        if proposal.parent_branch_id:
            parent_key = f"{proposal.universe_id}:{proposal.parent_branch_id[:50]}"
            if parent_key in self._validated_branches:
                parent = self._validated_branches[parent_key]
                # Check for contradictions (simplified)
                if (
                    "not" in proposal.choice_text.lower()
                    and parent.choice_text[:20] in proposal.choice_text
                ):
                    issues.append(
                        ValidationIssue(
                            severity=IssueSeverity.ERROR,
                            category="consistency",
                            message="Choice contradicts parent branch decision",
                            suggested_fix="Remove contradiction or adjust parent branch",
                        )
                    )
                    score -= 0.5

        return max(0.0, score), issues

    def _check_meaningfulness(
        self, proposal: BranchProposal
    ) -> tuple[float, list[ValidationIssue]]:
        """Assess meaningfulness of the branch.

        Args:
            proposal: Branch to validate

        Returns:
            Tuple of (meaningfulness_score, issues)
        """
        issues: list[ValidationIssue] = []
        score = 1.0

        # Check if choice is too vague
        vague_phrases = ["something", "maybe", "perhaps", "might"]
        vague_count = sum(
            1 for phrase in vague_phrases if phrase in proposal.choice_text.lower()
        )

        if vague_count >= 2:
            issues.append(
                ValidationIssue(
                    severity=IssueSeverity.WARNING,
                    category="meaningfulness",
                    message="Choice text is vague and lacks specific action",
                    suggested_fix="Replace vague language with concrete actions",
                )
            )
            score -= 0.3

        # Check if choice has clear consequences
        consequence_indicators = [
            "leads to",
            "results in",
            "causes",
            "triggers",
            "reveals",
        ]
        has_consequence = any(
            indicator in proposal.branch_description.lower()
            for indicator in consequence_indicators
        )

        if not has_consequence:
            issues.append(
                ValidationIssue(
                    severity=IssueSeverity.INFO,
                    category="meaningfulness",
                    message="Branch description doesn't clearly state consequences",
                    suggested_fix="Add explicit consequence description",
                )
            )
            score -= 0.1

        # Check for interesting tension/conflict
        if len(proposal.affected_characters) == 0:
            issues.append(
                ValidationIssue(
                    severity=IssueSeverity.WARNING,
                    category="meaningfulness",
                    message="No characters affected - may lack dramatic impact",
                    suggested_fix="Consider involving at least one character",
                )
            )
            score -= 0.2

        return max(0.0, score), issues

    def _check_character_alignment(
        self, proposal: BranchProposal
    ) -> tuple[float, list[ValidationIssue]]:
        """Check if choice aligns with character traits.

        Args:
            proposal: Branch to validate

        Returns:
            Tuple of (alignment_score, issues)
        """
        issues: list[ValidationIssue] = []
        score = 1.0

        # Check if characters are mentioned appropriately
        choice_lower = proposal.choice_text.lower()

        for character in proposal.affected_characters:
            char_lower = character.lower()

            # Check if character is mentioned in choice
            if char_lower not in choice_lower:
                issues.append(
                    ValidationIssue(
                        severity=IssueSeverity.INFO,
                        category="character",
                        message=f"Affected character '{character}' not mentioned in choice",
                        suggested_fix=f"Explicitly mention {character}'s role in the choice",
                    )
                )
                score -= 0.1

        # Check for character agency
        passive_indicators = ["is forced", "has no choice", "must"]
        passive_count = sum(
            1 for phrase in passive_indicators if phrase in choice_lower
        )

        if passive_count >= 2:
            issues.append(
                ValidationIssue(
                    severity=IssueSeverity.WARNING,
                    category="character",
                    message="Choice removes character agency",
                    suggested_fix="Rephrase to give character meaningful choice",
                )
            )
            score -= 0.3

        return max(0.0, score), issues

    def _check_universe_rules(
        self, proposal: BranchProposal
    ) -> tuple[float, list[ValidationIssue]]:
        """Check if choice violates universe rules.

        Args:
            proposal: Branch to validate

        Returns:
            Tuple of (universe_score, issues)
        """
        issues: list[ValidationIssue] = []
        score = 1.0

        # Check each rule
        choice_lower = proposal.choice_text.lower()
        description_lower = proposal.branch_description.lower()

        for rule_name, rule_text in proposal.universe_rules.items():
            rule_lower = rule_text.lower()

            # Check for rule violations (simplified keyword matching)
            # In production, use semantic analysis

            # Example: "no magic" rule
            if "no" in rule_lower and "magic" in rule_lower:
                if "magic" in choice_lower or "spell" in choice_lower:
                    issues.append(
                        ValidationIssue(
                            severity=IssueSeverity.ERROR,
                            category="universe",
                            message=f"Choice violates rule: {rule_name} ({rule_text})",
                            suggested_fix="Remove magic references or adjust universe rules",
                        )
                    )
                    score -= 0.5

            # Example: "realistic setting" rule
            if "realistic" in rule_lower:
                unrealistic_terms = ["dragon", "wizard", "teleport", "supernatural"]
                for term in unrealistic_terms:
                    if term in choice_lower or term in description_lower:
                        issues.append(
                            ValidationIssue(
                                severity=IssueSeverity.ERROR,
                                category="universe",
                                message=f"Choice includes unrealistic element: {term}",
                                suggested_fix="Replace with realistic alternative",
                            )
                        )
                        score -= 0.3
                        break

        return max(0.0, score), issues

    def _assess_dead_end_risk(self, proposal: BranchProposal) -> float:
        """Assess risk that branch leads to narrative dead end.

        Args:
            proposal: Branch to assess

        Returns:
            Dead end risk score (0.0-1.0, higher = more risk)
        """
        risk = 0.0

        # Check for definitive endings
        ending_phrases = ["the end", "game over", "dies", "destroys everything"]
        if any(phrase in proposal.choice_text.lower() for phrase in ending_phrases):
            risk += 0.8

        # Check for no affected characters (hard to continue)
        if len(proposal.affected_characters) == 0:
            risk += 0.3

        # Check for no timeline context (disconnected)
        if len(proposal.timeline_context) == 0:
            risk += 0.2

        # Check for very specific, limiting outcomes
        limiting_phrases = ["only", "never", "impossible", "final"]
        limiting_count = sum(
            1
            for phrase in limiting_phrases
            if phrase in proposal.branch_description.lower()
        )
        risk += limiting_count * 0.1

        return min(1.0, risk)

    def _generate_suggestions(
        self, issues: list[ValidationIssue], proposal: BranchProposal
    ) -> list[str]:
        """Generate actionable suggestions for improvement.

        Args:
            issues: Validation issues found
            proposal: Original proposal

        Returns:
            List of suggestions
        """
        suggestions: list[str] = []

        # Aggregate suggestions from issues
        for issue in issues:
            if issue.suggested_fix:
                suggestions.append(f"[{issue.category}] {issue.suggested_fix}")

        # Add general suggestions based on scores
        error_count = sum(
            1 for issue in issues if issue.severity == IssueSeverity.ERROR
        )

        if error_count == 0 and len(issues) > 0:
            suggestions.append(
                "Address warnings to improve branch quality before implementation"
            )

        if len(proposal.affected_characters) == 0:
            suggestions.append("Consider involving at least one character for impact")

        if len(proposal.timeline_context) < 2:
            suggestions.append(
                "Add more timeline context for better consistency validation"
            )

        return suggestions

    def get_validated_branches(self, universe_id: str) -> list[BranchProposal]:
        """Get all validated branches for a universe.

        Args:
            universe_id: Universe identifier

        Returns:
            List of validated branch proposals
        """
        return [
            branch
            for key, branch in self._validated_branches.items()
            if key.startswith(f"{universe_id}:")
        ]

    def clear_validated_branches(self, universe_id: str | None = None) -> None:
        """Clear validated branch cache.

        Args:
            universe_id: If provided, clear only branches for this universe.
                        If None, clear all.
        """
        if universe_id is None:
            self._validated_branches.clear()
        else:
            keys_to_remove = [
                key
                for key in self._validated_branches
                if key.startswith(f"{universe_id}:")
            ]
            for key in keys_to_remove:
                del self._validated_branches[key]
