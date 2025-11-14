---
applyTo:
  - pattern: "**/*.py"
tags: ["python", "quality", "linting", "formatting", "type-checking"]
description: "Python code quality standards, formatting rules, and type checking requirements for TTA"
---

# Python Quality Standards

## Overview

This instruction set defines code quality standards for all Python code in TTA. All Python files must follow consistent formatting, linting, and type checking standards.

## Code Formatting

### Black Formatter
- **Line Length**: 88 characters
- **String Quotes**: Double quotes preferred
- **Trailing Commas**: Use in multi-line structures

```bash
# Format code
uvx ruff format src/ tests/

# Check formatting
uvx ruff format --check src/ tests/
```

### Import Sorting (isort)
- **Profile**: Black-compatible
- **Line Length**: 88 characters
- **Order**: Standard library, third-party, local

```python
# ✅ Correct import order
import asyncio
from typing import Optional

import pytest
from fastapi import FastAPI

from src.models import Player
from src.services import PlayerService
```

## Linting with Ruff

### Configuration
```toml
[tool.ruff]
line-length = 88
target-version = "py312"

[tool.ruff.lint]
select = [
    "E",    # pycodestyle errors
    "W",    # pycodestyle warnings
    "F",    # Pyflakes
    "I",    # isort
    "B",    # flake8-bugbear
    "C4",   # flake8-comprehensions
    "UP",   # pyupgrade
]
```

### Running Ruff
```bash
# Check for issues
uvx ruff check src/ tests/

# Fix issues automatically
uvx ruff check --fix src/ tests/

# Check specific rule
uvx ruff check --select E501 src/
```

## Type Checking with Pyright

### Configuration
```json
{
  "typeCheckingMode": "strict",
  "pythonVersion": "3.12",
  "include": ["src", "tests"],
  "exclude": ["venv", ".venv"]
}
```

### Running Pyright
```bash
# Type check
uvx pyright src/

# Watch mode
uvx pyright --watch src/
```

### Type Hints Best Practices

```python
# ✅ Correct: Full type hints
async def process_player_input(
    player_id: str,
    input_text: str,
    context: dict[str, Any]
) -> ProcessedInput:
    """Process player input."""
    pass

# ❌ Incorrect: Missing type hints
async def process_player_input(player_id, input_text, context):
    """Process player input."""
    pass

# ✅ Correct: Optional types
def get_player(player_id: str) -> Optional[Player]:
    """Get player by ID."""
    pass

# ✅ Correct: Union types
def handle_response(response: str | dict) -> None:
    """Handle response."""
    pass
```

## Docstring Standards

### Google Style Docstrings

```python
def calculate_therapeutic_score(
    session_id: str,
    responses: list[str],
    baseline: float = 0.0
) -> float:
    """Calculate therapeutic effectiveness score.
    
    Analyzes player responses to determine therapeutic effectiveness
    based on emotional engagement and narrative coherence.
    
    Args:
        session_id: Unique session identifier
        responses: List of player responses
        baseline: Starting score for comparison (default: 0.0)
    
    Returns:
        Calculated therapeutic score (0.0-100.0)
    
    Raises:
        ValueError: If session_id is empty or responses is empty
        SessionNotFoundError: If session doesn't exist
    
    Example:
        >>> score = calculate_therapeutic_score(
        ...     "session_123",
        ...     ["response1", "response2"],
        ...     baseline=50.0
        ... )
        >>> print(score)
        75.5
    """
    pass
```

## Naming Conventions

### Functions and Variables
```python
# ✅ Correct: snake_case
def process_player_input(player_id: str) -> None:
    pass

player_responses: list[str] = []
max_retries: int = 3

# ❌ Incorrect: camelCase or PascalCase
def processPlayerInput(playerId: str) -> None:
    pass
```

### Classes
```python
# ✅ Correct: PascalCase
class PlayerStateRepository:
    pass

class TherapeuticContentValidator:
    pass

# ❌ Incorrect: snake_case
class player_state_repository:
    pass
```

### Constants
```python
# ✅ Correct: UPPER_SNAKE_CASE
MAX_RETRIES = 3
DEFAULT_TIMEOUT_SECONDS = 30
THERAPEUTIC_SAFETY_THRESHOLD = 0.8

# ❌ Incorrect: lowercase or mixed case
max_retries = 3
defaultTimeout = 30
```

## File Organization

### Module Structure
```python
"""Module docstring describing purpose."""

# Standard library imports
import asyncio
from typing import Optional

# Third-party imports
import pytest
from fastapi import FastAPI

# Local imports
from src.models import Player
from src.services import PlayerService

# Constants
MAX_RETRIES = 3

# Classes
class PlayerManager:
    pass

# Functions
async def process_input(text: str) -> str:
    pass

# Main execution
if __name__ == "__main__":
    pass
```

## Code Review Checklist

- [ ] Black formatting applied
- [ ] isort import sorting applied
- [ ] Ruff linting passed
- [ ] Pyright type checking passed
- [ ] Docstrings complete (Google style)
- [ ] Type hints on all functions
- [ ] Naming conventions followed
- [ ] No unused imports
- [ ] No hardcoded values
- [ ] Error handling comprehensive

## Common Issues and Fixes

### Unused Imports
```python
# ❌ Incorrect
import os
import sys
from typing import Optional

def get_name() -> str:
    return "test"

# ✅ Correct
from typing import Optional

def get_name() -> str:
    return "test"
```

### Missing Type Hints
```python
# ❌ Incorrect
def calculate_score(responses):
    return sum(len(r) for r in responses)

# ✅ Correct
def calculate_score(responses: list[str]) -> int:
    return sum(len(r) for r in responses)
```

## References

- Black Documentation: https://black.readthedocs.io/
- Ruff Documentation: https://docs.astral.sh/ruff/
- Pyright Documentation: https://github.com/microsoft/pyright
- PEP 8: https://www.python.org/dev/peps/pep-0008/
- PEP 257: https://www.python.org/dev/peps/pep-0257/

