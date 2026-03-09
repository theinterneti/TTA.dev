# CodeGraphContext (CGC) Integration with TTA.dev

## Overview

CodeGraphContext provides graph-database-powered code analysis through an MCP server. TTA.dev can leverage CGC's capabilities to build intelligent workflows that understand code structure, dependencies, and relationships.

## Quick Start

```bash
# 1. Install CGC (if not already installed)
uv pip install codegraphcontext

# 2. Index your repository
uv run cgc index .

# 3. Use CGC in TTA.dev workflows
python examples/cgc_integration.py
```

## Integration Benefits

### 1. **Intelligent Code Analysis**
- Find all implementations of a pattern (e.g., all Primitives)
- Analyze dependency graphs
- Detect circular dependencies
- Find unused code

### 2. **Agent-Powered Development**
- Agents can query the code graph to understand architecture
- Auto-generate documentation from code structure
- Suggest refactorings based on dependency analysis
- Validate architectural constraints

### 3. **Enhanced Observability**
- Track which code paths are actually executed
- Correlate workflow traces with code structure
- Identify performance bottlenecks by analyzing call graphs

## CGC Capabilities Available via MCP

### Find Commands
```bash
# Find all classes matching a pattern
cgc find classes -n "Primitive"

# Find functions
cgc find functions -n "execute"

# Find dependencies
cgc find dependencies -n "ttadev.primitives"
```

### Analyze Commands
```bash
# Analyze dependencies
cgc analyze dependencies -p /path/to/repo

# Analyze complexity
cgc analyze complexity -p /path/to/repo

# Analyze imports
cgc analyze imports -p /path/to/repo
```

### Query Commands
```bash
# Execute custom Cypher queries
cgc query "MATCH (n:Class)-[:IMPORTS]->(m) RETURN n, m LIMIT 10"
```

## TTA.dev Integration Patterns

### Pattern 1: Architecture Validation Workflow

```python
from ttadev.primitives.core import SequentialPrimitive, LambdaPrimitive
from ttadev.primitives.recovery import RetryPrimitive

async def validate_no_circular_deps(repo_path: str, ctx):
    """Ensure no circular dependencies exist."""
    # Use CGC to analyze dependency graph
    # Fail workflow if circular deps detected
    pass

workflow = SequentialPrimitive([
    LambdaPrimitive(index_repository),
    RetryPrimitive(
        LambdaPrimitive(validate_no_circular_deps),
        max_attempts=3
    )
])
```

### Pattern 2: Auto-Documentation Generation

```python
async def generate_primitive_docs(repo_path: str, ctx):
    """Auto-generate docs for all primitives."""
    # Query CGC for all Primitive classes
    # Extract docstrings and method signatures
    # Generate markdown documentation
    pass
```

### Pattern 3: Code Health Monitoring

```python
async def monitor_code_health(repo_path: str, ctx):
    """Track code health metrics over time."""
    # Use CGC to analyze complexity
    # Store metrics in observability system
    # Alert if complexity exceeds thresholds
    pass
```

## Advanced: Custom CGC MCP Tool

You can create a TTA.dev primitive that exposes CGC as an MCP tool for agents:

```python
from ttadev.mcp import MCPPrimitive

cgc_tool = MCPPrimitive(
    name="code_graph_query",
    description="Query the code graph database",
    server_command=["uv", "run", "cgc", "mcp", "start"]
)

# Agents can now use cgc_tool in workflows
workflow = cgc_tool >> process_results
```

## Real-World Use Cases

### 1. **Refactoring Assistant**
- CGC finds all usages of a function
- Agent proposes refactoring
- Validates no breaking changes via dependency analysis

### 2. **Test Coverage Analysis**
- CGC maps code structure
- Compare with test execution traces
- Identify untested code paths

### 3. **Performance Optimization**
- CGC identifies hot paths
- Correlate with observability data
- Suggest optimizations based on call frequency

### 4. **Security Auditing**
- Find all data flow paths
- Identify potential injection points
- Validate input sanitization

## Configuration

CGC can use either FalkorDB (default) or Neo4j. Configure via `.env`:

```bash
# Use FalkorDB (lightweight, no setup)
GRAPH_DB_BACKEND=falkordb

# Or use Neo4j (more features)
GRAPH_DB_BACKEND=neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
```

## Next Steps

1. **Experiment**: Run `python examples/cgc_integration.py`
2. **Explore**: Try `cgc find`, `cgc analyze` commands
3. **Integrate**: Add CGC queries to your TTA.dev workflows
4. **Extend**: Create custom analysis primitives

## Resources

- [CGC Documentation](https://github.com/CodeGraphContext/CodeGraphContext)
- [TTA.dev Primitives Catalog](./PRIMITIVES_CATALOG.md)
- [MCP Integration Guide](./MCP_INTEGRATION.md)
