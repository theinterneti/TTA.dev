# Changelog

> [!WARNING]
> This changelog is a historical release record, not a guarantee that every release claim below
> still matches the repository's current verified state.
>
> For March 2026 repo reality, prefer `README.md`, `GETTING_STARTED.md`, `QUICKSTART.md`, and
> `ROADMAP.md`.

All notable changes to TTA.dev will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

> All commits since the `v1.2.0` tag, including the **April 2026 remediation session**
> (2026-04-03). No version tag has been cut for this work yet.

### Added

#### 🛠️ GitHub Copilot Skills (April 2026)

- **`.github/skills/`** — ported 8 Claude Code skills to GitHub Copilot-compatible
  skill files, bringing AI-assistant parity across editors; skills cover primitives
  usage, anti-pattern detection, workflow orchestration, and testing patterns
  ([`c32de42`](https://github.com/theinterneti/TTA.dev/commit/c32de42))

- **`ACKNOWLEDGEMENTS.md`** — comprehensive credits for all open-source dependencies,
  tooling, and inspirations used across TTA.dev

#### 📖 Documentation (April 2026)

- **Ollama install guide** — step-by-step local model setup added to docs; referenced
  from `GETTING_STARTED.md` so zero-cost local inference is fully documented
  ([`e136f18`](https://github.com/theinterneti/TTA.dev/commit/e136f18),
  fixes [#289](https://github.com/theinterneti/TTA.dev/issues/289))

- **`GETTING_STARTED.md`** — added Step 1.5 (`.env.example` copy + free provider
  table) and Step 3c (MCP server setup with Claude Desktop config); fixes first-run
  onboarding gaps
  ([`5d4014c`](https://github.com/theinterneti/TTA.dev/commit/5d4014c),
  refs [#288](https://github.com/theinterneti/TTA.dev/issues/288),
  [#295](https://github.com/theinterneti/TTA.dev/issues/295))

#### 🤖 Task-Aware Model Routing

- **`feat(llm)`** — `TaskProfile` dataclass with `task_type` and `complexity` fields
  (`TASK_CODING`, `TASK_REASONING`, `TASK_GENERAL`, `TASK_SUMMARIZATION`, `TASK_CREATIVE`;
  `COMPLEXITY_SIMPLE`, `COMPLEXITY_MODERATE`, `COMPLEXITY_COMPLEX`)
- **`feat(llm)`** — `ModelRouterRequest.task_profile` field: pass a `TaskProfile` to rank
  available models by benchmark score for the requested task type
- **`feat(llm)`** — `ttadev/primitives/llm/task_selector.py`: scoring and ranking logic
  that maps `TaskProfile` → preferred provider tier
- **`feat(agents)`** — `ModelRouterChatAdapter` (`ttadev/agents/adapter.py`): bridges
  `ModelRouterPrimitive` to the `ChatPrimitive` protocol consumed by all agents
- **`feat(agents)`** — `AgentPrimitive.with_router(router, mode, task_profile)` classmethod:
  zero-config agent construction — reads each agent's `default_task_profile` automatically
- **`feat(agents)`** — `AgentSpec.default_task_profile` field: each concrete agent now
  declares the task profile that best describes its workload:
  - `DeveloperAgent` → `TaskProfile(TASK_CODING, COMPLEXITY_COMPLEX)`
  - `SecurityAgent` → `TaskProfile(TASK_REASONING, COMPLEXITY_COMPLEX)`
  - `DevOpsAgent` → `TaskProfile(TASK_GENERAL, COMPLEXITY_MODERATE)`
  - `QAAgent` → `TaskProfile(TASK_GENERAL, COMPLEXITY_MODERATE)`
  - `PerformanceAgent` → `TaskProfile(TASK_REASONING, COMPLEXITY_MODERATE)`
  - `GitAgent` → `TaskProfile(TASK_GENERAL, COMPLEXITY_SIMPLE)`
  - `GitHubAgent` → `TaskProfile(TASK_GENERAL, COMPLEXITY_SIMPLE)`

#### 🔍 LLM Provider Enhancements

- **`feat(llm)`** — `ModelPricing` catalog: decoupled cost metadata from `ModelEntry`;
  refreshed pricing for Groq (RPD corrected), added TPM/TPD limits, Cerebras, Cohere,
  GitHub Models, OpenRouter
- **`feat(llm)`** — Google Gemma 3 catalog entries (14.4K RPD free tier)
- **`feat(llm)`** — `HardwareDetector` + MCP LLM tools
  ([#279](https://github.com/theinterneti/TTA.dev/issues/279),
  [#266](https://github.com/theinterneti/TTA.dev/issues/266))
- **`feat(llm)`** — `ModelAdvisor` tier recommendation and ROI engine
  ([#282](https://github.com/theinterneti/TTA.dev/issues/282))
- **`feat(llm)`** — `BenchmarkFetcher` with live Artificial Analysis and HF Leaderboard 2
  integration
- **`feat(llm)`** — `ProviderModelDiscovery` and within-tier model rotation
- **`feat(llm)`** — `use_compat` flag and generic OpenAI-compatible helpers
- **`feat(llm)`** — native tool-calling, benchmark metadata, eval harness, and
  integrations package
- **`feat(cli)`** — `tta models advise` command wired into TTA CLI
  ([#282](https://github.com/theinterneti/TTA.dev/issues/282))

#### 🧠 Agent Memory

- **`feat(memory)`** — `AgentMemory` MCP tools + catalog docs
  ([#259](https://github.com/theinterneti/TTA.dev/issues/259))

### Fixed

#### 🩹 April 2026 Remediation

- **demo_workflow logging** — removed noisy debug output from `demo_workflow`; session
  list now correctly attributes actions to the originating agent
  ([`90b709b`](https://github.com/theinterneti/TTA.dev/commit/90b709b),
  fixes [#299](https://github.com/theinterneti/TTA.dev/issues/299),
  [#301](https://github.com/theinterneti/TTA.dev/issues/301))

- **`tta models advise` natural-language positional arg** — command now accepts a free-form
  natural-language description as a positional argument so callers no longer need to pass
  structured flags for simple queries
  ([`372303f`](https://github.com/theinterneti/TTA.dev/commit/372303f),
  fixes [#298](https://github.com/theinterneti/TTA.dev/issues/298))

- **P0 CLI usability (milestone [#26](https://github.com/theinterneti/TTA.dev/milestone/26))**
  ([`1102238`](https://github.com/theinterneti/TTA.dev/commit/1102238)):
  - `NoLLMProviderError` — actionable error message with provider options and a link to
    `GETTING_STARTED.md` when no LLM provider is reachable; exit code `1`
    (fixes [#287](https://github.com/theinterneti/TTA.dev/issues/287))
  - `--no-confirm` flag — fully suppresses approval-gate prompts; root cause was
    `_effective_policy()` always returning a fresh `GatePolicy(0.0)` overriding
    `auto_approve=True`; now returns a high-confidence sentinel with `[auto-approved]`
    audit trail (fixes [#296](https://github.com/theinterneti/TTA.dev/issues/296))
  - Ollama model auto-detection via `ollama list` instead of the hardcoded `qwen2.5:7b`
    model; respects `OLLAMA_MODEL` env-var override; falls back to `gemma3:4b` when Ollama
    is not installed (fixes [#297](https://github.com/theinterneti/TTA.dev/issues/297))
  - `ttadev/integrations/README.md` rewritten to accurately describe auth/CRUD utilities;
    added banner redirecting to `ttadev/primitives/integrations/` for LLM providers;
    corrected all import paths from legacy `tta_dev_integrations` stubs
    (fixes [#294](https://github.com/theinterneti/TTA.dev/issues/294))

- **Serena `--project` path** — replaced hardcoded absolute path with `${workspaceFolder}`
  so MCP config works on any machine without manual edits
  ([`8fa6945`](https://github.com/theinterneti/TTA.dev/commit/8fa6945))

- **`AGENTS.md` repo layout** — corrected ghost `platform/apps/monitoring` directory
  references to actual `ttadev/` layout; verified against live repo
  ([`e136f18`](https://github.com/theinterneti/TTA.dev/commit/e136f18),
  fixes [#291](https://github.com/theinterneti/TTA.dev/issues/291),
  [#289](https://github.com/theinterneti/TTA.dev/issues/289))

- **P0 onboarding docs**
  ([`5d4014c`](https://github.com/theinterneti/TTA.dev/commit/5d4014c)):
  - Replaced all `platform/` references with `ttadev/` in `copilot-instructions.md`,
    `python.instructions.md`, and `devops-engineer.agent.md`
  - Corrected line-length setting `100 → 88` in `python.instructions.md` to match
    `pyproject.toml`
  - Removed reference to non-existent `scripts/security_scan.py`
  - Fixed `.mcp/config.json`: replaced broken `tta-primitives` entry with correct
    `tta-dev` entry using `uv run python -m`
  - Closed [#286](https://github.com/theinterneti/TTA.dev/issues/286),
    [#288](https://github.com/theinterneti/TTA.dev/issues/288),
    [#289](https://github.com/theinterneti/TTA.dev/issues/289)

- **LLM provider registry** — updated Groq model list, added live discovery, removed dead
  models; fixed stale registry and smoke test
- **`ModelRouterPrimitive`** — resolved issues
  [#283](https://github.com/theinterneti/TTA.dev/issues/283),
  [#284](https://github.com/theinterneti/TTA.dev/issues/284),
  [#285](https://github.com/theinterneti/TTA.dev/issues/285)

### Changed

- **Provider naming** — renamed provider `"gemini"` → `"google"` throughout codebase for
  consistency with the upstream SDK

---

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


---
**Logseq:** [[TTA.dev/Changelog]]
