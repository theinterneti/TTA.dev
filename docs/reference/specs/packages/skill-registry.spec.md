# SkillRegistry Specification

- **Version:** 0.1.0
- **Status:** Draft
- **Package:** tta-skill-primitives
- **Source:** `platform/skills/src/tta_skill_primitives/`

## 1. Purpose

The SkillRegistry provides discovery, registration, and lookup of agent skills in TTA.dev.
Skills are self-describing capabilities that follow the SKILL.md specification and extend
`WorkflowPrimitive` for composability.

## 2. Core Types

### 2.1 SkillDescriptor

```python
class SkillDescriptor(BaseModel):
    name: str                    # Unique skill identifier
    description: str             # Human-readable description
    version: str | None = None   # Semantic version
    tags: list[str] = []         # Discovery tags
    metadata: dict[str, Any] = {} # Additional metadata
```

### 2.2 Skill

```python
class Skill(WorkflowPrimitive[TInput, TOutput]):
    descriptor: SkillDescriptor  # Class-level descriptor
    async def execute(self, input_data: TInput, context: WorkflowContext) -> TOutput: ...
```

### 2.3 SkillRegistry

```python
class SkillRegistry:
    def register(self, skill: Skill) -> None: ...
    def get(self, name: str) -> Skill | None: ...
    def list_skills(self) -> list[SkillDescriptor]: ...
    def search(self, query: str) -> list[SkillDescriptor]: ...
```

## 3. Registration Contract

### 3.1 Behavior Invariants

- `register()` MUST store the skill keyed by `skill.descriptor.name`.
- `register()` MUST overwrite any existing skill with the same name.
- `register()` MUST validate that the skill has a non-empty `descriptor.name`.

### 3.2 Error Contract

| Condition | Exception | Description |
|-----------|-----------|-------------|
| Skill with empty name | `ValueError` | Name MUST be non-empty |
| Duplicate name | *(none)* | Silently overwrites previous registration |

## 4. Lookup Contract

### 4.1 Behavior Invariants

- `get(name)` MUST return the registered `Skill` or `None` if not found.
- `list_skills()` MUST return descriptors for all registered skills.
- `search(query)` MUST perform case-insensitive matching against skill names and descriptions.

## 5. SKILL.md Integration

### 5.1 SKILL.md Format

```yaml
---
name: skill-name
description: What this skill does
version: 1.0.0
tags: [category, subcategory]
parameters:
  - name: param1
    type: string
    required: true
---
```

### 5.2 Parsing Contract

- `parse_skill_md(content: str)` MUST extract YAML frontmatter from SKILL.md content.
- `load_skill_md(path: Path)` MUST read a file and return a `SkillDescriptor`.
- `dump_skill_md(descriptor: SkillDescriptor)` MUST serialize to SKILL.md format.

## 6. Composition Rules

- Skills MUST compose with `>>` and `|` operators (inherited from `WorkflowPrimitive`).
- `SkillA >> SkillB` — sequential skill chaining.
- `SkillA | SkillB` — parallel skill execution.

## 7. Cross-References

- [WorkflowPrimitive Spec](../primitives/workflow-primitive.spec.md) — Base class for Skills
- [Span Schema](../observability/span-schema.spec.md) — Skills emit standard primitive spans
