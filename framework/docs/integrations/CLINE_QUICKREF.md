# Cline Quick Reference for TTA.dev

**One-Page Cheat Sheet for Copilot ↔ Cline Collaboration**

---

## When to Use What

| Task | Tool | Why |
|------|------|-----|
| Quick edit (1-3 files) | **Copilot** | Faster, in-chat |
| Explanation | **Copilot** | Optimized for conversation |
| Multi-file refactor (5+ files) | **Cline** | Autonomous, shows diffs |
| Complex implementation | **Cline** | Persistent, iterative |
| PR review | **Cline** | GitHub CLI integration |
| Planning/architecture | **Copilot** | Better for discussion |
| Terminal operations | **Cline** | Native shell integration |
| Documentation writing | **Copilot** | Better prose |

---

## Essential Commands

### Cline CLI

```bash
# Interactive mode
cline

# One-shot task
cline "Add tests to CachePrimitive"

# Autonomous (no approvals)
cline -y "Fix all ruff errors"

# Pipe context
cat file.py | cline task send "Add docstrings"

# Send to existing task
cline task send "Now add the tests"
```

### Cline in VS Code

```plaintext
# Start task
"Create a new primitive called X"

# With MCP
"Using Context7, find docs for Y"

# PR review
"Review PR #42"

# Approve/Reject
Click Save/Reject in diff view
```

### Copilot → Cline Handoff

```markdown
## In Copilot (@workspace #tta-cline)

User: "Refactor RouterPrimitive across all packages"

Copilot: "This affects 12 files. Let me prepare for Cline:

@cline Please refactor RouterPrimitive:
- Update all imports
- Change method signatures
- Update tests
- Verify with: uv run pytest
- Files: [list]
```

---

## Workflows

### PR Review

```plaintext
@cline Review PR #42

Cline will:
1. Fetch PR: gh pr view 42 --json ...
2. Get diff: gh pr diff 42
3. Analyze code quality
4. Check tests/docs
5. Provide recommendation
6. Ask to post review
```

### New Primitive

```plaintext
@cline Create a new RateLimitPrimitive:
- Category: performance
- Input: request details
- Output: allowed/denied
- Include tests and docs

Cline will:
1. Create primitive file
2. Add InstrumentedPrimitive base
3. Write tests (100% coverage)
4. Update PRIMITIVES_CATALOG.md
5. Create example
```

### Refactoring

```plaintext
@cline Refactor to use new context pattern:
1. Analyze affected files
2. Show plan for approval
3. Execute incrementally
4. Test after each change
5. Final validation
```

---

## MCP Integration

### Available Servers

- **Context7** - Library docs
- **Grafana** - Metrics/logs
- **Pylance** - Python tools
- **Logseq** - Knowledge base
- **GitHub** - PR operations

### Usage

```plaintext
"Using Context7, find async patterns for httpx"
"Using Grafana, show error rate last hour"
"Using Logseq, find my TODO for primitives"
```

---

## GitHub Actions

### Basic PR Review

```yaml
- name: Cline Review
  run: |
    gh pr view $PR --json title,body,comments > pr.json
    gh pr diff $PR > diff.txt
    cat << EOF | cline -y
    Review this PR: $(cat pr.json)
    Diff: $(cat diff.txt)
    EOF
```

### Auto-Fix

```yaml
- name: Fix Ruff Errors
  run: |
    uv run ruff check . > errors.txt || true
    cat errors.txt | cline -y task send "Fix all errors"
```

---

## Configuration

### API Providers

```json
{
  "apiProvider": "anthropic",
  "apiKey": "sk-ant-...",
  "apiModelId": "claude-3-5-sonnet-20241022"
}
```

### MCP Servers

```json
{
  "mcpServers": {
    "context7": { "command": "...", "args": [...] },
    "grafana": { "command": "...", "args": [...] }
  }
}
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| MCP not working | Reload window, check ~/.config/mcp/mcp_settings.json |
| API errors | Verify key in Settings → API Config |
| Terminal fails | Enable shell integration in VS Code settings |
| High costs | Switch to GPT-3.5 or Ollama (local) |
| Changes not applying | Check file permissions, git status |

---

## Best Practices

### ✅ DO

- Review all diffs before approving
- Run tests after Cline changes
- Use version control
- Leverage MCP servers
- Collaborate with Copilot

### ❌ DON'T

- Blindly approve multi-file changes
- Skip running tests
- Use expensive models for simple tasks
- Ignore API usage/costs

---

## Copilot Toolset

```jsonc
// .vscode/copilot-toolsets.jsonc
"tta-cline": {
  "tools": ["search", "read_file", "problems", "think", "todos"],
  "description": "Cline collaboration",
  "icon": "robot"
}
```

**Usage:**

```plaintext
@workspace #tta-cline
"Analyze RouterPrimitive and prepare Cline task for refactoring"
```

---

## Cost Management

### Model Selection

| Model | Cost | Use For |
|-------|------|---------|
| Claude 3.5 Sonnet | $$$ | Complex tasks |
| GPT-4 | $$$ | Complex reasoning |
| GPT-3.5 | $ | Simple tasks |
| Ollama (local) | Free | Dev/testing |

### Budget Tips

- Use local models for routine tasks
- Cache aggressively
- Monitor usage weekly
- Set budget alerts

---

## Example Session

```plaintext
User: "@workspace #tta-cline I need to add observability to CachePrimitive"

Copilot: "That's complex. Here's what's needed:
- Add OpenTelemetry spans
- Add Prometheus metrics
- Update tests
- Update docs

@cline Please add observability to CachePrimitive following the
InstrumentedPrimitive pattern in tta-observability-integration."

Cline:
1. Analyzes existing code
2. Shows implementation plan
3. Asks for approval
4. Implements changes
5. Shows diffs for each file
6. Runs tests
7. Updates documentation

User: [Reviews diffs] "Looks good!"

Cline: "Changes saved. Tests passing ✅"

User: "@workspace Review Cline's work"

Copilot: "Great job! Observability added correctly. One suggestion:
add metric for cache evictions."

User: "@cline Add eviction metric"

Cline: "Added cache_evictions_total. Updated tests."
```

---

## Resources

- **Full Evaluation:** [CLINE_INTEGRATION_EVALUATION.md](./CLINE_INTEGRATION_EVALUATION.md)
- **Setup Guide:** [CLINE_INTEGRATION_GUIDE.md](./CLINE_INTEGRATION_GUIDE.md)
- **MCP Servers:** [../../MCP_SERVERS.md](../../MCP_SERVERS.md)
- **Copilot Toolsets:** [../../.vscode/copilot-toolsets.jsonc](../../.vscode/copilot-toolsets.jsonc)

---

**Quick Start:** Install extension → Configure API → Run first task → Collaborate! 🚀
