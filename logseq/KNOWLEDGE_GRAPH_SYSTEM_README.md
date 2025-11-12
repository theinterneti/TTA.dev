# TTA.dev Logseq Knowledge Graph System

**A comprehensive, graph-native knowledge management system for the TTA.dev framework**

**Last Updated:** November 11, 2025
**Version:** 2.0
**Status:** Production-Ready

---

## 🎯 Overview

This document describes the complete knowledge management system for TTA.dev, implemented natively in Logseq. The system provides a structured taxonomy, property schema, and linking strategy that creates a "living developer's manual" for the framework.

### Key Benefits

- ✅ **Discoverable** - Graph-based navigation via backlinks and queries
- ✅ **Type-Safe** - Property schema enforces consistency
- ✅ **Hierarchical** - Namespace-based organization mirrors architecture
- ✅ **Observable** - Track relationships, dependencies, and usage
- ✅ **Extensible** - Easy to add new primitives and concepts

### What This System Covers

- Framework primitives (WorkflowPrimitive, SequentialPrimitive, etc.)
- Core architectural concepts (Composition, Observability, etc.)
- Data schemas (WorkflowContext, configuration models)
- Integrations (E2B, MCP, LLM providers)
- Services and infrastructure (FastAPI, Redis, Neo4j)

---

## 📐 Framework Primitive Taxonomy

The TTA.dev framework is composed of five fundamental primitive types. This taxonomy is **framework-focused** (not application-focused) and describes the building blocks of TTA.dev itself.

### Primitive Type Definitions

| Type | Symbol | Definition | Examples |
|------|--------|------------|----------|
| **CoreConcept** | `[C]` | Architectural principle or design pattern | Composition, Observability, Type Safety |
| **Primitive** | `[P]` | Executable workflow component | SequentialPrimitive, CachePrimitive, RetryPrimitive |
| **DataSchema** | `[D]` | Data structure or model class | WorkflowContext, OrchestratorConfig, SLOConfig |
| **Integration** | `[I]` | External service or tool integration | E2BPrimitive, MCPCodeExecution, AnthropicPrimitive |
| **Service** | `[S]` | Infrastructure or runtime component | ObservabilityStack, FastAPIServer, RedisCache |

### Taxonomy Rationale

**Why these five types?**

1. **[C] CoreConcept** - Captures the "why" and design philosophy
2. **[P] Primitive** - The actual code users compose in workflows
3. **[D] DataSchema** - Type definitions that flow through primitives
4. **[I] Integration** - Connections to external ecosystems
5. **[S] Service** - Runtime infrastructure supporting primitives

This taxonomy is **mutually exclusive** (each page has exactly one type) and **collectively exhaustive** (all framework components fit into one category).

---

## 🏷️ Logseq Property Schema

Every primitive page in Logseq embeds properties that capture metadata, relationships, and context.

### Universal Properties (All Primitive Types)

These properties appear on **every** primitive page:

```markdown
type:: [C] CoreConcept | [P] Primitive | [D] DataSchema | [I] Integration | [S] Service
status:: stable | beta | experimental | deprecated
tags:: (Comma-separated, e.g., #workflow, #recovery, #observability)
context-level:: 1-Strategic | 2-Operational | 3-Technical
created-date:: [[YYYY-MM-DD]]
last-updated:: [[YYYY-MM-DD]]
```

**Property Definitions:**

- `type::` - One of the five taxonomy types (required)
- `status::` - Maturity/stability indicator (required)
- `tags::` - Free-form tags for filtering/discovery (optional but recommended)
- `context-level::` - Conceptual "altitude" (1=Why, 2=What, 3=How) (required)
- `created-date::` - Page creation date (optional)
- `last-updated::` - Last modification date (optional)

### Type-Specific Properties

Each primitive type has additional properties specific to its role:

#### [C] CoreConcept Properties

```markdown
summary:: (One-sentence definition)
implemented-by:: (Links to [P] Primitives or [S] Services)
related-concepts:: (Links to other [C] CoreConcepts)
documentation:: (Link to guide/doc file)
examples:: (Links to example files or pages)
```

#### [P] Primitive Properties

```markdown
import-path:: (Python import statement)
source-file:: (Path to source code)
category:: core | recovery | performance | orchestration | testing | observability
input-type:: (TypeScript-style type annotation)
output-type:: (TypeScript-style type annotation)
composes-with:: (Links to other [P] Primitives it commonly pairs with)
uses-data:: (Links to [D] DataSchemas)
observability-spans:: (Span names created by primitive)
test-coverage:: (Percentage, e.g., 100%)
example-files:: (Links to example Python files)
```

#### [D] DataSchema Properties

```markdown
source-file:: (Path to source code)
base-class:: (Pydantic BaseModel, TypedDict, etc.)
used-by:: (Links to [P] Primitives that consume this schema)
fields:: (Key field names, comma-separated)
validation:: (Pydantic validators, constraints)
```

#### [I] Integration Properties

```markdown
integration-type:: mcp | llm | database | code-execution | tool
external-service:: (Name of external service, e.g., E2B, Anthropic)
wraps-primitive:: (Link to [P] Primitive if it's a wrapper)
requires-config:: (Links to [D] configuration schemas)
api-endpoint:: (URL/connection string if applicable)
dependencies:: (Python packages required)
```

#### [S] Service Properties

```markdown
service-type:: infrastructure | observability | api | database | cache
deployment:: docker | systemd | cloud | embedded
exposes:: (Links to APIs, endpoints, or [P] Primitives)
depends-on:: (Links to other [S] Services)
configuration:: (Links to [D] config schemas)
monitoring:: (Links to observability pages)
```

---

## 🗂️ Hierarchical Organization Strategy

We use Logseq's **namespace feature** (forward slashes in page titles) to create a clear, directory-like hierarchy.

### Core Namespace Structure

```
TTA.dev/
├── Concepts/
│   ├── Composition
│   ├── Observability
│   ├── TypeSafety
│   └── ErrorRecovery
├── Primitives/
│   ├── Core/
│   │   ├── WorkflowPrimitive
│   │   ├── SequentialPrimitive
│   │   ├── ParallelPrimitive
│   │   └── ConditionalPrimitive
│   ├── Recovery/
│   │   ├── RetryPrimitive
│   │   ├── FallbackPrimitive
│   │   ├── TimeoutPrimitive
│   │   └── CompensationPrimitive
│   ├── Performance/
│   │   ├── CachePrimitive
│   │   └── MemoryPrimitive
│   ├── Orchestration/
│   │   ├── DelegationPrimitive
│   │   └── MultiModelWorkflow
│   └── Testing/
│       └── MockPrimitive
├── Data/
│   ├── WorkflowContext
│   ├── OrchestratorConfig
│   ├── SLOConfig
│   └── RetryConfig
├── Integrations/
│   ├── E2B/
│   │   └── CodeExecutionPrimitive
│   ├── MCP/
│   │   └── MCPCodeExecution
│   └── LLM/
│       ├── AnthropicPrimitive
│       ├── OpenAIPrimitive
│       └── OllamaPrimitive
└── Services/
    ├── ObservabilityStack
    ├── FastAPIServer
    └── RedisCache
```

### Namespace Naming Conventions

**Pattern:** `TTA.dev/Category/Subcategory/ItemName`

**Examples:**
- `TTA.dev/Concepts/Composition` - Core concept
- `TTA.dev/Primitives/Recovery/RetryPrimitive` - Recovery primitive
- `TTA.dev/Data/WorkflowContext` - Data schema
- `TTA.dev/Integrations/LLM/AnthropicPrimitive` - LLM integration

### Why Namespaces Matter

- **Discovery** - Navigate via Logseq's namespace browser
- **Organization** - Mirrors code structure for intuitive mapping
- **Scoping** - Clear separation of concerns
- **Querying** - Easy to query all pages in a namespace

---

## 🔗 Linking Strategy

Links are the "edges" in our knowledge graph. We use two types of links:

### 1. Property-Based Links (Structured Relationships)

These appear in the YAML-like front matter and define **formal relationships**:

```markdown
# Example: TTA.dev/Primitives/Recovery/RetryPrimitive

type:: [P] Primitive
category:: recovery
composes-with:: [[TTA.dev/Primitives/Performance/CachePrimitive]]
uses-data:: [[TTA.dev/Data/WorkflowContext]]
implemented-by:: [[TTA.dev/Concepts/ErrorRecovery]]
```

**Why property-based links?**
- **Queryable** - Logseq queries can filter by property links
- **Typed** - Each property has semantic meaning
- **Bidirectional** - Backlinks show reverse relationships

### 2. Content-Based Links (Contextual Mentions)

These appear in the **body content** of the page and provide **contextual connections**:

```markdown
### Usage

When building fault-tolerant workflows, combine [[TTA.dev/Primitives/Recovery/RetryPrimitive]]
with [[TTA.dev/Primitives/Performance/CachePrimitive]] to avoid retrying expensive operations
that have already been cached.

The primitive accepts a [[TTA.dev/Data/WorkflowContext]] which propagates trace IDs for
[[TTA.dev/Concepts/Observability]].
```

**Why content-based links?**
- **Context** - Explains *why* components are related
- **Navigation** - Natural reading flow to related concepts
- **Discovery** - Backlinks surface unexpected connections

### Linking Best Practices

✅ **DO:**
- Link every mention of a primitive, concept, or data schema
- Use full namespace paths for clarity
- Add links in both properties AND content
- Keep link text concise and readable

❌ **DON'T:**
- Over-link common words (e.g., "workflow" when not referring to the specific primitive)
- Create circular dependencies in properties
- Link to pages that don't exist (create stub pages first)
- Use abbreviations or shorthand in link text

---

## 📋 Template System

Templates accelerate creating new primitive pages with correct structure and properties.

### Template File Location

All templates are defined in: **`logseq/templates.md`**

### Available Templates

1. **`TTA.dev Framework Primitive (Core Concept)`** - For [C] CoreConcept pages
2. **`TTA.dev Framework Primitive (Primitive)`** - For [P] Primitive pages
3. **`TTA.dev Framework Primitive (Data Schema)`** - For [D] DataSchema pages
4. **`TTA.dev Framework Primitive (Integration)`** - For [I] Integration pages
5. **`TTA.dev Framework Primitive (Service)`** - For [S] Service pages

### How to Use Templates

1. **Create new page** - Type `TTA.dev/Category/NewName` in Logseq
2. **Insert template** - Type `/template` and choose appropriate type
3. **Fill in properties** - Replace placeholders with actual values
4. **Add content** - Write description, examples, and links
5. **Commit** - Save and verify links work

---

## 📚 Example Primitive Pages

The following 15 key primitive pages are included as reference implementations:

### Core Concepts ([C])

1. `TTA.dev/Concepts/Composition` - How primitives combine
2. `TTA.dev/Concepts/Observability` - Built-in tracing and metrics
3. `TTA.dev/Concepts/TypeSafety` - Generic type system

### Primitives ([P])

4. `TTA.dev/Primitives/Core/WorkflowPrimitive` - Base class
5. `TTA.dev/Primitives/Core/SequentialPrimitive` - Sequential composition
6. `TTA.dev/Primitives/Core/ParallelPrimitive` - Parallel execution
7. `TTA.dev/Primitives/Recovery/RetryPrimitive` - Retry with backoff
8. `TTA.dev/Primitives/Recovery/FallbackPrimitive` - Graceful degradation
9. `TTA.dev/Primitives/Performance/CachePrimitive` - LRU caching
10. `TTA.dev/Primitives/Testing/MockPrimitive` - Testing utility

### Data Schemas ([D])

11. `TTA.dev/Data/WorkflowContext` - Execution context
12. `TTA.dev/Data/OrchestratorConfig` - Orchestration configuration

### Integrations ([I])

13. `TTA.dev/Integrations/E2B/CodeExecutionPrimitive` - E2B code execution
14. `TTA.dev/Integrations/LLM/AnthropicPrimitive` - Anthropic Claude

### Services ([S])

15. `TTA.dev/Services/ObservabilityStack` - Prometheus + Jaeger

---

## 🚀 Usage Guide

### Adding a New Primitive

**Scenario:** You've created a new primitive called `ValidationPrimitive` in the recovery category.

**Steps:**

1. **Create page:** `TTA.dev/Primitives/Recovery/ValidationPrimitive`
2. **Insert template:** Use "TTA.dev Framework Primitive (Primitive)"
3. **Fill properties:**
   ```markdown
   type:: [P] Primitive
   status:: beta
   category:: recovery
   import-path:: from tta_dev_primitives.recovery import ValidationPrimitive
   source-file:: packages/tta-dev-primitives/src/tta_dev_primitives/recovery/validation.py
   composes-with:: [[TTA.dev/Primitives/Recovery/RetryPrimitive]]
   uses-data:: [[TTA.dev/Data/WorkflowContext]]
   ```
4. **Write content:**
   ```markdown
   ## Overview

   ValidationPrimitive ensures data meets constraints before processing.
   Commonly used with [[TTA.dev/Primitives/Recovery/RetryPrimitive]] to avoid
   retrying invalid data.
   ```
5. **Add examples:** Link to example files or embed code
6. **Create backlinks:** Mention in related primitive pages

### Finding Related Primitives

Use Logseq queries to discover relationships:

```clojure
;; Find all primitives in recovery category
{{query (and [[Primitive]] (property category recovery))}}

;; Find primitives that use WorkflowContext
{{query (property uses-data [[TTA.dev/Data/WorkflowContext]])}}

;; Find stable primitives for production
{{query (and [[Primitive]] (property status stable))}}
```

### Exploring the Graph

1. **Namespace browser** - View hierarchical structure
2. **Graph view** - See visual connections between pages
3. **Backlinks** - Click to see what references a page
4. **Queries** - Create custom filtered views

---

## 🔍 Advanced Queries

### Find High-Level Concepts

```clojure
{{query (and (property type "[[C] CoreConcept") (property context-level "1-Strategic"))}}
```

### Find Production-Ready Primitives

```clojure
{{query (and (property type "[[P] Primitive") (property status stable) (property test-coverage "100%"))}}
```

### Find All LLM Integrations

```clojure
{{query (and (property type "[[I] Integration") (property integration-type llm))}}
```

### Find Primitives by Category

```clojure
{{query (and [[Primitive]] (property category performance))}}
```

### Find Dependencies

```clojure
{{query (property depends-on [[TTA.dev/Services/RedisCache]])}}
```

---

## 📊 Property Reference Table

### Quick Lookup

| Property | Applies To | Type | Required | Example |
|----------|-----------|------|----------|---------|
| `type` | All | Enum | Yes | `[P] Primitive` |
| `status` | All | Enum | Yes | `stable` |
| `tags` | All | List | No | `#workflow, #async` |
| `context-level` | All | Enum | Yes | `3-Technical` |
| `import-path` | [P] | String | Yes | `from tta_dev_primitives...` |
| `source-file` | [P], [D] | Path | Yes | `packages/.../base.py` |
| `category` | [P] | Enum | Yes | `recovery` |
| `composes-with` | [P] | Links | No | `[[OtherPrimitive]]` |
| `uses-data` | [P], [I] | Links | No | `[[DataSchema]]` |
| `implemented-by` | [C] | Links | No | `[[Primitive]]` |
| `integration-type` | [I] | Enum | Yes | `llm` |
| `service-type` | [S] | Enum | Yes | `infrastructure` |

---

## 🛠️ Maintenance Guide

### Regular Tasks

**Weekly:**
- Review new primitive pages for schema compliance
- Update `last-updated` properties on modified pages
- Run link validator to find broken references
- Check for orphaned pages (no incoming links)

**Monthly:**
- Review deprecated primitives for removal
- Update status from `beta` → `stable` as appropriate
- Consolidate duplicate or redundant pages
- Update namespace structure if architecture changes

**Quarterly:**
- Full schema audit across all pages
- Update this README with new patterns
- Review and refine taxonomy if needed
- Export knowledge graph statistics

### Tools for Maintenance

- **Link validator:** Check for broken `[[links]]`
- **Property validator:** Ensure required properties exist
- **Query dashboard:** Monitor page distribution by type
- **Orphan finder:** Identify unlinked pages

---

## 📈 Success Metrics

Track the effectiveness of the knowledge graph:

### Coverage Metrics

- **Primitive Coverage:** % of code primitives documented in Logseq
- **Link Density:** Avg links per page (target: 5-10)
- **Property Completeness:** % of pages with all required properties
- **Namespace Organization:** % of pages using proper namespaces

### Usage Metrics

- **Query Usage:** Track commonly used queries
- **Page Views:** Most-accessed primitive pages
- **Backlink Analysis:** Pages with most incoming links
- **Search Terms:** Common search patterns

### Quality Metrics

- **Broken Links:** Should be 0
- **Orphaned Pages:** Minimize to <5%
- **Outdated Pages:** last-updated > 90 days
- **Status Distribution:** Stable vs beta vs experimental

---

## 🎓 Learning Resources

### For New Users

1. Start with `TTA.dev/Concepts/*` pages (Strategic level)
2. Explore `TTA.dev/Primitives/Core/*` (Foundation)
3. Review example primitive pages for patterns
4. Use templates when creating first pages

### For Developers

1. Understand the taxonomy (5 types)
2. Master property schema for your primitive type
3. Learn namespace conventions
4. Practice linking strategies

### For Architects

1. Review the complete namespace structure
2. Understand context-level stratification
3. Use queries to analyze architecture
4. Contribute to taxonomy evolution

---

## 🔄 Migration from Old System

If you have existing Logseq pages that don't follow this schema:

### Migration Checklist

- [ ] Add `type::` property to every page
- [ ] Add `status::` property
- [ ] Add `context-level::` property
- [ ] Rename pages to use `TTA.dev/*` namespaces
- [ ] Convert inline mentions to `[[links]]`
- [ ] Add type-specific properties
- [ ] Update template usage
- [ ] Validate links

### Migration Script (Future)

A Python script to automate migration is planned:

```bash
python scripts/migrate_logseq_knowledge_graph.py \
  --input logseq/pages/ \
  --output logseq/pages_migrated/ \
  --validate
```

---

## 📝 Contributing

### Adding New Primitive Types

If you need a new taxonomy type (beyond the 5 defined):

1. **Justify:** Why existing types don't fit
2. **Define:** Properties, examples, use cases
3. **Template:** Create template in `logseq/templates.md`
4. **Document:** Update this README
5. **Migrate:** Update existing pages if needed

### Improving the Schema

Submit improvements via:

1. **Discussion:** Open issue to discuss changes
2. **Proposal:** Document new properties or conventions
3. **Prototype:** Test on 2-3 pages
4. **Review:** Get feedback from team
5. **Rollout:** Update templates and documentation

---

## 🔗 Related Documentation

- **Logseq Templates:** `logseq/templates.md`
- **TTA.dev Architecture:** `docs/architecture/`
- **Primitives Catalog:** `PRIMITIVES_CATALOG.md`
- **Agent Instructions:** `AGENTS.md`
- **TODO System:** `logseq/pages/TODO Management System.md`

---

## 📞 Support

**Questions?** Open an issue or discussion on GitHub.

**Bugs?** Report schema violations or broken links as issues.

**Improvements?** Submit PRs with new templates or examples.

---

**Version History:**

- **v2.0** (2025-11-11) - Complete taxonomy redesign with 5 types
- **v1.0** (2025-10-31) - Initial knowledge graph system

**Maintained by:** TTA.dev Team
**License:** MIT
