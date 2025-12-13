---
description: 'Add comprehensive tests for a component using MockPrimitive'
agent: 'agent'
---

# Add Tests

Add comprehensive tests for ${file} using TTA.dev testing patterns.

## Instructions

1. Read the source file to understand the component
2. Create tests covering:
   - Success cases
   - Failure cases
   - Edge cases
   - Integration with other primitives

## Test Template

```python
import pytest
from tta_dev_primitives.core.base import WorkflowContext
from tta_dev_primitives.testing import MockPrimitive

class Test${input:ComponentName}:
    """Tests for ${input:ComponentName}."""

    @pytest.fixture
    def context(self):
        """Provide test context."""
        return WorkflowContext(workflow_id="test")

    @pytest.mark.asyncio
    async def test_success(self, context):
        """Test successful execution."""
        # Arrange
        mock = MockPrimitive("test", return_value={"success": True})

        # Act
        result = await mock.execute("input", context)

        # Assert
        assert result == {"success": True}
        assert mock.call_count == 1

    @pytest.mark.asyncio
    async def test_failure(self, context):
        """Test error handling."""
        # Arrange
        mock = MockPrimitive("test", side_effect=ValueError("Error"))

        # Act & Assert
        with pytest.raises(ValueError, match="Error"):
            await mock.execute("input", context)

    @pytest.mark.asyncio
    async def test_composition(self, context):
        """Test composition with other primitives."""
        # Arrange
        mock1 = MockPrimitive("step1", return_value="result1")
        mock2 = MockPrimitive("step2", return_value="result2")
        workflow = mock1 >> mock2

        # Act
        result = await workflow.execute("input", context)

        # Assert
        assert result == "result2"
```

## Checklist

- [ ] Uses `@pytest.mark.asyncio` for async tests
- [ ] Uses `MockPrimitive` for dependencies
- [ ] Tests success, failure, and edge cases
- [ ] No external dependencies
- [ ] Descriptive test names

## Run Tests

```bash
uv run pytest tests/test_${input:module}.py -v
uv run pytest --cov=src --cov-report=html
```


---
**Logseq:** [[TTA.dev/.github/Prompts/Add-tests.prompt]]
