# TTA Repository Audit Checklist

**Purpose:** Systematic audit of TTA repository to identify migration targets
**Phase:** Phase 1 - Audit & Design
**Workspace:** Use this in `/home/thein/recovered-tta-storytelling` (TTA repo)
**Created:** November 8, 2025

---

## Instructions for Copilot Session in TTA Workspace

When you open TTA repository as workspace and start a new Copilot session:

1. **Give Copilot this checklist** - Share this file
2. **Reference TTA.dev patterns** - Mention you're migrating to TTA.dev architecture
3. **Focus on code analysis** - Deep dive into actual implementations
4. **Document findings** - Create audit results in TTA repo

---

## TTA.dev Context (What You're Migrating TO)

### Target Architecture: WorkflowPrimitive Pattern

```python
from tta_dev_primitives import WorkflowPrimitive, WorkflowContext

class MyPrimitive(WorkflowPrimitive[InputType, OutputType]):
    """Type-safe, observable, composable primitive."""

    async def _execute_impl(
        self,
        input_data: InputType,
        context: WorkflowContext
    ) -> OutputType:
        # Implementation with automatic observability
        return result

# Composable with operators
workflow = step1 >> step2 >> step3  # Sequential
parallel = branch1 | branch2 | branch3  # Parallel
```

### Key TTA.dev Patterns to Apply

- **Type Safety:** Full Python 3.11+ type hints (no `Optional`, use `T | None`)
- **Observability:** Built-in OpenTelemetry spans (automatic via base class)
- **Composition:** Works with `>>` and `|` operators
- **Recovery:** Compatible with `RetryPrimitive`, `FallbackPrimitive`, etc.
- **Testing:** 100% coverage with `pytest-asyncio` and `MockPrimitive`

### TTA.dev Package Structure

```
packages/[package-name]/
├── src/[package_name]/
│   ├── core/          # Base primitives
│   ├── [domain]/      # Domain-specific primitives
│   └── observability/ # OpenTelemetry integration
├── tests/             # 100% coverage
├── examples/          # Working examples
├── docs/              # Package documentation
├── AGENTS.md          # AI agent discovery
└── README.md          # Package overview
```

---

## Audit Checklist

### Package 1: tta-narrative-engine (5,612 lines)

**Location:** `packages/tta-narrative-engine/src/tta_narrative/`

#### Coherence Module

**Path:** `packages/tta-narrative-engine/src/tta_narrative/coherence/`

- [ ] **List all files** in coherence module
- [ ] **Identify core classes** - What are the main coherence validators?
- [ ] **Map key methods** - What does coherence validation do?
- [ ] **Document inputs/outputs** - What types flow through coherence checks?
- [ ] **Find dependencies** - What external libraries/modules used?
- [ ] **Assess complexity** - How complex is the logic? (simple/medium/complex)

**Questions to answer:**
1. What makes a narrative "coherent" in TTA's definition?
2. How is coherence scored/measured?
3. What are the failure modes (when is narrative incoherent)?
4. Can this logic be extracted as a pure function?
5. What state needs to be maintained?

**Migration target:** `CoherenceValidatorPrimitive`

**Expected signature:**
```python
class CoherenceValidatorPrimitive(WorkflowPrimitive[StoryState, CoherenceResult]):
    async def _execute_impl(
        self,
        story: StoryState,
        context: WorkflowContext
    ) -> CoherenceResult:
        # Validate narrative coherence
        pass
```

#### Generation Module

**Path:** `packages/tta-narrative-engine/src/tta_narrative/generation/`

- [ ] **List all files** in generation module
- [ ] **Identify generators** - World generation? Character generation? Plot generation?
- [ ] **Map generation flow** - What's the sequence? (world → characters → plot?)
- [ ] **Document inputs/outputs** - What triggers generation? What's produced?
- [ ] **Find templates/prompts** - Any hardcoded templates for generation?
- [ ] **Assess LLM integration** - How are LLMs called? Which providers?

**Questions to answer:**
1. What is a "therapeutic world" in TTA?
2. How are worlds parameterized (settings, themes, tone)?
3. How are characters created and developed?
4. How are character arcs managed?
5. What makes generation "therapeutic" vs generic storytelling?

**Migration targets:**
- `WorldGeneratorPrimitive`
- `CharacterArcPrimitive`
- `StoryProgressionPrimitive`

#### Orchestration Module

**Path:** `packages/tta-narrative-engine/src/tta_narrative/orchestration/`

- [ ] **List all files** in orchestration module
- [ ] **Identify orchestration patterns** - How are workflows coordinated?
- [ ] **Map state management** - How is story state tracked?
- [ ] **Document transitions** - How does story progress?
- [ ] **Find decision points** - Where are branching/routing decisions made?
- [ ] **Assess parallelization** - Any parallel narrative generation?

**Questions to answer:**
1. What orchestrates the narrative workflow?
2. How is story state passed between steps?
3. Are there different orchestration modes (linear, branching, etc.)?
4. How is user input incorporated?
5. What triggers state transitions?

**Migration target:** `NarrativeOrchestratorPrimitive`

---

### Package 2: tta-ai-framework

**Location:** `packages/tta-ai-framework/src/tta_ai/`

#### Therapeutic Scoring

**Path:** `packages/tta-ai-framework/src/tta_ai/orchestration/therapeutic_scoring/`

- [ ] **Read validator.py** - How is therapeutic value measured?
- [ ] **Read enums.py** - What are the therapeutic categories/scores?
- [ ] **Document scoring algorithm** - How are scores calculated?
- [ ] **Identify score dimensions** - What aspects are scored? (safety, empathy, growth?)
- [ ] **Map to research** - Any citations/research basis for scoring?

**Questions to answer:**
1. What makes content "therapeutic"?
2. How is therapeutic value scored (0-10? categories?)?
3. What are the key dimensions (safety, empathy, growth, etc.)?
4. Can scoring be async? (likely yes for LLM-based scoring)
5. Are there different scoring modes (strict, lenient)?

**Migration target:** `TherapeuticScoringPrimitive`

#### Safety Monitoring

**Path:** `packages/tta-ai-framework/src/tta_ai/orchestration/safety_monitoring/`

- [ ] **Read service.py** - What safety checks are performed?
- [ ] **Read provider.py** - What safety providers used? (OpenAI moderation? Custom?)
- [ ] **Document safety categories** - What's considered unsafe?
- [ ] **Map to generation** - When are safety checks run? (pre-gen? post-gen?)
- [ ] **Assess performance** - How fast are safety checks?

**Questions to answer:**
1. What content is flagged as unsafe?
2. What happens when unsafe content is detected?
3. Are there different safety levels/thresholds?
4. How are false positives handled?
5. Is safety checking synchronous or async?

**Migration target:** `SafetyMonitorPrimitive`

#### Router

**Path:** `packages/tta-ai-framework/src/tta_ai/orchestration/router.py`

- [ ] **Read router logic** - How are routes selected?
- [ ] **Identify routing criteria** - Complexity? Therapeutic need? Cost?
- [ ] **Map to models** - Which LLMs are routed to?
- [ ] **Document fallback** - What happens if primary route fails?
- [ ] **Compare to TTA.dev RouterPrimitive** - Similarities/differences?

**Questions to answer:**
1. What determines routing decisions?
2. Are routes therapeutic-value based or complexity-based?
3. How does this differ from TTA.dev's RouterPrimitive?
4. Should this be merged or kept separate?
5. What's unique about therapeutic routing?

**Migration decision:** Merge with TTA.dev `RouterPrimitive` or create `TherapeuticRouterPrimitive`?

---

### Package 3: universal-agent-context (1,937 lines)

**Location:** `packages/universal-agent-context/`

**Priority:** Compare with TTA.dev's existing `universal-agent-context` package

#### Comparison Analysis

- [ ] **Compare package structures** - TTA vs TTA.dev versions
- [ ] **Identify unique features** - What's in TTA version but not TTA.dev?
- [ ] **Map overlapping features** - What's duplicated?
- [ ] **Assess maturity** - Which version is more mature?
- [ ] **Document differences** - Create comparison table

**Questions to answer:**
1. Are these truly the same package or different projects?
2. Which version should be canonical?
3. What unique features should be ported?
4. Should we merge or deprecate TTA version?
5. Is there domain-specific context management for narratives?

**Migration decision:** Merge, deprecate, or extract unique features?

---

### Package 4: ai-dev-toolkit

**Location:** `packages/ai-dev-toolkit/`

**Priority:** Low - Review for unique tools

- [ ] **List toolkit contents** - What tools are included?
- [ ] **Identify unique capabilities** - Anything not in TTA.dev?
- [ ] **Assess relevance** - Are these still needed?
- [ ] **Check dependencies** - What does toolkit depend on?
- [ ] **Compare to TTA.dev tooling** - Overlaps with TTA.dev scripts/?

**Migration decision:** Extract useful tools or deprecate?

---

## Additional Analysis

### Logseq Knowledge Base

**Location:** `.augment/kb/` (symlinked to external repo)

- [ ] **Count total pages** - Verify 306 documents
- [ ] **Identify key architectural decisions** - What ADRs exist?
- [ ] **Extract therapeutic concepts** - Domain knowledge to preserve
- [ ] **Map to TTA.dev KB structure** - How to organize in TTA.dev/logseq/?
- [ ] **Prioritize migration** - Which KB pages are essential?

### Dependencies

- [ ] **Review pyproject.toml** - What are TTA's dependencies?
- [ ] **Compare to TTA.dev** - Any incompatibilities?
- [ ] **Identify narrative-specific deps** - What's unique to narrative generation?
- [ ] **Check versions** - Any outdated dependencies?

### Tests

- [ ] **Locate test files** - Where are tests for narrative engine?
- [ ] **Assess coverage** - What's the test coverage?
- [ ] **Identify test patterns** - How are tests structured?
- [ ] **Extract test scenarios** - Useful examples for new package?

---

## Output Format

### Create These Files in TTA Repository

#### 1. `TTA_AUDIT_RESULTS.md`

```markdown
# TTA Audit Results

## tta-narrative-engine

### Coherence Module
- **Files:** [list]
- **Core classes:** [list]
- **Key methods:** [list]
- **Complexity:** [simple/medium/complex]
- **Migration notes:** [notes]

### Generation Module
- **Files:** [list]
- **Generators:** [list]
- **Migration notes:** [notes]

[Continue for all modules...]

## Recommended Migrations

1. **High Priority:**
   - CoherenceValidatorPrimitive - [reasoning]
   - TherapeuticScoringPrimitive - [reasoning]

2. **Medium Priority:**
   - [primitives]

3. **Low Priority / Consider Deprecating:**
   - [items]
```

#### 2. `TTA_PRIMITIVE_SPECS.md`

For each primitive to migrate, create detailed spec:

```markdown
# CoherenceValidatorPrimitive Specification

## Source
- **TTA Location:** `packages/tta-narrative-engine/src/tta_narrative/coherence/`
- **Files:** [list]
- **Lines of code:** ~X

## Behavior
- **Purpose:** [what it does]
- **Inputs:** [type description]
- **Outputs:** [type description]
- **Side effects:** [any]

## Migration Plan
- **Target location:** `packages/tta-narrative-primitives/src/tta_narrative_primitives/core/coherence.py`
- **Type signature:** [exact signature]
- **Dependencies:** [what it needs]
- **Complexity estimate:** [hours/days]

## Implementation Notes
- [Key algorithms to preserve]
- [Edge cases to handle]
- [Testing approach]
```

#### 3. `TTA_MIGRATION_DECISIONS.md`

Document all decisions:

```markdown
# Migration Decisions

## What to Migrate
- [List with reasoning]

## What to Deprecate
- [List with reasoning]

## Merge vs Separate
- universal-agent-context: [decision]
- router: [decision]

## Open Questions
- [Questions needing discussion]
```

---

## Success Criteria for Audit Phase

- [ ] Complete understanding of all 5,612 lines in narrative engine
- [ ] Detailed specs for 8-10 primitives to migrate
- [ ] Clear migration plan with effort estimates
- [ ] Identified all dependencies
- [ ] Documented all therapeutic domain concepts
- [ ] Created migration roadmap

---

## Context for Next Phase (Creation in TTA.dev)

When you return to TTA.dev workspace with audit results:

1. **Share `TTA_AUDIT_RESULTS.md`** - Give Copilot the findings
2. **Share `TTA_PRIMITIVE_SPECS.md`** - Detailed implementation specs
3. **Reference TTA code** - Use terminal commands if needed to check TTA code
4. **Build in TTA.dev context** - Full access to TTA.dev patterns, examples, docs

The audit findings will bridge the context gap between sessions.

---

## Tips for TTA Workspace Session

### Essential Context to Provide

When starting Copilot session in TTA workspace:

```
I'm auditing the TTA repository to migrate therapeutic narrative primitives
to TTA.dev. I have an audit checklist from TTA.dev.

TTA.dev uses:
- WorkflowPrimitive[TInput, TOutput] base class
- Type-safe composition with >> and | operators
- Built-in OpenTelemetry observability
- Python 3.11+ patterns

I need to audit TTA's tta-narrative-engine package to create migration specs.

See: docs/planning/TTA_AUDIT_CHECKLIST.md (this file)
```

### Useful Commands

```bash
# Explore narrative engine
find packages/tta-narrative-engine -name "*.py" -type f

# Count lines per module
find packages/tta-narrative-engine/src/tta_narrative/coherence -name "*.py" | xargs wc -l

# Search for key patterns
grep -r "class.*Coherence" packages/tta-narrative-engine/

# Read specific files
cat packages/tta-narrative-engine/src/tta_narrative/coherence/[file].py
```

---

**Created:** November 8, 2025
**For Phase:** Phase 1 - Audit & Design
**Use in workspace:** `/home/thein/recovered-tta-storytelling`
**Return to TTA.dev for:** Phase 2 - Package Creation


---
**Logseq:** [[TTA.dev/_archive/Nested_copies/Framework/Docs/Planning/Tta_audit_checklist]]
