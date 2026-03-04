type:: [[Templates]]
description:: Copy-paste patterns for creating TODOs in Logseq

# TODO Templates

Reusable patterns for creating well-structured TODOs in TTA.dev.

## Basic TODO

```markdown
- TODO Task description #dev-todo
```

## TODO with Priority

```markdown
- TODO [#A] High priority task #dev-todo
- TODO [#B] Medium priority task #dev-todo
- TODO [#C] Low priority task #dev-todo
```

## Development Task

```markdown
- TODO Implement feature X #dev-todo
  type:: implementation
  priority:: high
  package:: tta-dev-primitives
  related:: [[TTA.dev/Primitives]]
```

## Bug Fix

```markdown
- TODO Fix bug in RetryPrimitive backoff calculation #dev-todo
  type:: bug
  priority:: high
  package:: tta-dev-primitives
```

## Documentation Task

```markdown
- TODO Add docstring to WorkflowPrimitive.execute #dev-todo
  type:: docs
  priority:: medium
  package:: tta-dev-primitives
```

## Learning Task

```markdown
- TODO Learn about OpenTelemetry tracing #learning-todo
  type:: research
  related:: [[tta-observability-integration]]
```

## Operations Task

```markdown
- TODO Set up GitHub Actions for package publish #ops-todo
  type:: infrastructure
  priority:: medium
```

## Template TODO (Reusable Pattern)

```markdown
- TODO Create template for common workflow pattern #template-todo
  type:: template
  related:: [[TTA.dev/Primitives]]
```

## Tag Reference

| Tag | Use For |
|-----|---------|
| `#dev-todo` | Building TTA.dev |
| `#learning-todo` | Learning and documentation |
| `#ops-todo` | Infrastructure and deployment |
| `#template-todo` | Reusable patterns |

## Related Pages
- [[TODO Management System]] - Active task dashboard
- [[TTA.dev/TODO Architecture]] - System design
