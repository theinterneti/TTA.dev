# Contributing to TTA.dev

Thank you for your interest in contributing to TTA.dev! This document provides guidelines for contributing to the framework.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Project Structure](#project-structure)
- [Contributing Guidelines](#contributing-guidelines)
- [Testing](#testing)
- [Documentation](#documentation)
- [Pull Request Process](#pull-request-process)

## Code of Conduct

We are committed to providing a welcoming and inclusive environment. Be respectful, constructive, and professional in all interactions.

## Getting Started

### Prerequisites

- Python 3.10 or higher
- [uv](https://docs.astral.sh/uv/) for dependency management
- Git

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/theinterneti/TTA.dev.git
cd TTA.dev

# Install development dependencies
uv sync --all-extras

# Install packages in editable mode
uv pip install -e packages/tta-dev-primitives
uv pip install -e packages/tta-dev-integrations
uv pip install -e packages/tta-agent-coordination
```

## Development Workflow

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

Use descriptive branch names:
- `feature/` for new features
- `fix/` for bug fixes
- `docs/` for documentation
- `refactor/` for code refactoring

### 2. Make Changes

Follow the coding standards:
- Use type hints
- Write docstrings for public APIs
- Keep functions focused and testable
- Follow existing patterns in the codebase

### 3. Test Your Changes

```bash
# Run all tests
uv run pytest -v

# Run tests with coverage
uv run pytest --cov=packages --cov-report=html

# Run specific test file
uv run pytest packages/tta-dev-primitives/tests/test_adaptive.py -v
```

### 4. Format and Lint

```bash
# Format code
uv run ruff format .

# Lint and fix issues
uv run ruff check . --fix

# Type check
uvx pyright packages/
```

### 5. Commit Changes

Write clear, descriptive commit messages:

```bash
git add .
git commit -m "feat: add retry primitive with exponential backoff

- Implement RetryPrimitive class
- Add configurable max attempts and delay
- Include exponential backoff strategy
- Add comprehensive tests
```

Follow [Conventional Commits](https://www.conventionalcommits.org/):
- `feat:` new feature
- `fix:` bug fix
- `docs:` documentation changes
- `test:` adding or updating tests
- `refactor:` code refactoring
- `chore:` maintenance tasks

## Project Structure

```
TTA.dev/
├── packages/                  # Framework packages
│   ├── tta-dev-primitives/   # Core primitives
│   ├── tta-dev-integrations/ # LLM & service integrations
│   └── tta-agent-coordination/ # Agent coordination
├── examples/                  # Usage examples
├── docs/                      # Documentation
├── tests/                     # Integration tests
└── archive/                   # Historical code
```

### Package Structure

Each package follows this structure:

```
package-name/
├── src/package_name/
│   ├── __init__.py
│   ├── module1.py
│   └── module2.py
├── tests/
│   ├── test_module1.py
│   └── test_module2.py
├── README.md
└── pyproject.toml
```

## Contributing Guidelines

### Adding a New Primitive

1. **Identify the category**: adaptive, orchestration, memory, etc.
2. **Create the primitive class**: Inherit from appropriate base class
3. **Add tests**: Cover happy path, error cases, edge cases
4. **Document**: Add docstrings and usage examples
5. **Update docs**: Add to relevant documentation

Example primitive structure:

```python
"""Module description."""

from typing import Any
from tta_dev_primitives.primitives import WorkflowPrimitive

class MyPrimitive(WorkflowPrimitive):
    """Brief description.
    
    Args:
        param1: Description of param1
        param2: Description of param2
        
    Example:
        >>> primitive = MyPrimitive(param1="value")
        >>> result = await primitive.execute(context)
    """
    
    def __init__(self, param1: str, param2: int = 10):
        super().__init__()
        self.param1 = param1
        self.param2 = param2
        
    async def execute(self, context: dict[str, Any]) -> Any:
        """Execute the primitive logic."""
        # Implementation
        pass
```

### Adding a New LLM Provider

1. **Create provider module**: `packages/tta-dev-integrations/src/tta_dev_integrations/llm/providers/new_provider.py`
2. **Implement provider interface**: Follow existing provider patterns
3. **Add to UniversalLLMPrimitive**: Register the provider
4. **Add tests**: Test provider-specific functionality
5. **Document**: Add provider configuration guide

### Writing Examples

1. **Self-contained**: Examples should run independently
2. **Well-commented**: Explain what's happening and why
3. **Realistic**: Show real-world usage patterns
4. **Simple**: Start simple, then show advanced features

## Testing

### Test Organization

- **Unit tests**: In `packages/*/tests/` for each package
- **Integration tests**: In `tests/integration/` for cross-package tests
- **Examples**: Ensure examples run without errors

### Writing Tests

```python
import pytest
from tta_dev_primitives.adaptive import RetryPrimitive

@pytest.mark.asyncio
async def test_retry_success_on_second_attempt():
    """Test that retry succeeds on second attempt."""
    attempt_count = 0
    
    async def flaky_function():
        nonlocal attempt_count
        attempt_count += 1
        if attempt_count == 1:
            raise ValueError("First attempt fails")
        return "success"
    
    primitive = RetryPrimitive(wrapped=flaky_function, max_attempts=3)
    result = await primitive.execute({})
    
    assert result == "success"
    assert attempt_count == 2
```

### Test Coverage

Aim for >80% test coverage on new code. Run coverage reports:

```bash
uv run pytest --cov=packages --cov-report=html
open htmlcov/index.html
```

## Documentation

### Docstring Format

Use Google-style docstrings:

```python
def function(arg1: str, arg2: int = 0) -> bool:
    """Brief description.
    
    More detailed description if needed.
    
    Args:
        arg1: Description of arg1
        arg2: Description of arg2 (default: 0)
        
    Returns:
        Description of return value
        
    Raises:
        ValueError: When input is invalid
        
    Example:
        >>> function("test", 5)
        True
    """
    pass
```

### Documentation Files

- **Architecture docs**: `docs/architecture/` - system design, patterns
- **Guides**: `docs/guides/` - how-to guides for users
- **Integration docs**: `docs/integrations/` - integration guides

## Pull Request Process

### Before Submitting

- [ ] All tests pass
- [ ] Code is formatted (ruff format)
- [ ] Code is linted (ruff check)
- [ ] Type checking passes (pyright)
- [ ] Documentation is updated
- [ ] Examples are updated if needed
- [ ] CHANGELOG is updated (if applicable)

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Refactoring

## Testing
Describe testing performed

## Checklist
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] Code formatted and linted
- [ ] Type checking passes
```

### Review Process

1. **Automated checks**: CI/CD runs tests, linting, type checking
2. **Code review**: Maintainer reviews code quality, design, tests
3. **Feedback**: Address review comments
4. **Approval**: Once approved, PR can be merged
5. **Merge**: Squash merge into main branch

## Getting Help

- **Questions**: Open a [Discussion](https://github.com/theinterneti/TTA.dev/discussions)
- **Bugs**: Open an [Issue](https://github.com/theinterneti/TTA.dev/issues)
- **Chat**: Join our community (link TBD)

## Recognition

Contributors are recognized in:
- GitHub contributors page
- Release notes
- CONTRIBUTORS.md file

Thank you for contributing to TTA.dev! 🚀
