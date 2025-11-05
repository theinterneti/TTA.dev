# Speckit Implementation Plan

**Date:** November 4, 2025
**Status:** Active Development
**Goal:** Implement spec-driven development workflow for TTA.dev

---

## Executive Summary

Implement the **Speckit** system - a collection of primitives that enable specification-driven development through formalized workflows. This addresses the critical Layer 2 gap identified in the AI Native Development Framework analysis.

**Timeline:** 4-5 weeks (Phase 1 of framework implementation)
**Priority:** Critical - Highest impact on reducing rework and improving quality

---

## Phase 1: Core Speckit Primitives (Week 1-2)

### Week 1: Foundation Primitives

#### Day 1-2: SpecifyPrimitive

**Purpose:** Transform high-level requirement into formal `.spec.md`

**Implementation:**
- Location: `packages/tta-dev-primitives/src/tta_dev_primitives/speckit/specify_primitive.py`
- Base class: `InstrumentedPrimitive[dict, dict]`
- Input: `{"requirement": str, "context": dict}`
- Output: `{"spec_path": str, "coverage_score": float, "gaps": list[str]}`

**Key Features:**
- Parse requirement text
- Generate structured specification
- Identify underspecified areas
- Calculate coverage score (0.0-1.0)

**Tests Required:**
1. Valid requirement generates complete spec
2. Complex requirement identifies gaps
3. Coverage score calculation
4. File creation and validation
5. Error handling for invalid inputs

**Estimated Time:** 2 days

---

#### Day 3-4: ClarifyPrimitive

**Purpose:** Run iterative clarification loop to refine specification

**Implementation:**
- Location: `packages/tta-dev-primitives/src/tta_dev_primitives/speckit/clarify_primitive.py`
- Base class: `InstrumentedPrimitive[dict, dict]`
- Input: `{"spec_path": str, "max_iterations": int, "coverage_threshold": float}`
- Output: `{"refined_spec_path": str, "iterations": int, "final_coverage": float}`

**Key Features:**
- Analyze spec for gaps
- Generate structured questions
- Incorporate answers into spec
- Iterative refinement until threshold met
- Question prioritization by impact

**Tests Required:**
1. Single iteration refinement
2. Multi-iteration convergence
3. Coverage threshold satisfaction
4. Question generation quality
5. Answer incorporation
6. Max iterations limit

**Estimated Time:** 2 days

---

#### Day 5: ValidationGatePrimitive

**Purpose:** Enforce human validation before proceeding

**Implementation:**
- Location: `packages/tta-dev-primitives/src/tta_dev_primitives/speckit/validation_gate_primitive.py`
- Base class: `InstrumentedPrimitive[dict, dict]`
- Input: `{"artifacts": list[str], "validation_criteria": dict}`
- Output: `{"approved": bool, "feedback": str, "timestamp": str}`

**Key Features:**
- Present artifacts for review
- Display validation checklist
- Block execution until approval
- Log validation decisions
- Support approval/rejection with feedback

**Tests Required:**
1. Approval flow
2. Rejection flow
3. Feedback capture
4. Timeout handling
5. Multiple artifacts validation

**Estimated Time:** 1 day

---

### Week 2: Planning & Task Primitives

#### Day 6-7: PlanPrimitive

**Purpose:** Generate implementation plan and data model

**Implementation:**
- Location: `packages/tta-dev-primitives/src/tta_dev_primitives/speckit/plan_primitive.py`
- Base class: `InstrumentedPrimitive[dict, dict]`
- Input: `{"spec_path": str, "project_context": dict}`
- Output: `{"plan_path": str, "data_model_path": str, "architecture_decisions": list[dict]}`

**Key Features:**
- Generate `plan.md` (architecture, approach, phases)
- Generate `data-model.md` (schemas, relationships)
- Identify architecture decisions
- Document risks and mitigations
- Estimate effort and dependencies

**Tests Required:**
1. Plan generation from spec
2. Data model extraction
3. Architecture decision recording
4. Risk identification
5. Dependency mapping

**Estimated Time:** 2 days

---

#### Day 8-9: TasksPrimitive

**Purpose:** Break plan into ordered, dependent tasks

**Implementation:**
- Location: `packages/tta-dev-primitives/src/tta_dev_primitives/speckit/tasks_primitive.py`
- Base class: `InstrumentedPrimitive[dict, dict]`
- Input: `{"plan_path": str, "granularity": str}`
- Output: `{"tasks_path": str, "task_count": int, "dependency_graph": dict}`

**Key Features:**
- Generate `tasks.md` with task IDs
- Identify task dependencies
- Order tasks topologically
- Estimate task durations
- Support different granularities (coarse/fine)

**Tests Required:**
1. Task generation from plan
2. Dependency detection
3. Topological ordering
4. Circular dependency detection
5. Task ID uniqueness

**Estimated Time:** 2 days

---

#### Day 10: Integration & Examples

**Purpose:** Compose primitives into complete workflow

**Implementation:**
- Location: `packages/tta-dev-primitives/examples/speckit_workflow.py`
- Demonstrate end-to-end spec-driven development
- Show composition patterns
- Include error recovery

**Key Features:**
- Complete workflow example
- Partial workflow examples (specify only, clarify only, etc.)
- Error handling patterns
- Progress tracking

**Tests Required:**
1. End-to-end workflow test
2. Partial workflow tests
3. Error recovery tests
4. Performance benchmarks

**Estimated Time:** 1 day

---

## Phase 2: Templates & Configuration (Week 3)

### Day 11-12: Specification Template

**Task:** Create `.spec.md` template

**Deliverables:**
- `.github/templates/feature.spec.md` - Standard template
- `.github/templates/feature.spec.minimal.md` - Minimal version
- `.github/templates/bugfix.spec.md` - Bug fix specific
- Template validation schema

**Sections:**
- Overview (problem, solution, success criteria)
- Requirements (functional, non-functional, out of scope)
- Architecture (components, data model, API changes)
- Implementation Plan (phases, dependencies, risks)
- Testing Strategy (unit, integration, performance)
- Clarification History
- Validation Checklist

**Estimated Time:** 2 days

---

### Day 13-14: APM Configuration Structure

**Task:** Define `apm.yml` schema

**Deliverables:**
- `apm.yml` root configuration file
- `apm.schema.json` - JSON schema for validation
- Documentation for each section

**Sections:**
```yaml
name: string
version: semver
description: string

dependencies:
  <mcp-server-name>: <version>

workflows:
  <workflow-name>:
    command: string (copilot|claude|gemini)
    file: path (to .prompt.md)
    description: string
    trigger?: string (pull_request|push|schedule)

chat-modes:
  - name: string
    file: path (to .chatmode.md)

toolset-mapping:
  <mode-name>: list[string]
```

**Estimated Time:** 2 days

---

### Day 15: Workflow Prompt Templates

**Task:** Create `.prompt.md` templates

**Deliverables:**
- `.workflows/specify.prompt.md`
- `.workflows/clarify.prompt.md`
- `.workflows/plan.prompt.md`
- `.workflows/tasks.prompt.md`
- `.workflows/implement.prompt.md`

**Template Structure:**
```markdown
---
workflow: <name>
version: <semver>
agent: <runtime>
tools: list[string]
---

# Workflow: <Title>

## Objective
<description>

## Input
<input schema>

## Process
<step-by-step process>

## Output
<output schema>

## Validation
<validation criteria>

## Next Step
<workflow continuation>
```

**Estimated Time:** 1 day

---

## Phase 3: Chat Modes & Professional Boundaries (Week 4-5)

### Week 4: Core Chat Modes

#### Day 16-17: Frontend Engineer Mode

**Task:** Create `frontend-engineer.chatmode.md`

**Deliverables:**
- `.chatmodes/frontend-engineer.chatmode.md`
- Tool allowlist (file operations on frontend files only)
- Command allowlist (npm, vite, eslint, prettier)
- MCP allowlist (context7 for frontend libraries)
- Workflow guidelines

**Sections:**
- Role description
- Professional boundaries (I CAN / I CANNOT)
- Allowed tools (with filters)
- Workflow guidelines
- Quality standards

**Estimated Time:** 2 days

---

#### Day 18-19: Backend Engineer Mode

**Task:** Create `backend-engineer.chatmode.md`

**Deliverables:**
- `.chatmodes/backend-engineer.chatmode.md`
- Tool allowlist (backend files, database operations)
- Command allowlist (pytest, uvicorn, docker)
- MCP allowlist (dbclient, context7 for backend libraries)
- API design guidelines

**Estimated Time:** 2 days

---

#### Day 20: DevOps Engineer Mode

**Task:** Create `devops-engineer.chatmode.md`

**Deliverables:**
- `.chatmodes/devops-engineer.chatmode.md`
- Tool allowlist (infrastructure files, CI/CD configs)
- Command allowlist (docker, kubectl, terraform, gh)
- MCP allowlist (grafana, infrastructure tools)
- Deployment guidelines

**Estimated Time:** 1 day

---

### Week 5: Specialized Modes & Integration

#### Day 21: Security Analyst Mode

**Task:** Create `security-analyst.chatmode.md`

**Deliverables:**
- `.chatmodes/security-analyst.chatmode.md`
- Read-only file access
- Security scanning tools
- Vulnerability reporting workflow

**Estimated Time:** 1 day

---

#### Day 22: QA Engineer Mode

**Task:** Create `qa-engineer.chatmode.md`

**Deliverables:**
- `.chatmodes/qa-engineer.chatmode.md`
- Test file operations
- Test execution tools
- Quality gate enforcement

**Estimated Time:** 1 day

---

#### Day 23-24: Toolset Integration

**Task:** Map chat modes to existing toolsets

**Deliverables:**
- Update `.vscode/copilot-toolsets.jsonc` with mode mappings
- Document mode activation
- Create mode switching guide

**Actions:**
1. Review existing 12 toolsets
2. Map toolsets to appropriate chat modes
3. Identify gaps (modes without toolsets, toolsets without modes)
4. Document recommended toolset per mode

**Estimated Time:** 2 days

---

#### Day 25: Documentation & Examples

**Task:** Complete Phase 1 documentation

**Deliverables:**
- `docs/guides/spec-driven-development.md` - Complete guide
- `docs/guides/chat-modes.md` - Mode usage guide
- Update `AGENTS.md` with speckit references
- Create example feature using speckit workflow

**Estimated Time:** 1 day

---

## Success Criteria

### Phase 1 Complete When:
- [ ] All 5 speckit primitives implemented
- [ ] 30+ tests passing (6+ per primitive)
- [ ] 100% test coverage on primitives
- [ ] Integration example working end-to-end
- [ ] Documentation complete

### Phase 2 Complete When:
- [ ] `.spec.md` template validated on 2+ features
- [ ] `apm.yml` schema defined and documented
- [ ] 5 `.prompt.md` templates created
- [ ] Templates validated with manual workflow

### Phase 3 Complete When:
- [ ] 5 chat modes defined
- [ ] Toolset mappings complete
- [ ] Mode switching documented
- [ ] Guide published

---

## Dependencies

### External Dependencies:
- None (all primitives use existing base classes)

### Internal Dependencies:
- `InstrumentedPrimitive` (already exists)
- `WorkflowContext` (already exists)
- File system operations (Python stdlib)
- YAML parsing (PyYAML)

### Optional Dependencies:
- OpenAI API (for AI-powered spec generation)
- GitHub API (for PR integration)
- Logseq API (for TODO sync)

---

## Risk Mitigation

### Risk: Speckit primitives too AI-dependent

**Mitigation:**
- Phase 1: Template-based implementation (no AI required)
- Phase 2: Add AI enhancement as optional feature
- Templates can be filled manually or by AI

### Risk: Chat modes too restrictive

**Mitigation:**
- Start with "soft" boundaries (warnings, not blocks)
- Add "unrestricted" mode for exploration
- Modes are guidelines, not hard enforcement

### Risk: APM adds complexity

**Mitigation:**
- Make APM optional (support manual workflows)
- Start with minimal CLI (`apm run <workflow>`)
- Build incrementally based on usage

---

## Metrics & Evaluation

### Phase 1 Metrics:
- Spec generation time: < 5 minutes
- Clarification rounds: ≤ 3
- Coverage improvement per iteration: +15%
- Task breakdown accuracy: 90% (measured by completion)

### Phase 2 Metrics:
- Template adoption: 50% of new features
- Template completion time: < 30 minutes
- APM workflow execution: 100% reproducible

### Phase 3 Metrics:
- Chat mode adoption: 30% of sessions
- Boundary violations: < 5%
- Developer satisfaction: 4/5 stars

---

## Next Phase Preview

### Phase 2 (APM CLI) - Weeks 6-13:
After speckit primitives are stable, implement:
- APM CLI tool (`packages/apm-cli/`)
- Draft PR workflow automation
- CI/CD agent integration
- Reproducible workflow execution

### Success Gates:
- Phase 1 must be complete before starting Phase 2
- 2-week buffer for feedback and iteration
- Validate with 3-5 real features before scaling

---

## Team Assignments

### Primary Developer:
- Speckit primitives implementation
- Test suite development
- Documentation

### Reviewer:
- Code review for each primitive
- Template validation
- Chat mode design review

### User Testing:
- Try templates on real features
- Provide feedback on chat modes
- Test end-to-end workflow

---

## Timeline Summary

```
Week 1: SpecifyPrimitive, ClarifyPrimitive, ValidationGatePrimitive
Week 2: PlanPrimitive, TasksPrimitive, Integration
Week 3: Templates, APM config, Workflow prompts
Week 4: Frontend, Backend, DevOps modes
Week 5: Security, QA modes, Toolset integration, Documentation

Total: 5 weeks (25 working days)
```

---

## Appendix: Example Workflow

### Scenario: Add Caching to LLM Pipeline

**Step 1: Specify**
```bash
# Generate specification
result = await SpecifyPrimitive().execute(
    {"requirement": "Add LRU cache with TTL to LLM pipeline"},
    context
)
# Creates: docs/specs/llm-cache.spec.md
```

**Step 2: Clarify**
```bash
# Run clarification loop
result = await ClarifyPrimitive().execute(
    {"spec_path": "docs/specs/llm-cache.spec.md", "max_iterations": 3},
    context
)
# Questions asked: "What invalidation strategy?", "TTL duration?", etc.
# Updates: docs/specs/llm-cache.spec.md with answers
```

**Step 3: Validate Spec**
```bash
# Human approval
result = await ValidationGatePrimitive().execute(
    {"artifacts": ["docs/specs/llm-cache.spec.md"]},
    context
)
# Blocks until developer approves
```

**Step 4: Plan**
```bash
# Generate implementation plan
result = await PlanPrimitive().execute(
    {"spec_path": "docs/specs/llm-cache.spec.md"},
    context
)
# Creates: docs/plans/llm-cache.plan.md, docs/plans/llm-cache.data-model.md
```

**Step 5: Tasks**
```bash
# Break into tasks
result = await TasksPrimitive().execute(
    {"plan_path": "docs/plans/llm-cache.plan.md"},
    context
)
# Creates: docs/tasks/llm-cache.tasks.md (12 ordered tasks)
```

**Step 6: Validate Plan**
```bash
# Human approval
result = await ValidationGatePrimitive().execute(
    {"artifacts": ["docs/plans/llm-cache.plan.md", "docs/tasks/llm-cache.tasks.md"]},
    context
)
# 🚨 STOP - Developer reviews architecture before implementation
```

**Result:**
- Specification: Complete, validated
- Plan: Detailed, approved
- Tasks: Ordered, ready for implementation
- Time: ~1 hour (vs 2-3 days of rework)
- Quality: High (systematic coverage)

---

**Status:** Ready to implement
**Next Action:** Start Day 1 (SpecifyPrimitive implementation)
