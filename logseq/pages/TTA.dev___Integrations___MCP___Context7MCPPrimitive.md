# TTA.dev/Integrations/MCP/Context7MCPPrimitive

**Query library documentation via Context7 MCP with adaptive configuration**

## Overview

`Context7MCPPrimitive` provides programmatic access to up-to-date library documentation via Context7/Upstash MCP, enabling workflows to query API references, usage patterns, and best practices.

**Package:** `tta-dev-primitives`
**Module:** `tta_dev_primitives.integrations.context7_mcp_primitive`
**Base Class:** [[TTA.dev/Primitives/WorkflowPrimitive]]

## Import

```python
from tta_dev_primitives.integrations import Context7MCPPrimitive
```

## Operations

### `get_docs()`

Retrieve library documentation with optional topic focus.

**Parameters:**
- `library: str` - Library name or Context7 ID
- `topic: str | None` - Optional topic to focus on
- `tokens: int` - Maximum tokens of documentation (default: 5000)
- `context: WorkflowContext` - Execution context

**Returns:** `dict` with documentation content

**Example:**
```python
context7 = Context7MCPPrimitive()

docs = await context7.get_docs(
    library="httpx",
    topic="async client usage",
    tokens=5000,
    context=context
)

print(docs['content'])
# Returns: Focused documentation on httpx async client patterns
```

### `resolve_library()`

Map library name to Context7-compatible library ID.

**Parameters:**
- `library_name: str` - Library name to resolve
- `context: WorkflowContext` - Execution context

**Returns:** `dict` with resolved library ID

**Example:**
```python
result = await context7.resolve_library(
    library_name="httpx",
    context=context
)

print(result['library_id'])
# Returns: "/encode/httpx" or similar Context7 ID
```

## Configuration

### No Authentication Required

Context7 MCP is a **public API** - no GITHUB_TOKEN or API key needed.

### Adaptive Detection

`Context7MCPConfig.detect()` checks:
1. **VS Code Copilot:** `.vscode/mcp.json`
2. **Cline:** `~/.config/cline/mcp_settings.json`

**Returns:** `Context7MCPConfig` with:
- `config_path: str` - Detected config file path
- `agent_type: str` - "copilot" or "cline"

### Validation

`Context7MCPConfigValidator` checks:
- ✅ MCP configuration file exists
- ✅ Context7/Upstash server configured

**Example:**
```python
from tta_dev_primitives.integrations import Context7MCPConfigValidator

validator = Context7MCPConfigValidator()
result = await validator.execute(None, context)

if not result["valid"]:
    for issue in result["issues"]:
        print(f"❌ {issue}")
```

### Setup Instructions

If not configured, primitive provides actionable errors:

```
Context7 MCP not configured. Fix options:

1. Create .vscode/mcp.json:
   {
     "mcpServers": {
       "context7": {
         "command": "npx",
         "args": ["-y", "@upstash/mcp-server-context7"]
       }
     }
   }

2. Get setup guide:
   python examples/mcp_integration_workflow.py --setup context7
```

## Usage Patterns

### Pattern 1: AI Coding Agent with Context

```python
from tta_dev_primitives import SequentialPrimitive

# Agent workflow: Identify library → Get docs → Generate code
workflow = (
    identify_unknown_library >>
    context7.get_docs >>
    generate_code_with_context >>
    validate_generated_code
)

result = await workflow.execute(
    {"user_request": "Use httpx to make async API calls"},
    context
)
```

### Pattern 2: Documentation-Augmented LLM Prompts

```python
# Get relevant docs
docs = await context7.get_docs(
    library="fastapi",
    topic="dependency injection",
    tokens=3000,
    context=context
)

# Include in LLM prompt
prompt = f"""
Using this FastAPI documentation:
{docs['content']}

Generate code that implements dependency injection for database connections.
"""
```

### Pattern 3: Library Comparison

```python
# Compare multiple libraries
libraries = ["httpx", "requests", "aiohttp"]

docs = await ParallelPrimitive([
    context7.get_docs(library=lib, topic="async support", context=context)
    for lib in libraries
])

# Analyze and recommend
best_choice = analyze_async_support(docs)
```

### Pattern 4: Learning Agent Knowledge Base

```python
# Build knowledge base of library patterns
from tta_dev_primitives.performance import CachePrimitive

# Cache docs for 24 hours
cached_docs = CachePrimitive(
    primitive=context7.get_docs,
    ttl_seconds=86400
)

# Agent can query without repeated API calls
docs = await cached_docs.execute(
    {"library": "pandas", "topic": "dataframe operations"},
    context
)
```

## Error Handling

### Configuration Errors

```python
try:
    docs = await context7.get_docs(library="httpx", context=context)
except Exception as e:
    if "MCP configuration not found" in str(e):
        print("Create .vscode/mcp.json with Context7 server")
        print("See: examples/mcp_integration_workflow.py --setup context7")
```

### Library Not Found

```python
# Try to resolve unknown library
try:
    result = await context7.resolve_library(
        library_name="unknown-lib",
        context=context
    )
except Exception as e:
    # Fallback to alternative documentation source
    docs = await fallback_docs_source.get_docs(...)
```

## Observability

All operations automatically create OpenTelemetry spans:

```python
# Span: context7_mcp.get_docs
# Attributes:
#   - library: "httpx"
#   - topic: "async client usage"
#   - tokens_requested: 5000
#   - docs_length: 4523
```

**Metrics:**
- `context7_mcp_operation_duration_seconds{operation="get_docs"}`
- `context7_mcp_docs_tokens_total{library="httpx"}`

## Supported Libraries

Context7 supports **thousands of libraries** across languages:

- **Python:** httpx, fastapi, pydantic, sqlalchemy, pandas, numpy, ...
- **JavaScript:** react, next.js, express, axios, ...
- **Go:** gin, echo, gorm, ...
- **Rust:** tokio, actix-web, serde, ...

Use `resolve_library()` to check if a library is available.

## Benefits vs Static Documentation

| Aspect | Static Docs | Context7 MCP |
|--------|------------|--------------|
| **Freshness** | Outdated quickly | Always current |
| **Versioning** | Manual version selection | Auto-detects latest |
| **Search** | Basic keyword search | Semantic understanding |
| **Integration** | Copy-paste from browser | Programmatic API |
| **Context** | Full docs (overwhelming) | Topic-focused snippets |

## Testing

### Unit Test with Mock

```python
from tta_dev_primitives.testing import MockPrimitive

mock_context7 = MockPrimitive(
    return_value={
        "content": "Mock httpx documentation...",
        "library": "httpx"
    }
)

workflow = identify_lib >> mock_context7 >> generate_code
result = await workflow.execute(data, context)
```

### Integration Test (Requires MCP Setup)

```python
@pytest.mark.integration
async def test_context7_get_docs_real():
    context7 = Context7MCPPrimitive()
    result = await context7.get_docs(
        library="httpx",
        topic="async",
        tokens=1000,
        context=WorkflowContext()
    )
    assert "httpx" in result["content"].lower()
    assert len(result["content"]) > 100
```

## Comparison with Other Doc Tools

| Tool | Pros | Cons | Use Case |
|------|------|------|----------|
| **Context7 MCP** | Always current, semantic search | Requires MCP setup | AI agents, dynamic workflows |
| **GitHub README** | Official source | May be outdated | Quick reference |
| **Read the Docs** | Comprehensive | Static, version-locked | Deep learning |
| **StackOverflow** | Real-world examples | Quality varies | Troubleshooting |

## Related Pages

- [[TTA.dev/Integrations/MCP]] - MCP integration overview
- [[TTA.dev/Primitives/WorkflowPrimitive]] - Base primitive class
- [[MCP_SERVERS.md#Context7]] - MCP server documentation

## Source Code

**File:** `packages/tta-dev-primitives/src/tta_dev_primitives/integrations/context7_mcp_primitive.py`

**Key Classes:**
- `Context7MCPPrimitive` - Main primitive
- `Context7MCPConfig` - Configuration detection
- `Context7MCPConfigValidator` - Validation primitive

## Tags

#context7 #documentation #mcp-integration #workflow-primitive #learning
