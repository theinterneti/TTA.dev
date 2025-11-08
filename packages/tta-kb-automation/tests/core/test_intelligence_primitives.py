import pytest
from tta_dev_primitives import WorkflowContext

from tta_kb_automation.core.intelligence_primitives import ClassifyTODO


class TestClassifyTODO:
    """Test cases for the ClassifyTODO primitive."""

    @pytest.mark.asyncio
    async def test_classify_implementation_todo(self):
        """Test classification of an implementation TODO."""
        classifier = ClassifyTODO()
        context = WorkflowContext()
        input_data = {"todo_text": "TODO: Implement new feature", "context": {}}
        result = await classifier.execute(input_data, context)
        assert result["category"] == "implementation"
        assert result["priority"] == "medium"
        assert result["confidence"] == 0.8

    @pytest.mark.asyncio
    async def test_classify_testing_todo(self):
        """Test classification of a testing TODO."""
        classifier = ClassifyTODO()
        context = WorkflowContext()
        input_data = {
            "todo_text": "TODO: Add unit tests for new feature",
            "context": {},
        }
        result = await classifier.execute(input_data, context)
        assert result["category"] == "testing"
        assert result["priority"] == "medium"
        assert result["confidence"] == 0.8

    @pytest.mark.asyncio
    async def test_classify_documentation_todo(self):
        """Test classification of a documentation TODO."""
        classifier = ClassifyTODO()
        context = WorkflowContext()
        input_data = {
            "todo_text": "TODO: Update README with new usage examples",
            "context": {},
        }
        result = await classifier.execute(input_data, context)
        assert result["category"] == "documentation"
        assert result["priority"] == "medium"
        assert result["confidence"] == 0.8

    @pytest.mark.asyncio
    async def test_classify_bugfix_todo(self):
        """Test classification of a bugfix TODO."""
        classifier = ClassifyTODO()
        context = WorkflowContext()
        input_data = {
            "todo_text": "FIXME: Fix critical bug in authentication",
            "context": {},
        }
        result = await classifier.execute(input_data, context)
        assert result["category"] == "bugfix"
        assert result["priority"] == "high"  # "critical" keyword
        assert result["confidence"] == 0.8

    @pytest.mark.asyncio
    async def test_classify_refactoring_todo(self):
        """Test classification of a refactoring TODO."""
        classifier = ClassifyTODO()
        context = WorkflowContext()
        input_data = {"todo_text": "HACK: Refactor old API endpoints", "context": {}}
        result = await classifier.execute(input_data, context)
        assert result["category"] == "refactoring"
        assert result["priority"] == "medium"
        assert result["confidence"] == 0.8

    @pytest.mark.asyncio
    async def test_classify_high_priority_todo(self):
        """Test classification of a high priority TODO."""
        classifier = ClassifyTODO()
        context = WorkflowContext()
        input_data = {
            "todo_text": "TODO: URGENT - Address security vulnerability",
            "context": {},
        }
        result = await classifier.execute(input_data, context)
        assert result["category"] == "implementation"  # Default category if no other matches
        assert result["priority"] == "high"
        assert result["confidence"] == 0.8

    @pytest.mark.asyncio
    async def test_classify_low_priority_todo(self):
        """Test classification of a low priority TODO."""
        classifier = ClassifyTODO()
        context = WorkflowContext()
        input_data = {
            "todo_text": "TODO: Nice to have feature for someday",
            "context": {},
        }
        result = await classifier.execute(input_data, context)
        assert result["category"] == "implementation"  # Default category if no other matches
        assert result["priority"] == "low"
        assert result["confidence"] == 0.8

    @pytest.mark.asyncio
    async def test_classify_infrastructure_todo(self):
        """Test classification of an infrastructure TODO."""
        classifier = ClassifyTODO()
        context = WorkflowContext()
        input_data = {"todo_text": "TODO: Deploy new CI/CD pipeline", "context": {}}
        result = await classifier.execute(input_data, context)
        assert result["category"] == "infrastructure"
        assert result["priority"] == "medium"
        assert result["confidence"] == 0.8

    @pytest.mark.asyncio
    async def test_classify_learning_todo(self):
        """Test classification of a learning TODO."""
        classifier = ClassifyTODO()
        context = WorkflowContext()
        input_data = {"todo_text": "TODO: Create tutorial for new users", "context": {}}
        result = await classifier.execute(input_data, context)
        assert result["category"] == "learning"
        assert result["priority"] == "medium"
        assert result["confidence"] == 0.8

    @pytest.mark.asyncio
    async def test_classify_template_todo(self):
        """Test classification of a template TODO."""
        classifier = ClassifyTODO()
        context = WorkflowContext()
        input_data = {"todo_text": "TODO: Design new workflow template", "context": {}}
        result = await classifier.execute(input_data, context)
        assert result["category"] == "template"
        assert result["priority"] == "medium"
        assert result["confidence"] == 0.8

    @pytest.mark.asyncio
    async def test_classify_operations_todo(self):
        """Test classification of an operations TODO."""
        classifier = ClassifyTODO()
        context = WorkflowContext()
        input_data = {"todo_text": "TODO: Monitor production alerts", "context": {}}
        result = await classifier.execute(input_data, context)
        assert result["category"] == "operations"
        assert result["priority"] == "medium"
        assert result["confidence"] == 0.8

    @pytest.mark.asyncio
    async def test_empty_todo_text(self):
        """Test classification with empty TODO text."""
        classifier = ClassifyTODO()
        context = WorkflowContext()
        input_data = {"todo_text": "", "context": {}}
        result = await classifier.execute(input_data, context)
        assert result["category"] == "implementation"
        assert result["priority"] == "medium"
        assert result["confidence"] == 0.8
