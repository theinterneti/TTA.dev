# Prompt Patterns for Agent Bodies

## Body Structure

Every `.agent.md` body should follow this pattern:

```markdown
# Agent Name

You are a **[Role]** for TTA.dev. [One-line identity.]

## Before You Begin

- [ ] Load context: recall from Hindsight, orient with CGC
- [ ] Review composition: check `.github/copilot-catalog.yml` for your skills/workflows

## Core Responsibilities

1. [Primary task]
2. [Secondary task]
3. [Tertiary task]

## Approach

[How this agent thinks and works]

## Constraints

- Never [do X]
- Always [do Y]
- Defer to [other agent] for [out-of-scope work]

## Quality Standards

- Run `make watch` during development
- All new code needs 100% test coverage
- Follow TTA.dev primitives — never manual retry/timeout loops
```

## Dynamic Variables

Agents can extract values from user input for parameterized behavior.

### Declaration

```markdown
## Dynamic Parameters

- **projectName**: Name of the project (required)
- **basePath**: Root directory (default: current workspace)
- **mode**: Processing depth — quick/standard/detailed (default: standard)
```

### Extraction Priority

1. **Explicit** — user mentions it directly in prompt
2. **File context** — infer from current file/workspace
3. **Settings** — read from config files
4. **Ask** — prompt user for missing required values

### Passing to Sub-Agents

Pass paths and identifiers, never full file contents:

```text
This phase must be performed as the agent "testing-specialist".

IMPORTANT:
- Project: "${projectName}"
- Base path: "${basePath}"
- Focus: unit tests for new code only

Task:
1. Find untested code under "${basePath}/src/"
2. Write tests under "${basePath}/tests/"
3. Return summary: files created, coverage delta, issues found
```

### Variable Best Practices

- Use `camelCase` for variable names
- Document required vs optional with defaults
- Validate constraints (types, allowed values, patterns)
- Derive computed variables from base ones (e.g., `outputDir = ${basePath}/output`)

## Prompt Writing Tips

| Do | Don't |
|----|-------|
| Use imperative mood ("Analyze", "Generate") | Use vague terms ("maybe consider") |
| Define clear scope limits | Leave boundaries open-ended |
| Reference TTA.dev conventions explicitly | Assume the agent knows project standards |
| Keep sections scannable with bullets/tables | Write long prose paragraphs |
| Include quality gates ("Run `make test`") | Skip verification steps |
