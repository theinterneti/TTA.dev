# TTA Agent Testing Framework

**Automated AI Agentic Coder Testing Framework**

A comprehensive testing framework for validating AI coding assistants in VS Code workspaces using web-based Playwright automation, MCP server testing, and performance benchmarking.

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![uv](https://img.shields.io/badge/package_manager-uv-orange.svg)](https://github.com/astral-sh/uv)
[![Playwright](https://img.shields.io/badge/automation-Playwright-green.svg)](https://playwright.dev/)

## Overview

This framework provides automated validation of AI coding assistants (Cline, Augment, GitHub Copilot) by:

- **Browser Automation**: Testing vscode.dev with custom workspace configurations
- **MCP Server Validation**: Health checking and performance benchmarking for MCP servers
- **Agent Handoff Protocols**: Standardized state transfer between agents
- **Performance Analysis**: Comparative analysis of agent effectiveness and cost optimization
- **ACE Learning Integration**: Self-improving strategies using observability data

## Quick Start

### Installation

```bash
# Install dependencies using uv
uv pip install -e "packages/tta-agent-testing-framework[dev,playwright,mcp]"

# Or install all optional dependencies
uv sync --all-extras

# Run the basic validation test
uv run python examples/basic_agent_test.py
```

### Basic Usage

```python
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

from tta_agent_testing_framework import AgentTestingFramework
from tta_agent_testing_framework.browser import PlaywrightAutomationProvider
from tta_agent_testing_framework.core import WorkspaceType
from tta_agent_testing_framework.mcp import MCPConnectionHealthChecker

async def test_cline_workspace():
    workspace_root = Path("/path/to/tta-dev-project")

    # Initialize components
    async with async_playwright() as playwright:
        browser_provider = PlaywrightAutomationProvider(playwright)
        mcp_checker = MCPConnectionHealthChecker()

        # Create testing framework
        framework = AgentTestingFramework(
            workspace_root=workspace_root,
            browser_provider=browser_provider,
            mcp_checker=mcp_checker,
        )

        # Run comprehensive test
        result = await framework.run_comprehensive_test(WorkspaceType.CLINE)
        print(f"Test {'PASSED' if result.success else 'FAILED'}")

asyncio.run(test_cline_workspace())
```

## Key Features

### 🤖 AI Agent Testing
- **Multiple Workspace Support**: Cline, Augment, GitHub Copilot configurations
- **Browser Automation**: VS Code web testing with Playwright
- **Agent Initialization**: Validated startup and extension loading
- **Handoff Protocols**: Standardized state transfer between agents

### 🔧 MCP Server Ecosystem
- **Health Checking**: Connectivity validation for all MCP server types
- **Performance Benchmarking**: Response time and reliability metrics
- **Capability Validation**: Server feature availability testing
- **Multi-Protocol Support**: stdio, SSE, WebSocket server testing

### 📊 Performance & Analytics
- **Comparative Analysis**: Cost and quality metrics across agents
- **Execution Tracking**: Token usage, response times, success rates
- **Observability Integration**: OpenTelemetry tracing and metrics
- **Benchmarking Suite**: Automated performance regression testing

### 🧠 Adaptive Learning
- **ACE Integration**: Self-improving strategies from execution data
- **Cost Optimization**: Intelligent model selection algorithms
- **Failure Pattern Learning**: Circuit breakers and retry optimization
- **Knowledge Base Updates**: Automatic strategy persistence

## Architecture

### Core Components

```
tta-agent-testing-framework/
├── core.py              # Core types, protocols, and framework
├── browser.py           # Playwright-based VS Code web testing
├── mcp.py               # MCP server health checking
├── primitives/          # Testing-specific primitives
├── analytics/           # Performance analysis and reporting
└── learning/            # ACE integration and strategy learning
```

### Testing Pipeline

1. **Workspace Validation**: Configuration file and structure checking
2. **Browser Setup**: VS Code web loading and extension initialization
3. **MCP Connectivity**: Server health and capability validation
4. **Agent Handoffs**: State transfer and multi-agent coordination
5. **Performance Analysis**: Cost, quality, and timing metrics collection
6. **Learning Updates**: Strategy optimization using execution feedback

## AI Agent Profiles

### Cline Workspace
- **Extensions**: `saoudrizwan.claude-dev`
- **MCP Servers**: Context7, Sequential Thinking, Serena, Playwright
- **Profile**: Full-featured with comprehensive MCP ecosystem
- **Use Case**: Complex tasks requiring extensive tool integration

### Augment Workspace
- **Extensions**: `augment.augment`
- **MCP Servers**: None (native integrations)
- **Profile**: Speed-optimized for rapid iteration
- **Use Case**: Fast prototyping and code completion tasks

### GitHub Copilot Workspace
- **Extensions**: `github.copilot`, `github.copilot-chat`
- **MCP Servers**: None (GitHub native API)
- **Profile**: Quality-focused with extensive GitHub integration
- **Use Case**: Enterprise development with code review and PR management

## Testing Strategies

### Agent Handoff Scenarios
```python
# Sequential agent chain with handoffs
workflow = (
    cline_agent >>
    augment_agent >>
    copilot_agent >>
    validation_agent
)

# Parallel agent exploration
workflow = (
    cline_agent |
    augment_agent |
    copilot_agent >>
    aggregator_agent
)
```

### Cost Optimization
```python
# Free-tier first, premium fallback
strategy = FreeTierAgent() >> RetryPrimitive(
    target=PremiumAgent(),
    max_retries=1,
    cost_threshold=0.1  # $0.10 max per request
)
```

### Quality Gates
```python
# Multi-agent validation before acceptance
quality_gate = (
    AgentExecution() >>
    ASTValidation() >>
    TestExecution() >>
    CodeQualityCheck()
).require_all_success()
```

## Configuration

### MCP Server Setup

Create a `.vscode/mcp.json` configuration file:

```json
{
  "mcpServers": {
    "context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp@latest"],
      "type": "stdio"
    },
    "playwright": {
      "command": "npx",
      "args": ["@playwright/mcp@latest", "--headless"],
      "type": "stdio"
    }
  }
}
```

### Workspace Configuration

Each agent requires a `.code-workspace` file:

```bash
# Example workspace files in project root
cline.code-workspace
augment.code-workspace
github-copilot.code-workspace
```

## Development

### Running Tests

```bash
# Install dependencies
uv sync --all-extras

# Run all tests
uv run pytest -v

# Run with coverage
uv run pytest --cov=tta_agent_testing_framework --cov-report=html

# Run specific test categories
uv run pytest -m "browser" -v      # Browser automation tests
uv run pytest -m "integration" -v  # Integration tests
uv run pytest -m "slow" -v         # Performance tests
```

### Code Quality

```bash
# Format code
uv run ruff format .

# Lint code
uv run ruff check . --fix

# Type checking
uv run mypy src/tta_agent_testing_framework/

# Security scanning
uv run bandit src/tta_agent_testing_framework/
```

## Examples

### Agent Performance Comparison

```python
from tta_agent_testing_framework.analytics import AgentPerformanceAnalyzer

analyzer = AgentPerformanceAnalyzer()

# Compare agents on fibonacci implementation task
results = await analyzer.compare_agents(
    task="Create a function to calculate fibonacci numbers",
    agents=[WorkspaceType.CLINE, WorkspaceType.AUGMENT, WorkspaceType.GITHUB_COPILOT],
    iterations=10,
)

print(results.report())
# Output: Performance metrics, cost analysis, quality scores
```

### Handoff Strategy Learning

```python
from tta_agent_testing_framework.learning import AgentStrategyLearner

learner = AgentStrategyLearner()

# Train handoff strategy based on task complexity
await learner.train_strategy(
    task_type="fibonacci_implementation",
    complexity_threshold=0.8,  # Complex tasks use premium agents
    cost_budget=0.5,  # $0.50 max per task
)

# Apply learned strategy
strategy = await learner.get_optimal_strategy(task_complexity=0.9)
```

## Integration with TTA.dev

This framework is designed to integrate seamlessly with TTA.dev primitives:

- **Observability**: Full OpenTelemetry tracing integration
- **Workflow Composition**: Uses `>>` and `|` operators
- **Error Handling**: Built-in retry and fallback primitives
- **Caching**: Performance caching for repeated operations
- **ACE Learning**: Self-improvement through execution feedback

## Contributing

See the main TTA.dev repository for contribution guidelines.

## License

MIT License - see individual package licenses.
