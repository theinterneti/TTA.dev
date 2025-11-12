# Migration Guide: Transitioning to TTA.dev Knowledge Graph System v2.0

**Migrate existing Logseq pages to the new framework primitive taxonomy and property schema**

**Created:** November 11, 2025
**Target Completion:** Rolling migration (no deadline)
**Status:** Reference Guide

---

## 🎯 Overview

This guide helps you migrate existing Logseq pages to the new TTA.dev Knowledge Graph System v2.0, which introduces:

- **5 primitive types:** [C] CoreConcept, [P] Primitive, [D] DataSchema, [I] Integration, [S] Service
- **Unified property schema:** Type-specific properties for each primitive type
- **Namespace organization:** `TTA.dev/*` hierarchical structure
- **Enhanced linking:** Property-based and content-based links

### Who Needs to Migrate?

- **Existing pages** - Pages created before November 11, 2025
- **Non-standard pages** - Pages without `type::` property
- **Flat hierarchy** - Pages not using `TTA.dev/*` namespace

### Migration is Optional

The new system **coexists** with old pages. Migrate when:
- ✅ Creating new pages (use templates)
- ✅ Significantly updating existing pages
- ⚠️ Page is frequently referenced (high value)
- ❌ Page is rarely used (low priority)

---

## 📋 Migration Checklist

Use this checklist for each page:

- [ ] **Step 1:** Determine primitive type ([C], [P], [D], [I], or [S])
- [ ] **Step 2:** Rename page to use `TTA.dev/*` namespace
- [ ] **Step 3:** Add required universal properties
- [ ] **Step 4:** Add type-specific properties
- [ ] **Step 5:** Update links to use full namespace paths
- [ ] **Step 6:** Review and refine content
- [ ] **Step 7:** Test queries and backlinks
- [ ] **Step 8:** Mark as migrated (add `migrated:: true`)

---

## 🔄 Migration Process

### Step 1: Determine Primitive Type

**Decision Tree:**

```
Is it an architectural principle or design pattern?
  └─ YES → [C] CoreConcept
  └─ NO  → Continue

Is it executable code (extends WorkflowPrimitive)?
  └─ YES → [P] Primitive
  └─ NO  → Continue

Is it a data structure/model (Pydantic, TypedDict)?
  └─ YES → [D] DataSchema
  └─ NO  → Continue

Does it connect to an external service/tool?
  └─ YES → [I] Integration
  └─ NO  → Continue

Is it infrastructure or runtime service?
  └─ YES → [S] Service
  └─ NO  → [C] CoreConcept (default)
```

**Examples:**

| Old Page Name | Type | New Page Name |
|---------------|------|---------------|
| `RetryPrimitive` | [P] | `TTA.dev/Primitives/Recovery/RetryPrimitive` |
| `WorkflowContext` | [D] | `TTA.dev/Data/WorkflowContext` |
| `Composition` | [C] | `TTA.dev/Concepts/Composition` |
| `E2BPrimitive` | [I] | `TTA.dev/Integrations/CodeExecution/E2BPrimitive` |
| `ObservabilityStack` | [S] | `TTA.dev/Services/ObservabilityStack` |

### Step 2: Rename Page

**In Logseq:**

1. Open the page you want to migrate
2. Click the page title
3. Rename to use `TTA.dev/*` namespace:
   - Primitives: `TTA.dev/Primitives/{Category}/{Name}`
   - Concepts: `TTA.dev/Concepts/{Name}`
   - Data: `TTA.dev/Data/{Name}`
   - Integrations: `TTA.dev/Integrations/{Category}/{Name}`
   - Services: `TTA.dev/Services/{Name}`

**Category Mapping for Primitives:**

- Core → `TTA.dev/Primitives/Core/`
- Recovery → `TTA.dev/Primitives/Recovery/`
- Performance → `TTA.dev/Primitives/Performance/`
- Orchestration → `TTA.dev/Primitives/Orchestration/`
- Testing → `TTA.dev/Primitives/Testing/`
- Observability → `TTA.dev/Primitives/Observability/`

### Step 3: Add Universal Properties

**All pages need these properties:**

```markdown
type:: [C] CoreConcept | [P] Primitive | [D] DataSchema | [I] Integration | [S] Service
status:: stable | beta | experimental | deprecated
tags:: [comma-separated tags]
context-level:: 1-Strategic | 2-Operational | 3-Technical
created-date:: [[2025-11-11]]
last-updated:: [[2025-11-11]]
migrated:: true
```

**Context-Level Guide:**

- **1-Strategic** - Why (architectural principles, design patterns)
- **2-Operational** - What (workflows, integrations, services)
- **3-Technical** - How (implementations, configurations, code)

### Step 4: Add Type-Specific Properties

#### For [C] CoreConcept Pages

```markdown
summary:: [One-sentence definition]
implemented-by:: [[TTA.dev/Primitives/...]]
related-concepts:: [[TTA.dev/Concepts/...]]
documentation:: [path to doc file]
examples:: [path to example files]
```

#### For [P] Primitive Pages

```markdown
import-path:: from tta_dev_primitives.{module} import {Name}
source-file:: packages/tta-dev-primitives/src/...
category:: core | recovery | performance | orchestration | testing | observability
input-type:: [type annotation]
output-type:: [type annotation]
composes-with:: [[TTA.dev/Primitives/...]]
uses-data:: [[TTA.dev/Data/...]]
observability-spans:: {span names}
test-coverage:: 100%
example-files:: [paths]
```

#### For [D] DataSchema Pages

```markdown
source-file:: packages/tta-dev-primitives/src/...
base-class:: BaseModel | TypedDict | dataclass
used-by:: [[TTA.dev/Primitives/...]]
fields:: field1, field2, field3
validation:: [validation rules]
```

#### For [I] Integration Pages

```markdown
integration-type:: mcp | llm | database | code-execution | tool
external-service:: [service name]
wraps-primitive:: [[TTA.dev/Primitives/...]]
requires-config:: [[TTA.dev/Data/...Config]]
api-endpoint:: [URL]
dependencies:: package1, package2
import-path:: from tta_dev_primitives.integrations import {Name}
source-file:: packages/tta-dev-primitives/src/...
```

#### For [S] Service Pages

```markdown
service-type:: infrastructure | observability | api | database | cache
deployment:: docker | systemd | cloud | embedded
exposes:: [APIs, endpoints, primitives]
depends-on:: [[TTA.dev/Services/...]]
configuration:: [[TTA.dev/Data/...Config]]
monitoring:: [observability details]
```

### Step 5: Update Links

**Find and replace old links with new namespace paths:**

**Example:**

```markdown
# Old (before migration)
This primitive uses [[WorkflowContext]] and composes with [[RetryPrimitive]].

# New (after migration)
This primitive uses [[TTA.dev/Data/WorkflowContext]] and composes with
[[TTA.dev/Primitives/Recovery/RetryPrimitive]].
```

**Bulk Link Update Tips:**

1. **Find all references:**
   - Use Logseq's search: `{{query [[OldPageName]]}}`
   - List all pages that link to this one

2. **Update references systematically:**
   - Update property links first (queryable)
   - Update content links second (contextual)

3. **Verify backlinks:**
   - Check "Linked References" section
   - Ensure old links redirect correctly

### Step 6: Review and Refine Content

**Content Structure:**

```markdown
# TTA.dev/Primitives/{Category}/{Name}

[Properties...]

---

## Overview

[Brief description of what this is and when to use it]

---

## [Type-Specific Sections]

[Use template sections as guide]

---

## Related Content

[Links to related primitives, concepts, data schemas]

---

## Tags

[Relevant tags]
```

**Quality Checks:**

- [ ] All sections make sense for this primitive type
- [ ] Code examples are correct and tested
- [ ] Links resolve to valid pages
- [ ] Properties are complete and accurate
- [ ] Content is clear and concise

### Step 7: Test Queries and Backlinks

**Test Property Queries:**

```clojure
# Find this page by type
{{query (property type "[[P] Primitive")}}

# Find related primitives
{{query (property composes-with [[TTA.dev/Primitives/Recovery/RetryPrimitive]])}}

# Find by category
{{query (and [[Primitive]] (property category recovery))}}
```

**Test Backlinks:**

1. Click page title to see "Linked References"
2. Verify expected pages link to this one
3. Check property-based and content-based links both work

### Step 8: Mark as Migrated

Add to page properties:

```markdown
migrated:: true
migration-date:: [[2025-11-11]]
migration-version:: 2.0
```

---

## 📊 Migration Examples

### Example 1: Migrating a Primitive Page

**Before:**

```markdown
# CachePrimitive

status:: stable

## Overview
CachePrimitive provides LRU caching...

## Usage
```python
from tta_dev_primitives.performance import CachePrimitive
```
```

**After:**

```markdown
# TTA.dev/Primitives/Performance/CachePrimitive

type:: [P] Primitive
status:: stable
category:: performance
tags:: #primitive, #caching, #performance
context-level:: 2-Operational
import-path:: from tta_dev_primitives.performance import CachePrimitive
source-file:: packages/tta-dev-primitives/src/tta_dev_primitives/performance/cache.py
input-type:: T
output-type:: T
composes-with:: [[TTA.dev/Primitives/Recovery/RetryPrimitive]]
uses-data:: [[TTA.dev/Data/WorkflowContext]]
observability-spans:: cache.execute, cache.hit, cache.miss
test-coverage:: 100%
example-files:: packages/tta-dev-primitives/examples/caching.py
created-date:: [[2025-10-01]]
last-updated:: [[2025-11-11]]
migrated:: true
migration-date:: [[2025-11-11]]

---

## Overview

CachePrimitive provides LRU caching with TTL support for expensive operations,
reducing cost and latency. Commonly used with [[TTA.dev/Primitives/Recovery/RetryPrimitive]]
to avoid retrying cached results.

---

## Usage

```python
from tta_dev_primitives.performance import CachePrimitive
from tta_dev_primitives import WorkflowContext

cached = CachePrimitive(
    primitive=expensive_llm_call,
    ttl_seconds=3600,
    max_size=1000
)

context = WorkflowContext()
result = await cached.execute(data, context)
```

---

## Tags

#primitive #caching #performance #lru #ttl
```

### Example 2: Migrating a Concept Page

**Before:**

```markdown
# Observability

## What is Observability?
Observability in TTA.dev means...
```

**After:**

```markdown
# TTA.dev/Concepts/Observability

type:: [C] CoreConcept
status:: stable
tags:: #concept, #observability, #monitoring
context-level:: 1-Strategic
summary:: Built-in tracing, metrics, and logging enable understanding workflow behavior in production
implemented-by:: [[TTA.dev/Primitives/Observability/InstrumentedPrimitive]], [[TTA.dev/Services/ObservabilityStack]]
related-concepts:: [[TTA.dev/Concepts/Composition]], [[TTA.dev/Concepts/TypeSafety]]
documentation:: docs/observability/
examples:: packages/tta-dev-primitives/examples/observability_demo.py
created-date:: [[2025-10-01]]
last-updated:: [[2025-11-11]]
migrated:: true

---

## Overview

**Observability** in TTA.dev provides production-grade visibility into workflow
execution through automatic tracing, metrics, and structured logging. Built on
OpenTelemetry standards, it requires zero configuration.

---

## Why This Matters

[Content...]

---

## Tags

#concept #observability #monitoring #opentelemetry
```

---

## 🔍 Finding Pages to Migrate

### Query for Non-Migrated Pages

```clojure
# Pages without type property
{{query (not (property type))}}

# Pages not in TTA.dev namespace
{{query (not (page-property namespace "TTA.dev"))}}

# Pages marked for migration
{{query (property needs-migration true)}}
```

### Priority Order

**High Priority (Migrate First):**
1. Frequently accessed pages (check backlinks)
2. Core primitive pages (SequentialPrimitive, RetryPrimitive, etc.)
3. Key concept pages (Composition, Observability, etc.)
4. Documentation index pages

**Medium Priority:**
5. Secondary primitives
6. Data schema pages
7. Integration pages

**Low Priority:**
8. Experimental pages
9. Deprecated pages
10. Archive pages

---

## ⚠️ Common Migration Issues

### Issue 1: Link Conflicts

**Problem:** Old and new page names create duplicate links

**Solution:**
1. Rename old page to `{Name} (Old)`
2. Create new page with correct namespace
3. Copy content and update
4. Redirect old page: `redirect:: [[TTA.dev/...]]`
5. Mark old page as deprecated

### Issue 2: Missing Properties

**Problem:** Don't know what value to use for a property

**Solution:**
- Check similar pages for examples
- Use "Unknown" or "TBD" temporarily
- Add `TODO` comment: `# TODO: Determine correct value`
- Ask in discussion or issue

### Issue 3: Circular Dependencies

**Problem:** Properties create circular references (A → B → A)

**Solution:**
- Use `related-concepts::` for conceptual relationships
- Use `composes-with::` only for composition patterns
- Break cycles by removing one direction
- Document relationship in content instead

### Issue 4: Category Unclear

**Problem:** Primitive fits multiple categories

**Solution:**
- Choose **primary** category (where most related primitives are)
- Use `tags::` for secondary categorizations
- Example: `CachePrimitive` → `performance` (primary) + `#optimization` tag

---

## 🤖 Semi-Automated Migration

### Using Scripts (Future)

A migration script is planned:

```bash
python scripts/migrate_logseq_page.py \
  --page "CachePrimitive" \
  --type "[P] Primitive" \
  --namespace "TTA.dev/Primitives/Performance" \
  --dry-run
```

### Manual Migration Template

```markdown
# Migration Template

1. **Original Page:** `{OldName}`
2. **New Page Name:** `TTA.dev/{Category}/{Name}`
3. **Primitive Type:** [C] | [P] | [D] | [I] | [S]
4. **Status:** stable | beta | experimental | deprecated
5. **Context Level:** 1-Strategic | 2-Operational | 3-Technical

## Properties to Add:
- [ ] type
- [ ] status
- [ ] tags
- [ ] context-level
- [ ] [type-specific properties]

## Links to Update:
- [ ] Property-based links
- [ ] Content-based links
- [ ] Update referring pages

## Content Review:
- [ ] Overview section
- [ ] Examples accurate
- [ ] Related content linked
- [ ] Tags appropriate
```

---

## 📈 Tracking Migration Progress

### Migration Dashboard

Create a Logseq page `TTA.dev/Migration Dashboard`:

```markdown
# Migration Dashboard

## Total Pages: {{query (page-property type)}}

## Migrated Pages: {{query (property migrated true)}}

## Remaining Pages: {{query (not (property type))}}

## By Type:
- [C] CoreConcept: {{query (property type "[[C] CoreConcept")}}
- [P] Primitive: {{query (property type "[[P] Primitive")}}
- [D] DataSchema: {{query (property type "[[D] DataSchema")}}
- [I] Integration: {{query (property type "[[I] Integration")}}
- [S] Service: {{query (property type "[[S] Service")}}

## Next to Migrate:
{{query (and (property priority high) (not (property migrated true)))}}
```

### Weekly Review

Add to weekly TODO review:

```markdown
## Migration Progress Review

- **This week:** [Number] pages migrated
- **Total progress:** [Percentage]% complete
- **Blockers:** [List any issues]
- **Next week target:** [Number] pages
```

---

## 🎓 Best Practices

### DO

✅ **Migrate in batches** - 5-10 pages at a time
✅ **Test queries** after migration
✅ **Update referring pages** when renaming
✅ **Use templates** for consistency
✅ **Document edge cases** in this guide

### DON'T

❌ **Don't rush** - Quality over quantity
❌ **Don't break links** - Verify backlinks work
❌ **Don't skip properties** - Complete schema required
❌ **Don't forget tags** - Aid discovery
❌ **Don't ignore deprecations** - Mark clearly

---

## 📞 Getting Help

**Questions?**
- Check example migrated pages (listed in README)
- Search for similar primitive type
- Ask in GitHub Discussions

**Issues?**
- Report schema violations
- Suggest template improvements
- Request new property types

---

## 🔗 Related Documentation

- **Main System Documentation:** `logseq/KNOWLEDGE_GRAPH_SYSTEM_README.md`
- **Templates:** `logseq/templates.md`
- **Example Pages:** See README for list of 15 reference implementations

---

**Last Updated:** November 11, 2025
**Maintained by:** TTA.dev Team
