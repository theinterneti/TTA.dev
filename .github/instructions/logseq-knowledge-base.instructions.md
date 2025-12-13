---
applyTo: "logseq/**/*.md"
description: "Logseq knowledge base files"
---

# Logseq Knowledge Base Guidelines

## Purpose

Logseq stores learning materials and architecture decisions. For task tracking, use **GitHub Issues**.

## When to Use Logseq

- Architecture decision records
- Learning flashcards
- Primitive documentation
- Design patterns

## When NOT to Use Logseq

- Task tracking → Use GitHub Issues
- Status reports → Use git commits/PRs
- Meeting notes → Use GitHub Discussions

## File Structure

```
logseq/
├── pages/
│   ├── TTA Primitives/       # Primitive documentation
│   ├── Learning/             # Flashcards and exercises
│   └── Architecture/         # Design decisions
└── journals/                 # Daily notes (optional)
```

## Page Format

```markdown
# Topic Name

Brief description.

## Key Concepts

- Concept 1
- Concept 2

## Examples

\`\`\`python
# Working code example
\`\`\`

## Related

- [[Related Page]]
- [[Another Page]]
```

## Flashcard Format

```markdown
## Question #card

What does RetryPrimitive do?

---

Automatically retries failed operations with configurable backoff.
```


---
**Logseq:** [[TTA.dev/.github/Instructions/Logseq-knowledge-base.instructions]]
