# Logseq Documentation Migration - Quick Start Guide

**Created:** 2025-10-30
**Purpose:** Step-by-step guide to start migrating TTA.dev docs to Logseq
**Time Required:** 1-2 hours for initial setup

---

## 🎯 Goal

Transform TTA.dev's linear documentation into an interconnected Logseq knowledge base using:

- **Block embedding** - Single source of truth
- **Whiteboard** - Visual architecture diagrams
- **Dynamic queries** - Auto-updating content
- **Properties** - Rich metadata and filtering

---

## ✅ Prerequisites

1. **Logseq Desktop App** installed
2. **TTA.dev repository** cloned locally
3. **Logseq graph** opened at `~/repos/TTA.dev/logseq/`
4. **Familiarity** with basic Logseq (pages, blocks, links)

---

## 📋 Phase 1: Foundation (30 minutes)

### Step 1: Create Reusable Content Library

We've already created:

- ✅ `[[Templates]]` - All templates for new pages
- ✅ `[[TTA.dev/Common]]` - Reusable blocks for embedding

**Action:** Review these pages in your Logseq graph

### Step 2: Create Main Hub Page

Create `[[TTA.dev]]` page:

```markdown
# TTA.dev

type:: [[Meta-Project]]
status:: [[Active]]
visibility:: [[Public]]

---

## Overview
- id:: tta-dev-overview
  TTA.dev is a production-ready AI development toolkit providing composable agentic primitives for building reliable AI workflows.

  **Core Value:** Transform complex async orchestration into simple, composable workflow patterns with built-in observability.

---

## 📦 Packages

### Core Packages
- [[TTA.dev/Packages/tta-dev-primitives]] - Core workflow primitives
- [[TTA.dev/Packages/tta-observability-integration]] - OpenTelemetry integration
- [[TTA.dev/Packages/universal-agent-context]] - Agent coordination
- [[TTA.dev/Packages/keploy-framework]] - API testing
- [[TTA.dev/Packages/python-pathway]] - Python analysis

### Package Overview Table
logseq.table.version:: 2
logseq.table.hover:: row
logseq.table.stripes:: true
| Package | Purpose | Status | Version |
|---------|---------|--------|---------|
| [[tta-dev-primitives]] | Core workflow primitives | [[Stable]] | 1.0.0 |
| [[tta-observability-integration]] | OpenTelemetry + Prometheus | [[Stable]] | 0.2.0 |
| [[universal-agent-context]] | Agent coordination | [[Experimental]] | 0.1.0 |

---

## 🧱 Primitives

### Core Workflow
- [[TTA.dev/Primitives/SequentialPrimitive]] - Execute steps in sequence
- [[TTA.dev/Primitives/ParallelPrimitive]] - Execute steps in parallel
- [[TTA.dev/Primitives/ConditionalPrimitive]] - Conditional branching
- [[TTA.dev/Primitives/RouterPrimitive]] - Dynamic routing

### Recovery Patterns
- [[TTA.dev/Primitives/RetryPrimitive]] - Retry with backoff
- [[TTA.dev/Primitives/FallbackPrimitive]] - Graceful degradation
- [[TTA.dev/Primitives/TimeoutPrimitive]] - Circuit breaker
- [[TTA.dev/Primitives/CompensationPrimitive]] - Saga pattern

### All Primitives Query
{{query (page-property type [[Primitive]])}}

---

## 📚 Documentation

### Getting Started
- [[TTA.dev/Guides/Getting Started]]
- [[TTA.dev/Guides/Beginner Quickstart]]
- [[TTA.dev/Guides/First Workflow]]

### Prerequisites (Embedded)
{{embed ((prerequisites-full))}}

---

## 🎯 Active Tasks

### Current Sprint
{{query (and (task TODO DOING) (between [[2025-10-28]] [[2025-11-03]]))}}

### Recently Completed
{{query (and (task DONE) (between -7d today))}}

---

## 📊 Metrics

### Documentation Coverage
- Total primitives: {{query (page-property type [[Primitive]])}}
- Total examples: {{query (page-property type [[Example]])}}
- Total guides: {{query (page-property type [[Guide]])}}

### Quality Status
- Stable primitives: {{query (and (page-property type [[Primitive]]) (page-property status [[Stable]]))}}
- Experimental: {{query (and (page-property type [[Primitive]]) (page-property status [[Experimental]]))}}

---

## 🔗 Quick Access

- [[TTA.dev/Agents]] - AI agent instructions
- [[TTA.dev/Primitives]] - Full primitives catalog
- [[TTA.dev/Architecture]] - Architecture decisions
- [[TTA.dev/Examples]] - Working examples
- [[Templates]] - Page templates
- [[TTA.dev/Common]] - Reusable content blocks
```

**Save** the page and verify queries work!

### Step 3: Create Your First Primitive Page

Create `[[TTA.dev/Primitives/SequentialPrimitive]]`:

```markdown
# SequentialPrimitive

type:: [[Primitive]]
category:: [[Core Workflow]]
package:: [[TTA.dev/Packages/tta-dev-primitives]]
status:: [[Stable]]
version:: 1.0.0
python-class:: `SequentialPrimitive`
import-path:: `from tta_dev_primitives import SequentialPrimitive`
related-primitives:: [[ParallelPrimitive]], [[ConditionalPrimitive]]

---

## Overview
- id:: sequential-primitive-overview
  Execute primitives in sequence, where each primitive's output becomes the next primitive's input. The fundamental building block for linear workflows.

## Use Cases
- id:: sequential-primitive-use-cases
  - **Data pipelines:** Input → Process → Transform → Output
  - **LLM chains:** Prompt → Generate → Refine → Format
  - **API workflows:** Fetch → Validate → Store → Notify

## Key Benefits
- id:: sequential-primitive-benefits
  - **Type-safe composition** with `>>` operator
  - **Automatic context propagation** via WorkflowContext
  - **Built-in observability** - spans for each step
  - **Error propagation** - fails fast on any error

---

## API Reference
- id:: sequential-primitive-api

### Constructor
```python
SequentialPrimitive(
    primitives: list[WorkflowPrimitive]
)
```

### Using the >> Operator (Recommended)

```python
# Chain primitives naturally
workflow = step1 >> step2 >> step3
```

---

## Examples

### Basic Sequential Workflow

- id:: sequential-basic-example

```python
{{embed ((standard-imports))}}

# Define three simple steps
async def step1(context, data):
    return {"stage": 1, "value": data * 2}

async def step2(context, data):
    return {"stage": 2, "value": data["value"] + 10}

async def step3(context, data):
    return {"stage": 3, "value": data["value"] ** 2}

# Compose with >> operator
workflow = step1 >> step2 >> step3

# Execute
context = WorkflowContext(correlation_id="example-001")
result = await workflow.execute(context, 5)
# Result: {"stage": 3, "value": 400}  # ((5*2)+10)^2
```

### LLM Chain Example

- id:: sequential-llm-chain

```python
# Real-world: LLM content pipeline
workflow = (
    prompt_builder >>
    llm_generator >>
    content_refiner >>
    output_formatter
)

result = await workflow.execute(context, user_input)
```

---

## Composition Patterns

- id:: sequential-composition-patterns

### Sequential → Parallel

```python
# Linear steps followed by parallel processing
workflow = (
    input_validator >>
    data_fetcher >>
    (processor1 | processor2 | processor3) >>
    result_aggregator
)
```

### Nested Sequential

```python
# Sub-workflows as steps
preprocessing = step1 >> step2 >> step3
postprocessing = step7 >> step8 >> step9

workflow = preprocessing >> main_step >> postprocessing
```

---

## Related Content

### Works Well With

- [[ParallelPrimitive]] - Follow sequential with parallel processing
- [[RouterPrimitive]] - Route to different sequential chains
- [[RetryPrimitive]] - Wrap sequential steps for resilience

### Used In Examples

{{query (and [[Example]] [[SequentialPrimitive]])}}

---

## Implementation Notes

- id:: sequential-implementation-notes

### Performance

- **Sequential execution** - No parallelism within the primitive
- **Memory efficient** - One step at a time, no buffering
- **Observability overhead** - ~1-2ms per step for tracing

### Best Practices

- **Keep steps focused** - Each step should do one thing well
- **Use WorkflowContext** - Pass shared state via context, not globals
- **Add retry logic** - Wrap with RetryPrimitive for unreliable operations
- **Monitor spans** - Each step creates a child span for observability

### Edge Cases

- **Empty primitives list** - Raises `ValueError`
- **Type mismatches** - Output of step N must match input of step N+1
- **Exceptions** - Any step failure stops the workflow immediately

---

## Metadata

**Source:** [GitHub](https://github.com/theinterneti/TTA.dev/tree/main/packages/tta-dev-primitives/src/tta_dev_primitives/core/sequential.py)
**Tests:** [Test Suite](https://github.com/theinterneti/TTA.dev/tree/main/packages/tta-dev-primitives/tests/test_sequential.py)
**Last Updated:** [[2025-10-30]]
**Test Coverage:** 100%

```

---

## 📋 Phase 2: Block Embedding (20 minutes)

### Step 4: Use Block References

In any guide or example, reference shared content:

**Example: Create `[[TTA.dev/Guides/Getting Started]]`:**

```markdown
# Getting Started with TTA.dev

type:: [[Guide]]
category:: [[Getting Started]]
difficulty:: [[Beginner]]
estimated-time:: 15 minutes

---

## Prerequisites

{{embed ((prerequisites-full))}}

## Installation

{{embed ((uv-installation))}}

{{embed ((project-setup))}}

## Your First Workflow

Now let's create your first workflow using [[SequentialPrimitive]]:

{{embed ((sequential-basic-example))}}

## Next Steps
- Try [[TTA.dev/Guides/Building Agentic Workflows]]
- Explore [[TTA.dev/Primitives]] catalog
```

**Notice:** All the installation steps, prerequisites, and examples are **embedded**, not copied!

### Step 5: Verify Embedding Works

1. Edit the `[[TTA.dev/Common]]` page
2. Change the Python version in `prerequisites-full` from 3.11+ to 3.12+
3. Open `[[TTA.dev/Guides/Getting Started]]`
4. **Verify** the change appears automatically!

This is the **magic** - edit once, update everywhere!

---

## 🎨 Phase 3: Visual Architecture (30 minutes)

### Step 6: Create Your First Whiteboard

1. Click "Whiteboards" in Logseq sidebar
2. Create new whiteboard: "TTA.dev Primitive Composition"
3. Add blocks from documentation:
   - Drag `[[SequentialPrimitive]]` onto whiteboard
   - Drag `[[ParallelPrimitive]]` onto whiteboard
   - Drag `[[RouterPrimitive]]` onto whiteboard

4. **Draw connections:**
   - SequentialPrimitive → "chains to" → ParallelPrimitive
   - RouterPrimitive → "routes to" → SequentialPrimitive

5. **Add visual elements:**
   - Shapes for different categories (Core, Recovery, Performance)
   - Colors for status (Stable = green, Experimental = yellow)
   - Arrows showing data flow

6. **Link back to documentation:**
   - Right-click any block → "Go to page"
   - Edit page → reference whiteboard: `![[Whiteboard: Primitive Composition]]`

---

## 🔍 Phase 4: Dynamic Queries (20 minutes)

### Step 7: Create Query-Driven Dashboards

Create `[[TTA.dev/Dashboard]]`:

```markdown
# TTA.dev Development Dashboard

type:: [[Dashboard]]

---

## 🎯 Active Work

### Current Sprint Tasks
{{query (and (task TODO DOING) [[TTA.dev]] (between [[2025-10-28]] [[2025-11-03]]))}}

### Blocked Items
{{query (and (task TODO) (property blocked true))}}

---

## 📊 Primitives Status

### Stable Primitives
{{query (and (page-property type [[Primitive]]) (page-property status [[Stable]]))}}

### Experimental Features
{{query (and (page-property type [[Primitive]]) (page-property status [[Experimental]]))}}

### Deprecated
{{query (and (page-property type [[Primitive]]) (page-property status [[Deprecated]]))}}

---

## 📚 Documentation Coverage

### Missing Examples
{{query (and (page-property type [[Primitive]]) (not (mentions [[Example]])))}}

### Recently Updated
{{query (and (page-property type [[Documentation]]) (between -7d today))}}

---

## 🧪 Testing

### Low Coverage Primitives
{{query (and (page-property type [[Primitive]]) (property test-coverage < 90))}}

---

## 🔗 Most Referenced Pages

### Top 10 by Backlinks
(Manually check page backlinks or use graph view)

1. [[SequentialPrimitive]] - X references
2. [[WorkflowContext]] - Y references
...
```

### Step 8: Add Properties for Query Filtering

Go back to your primitive page and add more properties:

```markdown
# SequentialPrimitive

type:: [[Primitive]]
category:: [[Core Workflow]]
status:: [[Stable]]
test-coverage:: 100
last-updated:: [[2025-10-30]]
examples-count:: 5
github-stars:: 120
complexity:: [[Low]]
```

Now queries can filter by **any property**!

---

## 📊 Phase 5: Tables for Structured Data (15 minutes)

### Step 9: Create Primitive Comparison Table

Create `[[TTA.dev/Primitives/Comparison]]`:

```markdown
# Primitives Comparison Table

logseq.table.version:: 2
logseq.table.hover:: row
logseq.table.stripes:: true
logseq.table.borders:: false
logseq.color:: blue

| Primitive | Category | Use Case | Complexity | Status |
|-----------|----------|----------|------------|--------|
| [[SequentialPrimitive]] | Core | Linear workflows | Low | [[Stable]] |
| [[ParallelPrimitive]] | Core | Concurrent execution | Medium | [[Stable]] |
| [[RouterPrimitive]] | Core | Dynamic routing | Medium | [[Stable]] |
| [[RetryPrimitive]] | Recovery | Error resilience | Low | [[Stable]] |
| [[FallbackPrimitive]] | Recovery | Graceful degradation | Low | [[Stable]] |
| [[CachePrimitive]] | Performance | Result caching | Medium | [[Stable]] |
```

**Note:** Each cell is a link, click through to the full documentation!

---

## ✅ Success Criteria

After completing these phases, you should have:

- [x] **Main hub page** with working queries
- [x] **5+ primitive pages** with full documentation
- [x] **Reusable content blocks** being embedded
- [x] **Block references** working (edit once, update everywhere)
- [x] **Whiteboard** visualizing architecture
- [x] **Dynamic queries** showing relevant content
- [x] **Properties** enabling filtering and organization
- [x] **Tables** for structured comparisons

---

## 🚀 Next Steps

### Expand Documentation

1. **Create remaining primitives** (use template: `[[Templates]]#new-primitive`)
2. **Add examples** for each primitive
3. **Write guides** for common workflows
4. **Document architecture decisions** (ADRs)

### Enhance Queries

1. **Task dashboard** - All TODO/DOING across project
2. **Coverage report** - Missing documentation
3. **Quality metrics** - Test coverage, update frequency

### Visual Architecture

1. **Primitive taxonomy** whiteboard
2. **Package dependencies** diagram
3. **User journey** flows

### Advanced Features

1. **Linked References** - See what references each page
2. **Graph View** - Visualize entire knowledge graph
3. **Journals** - Daily development notes linked to pages
4. **Templates** - Custom templates for recurring patterns

---

## 💡 Pro Tips

### 1. Use Block IDs Liberally

```markdown
- id:: important-concept
  This is an important concept that will be referenced often
```

### 2. Think in Graphs, Not Trees

- Don't worry about perfect hierarchy
- Link liberally between related concepts
- Let queries and backlinks create structure dynamically

### 3. Embed, Don't Copy

- If content appears in multiple places, embed it
- Single source of truth = easier maintenance
- Example: Installation steps, code patterns, definitions

### 4. Properties Over Content

- Use properties for filtering and queries
- Keep property values consistent (use existing pages)
- Example: `status:: [[Stable]]` not `status:: stable`

### 5. Queries Are Your Friend

- Start simple: `{{query [[Tag]]}}`
- Add filters: `{{query (and [[Tag1]] [[Tag2]])}}`
- Use properties: `{{query (page-property type [[Primitive]])}}`

### 6. Whiteboard for Understanding

- Use whiteboards to understand complex relationships
- Drag-and-drop actual content blocks
- Visual + text = better comprehension

---

## 🎯 Quick Reference

### Useful Syntax

```markdown
# Page Link
[[Page Name]]

# Block Reference (inline)
((block-id))

# Block Embed (full block)
{{embed ((block-id))}}

# Query
{{query (and [[Tag1]] [[Tag2]])}}

# Property
key:: value
key:: [[Page Value]]

# Block ID
- id:: unique-identifier
  Content

# Table (v2)
logseq.table.version:: 2
| Col1 | Col2 |
|------|------|
| A    | B    |
```

---

## 📞 Need Help?

- **Logseq Docs:** <https://docs.logseq.com/>
- **Templates:** See `[[Templates]]` page
- **Common Blocks:** See `[[TTA.dev/Common]]` page
- **Examples:** Look at existing primitive pages

---

**Last Updated:** 2025-10-30
**Status:** Ready to Use
**Estimated Time:** 1-2 hours initial setup


---
**Logseq:** [[TTA.dev/Local/Planning/Logseq_migration_quickstart]]
