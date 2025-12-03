# TTA.dev (Meta-Project)

type:: [[Meta-Project]]
category:: [[Project Hub]]
status:: [[Active]]
visibility:: [[Public]]

---

## 🎯 Project Mission

TTA.dev is a production-ready AI development toolkit providing composable agentic primitives for building reliable AI workflows.

**Core Value:** Transform complex async orchestration into simple, composable workflow patterns with built-in observability.

---

## 📦 Package Architecture

### Core Packages

- [[TTA Primitives]] - Workflow primitives (Sequential, Parallel, Router, Retry, etc.)
- [[Observability Integration]] - OpenTelemetry + Prometheus integration
- [[Universal Agent Context]] - Agent coordination and context management
- [[Keploy Framework]] - API testing and replay
- [[Python Pathway]] - Python code analysis utilities

---

## 🔥 Current Focus

### Active Priorities

- TODO Complete [[Phase 2 Integration Tests]]
- TODO Finalize [[MCP Server Integration]]
- TODO Implement [[Logseq Knowledge Base]] setup
- DOING Review and merge [[Copilot Toolsets]] optimization

### Recent Completions

- DONE [[Phase 1 Agent Coordination]] - Multi-agent workflow validation
- DONE [[Primitives Catalog]] - Comprehensive primitive documentation
- DONE [[GitHub Agent HQ]] - Automated PR review and management

---

## 📊 Live Dashboards

### Open Tasks (All Packages)

{{query (task TODO DOING)}}

### Completed This Week

{{query (and (task DONE) (between -7d today))}}

### High Priority Issues

{{query (and (task TODO) (priority A))}}

### Research Backlog

{{query (and (task LATER) (tag research))}}

---

## 🧱 Component Map

### Workflow Primitives

Core execution patterns:

- [[SequentialPrimitive]] - Sequential composition (`>>` operator)
- [[ParallelPrimitive]] - Parallel composition (`|` operator)
- [[RouterPrimitive]] - Dynamic routing (LLM selection, etc.)
- [[ConditionalPrimitive]] - Conditional branching

Recovery patterns:

- [[RetryPrimitive]] - Automatic retry with backoff
- [[FallbackPrimitive]] - Graceful degradation
- [[TimeoutPrimitive]] - Circuit breaker
- [[CompensationPrimitive]] - Saga pattern rollback

Performance:

- [[CachePrimitive]] - LRU + TTL caching

### Observability Stack

- [[OpenTelemetry Integration]] - Distributed tracing
- [[Prometheus Metrics]] - Performance monitoring
- [[Structured Logging]] - Context-aware logging
- [[WorkflowContext]] - State propagation

---

## 🎨 Development Workflows

### Adding a New Primitive

1. Create primitive class in `platform/primitives/src/`
2. Implement `WorkflowPrimitive[InputType, OutputType]`
3. Add comprehensive tests (100% coverage required)
4. Create example in `examples/`
5. Update [[PRIMITIVES CATALOG]]
6. Update package README

**Reference:** [[TTA Primitives/Development Guide]]

### Running Quality Checks

```bash
# Format code
uv run ruff format .

# Lint
uv run ruff check . --fix

# Type check
uvx pyright packages/

# Run tests
uv run pytest -v

# Or run everything
# Use VS Code task: "✅ Quality Check (All)"
```

## Integration Testing

See [[Phase 2 Integration Tests]] for current status.

---

## 🔗 External Integrations

### MCP Servers

- [[Context7 MCP]] - Library documentation lookup
- [[Docker Sift MCP]] - Container investigation
- [[Grafana MCP]] - Observability queries
- [[Pylance MCP]] - Python language server

**Full list:** [[MCP_SERVERS.md]]

### AI Tools

- [[GitHub Copilot]] - Code generation with custom toolsets
- [[AI Toolkit]] - Agent development and evaluation
- [[Augment]] - Context-aware coding assistant

---

## 📚 Documentation Structure

### For Users

- **README.md** - Project overview
- **GETTING_STARTED.md** - Setup guide
- **PRIMITIVES_CATALOG.md** - Complete primitive reference
- **docs/guides/** - Usage guides and tutorials

### For AI Agents

- **AGENTS.md** - Primary agent instructions (hub)
- **packages/*/AGENTS.md** - Package-specific guidance
- **.github/copilot-instructions.md** - Copilot workspace config
- **.github/instructions/*.md** - File-type specific rules

### For Developers

- **docs/architecture/** - ADRs and design docs
- **docs/development/** - Development guides
- **CONTRIBUTING.md** - Contribution guidelines

---

## 🎯 Decision Framework

When making technical decisions, prioritize:

1. **Correctness** - Code must work and be tested
2. **Type Safety** - Full type annotations required
3. **Composability** - Use primitives for reusable patterns
4. **Testability** - Easy to test with mocks
5. **Performance** - Parallel where appropriate
6. **Observability** - Traceable and debuggable

**Reference:** [[DECISION_QUICK_REFERENCE.md]]

---

## 🚧 Common Issues & Solutions

### Import Errors

```bash
# Sync dependencies
uv sync --all-extras

# Verify Python version
python --version  # Should be 3.11+
```

## Type Errors

```bash
# Run type checker on specific package
uvx pyright platform/primitives/
```

## Test Failures

```bash
# Verbose output with stdout
uv run pytest -v -s

# Run specific test file
uv run pytest platform/primitives/tests/test_sequential.py
```

---

## 📊 Metrics & KPIs

### Code Quality

- Test Coverage: Target 100% for all new code
- Type Coverage: 100% for public APIs
- Lint Score: 10.0/10.0 (Ruff)

### Performance

- Primitive Execution: < 1ms overhead
- Cache Hit Rate: > 80% (production)
- Retry Success: > 95% (after retries)

### Community

- GitHub Stars: Track growth
- Issues: Response time < 24h
- PRs: Review time < 48h

---

## 🔮 Future Roadmap

### Q4 2025

- [ ] Complete [[Multi-Language Support]] (TypeScript/JavaScript)
- [ ] Launch [[TTA Marketplace]] (community primitives)
- [ ] Implement [[Advanced Router Strategies]]

### Q1 2026

- [ ] [[Distributed Workflow Execution]]
- [ ] [[Visual Workflow Designer]]
- [ ] [[Enterprise Features]] (audit logs, compliance)

**Full roadmap:** [[VISION.md]]

---

## 🔗 Quick Links

- **GitHub:** <https://github.com/theinterneti/TTA.dev>
- **Issues:** <https://github.com/theinterneti/TTA.dev/issues>
- **CI/CD:** <https://github.com/theinterneti/TTA.dev/actions>

---

## 📅 Weekly Reviews

### Week of 2025-10-28

- [[2025_10_28]] - Copilot toolsets optimization complete
- [[2025_10_29]] - Integration test fixes
- [[2025_10_30]] - Logseq knowledge base setup

---

**Last Updated:** 2025-10-30
**Maintained by:** @theinterneti
**Repository:** <https://github.com/theinterneti/TTA.dev>
