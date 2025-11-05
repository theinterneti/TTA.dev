# Whiteboard - Agentic Development Workflow

type:: Whiteboard
category:: [[TTA.dev/Guides]]
status:: Active
created:: [[2025-11-03]]
related:: [[TTA.dev/Guides/Agentic Primitives]], [[TODO Management System]]

---

## 🎯 Purpose

**Meta-pattern:** How AI agents should work on TTA.dev, integrating:

- TODO orchestration via Logseq
- Knowledge base building (for humans AND agents)
- Primitives-based development workflow
- Intelligent testing practices
- Self-documenting code

**Vision:** Agents that build modular, testable code while automatically creating documentation that teaches future agents and users.

---

## 🔄 Complete Agentic Development Cycle

```text
┌─────────────────────────────────────────────────────────────┐
│                    AGENT RECEIVES TASK                      │
│                                                             │
│  "Implement CachePrimitive with LRU + TTL"                 │
└───────────────────────────┬─────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 1: CREATE TODO IN LOGSEQ                              │
│                                                             │
│  - Add to today's journal (logseq/journals/YYYY_MM_DD.md)  │
│  - Use #dev-todo tag                                       │
│  - Set properties: type, priority, package, related        │
│  - Status: not-started                                     │
└───────────────────────────┬─────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 2: RESEARCH & DESIGN                                  │
│                                                             │
│  - Search KB: [[TTA Primitives/CachePrimitive]]           │
│  - Check related: [[TTA.dev/Guides/Performance]]          │
│  - Review examples: examples/cache_usage.py                │
│  - Update TODO: status: in-progress                        │
└───────────────────────────┬─────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 3: IMPLEMENT (Using Primitives Pattern)              │
│                                                             │
│  class CachePrimitive(InstrumentedPrimitive[T, T]):       │
│      """LRU cache with TTL.                                │
│                                                             │
│      See: [[TTA Primitives/CachePrimitive]] for details.   │
│      """                                                    │
│      async def _execute_impl(self, ...):                   │
│          # Implementation with observability               │
└───────────────────────────┬─────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 4: WRITE TESTS (Following Testing Architecture)      │
│                                                             │
│  tests/unit/performance/test_cache_primitive.py:           │
│                                                             │
│  def test_cache_hit():                                     │
│      # Fast unit test (default)                           │
│                                                             │
│  @pytest.mark.integration                                  │
│  async def test_cache_with_prometheus():                   │
│      # Integration test (explicit)                        │
└───────────────────────────┬─────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 5: CREATE KB PAGE                                     │
│                                                             │
│  Create: logseq/pages/TTA Primitives___CachePrimitive.md   │
│                                                             │
│  Content:                                                   │
│  - Purpose and use cases                                   │
│  - API documentation                                       │
│  - Code examples                                           │
│  - Flashcards for learning                                 │
│  - Links to implementation                                 │
└───────────────────────────┬─────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 6: RUN TESTS LOCALLY                                  │
│                                                             │
│  ./scripts/test_fast.sh                                    │
│  ✅ Unit tests pass                                        │
│                                                             │
│  RUN_INTEGRATION=true ./scripts/test_integration.sh        │
│  ✅ Integration tests pass                                 │
└───────────────────────────┬─────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 7: UPDATE JOURNAL & COMPLETE TODO                    │
│                                                             │
│  - Mark TODO as DONE                                       │
│  - Add completed:: [[2025-11-03]]                          │
│  - Document key decisions                                  │
│  - Link to new KB page                                     │
│  - Create learning TODOs if needed                         │
└───────────────────────────┬─────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 8: CREATE LEARNING MATERIALS                          │
│                                                             │
│  - Add flashcards to KB page                               │
│  - Create example in examples/                             │
│  - Update whiteboards if architectural change              │
│  - Add to learning paths                                   │
└───────────────────────────┬─────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 9: COMMIT & DOCUMENT                                  │
│                                                             │
│  git commit -m "feat(primitives): add CachePrimitive       │
│                                                             │
│  - LRU eviction with configurable max_size                 │
│  - TTL-based expiration                                    │
│  - Thread-safe with asyncio.Lock                           │
│  - 100% test coverage                                      │
│  - KB page: [[TTA Primitives/CachePrimitive]]"             │
└───────────────────────────┬─────────────────────────────────┘
                            ↓
                    TASK COMPLETE ✅
```

---

## 📝 TODO Management Pattern

### Creating TODOs

```markdown
## [[2025-11-03]] Daily Journal

- TODO Implement CachePrimitive with LRU + TTL #dev-todo
  type:: implementation
  priority:: high
  package:: tta-dev-primitives
  related:: [[TTA Primitives/CachePrimitive]]
  related:: [[TTA.dev/Guides/Performance]]
  status:: not-started
  estimate:: 4 hours
```

### Updating During Development

```markdown
- DOING Implement CachePrimitive with LRU + TTL #dev-todo
  type:: implementation
  priority:: high
  package:: tta-dev-primitives
  related:: [[TTA Primitives/CachePrimitive]]
  status:: in-progress
  progress:: Implemented LRU, working on TTL
  blockers:: None
```

### Completing TODOs

```markdown
- DONE Implement CachePrimitive with LRU + TTL #dev-todo
  type:: implementation
  priority:: high
  package:: tta-dev-primitives
  related:: [[TTA Primitives/CachePrimitive]]
  completed:: [[2025-11-03]]
  deliverables::
    - packages/tta-dev-primitives/src/.../cache.py
    - tests/unit/performance/test_cache_primitive.py
    - logseq/pages/TTA Primitives___CachePrimitive.md
    - examples/cache_usage.py
  test-coverage:: 100%
  kb-updated:: true
```

---

## 📚 KB Integration Workflow

```text
Code Implementation
        ↓
┌───────────────────────┐
│ Create KB Page        │
│                       │
│ Location:             │
│ logseq/pages/         │
│ TTA Primitives___     │
│ [Name].md             │
└─────────┬─────────────┘
          ↓
┌───────────────────────┐
│ Page Structure:       │
│                       │
│ # Purpose             │
│ # API Reference       │
│ # Examples            │
│ # Flashcards          │
│ # Related Pages       │
└─────────┬─────────────┘
          ↓
┌───────────────────────┐
│ Add Code References   │
│                       │
│ - Link to source file │
│ - Link to tests       │
│ - Embed examples      │
│ - Show import paths   │
└─────────┬─────────────┘
          ↓
┌───────────────────────┐
│ Create Learning       │
│ Materials             │
│                       │
│ - Flashcards          │
│ - Cloze deletions     │
│ - Practice exercises  │
└─────────┬─────────────┘
          ↓
┌───────────────────────┐
│ Link from Related     │
│ Pages                 │
│                       │
│ - Update parent pages │
│ - Add to catalogues   │
│ - Update whiteboards  │
└───────────────────────┘
```

---

## 🧪 Testing Integration Pattern

### Test First Approach

```text
Feature Request
        ↓
Write Test (TDD)
        ↓
┌───────────────────────┐
│ def test_feature():   │
│     # Expected        │
│     # behavior        │
│     assert result == X│
└─────────┬─────────────┘
          ↓
    Run Test
    ❌ Fails
          ↓
Implement Feature
          ↓
    Run Test
    ✅ Passes
          ↓
Add to KB with Test Link
```

### Test Categories Decision Tree

```text
Writing a test?
        ↓
    What does it test?
        ↓
    ┌───────┴───────┐
    │               │
Pure Logic    Uses External
    │         Resources?
    ↓               ↓
Unit Test     Integration Test
(no marker)   @pytest.mark.integration
    ↓               ↓
60s timeout   300s timeout
    ↓               ↓
Run locally   RUN_INTEGRATION=true
by default        required
    ↓               ↓
Fast CI job   Separate CI job
```

---

## 🎓 Learning Materials Creation

### After Every Feature

```text
New Feature Implemented
        ↓
┌───────────────────────────┐
│ Create Flashcards         │
│                           │
│ ### What is X? #card      │
│ X is a primitive that...  │
│                           │
│ ### When to use X? #card  │
│ Use X when you need...    │
└─────────────┬─────────────┘
              ↓
┌───────────────────────────┐
│ Add Cloze Deletions       │
│                           │
│ X uses {{cloze strategy}} │
│ for {{cloze purpose}}.    │
│ #card                     │
└─────────────┬─────────────┘
              ↓
┌───────────────────────────┐
│ Create Code Examples      │
│                           │
│ # Usage example #card     │
│ ```python                 │
│ from tta... import X      │
│ x = X(param=value)        │
│ result = await x.execute()│
│ ```                       │
└─────────────┬─────────────┘
              ↓
┌───────────────────────────┐
│ Add to Learning Path      │
│                           │
│ Update:                   │
│ [[TTA.dev/Learning Paths]]│
│                           │
│ Beginner → ... → X → ...  │
└───────────────────────────┘
```

---

## 🔗 Cross-Referencing Strategy

### Bi-directional Links

```text
Code File (cache.py)
    ↕ (docstring link)
KB Page (TTA Primitives/CachePrimitive)
    ↕ (related:: property)
TODO (journal entry)
    ↕ (related:: property)
Whiteboard (Performance Patterns)
    ↕ (embedded block)
Learning Path (Intermediate Users)
    ↕ (prerequisite:: property)
Flashcards (for review)
```

**Example in Code:**

```python
class CachePrimitive(InstrumentedPrimitive[T, T]):
    """LRU cache with TTL expiration.

    **Documentation:** [[TTA Primitives/CachePrimitive]]
    **Examples:** examples/cache_usage.py
    **Tests:** tests/unit/performance/test_cache_primitive.py
    """
```

**Example in KB Page:**

```markdown
# TTA Primitives/CachePrimitive

**Implementation:**
- Source: `packages/tta-dev-primitives/src/.../cache.py`
- Tests: `tests/unit/performance/test_cache_primitive.py`

**Related Pages:**
- [[TTA Primitives/WorkflowPrimitive]]
- [[TTA.dev/Guides/Performance]]
- [[Whiteboard - Performance Patterns]]

**TODOs:**
- {{query (and [[#dev-todo]] [[TTA Primitives/CachePrimitive]])}}
```

---

## 🤖 Agentic Testing Best Practices

### 1. Default to Safety

```python
# ✅ GOOD: Unit test by default
async def test_cache_hit():
    """Fast, isolated, safe for local development."""
    cache = CachePrimitive(ttl=60)
    await cache.execute({"key": "test"}, context)
    result = await cache.execute({"key": "test"}, context)
    assert result  # Cache hit

# ⚠️ CAUTION: Integration test (mark explicitly)
@pytest.mark.integration
async def test_cache_with_prometheus():
    """Requires Prometheus running. WSL: Use RUN_INTEGRATION=true"""
    # Service integration
```

### 2. Document Requirements

```python
@pytest.mark.integration
@pytest.mark.timeout(120)
async def test_multi_primitive_workflow():
    """
    Integration test for complete workflow.

    **Requirements:**
    - Docker running
    - Ports 8001-8002 available
    - 200MB+ memory

    **Local Usage:**
    RUN_INTEGRATION=true ./scripts/test_integration.sh

    **CI:** Runs in separate job with timeouts

    **KB Reference:** [[Whiteboard - Testing Architecture]]
    """
```

### 3. Use Mocks for Unit Tests

```python
from tta_dev_primitives.testing import MockPrimitive

async def test_workflow_composition():
    """Unit test using mocks - fast and safe."""
    # Mock expensive LLM call
    mock_llm = MockPrimitive(return_value={"result": "test"})

    # Test composition logic
    workflow = router >> mock_llm >> processor
    result = await workflow.execute(input_data, context)

    assert mock_llm.call_count == 1
```

### 4. Test Coverage = KB Quality

```text
100% Test Coverage
        ↓
Every function tested
        ↓
Every test has docstring
        ↓
Docstring links to KB
        ↓
KB page has examples
        ↓
Examples have flashcards
        ↓
Users can learn from tests
```

---

## 🎯 Agent Decision Trees

### "Should I create a KB page?"

```text
Did I implement new code?
        ↓
    ┌───┴───┐
   Yes      No
    ↓       └─→ Update existing page
    ↓
Is it a new primitive/feature?
    ↓
    ┌───┴───┐
   Yes      No
    ↓       └─→ Add to existing KB page
    ↓
CREATE NEW KB PAGE
    ↓
Include:
- Purpose & use cases
- API reference
- Code examples
- Flashcards
- Links to implementation
- Related pages
```

### "What type of test should I write?"

```text
What am I testing?
        ↓
    ┌───────┴───────┐
    │               │
Pure logic    External dependency?
    │               ↓
    ↓           ┌───┴───┐
Unit test      │       │
(no marker)   Mock    Real
    ↓          ↓       ↓
Default     Unit    Integration
            test    @pytest.mark.integration
```

### "Should I update the whiteboard?"

```text
Did I change architecture?
        ↓
    ┌───┴───┐
   Yes      No
    ↓       └─→ No whiteboard update
    ↓
Is there an existing whiteboard?
    ↓
    ┌───┴───┐
   Yes      No
    ↓       ↓
Update   Create new
existing whiteboard
```

---

## 📊 Quality Checklist (Agent Self-Review)

### Before Marking TODO as DONE

- [ ] **Code written** with type hints and docstrings
- [ ] **Tests written** with 100% coverage
- [ ] **Tests pass** locally (fast tests + integration if applicable)
- [ ] **KB page created/updated** with:
  - [ ] Purpose and use cases
  - [ ] API documentation
  - [ ] Code examples
  - [ ] Flashcards (at least 3)
  - [ ] Links to implementation
- [ ] **Whiteboards updated** if architectural change
- [ ] **Journal updated** with completion details
- [ ] **Learning TODOs created** if user-facing feature
- [ ] **Commit message** follows conventional commits
- [ ] **Links verified** in KB pages (bi-directional)

---

## 🔄 Continuous Improvement Loop

```text
Agent completes task
        ↓
Documents in KB
        ↓
Creates flashcards
        ↓
Future agent reads KB
        ↓
Learns faster
        ↓
Implements better
        ↓
Documents improvements
        ↓
KB gets better
        ↓
Cycle repeats ♻️
```

**Result:** Self-improving documentation that serves both humans and AI agents.

---

## 🎨 Visualization Best Practices

### When to Create Whiteboards

- **New architecture** patterns emerge
- **Complex flows** need visual explanation
- **Multiple components** interact
- **Decision trees** guide behavior
- **Learning paths** need structure

### Whiteboard Content

```markdown
# Whiteboard - [Topic]

## Purpose
What this visualizes and why it matters

## Visual Diagrams
ASCII art or text-based diagrams

## Code Examples
Concrete implementations

## Links
Related KB pages, code files

## Flashcards
Learning materials
```

---

## 🔗 Related Pages

- [[TODO Management System]] - Complete TODO workflow
- [[Whiteboard - Testing Architecture]] - Testing patterns
- [[TTA.dev/Guides/Agentic Primitives]] - Building with primitives
- [[TTA.dev/Learning Paths]] - Structured learning
- [[Learning TTA Primitives]] - Flashcards and exercises

---

## 💡 Key Principles

1. **TODO-Driven Development** - Every task starts with a TODO
2. **KB-First Documentation** - Document as you build
3. **Test-Driven Quality** - Tests prove correctness
4. **Learning-Oriented** - Create materials for users
5. **Self-Improving** - Each cycle makes next cycle better

---

**Last Updated:** November 3, 2025
**Status:** Active - Meta-Pattern
**Purpose:** Guide AI agents in building TTA.dev using TTA.dev patterns
