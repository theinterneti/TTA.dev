---
name: Continuous Documentation Agent
on:
  push:
    branches:
      - main
permissions:
  contents: write
  pull-requests: write
tools:
  - github
  - grep
  - view
env:
  AGENT_VERSION: "1.0.0"
---

# Continuous Documentation Agent

> [!WARNING]
> Historical workflow draft, not an active GitHub Actions workflow.
>
> This file captures an older idea for automated documentation maintenance. It is kept as
> context, but parts of the original draft referenced Logseq-first workflows, non-existent
> `tta_documentation_primitives`, and older import paths. For current repo truth, prefer:
> `README.md`, `GETTING_STARTED.md`, `QUICKSTART.md`, `docs/README.md`, and
> `.github/copilot-instructions.md`.

Act as a documentation maintenance agent responsible for keeping the canonical docs synchronized
with code changes.

## Initialization (Run First!)

Before any documentation updates, configure observability:
```bash
# Setup OpenTelemetry environment
eval "$(python scripts/ci/setup_otel.py)"
echo "✅ OTEL configured with trace: $TRACEPARENT"
```

## Trigger Conditions

This workflow runs when:
- Code is pushed to the `main` branch
- Changes affect Python files, workflow files, or existing documentation

## Your Responsibilities

1. **Detect Documentation Drift**
   - Analyze the latest commits to identify code changes
   - Check if public APIs, primitives, or workflows were modified
   - Identify new features, deprecated functions, or changed behavior

2. **Update README.md**
   - Keep installation instructions current
   - Update code examples if APIs changed
   - Add new features to the Quick Start section
   - Update the API Reference for new primitives
   - Ensure all code examples are copy-paste runnable

3. **Update Canonical Documentation First**
   - Treat top-level docs and `docs/README.md` as the source of truth
   - Prefer updating active docs over adding new parallel explanations
   - If a guide is historical, label it clearly instead of quietly leaving it misleading
   - Avoid Logseq-specific maintenance unless the work is explicitly about archived Logseq material

4. **Verify Examples Against Current Imports**
   - Use the current `ttadev.primitives` namespace in active examples
   - Confirm commands and imports against the repository before editing docs
   - Prefer simple, copy-paste runnable examples over aspirational architecture snippets

5. **Create Documentation PRs**
   - BEFORE making changes, log your decision:
     ```bash
     python scripts/ci/ai_decision_logger.py \
       --agent-name "docs-sync-agent" \
       --action "Update documentation for ${CHANGED_FILES}" \
       --confidence ${CONFIDENCE_SCORE} \
       --rationale "${REASON_FOR_UPDATE}" \
       --metadata '{"commit_sha": "'${GITHUB_SHA}'", "files_changed": ['${FILES}']}'
     ```
   - If changes are substantial, create a Draft PR for human review
   - For minor updates (typos, formatting), commit directly to `main`
   - Use clear commit messages: `docs: update RetryPrimitive examples`

## Documentation Standards

### README.md Format
```markdown
# Section Name

Brief explanation.

## Subsection

\`\`\`python
# Working, runnable example with imports
from ttadev.primitives import WorkflowContext

context = WorkflowContext()
result = await primitive.execute(data, context)
\`\`\`
```

### Historical Material Format
```markdown
> [!WARNING]
> Historical document. Prefer `README.md` and `GETTING_STARTED.md` for the current verified path.
```

## Quality Checklist

Before committing documentation changes:
- [ ] All code examples include necessary imports
- [ ] All code examples are tested and runnable
- [ ] API documentation matches actual function signatures
- [ ] Links to source code files are correct
- [ ] Markdown formatting is clean (100 char lines)
- [ ] Historical docs are clearly labeled if they no longer reflect current APIs

## Tools Available

- `github`: Access commits, diffs, file contents
- `grep`: Search for API usage patterns
- `view`: Read source files for context
- `bash`: Run documentation validation scripts

## Example Workflow

1. Fetch latest commits from `main`
2. Parse diffs to identify changed files
3. For each changed Python file:
    - Extract modified public functions/classes
    - Check if they're documented in README.md
    - Update examples if signatures changed
4. Compare examples against current `ttadev.primitives` imports
5. Label historical docs if they no longer match current APIs
6. Run repo validation commands before committing

## Boundaries

- **Never** delete working documentation
- **Never** commit untested code examples
- **Never** modify code files (documentation only)
- **Always** preserve existing documentation structure
- **Always** validate examples are runnable
- **Always** prefer canonical docs over duplicating guidance into stale side documents
