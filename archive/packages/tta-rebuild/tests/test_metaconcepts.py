"""Tests for metaconcept system."""

from tta_rebuild.core import (
    Metaconcept,
    MetaconceptCategory,
    MetaconceptRegistry,
)


class TestMetaconcept:
    """Tests for Metaconcept dataclass."""

    def test_metaconcept_creation(self) -> None:
        """Test basic metaconcept creation."""
        mc = Metaconcept(
            name="Test Metaconcept",
            category=MetaconceptCategory.THERAPEUTIC,
            description="Test description",
            scope=["StoryGenerator"],
        )

        assert mc.name == "Test Metaconcept"
        assert mc.category == MetaconceptCategory.THERAPEUTIC
        assert "StoryGenerator" in mc.scope

    def test_applies_to_all(self) -> None:
        """Test metaconcept with 'all' scope."""
        mc = Metaconcept(
            name="Universal",
            category=MetaconceptCategory.SAFETY,
            description="Applies everywhere",
            scope=["all"],
        )

        assert mc.applies_to("StoryGenerator")
        assert mc.applies_to("CharacterDeveloper")
        assert mc.applies_to("AnythingElse")

    def test_applies_to_specific(self) -> None:
        """Test metaconcept with specific scope."""
        mc = Metaconcept(
            name="Specific",
            category=MetaconceptCategory.NARRATIVE,
            description="Only for stories",
            scope=["StoryGenerator", "DialogueCreator"],
        )

        assert mc.applies_to("StoryGenerator")
        assert mc.applies_to("DialogueCreator")
        assert not mc.applies_to("CharacterDeveloper")


class TestMetaconceptRegistry:
    """Tests for MetaconceptRegistry."""

    def test_get_all(self) -> None:
        """Test retrieving all metaconcepts."""
        all_metaconcepts = MetaconceptRegistry.get_all()

        # Should have all 18 metaconcepts
        assert len(all_metaconcepts) == 18

        # Verify categories present
        categories = {mc.category for mc in all_metaconcepts}
        assert MetaconceptCategory.THERAPEUTIC in categories
        assert MetaconceptCategory.NARRATIVE in categories
        assert MetaconceptCategory.SAFETY in categories
        assert MetaconceptCategory.GAME in categories

    def test_get_by_category(self) -> None:
        """Test filtering metaconcepts by category."""
        therapeutic = MetaconceptRegistry.get_by_category(
            MetaconceptCategory.THERAPEUTIC
        )

        assert len(therapeutic) == 4
        assert all(mc.category == MetaconceptCategory.THERAPEUTIC for mc in therapeutic)

        # Check some expected therapeutic metaconcepts
        names = {mc.name for mc in therapeutic}
        assert "Support Therapeutic Goals" in names
        assert "Promote Self-Compassion" in names

    def test_get_for_primitive(self) -> None:
        """Test getting metaconcepts for specific primitive."""
        # therapeutic and narrative primitives should get relevant metaconcepts
        therapeutic_mcs = MetaconceptRegistry.get_for_primitive("therapeutic")

        # Should include therapeutic, narrative, and safety
        categories = {mc.category for mc in therapeutic_mcs}
        assert MetaconceptCategory.THERAPEUTIC in categories
        assert MetaconceptCategory.NARRATIVE in categories
        assert MetaconceptCategory.SAFETY in categories

    def test_get_by_names(self) -> None:
        """Test retrieving specific metaconcepts by name."""
        names = ["Support Therapeutic Goals", "Ensure Narrative Quality"]
        metaconcepts = MetaconceptRegistry.get_by_names(names)

        assert len(metaconcepts) == 2
        mc_names = {mc.name for mc in metaconcepts}
        assert "Support Therapeutic Goals" in mc_names
        assert "Ensure Narrative Quality" in mc_names

    def test_get_by_names_missing(self) -> None:
        """Test that missing names are silently skipped."""
        names = ["Support Therapeutic Goals", "Nonexistent Metaconcept"]
        metaconcepts = MetaconceptRegistry.get_by_names(names)

        # Should only return the one that exists
        assert len(metaconcepts) == 1
        assert metaconcepts[0].name == "Support Therapeutic Goals"

    def test_category_counts(self) -> None:
        """Test that each category has expected number of metaconcepts."""
        therapeutic = MetaconceptRegistry.get_by_category(
            MetaconceptCategory.THERAPEUTIC
        )
        narrative = MetaconceptRegistry.get_by_category(MetaconceptCategory.NARRATIVE)
        safety = MetaconceptRegistry.get_by_category(MetaconceptCategory.SAFETY)
        game = MetaconceptRegistry.get_by_category(MetaconceptCategory.GAME)

        assert len(therapeutic) == 4
        assert len(narrative) == 5
        assert len(safety) == 6
        assert len(game) == 3
