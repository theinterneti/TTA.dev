# TTA.dev Roadmap

**Last Updated:** June 2026 (reality-aligned; see Issue #234)

---

## Overview

This roadmap distinguishes between:

- **what is working today**
- **what is partially implemented**
- **what is still aspirational**

That distinction matters because the repository has a real core, but it is not yet honest to call
the entire platform production-ready.

**🎯 Vision:** Build reusable AI-native workflow and devops tooling that the future TTA product can
depend on.

**🚀 Long-Term Vision:** Build a complete **Atomic DevOps Architecture** - a layered agent system
for autonomous, self-improving DevSecOps. See
[`docs/architecture/ATOMIC_DEVOPS_ARCHITECTURE.md`](docs/architecture/ATOMIC_DEVOPS_ARCHITECTURE.md)
for the longer-term design direction.

---

## Current state snapshot

### Working today

- core primitives in `ttadev/primitives/`
- observability server entrypoint via `python -m ttadev.observability`
- agent and workflow foundations in `ttadev/agents/` and `ttadev/workflows/`
- a large automated test suite around the current foundation

### Known gaps

- not every package-local or historical doc has been reconciled with the current proof path yet
- Pyright still reports significant type issues
- some integrations and knowledge-base surfaces remain partial or stubbed
- the “one canonical proof path” story is now in place, but broader supporting examples still lag

---

## Phase 1: Foundation (substantial, not yet fully production-ready)

**Status:** Mostly implemented, with cleanup and reality-alignment still in progress

### Delivered components

#### 1. Core workflow primitives

**Location:** `ttadev/primitives/core/`

- ✅ `WorkflowPrimitive`
- ✅ `SequentialPrimitive`
- ✅ `ParallelPrimitive`
- ✅ `ConditionalPrimitive`
- ✅ `RouterPrimitive`

#### 2. Recovery primitives

**Location:** `ttadev/primitives/recovery/`

- ✅ `RetryPrimitive`
- ✅ `FallbackPrimitive`
- ✅ `TimeoutPrimitive`
- ✅ `CompensationPrimitive`
- ✅ `CircuitBreakerPrimitive`

#### 3. Performance and lifecycle primitives

**Locations:** `ttadev/primitives/performance/`, `ttadev/primitives/lifecycle/`

- ✅ caching and related performance helpers
- ✅ lifecycle stages and readiness checks
- ✅ orchestration building blocks

#### 4. Observability foundation

**Location:** `ttadev/observability/`

- ✅ observability server entrypoint
- ✅ v2 API routes and dashboard assets
- ✅ trace ingestion from `.observability/traces.jsonl`
- ✅ one supported observability entrypoint documented at `python -m ttadev.observability`
- ⚠ compatibility surfaces still exist for older entrypoints and v1 API consumers

#### 5. Testing and developer support

**Locations:** `tests/`, `.github/workflows/`, `.github/copilot-hooks/`

- ✅ large automated test suite
- ✅ repo quality gate hook
- ✅ lightweight public demo scripts now match the current API surface
- ⚠ type-health and broader example coverage still lag behind test volume

### Phase 1 remaining work

- reduce Pyright failures in `ttadev/`
- keep non-canonical and package-local docs aligned with the verified proof path
- clarify which backward-compatibility surfaces are transitional vs supported long term
- expand the set of runnable, current-API examples beyond the narrow proof path

---

## Phase 2: Role-Based Agent System (partially implemented, still maturing)

**Status:** Partially implemented in code; stable user-facing workflows and examples still limited

**Current implementation locations:**

- `ttadev/agents/`
- `ttadev/workflows/`

### How L0 fits Phase 2

The L0 developer control plane now lives in:

- `ttadev/control_plane/`
- `ttadev/cli/control.py`
- `ttadev/primitives/mcp_server/server.py`

Its role is not to become a parallel product inside the repo. Its role is to
make Phase 2 real by giving multi-agent work a shared local backbone for:

- task ownership
- active run state
- required review/approval gates
- workspace and file coordination
- audit-friendly workflow inspection

That means the next L0 milestone should be judged against the Phase 2 success
criteria below: if a control-plane feature does not help prove one documented,
repeatable multi-agent workflow, it is probably not the highest-leverage next
slice.

### Already present

- ✅ agent specs and registry
- ✅ agent router
- ✅ multiple domain-specific agent classes
- ✅ tool-call loop and quality-gate oriented workflow building blocks
- ✅ local L0 control-plane backbone for task/run/gate/lock/ownership workflows

### Still needed

- clearer end-to-end examples
- stronger documentation around real agent workflows
- better validation of what is stable vs experimental
- broader workflow coverage beyond the first real proof path

### Near-term success criteria

- [x] one documented, repeatable multi-agent workflow that stays green
- [x] integration test proves 3-agent workflow with L0 tracking (no API key required)
- [ ] roadmap and docs fully aligned with actual agent capabilities
- [ ] fewer type issues in agent-facing modules

### Current proof workflow

**CI-safe (no API key):**

```bash
uv run pytest tests/integration/test_multi_agent_proof.py -v
```

**Live CLI path (requires Ollama or `OPENROUTER_API_KEY`):**

```bash
tta workflow run feature_dev --goal "Add password reset flow" --track-l0 --no-confirm
tta control task show <task_id>
```

That path proves:

- one top-level L0 task per workflow execution
- one L0 run tied to the orchestrator
- per-step workflow metadata and confidence on the tracked task
- inspectable failure/completion state through the existing control-plane CLI

### Phase 2 L0 priorities

1. ✅ prove one repeatable multi-agent workflow on top of the current L0 surface (completed 2026-03-26)
2. deepen gate semantics only where that workflow needs them
3. improve telemetry attribution enough to explain who owns active workflow steps
4. connect more agent-facing surfaces to L0 state instead of creating parallel coordination models

---

## Phase 3: Guided Workflow System (Q2 2026) 📋 PLANNED

**Status:** Research Phase

**Goal:** Interactive, step-by-step guidance through complex development tasks.

### Proposed Components

#### 1. Guided Workflow Module 📋

**Location:** `ttadev/primitives/guided/` (proposed)

- 📋 `GuidedWorkflow` - Interactive workflow execution
- 📋 `Step` - Individual step with validation
- 📋 `ProgressPersistence` - Save/resume capability
- 📋 `InteractivePrompt` - User interaction handling

#### 2. Workflow Templates 📋

Pre-built workflows for common tasks:

- 📋 "Deploy MCP Server to GitHub Registry"
- 📋 "Set Up CI/CD Pipeline"
- 📋 "Add Tests to Legacy Project"
- 📋 "Create Python Package"
- 📋 "Configure Observability"

#### 3. Features 📋

- 📋 Real-time progress tracking
- 📋 Validation before proceeding to next step
- 📋 Auto-fix suggestions when validation fails
- 📋 Time estimates per step
- 📋 Optional step skipping
- 📋 Multi-session resume

### Phase 3 Success Metrics

- [ ] 5+ workflow templates available
- [ ] 100+ successful guided completions
- [ ] <1 hour average completion time for deployment
- [ ] 90%+ success rate on first attempt

### Why Not Earlier?

**Decision:** Need user validation that interactive guidance is valuable vs. just good documentation.

**Questions:**

- Do users prefer step-by-step guidance or documentation?
- What tasks benefit most from guidance?
- How much hand-holding is helpful vs. annoying?

**Current approach:** Detailed documentation and examples instead of interactive guidance.

---

## Phase 4: Knowledge Integration (Q3 2026) 🚧 STUB IMPLEMENTED

**Status:** Partially implemented — core primitive exists, integration is aspirational

**Goal:** Capture and surface best practices contextually throughout the development lifecycle.

### Implemented

**Location:** `ttadev/primitives/knowledge/`

- ✅ `KnowledgeBasePrimitive` — query a knowledge backend for contextual guidance
- ✅ `KBQuery`, `KBResult`, `KBPage` models with Pydantic validation
- ✅ Graceful degradation when the configured backend is unavailable
- ✅ Query types: `best_practices`, `common_mistakes`, `examples`, `related`, `tags`

### Still Needed 📋

- 📋 Populated knowledge content (best practices, common mistakes)
- 📋 Integration with agent system (Phase 2) for contextual queries
- 📋 Integration with guided workflows (Phase 3)
- 📋 CLI commands that surface contextual tips
- 📋 Lifecycle validation using knowledge base

### Phase 4 Success Criteria

- [ ] Knowledge base populated with meaningful content (50+ entries)
- [ ] Agent system queries knowledge base during workflow execution
- [ ] 80%+ relevance on contextual advice

### Why Not Earlier?

**Decision:** Need agent system and guided workflows to provide context for knowledge retrieval.
The primitive exists now but is essentially a stub — there is no populated backend yet.

**Current approach:** Documentation in markdown files serves this role for now.

---

## Phase 5: AI-Native IDE (Q4 2026) 📋 CONCEPT

**Status:** Long-term Vision

**Goal:** Bring TTA.dev directly into the development environment with real-time guidance.

### Proposed Components

#### 1. VS Code Extension 📋

- Real-time workflow composition suggestions
- Inline primitive documentation
- One-click primitive insertion
- Visual workflow builder
- Integrated observability viewer

#### 2. IDE Features 📋

- Proactive mistake prevention
- Context-aware completions
- Inline best practice tips
- Learning mode (explains as you work)
- Workflow debugging tools

### Phase 5 Success Metrics

- [ ] VS Code extension published
- [ ] 1,000+ active users
- [ ] <5% mistake rate with IDE guidance
- [ ] 95%+ satisfaction on developer experience

---

## Migration Guide: Vision to Reality

### For New Users

**What you can experiment with now (beyond the canonical proof path):**

1. **Try lifecycle primitives** - Explore deployment-readiness style checks

   ```bash
   uv run python scripts/assess_deployment_readiness.py --target your-project
   ```

2. **Use core workflow primitives** - Build reliable workflows

   ```python
   from ttadev.primitives import FallbackPrimitive, RetryPrimitive

   protected_call = RetryPrimitive(api_call)
   workflow = FallbackPrimitive(
       primary=protected_call,
       fallback=backup_llm,
   )
   ```

3. **Add observability** - Monitor your workflows

   ```bash
   uv run python -m ttadev.observability
   ```

**What to wait for:**

- 📋 Stable, well-documented multi-agent workflows
- 📋 Interactive guided workflows (Phase 3)
- 📋 Knowledge base queries integrated into supported workflows

### Building Agent Patterns Now

You can create agent-like behavior with current primitives:

```python
from ttadev.primitives.core.base import LambdaPrimitive
from ttadev.primitives.orchestration import DelegationPrimitive

# Simulate DeveloperAgent
developer = LambdaPrimitive(
    func=lambda data, ctx: {"analysis": "...", "suggestions": [...]},
    name="developer_agent"
)

# Simulate QAAgent
qa = LambdaPrimitive(
    func=lambda data, ctx: {"coverage": "95%", "issues": 2},
    name="qa_agent"
)

# Compose agents
team = developer >> qa
```

See: Phase 2 specs and examples are still being aligned; do not assume a canonical
`agent_patterns.py` example exists yet.

---

## Contributing to the Roadmap

This is a solo developer project. The roadmap reflects personal priorities and evolving reality — not a community vote.

If you're using TTA.dev and hit something broken or missing:

- **Open a GitHub Issue** with a clear description and reproduction steps
- **Open a Discussion** to share how you're using primitives or what you wish existed

Priority is driven by what actually unblocks building TTA, not by feature requests.

---

## Success Stories

*This section is illustrative placeholder material, not verified repository-level adoption data yet.*

### Outcomes we want to validate over time

- evidence that primitives reduce repeated workflow boilerplate
- real examples showing observability helps debug agent or workflow behavior
- measured cases where caching, retries, or fallbacks improve reliability or cost

---

## Timeline Summary

| Phase | Status | Target window | Key Deliverable |
|-------|--------|---------------|-----------------|
| Phase 1: Foundation | ⚠ Mostly implemented | Q4 2025 (delivered) | Core primitives + observability foundation |
| Phase 2: Agents | ⚠ Partially implemented | Q1–Q2 2026 | Role-based agent system + L0 control plane |
| Phase 3: Guided Workflows | 📋 Planned | Q3 2026 | Interactive step-by-step guidance |
| Phase 4: Knowledge Base | 🚧 Stub exists | Q4 2026 | Contextual best practices (primitive exists, content doesn't) |
| Phase 5: IDE Integration | 📋 Concept | 2027 | IDE and editor integrations |

---

## 🚀 Beyond 2026: Atomic DevOps Architecture

**Vision:** Complete 5-layer autonomous DevSecOps system

The **Atomic DevOps Architecture** represents the ultimate evolution of TTA.dev - a complete self-managing, self-healing DevSecOps platform built entirely from composable primitives.

### Architecture Layers

1. **L0: Meta-Control** - System self-management
   - Meta-Orchestrator coordinates all operations
   - Agent-Lifecycle-Manager handles agent health
   - AI-Observability-Manager provides system analytics

2. **L1: Orchestration** - Strategic coordination
   - ProdMgr, DevMgr, QA, Security, Release, Feedback, DevEx Orchestrators
   - High-level decision making across DevOps lifecycle

3. **L2: Domain Management** - Workflow execution
   - SCM, CI, Vulnerability, Infrastructure, Telemetry, Remediation Managers
   - State management and workflow coordination

4. **L3: Tool Expertise** - API/Interface specialization
   - GitHub, Docker, PyTest, SAST, SCA, Terraform, K8s, Prometheus Experts
   - Deep tool knowledge and best practices

5. **L4: Execution Wrappers** - CLI/SDK primitives
   - Direct tool interaction primitives
   - Error handling and retry logic

### Key Innovations

- **Security-First:** DevSec integrated at every layer
- **Self-Healing:** Predictive analytics → automated remediation
- **Platform Engineering:** Developer self-service via DevEx layer
- **AI-Powered:** Generative remediation for code and security
- **Observable:** OpenTelemetry throughout the stack

### Implementation Timeline

**2026-2027:** Foundation

- L4 execution wrappers for core tools
- L3 experts for GitHub, Docker, Terraform, Prometheus

**2027-2028:** Intelligence Layer

- L2 domain managers with workflow orchestration
- L1 orchestrators for strategic coordination
- AI-powered remediation experts

**2028-2029:** Autonomous Operations

- L0 meta-control for system self-management
- Predictive analytics and self-healing
- Full DevEx platform capabilities

**Full Details:** See [`docs/architecture/ATOMIC_DEVOPS_ARCHITECTURE.md`](docs/architecture/ATOMIC_DEVOPS_ARCHITECTURE.md)

---

## Related Documentation

- **Vision vs Reality:** `USER_JOURNEY.md` - current framing of ambition vs verified behavior
- **Current State:** `PRIMITIVES_CATALOG.md` - broad reference, still being refreshed
- **Atomic DevOps:** `docs/architecture/ATOMIC_DEVOPS_ARCHITECTURE.md` - Complete architecture
- **Getting Started:** `GETTING_STARTED.md` - current verified proof path
- **Architecture:** `docs/architecture/` - Technical decisions
- **Examples:** `scripts/test_realtime_traces.py` - currently re-verified runnable example

---

**Questions? Feedback? Ideas?**

- GitHub Discussions: <https://github.com/theinterneti/TTA.dev/discussions>
- Issues: <https://github.com/theinterneti/TTA.dev/issues>

**Last Updated:** June 2026 (reality-aligned; see Issue #234)
