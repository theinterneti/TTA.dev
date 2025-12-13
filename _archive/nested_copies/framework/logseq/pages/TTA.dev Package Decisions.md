# TTA.dev Package Decisions Tracker

**Decision tracking for packages under review: keploy-framework, python-pathway, js-dev-primitives**

---

## Decision Timeline

### 📅 November 7, 2025 Deadline

- [[#keploy-framework]]
- [[#python-pathway]]

### 📅 November 14, 2025 Deadline

- [[#js-dev-primitives]]

---

## keploy-framework

### Current Status

**Location:** `packages/keploy-framework/`

**Status:** ⚠️ Under Review (Not in workspace)

**Assessment:** Complete (see `packages/keploy-framework/STATUS.md`)

### Findings

#### Structure
- Has basic directory structure
- Missing `pyproject.toml`
- No tests
- Placeholder README

#### Integration
- Not included in workspace `pyproject.toml`
- No imports from other packages
- No examples

#### Documentation
- Minimal README
- No architecture docs
- No usage examples

### Recommendation

**Archive the package** ✅

**Reasoning:**
1. Minimal implementation (placeholder only)
2. No clear integration path with TTA.dev primitives
3. Not in workspace (not being developed)
4. Keploy is better used as external tool
5. No current use case requiring deep integration

### Action Items

If decision is to **archive**:

- [ ] Create `archive/keploy-framework/` directory
- [ ] Move package to archive with timestamp
- [ ] Document decision in `archive/keploy-framework/ARCHIVE_REASON.md`
- [ ] Update `AGENTS.md` to remove from package list
- [ ] Update documentation references
- [ ] Communicate to team

If decision is to **keep**:

- [ ] Add `pyproject.toml`
- [ ] Add to workspace
- [ ] Write integration plan
- [ ] Document use cases
- [ ] Implement core functionality
- [ ] Add tests (minimum 80% coverage)
- [ ] Create examples

### Decision Log

**Date:** TBD (by 2025-11-07)

**Decision:** [To be decided]

**Rationale:** [To be documented]

**Approved by:** [Team member]

---

## python-pathway

### Current Status

**Location:** `packages/python-pathway/`

**Status:** ⚠️ Under Review (Not in workspace)

**Assessment:** Complete (see `packages/python-pathway/STATUS.md`)

### Findings

#### Structure
- Has `pyproject.toml`
- Basic package structure
- Minimal implementation

#### Purpose
- Name suggests Python code analysis
- Unclear differentiation from existing tools
- No documented use case

#### Integration
- Not in workspace
- No imports from TTA.dev
- No examples

#### Overlap
- Overlaps with: pyright, ruff, ast module
- No unique value proposition documented

### Recommendation

**Remove the package** ✅

**Reasoning:**
1. Unclear use case not documented
2. Overlaps with better-established tools
3. Not in active development
4. No integration with TTA.dev primitives
5. No community need identified

### Action Items

If decision is to **remove**:

- [ ] Create `archive/python-pathway/` directory
- [ ] Move package to archive with timestamp
- [ ] Document decision in `archive/python-pathway/REMOVAL_REASON.md`
- [ ] Update `AGENTS.md`
- [ ] Check for any hidden dependencies
- [ ] Update documentation
- [ ] Communicate to team

If decision is to **keep**:

- [ ] Document clear use case
- [ ] Add to workspace
- [ ] Write integration plan
- [ ] Differentiate from existing tools
- [ ] Implement core functionality
- [ ] Add comprehensive tests
- [ ] Create usage examples
- [ ] Update documentation

### Decision Log

**Date:** TBD (by 2025-11-07)

**Decision:** [To be decided]

**Rationale:** [To be documented]

**Approved by:** [Team member]

---

## js-dev-primitives

### Current Status

**Location:** `packages/js-dev-primitives/`

**Status:** 🚧 Placeholder (Not in workspace)

**Assessment:** Pending (by 2025-11-14)

### Current State

#### Structure
- Directory structure only
- `src/`, `tests/`, `examples/` folders exist
- No implementation files
- No `package.json` or `tsconfig.json`

#### Intent
- JavaScript/TypeScript version of TTA.dev primitives
- Cross-language primitive patterns
- Browser and Node.js support

### Options

#### Option 1: Implement JavaScript Primitives

**Pros:**
- Expands TTA.dev to JavaScript ecosystem
- Enables browser-based workflows
- Cross-language primitive patterns
- Large potential user base

**Cons:**
- Significant development effort
- Need TypeScript expertise
- Maintenance burden
- Different async patterns (Promises vs async/await)

**Requirements:**
- TypeScript implementation
- Jest or Vitest for testing
- Examples in Node.js and browser
- npm package publishing
- Documentation parity with Python

**Effort:** ~160-240 hours (1-1.5 months full-time)

#### Option 2: Document Plan, Delay Implementation

**Pros:**
- Reserves namespace
- Allows proper planning
- Can assess demand first
- Reduces immediate workload

**Cons:**
- Empty placeholder may confuse users
- Delays JavaScript ecosystem entry
- Risk of becoming abandoned

**Requirements:**
- Create `PLAN.md` with:
  - Architecture design
  - API surface
  - Implementation phases
  - Resource requirements
  - Success criteria
- Update README with timeline
- Add to long-term roadmap

**Effort:** ~8-16 hours (planning phase)

#### Option 3: Remove Placeholder

**Pros:**
- Clean repository
- No maintenance burden
- Can revisit later if needed
- Reduces confusion

**Cons:**
- Loses namespace
- Signals no JavaScript support
- May disappoint JavaScript users

**Requirements:**
- Archive directory
- Document decision
- Update documentation

**Effort:** ~2-4 hours

### Research Questions

Before deciding, investigate:

1. **Community Need**
   - Is there demand for JavaScript primitives?
   - What are JavaScript developers currently using?
   - Are there similar projects?

2. **Technical Feasibility**
   - Can we port patterns to JavaScript idioms?
   - How do we handle observability (OpenTelemetry JS)?
   - Browser vs Node.js considerations?

3. **Resource Availability**
   - Do we have JavaScript/TypeScript expertise?
   - Can we commit to maintenance?
   - What's the ROI?

4. **Strategic Alignment**
   - Does this align with TTA.dev vision?
   - Is Python-first sufficient?
   - Should we focus on Python maturity first?

### Recommendation

**Option 2: Document Plan, Delay Implementation**

**Reasoning:**
1. High potential value (JavaScript ecosystem is large)
2. Significant effort required (do it right or not at all)
3. Python primitives should reach maturity first
4. Proper planning ensures quality
5. Can assess demand before committing

**Suggested Timeline:**
- **November 2025:** Research & planning phase
- **December 2025:** Community feedback on design
- **Q1 2026:** Implementation (if validated)
- **Q2 2026:** Release v1.0 (if implemented)

### Action Items

#### If Option 1 (Implement):

- [ ] Create `package.json` and `tsconfig.json`
- [ ] Set up TypeScript build
- [ ] Port core primitives (Sequential, Parallel, etc.)
- [ ] Implement observability integration
- [ ] Add comprehensive tests
- [ ] Create examples
- [ ] Write documentation
- [ ] Publish to npm
- [ ] Update TTA.dev documentation

#### If Option 2 (Document Plan):

- [ ] Research JavaScript observability patterns
- [ ] Design TypeScript API surface
- [ ] Create `PLAN.md` with architecture
- [ ] Document implementation phases
- [ ] Estimate resource requirements
- [ ] Add to roadmap
- [ ] Gather community feedback
- [ ] Update package README

#### If Option 3 (Remove):

- [ ] Archive `js-dev-primitives/`
- [ ] Document removal reason
- [ ] Update `AGENTS.md`
- [ ] Update documentation
- [ ] Communicate decision

### Decision Log

**Date:** TBD (by 2025-11-14)

**Decision:** [To be decided]

**Rationale:** [To be documented]

**Approved by:** [Team member]

---

## Decision Process

### Step 1: Review Status Files

- Read `packages/<package>/STATUS.md`
- Review findings and recommendations
- Check for any new information

### Step 2: Team Discussion

- Present findings
- Discuss trade-offs
- Consider alternatives
- Assess resources

### Step 3: Make Decision

- Choose option
- Document rationale
- Assign action items
- Set timeline

### Step 4: Execute

- Follow action items
- Update documentation
- Communicate changes
- Archive/implement as decided

### Step 5: Review

- After 1 month: Review impact
- After 3 months: Assess satisfaction
- After 6 months: Consider reversal if needed

---

## Decision Matrix

### Evaluation Criteria

| Criterion | Weight | keploy-framework | python-pathway | js-dev-primitives |
|-----------|--------|------------------|----------------|-------------------|
| **Use Case Clarity** | High | ❌ Unclear | ❌ Not documented | ⚠️ Clear but speculative |
| **Integration Value** | High | ❌ Low | ❌ Low | ✅ High (if done well) |
| **Implementation Status** | Medium | ❌ Minimal | ❌ Minimal | ❌ None |
| **Resource Requirement** | High | Medium | Low | Very High |
| **Strategic Alignment** | High | ⚠️ Tangential | ❌ No | ✅ Yes |
| **Community Need** | Medium | ⚠️ Unknown | ❌ None identified | ⚠️ Unknown |
| **Maintenance Burden** | High | Medium | Low | Very High |
| **Risk of Removal** | Low | Low | Low | Medium |

### Recommendation Summary

| Package | Recommendation | Rationale | Effort to Keep | Effort to Remove |
|---------|---------------|-----------|----------------|------------------|
| **keploy-framework** | **Archive** | No clear integration path, minimal implementation | Very High | Low |
| **python-pathway** | **Remove** | No unique value, overlaps with existing tools | High | Very Low |
| **js-dev-primitives** | **Plan & Delay** | High potential, but needs proper planning and resources | Very High | Low |

---

## Related Pages

- [[TTA.dev/Architecture]]
- [[AGENTS]]
- [[packages/keploy-framework/STATUS.md]]
- [[packages/python-pathway/STATUS.md]]
- [[TTA.dev (Meta-Project)]]

---

## Updates

### [[2025-10-31]]

- Created decision tracking page
- Documented current status for all three packages
- Added recommendations and action items
- Set decision deadlines

### [Date TBD]

- Decisions made
- Actions executed
- Documentation updated

---

**Created:** [[2025-10-31]]
**Deadline (keploy-framework, python-pathway):** [[2025-11-07]]
**Deadline (js-dev-primitives):** [[2025-11-14]]
**Status:** Awaiting decisions


---
**Logseq:** [[TTA.dev/_archive/Nested_copies/Framework/Logseq/Pages/Tta.dev package decisions]]
