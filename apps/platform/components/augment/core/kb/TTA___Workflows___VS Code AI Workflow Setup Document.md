---
title: 🚀 VS Code AI Workflow Setup Guide
tags: #TTA
status: Active
repo: theinterneti/TTA
path: VS_CODE_AI_WORKFLOW_SETUP.md
created: 2025-11-01
updated: 2025-11-01
---
# [[TTA/Workflows/🚀 VS Code AI Workflow Setup Guide]]

## Overview

This guide configures VS Code for AI-assisted development using TTA's workflow primitives and dev toolkit.

## 📦 Components Configured

### 1. **Workspace Structure**
- Multi-root workspace with organized folders
- Separate views for source, tests, packages, AI primitives, scripts, and docs

### 2. **AI Workflow Primitives** (`.augment/`)
- **Chatmodes**: Role-based AI assistance (architect, backend-dev, qa-engineer, etc.)
- **Contexts**: Scenario-specific guidance (debugging, refactoring, testing, etc.)
- **Workflows**: Reusable workflow templates (bug-fix, feature-implementation, etc.)
- **Memory**: Project knowledge and learnings
- **Rules**: AI agent behavior guidelines

### 3. **Dev Toolkit Packages** (`packages/`)
- **tta-workflow-primitives**: Router, Cache, Retry, Fallback patterns
- **ai-dev-toolkit**: Integrated toolkit with monitoring
- **dev-primitives**: Error recovery and utilities
- **tta-ai-framework**: Multi-agent orchestration
- **tta-narrative-engine**: Narrative generation

### 4. **Development Tools** (`scripts/`)
- OpenHands integration and testing
- Component maturity analysis
- Workflow automation
- Monitoring and observability
- Docker and deployment utilities

## 🎯 Quick Start

### 1. Open Workspace
```bash
code TTA-AI-Workflow.code-workspace
```

### 2. Install Recommended Extensions
VS Code will prompt to install recommended extensions. Key extensions:
- **Python** - Python language support
- **Pylance** - Advanced type checking
- **Ruff** - Fast Python linting/formatting
- **GitHub Copilot** - AI-powered code completion
- **Docker** - Container management
- **GitLens** - Enhanced Git capabilities
- **Error Lens** - Inline error display
- **TODO Tree** - Track TODOs and FIXMEs
- **Better Comments** - Highlighted comments

### 3. Setup Python Environment
Press `Ctrl+Shift+P` and run:
```
Tasks: Run Task -> 📦 UV: Sync Dependencies
```

Or in terminal:
```bash
uv sync --all-extras
```

### 4. Verify Setup
Run the verification task:
```
Tasks: Run Task -> UV: Verify Environment
```

## 🛠️ Available Tasks

### Package Management
- **📦 UV: Sync Dependencies** - Install/update all dependencies
- **📦 UV: Add Package** - Add new package
- **🔧 UV: Clean & Rebuild Environment** - Fresh environment rebuild

### Testing
- **🧪 Test: Run All Tests** - Run complete test suite
- **🧪 Test: Run with Coverage** - Tests with coverage report
- **🧪 Test: Run Current File** - Test only current file
- **🧪 Test: Run Failed Tests** - Re-run previously failed tests

### Code Quality
- **✨ Quality: Format Code (Ruff)** - Auto-format Python code
- **🔍 Quality: Lint Code (Ruff)** - Check and fix linting issues
- **🔍 Quality: Type Check (Pyright)** - Run type checking
- **✅ Quality: Run All Checks** - Format, lint, and type check

### Development Services
- **🚀 Dev: Start All Services** - Start Docker services
- **🛑 Dev: Stop All Services** - Stop Docker services
- **📋 Dev: View Logs** - View service logs
- **🔄 Dev: Restart Services** - Restart all services
- **📊 Dev: Service Status** - Check service status

### AI Workflow Primitives
- **🤖 AI: List Chatmodes** - Show available chatmodes
- **🤖 AI: List Workflows** - Show available workflows
- **🤖 AI: List Context Helpers** - Show context helpers
- **🤖 AI: Show Memory Bank** - Display memory files

### Monitoring
- **📊 Monitoring: Start Stack** - Start Prometheus/Grafana
- **📊 Monitoring: Stop Stack** - Stop monitoring
- **🌐 Open: Grafana Dashboard** - Open Grafana UI
- **🌐 Open: Neo4j Browser** - Open Neo4j UI
- **🌐 Open: Redis Commander** - Open Redis UI

### Workflow Automation
- **⚙️ Workflow: Component Promotion** - Promote component through stages
- **⚙️ Workflow: Analyze Component Maturity** - Analyze component status

### OpenHands Integration
- **🔧 OpenHands: Test Workflow** - Test OpenHands workflow
- **🔧 OpenHands: Verify Runtime** - Verify Docker runtime setup
- **🔧 OpenHands: Diagnose System** - Run system diagnostics

### Documentation
- **📚 Docs: Build Site** - Build MkDocs site
- **📚 Docs: Serve Locally** - Serve docs at http://localhost:8000

## ⌨️ Keyboard Shortcuts

### Testing
- `F5` - Start debugging
- `Ctrl+Shift+P` → "Test: Run All Tests" - Run tests
- Right-click in test file → "Run Tests" - Run specific test

### Code Navigation
- `F12` - Go to definition
- `Shift+F12` - Find all references
- `Ctrl+Shift+O` - Go to symbol in file
- `Ctrl+T` - Go to symbol in workspace

### Terminal
- `` Ctrl+` `` - Toggle terminal
- `Ctrl+Shift+\`` - Create new terminal
- In terminal dropdown, select "uv-shell" for activated environment

### Tasks
- `Ctrl+Shift+B` - Run default build task (UV: Sync Dependencies)
- `Ctrl+Shift+T` - Run default test task (Test: Run All Tests)
- `Ctrl+Shift+P` → "Tasks: Run Task" - Browse all tasks

## 🤖 Using AI Workflow Primitives

### Chatmodes

Switch AI context by referencing chatmodes in your prompts:

**Available Chatmodes:**
- **architect** - System architecture and design
- **backend-dev** - Python/FastAPI implementation
- **frontend-dev** - React/Next.js development
- **qa-engineer** - Testing and quality assurance
- **devops** - Deployment and infrastructure

**Example Usage:**
```
@architect Help me design the caching strategy for our API
```

### Context Helpers

Add scenario-specific guidance:

**Available Contexts:**
- **debugging** - Debugging workflows and strategies
- **refactoring** - Code refactoring patterns
- **testing** - Testing strategies and patterns
- **performance** - Performance optimization
- **security** - Security best practices
- **deployment** - Deployment procedures

**Example Usage:**
```
@debugging Why is this test failing intermittently?
@refactoring How should I extract this into a separate service?
```

### Workflows

Use pre-built workflow templates:

**Available Workflows:**
- **bug-fix** - Systematic bug investigation
- **feature-implementation** - Feature development flow
- **test-coverage-improvement** - Increase test coverage
- **component-promotion** - Promote components through stages
- **quality-gate-fix** - Fix quality gate failures

**Example Usage:**
```
Let's use the bug-fix workflow to investigate why the cache is returning stale data
```

### Memory Bank

The AI maintains project knowledge in `.augment/memory/`:
- **architectural-decisions** - Major design choices
- **implementation-failures** - Failed approaches to avoid
- **successful-patterns** - Proven patterns to reuse
- **workflow-learnings** - Lessons from workflows

## 📦 Using Dev Toolkit Packages

### Workflow Primitives

```python
from tta_workflow_primitives.core import RouterPrimitive
from tta_workflow_primitives.performance import CachePrimitive
from tta_workflow_primitives.recovery import RetryPrimitive

# Cost-optimized routing
router = RouterPrimitive(
    routes={
        'fast': local_llama,
        'premium': gpt4
    },
    router_fn=lambda input, ctx: (
        'fast' if len(input['prompt']) < 100 else 'premium'
    )
)

# Add caching
cached_router = CachePrimitive(router, ttl_seconds=3600)

# Add retry logic
robust_router = RetryPrimitive(cached_router, max_attempts=3)

# Use it
response = await robust_router.execute(
    {'prompt': user_input},
    WorkflowContext()
)
```

### Development Primitives

```python
from dev_primitives.recovery import with_retry, with_fallback
from dev_primitives.observability import track_metrics

@with_retry(max_attempts=3)
@track_metrics()
async def call_api(endpoint: str) -> dict:
    return await httpx.get(endpoint)
```

## 🐛 Debugging

### Python Debugging

1. Set breakpoints by clicking left of line numbers
2. Press `F5` and select debug configuration:
   - **🐍 Python: Current File** - Debug current Python file
   - **🧪 Python: Debug Tests** - Debug test file
   - **🧪 Python: Debug Current Test** - Debug specific test
   - **🚀 Python: API Server** - Debug API server with reload

### Test Debugging

1. Open test file
2. Right-click on test function
3. Select "Debug Test"

Or press `F5` with test file open and select "Debug Tests"

## 📊 Monitoring & Observability

### Start Monitoring Stack

```bash
# Using task
Tasks: Run Task -> 📊 Monitoring: Start Stack

# Or manually
docker-compose -f monitoring/docker-compose.monitoring.yml up -d
```

### Access Dashboards

- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090
- **Neo4j**: http://localhost:7474
- **Redis Commander**: http://localhost:8081

### View Metrics

```python
from tta_workflow_primitives.metrics import get_metrics

# Get workflow metrics
metrics = get_metrics('my_workflow')
print(f"Executions: {metrics['count']}")
print(f"Avg Duration: {metrics['avg_duration_ms']}ms")
print(f"Error Rate: {metrics['error_rate']}%")
```

## 🔧 Troubleshooting

### UV Environment Issues

**Problem**: `list` directory appearing
**Solution**:
```bash
Tasks: Run Task -> 🔧 UV: Clean & Rebuild Environment
```

**Problem**: Import errors
**Solution**:
1. Verify PYTHONPATH in settings
2. Rebuild environment
3. Reload VS Code window (`Ctrl+Shift+P` → "Developer: Reload Window")

### Testing Issues

**Problem**: Tests not discovered
**Solution**:
1. Check Python interpreter: `Ctrl+Shift+P` → "Python: Select Interpreter"
2. Select `.venv/bin/python`
3. Run: `Tasks: Run Task -> Test: Run All Tests`

**Problem**: Import errors in tests
**Solution**:
Verify `pytest.ini` has correct `pythonpath`:
```ini
[pytest]
pythonpath = src packages/tta-workflow-primitives/src
```

### Docker Issues

**Problem**: Services won't start
**Solution**:
```bash
# Check status
docker-compose -f docker-compose.dev.yml ps

# View logs
docker-compose -f docker-compose.dev.yml logs

# Restart
docker-compose -f docker-compose.dev.yml restart
```

## 🎓 Best Practices

### 1. Use AI Primitives
- Reference chatmodes for role-specific help
- Use context helpers for scenarios
- Follow workflow templates for common tasks

### 2. Run Quality Checks
Before committing:
```bash
Tasks: Run Task -> ✅ Quality: Run All Checks
```

### 3. Write Tests
- Use TDD approach
- Run tests with coverage
- Debug failing tests immediately

### 4. Monitor Performance
- Check monitoring dashboards regularly
- Track component maturity
- Review metrics in Grafana

### 5. Document Decisions
- Add to `.augment/memory/` for future reference
- Update chatmodes if new patterns emerge
- Create workflows for repeated processes

## 📚 Additional Resources

### Documentation
- [[TTA/Workflows/README|AI Dev Toolkit]]
- [[TTA/Workflows/README|Workflow Primitives]]
- [[TTA/Workflows/AGENTIC_PRIMITIVES_INDEX|Agentic Primitives Index]]
- [[TTA/Workflows/OPENHANDS_DEV_TOOLS|OpenHands Dev Tools]]

### Examples
- [Workflow Primitives Examples](packages/tta-workflow-primitives/examples/)
- [AI Dev Toolkit Examples](packages/ai-dev-toolkit/examples/)

### Project Docs
- [[TTA/Workflows/GEMINI|GEMINI.md]] - Project overview for AI
- [[TTA/Workflows/CONTRIBUTING|CONTRIBUTING.md]] - Contribution guidelines
- [[TTA/Workflows/README|README.md]] - Project README

## 🚀 Next Steps

1. ✅ Open workspace: `code TTA-AI-Workflow.code-workspace`
2. ✅ Install recommended extensions
3. ✅ Run "📦 UV: Sync Dependencies"
4. ✅ Run "🧪 Test: Run All Tests" to verify setup
5. ✅ Start development services: "🚀 Dev: Start All Services"
6. ✅ Open monitoring: "📊 Monitoring: Start Stack"
7. 🎯 Start coding with AI assistance!

## 💡 Pro Tips

- **Use tasks**: Don't memorize commands, use tasks menu (`Ctrl+Shift+P` → "Tasks: Run Task")
- **Leverage AI**: Reference chatmodes and contexts in your prompts
- **Monitor everything**: Keep Grafana open in another window
- **Test continuously**: Run tests on save (enable in settings)
- **Debug smartly**: Use VS Code debugger instead of print statements
- **Document learnings**: Add to memory bank for future reference

---

**Ready to build AI applications with intelligent workflows!** 🤖✨


---
**Logseq:** [[TTA.dev/Platform_tta_dev/Components/Augment/Core/Kb/Tta___workflows___vs code ai workflow setup document]]
