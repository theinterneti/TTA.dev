# KB Broken Links Fix Strategy

## Summary

**Total broken links:** 1,063 real broken links (1,900 total minus 837 false positives)

**False Positives (filtered out):**
- Tags: 204 links (`#dev-todo`, etc.)
- Dates: 247 links (`[[2025-10-30]]`)
- Date placeholders: 65 links (`[[YYYY-MM-DD]]`)
- Inline tags: 230 links (`Beginner`, `Stable`, etc.)
- Generic references: 85 links (`Guide`, `Developers`, etc.)
- External files: 4 links (`file://...`, `http://...`)

## Top 20 Missing Pages (High Impact)

Create these pages first - they have the most incoming references:

1. **TTA Primitives/CachePrimitive** (19 references) → Redirect to TTA.dev/Primitives/CachePrimitive
2. **TTA.dev/Observability** (14 references) → Create namespace/overview page
3. **TTA.dev/Testing** (13 references) → Create namespace/overview page
4. **AI Engineers** (12 references) → Create audience page
5. **Architecture** (11 references) → Disambiguate or redirect to TTA.dev/Architecture
6. **RouterPrimitive** (10 references) → Redirect to TTA.dev/Primitives/RouterPrimitive
7. **Core Primitives** (10 references) → Create category page
8. **Recovery Patterns** (10 references) → Create pattern guide
9. **How-To** (9 references) → Create namespace page
10. **FallbackPrimitive** (8 references) → Redirect to TTA.dev/Primitives/FallbackPrimitive
11. **WorkflowContext** (8 references) → Create core concept page
12. **Core** (8 references) → Disambiguate
13. **CachePrimitive** (8 references) → Redirect to TTA.dev/Primitives/CachePrimitive
14. **RetryPrimitive** (8 references) → Redirect to TTA.dev/Primitives/RetryPrimitive
15. **Multi-Agent Orchestration** (8 references) → Create guide page
16. **DevOps** (7 references) → Create topic page
17. **Performance Optimization** (7 references) → Create guide page
18. **Logseq Knowledge Base** (7 references) → Create meta page
19. **Logseq Features** (7 references) → Create feature overview
20. **Example** (14 references) → Disambiguate or create template

## Fix Strategies

### Strategy 1: Create Redirect Pages (Primitive Namespace Migration)

**Problem:** Links reference `TTA Primitives/CachePrimitive` but page is at `TTA.dev/Primitives/CachePrimitive`

**Solution:** Create redirect pages at old locations:

```markdown
# TTA Primitives/CachePrimitive

> **Note:** This page has moved to [[TTA.dev/Primitives/CachePrimitive]]

**New location:** [[TTA.dev/Primitives/CachePrimitive]]

All documentation and examples are now at the new location.
```

**Impact:** Fixes ~50-60 broken links immediately

**Pages to create:**
- TTA Primitives/CachePrimitive → TTA.dev/Primitives/CachePrimitive
- TTA Primitives/RouterPrimitive → TTA.dev/Primitives/RouterPrimitive
- TTA Primitives/RetryPrimitive → TTA.dev/Primitives/RetryPrimitive
- TTA Primitives/FallbackPrimitive → TTA.dev/Primitives/FallbackPrimitive
- TTA Primitives/TimeoutPrimitive → TTA.dev/Primitives/TimeoutPrimitive
- TTA Primitives/ParallelPrimitive → TTA.dev/Primitives/ParallelPrimitive
- TTA Primitives/SequentialPrimitive → TTA.dev/Primitives/SequentialPrimitive
- TTA Primitives/ConditionalPrimitive → TTA.dev/Primitives/ConditionalPrimitive
- TTA Primitives/CompensationPrimitive → TTA.dev/Primitives/CompensationPrimitive
- TTA Primitives/MockPrimitive → TTA.dev/Primitives/MockPrimitive
- TTA Primitives/WorkflowPrimitive → TTA.dev/Primitives/WorkflowPrimitive

### Strategy 2: Create Namespace/Overview Pages

**Problem:** Links reference namespace pages that don't exist (TTA.dev/Observability, TTA.dev/Testing)

**Solution:** Create namespace overview pages that list and link to all pages in that namespace

Example: `TTA.dev/Observability.md`:
```markdown
# TTA.dev/Observability

Overview of observability features in TTA.dev.

## Pages

- [[TTA.dev/Guides/Observability]]
- [[TTA.dev/Architecture/Observability Implementation]]
- [[TTA.dev/Packages/tta-observability-integration]]

## Related

- [[TTA.dev/Guides/Getting Started]]
- [[TTA.dev/Architecture]]
```

**Impact:** Fixes ~40-50 broken links

**Pages to create:**
- TTA.dev/Observability
- TTA.dev/Testing
- TTA.dev/How-To (namespace overview)

### Strategy 3: Create Audience Pages

**Problem:** Links reference audience pages that don't exist (AI Engineers, Developers, etc.)

**Solution:** Create audience persona pages

Example: `AI Engineers.md`:
```markdown
# AI Engineers

Resources for AI/ML engineers using TTA.dev.

## Learning Paths

- [[TTA.dev/Learning Paths]] - Core Primitives Path
- [[Learning TTA Primitives]]

## Key Concepts

- [[TTA Primitives]]
- [[TTA.dev/Guides/Agentic Primitives]]

## Examples

- [[TTA.dev/Examples/Overview]]
```

**Impact:** Fixes ~20-30 broken links

**Pages to create:**
- AI Engineers
- Developers
- Senior Developers
- Framework Developers
- Library Authors

### Strategy 4: Create Category/Topic Pages

**Problem:** Links reference category pages (Core Primitives, Recovery Patterns, etc.)

**Solution:** Create category index pages

**Impact:** Fixes ~20-30 broken links

**Pages to create:**
- Core Primitives (overview of sequential, parallel, conditional, router)
- Recovery Patterns (overview of retry, fallback, timeout, compensation)
- Performance Optimization (caching, routing strategies)
- Multi-Agent Orchestration

### Strategy 5: Fix or Remove External File References

**Problem:** Links to external files that may or may not exist

**Solution:** 
1. Check if file exists
2. If yes, verify link format
3. If no, remove link or update to correct location

**Impact:** Fixes ~20-30 broken links

**Example broken links:**
- `file:../../REPOSITORY_AUDIT_2025_10_31.md`
- `file:../../docs/architecture/KNOWLEDGE_BASE_INTEGRATION.md`
- `.github/copilot-instructions.md`
- `local/planning/logseq-docs-integration-todos.md`

### Strategy 6: Create Concept/Feature Pages

**Problem:** Links reference concepts without dedicated pages

**Solution:** Create standalone concept explanation pages

**Impact:** Fixes ~20-30 broken links

**Pages to create:**
- WorkflowContext (core concept)
- Logseq Knowledge Base (meta/system page)
- Logseq Features (feature list)
- MCP Servers (integration overview)
- GitHub Actions (CI/CD overview)

## Prioritized Execution Plan

### Phase 1: High-Impact Quick Wins (Fixes ~150 links)

1. Create 11 primitive redirect pages (Strategy 1) - **~50 links**
2. Create 3 namespace pages (Strategy 2) - **~40 links**
3. Create 5 audience pages (Strategy 3) - **~30 links**
4. Create 4 category pages (Strategy 4) - **~30 links**

### Phase 2: Medium-Impact Pages (Fixes ~100 links)

5. Create concept pages (Strategy 6) - **~40 links**
6. Fix/verify external file references (Strategy 5) - **~20 links**
7. Create remaining missing pages from top 20 list - **~40 links**

### Phase 3: Long Tail (Fixes remaining ~813 links)

8. Review pages with 20+ broken links each
9. Bulk fix common patterns
10. Create disambiguation pages where needed
11. Consider if some links should just be removed

## Implementation Notes

### Redirect Page Template

```markdown
# [Old Page Name]

> **Note:** This page has moved to [[New Location]]

**New location:** [[New Location]]

All content is now at the new location. Please update your links.
```

### Namespace Overview Template

```markdown
# [Namespace Name]

Brief description of this namespace.

## Pages in This Namespace

- [[Page 1]]
- [[Page 2]]

## Related Namespaces

- [[Related Namespace]]
```

### Audience Persona Template

```markdown
# [Audience Name]

Resources tailored for [audience description].

## Learning Path

Recommended sequence:
1. [[First Step]]
2. [[Next Step]]

## Key Resources

- [[Resource 1]]
- [[Resource 2]]
```

## Success Metrics

- **Phase 1 target:** Reduce from 1,063 to ~913 broken links (150 fixed, 86% reduction)
- **Phase 2 target:** Reduce from ~913 to ~813 broken links (100 fixed, 89% reduction)
- **Phase 3 target:** Reduce from ~813 to <100 broken links (713 fixed, 91%+ reduction)

## Tools

- **Analysis script:** `scripts/analyze_real_broken_links.py`
- **Validation:** `.github/workflows/kb-validation.yml`
- **Report:** `kb-real-broken-links.txt`

## Notes

- Most broken links are **namespace migrations** (old TTA Primitives/* → new TTA.dev/Primitives/*)
- Creating redirect pages is faster than updating all references
- Namespace pages provide navigation structure
- Some links may need removal rather than fixing (orphaned references)

---

**Generated:** 2025-11-04
**Status:** Ready for implementation
**Estimated Time:** Phase 1 = 2-3 hours, Phase 2 = 2-3 hours, Phase 3 = 4-6 hours
