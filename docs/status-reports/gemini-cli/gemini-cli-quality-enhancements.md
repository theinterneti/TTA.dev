# Gemini CLI Quality Enhancements

**Quality-first improvements with generous Pro tier + expanded MCP capabilities**

**Date:** October 31, 2025
**Status:** Ready for Implementation
**Priority:** Quality over Speed

---

## 🎯 Overview

This document outlines enhancements to the Gemini CLI integration focusing on:

1. **Quality-First Models** - Using Gemini Pro's generous free tier
2. **Extended MCP Capabilities** - Context7, Universal Agent Context, and more
3. **A/B Testing Framework** - Ready for model comparison and optimization
4. **Graceful Degradation** - Rate limit handling and fallbacks

---

## 📊 Gemini Model Tiers (Free Tier)

### Recommended Quality Stack

**Primary: Gemini 2.0 Flash Thinking (Extended Reasoning)**
```yaml
model: gemini-2.0-flash-thinking-exp-1219
limits:
  context_window: 1M tokens
  rate_limit: Higher than Pro (experimental)
  cost: FREE
benefits:
  - Shows reasoning process
  - Extended chain-of-thought
  - Best balance: quality + transparency
use_for: Complex analysis, architectural decisions, code reviews
```

**Secondary: Gemini 1.5 Pro (Proven Quality)**
```yaml
model: gemini-1.5-pro-002
limits:
  requests_per_minute: 2
  tokens_per_minute: 32,000
  requests_per_day: 1,500
  context_window: 2M tokens
  cost: FREE
benefits:
  - Highest quality reasoning
  - Largest context window
  - Production stable
use_for: Critical decisions, complex refactors, documentation
```

**Tertiary: Gemini 2.0 Flash (Speed)**
```yaml
model: gemini-2.0-flash-exp
limits:
  rate_limit: Higher RPM
  context_window: 1M tokens
  cost: FREE
benefits:
  - Fastest response times
  - Good for simple tasks
use_for: Quick reviews, triage, simple questions
```

---

## 🛠️ Multi-MCP Configuration

### Available MCP Servers

#### 1. Context7 - Library Documentation
```yaml
mcpServers:
  context7:
    command: "npx"
    args: ["-y", "@context7/mcp-server"]
    includeTools:
      - resolve-library-id
      - get-library-docs
    env:
      CONTEXT7_API_KEY: "${CONTEXT7_API_KEY}"
```

**Use Cases:**
- Look up API documentation during code reviews
- Find best practices for libraries
- Validate implementation patterns

#### 2. Universal Agent Context - Memory Management
```yaml
mcpServers:
  agent-context:
    command: "python"
    args: ["-m", "universal_agent_context.mcp_server"]
    includeTools:
      - store_memory
      - retrieve_memory
      - query_decisions
      - list_architecture_decisions
    env:
      MEMORY_STORE: "${GITHUB_WORKSPACE}/.agent-memory"
```

**Use Cases:**
- Remember architectural decisions across sessions
- Track patterns and anti-patterns
- Maintain consistency in large refactors

#### 3. GitHub MCP (Current)
```yaml
mcpServers:
  github:
    command: "docker"
    args:
      - "run"
      - "-i"
      - "--rm"
      - "-e"
      - "GITHUB_PERSONAL_ACCESS_TOKEN"
      - "ghcr.io/github/github-mcp-server:v0.20.1"
    includeTools:
      # ... existing 18 tools ...
```

#### 4. Prometheus/Grafana - Observability (Optional)
```yaml
mcpServers:
  grafana:
    command: "docker"
    args:
      - "run"
      - "-i"
      - "--rm"
      - "-e"
      - "GRAFANA_URL"
      - "-e"
      - "GRAFANA_TOKEN"
      - "ghcr.io/grafana/mcp-grafana-server:latest"
    includeTools:
      - query_prometheus
      - query_loki_logs
      - get_alert_rules
```

**Use Cases:**
- Check metrics during performance reviews
- Query logs for debugging
- Validate observability instrumentation

#### 5. Database Client - Schema Analysis (Optional)
```yaml
mcpServers:
  database:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-postgres"]
    includeTools:
      - list_tables
      - describe_table
      - query
    env:
      DATABASE_URL: "${DATABASE_URL}"
```

**Use Cases:**
- Review schema changes in PRs
- Validate migrations
- Generate documentation

---

## 🔄 A/B Testing Framework

### Model Selection Strategy

Create a flexible model selection system that can:
1. Choose model based on task complexity
2. Fall back gracefully on rate limits
3. Track performance metrics
4. A/B test different models

### Implementation: Enhanced Workflow

```yaml
name: Gemini Invoke (Quality-First with A/B Testing)

on:
  workflow_dispatch:
    inputs:
      model_tier:
        description: 'Model tier (thinking|pro|fast|auto)'
        required: false
        default: 'auto'
        type: choice
        options:
          - auto
          - thinking
          - pro
          - fast

      enable_ab_testing:
        description: 'Enable A/B testing (compare models)'
        required: false
        default: false
        type: boolean

      mcp_servers:
        description: 'MCP servers to enable (comma-separated)'
        required: false
        default: 'github,context7,agent-context'

jobs:
  select-model:
    runs-on: ubuntu-latest
    outputs:
      primary_model: ${{ steps.select.outputs.primary_model }}
      fallback_model: ${{ steps.select.outputs.fallback_model }}
      test_models: ${{ steps.select.outputs.test_models }}

    steps:
      - name: Select Model Based on Context
        id: select
        run: |
          TIER="${{ github.event.inputs.model_tier }}"

          if [ "$TIER" = "auto" ]; then
            # Auto-select based on complexity hints in prompt
            PROMPT="${{ github.event.inputs.prompt }}"

            if echo "$PROMPT" | grep -iE "(architect|design|complex|refactor)"; then
              PRIMARY="gemini-2.0-flash-thinking-exp-1219"
              FALLBACK="gemini-1.5-pro-002"
            elif echo "$PROMPT" | grep -iE "(review|analyze|explain)"; then
              PRIMARY="gemini-1.5-pro-002"
              FALLBACK="gemini-2.0-flash-thinking-exp-1219"
            else
              PRIMARY="gemini-2.0-flash-exp"
              FALLBACK="gemini-2.0-flash-thinking-exp-1219"
            fi
          elif [ "$TIER" = "thinking" ]; then
            PRIMARY="gemini-2.0-flash-thinking-exp-1219"
            FALLBACK="gemini-1.5-pro-002"
          elif [ "$TIER" = "pro" ]; then
            PRIMARY="gemini-1.5-pro-002"
            FALLBACK="gemini-2.0-flash-thinking-exp-1219"
          else
            PRIMARY="gemini-2.0-flash-exp"
            FALLBACK="gemini-2.0-flash-thinking-exp-1219"
          fi

          echo "primary_model=$PRIMARY" >> $GITHUB_OUTPUT
          echo "fallback_model=$FALLBACK" >> $GITHUB_OUTPUT

          # For A/B testing
          if [ "${{ github.event.inputs.enable_ab_testing }}" = "true" ]; then
            echo "test_models=$PRIMARY,$FALLBACK,gemini-2.0-flash-exp" >> $GITHUB_OUTPUT
          fi

  invoke-gemini:
    needs: select-model
    runs-on: ubuntu-latest

    strategy:
      matrix:
        model: ${{ fromJson(format('["{0}"]', needs.select-model.outputs.primary_model)) }}

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Mint GitHub App Token
        id: mint-token
        uses: actions/create-github-app-token@v1
        with:
          app-id: ${{ secrets.GEMINI_BOT_APP_ID }}
          private-key: ${{ secrets.GEMINI_BOT_PRIVATE_KEY }}
          permissions: >-
            {
              "contents": "write",
              "issues": "write",
              "pull_requests": "write"
            }

      - name: Setup MCP Servers Config
        id: setup-mcps
        run: |
          # Generate MCP config based on input
          SERVERS="${{ github.event.inputs.mcp_servers }}"

          # Start with GitHub (always included)
          MCP_CONFIG='{"github": {...}}'  # Existing config

          # Add Context7 if requested
          if echo "$SERVERS" | grep -q "context7"; then
            # Add context7 config
          fi

          # Add Universal Agent Context if requested
          if echo "$SERVERS" | grep -q "agent-context"; then
            # Add agent-context config
          fi

          echo "mcp_config=$MCP_CONFIG" >> $GITHUB_OUTPUT

      - name: Run Gemini CLI
        uses: google-github-actions/run-gemini-cli@v0
        with:
          gemini_api_key: ${{ secrets.GEMINI_API_KEY }}
          gemini_model: ${{ matrix.model }}
          use_vertex_ai: false
          use_gemini_code_assist: false
          gemini_debug: true
          timeout-minutes: 15
          auto_accept_tools: true
          settings: |
            {
              "global": {
                "multiTurnReply": {
                  "enabled": true
                }
              },
              "mcpServers": ${{ steps.setup-mcps.outputs.mcp_config }}
            }
          prompt: |-
            ## Persona

            You are a world-class software engineering agent with access to:
            - GitHub operations (18 tools)
            - Library documentation (Context7)
            - Architectural memory (Universal Agent Context)

            ## Task Context

            Repository: ${{ github.repository }}
            Branch: ${{ github.ref_name }}
            Model: ${{ matrix.model }}

            ## Your Task

            ${{ github.event.inputs.prompt }}

            ## Quality Standards

            - Prioritize correctness over speed
            - Use architectural memory to maintain consistency
            - Look up documentation when unsure
            - Store important decisions for future reference
            - Show your reasoning process

          github_token: ${{ steps.mint-token.outputs.token }}

      - name: Track Model Performance
        if: always()
        run: |
          # Log model performance metrics
          echo "Model: ${{ matrix.model }}"
          echo "Duration: ${{ steps.run-gemini.outputs.duration }}"
          echo "Status: ${{ job.status }}"

          # Store for later analysis
          mkdir -p .github/metrics
          cat > ".github/metrics/model-performance-$(date +%s).json" <<EOF
          {
            "model": "${{ matrix.model }}",
            "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
            "duration_seconds": "${{ steps.run-gemini.outputs.duration }}",
            "status": "${{ job.status }}",
            "task_type": "$(echo '${{ github.event.inputs.prompt }}' | head -c 50)"
          }
          EOF

      - name: Fallback on Rate Limit
        if: failure() && contains(steps.run-gemini.outputs.error, 'rate limit')
        uses: google-github-actions/run-gemini-cli@v0
        with:
          gemini_model: ${{ needs.select-model.outputs.fallback_model }}
          # ... same config as above ...

  # Optional: A/B testing job
  compare-models:
    if: github.event.inputs.enable_ab_testing == 'true'
    needs: invoke-gemini
    runs-on: ubuntu-latest

    strategy:
      matrix:
        model: ${{ fromJson(format('[{0}]', needs.select-model.outputs.test_models)) }}

    steps:
      - name: Run Parallel Tests
        # Run same prompt with different models
        # Compare outputs, duration, quality
```

### A/B Testing Analysis Script

```python
#!/usr/bin/env python3
"""Analyze A/B testing results for model selection."""

import json
from pathlib import Path
from datetime import datetime, timedelta

def analyze_model_performance():
    """Analyze model performance from stored metrics."""
    metrics_dir = Path(".github/metrics")

    if not metrics_dir.exists():
        print("No metrics found")
        return

    # Load all metrics
    metrics = []
    for file in metrics_dir.glob("model-performance-*.json"):
        with open(file) as f:
            metrics.append(json.load(f))

    # Group by model
    by_model = {}
    for m in metrics:
        model = m["model"]
        if model not in by_model:
            by_model[model] = []
        by_model[model].append(m)

    # Analyze each model
    print("## Model Performance Summary\n")
    for model, runs in by_model.items():
        total = len(runs)
        successful = sum(1 for r in runs if r["status"] == "success")
        avg_duration = sum(float(r["duration_seconds"]) for r in runs) / total

        print(f"### {model}")
        print(f"- Total runs: {total}")
        print(f"- Success rate: {successful/total*100:.1f}%")
        print(f"- Avg duration: {avg_duration:.1f}s")
        print(f"- Success rate: {successful}/{total}")
        print()

    # Recommendations
    print("\n## Recommendations\n")

    # Best for quality (highest success rate)
    best_quality = max(by_model.items(),
                      key=lambda x: sum(1 for r in x[1] if r["status"]=="success")/len(x[1]))
    print(f"**Best for Quality:** {best_quality[0]}")

    # Best for speed (lowest avg duration with good success rate)
    fast_reliable = [(m, runs) for m, runs in by_model.items()
                     if sum(1 for r in runs if r["status"]=="success")/len(runs) > 0.8]
    if fast_reliable:
        best_speed = min(fast_reliable,
                        key=lambda x: sum(float(r["duration_seconds"]) for r in x[1])/len(x[1]))
        print(f"**Best for Speed:** {best_speed[0]}")

if __name__ == "__main__":
    analyze_model_performance()
```

---

## 🔌 Creating Universal Agent Context MCP Server

To expose your `universal-agent-context` package as an MCP server:

### 1. Create MCP Server Script

```python
# platform/agent-context/src/universal_agent_context/mcp_server.py

"""MCP Server for Universal Agent Context System."""

import asyncio
import json
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from .primitives.memory import AgentMemoryPrimitive
from .primitives.coordination import CoordinationPrimitive

app = Server("universal-agent-context")

@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="store_memory",
            description="Store an architectural decision or important context",
            inputSchema={
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "Memory key"},
                    "value": {"type": "object", "description": "Data to store"},
                    "scope": {
                        "type": "string",
                        "enum": ["session", "workflow", "global"],
                        "description": "Memory scope"
                    }
                },
                "required": ["key", "value"]
            }
        ),
        Tool(
            name="retrieve_memory",
            description="Retrieve stored architectural decision or context",
            inputSchema={
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "Memory key"}
                },
                "required": ["key"]
            }
        ),
        Tool(
            name="query_decisions",
            description="Query architectural decisions by pattern",
            inputSchema={
                "type": "object",
                "properties": {
                    "pattern": {"type": "string", "description": "Search pattern"},
                    "scope": {"type": "string", "description": "Search scope"}
                },
                "required": ["pattern"]
            }
        ),
        Tool(
            name="list_architecture_decisions",
            description="List all stored architectural decisions",
            inputSchema={
                "type": "object",
                "properties": {
                    "scope": {"type": "string", "description": "Filter by scope"}
                }
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls."""
    if name == "store_memory":
        memory_primitive = AgentMemoryPrimitive(
            operation="store",
            memory_key=arguments["key"],
            memory_scope=arguments.get("scope", "session")
        )
        # Execute primitive and return result
        # ... implementation ...

    elif name == "retrieve_memory":
        memory_primitive = AgentMemoryPrimitive(
            operation="retrieve",
            memory_key=arguments["key"]
        )
        # ... implementation ...

    elif name == "query_decisions":
        # Query implementation
        pass

    elif name == "list_architecture_decisions":
        # List implementation
        pass

    return [TextContent(type="text", text=json.dumps(result))]

async def main():
    """Run MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
```

### 2. Add to Workflow

```yaml
mcpServers:
  agent-context:
    command: "python"
    args:
      - "-m"
      - "universal_agent_context.mcp_server"
    includeTools:
      - store_memory
      - retrieve_memory
      - query_decisions
      - list_architecture_decisions
    env:
      MEMORY_STORE: "${{ github.workspace }}/.agent-memory"
      PYTHONPATH: "${{ github.workspace }}/packages"
```

---

## 📈 Rate Limit Handling

### Graceful Degradation Strategy

```yaml
- name: Handle Rate Limits Gracefully
  if: failure()
  run: |
    ERROR="${{ steps.run-gemini.outputs.error }}"

    if echo "$ERROR" | grep -q "rate limit"; then
      echo "⚠️ Rate limit hit on ${{ matrix.model }}"
      echo "Falling back to ${{ needs.select-model.outputs.fallback_model }}"

      # Trigger fallback workflow
      gh workflow run gemini-invoke.yml \
        -f model_tier=fast \
        -f prompt="${{ github.event.inputs.prompt }}" \
        -f issue_number="${{ github.event.inputs.issue_number }}"
    fi
```

### Rate Limit Monitoring

```python
# scripts/monitor-rate-limits.py

"""Monitor Gemini API rate limits and usage."""

import json
from pathlib import Path
from collections import Counter
from datetime import datetime, timedelta

def check_rate_limits():
    """Check recent usage against rate limits."""
    metrics_dir = Path(".github/metrics")
    now = datetime.now()

    # Last hour
    recent_metrics = []
    for file in metrics_dir.glob("model-performance-*.json"):
        with open(file) as f:
            m = json.load(f)
            timestamp = datetime.fromisoformat(m["timestamp"].replace("Z", "+00:00"))
            if now - timestamp < timedelta(hours=1):
                recent_metrics.append(m)

    # Count by model
    usage = Counter(m["model"] for m in recent_metrics)

    # Check against limits
    limits = {
        "gemini-1.5-pro-002": {"rpm": 2, "rpd": 1500},
        "gemini-2.0-flash-thinking-exp-1219": {"rpm": 10, "rpd": 5000},  # Estimated
        "gemini-2.0-flash-exp": {"rpm": 15, "rpd": 10000}  # Estimated
    }

    print("## Rate Limit Status\n")
    for model, count in usage.items():
        limit = limits.get(model, {"rpm": 10, "rpd": 1000})
        rpm_used = count
        rpm_limit = limit["rpm"]

        percent = (rpm_used / rpm_limit) * 100
        status = "🟢" if percent < 50 else "🟡" if percent < 80 else "🔴"

        print(f"{status} **{model}**")
        print(f"   - RPM: {rpm_used}/{rpm_limit} ({percent:.0f}%)")
        print()

if __name__ == "__main__":
    check_rate_limits()
```

---

## 🎨 Example Commands

### Quality-First Review
```
@gemini-cli /review --model thinking
```

### With Context7 Documentation Lookup
```
@gemini-cli Using Context7, review this PR for best practices with FastAPI and SQLAlchemy
```

### With Architectural Memory
```
@gemini-cli Check our architectural decisions and review if this PR aligns with our patterns
```

### A/B Testing
```
# Manual trigger with A/B testing enabled
gh workflow run gemini-invoke.yml \
  -f prompt="Review PR #123" \
  -f enable_ab_testing=true \
  -f mcp_servers="github,context7,agent-context"
```

---

## 📊 Success Metrics

Track these metrics to validate improvements:

1. **Quality Metrics**
   - Review accuracy (fewer follow-up corrections needed)
   - Architectural consistency (decisions aligned with memory)
   - Documentation quality (better references via Context7)

2. **Performance Metrics**
   - Response time by model
   - Rate limit hits per model
   - Fallback success rate

3. **Cost Metrics**
   - Staying within free tier
   - RPM/RPD utilization
   - Cost per quality review

---

## 🚀 Implementation Plan

### Phase 1: Model Upgrade (Immediate)
- [ ] Update default model to `gemini-2.0-flash-thinking-exp-1219`
- [ ] Add fallback to `gemini-1.5-pro-002`
- [ ] Test with 5 sample reviews
- [ ] Document quality improvements

### Phase 2: Context7 Integration (1-2 hours)
- [ ] Add Context7 MCP server configuration
- [ ] Test documentation lookup
- [ ] Update commands documentation
- [ ] Validate with library-heavy PRs

### Phase 3: Universal Agent Context MCP (2-4 hours)
- [ ] Create MCP server script
- [ ] Implement memory tools
- [ ] Add to workflow configuration
- [ ] Test architectural decision storage/retrieval

### Phase 4: A/B Testing Framework (4-6 hours)
- [ ] Implement model selection logic
- [ ] Add performance tracking
- [ ] Create analysis scripts
- [ ] Set up monitoring dashboard

### Phase 5: Rate Limit Monitoring (2-3 hours)
- [ ] Implement rate limit checker
- [ ] Add fallback logic
- [ ] Create alerts
- [ ] Document escalation procedure

---

## 🔐 Security Considerations

### Additional Secrets Needed

```yaml
# .github/workflows/gemini-invoke.yml
secrets:
  GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}  # Existing
  CONTEXT7_API_KEY: ${{ secrets.CONTEXT7_API_KEY }}  # New
  GEMINI_BOT_APP_ID: ${{ secrets.GEMINI_BOT_APP_ID }}  # Existing
  GEMINI_BOT_PRIVATE_KEY: ${{ secrets.GEMINI_BOT_PRIVATE_KEY }}  # Existing
```

### MCP Access Controls

Limit which MCP servers are available based on context:

```yaml
# For public repos: Only GitHub + Context7
# For private repos: Add agent-context for architectural memory
# For production: Add observability MCPs
```

---

## 📚 References

- [Gemini API Pricing](https://ai.google.dev/pricing)
- [Context7 MCP Server](https://github.com/context7/mcp-server)
- [MCP Protocol](https://modelcontextprotocol.io)
- [Universal Agent Context Package](../../platform/agent-context/)

---

**Next Steps:** Review this plan and let me know which phases to prioritize!
