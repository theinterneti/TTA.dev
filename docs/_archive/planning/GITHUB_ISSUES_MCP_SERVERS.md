# GitHub Issues for TTA.dev MCP Server Development

**Purpose:** Create comprehensive GitHub issues for building custom MCP servers that will be published to GitHub's MCP Registry.

---

## Issue #1: Build `tta-workflow-primitives-mcp` Server

**Title:** Build Custom MCP Server for TTA.dev Workflow Primitives

**Labels:** `enhancement`, `mcp-server`, `high-priority`, `github-agent-hq`, `good-first-issue`

**Milestone:** GitHub Agent HQ Integration - Phase 2

**Assignees:** Unassigned (open for contributors)

**Description:**

### 🎯 Objective

Create a custom MCP (Model Context Protocol) server that exposes TTA.dev workflow primitives as tools, allowing AI agents to compose production-grade workflows without writing code directly.

### 📋 Background

GitHub's Agent HQ just launched with MCP Registry support. By publishing TTA.dev primitives as MCP servers, we can:
- Reach 180M GitHub developers via one-click install
- Enable AI agents to use TTA.dev patterns naturally
- Differentiate from competitors (LangChain, LlamaIndex)
- Drive organic adoption of TTA.dev

**Related Docs:**
- [GitHub Agent HQ Strategy](../GITHUB_AGENT_HQ_STRATEGY.md)
- [MCP Registry Integration Plan](../MCP_REGISTRY_INTEGRATION_PLAN.md)
- [Primitives Catalog](../PRIMITIVES_CATALOG.md)

### 🏗️ Technical Scope

**Package Location:** `packages/tta-workflow-primitives-mcp/`

**Core Tools to Implement:**

1. **`create_sequential_workflow`**
   - Maps to: `SequentialPrimitive`
   - Input: Array of workflow step definitions
   - Output: Workflow ID

2. **`create_parallel_workflow`**
   - Maps to: `ParallelPrimitive`
   - Input: Array of parallel branch definitions
   - Output: Workflow ID

3. **`create_conditional_workflow`**
   - Maps to: `ConditionalPrimitive`
   - Input: Condition function + branch definitions
   - Output: Workflow ID

4. **`execute_workflow`**
   - Maps to: `WorkflowPrimitive.execute()`
   - Input: Workflow ID, input data, context
   - Output: Execution results

5. **`get_workflow_status`**
   - Query workflow execution status
   - Input: Workflow ID
   - Output: Status, progress, errors

### 📦 Deliverables

**Required Files:**

```
packages/tta-workflow-primitives-mcp/
├── src/
│   └── tta_workflow_primitives_mcp/
│       ├── __init__.py
│       ├── server.py              # FastMCP server
│       ├── tools/
│       │   ├── __init__.py
│       │   ├── sequential.py      # create_sequential_workflow
│       │   ├── parallel.py        # create_parallel_workflow
│       │   ├── conditional.py     # create_conditional_workflow
│       │   ├── execution.py       # execute_workflow
│       │   └── status.py          # get_workflow_status
│       └── storage/
│           └── workflow_registry.py  # Track created workflows
├── tests/
│   ├── test_server.py
│   ├── test_sequential.py
│   ├── test_parallel.py
│   ├── test_conditional.py
│   └── test_execution.py
├── examples/
│   ├── basic_usage.py
│   ├── multi_agent_orchestration.py
│   └── error_handling.py
├── pyproject.toml
├── README.md
├── CHANGELOG.md
├── LICENSE
└── mcp-manifest.json           # GitHub MCP Registry metadata
```

### 🔧 Implementation Details

**Dependencies:**
```toml
[project.dependencies]
python = "^3.11"
fastmcp = "^0.1.0"
tta-dev-primitives = "^0.1.0"
pydantic = "^2.0.0"
```

**Server Structure (server.py):**
```python
from fastmcp import FastMCP

mcp = FastMCP(
    name="TTA Workflow Primitives",
    description="Production-grade workflow primitives for AI agents",
    version="0.1.0"
)

@mcp.tool()
async def create_sequential_workflow(steps: list[dict]) -> dict:
    """Create a sequential workflow pipeline."""
    # Implementation
    pass

@mcp.tool()
async def create_parallel_workflow(branches: list[dict]) -> dict:
    """Create a parallel workflow for concurrent execution."""
    # Implementation
    pass

# ... more tools
```

**MCP Manifest (mcp-manifest.json):**
```json
{
  "name": "tta-workflow-primitives",
  "version": "0.1.0",
  "description": "Production-grade workflow primitives for AI agents",
  "author": "TTA.dev Team",
  "license": "MIT",
  "repository": "https://github.com/theinterneti/TTA.dev",
  "keywords": ["workflow", "primitives", "agents", "github-agent-hq"],
  "tools": [
    {
      "name": "create_sequential_workflow",
      "description": "Create a sequential workflow pipeline"
    }
  ]
}
```

### ✅ Acceptance Criteria

- [ ] All 5 core tools implemented and working
- [ ] 100% test coverage (pytest)
- [ ] Type hints complete (pyright passes)
- [ ] Documentation complete (README, examples)
- [ ] Passes all CI checks (format, lint, type, test)
- [ ] Manual testing in VS Code with Copilot
- [ ] MCP manifest valid and complete
- [ ] Ready for GitHub MCP Registry submission

### 🧪 Testing Requirements

**Unit Tests:**
- Test each tool independently
- Mock TTA.dev primitives
- Test error handling
- Test input validation

**Integration Tests:**
- Test server initialization
- Test tool discovery
- Test end-to-end workflow execution
- Test in VS Code with GitHub Copilot

**Example Test:**
```python
import pytest
from tta_workflow_primitives_mcp.server import mcp

@pytest.mark.asyncio
async def test_create_sequential_workflow():
    result = await mcp.call_tool(
        "create_sequential_workflow",
        {"steps": [{"type": "api_call"}, {"type": "process"}]}
    )
    assert "workflow_id" in result
    assert result["status"] == "created"
```

### 📚 Documentation Requirements

**README.md must include:**
1. Installation instructions
2. Quick start example
3. All tool descriptions with examples
4. Integration with GitHub Agent HQ
5. Configuration options
6. Troubleshooting guide

**Example Usage:**
```
@workspace with tta-workflow-primitives-mcp

Create a workflow that:
1. Fetches user data from API with retry
2. Processes it in parallel across 3 functions
3. Aggregates results
```

### 🚀 Success Metrics

- Server installs successfully via `code --install-mcp tta-workflow-primitives`
- Works in VS Code with GitHub Copilot
- All examples run without errors
- Documentation is clear and complete
- Ready for community contributions

### 🔗 Related Issues

- #TBD - Build `tta-observability-mcp` server
- #TBD - Build `tta-agent-context-mcp` server
- #TBD - Submit to GitHub MCP Registry
- #TBD - Create MCP server documentation hub

### 💡 Implementation Tips

1. **Start Simple:** Implement `create_sequential_workflow` first
2. **Use Existing Patterns:** Follow `tta-dev-primitives` API design
3. **Test Early:** Write tests alongside code
4. **Document As You Go:** Update README with each tool
5. **Ask Questions:** Use GitHub Discussions for clarification

### 📖 Resources

- **MCP Spec:** https://modelcontextprotocol.io
- **FastMCP Docs:** https://github.com/jlowin/fastmcp
- **TTA.dev Primitives:** `platform/primitives/`
- **GitHub MCP Registry:** https://code.visualstudio.com/docs/copilot/customization/mcp-servers

### 🤝 Contributing

This is a great first issue! If you're interested:
1. Comment to claim the issue
2. Fork the repository
3. Create a branch: `feature/mcp-workflow-primitives`
4. Follow the implementation plan above
5. Submit a PR when ready

Questions? Ask in [GitHub Discussions](https://github.com/theinterneti/TTA.dev/discussions)!

---

## Issue #2: Build `tta-observability-mcp` Server

**Title:** Build MCP Server for TTA.dev Observability and Metrics

**Labels:** `enhancement`, `mcp-server`, `observability`, `github-agent-hq`

**Milestone:** GitHub Agent HQ Integration - Phase 3

**Description:**

### 🎯 Objective

Create an MCP server that exposes TTA.dev observability features, allowing AI agents to query workflow metrics, traces, and logs for debugging and optimization.

### 📋 Background

TTA.dev includes `tta-observability-integration` with Prometheus metrics and OpenTelemetry tracing. This MCP server makes observability data queryable by AI agents.

**Use Case Example:**
```
@workspace with tta-observability-mcp

Show me all workflows that failed in the last hour with rate limit errors.
Show the trace for workflow correlation_id abc-123.
What's the average execution time for RouterPrimitive today?
```

### 🏗️ Technical Scope

**Package Location:** `packages/tta-observability-mcp/`

**Core Tools:**

1. **`query_workflow_metrics`**
   - Query Prometheus metrics
   - Input: PromQL query, time range
   - Output: Metric data

2. **`get_workflow_traces`**
   - Get OpenTelemetry traces
   - Input: Filters (correlation_id, time range, status)
   - Output: Trace data with spans

3. **`list_active_workflows`**
   - List currently running workflows
   - Output: Workflow IDs, status, duration

4. **`get_workflow_logs`**
   - Query structured logs
   - Input: Filters (level, time range, workflow_id)
   - Output: Log entries

5. **`get_performance_summary`**
   - Aggregate performance metrics
   - Input: Time range, primitive types
   - Output: Summary statistics

### 📦 Dependencies

```toml
[project.dependencies]
tta-observability-integration = "^0.1.0"
prometheus-client = "^0.18.0"
opentelemetry-api = "^1.20.0"
fastmcp = "^0.1.0"
```

### ✅ Acceptance Criteria

- [ ] All 5 tools implemented
- [ ] Integration with `tta-observability-integration`
- [ ] Prometheus metrics queries working
- [ ] OpenTelemetry trace retrieval working
- [ ] 100% test coverage
- [ ] Documentation complete
- [ ] Manual testing with real metrics data

### 🔗 Dependencies

- Requires: `tta-observability-integration` package
- Blocks: None
- Related: Issue #1 (workflow primitives MCP server)

---

## Issue #3: Build `tta-agent-context-mcp` Server

**Title:** Build MCP Server for Multi-Agent Context Management

**Labels:** `enhancement`, `mcp-server`, `agent-coordination`, `github-agent-hq`

**Milestone:** GitHub Agent HQ Integration - Phase 3

**Description:**

### 🎯 Objective

Create an MCP server for managing shared context across multiple AI agents working on the same task.

### 📋 Background

`universal-agent-context` provides coordination for multi-agent systems. This MCP server exposes context management as tools.

**Use Case Example:**
```
@workspace with tta-agent-context-mcp

Create a shared context for PR #12345 with these agents: reviewer, tester, documenter.
Update the context with the test results.
Show me the complete history of all agent actions on this PR.
```

### 🏗️ Technical Scope

**Package Location:** `packages/tta-agent-context-mcp/`

**Core Tools:**

1. **`create_workflow_context`**
   - Create shared context
   - Input: Metadata, initial state
   - Output: Context ID

2. **`update_context`**
   - Update context state
   - Input: Context ID, updates
   - Output: Updated context

3. **`get_context`**
   - Retrieve context
   - Input: Context ID
   - Output: Full context data

4. **`create_child_context`**
   - Create nested context
   - Input: Parent context ID
   - Output: Child context ID

5. **`get_correlation_chain`**
   - Get causation chain
   - Input: Context ID
   - Output: Parent/child relationships

### 📦 Dependencies

```toml
[project.dependencies]
universal-agent-context = "^0.1.0"
tta-dev-primitives = "^0.1.0"
fastmcp = "^0.1.0"
```

### ✅ Acceptance Criteria

- [ ] All 5 tools implemented
- [ ] Integration with `universal-agent-context`
- [ ] Context persistence working
- [ ] Parent/child relationships tracked
- [ ] 100% test coverage
- [ ] Documentation complete

---

## Issue #4: Create MCP Server Documentation Hub

**Title:** Create Centralized Documentation for TTA.dev MCP Servers

**Labels:** `documentation`, `mcp-server`, `good-first-issue`

**Milestone:** GitHub Agent HQ Integration - Phase 2

**Description:**

### 🎯 Objective

Create a comprehensive documentation hub for all TTA.dev MCP servers in `docs/mcp/`.

### 📋 Deliverables

**Required Files:**

```
docs/mcp/
├── README.md                       # Hub landing page
├── getting-started.md              # Quick start guide
├── installation.md                 # Installation for all servers
├── servers/
│   ├── workflow-primitives.md     # tta-workflow-primitives-mcp
│   ├── observability.md            # tta-observability-mcp
│   └── agent-context.md            # tta-agent-context-mcp
├── examples/
│   ├── basic-workflow.md
│   ├── multi-agent-orchestration.md
│   ├── debugging-with-observability.md
│   └── shared-context-coordination.md
└── guides/
    ├── github-agent-hq-integration.md
    ├── vscode-setup.md
    ├── troubleshooting.md
    └── contributing.md
```

**Hub README should include:**
1. Overview of all MCP servers
2. Quick install commands
3. Common use cases
4. Links to detailed docs
5. Support resources

### ✅ Acceptance Criteria

- [ ] All documentation files created
- [ ] Examples are working and tested
- [ ] Screenshots/GIFs for VS Code integration
- [ ] Cross-links between docs
- [ ] Updated main `MCP_SERVERS.md`

---

## Issue #5: Submit MCP Servers to GitHub Registry

**Title:** Submit TTA.dev MCP Servers to GitHub MCP Registry

**Labels:** `deployment`, `mcp-server`, `high-priority`, `github-agent-hq`

**Milestone:** GitHub Agent HQ Integration - Phase 2

**Description:**

### 🎯 Objective

Submit all TTA.dev MCP servers to GitHub's MCP Registry for one-click installation.

### 📋 Prerequisites

- [ ] Issue #1 complete (workflow primitives)
- [ ] Issue #4 complete (documentation)
- [ ] All tests passing
- [ ] Manifests validated

### 🏗️ Tasks

1. **Prepare Submission Package**
   - [ ] Validate `mcp-manifest.json` for each server
   - [ ] Ensure all metadata complete
   - [ ] Add icons/logos
   - [ ] Create screenshots
   - [ ] Verify license files

2. **Test Installation**
   - [ ] Test via `code --install-mcp`
   - [ ] Test in VS Code UI
   - [ ] Test with GitHub Copilot
   - [ ] Verify all tools work

3. **Submit to Registry**
   - [ ] Create registry submission PR
   - [ ] Respond to review feedback
   - [ ] Get approval
   - [ ] Publish

4. **Post-Launch**
   - [ ] Monitor installation metrics
   - [ ] Track issues/feedback
   - [ ] Update documentation
   - [ ] Marketing announcement

### ✅ Acceptance Criteria

- [ ] All servers published to GitHub MCP Registry
- [ ] Installable via one-click in VS Code
- [ ] All tools discoverable by Copilot
- [ ] Documentation linked from registry
- [ ] Launch blog post published

---

## Issue #6: Create MCP Server Development Kit

**Title:** Build Development Kit for Creating TTA.dev MCP Servers

**Labels:** `enhancement`, `mcp-server`, `developer-experience`

**Milestone:** Community Enablement

**Description:**

### 🎯 Objective

Create a development kit (template + scripts) to help community members create their own MCP servers using TTA.dev primitives.

### 📋 Deliverables

**Package:** `packages/tta-mcp-dev-kit/`

**Includes:**
1. **Template Project Structure**
   - Cookiecutter template
   - Pre-configured pyproject.toml
   - CI/CD workflows
   - Testing boilerplate

2. **CLI Tool**
   ```bash
   tta-mcp create my-custom-server
   tta-mcp add-tool my_tool_name
   tta-mcp test
   tta-mcp validate-manifest
   tta-mcp publish
   ```

3. **Documentation**
   - Step-by-step guide
   - Best practices
   - Testing strategies
   - Publishing checklist

4. **Example Server**
   - Fully commented reference implementation
   - Shows all patterns
   - Ready to customize

### ✅ Acceptance Criteria

- [ ] Template generates valid MCP server
- [ ] CLI tool working for all commands
- [ ] Documentation complete
- [ ] Community successfully uses it
- [ ] Example server published

---

## Issue #7: Build MCP Server for Keploy Integration

**Title:** Create MCP Server for Keploy API Testing

**Labels:** `enhancement`, `mcp-server`, `testing`

**Milestone:** Testing & Quality

**Description:**

### 🎯 Objective

Expose Keploy framework capabilities as MCP tools for AI-assisted API testing.

### 📋 Background

The `keploy-framework` package provides API test recording and replay. This MCP server lets AI agents generate and run API tests.

**Use Case:**
```
@workspace with tta-keploy-mcp

Record API tests for the /api/users endpoint.
Replay recorded tests and show me the results.
Generate test assertions based on the recorded responses.
```

### 🏗️ Core Tools

1. `start_recording` - Start recording API calls
2. `stop_recording` - Stop and save recording
3. `replay_tests` - Replay recorded tests
4. `list_recordings` - List available test recordings
5. `generate_assertions` - AI-generate test assertions

### 📦 Dependencies

```toml
[project.dependencies]
keploy-framework = "^0.1.0"
fastmcp = "^0.1.0"
```

---

## Issue #8: Integration Testing for MCP Servers

**Title:** Create Comprehensive Integration Tests for All MCP Servers

**Labels:** `testing`, `mcp-server`, `ci-cd`

**Milestone:** Quality Assurance

**Description:**

### 🎯 Objective

Build integration test suite that validates all MCP servers work correctly with:
- VS Code
- GitHub Copilot
- Real TTA.dev primitives
- Each other (cross-server interactions)

### 📋 Test Scenarios

1. **Installation Tests**
   - Install via `code --install-mcp`
   - Verify server discovery
   - Verify tool discovery

2. **Tool Execution Tests**
   - Call each tool via Copilot
   - Verify correct responses
   - Test error handling

3. **Cross-Server Tests**
   - Workflow primitives → Observability
   - Workflow primitives → Agent context
   - All three servers together

4. **Performance Tests**
   - Tool response times
   - Concurrent requests
   - Memory usage

### ✅ Acceptance Criteria

- [ ] All test scenarios covered
- [ ] Automated CI/CD pipeline
- [ ] Tests run on every PR
- [ ] Performance benchmarks tracked
- [ ] Documentation for running tests

---

## Summary: Issue Roadmap

| Issue # | Title | Priority | Dependencies | Estimated Effort |
|---------|-------|----------|--------------|------------------|
| #1 | Build `tta-workflow-primitives-mcp` | 🔥 High | None | 1-2 weeks |
| #4 | Create MCP Documentation Hub | 🔥 High | None | 3-5 days |
| #5 | Submit to GitHub Registry | 🔥 High | #1, #4 | 1 week |
| #2 | Build `tta-observability-mcp` | Medium | #1 | 1 week |
| #3 | Build `tta-agent-context-mcp` | Medium | #1 | 1 week |
| #7 | Build Keploy MCP Server | Low | #1 | 1 week |
| #6 | Create MCP Dev Kit | Low | #1, #2, #3 | 2 weeks |
| #8 | Integration Testing | Medium | #1, #2, #3 | 1 week |

### Suggested Order

**Phase 1 (Weeks 1-2):**
1. Issue #1 - Build workflow primitives MCP server
2. Issue #4 - Create documentation hub

**Phase 2 (Week 3):**
3. Issue #5 - Submit to GitHub Registry
4. Launch marketing campaign

**Phase 3 (Weeks 4-6):**
5. Issue #2 - Build observability MCP server
6. Issue #3 - Build agent context MCP server
7. Issue #8 - Integration testing

**Phase 4 (Weeks 7-8):**
8. Issue #7 - Build Keploy MCP server
9. Issue #6 - Create dev kit for community

---

**Ready to create these issues on GitHub?**


---
**Logseq:** [[TTA.dev/Docs/Planning/Github_issues_mcp_servers]]
