# Changelog

All notable changes to TTA.dev will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.3.0] - 2025-12-06

### Added

#### 🛠️ AST-Based Code Transformer

**Intelligent code rewriting using Abstract Syntax Tree analysis:**

- **`transformer.py`** - New module for AST-based code transformation
  - `CodeTransformer` class with intelligent pattern detection
  - `TransformResult` dataclass with transformation metadata
  - Preserves code structure while applying primitive wrappers
  - Handles imports automatically

- **Supported transformations:**
  - `RetryPrimitive` - Transforms manual retry loops
  - `TimeoutPrimitive` - Transforms asyncio.wait_for patterns
  - `FallbackPrimitive` - Transforms try/except fallback chains
  - `CachePrimitive` - Transforms manual caching dictionaries
  - `ParallelPrimitive` - Transforms gather/create_task patterns
  - `SequentialPrimitive` - Transforms chained await patterns
  - `RouterPrimitive` - Transforms if/elif routing chains
  - `CircuitBreakerPrimitive` - Transforms manual circuit breaker patterns

#### 🔍 Enhanced Anti-Pattern Detection

**8 anti-patterns now detected with line numbers:**

- `manual_retry` - Retry loops with `for` + `range()` + `try/except`
- `manual_timeout` - `asyncio.wait_for()` usage
- `manual_fallback` - `or default_value` / `if x is None` patterns
- `manual_cache` - Dictionary-based caching with `if key in cache`
- `manual_parallel` - `asyncio.gather()` / `create_task()` usage
- `manual_circuit_breaker` - `failure_count` / `circuit_open` patterns
- `manual_sequential` - Chained `await` calls like `result = await step(await step(data))`
- `manual_routing` - `if provider == X` routing chains

#### 🔧 New MCP Tool: `rewrite_code`

**AST-based code rewriting via MCP:**

```python
# Example usage in MCP client
result = await mcp.call_tool("rewrite_code", {
    "code": code_with_anti_patterns,
    "primitive": "RetryPrimitive",  # Optional: specific primitive
    "auto_detect": True  # Auto-detect all anti-patterns
})
# Returns: transformed_code, changes_made, imports_added, diff
```

### Changed

- **`--apply` flag** now uses AST transformer for smarter rewrites
- Pattern detection now includes line numbers for all matches
- MCP server now has 10 tools (added `rewrite_code`)

### Testing

- **283 tests passing** (52 CLI + 81 MCP + 150 analysis)
- 23 new tests for AST transformer
- 7 new tests for `rewrite_code` MCP tool

## [1.2.0] - 2025-12-06

### Added

#### 🤖 Agent-Friendly CLI

**CLI optimized for AI agent workflows with machine-parseable output:**

- **`--quiet` flag** - Suppresses debug logs, returns only structured JSON
- **`--lines` flag** - Includes exact line numbers for each detected pattern
- **`--suggest-diff` flag** - Shows actionable transformation suggestions
- **`--apply` flag** - Automatically transforms ALL detected anti-patterns
- **`--apply-primitive NAME` flag** - Transforms specific primitive type only

**New Commands:**
- **`tta-dev transform`** - Direct code transformation command
  - `--code` / `--file` - Input source
  - `--to` - Target primitive to transform to
  - `--write` - Write transformation to file

**Usage Examples:**
```bash
# Agent workflow: analyze with line numbers, quiet
tta-dev analyze code.py --lines --quiet

# Auto-fix all patterns
tta-dev analyze code.py --apply --quiet

# Transform specific pattern
tta-dev transform --file code.py --to RetryPrimitive
```

#### 🔧 Enhanced MCP Server

**Three new MCP tools for AI agent integration:**

- **`transform_code`** - Transform code snippets to use TTA.dev primitives
  - Input: code snippet + target primitive
  - Output: transformed code with proper imports

- **`analyze_and_fix`** - Analyze code and return fixed version
  - Input: code snippet + optional primitive filter
  - Output: analysis + automatically transformed code

- **`suggest_fixes`** - Get actionable fix suggestions
  - Input: code snippet
  - Output: list of suggestions with line numbers and diffs

**VS Code Integration:**
```json
{
  "mcp": {
    "servers": {
      "tta-dev": {
        "command": "uv",
        "args": ["run", "tta-dev-mcp"],
        "cwd": "/path/to/TTA.dev/platform/primitives"
      }
    }
  }
}
```

### Changed

- Improved pattern detection with exact line number tracking
- Better error messages for transformation failures
- CLI output now JSON-parseable when using `--quiet`

### Testing

- **117 tests passing** (52 CLI + 65 MCP)
- All transformations validated with real code samples
- Agent workflow integration tests added

## [1.1.0] - 2025-11-17

### Added

#### 🤖 GitHub Integration - @cline Agent

**Autonomous AI issue analysis integrated into GitHub Actions:**

- **Cline Responder Workflow** - Triggers on `@cline` mentions in GitHub issues
  - Automatically starts Cline CLI instances in GitHub Actions
  - Uses TTA.dev-specific knowledge base for intelligent analysis
  - Posts structured responses as GitHub comments

- **TTA.dev Specialized Analysis** - Agent understands our ecosystem deeply
  - Reads AGENTS.md, PRIMITIVES_CATALOG.md, and package documentation
  - Identifies relevant packages (tta-dev-primitives, tta-observability-integration, etc.)
  - Suggests specific primitives and patterns (RetryPrimitive, CachePrimitive, etc.)
  - References examples directory for working code samples
  - Enforces TTA.dev standards (uv, type hints with `str | None`, primitives workflow patterns)

- **Security & Infrastructure**
  - Environment-scoped execution ("cline-actions" environment)
  - OpenRouter API key storage in GitHub secrets
  - No external script execution - all analysis within GitHub Actions
  - Automated workflow triggers on issue comments

- **Files Added:**
  - `.github/workflows/cline-responder.yml` - GitHub Actions workflow
  - `git-scripts/analyze-issue.sh` - TTA.dev-specialized analysis script
  - `docs/guides/github-integration.md` - Complete usage guide

**Benefits:**
- 🚀 Instant assistance for developers using TTA.dev primitives
- 📚 Direct connection between GitHub issues and knowledge base
- 🔧 Standards compliance and anti-pattern avoidance
- 📖 Working code examples and primitive recommendations
- 🤖 Autonomous analysis using full TTA.dev context

**Usage:** Comment `@cline [question]` on any GitHub issue to get AI-powered assistance tailored to TTA.dev patterns and standards.

**Example:**
```
@cline What primitive should I use for retry logic?
@cline Generate a WorkflowContext example
@cline Analyze this error and suggest a pattern
```

## [1.0.0] - 2025-11-07

### ⭐ Major Release - Production Ready

This is the first production-ready release of TTA.dev, featuring self-improving adaptive primitives, zero-cost AI code generation, and comprehensive observability integration.

**Key Achievement:** 574 tests passing with 95%+ coverage across all packages.

### Added

#### 🧠 Adaptive/Self-Improving Primitives System

**Revolutionary self-learning primitives that automatically optimize themselves:**

- **AdaptivePrimitive** - Base class for primitives that learn from execution patterns
  - Automatic strategy learning from observability data
  - Context-aware optimization (production/staging/dev)
  - Circuit breakers and safety validation
  - Learning modes: DISABLED, OBSERVE, VALIDATE, ACTIVE

- **AdaptiveRetryPrimitive** - Retry that learns optimal retry parameters
  - Learns best retry count, backoff factor, initial delay
  - Context-specific strategies (different for each environment)
  - 100% test pass rate across verification suites

- **AdaptiveFallbackPrimitive** - Fallback that learns optimal service ordering
  - Learns from failure patterns
  - Optimizes fallback order based on latency and reliability

- **AdaptiveCachePrimitive** - Cache that learns optimal TTL and size parameters
  - Learns from hit rate patterns
  - Adapts TTL based on data freshness requirements

- **AdaptiveTimeoutPrimitive** - Timeout that learns from latency distributions
  - P95/P99 percentile-based timeout learning
  - Reduces timeouts for fast services, increases for slow services

- **LogseqStrategyIntegration** - Knowledge base integration
  - Automatic strategy persistence to Logseq pages
  - Daily journal logging of learning events
  - Cross-service strategy sharing via knowledge graph
  - Complete strategy documentation with performance history

**Benefits:**
- 🎯 Zero manual tuning required
- 🔄 Automatic optimization over time
- 📊 Full observability of learning process
- 🛡️ Production-safe with circuit breakers
- 📚 Knowledge sharing across services

**Verification:** 100% pass rate across 5 independent test suites (basic learning, context-aware, performance improvement, Logseq integration, observability-driven).

**Examples:**
- `examples/auto_learning_demo.py` - Automatic learning with Logseq persistence
- `examples/verify_adaptive_primitives.py` - Comprehensive verification suite
- `examples/production_adaptive_demo.py` - Multi-region production simulation

**Documentation:**
- `ADAPTIVE_PRIMITIVES_VERIFICATION_COMPLETE.md` - Full verification report
- `ADAPTIVE_PRIMITIVES_AUDIT.md` - System audit and quality review
- `ADAPTIVE_PRIMITIVES_IMPROVEMENTS.md` - Latest improvements

#### 🤖 ACE Framework (Autonomous Cognitive Engine)

**Zero-cost AI code generation with perfect test validation:**

- **Generator Agent** - LLM-powered code generation using learned strategies
- **Reflector Agent** - Deep analysis of execution results and failure patterns
- **Curator Agent** - Intelligent playbook management and strategy selection

**Key Achievement:**
- 100% test pass rate (improved from 24% = 4.17x improvement)
- 24-48x faster than manual test writing
- $0 total cost using Google Gemini 2.0 Flash Experimental (free tier)
- E2B sandbox integration for code validation (free tier)

**A/B Testing Results:**
- ACE-generated tests: 100% pass rate
- Manual tests: 100% pass rate
- Identical quality, dramatically faster generation
- Zero false positives or invalid tests

**Documentation:**
- `ACE_COMPLETE_JOURNEY_SUMMARY.md` - Full development journey
- `ACE_AB_COMPARISON_MANUAL_VS_AI_TESTS.md` - A/B test validation
- `ACE_E2B_IMPLEMENTATION_COMPLETE.md` - E2B integration details

#### 💾 Memory Primitives

**Hybrid conversational memory with zero-setup fallback:**

- **MemoryPrimitive** - Multi-turn conversation memory
  - Zero-setup mode (works without Docker/Redis)
  - Optional Redis backend for persistence
  - Automatic fallback to in-memory if Redis unavailable
  - LRU eviction for memory management
  - Keyword search across conversation history
  - Task-specific memory namespaces

**Benefits:**
- 🚀 Works immediately without infrastructure setup
- 🔄 Clear upgrade path to persistent storage
- 🛡️ Graceful degradation on Redis failures
- 🔍 Built-in search capabilities

**Pattern Established:** "Fallback first, enhancement optional" for all future integrations.

#### 🔄 Development Lifecycle Meta-Framework

**5-stage automated workflow for feature development:**

1. **EXPERIMENTATION** - Prototype and POC development
2. **TESTING** - Test generation and validation
3. **STAGING** - Pre-production verification
4. **DEPLOYMENT** - Release preparation
5. **PRODUCTION** - Live monitoring and optimization

**Integration:**
- Logseq-based TODO management across all stages
- Automatic progression tracking
- Stage-specific validation gates
- Knowledge base integration for learning capture

#### 📚 Knowledge Base Integration (Logseq)

**Complete integration with Logseq for knowledge management:**

- Daily journal workflow with TODO tracking
- Learning paths and flashcards for primitives
- Strategy persistence for adaptive primitives
- Package-specific dashboards
- Query-powered task discovery
- Cross-service knowledge sharing

**Tag Convention:**
- `#dev-todo` - Development work
- `#learning-todo` - User education
- `#template-todo` - Reusable patterns
- `#ops-todo` - Infrastructure

#### 🔭 Enhanced Observability Integration

**Production-ready observability across all primitives:**

- **InstrumentedPrimitive** - Base class with automatic observability
  - OpenTelemetry span creation
  - Prometheus metrics export (port 9464)
  - Structured logging with correlation IDs
  - Context propagation

- **Enhanced Primitives:**
  - RouterPrimitive with route selection metrics
  - CachePrimitive with hit/miss rate tracking
  - TimeoutPrimitive with latency distribution metrics

**Benefits:**
- 30-40% cost reduction via Cache + Router optimization
- Real-time metrics in Prometheus/Grafana
- Distributed tracing across workflows
- Automatic span creation for all operations

#### 📦 Package Ecosystem

**6 production-ready packages:**

1. **tta-dev-primitives** (v1.0.0)
   - Core workflow primitives
   - Adaptive/self-improving primitives
   - Recovery patterns (Retry, Fallback, Timeout, Compensation)
   - Performance primitives (Cache, Memory)
   - ACE framework integration
   - 574 tests passing

2. **tta-observability-integration** (v1.0.0)
   - OpenTelemetry + Prometheus integration
   - Enhanced primitives with metrics
   - Prometheus exporter on port 9464
   - Grafana dashboard templates

3. **universal-agent-context** (v1.0.0)
   - Agent context management
   - Multi-agent coordination
   - Context propagation utilities
   - MIT licensed

4. **tta-kb-automation** (v1.0.0)
   - Logseq knowledge base automation
   - Automated page creation
   - Journal entry management
   - Query utilities

5. **tta-agent-coordination** (v1.0.0)
   - Multi-agent orchestration
   - Agent communication primitives
   - Coordination patterns

6. **tta-documentation-primitives** (v1.0.0)
   - Documentation generation
   - Markdown utilities
   - Example automation

#### 🧪 Comprehensive Testing

- **574 tests** passing across all packages
- **95%+ code coverage**
- **103 adaptive primitive tests**
- Integration tests for all major features
- E2B sandbox validation for generated code
- pytest-asyncio for async primitive testing

#### 📖 Documentation

- Complete user guides in `docs/`
- Architecture decision records
- Production integration guides
- Learning paths with flashcards
- Package-specific AGENTS.md files
- Comprehensive examples in all packages

### Changed

- **Import paths:** All adaptive primitives now importable from `tta_dev_primitives.adaptive`
  - Before: `from tta_dev_primitives.adaptive.retry import AdaptiveRetryPrimitive`
  - After: `from tta_dev_primitives.adaptive import AdaptiveRetryPrimitive`

- **LogseqStrategyIntegration:** Now fully exported and usable
  - Helper functions implemented inline
  - Clean public API
  - Full type annotations

- **Example file paths:** Verification examples moved to top-level `examples/`
  - `examples/auto_learning_demo.py`
  - `examples/verify_adaptive_primitives.py`
  - `examples/production_adaptive_demo.py`

### Deprecated

- None. This is the first major release.

### Removed

- None. This is the first major release.

### Fixed

- LogseqStrategyIntegration export (was commented out due to missing helper functions)
- Import consistency across all examples
- Type annotations throughout adaptive primitives
- Markdown linting issues in documentation

### Security

- All dependencies scanned (pending security audit completion)
- No known vulnerabilities
- MIT license applied to all packages

## [0.1.0] - 2025-10-28

### Added

- Initial repository structure
- Core primitive framework
- Basic observability integration
- Package scaffolding

---

## Version History

- **1.1.0** (2025-11-17) - GitHub Integration @cline Agent
- **1.0.0** (2025-11-07) - First production release
- **0.1.0** (2025-10-28) - Initial development release

## Upgrade Guide

See [MIGRATION_0.1_TO_1.0.md](docs/MIGRATION_0.1_TO_1.0.md) for detailed upgrade instructions from 0.1.x to 1.0.0.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.

## License

All packages are MIT licensed. See individual package LICENSE files.
