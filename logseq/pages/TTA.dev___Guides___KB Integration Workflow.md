# TTA.dev/Guides/KB Integration Workflow

type:: Guide
category:: [[TTA.dev/Development]]
audience:: AI Agents, Developers
created:: [[2025-11-03]]
related:: [[Whiteboard - Agentic Development Workflow]], [[TODO Management System]]

---

## 🎯 Purpose

**How to integrate code, tests, documentation, and TODOs** into a cohesive, self-documenting knowledge base.

This guide shows:

- Code → KB page creation workflow
- TODO → Implementation → Documentation pipeline
- Flashcard generation from code
- Cross-referencing strategies
- Learning path integration

**Vision:** Every piece of code is discoverable, documented, and teachable.

---

## 🔄 Complete Integration Workflow

```text
┌─────────────────────────────────────────────────────────────┐
│ PHASE 1: PLANNING                                           │
└───────────────────────────┬─────────────────────────────────┘
                            ↓
        Create TODO in Journal (Logseq)
                            ↓
        - Add to today's journal
        - Tag with #dev-todo or #learning-todo
        - Set properties (type, priority, package)
        - Link to related pages
        - Status: not-started
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ PHASE 2: RESEARCH                                           │
└───────────────────────────┬─────────────────────────────────┘
                            ↓
        Search Existing KB Pages
                            ↓
        - Check [[TTA Primitives]]
        - Review related whiteboards
        - Read similar implementations
        - Update TODO status: in-progress
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ PHASE 3: IMPLEMENTATION                                     │
└───────────────────────────┬─────────────────────────────────┘
                            ↓
        Write Code
                            ↓
        - Follow TTA.dev patterns
        - Add type hints
        - Write docstrings with KB links
        - Include examples in docstrings
                            ↓
        Write Tests
                            ↓
        - 100% coverage requirement
        - Unit tests by default
        - Mark integration tests
        - Document requirements
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ PHASE 4: DOCUMENTATION                                      │
└───────────────────────────┬─────────────────────────────────┘
                            ↓
        Create/Update KB Page
                            ↓
        - Location: logseq/pages/
        - Name: TTA Primitives___[Name].md
        - Structure: Purpose, API, Examples, Flashcards
        - Link to code and tests
                            ↓
        Add Flashcards
                            ↓
        - Create learning materials
        - Use #card marker
        - Include cloze deletions
        - Link to code examples
                            ↓
        Update Whiteboards (if architectural)
                            ↓
        - Visual representations
        - Decision trees
        - Flow diagrams
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ PHASE 5: VALIDATION                                         │
└───────────────────────────┬─────────────────────────────────┘
                            ↓
        Run Tests Locally
                            ↓
        - ./scripts/test_fast.sh
        - Check coverage
        - Integration tests if needed
                            ↓
        Quality Check
                            ↓
        - Ruff format
        - Ruff lint
        - Pyright type check
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ PHASE 6: COMPLETION                                         │
└───────────────────────────┬─────────────────────────────────┘
                            ↓
        Update Journal TODO
                            ↓
        - Mark as DONE
        - Add completion date
        - List deliverables
        - Link to KB page
        - Document key decisions
                            ↓
        Create Learning TODOs (if user-facing)
                            ↓
        - Add #learning-todo items
        - Link to flashcards
        - Add to learning paths
                            ↓
        Commit with Conventional Commits
                            ↓
        - feat/fix/docs/test prefix
        - Reference KB pages in commit message
        - List deliverables
                            ↓
                    COMPLETE ✅
```

---

## 📝 KB Page Structure

### Standard Template

```markdown
# TTA Primitives/[PrimitiveName]

type:: Primitive
category:: [[TTA Primitives]]
package:: tta-dev-primitives
created:: [[YYYY-MM-DD]]
status:: Active

---

## 🎯 Purpose

[What this primitive does and why it exists]

**Use Cases:**
- [Use case 1]
- [Use case 2]
- [Use case 3]

**Benefits:**
- [Benefit 1]
- [Benefit 2]

---

## 📚 API Reference

### Import

\`\`\`python
from tta_dev_primitives.[category] import [PrimitiveName]
\`\`\`

### Class Signature

\`\`\`python
class [PrimitiveName](InstrumentedPrimitive[TInput, TOutput]):
    def __init__(
        self,
        param1: Type1,
        param2: Type2 = default
    ):
        """Initialize [PrimitiveName].

        Args:
            param1: Description
            param2: Description (default: value)
        """
\`\`\`

### Parameters

- **param1** (\`Type1\`) - Description
- **param2** (\`Type2\`, optional) - Description. Default: \`value\`

### Returns

- **Type** - Description of return value

---

## 💻 Examples

### Basic Usage

\`\`\`python
from tta_dev_primitives import [PrimitiveName], WorkflowContext

# Create primitive
primitive = [PrimitiveName](param1=value1)

# Execute
context = WorkflowContext()
result = await primitive.execute(input_data, context)
\`\`\`

### Composition

\`\`\`python
# Sequential composition
workflow = step1 >> [PrimitiveName](...) >> step3

# Parallel composition
workflow = branch1 | [PrimitiveName](...) | branch3
\`\`\`

### Production Pattern

\`\`\`python
# Complete production setup
from tta_dev_primitives.recovery import RetryPrimitive
from tta_dev_primitives.performance import CachePrimitive

workflow = (
    CachePrimitive(ttl=3600) >>
    RetryPrimitive(max_retries=3) >>
    [PrimitiveName](...)
)
\`\`\`

---

## 🎓 Flashcards

### What is [PrimitiveName]? #card

[Description of the primitive and its purpose]

### When should you use [PrimitiveName]? #card

**Use when:**
- [Scenario 1]
- [Scenario 2]

**Don't use when:**
- [Anti-pattern 1]
- [Anti-pattern 2]

### How do you import [PrimitiveName]? #card

\`\`\`python
from tta_dev_primitives.[category] import [PrimitiveName]
\`\`\`

### Code Example #card

\`\`\`python
primitive = [PrimitiveName](param={{cloze value}})
result = await primitive.{{cloze execute}}(data, context)
\`\`\`

---

## 🔗 Related Pages

- [[TTA Primitives]] - All primitives
- [[TTA Primitives/WorkflowPrimitive]] - Base class
- [[Whiteboard - [Relevant Whiteboard]]] - Visual guide
- [[TTA.dev/Guides/[Relevant Guide]]] - Usage guide

---

## 📦 Implementation

**Source Code:**
- \`platform/primitives/src/tta_dev_primitives/[category]/[filename].py\`

**Tests:**
- \`platform/primitives/tests/unit/[category]/test_[filename].py\`
- \`platform/primitives/tests/integration/test_[filename]_integration.py\`

**Examples:**
- \`platform/primitives/examples/[filename]_example.py\`

**Coverage:** 100% ✅

---

## 🎯 Learning Path

**Prerequisites:**
- [[TTA Primitives/WorkflowPrimitive]] - Understand base class
- [[TTA.dev/Guides/First Workflow]] - Basic composition

**Next Steps:**
- [Related Primitive 1]
- [Related Primitive 2]
- [Advanced Guide]

---

## 💡 Key Insights

### Design Decisions

- [Why certain approach was chosen]
- [Tradeoffs considered]
- [Alternative approaches rejected]

### Performance Characteristics

- **Time Complexity:** O(n)
- **Space Complexity:** O(1)
- **Async:** Yes
- **Thread-Safe:** Yes (via asyncio.Lock)

### Common Pitfalls

- [Mistake 1 and how to avoid]
- [Mistake 2 and how to avoid]

---

**Last Updated:** [Date]
**Status:** Active
**Maintainer:** TTA.dev Team
```

---

## 🔗 Cross-Referencing Strategy

### Bi-Directional Links

Every entity should link to related entities:

```text
Code File (.py)
    ↕ (docstring: KB: [[Page]])
KB Page (.md)
    ↕ (Implementation: path/to/file.py)
Test File (.py)
    ↕ (docstring: KB: [[Page#Section]])
KB Page (.md)
    ↕ (Tests: path/to/test.py)
Journal TODO
    ↕ (related:: [[KB Page]])
KB Page (.md)
    ↕ (Query: {{query TODOs for this page}})
Whiteboard
    ↕ (embed: [[KB Page]])
KB Page (.md)
    ↕ (Visual: [[Whiteboard - Name]])
```

### Example: CachePrimitive Cross-References

**In Code (cache.py):**

```python
class CachePrimitive(InstrumentedPrimitive[T, T]):
    """LRU cache with TTL expiration.

    **KB:** [[TTA Primitives/CachePrimitive]]
    **Examples:** examples/cache_usage.py
    **Tests:** tests/unit/performance/test_cache_primitive.py

    **Whiteboard:** [[Whiteboard - Performance Patterns]]
    """
```

**In KB Page (TTA Primitives/CachePrimitive.md):**

```markdown
## Implementation

**Source:** `platform/primitives/src/tta_dev_primitives/performance/cache.py`
**Tests:** `platform/primitives/tests/unit/performance/test_cache_primitive.py`

## Visual Guide

[[Whiteboard - Performance Patterns#Cache Strategy]]

## TODOs

{{query (and [[#dev-todo]] [[TTA Primitives/CachePrimitive]])}}
```

**In Journal (2025_11_03.md):**

```markdown
- DONE Implement CachePrimitive #dev-todo
  related:: [[TTA Primitives/CachePrimitive]]
  related:: [[Whiteboard - Performance Patterns]]
  deliverables::
    - Source code
    - Tests (100% coverage)
    - KB page created
    - Flashcards added
```

**In Whiteboard (Whiteboard - Performance Patterns.md):**

```markdown
## Cache Strategy

See [[TTA Primitives/CachePrimitive]] for implementation details.

\`\`\`python
# Code example from [[TTA Primitives/CachePrimitive#Examples]]
cache = CachePrimitive(ttl=3600)
\`\`\`
```

---

## 🎴 Flashcard Generation

### From Code to Flashcards

```text
Code Implementation
        ↓
Identify Key Concepts
        ↓
    ┌───────────────┐
    │ What it does  │ → "What is [Feature]?" #card
    │ How to use it │ → "How do you [Action]?" #card
    │ When to use   │ → "When should you use [Feature]?" #card
    │ Parameters    │ → "What parameters does [Feature] take?" #card
    │ Return value  │ → "What does [Feature] return?" #card
    └───────────────┘
            ↓
Create Cloze Deletions
        ↓
    ┌───────────────┐
    │ Code patterns │ → Code with {{cloze}} markers
    │ Import paths  │ → from {{cloze package}} import {{cloze Class}}
    │ Key concepts  │ → [Feature] uses {{cloze strategy}} for {{cloze purpose}}
    └───────────────┘
            ↓
Add to KB Page
```

### Flashcard Templates

**Concept Understanding:**

```markdown
### What is [Feature]? #card

[Feature] is [description].

**Purpose:** [Why it exists]
**Use cases:** [When to use]
```

**Code Pattern:**

```markdown
### How do you [action] with [Feature]? #card

\`\`\`python
from tta_dev_primitives import [Feature]

# [Step-by-step example]
feature = [Feature](param=value)
result = await feature.execute(data, context)
\`\`\`
```

**Cloze Deletion:**

```markdown
### [Feature] Usage Pattern #card

\`\`\`python
from {{cloze tta_dev_primitives}} import {{cloze Feature}}

feature = {{cloze Feature}}({{cloze param}}={{cloze value}})
result = await feature.{{cloze execute}}(data, context)
\`\`\`
```

**When to Use:**

```markdown
### When should you use [Feature]? #card

**Use when:**
- [Scenario 1]
- [Scenario 2]

**Don't use when:**
- [Anti-pattern 1]
- [Anti-pattern 2]
```

---

## 📊 Quality Metrics

### KB Page Completeness

```python
kb_page_score = (
    has_purpose_section * 0.2 +          # 20%: Clear purpose
    has_api_reference * 0.2 +            # 20%: Complete API docs
    has_examples * 0.2 +                 # 20%: Working examples
    (flashcard_count / 5) * 0.2 +        # 20%: At least 5 flashcards
    has_cross_references * 0.1 +         # 10%: Links to code/tests
    has_related_pages * 0.1              # 10%: Links to other KB pages
)

# Target: > 0.9 (excellent)
# Minimum: 0.7 (acceptable)
```

### Cross-Reference Coverage

Every entity should have at least:

- **Code files** → 2 KB page links (feature page + category page)
- **KB pages** → 3+ related pages, 1+ whiteboard, 1+ code file
- **Test files** → 1 KB page link minimum
- **Journal TODOs** → 1+ KB page link
- **Whiteboards** → 3+ KB page embeds

---

## 🎯 Agent Workflow Example

### Scenario: Implementing TimeoutPrimitive

**Step 1: Create TODO**

```markdown
## [[2025-11-03]]

- TODO Implement TimeoutPrimitive for circuit breaker pattern #dev-todo
  type:: implementation
  priority:: high
  package:: tta-dev-primitives
  related:: [[TTA Primitives/TimeoutPrimitive]]
  related:: [[TTA.dev/Guides/Error Handling Patterns]]
  status:: not-started
  estimate:: 3 hours
```

**Step 2: Research**

- Read [[TTA Primitives/RetryPrimitive]] (similar pattern)
- Check [[Whiteboard - Recovery Patterns Flow]]
- Review `examples/error_handling_patterns.py`

**Step 3: Implement**

```python
# platform/primitives/src/tta_dev_primitives/recovery/timeout.py

class TimeoutPrimitive(InstrumentedPrimitive[T, T]):
    """Circuit breaker with configurable timeout.

    **KB:** [[TTA Primitives/TimeoutPrimitive]]
    **Examples:** examples/timeout_usage.py
    **Tests:** tests/unit/recovery/test_timeout_primitive.py

    **Pattern:** Circuit Breaker
    **Whiteboard:** [[Whiteboard - Recovery Patterns Flow#Circuit Breaker]]
    """
```

**Step 4: Write Tests**

```python
# tests/unit/recovery/test_timeout_primitive.py

"""Test suite for TimeoutPrimitive.

**KB:** [[TTA Primitives/TimeoutPrimitive]]
**Coverage:** 100%
"""

async def test_timeout_before_completion():
    """Test that operation times out if exceeds limit.

    **Scenario:** Long operation with short timeout
    **Expected:** TimeoutError raised

    KB: [[TTA Primitives/TimeoutPrimitive#Timeout Behavior]]
    """
```

**Step 5: Create KB Page**

Create `logseq/pages/TTA Primitives___TimeoutPrimitive.md` using template above.

**Step 6: Add Flashcards**

```markdown
### What is TimeoutPrimitive? #card

Circuit breaker primitive that enforces maximum execution time.

**Pattern:** Circuit Breaker
**Use case:** Prevent hanging operations

### How do you use TimeoutPrimitive? #card

\`\`\`python
from tta_dev_primitives.recovery import TimeoutPrimitive

timeout = TimeoutPrimitive(
    primitive=slow_operation,
    timeout_seconds={{cloze 30.0}}
)

result = await timeout.{{cloze execute}}(data, context)
\`\`\`
```

**Step 7: Update Whiteboard**

Add TimeoutPrimitive to [[Whiteboard - Recovery Patterns Flow]].

**Step 8: Complete TODO**

```markdown
- DONE Implement TimeoutPrimitive for circuit breaker pattern #dev-todo
  type:: implementation
  priority:: high
  package:: tta-dev-primitives
  completed:: [[2025-11-03]]
  deliverables::
    - TimeoutPrimitive class (timeout.py)
    - Test suite (100% coverage)
    - KB page with 5 flashcards
    - Updated Recovery Patterns whiteboard
    - Example file (timeout_usage.py)
  test-results:: All tests pass ✅
  kb-updated:: true
```

---

## 📚 Learning Path Integration

### Adding to Learning Paths

When creating a new KB page, add it to appropriate learning paths:

**Edit:** `logseq/pages/TTA.dev___Learning Paths.md`

```markdown
## Intermediate Level: Recovery Patterns

**Prerequisites:**
- [[TTA Primitives/WorkflowPrimitive]]
- [[TTA Primitives/SequentialPrimitive]]

**Path:**
1. [[TTA Primitives/RetryPrimitive]] - Exponential backoff
2. [[TTA Primitives/TimeoutPrimitive]] - Circuit breaker ← NEW
3. [[TTA Primitives/FallbackPrimitive]] - Graceful degradation
4. [[TTA Primitives/CompensationPrimitive]] - Saga pattern

**Exercises:**
- Implement retry cascade
- Build circuit breaker workflow
- Create fault-tolerant pipeline
```

---

## 🔄 Maintenance & Updates

### When to Update KB Pages

- **Bug fixes** → Update "Known Issues" or "Common Pitfalls"
- **New features** → Add to API reference and examples
- **Performance improvements** → Update "Performance Characteristics"
- **Deprecations** → Add warning banner at top
- **Breaking changes** → Create migration guide section

### Update Process

```text
Code Change
        ↓
Update KB Page
        ↓
Update Flashcards (if API changed)
        ↓
Update Examples
        ↓
Update Whiteboards (if architecture changed)
        ↓
Update Learning Paths (if prerequisites changed)
        ↓
Create Migration TODO (if breaking)
```

---

## 🔗 Related Pages

- [[Whiteboard - Agentic Development Workflow]] - Complete development cycle
- [[TODO Management System]] - TODO orchestration
- [[TTA.dev/Best Practices/Agentic Testing]] - Testing practices
- [[TTA.dev/Guides/Agentic Primitives]] - Building primitives
- [[Learning TTA Primitives]] - Learning materials

---

## 💡 Key Principles

1. **Documentation-Driven** - KB page before or during implementation
2. **Bi-Directional Links** - Every entity references related entities
3. **Flashcard First** - Learning materials are first-class
4. **Cross-Reference Everything** - Code ↔ KB ↔ Tests ↔ TODOs
5. **Visual Thinking** - Whiteboards for complex concepts
6. **Learning Path Integration** - New features added to learning sequences
7. **Maintenance Mindset** - KB pages evolve with code

---

**Last Updated:** November 3, 2025
**Status:** Active - Core Workflow
**Purpose:** Guide agents in creating integrated, self-documenting codebase
