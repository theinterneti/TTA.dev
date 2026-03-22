# TODO Management

Deep reference for the **current** TODO expectations in TTA.dev.

## Two layers of task tracking

### 1. Repository TODO comments

TODOs committed into the repository must use the CI-enforced format:

```markdown
- TODO <description> #dev-todo
  type:: <bug|implementation|refactor|documentation>
  priority:: <critical|high|medium|low>
  package:: <affected-package-name>
```

This is the format validated by:

- `scripts/validate-todos.py`
- the `validate-todos` CI step

### 2. Session task tracking

For active AI-agent work, short-lived task tracking now happens in:

- the session `plan.md`
- the session SQL todo store

That keeps execution state out of the repository while still allowing CI to validate committed TODO
comments.

## Required repository TODO properties

| Property | Required | Values |
|----------|----------|--------|
| `type::` | Yes | `bug`, `implementation`, `refactor`, `documentation` |
| `priority::` | Yes | `critical`, `high`, `medium`, `low` |
| `package::` | Yes | affected package or repo area |

## Notes on legacy Logseq references

Older docs and archived material still mention Logseq-backed TODO workflows. Treat those references
as historical unless a file explicitly documents a maintained Logseq export process.

## Hindsight memory

Cross-agent persistent memory lives in `.hindsight/`. See
[`docs/guides/agents/HINDSIGHT_MEMORY_ARCHITECTURE.md`](../guides/agents/HINDSIGHT_MEMORY_ARCHITECTURE.md)
for the full guide.
