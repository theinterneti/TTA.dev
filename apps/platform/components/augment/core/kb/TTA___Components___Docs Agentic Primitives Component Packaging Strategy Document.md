---
title: TTA Component Packaging Strategy
tags: #TTA
status: Active
repo: theinterneti/TTA
path: docs/agentic-primitives/COMPONENT_PACKAGING_STRATEGY.md
created: 2025-11-01
updated: 2025-11-01
---
# [[TTA/Components/TTA Component Packaging Strategy]]

**Date:** 2025-10-26
**Status:** Recommendations based on dependency analysis
**Goal:** Extract reusable components into independent packages

---

## Executive Summary

Based on dependency analysis of the TTA codebase, I recommend packaging **2-3 additional components immediately** and planning for 2-3 more over the next month. This will improve modularity, reusability, and maintainability.

**Current Status:** 4 packages exist
**Recommendation:** Add 4-5 more packages over 4 weeks
**Target:** 8-9 total packages + main application

---

## Analysis Results

### Components by Size and Dependencies

| Component | Files | Complexity | External Deps | Recommendation |
|-----------|-------|------------|---------------|----------------|
| agent_orchestration | 120 | 440 | 1 | ⚠️ Overlap with tta-ai-framework |
| components | 84 | 288 | 2 | ✅ Package (split into 3) |
| player_experience | 80 | 543 | 2 | ✅ Package |
| monitoring | 7 | 36 | 0 | ✅ Package immediately |
| orchestration | 6 | 12 | 1 | ❌ Keep in monorepo |
| ai_components | 3 | 7 | 0 | ❌ Keep in monorepo |
| analytics | 3 | 43 | 0 | 📦 Merge into monitoring |
| common | 3 | 15 | 0 | ✅ Package immediately |

---

## Immediate Priorities (Next 2 Weeks)

### 🟢 Priority 1: `tta-common` Package

**Why:** Foundation for all other packages, zero dependencies

**Contents:**
```
packages/tta-common/
├── src/tta_common/
│   ├── utils/          # General utilities
│   ├── types/          # Common type definitions
│   ├── exceptions/     # Shared exceptions
│   └── constants/      # Project constants
└── tests/
```

**Benefits:**
- Single source of truth for shared code
- Other packages can depend on it
- Reduces duplication
- Clear dependency hierarchy

**Effort:** 1-2 days

---

### 🟢 Priority 2: `tta-monitoring` Package

**Why:** Zero dependencies, high reusability

**Contents:**
```
packages/tta-monitoring/
├── src/tta_monitoring/
│   ├── metrics/        # Prometheus metrics collection
│   ├── observability/  # Tracing and logging
│   ├── analytics/      # Query builder, data analysis
│   ├── health/         # Health checks
│   └── dashboards/     # Grafana dashboard configs
└── tests/
```

**Benefits:**
- Reusable across all TTA projects
- Can be used in other applications
- Clean separation from business logic
- Independent evolution

**Effort:** 2-3 days

**Source:** Merge `src/monitoring` + `src/analytics`

---

## Medium Priority (Weeks 3-4)

### 🟡 Priority 3: `tta-player-experience` Package

**Why:** Large, well-defined domain with clear boundaries

**Contents:**
```
packages/tta-player-experience/
├── src/tta_player_experience/
│   ├── api/            # Player API endpoints
│   ├── managers/       # Session, progress, state
│   ├── services/       # Player-specific services
│   ├── models/         # Player data models
│   ├── database/       # Player data persistence
│   └── frontend/       # Player UI components (if applicable)
└── tests/
```

**Dependencies:** `tta-common`, `tta-monitoring`

**Benefits:**
- Clear domain boundary
- Independent development and testing
- Version player features separately
- Can reuse in multiple TTA variants

**Effort:** 3-5 days

**Note:** Wait until `tta-common` and `tta-monitoring` exist first

---

### 🟡 Priority 4: Component Libraries (Split into 3 packages)

**Why:** Large, reusable game mechanics

#### 4a. `tta-gameplay-components`
```
packages/tta-gameplay-components/
└── src/tta_gameplay/
    ├── gameplay_loop/
    ├── adventure_experience/
    └── living_worlds/
```

#### 4b. `tta-narrative-components`
```
packages/tta-narrative-components/
└── src/tta_narrative/
    ├── arc_orchestrator/
    ├── coherence_validator/
    └── story_elements/
```

#### 4c. `tta-therapeutic-components`
```
packages/tta-therapeutic-components/
└── src/tta_therapeutic/
    ├── scoring/
    ├── safety/
    └── interventions/
```

**Dependencies:** `tta-common`, `tta-ai-framework`, `tta-narrative-engine`

**Effort:** 5-7 days total

---

## Special Case: `agent_orchestration`

### ⚠️ Analysis Needed

**Issue:** Significant overlap with existing `tta-ai-framework` package

**Recommendation:**
1. **Audit** both packages for duplicate code
2. **Merge** overlapping functionality into `tta-ai-framework`
3. **Move** unique orchestration code to `tta-ai-framework`
4. **Keep** application-specific orchestration in main app
5. **Delete** or consolidate remaining code

**Questions to Answer:**
- What's in `agent_orchestration` that's not in `tta-ai-framework`?
- What's application-specific vs. reusable?
- Can we consolidate into a single agent package?

**Effort:** 3-5 days for audit + migration

---

## Components to Keep in Monorepo

These should **NOT** be packaged:

### ❌ `api_gateway` (1 file, 17 defs)
- Application-specific routing
- Too coupled to app structure
- No reusability outside TTA

### ❌ `orchestration` (6 files, 12 defs)
- Application orchestration logic
- Already have `tta-workflow-primitives`
- App-specific coordination

### ❌ `ai_components` (3 files, 7 defs)
- Small, application-specific
- Prompts are app-dependent
- Not reusable

### ❌ `developer_dashboard` (2 files, 11 defs)
- Development tooling only
- Not part of runtime system

### ❌ `living_worlds` (1 file, 3 defs)
- Too small (can merge into gameplay components later)
- Still evolving

### ❌ `integration` (2 files, 1 def)
- Integration layer code
- Application-specific

---

## Implementation Roadmap

### Week 1: Foundation
- [x] `dev-primitives` ✅ (DONE)
- [x] `tta-workflow-primitives` ✅ (DONE)
- [ ] `tta-common` 🔄
- [ ] `tta-monitoring` 🔄

### Week 2: Audit
- [ ] Audit `agent_orchestration` vs `tta-ai-framework`
- [ ] Merge duplicate code
- [ ] Document differences

### Week 3-4: Domain Packages
- [ ] `tta-player-experience`
- [ ] Split `tta-components` into 3 packages

### Week 5+: Polish
- [ ] Documentation for all packages
- [ ] Examples and migration guides
- [ ] CI/CD for independent testing
- [ ] Version 1.0 releases

---

## Package Dependency Graph

```
┌─────────────────┐
│   tta-common    │  ← Foundation (no deps)
└────────┬────────┘
         │
    ┌────┴────┬────────────┬─────────────┐
    ▼         ▼            ▼             ▼
┌────────┐ ┌────────┐ ┌──────────┐ ┌──────────┐
│monitor │ │workflow│ │ ai-frame │ │narrative │
│  ing   │ │ prims  │ │   work   │ │  engine  │
└────────┘ └────────┘ └─────┬────┘ └────┬─────┘
                            │            │
         ┌──────────────────┴───┬────────┴─────┬──────────┐
         ▼                      ▼              ▼          ▼
    ┌────────┐          ┌──────────┐    ┌──────────┐ ┌──────┐
    │ player │          │ gameplay │    │narrative │ │therap│
    │  exp   │          │  comps   │    │  comps   │ │comps │
    └────────┘          └──────────┘    └──────────┘ └──────┘
         │                     │              │          │
         └─────────────────────┴──────────────┴──────────┘
                               ▼
                        ┌──────────────┐
                        │   Main TTA   │
                        │ Application  │
                        └──────────────┘
```

---

## Benefits by Package

### `tta-common`
✅ Single source of truth
✅ Clear dependency direction
✅ Reduces duplication
✅ Easy versioning

### `tta-monitoring`
✅ Reusable infrastructure
✅ Independent testing
✅ Can use in other projects
✅ Clean separation

### `tta-player-experience`
✅ Clear domain boundary
✅ Independent development
✅ Version separately
✅ Reuse across TTA variants

### Component packages
✅ Reusable game mechanics
✅ Share across projects
✅ Clear versioning
✅ Modular updates

---

## Anti-Patterns to Avoid

### ❌ Premature Packaging
- Don't package small components (< 10 files)
- Don't package evolving code
- Don't package tightly coupled code

### ❌ Circular Dependencies
- Always maintain acyclic dependency graph
- Foundation packages have zero deps
- Application depends on packages, not reverse

### ❌ Over-Packaging
- Aim for 8-10 packages maximum
- Too many = maintenance burden
- Keep related code together

---

## Success Metrics

### After Foundation (Week 1)
- ✅ 6 total packages
- ✅ Clear dependency graph
- ✅ < 5% code duplication
- ✅ All packages independently testable

### After Audit (Week 2)
- ✅ Agent orchestration consolidated
- ✅ No duplicate code
- ✅ Clear responsibility boundaries

### After Domain Packages (Week 4)
- ✅ 9-10 total packages
- ✅ Main app < 40% of codebase
- ✅ Each package has CI/CD
- ✅ Documentation complete

---

## Migration Strategy

### For Each New Package:

1. **Create package structure**
   ```bash
   mkdir -p packages/tta-<name>/src/tta_<name>
   mkdir -p packages/tta-<name>/tests
   ```

2. **Copy code from src/**
   ```bash
   cp -r src/<component>/* packages/tta-<name>/src/tta_<name>/
   ```

3. **Update imports**
   - Change `from src.<component>` to `from tta_<name>`
   - Update all dependent code

4. **Add pyproject.toml**
   - Define dependencies
   - Set version
   - Configure build system

5. **Write tests**
   - Unit tests for all modules
   - Integration tests if needed

6. **Install as editable**
   ```bash
   uv pip install -e packages/tta-<name>
   ```

7. **Update main app**
   - Change imports to use package
   - Remove code from src/
   - Test thoroughly

8. **Document**
   - README.md
   - API documentation
   - Migration guide

---

## Next Steps

### Immediate (This Week)
1. ✅ Review this document with team
2. 🔄 Create `tta-common` package
3. 🔄 Create `tta-monitoring` package
4. 🔄 Update main app to use new packages

### Next Week
1. 🔄 Audit `agent_orchestration` vs `tta-ai-framework`
2. 🔄 Create consolidation plan
3. 🔄 Begin migration

### Following Weeks
1. 🔄 Extract `tta-player-experience`
2. 🔄 Split component packages
3. 🔄 Complete documentation
4. 🔄 Release version 1.0 of all packages

---

## Conclusion

Packaging the right components will significantly improve TTA's:
- **Modularity** - Clear boundaries between concerns
- **Reusability** - Share code across projects
- **Maintainability** - Independent versioning and updates
- **Testability** - Isolated testing of components

**Start with `tta-common` and `tta-monitoring`** - they're foundational, have no dependencies, and will unblock further packaging efforts.


---
**Logseq:** [[TTA.dev/Platform_tta_dev/Components/Augment/Core/Kb/Tta___components___docs agentic primitives component packaging strategy document]]
