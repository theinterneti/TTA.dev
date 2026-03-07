---
type: "always_apply"
description: "Guide for selecting and using MCP (Model Context Protocol) servers effectively"
---

# MCP Tool Selection Guide

**For AI Agent Use Only** - Strategic guidance for selecting and using MCP (Model Context Protocol) servers.

## What Are MCP Servers?

**MCP (Model Context Protocol) servers** are specialized capabilities that extend the AI agent's functionality beyond basic code operations. They provide:

- **Browser Automation** (Playwright) - Interact with web applications, run E2E tests
- **Documentation Lookup** (Context7) - Fetch current, AI-friendly library documentation
- **Complex Reasoning** (Sequential thinking) - Structure multi-step problem-solving
- **GitHub Operations** (GitHub) - Interact with GitHub API (issues, PRs, commits)
- **Semantic Code Operations** (Serena) - Navigate, refactor, and analyze code semantically
- **Database Operations** (Neo4j, Redis) - Interact with graph and key-value databases
- **Community Data** (Reddit) - Access Reddit discussions and community knowledge

## MCP Servers vs Other Tools

### MCP Servers vs CLI Tools

**MCP Servers:**
- Always available as function calls
- Integrated into agent's tool interface
- Provide structured, programmatic access
- Return parsed, actionable data
- Examples: Playwright, Context7, Serena, GitHub

**CLI Tools:**
- Require execution via `launch-process`
- Run in shell environment
- Return raw text output
- Require parsing and interpretation
- Examples: `uvx pytest`, `uvx ruff`, `git`, `docker`

**When to use MCP servers:** Prefer MCP servers when available - they provide better integration, error handling, and structured data.

**When to use CLI tools:** Use CLI tools for operations not covered by MCP servers, or when you need direct shell access (e.g., running build scripts, package managers).

### MCP Servers vs Direct File Operations

**MCP Servers (e.g., Serena):**
- Semantic understanding of code structure
- Symbol-level operations (find class, rename function)
- Language-aware refactoring
- Cross-reference tracking

**Direct File Operations (view, str-replace-editor):**
- Text-based file reading/editing
- Line-by-line operations
- Simple pattern matching
- No semantic understanding

**When to use MCP servers:** Prefer MCP servers for code navigation, refactoring, and analysis.

**When to use direct file operations:** Use for simple file reading, text editing, or when MCP server is unavailable.

## Tool Selection Decision Tree

```
Need to interact with code?
├─ Yes → Use Serena MCP (see use-serena-tools.md)
│   ├─ Find symbols, navigate code structure
│   ├─ Refactor code semantically
│   └─ Track references and dependencies
│
Need to interact with web applications?
├─ Yes → Use Playwright MCP
│   ├─ Run E2E tests
│   ├─ Automate browser interactions
│   └─ Scrape web content
│
Need library documentation?
├─ Yes → Use Context7 MCP
│   ├─ Fetch current API docs
│   ├─ Get usage examples
│   └─ Verify library features
│
Need to solve complex multi-step problems?
├─ Yes → Use Sequential Thinking MCP
│   ├─ Break down complex tasks
│   ├─ Track reasoning steps
│   └─ Maintain problem-solving context
│
Need to interact with GitHub?
├─ Yes → Use GitHub MCP
│   ├─ Create/update issues and PRs
│   ├─ Query repository data
│   └─ Manage project boards
│
Need to interact with databases?
├─ Yes → Use Database MCP (Neo4j, Redis)
│   ├─ Query graph data (Neo4j)
│   ├─ Manage key-value data (Redis)
│   └─ Execute database operations
│
Need to run CLI tools?
└─ Yes → Use launch-process
    ├─ Run tests (uvx pytest)
    ├─ Run linters (uvx ruff)
    └─ Execute build scripts
```

## Individual MCP Server Rule Files

Each MCP server has (or should have) its own dedicated rule file following a consistent pattern:

### Existing MCP Server Rules

- **`use-serena-tools.md`** - Semantic code operations (navigation, refactoring, analysis)
  - ✅ Comprehensive guide with examples (437 lines)
  - ✅ Clear trigger conditions and use cases
  - ✅ Anti-patterns and troubleshooting

- **`use-playwright.md`** - Browser automation and E2E testing
  - ✅ Comprehensive guide with 13 browser automation tools (448 lines)
  - ✅ E2E testing, form filling, screenshot capture
  - ✅ Performance considerations and TTA-specific use cases

- **`use-context7.md`** - Library documentation lookup
  - ✅ Comprehensive guide with 2 documentation tools (420 lines)
  - ✅ Up-to-date library docs, API references, version-specific docs
  - ✅ Integration with prefer-uvx-for-tools.md

- **`use-sequential-thinking.md`** - Complex multi-step reasoning
  - ✅ Comprehensive guide with structured reasoning tool (300 lines)
  - ✅ Hypothesis testing, branching exploration, decision revision
  - ✅ Integration with ai-context-management.md

- **`use-github.md`** - GitHub API operations
  - ✅ Comprehensive guide with GitHub API tool (300 lines)
  - ✅ Issue management, PR operations, CI/CD status
  - ✅ Integration with integrated-workflow.md

- **`use-redis.md`** - Redis database operations
  - ✅ Comprehensive guide with 40+ Redis tools (470 lines)
  - ✅ Hash, JSON, list, set, sorted set, stream, vector search, pub/sub
  - ✅ Caching, state management, real-time messaging

**Pattern for Individual MCP Server Rules:**
1. Rule priority and trigger conditions
2. Concrete examples with actual tool calls
3. Use cases and anti-patterns
4. When to use this MCP server vs alternatives
5. Integration with other rules
6. Troubleshooting section

## Integration with Other Rules

### Code Operations
- **Primary:** Use Serena MCP for semantic code operations (see `use-serena-tools.md`)
- **Fallback:** Use `view` and `str-replace-editor` for simple text operations
- **Complement:** Use `codebase-retrieval` for high-level code search

### CLI Tool Execution
- **Primary:** Use `uvx` for standalone development tools (see `prefer-uvx-for-tools.md`)
- **Context:** Use `uv run` for project-specific scripts
- **Integration:** Use within workflows (see `integrated-workflow.md`)

### Development Workflows
- **Context Management:** Track decisions with AI context (see `ai-context-management.md`)
- **Integrated Workflow:** Use MCP servers within spec-to-production pipeline (see `integrated-workflow.md`)
- **Code Quality:** Maintain file size limits (see `avoid-long-files.md`)

## Best Practices

### 1. Prefer MCP Servers Over CLI Tools
When both options are available, prefer MCP servers for better integration and structured data.

**Example:**
```
✅ Good: Use GitHub MCP to create issue
❌ Avoid: Use `gh issue create` via launch-process (unless MCP unavailable)
```

### 2. Use Appropriate MCP Server for Task
Match the MCP server to the task type - don't use Playwright for code navigation or Serena for web scraping.

**Example:**
```
✅ Good: Use Serena to find all classes named "Agent"
❌ Avoid: Use grep via launch-process for code search
```

### 3. Combine MCP Servers When Needed
Some tasks require multiple MCP servers working together.

**Example:**
```
1. Use Context7 to fetch FastAPI documentation
2. Use Serena to find existing API routes
3. Use str-replace-editor to add new route
4. Use GitHub MCP to create PR
```

### 4. Leverage Parallel Tool Calls
When using multiple MCP servers, call them in parallel when possible.

**Example:**
```
✅ Good: Call Serena and codebase-retrieval in parallel
❌ Avoid: Sequential calls when operations are independent
```

## Common Patterns

### Pattern 1: Documentation-Driven Development
```
1. Use Context7 to fetch library documentation
2. Use Serena to find existing usage patterns
3. Implement feature following documented patterns
4. Use GitHub MCP to create PR with documentation links
```

### Pattern 2: Test-Driven Refactoring
```
1. Use Serena to find symbol and its references
2. Use Playwright to run E2E tests (baseline)
3. Use Serena to refactor code
4. Use Playwright to verify tests still pass
```

### Pattern 3: Issue-Driven Development
```
1. Use GitHub MCP to fetch issue details
2. Use Serena to locate relevant code
3. Use Sequential Thinking to plan implementation
4. Implement changes
5. Use GitHub MCP to update issue and create PR
```

## Troubleshooting

### MCP Server Not Responding
**Symptom:** Tool call times out or returns error

**Solutions:**
1. Check if MCP server is configured correctly
2. Verify network connectivity (for remote MCP servers)
3. Fall back to alternative approach (CLI tools, direct file operations)
4. Report issue to user if persistent

### Choosing Between Similar MCP Servers
**Symptom:** Multiple MCP servers seem applicable

**Solutions:**
1. Consult tool selection decision tree above
2. Prefer more specialized MCP server (e.g., Serena for code vs view)
3. Consider data structure needs (structured vs raw text)
4. Check individual MCP server rule files for guidance

### MCP Server Returns Unexpected Data
**Symptom:** Tool returns data in unexpected format

**Solutions:**
1. Verify tool call parameters match expected signature
2. Check individual MCP server rule file for examples
3. Inspect returned data structure before processing
4. Add error handling for unexpected formats

## Summary

**Default approach:** Use MCP servers when available - they provide better integration than CLI tools

**Tool selection:** Match MCP server to task type (code → Serena, web → Playwright, docs → Context7, etc.)

**Best practice:** Consult individual MCP server rule files for detailed guidance on each tool

**Pattern:** Each MCP server should have its own dedicated rule file following the `use-serena-tools.md` pattern

---

**Status:** Active (Meta-Level Guide)
**Last Updated:** 2025-10-22
**Related Rules:** `use-serena-tools.md`, `use-playwright.md`, `use-context7.md`, `use-sequential-thinking.md`, `use-github.md`, `use-redis.md`, `prefer-uvx-for-tools.md`, `integrated-workflow.md`


---
**Logseq:** [[TTA.dev/Platform_tta_dev/Components/Augment/Core/Rules/Use-your-tools]]
