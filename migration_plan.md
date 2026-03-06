# 3-Tier Instruction Architecture Migration Plan

## Overview

Refactor from ~16,000 lines of overlapping, duplicated instruction files across 6+ agent configs into a strict 3-tier architecture with progressive disclosure.

---

## Current State (Audit Summary)

| File/Directory | Lines | Status | Problem |
|---|---|---|---|
| `AGENTS.md` | 234 | Bloated | Mixes TOC with full code examples, primitives catalog |
| `CLAUDE.md` | 206 | Bloated | Mixes TOC with SDD constitution, build commands, code style |
| `.clinerules` | 397 | Redundant | 95% duplicate of CLAUDE.md + extra code examples |
| `.augment/` (7 files) | 3,433 | Redundant | Duplicated rules across .cursor and .cline |
| `.cursor/` (5 files) | 1,473 | Redundant | Near-identical copy of .augment/rules/ |
| `.cline/` (27 files) | 10,529 | Bloated | Advanced engines, examples, duplicated rules |
| `.universal-instructions/` | 331 | Legacy | Source templates for generating CLAUDE.md |
| `.github/instructions/` (5 files) | 492 | Keep | Path-based instruction system (Copilot) |
| `.github/copilot-instructions.md` | 82 | Keep | Already concise |

**Total duplication:** The SDD Constitution appears in 3 files. Build/test commands appear in 5+ files. Python type-hint rules appear in 6+ files.

---

## Target State (3-Tier Architecture)

### Tier 1: Root Instructions (< 100 lines each)

These files serve as a table of contents pointing to Tier 2 skills and Tier 3 guides.

| File | Purpose | Content |
|---|---|---|
| `AGENTS.md` | Universal agent entry point | What is TTA.dev, repo structure, link to skills & guides |
| `CLAUDE.md` | Claude-specific root | Claude as primary agent, link to SDD skill, link to skills & guides |

**Rules for Tier 1:**
- No build/test commands
- No code style rules
- No code examples
- Only links to Tier 2 and Tier 3

### Tier 2: Agent Skills (`.claude/skills/<name>/SKILL.md`)

Each skill has YAML frontmatter (`name`, `description`) for dynamic loading.

| Skill | Source Content | Lines Target |
|---|---|---|
| `build-test-verify` | Quality gate commands from CLAUDE.md §3, .clinerules §3 | ~60 |
| `git-commit` | Conventional commits from CLAUDE.md, .clinerules | ~40 |
| `create-pull-request` | PR workflow (new, consolidated) | ~50 |
| `core-conventions` | Python standards, uv, type hints from .clinerules, CLAUDE.md | ~80 |
| `self-review-checklist` | Pre-commit checklist from .clinerules code quality section | ~50 |
| `sdd-workflow` | SDD Constitution §1-§4 from CLAUDE.md | ~100 |

### Tier 3: Agent Guides (`docs/agent-guides/`)

Deep reference material. Skills link here for progressive disclosure.

| Guide | Source Content |
|---|---|
| `testing-architecture.md` | Full testing standards from .github/instructions/testing.instructions.md, .clinerules testing section |
| `primitives-patterns.md` | Full primitives catalog, composition operators, recovery/performance patterns from .clinerules, AGENTS.md |
| `python-standards.md` | Full Python style guide from .github/instructions/python.instructions.md, .clinerules |
| `sdd-constitution.md` | Complete SDD Constitution with all tables and examples from CLAUDE.md §1-§4 |
| `observability-guide.md` | OpenTelemetry integration patterns (from .augment/rules/ deep content) |
| `todo-management.md` | Logseq TODO system, tags, properties, validation from .clinerules, AGENTS.md |

---

## Migration Map (What Moves Where)

### From `CLAUDE.md` (206 lines → ~70 lines)

| Section | Current Lines | Destination |
|---|---|---|
| SDD Constitution §1-§4 | 9-112 | Tier 2: `sdd-workflow/SKILL.md` + Tier 3: `sdd-constitution.md` |
| What is TTA.dev + Repo Layout | 115-142 | Stays in Tier 1 (condensed) |
| Non-Negotiable Standards | 144-153 | Tier 2: `core-conventions/SKILL.md` |
| Core Pattern + Anti-patterns | 155-170 | Tier 2: `core-conventions/SKILL.md` → Tier 3: `primitives-patterns.md` |
| Quality Gate commands | 172-179 | Tier 2: `build-test-verify/SKILL.md` |
| TODO Management | 181-184 | Tier 2: `core-conventions/SKILL.md` → Tier 3: `todo-management.md` |
| Multi-Agent Context table | 186-196 | Stays in Tier 1 |
| Key Reference Files | 198-205 | Stays in Tier 1 (updated links) |

### From `AGENTS.md` (234 lines → ~80 lines)

| Section | Current Lines | Destination |
|---|---|---|
| Quick Start / What is TTA.dev | 7-18 | Stays in Tier 1 (condensed) |
| MCP Tool Registry link | 20-23 | Stays in Tier 1 |
| TODO Management (detailed) | 25-51 | Tier 3: `todo-management.md` |
| Hindsight Memory (detailed) | 53-82 | Tier 3: stays as link to existing guide |
| Agent Context & Tooling | 86-115 | Stays in Tier 1 (condensed) |
| Primitives usage rules | 117-119 | Tier 2: `core-conventions/SKILL.md` |
| Repository Structure (full tree) | 121-151 | Tier 3 or condensed in Tier 1 |
| Core Concept: Primitives (code) | 153-172 | Tier 3: `primitives-patterns.md` |
| Available Primitives table | 176-184 | Tier 3: `primitives-patterns.md` |
| Agent Skills (SKILL.md) | 186-214 | Tier 3: `primitives-patterns.md` |
| Anti-Patterns table | 222-229 | Tier 2: `core-conventions/SKILL.md` |

### From `.clinerules` (397 lines → REMOVED)

All content is already duplicated in CLAUDE.md or will be in Tier 2/3. This file will be replaced with a stub pointing to the skills.

### From `.augment/` (3,433 lines → REMOVED)

| Content | Destination |
|---|---|
| `instructions.md` | Replaced by Tier 1 `AGENTS.md` links |
| `rules/*.md` | Consolidated into Tier 2 skills + Tier 3 guides |
| `workflows/*.md` | Archived or consolidated into Tier 2 skills |

### From `.cursor/` (1,473 lines → REMOVED)

Near-identical copy of `.augment/rules/`. Fully replaced by Tier 2 + Tier 3.

### From `.universal-instructions/` (331 lines → REMOVED)

Legacy source templates. Replaced by the new Tier 1 `CLAUDE.md`.

---

## Files to DELETE after migration

| File/Directory | Reason |
|---|---|
| `.clinerules` | Content migrated to Tier 2 skills + Tier 3 guides |
| `.augment/` | Duplicated content migrated to Tier 2 + Tier 3 |
| `.cursor/` | Duplicated content migrated to Tier 2 + Tier 3 |
| `.universal-instructions/` | Legacy template system replaced by Tier 1 |

## Files to KEEP (unchanged)

| File | Reason |
|---|---|
| `.github/instructions/*.md` | Path-based Copilot instruction system (orthogonal to 3-tier) |
| `.github/copilot-instructions.md` | Already concise, Copilot-specific |
| `.cline/` | Cline-specific advanced features (hooks, engines) - update `instructions.md` to point to skills |
| `.gemini/settings.json` | Agent config, not instructions |

---

## Execution Order

1. Create `docs/agent-guides/` directory and Tier 3 guides
2. Create `.claude/skills/` directory structure and Tier 2 skills
3. Rewrite `AGENTS.md` as Tier 1 TOC (< 100 lines)
4. Rewrite `CLAUDE.md` as Tier 1 TOC (< 100 lines)
5. Update `.clinerules` to a stub referencing the new architecture
6. Remove `.augment/`, `.cursor/`, `.universal-instructions/`
