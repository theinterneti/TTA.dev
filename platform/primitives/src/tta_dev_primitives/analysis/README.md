# TTA.dev Analysis Core

Shared analysis engine for detecting code patterns and recommending TTA.dev primitives.

## Components

### PatternDetector

Detects code patterns using AST analysis:

```python
from tta_dev_primitives.analysis import PatternDetector

detector = PatternDetector()
patterns = detector.detect(code)

# Returns list of detected patterns:
# [
#   {"name": "async_operation", "confidence": 0.95, "locations": [...]},
#   {"name": "error_handling", "confidence": 0.80, "locations": [...]}
# ]
```

**Supported Patterns:**
- `async_operation` - async/await usage
- `error_handling` - try/except blocks
- `retry_logic` - manual retry loops
- `timeout_handling` - timeout implementations
- `caching` - manual caching patterns
- `parallel_execution` - concurrent operations
- `api_calls` - HTTP/external API calls
- `database_operations` - DB queries
- `file_operations` - File I/O

### PrimitiveMatcher

Matches detected patterns to recommended primitives:

```python
from tta_dev_primitives.analysis import PrimitiveMatcher

matcher = PrimitiveMatcher()
matches = matcher.match(patterns)

# Returns list of matched primitives:
# [
#   {"name": "RetryPrimitive", "confidence": 0.90, "patterns": ["retry_logic"]},
#   {"name": "TimeoutPrimitive", "confidence": 0.85, "patterns": ["async_operation"]}
# ]
```

### TemplateProvider

Provides code templates for primitives:

```python
from tta_dev_primitives.analysis import TemplateProvider

provider = TemplateProvider()

# Get template for a primitive
template = provider.get_template("RetryPrimitive")

# Search templates
results = provider.search("retry")

# Get composition example
code = provider.compose(["RetryPrimitive", "CachePrimitive"])
```

### TTAAnalyzer

Main orchestrator combining all components:

```python
from tta_dev_primitives.analysis import TTAAnalyzer

analyzer = TTAAnalyzer()
result = analyzer.analyze(
    code=code,
    file_path="app.py",
    project_type="api",
    min_confidence=0.5
)

# Returns CodeAnalysisResult with:
# - patterns: List of detected patterns
# - primitives: List of matched primitives
# - recommendations: List of recommendations with templates
# - inferred_requirements: Inferred project requirements
```

## Architecture

```
analysis/
├── __init__.py      # Public exports
├── patterns.py      # PatternDetector - AST-based pattern detection
├── matcher.py       # PrimitiveMatcher - Pattern to primitive mapping
├── templates.py     # TemplateProvider - Code templates
├── analyzer.py      # TTAAnalyzer - Main orchestrator
└── models.py        # Pydantic models for results
```

## Usage

The analysis core is used by both the CLI and MCP server:

```python
# CLI uses it directly
from tta_dev_primitives.analysis import TTAAnalyzer

analyzer = TTAAnalyzer()
result = analyzer.analyze(code)

# MCP server wraps it in tools
@mcp.tool()
def analyze_code(code: str) -> dict:
    result = analyzer.analyze(code)
    return result.model_dump()
```

## Extending

### Adding New Patterns

Add pattern detection in `patterns.py`:

```python
def _detect_custom_pattern(self, tree: ast.AST) -> list[dict]:
    """Detect custom pattern."""
    locations = []
    for node in ast.walk(tree):
        if self._is_custom_pattern(node):
            locations.append({"line": node.lineno})

    if locations:
        return [{"name": "custom_pattern", "confidence": 0.8, "locations": locations}]
    return []
```

### Adding New Primitives

Add primitive info in `matcher.py`:

```python
PRIMITIVES = {
    "CustomPrimitive": {
        "name": "CustomPrimitive",
        "category": "custom",
        "description": "Custom primitive description",
        "import_path": "from tta_dev_primitives.custom import CustomPrimitive",
        "patterns": ["custom_pattern"],
        "use_cases": ["Custom use case"],
    }
}
```

### Adding New Templates

Add templates in `templates.py`:

```python
TEMPLATES = {
    "CustomPrimitive": {
        "name": "custom_template",
        "description": "Custom template",
        "code": '''
from tta_dev_primitives.custom import CustomPrimitive

custom = CustomPrimitive(param=value)
result = await custom.execute(data, context)
''',
        "primitives": ["CustomPrimitive"],
    }
}
```

## Observability

The analyzer includes structured logging:

```python
import structlog

logger = structlog.get_logger("tta_dev.analysis")

# Logs include:
# - starting_analysis: Analysis started
# - patterns_detected: Number of patterns found
# - primitives_matched: Number of primitives matched
# - analysis_complete: Analysis finished with timing
```


---
**Logseq:** [[TTA.dev/Platform/Primitives/Src/Tta_dev_primitives/Analysis/Readme]]
