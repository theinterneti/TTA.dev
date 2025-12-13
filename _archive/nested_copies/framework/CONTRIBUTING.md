# Contributing to TTA.dev

Thank you for your interest in contributing to TTA.dev! This project maintains high quality standards to ensure all components are production-ready and battle-tested.

## Philosophy

**Only proven code enters this repository.**

Every component must have:
- ✅ 100% test coverage
- ✅ Real-world production usage
- ✅ Comprehensive documentation
- ✅ Zero known critical bugs

## Getting Started

### Prerequisites

- Python 3.11 or higher
- [uv](https://github.com/astral-sh/uv) package manager
- Git
- VS Code (recommended)

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/theinterneti/TTA.dev
cd TTA.dev

# Install dependencies
uv sync --all-extras

# Verify installation
uv run pytest -v
```

## Contribution Process

### 1. Find or Create an Issue

- Check existing [issues](https://github.com/theinterneti/TTA.dev/issues)
- Create a new issue if needed, describing:
  - The problem you're solving
  - Your proposed solution
  - Real-world use case
  - Expected impact

### 2. Fork and Branch

```bash
# Fork the repository on GitHub
# Clone your fork
git clone https://github.com/YOUR_USERNAME/TTA.dev
cd TTA.dev

# Create a feature branch
git checkout -b feature/your-feature-name
```

### 3. Make Changes

Follow our [Coding Standards](docs/development/CodingStandards.md):

- Write clean, readable code
- Add comprehensive type hints
- Include docstrings (Google style)
- Follow PEP 8 (enforced by Ruff)
- Keep functions focused and small

### 4. Write Tests

**100% test coverage is required.**

```bash
# Run tests
uv run pytest -v

# Check coverage
uv run pytest --cov=packages --cov-report=html
```

Test requirements:
- Unit tests for all new code
- Integration tests for component interactions
- Docstring examples that work as doctests
- Edge cases and error conditions

### 5. Document Your Changes

Documentation requirements:
- Update relevant README files
- Add docstrings to all public APIs
- Include usage examples
- Update architecture docs if applicable
- Add entry to CHANGELOG.md

### 6. Run Quality Checks

```bash
# Format code
uv run ruff format .

# Lint code
uv run ruff check . --fix

# Type check
uvx pyright packages/

# Validate TODO compliance (REQUIRED!)
uv run python scripts/validate-todos.py

# Run all quality checks
uv run task "✅ Quality Check (All)"
```

All checks must pass before submitting PR.

#### TODO Compliance Requirement ⚠️

**All TODOs in Logseq journals must be 100% compliant with the [TODO Management System](logseq/pages/TODO%20Management%20System.md).**

Every TODO must have:
1. **Category tag**: `#dev-todo` or `#user-todo`
2. **Required properties** (based on category)

**For `#dev-todo` (Development Work):**
```markdown
- TODO Implement feature #dev-todo
  type:: implementation
  priority:: high
  package:: tta-dev-primitives
  related:: [[TTA.dev/Primitives/FeatureName]]
```

Required properties: `type::`, `priority::`, `package::`, `related::`

**For `#user-todo` (Learning/Documentation):**
```markdown
- TODO Create guide #user-todo
  type:: learning
  audience:: intermediate-users
  difficulty:: intermediate
  related:: [[TTA.dev/Guides/GuideName]]
```

Required properties: `type::`, `audience::`, `difficulty::`, `related::`

**Validation:**
```bash
# Check compliance locally
uv run python scripts/validate-todos.py

# Expected output: 100.0% compliance
```

The CI will automatically validate TODO compliance on all PRs. Non-compliant TODOs will block the merge.

### 7. Commit Changes

Use [Conventional Commits](https://www.conventionalcommits.org/):

```bash
git commit -m "feat(primitives): add circuit breaker primitive"
git commit -m "fix(cache): resolve TTL expiration bug"
git commit -m "docs(examples): add LLM chain example"
git commit -m "test(recovery): add retry edge cases"
```

Commit types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Test additions/changes
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `chore`: Maintenance tasks

### 8. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Create a PR with:
- Clear, descriptive title
- Detailed description of changes
- Link to related issues
- Screenshots/examples if applicable
- Checklist of completed items

## Pull Request Checklist

Before submitting, ensure:

- [ ] All tests pass (`uv run pytest -v`)
- [ ] Test coverage is 100% for new code
- [ ] Code is formatted (`uv run ruff format .`)
- [ ] No lint errors (`uv run ruff check .`)
- [ ] Type checks pass (`uvx pyright packages/`)
- [ ] Documentation is complete
- [ ] CHANGELOG.md is updated
- [ ] Commit messages follow convention
- [ ] PR description is clear and complete

## Code Review Process

1. **Automated Checks**: CI/CD runs all quality checks
2. **Maintainer Review**: Code review by project maintainers
3. **Testing**: Manual testing if needed
4. **Approval**: At least one approval required
5. **Merge**: Squash and merge to main

## What We Look For

### Code Quality
- Clean, readable, maintainable code
- Proper error handling
- Performance considerations
- Security best practices

### Testing
- Comprehensive test coverage
- Clear test names and structure
- AAA pattern (Arrange, Act, Assert)
- Edge cases covered

### Documentation
- Clear, concise docstrings
- Usage examples
- Type hints on all public APIs
- README updates where applicable

### Real-World Validation
- Evidence of production usage
- Performance metrics
- User feedback
- Battle-tested in real scenarios

## Types of Contributions

### 🐛 Bug Fixes
- Always welcome!
- Include reproduction steps
- Add regression tests
- Document the fix

### ✨ New Features
- Discuss in an issue first
- Must solve real-world problem
- Requires production validation
- Full documentation required

### 📚 Documentation
- Clarifications and improvements
- New examples and guides
- API documentation
- Architecture diagrams

### 🧪 Tests
- Additional test coverage
- Edge case testing
- Performance benchmarks
- Integration tests

### ⚡ Performance
- Benchmarks required
- Profiling data appreciated
- No premature optimization
- Maintain readability

## Style Guide

### Python Code

```python
from typing import Any

from tta_dev_primitives.core.base import WorkflowContext, WorkflowPrimitive


class MyPrimitive(WorkflowPrimitive):
    """One-line summary of what this primitive does.

    Longer description with more details about usage, behavior,
    and any important considerations.

    Args:
        param: Description of parameter

    Example:
        >>> primitive = MyPrimitive()
        >>> result = await primitive.execute(data, context)
        {"status": "success"}
    """

    def __init__(self, param: str) -> None:
        super().__init__()
        self.param = param

    async def _execute(
        self,
        data: dict[str, Any],
        context: WorkflowContext
    ) -> dict[str, Any]:
        """Execute the primitive logic."""
        # Implementation
        return {"result": "value"}
```

### Tests

```python
import pytest

from tta_dev_primitives.core.base import WorkflowContext


@pytest.fixture
def context():
    """Create a test workflow context."""
    return WorkflowContext(
        workflow_id="test",
        session_id="test-session"
    )


async def test_my_primitive_success(context):
    """Test that MyPrimitive succeeds with valid input."""
    # Arrange
    primitive = MyPrimitive(param="test")
    data = {"input": "value"}

    # Act
    result = await primitive.execute(data, context)

    # Assert
    assert result["result"] == "value"
    assert "input" in result


async def test_my_primitive_handles_error(context):
    """Test that MyPrimitive handles errors gracefully."""
    # Arrange
    primitive = MyPrimitive(param="test")
    data = {}  # Missing required field

    # Act & Assert
    with pytest.raises(ValueError, match="Missing required field"):
        await primitive.execute(data, context)
```

## Community Guidelines

### Be Respectful
- Treat everyone with respect
- Welcome newcomers
- Provide constructive feedback
- Assume good intentions

### Be Collaborative
- Share knowledge
- Help others learn
- Review PRs thoughtfully
- Celebrate contributions

### Be Professional
- Keep discussions on-topic
- Be patient with questions
- Admit when you're wrong
- Give credit where due

## Questions?

- 📖 Read the [docs](docs/)
- 💬 Open a [discussion](https://github.com/theinterneti/TTA.dev/discussions)
- 🐛 Report [issues](https://github.com/theinterneti/TTA.dev/issues)
- 📧 Email: [contact info needed]

## License

By contributing, you agree that your contributions will be licensed under the same license as the project (see [LICENSE](LICENSE)).

## Recognition

Contributors are recognized in:
- CONTRIBUTORS.md file
- Release notes
- Project README

Thank you for helping make TTA.dev better! 🎉


---
**Logseq:** [[TTA.dev/_archive/Nested_copies/Framework/Contributing]]
