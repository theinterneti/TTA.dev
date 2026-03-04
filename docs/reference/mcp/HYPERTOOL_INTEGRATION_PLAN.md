# Hypertool MCP Integration Plan

**Status:** Planning Phase
**Priority:** High - Game Changer
**Impact:** Massive - 89% better tool selection, optimized context usage

---

## 🎯 Executive Summary

Hypertool MCP solves the exact problem we face with 130+ MCP tools causing AI confusion and degraded performance. It provides:

- **Dynamic toolsets** - Switch between focused tool collections on-the-fly
- **Context optimization** - See token costs, optimize tool selections
- **89% better accuracy** - AI picks right tool with focused context
- **Hot-swap in Cursor** - No restarts needed when changing workflows
- **Unlimited servers** - Break free from 100-tool limit

This aligns perfectly with TTA.dev's composable primitives philosophy.

---

## 🔗 Alignment with TTA.dev

### Conceptual Mapping

| TTA.dev Concept | Hypertool Equivalent | Benefit |
|----------------|---------------------|---------|
| **WorkflowPrimitive** | Toolset | Focused, composable units |
| **SequentialPrimitive** | "coding" toolset | Git → Docker → Deploy |
| **ParallelPrimitive** | Multiple toolsets | Debug + Write simultaneously |
| **RouterPrimitive** | Dynamic toolset switch | Route to right tools for task |
| **CachePrimitive** | Context optimization | Reduce token waste |
| **Composition (>>)** | Toolset switching | Chain workflows naturally |

### Philosophy Alignment

```python
# TTA.dev: Compose primitives for workflows
workflow = cache >> router >> retry >> fallback

# Hypertool: Compose toolsets for AI workflows
coding_flow = git_tools + docker_tools + filesystem_tools
debug_flow = logs_tools + traces_tools + monitoring_tools

# Both: Focus on the right tools for the job
```

---

## 📊 Current State Analysis

### Existing TTA.dev Toolsets

From `.vscode/copilot-toolsets.jsonc`:

| Toolset | Tool Count | Purpose |
|---------|-----------|---------|
| `#tta-minimal` | 3 | Quick queries |
| `#tta-package-dev` | 12 | Package development |
| `#tta-testing` | 10 | Testing workflows |
| `#tta-observability` | 12 | Metrics & logs |
| `#tta-agent-dev` | 13 | Agent development |
| `#tta-full-stack` | 20 | ⚠️ Too many tools |

**Problems:**
- ✅ We already recognize the need for focused toolsets
- ❌ Static configuration in JSON
- ❌ No context measurement
- ❌ No hot-swapping (requires VS Code reload)
- ❌ No visibility into tool token costs
- ❌ Manual optimization

### Available MCP Servers

From `MCP_SERVERS.md`:

1. **Context7** - Library documentation
2. **AI Toolkit** - Agent best practices
3. **Grafana** - Prometheus/Loki queries
4. **Pylance** - Python tools
5. **Database Client** - SQL operations
6. **GitHub PR** - PR reviews
7. **Sift** - Investigation analysis
8. **LogSeq** - Knowledge base (disabled)

**Total:** 8 MCP servers, ~50-60 tools

---

## 🚀 Implementation Strategy

### Phase 1: Setup & Discovery (Week 1)

**Goal:** Get Hypertool running and measure current state

#### 1.1 Install Hypertool

```bash
# Add to project dependencies
uv add @toolprint/hypertool-mcp

# Or use npx (no install)
npx -y @toolprint/hypertool-mcp --version
```

#### 1.2 Configure Hypertool

```bash
# Copy existing MCP config
cp .mcp.json .mcp.hypertool.json

# Update .mcp.json to use Hypertool
cat > .mcp.json << 'EOF'
{
  "mcpServers": {
    "hypertool": {
      "command": "npx",
      "args": [
        "-y",
        "@toolprint/hypertool-mcp",
        "mcp",
        "run",
        "--mcp-config",
        ".mcp.hypertool.json"
      ]
    }
  }
}
EOF
```

#### 1.3 Measure Current Tools

Use Hypertool to analyze all available tools:

```bash
# In Copilot Chat:
@workspace List all available tools with token estimates

# Expected output:
# - mcp_github_github_create_pull_request (450 tokens)
# - mcp_grafana_query_prometheus (380 tokens)
# - mcp_pylance_mcp_s_pylanceRunCodeSnippet (520 tokens)
# ... etc
```

**Deliverable:** Token analysis report showing:
- Total tools available
- Token cost per tool
- High-cost tools to optimize
- Grouping recommendations

#### 1.4 Test Hot-Swap

```bash
# In Cursor/VSCode:
@workspace Create toolset "quick-test" with search and problems tools

@workspace Switch to "quick-test" toolset

@workspace Show active toolset with token usage
```

**Success Criteria:**
- Hypertool responds to commands
- Can create/switch toolsets without restart
- Token estimates displayed correctly

### Phase 2: TTA.dev Toolset Migration (Week 2)

**Goal:** Migrate existing static toolsets to dynamic Hypertool toolsets

#### 2.1 Core Development Toolsets

Recreate current toolsets with optimization:

```typescript
// tta-minimal (3 tools → optimize to 2-3 tools)
{
  "name": "tta-minimal",
  "tools": [
    "search",
    "think"
  ],
  "description": "Lightweight queries - under 300 tokens"
}

// tta-package-dev (12 tools → optimize to 8-10 tools)
{
  "name": "tta-package-dev",
  "tools": [
    "edit",
    "search",
    "usages",
    "problems",
    "mcp_pylance_mcp_s_pylanceRunCodeSnippet",
    "mcp_pylance_mcp_s_pylanceFileSyntaxErrors",
    "configure_python_environment",
    "run_task"
  ],
  "description": "Core package development - under 2000 tokens"
}

// tta-observability (12 tools → optimize to 6-8 tools)
{
  "name": "tta-observability",
  "tools": [
    "mcp_grafana_query_prometheus",
    "mcp_grafana_query_loki_logs",
    "mcp_grafana_list_alert_rules",
    "search",
    "problems",
    "think"
  ],
  "description": "Metrics & logs - under 1500 tokens"
}
```

**Token Budget Goals:**
- Minimal: <300 tokens
- Focused: <2000 tokens
- Comprehensive: <4000 tokens
- ⚠️ Avoid: >5000 tokens (context waste)

#### 2.2 Specialized Toolsets

Create new optimized toolsets:

```typescript
// Adaptive Primitives Development
{
  "name": "tta-adaptive-dev",
  "tools": [
    "edit",
    "search",
    "mcp_pylance_mcp_s_pylanceRunCodeSnippet",
    "mcp_grafana_query_prometheus",  // For observing learning
    "mcp_context7_get-library-docs",  // For research
    "run_task"
  ],
  "description": "Self-improving primitives development"
}

// LogSeq Integration (when enabled)
{
  "name": "tta-knowledge-base",
  "tools": [
    "mcp_logseq_search",
    "mcp_logseq_create_page",
    "mcp_logseq_update_page",
    "search",
    "think"
  ],
  "description": "Knowledge base management"
}

// E2B Code Execution
{
  "name": "tta-code-validation",
  "tools": [
    "mcp_e2b_execute_code",
    "edit",
    "search",
    "mcp_pylance_mcp_s_pylanceFileSyntaxErrors",
    "think"
  ],
  "description": "Validate generated code in sandbox"
}
```

#### 2.3 Token Optimization

For each toolset:

1. **Measure baseline:** Run `get-active-toolset` to see current token usage
2. **Remove heavy tools:** Identify tools >500 tokens that aren't essential
3. **Add annotations:** Enhance tool descriptions to improve selection
4. **Validate:** Test with real workflows

**Example Optimization:**

```typescript
// Before: 12 tools, 5400 tokens
"tta-full-stack": {
  "tools": [/* 20 tools */],
  "description": "Everything"
}

// After: 8 tools, 2200 tokens (59% reduction)
"tta-full-stack-optimized": {
  "tools": [
    "mcp_grafana_query_prometheus",
    "mcp_database_execute_query",
    "mcp_context7_get-library-docs",
    "edit",
    "search",
    "problems",
    "run_task",
    "think"
  ],
  "description": "Essential full-stack tools"
}
```

#### 2.4 Documentation Update

Update `docs/guides/copilot-toolsets-guide.md`:

```markdown
## Hypertool-Powered Toolsets

TTA.dev uses Hypertool MCP for dynamic, optimized toolsets with:

- **Token measurement** - See exact context cost per tool
- **Hot-swapping** - Change toolsets without restart (Cursor/VSCode)
- **89% better selection** - AI picks right tool with focused context

### Quick Start

# Create toolset
@workspace Create toolset "my-workflow" with git, docker, and filesystem tools

# Switch toolset (no restart!)
@workspace Switch to "my-workflow" toolset

# Check context usage
@workspace Show active toolset with token costs

### Available Toolsets

| Toolset | Tools | Token Budget | Use For |
|---------|-------|-------------|---------|
| tta-minimal | 2-3 | <300 | Quick queries |
| tta-package-dev | 8-10 | <2000 | Package development |
| tta-adaptive-dev | 6-8 | <1800 | Self-improving primitives |
| tta-observability | 6-8 | <1500 | Metrics & debugging |
```

**Deliverable:** Migrated toolsets with:
- Token budgets documented
- Optimization strategies applied
- User guide updated
- Hot-swap workflows documented

### Phase 3: Advanced Features (Week 3)

**Goal:** Leverage Hypertool's advanced capabilities

#### 3.1 Tool Annotations

Enhance tools with examples and context:

```typescript
// Add custom annotations for better AI tool selection
{
  "toolset": "tta-package-dev",
  "annotations": {
    "mcp_pylance_mcp_s_pylanceRunCodeSnippet": {
      "description": "Execute Python code in workspace context. PREFERRED over terminal for testing snippets. Handles imports, async, proper error reporting.",
      "examples": [
        "Test if a function works before committing",
        "Validate imports are available",
        "Check syntax without creating files"
      ],
      "when_to_use": "Always prefer this over 'python -c' or terminal execution"
    }
  }
}
```

**Research shows:** Custom annotations improve tool selection accuracy by 89%

#### 3.2 Personas for TTA.dev

Create pre-configured personas for common workflows:

```bash
# TTA.dev Primitive Developer
{
  "name": "tta-primitive-dev",
  "servers": ["pylance", "github", "context7"],
  "toolsets": {
    "default": "tta-package-dev",
    "testing": "tta-testing",
    "docs": "tta-docs"
  }
}

# TTA.dev Observability Engineer
{
  "name": "tta-observability-eng",
  "servers": ["grafana", "pylance", "github"],
  "toolsets": {
    "default": "tta-observability",
    "debugging": "tta-troubleshoot"
  }
}

# TTA.dev Agent Developer
{
  "name": "tta-agent-dev",
  "servers": ["context7", "ai-toolkit", "github", "e2b"],
  "toolsets": {
    "default": "tta-agent-dev",
    "validation": "tta-code-validation"
  }
}
```

**Usage:**

```bash
# Start with persona
npx -y @toolprint/hypertool-mcp mcp run --persona tta-primitive-dev

# Switch toolsets within persona
@workspace Switch to testing toolset
```

#### 3.3 HTTP Mode for Performance

For long-running development sessions:

```bash
# Start Hypertool as HTTP server
npx -y @toolprint/hypertool-mcp mcp http --port 3000

# Configure Cursor/VSCode to connect
{
  "mcpServers": {
    "hypertool": {
      "url": "http://localhost:3000"
    }
  }
}
```

**Benefits:**
- Faster response times
- Persistent connections
- Better resource utilization

#### 3.4 Server Groups

Organize MCP servers by purpose:

```typescript
{
  "serverGroups": {
    "development": ["pylance", "github", "filesystem"],
    "observability": ["grafana", "prometheus", "loki"],
    "research": ["context7", "ai-toolkit"],
    "validation": ["e2b", "pylance"]
  }
}
```

**Usage:**

```bash
# Launch group of servers
@workspace Load development server group

# Switch groups
@workspace Switch to observability server group
```

**Deliverable:** Advanced configuration with:
- Annotated tools for better selection
- 3-5 TTA.dev personas
- HTTP mode setup for performance
- Server groups for workflow isolation

### Phase 4: Integration & Validation (Week 4)

**Goal:** Full integration testing and documentation

#### 4.1 Integration Tests

Test all workflows with Hypertool:

```python
# tests/integration/test_hypertool_toolsets.py
import pytest
from tta_dev_primitives import WorkflowContext

@pytest.mark.asyncio
async def test_package_dev_toolset():
    """Verify tta-package-dev toolset works end-to-end."""
    # 1. Switch to toolset
    # 2. Execute package development workflow
    # 3. Validate correct tools used
    # 4. Check token usage within budget
    pass

@pytest.mark.asyncio
async def test_hot_swap_performance():
    """Verify hot-swapping doesn't degrade performance."""
    # 1. Measure baseline with static toolset
    # 2. Measure with Hypertool hot-swap
    # 3. Assert <100ms overhead
    pass

@pytest.mark.asyncio
async def test_context_optimization():
    """Verify token budgets are respected."""
    # 1. Activate toolset
    # 2. Get active toolset info
    # 3. Parse token usage
    # 4. Assert within documented budget
    pass
```

#### 4.2 Documentation

Complete documentation suite:

1. **Hypertool Integration Guide** (this file)
2. **User Guide** - How to use toolsets in daily development
3. **Migration Guide** - Transition from static toolsets
4. **Optimization Guide** - Token budgeting strategies
5. **Troubleshooting** - Common issues and solutions

#### 4.3 VS Code Integration

Update workspace settings:

```json
// .vscode/settings.json
{
  "hypertool.enableHotSwap": true,
  "hypertool.showTokenUsage": true,
  "hypertool.defaultToolset": "tta-package-dev",
  "hypertool.autoOptimize": true
}
```

#### 4.4 CI/CD Integration

Add Hypertool checks to CI:

```yaml
# .github/workflows/hypertool-validation.yml
name: Hypertool Validation

on: [pull_request]

jobs:
  validate-toolsets:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install Hypertool
        run: npm install -g @toolprint/hypertool-mcp

      - name: Validate Toolset Configs
        run: |
          hypertool-mcp validate-config .mcp.hypertool.json

      - name: Check Token Budgets
        run: |
          hypertool-mcp analyze-tokens --fail-if-over-budget

      - name: Test Hot-Swap
        run: |
          python tests/integration/test_hypertool_toolsets.py
```

**Deliverable:** Production-ready integration with:
- Full test coverage
- Complete documentation
- VS Code configuration
- CI/CD validation

---

## 📊 Expected Benefits

### Quantitative Improvements

| Metric | Before Hypertool | After Hypertool | Improvement |
|--------|-----------------|-----------------|-------------|
| Tool Selection Accuracy | ~60% | ~89% | **+48%** |
| Context Token Usage | ~8000 tokens | ~2000 tokens | **-75%** |
| Tool Switch Time | 30-60s (reload) | <1s (hot-swap) | **-97%** |
| AI Response Quality | Baseline | +89% accuracy | **+89%** |
| Developer Productivity | Baseline | +40% (est) | **+40%** |

### Qualitative Benefits

1. **Better AI Performance**
   - AI picks right tool 89% of time
   - Less context confusion
   - More focused responses

2. **Developer Experience**
   - Instant toolset switching
   - Visibility into token costs
   - Optimized workflows

3. **Cost Optimization**
   - 75% less context waste
   - Reduced API calls from better tool selection
   - Lower LLM costs overall

4. **Alignment with TTA.dev**
   - Composable toolsets = composable primitives
   - Dynamic adaptation = adaptive primitives
   - Measurable optimization = observability

---

## 🎯 Success Metrics

### Phase 1: Setup (Week 1)
- [ ] Hypertool installed and configured
- [ ] All 8 MCP servers accessible
- [ ] Token analysis complete
- [ ] Hot-swap verified in Cursor

### Phase 2: Migration (Week 2)
- [ ] All existing toolsets migrated
- [ ] Token budgets documented
- [ ] 20-30% token reduction achieved
- [ ] User guide updated

### Phase 3: Advanced (Week 3)
- [ ] Tool annotations added
- [ ] 3-5 personas created
- [ ] HTTP mode configured
- [ ] Server groups defined

### Phase 4: Integration (Week 4)
- [ ] Integration tests passing
- [ ] Documentation complete
- [ ] VS Code settings optimized
- [ ] CI/CD validation added

### Overall Success
- [ ] 89% tool selection accuracy achieved
- [ ] 75% context token reduction
- [ ] <1s toolset switching
- [ ] Developer productivity measurably improved

---

## 🚧 Potential Challenges

### Challenge 1: Learning Curve

**Risk:** Team needs to learn Hypertool concepts

**Mitigation:**
- Start with simple migration
- Comprehensive documentation
- Interactive tutorials
- Gradual rollout

### Challenge 2: MCP Server Compatibility

**Risk:** Not all MCP servers work perfectly with Hypertool

**Mitigation:**
- Test each server individually
- Document any quirks
- Contribute fixes upstream
- Maintain fallback configs

### Challenge 3: Token Estimation Accuracy

**Risk:** BPE approximation may not match actual tokenizer

**Mitigation:**
- Use for relative comparisons, not absolutes
- Validate with real LLM usage
- Document known discrepancies
- Regular calibration

### Challenge 4: Configuration Complexity

**Risk:** More moving parts to maintain

**Mitigation:**
- Automated validation in CI
- Version control all configs
- Clear documentation
- Regular audits

---

## 🔄 Rollback Plan

If Hypertool causes issues:

1. **Immediate Rollback:**
   ```bash
   # Restore original config
   cp .mcp.json.backup .mcp.json
   # Reload VS Code
   ```

2. **Gradual Fallback:**
   - Keep static toolsets in parallel
   - Switch back to `.vscode/copilot-toolsets.jsonc`
   - Document lessons learned

3. **Hybrid Approach:**
   - Use Hypertool for development
   - Use static toolsets for production
   - Transition gradually

---

## 📚 Related Documentation

- **Hypertool Repository:** https://github.com/toolprint/hypertool-mcp
- **Personas Guide:** https://github.com/toolprint/hypertool-mcp/blob/main/guides/PERSONAS.md
- **Research & Performance:** https://github.com/toolprint/hypertool-mcp/blob/main/guides/RESEARCH.md
- **Advanced Features:** https://github.com/toolprint/hypertool-mcp/blob/main/guides/ADVANCED.md
- **TTA.dev MCP Servers:** `/home/thein/repos/TTA.dev/MCP_SERVERS.md`
- **TTA.dev Toolsets Guide:** `/home/thein/repos/TTA.dev/docs/guides/copilot-toolsets-guide.md`

---

## 🎬 Next Steps

1. **Review this plan** with team
2. **Get approval** for implementation
3. **Start Phase 1** - Setup & Discovery
4. **Track progress** in Logseq journal
5. **Document learnings** throughout

---

**Created:** 2025-11-14
**Status:** Planning
**Owner:** TTA.dev Team
**Priority:** High
**Estimated Effort:** 4 weeks
**Expected Impact:** Massive - Game changer for AI-assisted development


---
**Logseq:** [[TTA.dev/Docs/Mcp/Hypertool_integration_plan]]
