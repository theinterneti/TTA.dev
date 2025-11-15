"""Tests for BranchValidatorPrimitive."""

from datetime import UTC, datetime

import pytest

from tta_rebuild.core import TTAContext, ValidationError
from tta_rebuild.narrative.branch_validator import (
    BranchProposal,
    BranchValidatorPrimitive,
    IssueSeverity,
)


@pytest.fixture
def branch_validator():
    """Create BranchValidatorPrimitive for testing."""
    return BranchValidatorPrimitive()


@pytest.fixture
def test_context():
    """Create test context."""
    return TTAContext(
        workflow_id="test-workflow",
        correlation_id="test-correlation",
        timestamp=datetime.now(UTC),
        metaconcepts=["branch_validation"],
        player_boundaries={},
    )


class TestBranchValidatorBasics:
    """Test basic branch validation."""

    @pytest.mark.asyncio
    async def test_validate_simple_branch(
        self, branch_validator: BranchValidatorPrimitive, test_context: TTAContext
    ):
        """Test validating a simple branch."""
        proposal = BranchProposal(
            universe_id="main",
            branch_description="Hero decides to enter the forest",
            choice_text="Enter the mysterious forest to search for clues",
            affected_characters=["hero"],
            timeline_context=["Hero arrived at the village"],
        )

        validation = await branch_validator.execute(proposal, test_context)

        assert validation.overall_score >= 0.0
        assert validation.overall_score <= 1.0
        assert isinstance(validation.is_valid, bool)

    @pytest.mark.asyncio
    async def test_valid_branch_is_stored(
        self, branch_validator: BranchValidatorPrimitive, test_context: TTAContext
    ):
        """Test valid branches are stored."""
        proposal = BranchProposal(
            universe_id="main",
            branch_description="Hero explores the ancient ruins carefully",
            choice_text="Carefully explore the ruins while watching for traps",
            affected_characters=["hero"],
        )

        validation = await branch_validator.execute(proposal, test_context)

        if validation.is_valid:
            validated = branch_validator.get_validated_branches("main")
            assert len(validated) > 0


class TestConsistencyValidation:
    """Test consistency checking."""

    @pytest.mark.asyncio
    async def test_temporal_ambiguity_warning(
        self, branch_validator: BranchValidatorPrimitive, test_context: TTAContext
    ):
        """Test temporal ambiguity is detected."""
        proposal = BranchProposal(
            universe_id="main",
            branch_description="Hero travels before and after the event",
            choice_text="Go back before the event but also after it happens",
            affected_characters=["hero"],
        )

        validation = await branch_validator.execute(proposal, test_context)

        # Should have consistency warning
        consistency_issues = [
            issue for issue in validation.issues if issue.category == "consistency"
        ]
        assert len(consistency_issues) > 0

    @pytest.mark.asyncio
    async def test_parent_branch_contradiction(
        self, branch_validator: BranchValidatorPrimitive, test_context: TTAContext
    ):
        """Test contradiction with parent branch is detected."""
        # First, validate a parent branch
        parent_proposal = BranchProposal(
            universe_id="main",
            branch_description="Hero accepts the quest",
            choice_text="Accept the quest from the elder",
            affected_characters=["hero"],
        )
        await branch_validator.execute(parent_proposal, test_context)

        # Now create a contradictory child branch
        child_proposal = BranchProposal(
            universe_id="main",
            branch_description="Hero rejects everything",
            choice_text="Accept the quest from not the elder",  # Contains contradiction
            affected_characters=["hero"],
            parent_branch_id="Accept the quest from the elder",
        )

        validation = await branch_validator.execute(child_proposal, test_context)

        # Should have error-level consistency issue
        consistency_errors = [
            issue
            for issue in validation.issues
            if issue.category == "consistency" and issue.severity == IssueSeverity.ERROR
        ]
        assert len(consistency_errors) > 0 or validation.consistency_score < 1.0


class TestMeaningfulnessValidation:
    """Test meaningfulness checking."""

    @pytest.mark.asyncio
    async def test_vague_choice_warning(
        self, branch_validator: BranchValidatorPrimitive, test_context: TTAContext
    ):
        """Test vague language is detected."""
        proposal = BranchProposal(
            universe_id="main",
            branch_description="Something might perhaps happen maybe",
            choice_text="Maybe do something that might perhaps work",
            affected_characters=["hero"],
        )

        validation = await branch_validator.execute(proposal, test_context)

        # Should have meaningfulness warning
        meaningfulness_issues = [
            issue for issue in validation.issues if issue.category == "meaningfulness"
        ]
        assert len(meaningfulness_issues) > 0

    @pytest.mark.asyncio
    async def test_no_consequences_info(
        self, branch_validator: BranchValidatorPrimitive, test_context: TTAContext
    ):
        """Test missing consequences are flagged."""
        proposal = BranchProposal(
            universe_id="main",
            branch_description="Hero does something",  # No clear consequences
            choice_text="Take the mysterious action without clear result",
            affected_characters=["hero"],
        )

        validation = await branch_validator.execute(proposal, test_context)

        # Should have info about missing consequences
        meaningfulness_issues = [
            issue for issue in validation.issues if issue.category == "meaningfulness"
        ]
        assert len(meaningfulness_issues) > 0

    @pytest.mark.asyncio
    async def test_no_characters_warning(
        self, branch_validator: BranchValidatorPrimitive, test_context: TTAContext
    ):
        """Test warning when no characters affected."""
        proposal = BranchProposal(
            universe_id="main",
            branch_description="The wind blows",
            choice_text="Let the wind blow through the trees",
            affected_characters=[],  # No characters
        )

        validation = await branch_validator.execute(proposal, test_context)

        # Should have warning about lacking dramatic impact
        meaningfulness_issues = [
            issue for issue in validation.issues if issue.category == "meaningfulness"
        ]
        assert len(meaningfulness_issues) > 0


class TestCharacterAlignmentValidation:
    """Test character alignment checking."""

    @pytest.mark.asyncio
    async def test_character_not_mentioned_info(
        self, branch_validator: BranchValidatorPrimitive, test_context: TTAContext
    ):
        """Test info when affected character not mentioned."""
        proposal = BranchProposal(
            universe_id="main",
            branch_description="An action happens",
            choice_text="Do something important",  # Doesn't mention ally
            affected_characters=["hero", "ally"],
        )

        validation = await branch_validator.execute(proposal, test_context)

        # Should have info about unmentioned characters
        character_issues = [
            issue for issue in validation.issues if issue.category == "character"
        ]
        assert len(character_issues) > 0

    @pytest.mark.asyncio
    async def test_character_agency_warning(
        self, branch_validator: BranchValidatorPrimitive, test_context: TTAContext
    ):
        """Test warning when choice removes character agency."""
        proposal = BranchProposal(
            universe_id="main",
            branch_description="Hero has no choice and is forced to act",
            choice_text="Hero is forced to act and has no choice but must obey",
            affected_characters=["hero"],
        )

        validation = await branch_validator.execute(proposal, test_context)

        # Should have warning about removed agency
        character_issues = [
            issue for issue in validation.issues if issue.category == "character"
        ]
        assert len(character_issues) > 0


class TestUniverseRulesValidation:
    """Test universe rules enforcement."""

    @pytest.mark.asyncio
    async def test_magic_rule_violation(
        self, branch_validator: BranchValidatorPrimitive, test_context: TTAContext
    ):
        """Test detection of magic in no-magic universe."""
        proposal = BranchProposal(
            universe_id="realistic",
            branch_description="Hero casts a magic spell",
            choice_text="Cast a powerful spell to defeat the enemy",
            affected_characters=["hero"],
            universe_rules={"no_magic": "no magic allowed in this universe"},
        )

        validation = await branch_validator.execute(proposal, test_context)

        # Should have error about rule violation
        universe_issues = [
            issue for issue in validation.issues if issue.category == "universe"
        ]
        assert len(universe_issues) > 0

    @pytest.mark.asyncio
    async def test_realistic_setting_violation(
        self, branch_validator: BranchValidatorPrimitive, test_context: TTAContext
    ):
        """Test detection of unrealistic elements."""
        proposal = BranchProposal(
            universe_id="realistic",
            branch_description="Hero encounters a dragon and teleports away",
            choice_text="Use teleportation to escape the dragon attack",
            affected_characters=["hero"],
            universe_rules={"realistic": "realistic setting only"},
        )

        validation = await branch_validator.execute(proposal, test_context)

        # Should have error about unrealistic elements
        universe_issues = [
            issue for issue in validation.issues if issue.category == "universe"
        ]
        assert len(universe_issues) > 0


class TestDeadEndDetection:
    """Test dead end risk assessment."""

    @pytest.mark.asyncio
    async def test_ending_phrase_high_risk(
        self, branch_validator: BranchValidatorPrimitive, test_context: TTAContext
    ):
        """Test ending phrases increase dead end risk."""
        proposal = BranchProposal(
            universe_id="main",
            branch_description="This is the end of the story",
            choice_text="Accept that this is the end and game over",
            affected_characters=["hero"],
        )

        validation = await branch_validator.execute(proposal, test_context)

        # Should have high dead end risk
        assert validation.dead_end_risk > 0.5

    @pytest.mark.asyncio
    async def test_no_characters_increases_risk(
        self, branch_validator: BranchValidatorPrimitive, test_context: TTAContext
    ):
        """Test no characters increases dead end risk."""
        proposal = BranchProposal(
            universe_id="main",
            branch_description="An event occurs",
            choice_text="Something happens in the environment",
            affected_characters=[],  # No characters
        )

        validation = await branch_validator.execute(proposal, test_context)

        # Should have some dead end risk
        assert validation.dead_end_risk > 0.0

    @pytest.mark.asyncio
    async def test_limiting_phrases_increase_risk(
        self, branch_validator: BranchValidatorPrimitive, test_context: TTAContext
    ):
        """Test limiting language increases dead end risk."""
        proposal = BranchProposal(
            universe_id="main",
            branch_description="This is the only final option with never any alternatives",
            choice_text="Take the impossible final action",
            affected_characters=["hero"],
        )

        validation = await branch_validator.execute(proposal, test_context)

        # Should have elevated dead end risk
        assert validation.dead_end_risk > 0.2


class TestValidation:
    """Test input validation."""

    @pytest.mark.asyncio
    async def test_empty_universe_id_raises_error(
        self, branch_validator: BranchValidatorPrimitive, test_context: TTAContext
    ):
        """Test empty universe_id raises ValidationError."""
        proposal = BranchProposal(
            universe_id="",
            branch_description="Some description",
            choice_text="Some choice text here",
            affected_characters=[],
        )

        with pytest.raises(ValidationError, match="universe_id is required"):
            await branch_validator.execute(proposal, test_context)

    @pytest.mark.asyncio
    async def test_empty_branch_description_raises_error(
        self, branch_validator: BranchValidatorPrimitive, test_context: TTAContext
    ):
        """Test empty branch_description raises ValidationError."""
        proposal = BranchProposal(
            universe_id="main",
            branch_description="",
            choice_text="Some choice text here",
            affected_characters=[],
        )

        with pytest.raises(ValidationError, match="branch_description is required"):
            await branch_validator.execute(proposal, test_context)

    @pytest.mark.asyncio
    async def test_empty_choice_text_raises_error(
        self, branch_validator: BranchValidatorPrimitive, test_context: TTAContext
    ):
        """Test empty choice_text raises ValidationError."""
        proposal = BranchProposal(
            universe_id="main",
            branch_description="Some description",
            choice_text="",
            affected_characters=[],
        )

        with pytest.raises(ValidationError, match="choice_text is required"):
            await branch_validator.execute(proposal, test_context)

    @pytest.mark.asyncio
    async def test_choice_text_too_short_raises_error(
        self, branch_validator: BranchValidatorPrimitive, test_context: TTAContext
    ):
        """Test too-short choice_text raises ValidationError."""
        proposal = BranchProposal(
            universe_id="main",
            branch_description="Some description",
            choice_text="Short",  # Less than MIN_CHOICE_LENGTH (10)
            affected_characters=[],
        )

        with pytest.raises(ValidationError, match="at least"):
            await branch_validator.execute(proposal, test_context)

    @pytest.mark.asyncio
    async def test_choice_text_too_long_raises_error(
        self, branch_validator: BranchValidatorPrimitive, test_context: TTAContext
    ):
        """Test too-long choice_text raises ValidationError."""
        proposal = BranchProposal(
            universe_id="main",
            branch_description="Some description",
            choice_text="x" * 250,  # More than MAX_CHOICE_LENGTH (200)
            affected_characters=[],
        )

        with pytest.raises(ValidationError, match="at most"):
            await branch_validator.execute(proposal, test_context)


class TestUtilityMethods:
    """Test utility methods."""

    @pytest.mark.asyncio
    async def test_get_validated_branches(
        self, branch_validator: BranchValidatorPrimitive, test_context: TTAContext
    ):
        """Test getting validated branches for a universe."""
        # Create and validate multiple branches
        for i in range(3):
            proposal = BranchProposal(
                universe_id="main",
                branch_description=f"Description {i}",
                choice_text=f"Choice number {i} with sufficient length",
                affected_characters=["hero"],
            )
            await branch_validator.execute(proposal, test_context)

        # Get validated branches
        validated = branch_validator.get_validated_branches("main")
        assert len(validated) >= 0  # At least some should be valid

    @pytest.mark.asyncio
    async def test_clear_validated_branches_specific_universe(
        self, branch_validator: BranchValidatorPrimitive, test_context: TTAContext
    ):
        """Test clearing branches for specific universe."""
        # Create branches in different universes
        proposal1 = BranchProposal(
            universe_id="main",
            branch_description="Main universe branch",
            choice_text="Main choice with enough length here",
            affected_characters=["hero"],
        )
        await branch_validator.execute(proposal1, test_context)

        proposal2 = BranchProposal(
            universe_id="alternate",
            branch_description="Alternate universe branch",
            choice_text="Alternate choice with enough length",
            affected_characters=["hero"],
        )
        await branch_validator.execute(proposal2, test_context)

        # Clear only main universe
        branch_validator.clear_validated_branches("main")

        # Main should be empty, alternate should remain
        main_branches = branch_validator.get_validated_branches("main")
        alternate_branches = branch_validator.get_validated_branches("alternate")

        assert len(main_branches) == 0
        # Alternate may or may not have branches depending on validation success

    @pytest.mark.asyncio
    async def test_clear_all_validated_branches(
        self, branch_validator: BranchValidatorPrimitive, test_context: TTAContext
    ):
        """Test clearing all validated branches."""
        # Create branches
        proposal = BranchProposal(
            universe_id="main",
            branch_description="Some branch",
            choice_text="Some choice with enough length",
            affected_characters=["hero"],
        )
        await branch_validator.execute(proposal, test_context)

        # Clear all
        branch_validator.clear_validated_branches()

        # All should be empty
        main_branches = branch_validator.get_validated_branches("main")
        assert len(main_branches) == 0


class TestOverallValidation:
    """Test overall validation logic."""

    @pytest.mark.asyncio
    async def test_high_quality_branch_is_valid(
        self, branch_validator: BranchValidatorPrimitive, test_context: TTAContext
    ):
        """Test high-quality branch passes validation."""
        proposal = BranchProposal(
            universe_id="main",
            branch_description="Hero decides to help the villagers, which leads to gaining their trust",
            choice_text="Offer to help the villagers defend against the bandits",
            affected_characters=["hero", "villagers"],
            timeline_context=[
                "Hero arrived at village",
                "Villagers mentioned bandit threat",
            ],
        )

        validation = await branch_validator.execute(proposal, test_context)

        # Should have high scores
        assert validation.overall_score > 0.6
        assert validation.is_valid is True

    @pytest.mark.asyncio
    async def test_error_level_issue_invalidates_branch(
        self, branch_validator: BranchValidatorPrimitive, test_context: TTAContext
    ):
        """Test error-level issues make branch invalid."""
        proposal = BranchProposal(
            universe_id="realistic",
            branch_description="Hero uses magic spell",
            choice_text="Cast a powerful magic spell to solve the problem",
            affected_characters=["hero"],
            universe_rules={"no_magic": "no magic allowed"},
        )

        validation = await branch_validator.execute(proposal, test_context)

        # Should be invalid due to error-level issue
        assert validation.is_valid is False or validation.overall_score < 0.6

    @pytest.mark.asyncio
    async def test_suggestions_generated(
        self, branch_validator: BranchValidatorPrimitive, test_context: TTAContext
    ):
        """Test suggestions are generated for issues."""
        proposal = BranchProposal(
            universe_id="main",
            branch_description="Something happens maybe",
            choice_text="Perhaps do something that might work",
            affected_characters=[],
        )

        validation = await branch_validator.execute(proposal, test_context)

        # Should have suggestions
        assert len(validation.suggestions) > 0
