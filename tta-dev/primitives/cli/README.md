# TTA.dev CLI

Command-line interface for TTA.dev primitives - analyze code, get recommendations, and explore primitives.

## Installation

The CLI is included with the `tta-dev-primitives` package:

```bash
uv add tta-dev-primitives
```

## Commands

### `tta-dev analyze`

Analyze Python code and get primitive recommendations:

```bash
# Analyze a file
tta-dev analyze path/to/file.py

# Analyze with JSON output
tta-dev analyze path/to/file.py --format json

# Set minimum confidence threshold
tta-dev analyze path/to/file.py --min-confidence 0.7

# Specify project type for better recommendations
tta-dev analyze path/to/file.py --project-type api
```

**Output includes:**
- Detected patterns (async operations, error handling, retry logic, etc.)
- Matched primitives with confidence scores
- Recommendations with rationale
- Code templates for suggested primitives

### `tta-dev primitives`

List all available primitives:

```bash
# List all primitives
tta-dev primitives

# Filter by category
tta-dev primitives --category recovery

# JSON output
tta-dev primitives --format json
```

**Categories:**
- `core` - Base workflow primitives
- `recovery` - Error handling (Retry, Fallback, Timeout, CircuitBreaker)
- `performance` - Optimization (Cache, Memory)
- `orchestration` - Multi-agent coordination

### `tta-dev docs`

Show documentation for a specific primitive:

```bash
# Get docs for RetryPrimitive
tta-dev docs RetryPrimitive

# JSON output
tta-dev docs CachePrimitive --format json
```

### `tta-dev serve`

Start the MCP server:

```bash
# Start server (uses stdio transport)
tta-dev serve

# Or use the dedicated entry point
tta-dev-mcp
```

### `tta-dev version`

Show version information:

```bash
tta-dev version
```

## Architecture

The CLI uses a shared analysis core with the MCP server:

```
cli/
├── app.py          # Typer CLI application
analysis/
├── patterns.py     # PatternDetector - finds code patterns
├── matcher.py      # PrimitiveMatcher - matches patterns to primitives
├── templates.py    # TemplateProvider - code templates
├── analyzer.py     # TTAAnalyzer - orchestrates analysis
```

## Examples

### Analyze a workflow file

```bash
$ tta-dev analyze examples/workflow.py

📊 TTA.dev Code Analysis
========================

📁 File: examples/workflow.py
📋 Project Type: workflow

🔍 Detected Patterns:
  • async_operation (confidence: 0.95)
  • error_handling (confidence: 0.80)
  • retry_logic (confidence: 0.70)

🧩 Recommended Primitives:
  • RetryPrimitive (confidence: 0.90)
    → Automatic retry with exponential backoff
  • TimeoutPrimitive (confidence: 0.85)
    → Circuit breaker pattern with timeout

💡 Recommendations:
  1. Add RetryPrimitive for transient failure handling
  2. Wrap external calls with TimeoutPrimitive
```

### Get primitive info

```bash
$ tta-dev docs CachePrimitive

📚 CachePrimitive
=================

LRU cache with TTL for expensive operations.

Import:
  from tta_dev_primitives.performance import CachePrimitive

Use Cases:
  • Cache expensive LLM calls
  • Reduce API costs
  • Improve response latency

Example:
  cached = CachePrimitive(
      primitive=expensive_call,
      ttl_seconds=3600,
      max_size=1000
  )
```

## Observability

The CLI includes structured logging via `structlog`:

```bash
# Enable debug logging
export TTA_LOG_LEVEL=debug
tta-dev analyze file.py
```

Log events include:
- `starting_analysis` - Analysis initiated
- `patterns_detected` - Patterns found with count
- `primitives_matched` - Primitives matched with count
- `analysis_complete` - Analysis finished with timing
