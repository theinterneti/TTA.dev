# MCP Integration with Claude

## Model Context Protocol (MCP)

Claude integrates with MCP servers to extend capabilities with external tools and data sources.

## Available MCP Servers

When working in this repository, the following MCP servers may be available:

### Context7 MCP Server

Provides access to library documentation:

- **Use for**: Fetching up-to-date library docs (React, Python packages, frameworks)
- **Tool**: `resolve-library-id` → `get-library-docs`
- **Example**: Validating API usage, checking latest features

### Grafana MCP Server

Provides monitoring and observability integration:

- **Use for**: Querying metrics, dashboards, alerts
- **Tools**: Dashboard queries, alert rules, data source queries
- **Example**: Analyzing system performance, debugging production issues

### Sift MCP Server

Provides investigation and analysis capabilities:

- **Use for**: Root cause analysis, incident investigation
- **Tools**: Investigation management, analysis retrieval
- **Example**: Tracking debugging sessions, documenting findings

### Pylance MCP Server

Provides Python language analysis:

- **Use for**: Type checking, import analysis, syntax validation
- **Tools**: Syntax error checking, import resolution, refactoring
- **Example**: Validating Python code before execution

## MCP Workflow Patterns

### Documentation Lookup Workflow

```text
User asks about library API
↓
resolve-library-id (get Context7 ID)
↓
get-library-docs (fetch documentation)
↓
Apply knowledge to current task
```

### Debugging Workflow

```text
User reports issue
↓
Check Grafana metrics (identify anomalies)
↓
Query Loki logs (find error patterns)
↓
Create Sift investigation (track analysis)
↓
Apply fix and verify
```

### Code Quality Workflow

```text
Generate Python code
↓
pylance syntax check (validate before running)
↓
pylance import analysis (verify dependencies)
↓
Run tests with pytest
```

## MCP Server Discovery

Use the appropriate MCP tool based on task:

- **Library docs?** → Context7
- **System metrics?** → Grafana
- **Investigation tracking?** → Sift
- **Python validation?** → Pylance

## Integration with tta-dev-primitives

MCP servers can be integrated into workflow primitives:

```python
# Example: Documentation lookup primitive
class DocLookupPrimitive(WorkflowPrimitive[str, str]):
    async def execute(self, library_name: str, context: WorkflowContext) -> str:
        # Use Context7 MCP to fetch docs
        library_id = await resolve_library_id(library_name)
        docs = await get_library_docs(library_id)
        return docs
```

Consider creating primitives that wrap MCP tools for reusable workflows.


---
**Logseq:** [[TTA.dev/.universal-instructions/Claude-specific/Mcp-integration]]
