# TODO Management

Deep reference for the Logseq-based TODO management system in TTA.dev.

## Location

All TODOs go in Logseq daily journals: `logseq/journals/YYYY_MM_DD.md`

## Format

```markdown
- TODO <description> #<tag>
  type:: <bug|implementation|refactor|documentation>
  priority:: <critical|high|medium|low>
  package:: <affected-package-name>
  related:: [[Related Page]]
```

**Status must be UPPERCASE:** `TODO`, `DOING`, `DONE`

## Tags

| Tag | Purpose |
|-----|---------|
| `#dev-todo` | Development work (building TTA.dev itself) |
| `#learning-todo` | User education (tutorials, flashcards, exercises) |
| `#template-todo` | Reusable patterns (for agents/users) |
| `#ops-todo` | Infrastructure (deployment, monitoring) |

## Required Properties

| Property | Required | Values |
|----------|----------|--------|
| `type::` | Yes | `bug`, `implementation`, `refactor`, `documentation` |
| `priority::` | Yes | `critical`, `high`, `medium`, `low` |
| `package::` | When applicable | Package name (e.g., `tta-dev-primitives`) |
| `related::` | Optional | Logseq page link |

## Validation

CI enforces 100% compliance via:
- **Validator script:** `scripts/validate-todos.py`
- **CI workflow:** `.github/workflows/validate-todos.yml`

The validator checks that all TODOs have required tags and properties.

## Package Dashboards

- [`TTA.dev/Packages/tta-dev-primitives/TODOs`](../../logseq/pages/TTA.dev___Packages___tta-dev-primitives___TODOs.md)
- [`TTA.dev/Packages/tta-observability-integration/TODOs`](../../logseq/pages/TTA.dev___Packages___tta-observability-integration___TODOs.md)
- [`TTA.dev/Packages/universal-agent-context/TODOs`](../../logseq/pages/TTA.dev___Packages___universal-agent-context___TODOs.md)

## Knowledge Base Structure

```
logseq/
├── pages/
│   ├── TTA Primitives/       # Primitive documentation
│   ├── Learning/             # Flashcards and exercises
│   └── Architecture/         # Design decisions
└── journals/                 # Daily notes with TODOs
```

## Hindsight Memory

Cross-agent persistent memory lives in `.hindsight/`. See [`docs/guides/agents/HINDSIGHT_MEMORY_ARCHITECTURE.md`](../guides/agents/HINDSIGHT_MEMORY_ARCHITECTURE.md) for the full guide.
