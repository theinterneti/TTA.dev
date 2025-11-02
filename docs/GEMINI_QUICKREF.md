# Quick Reference: @gemini-cli in TTA.dev

**Fast reference for using Gemini CLI in GitHub issues and PRs**

---

## Basic Commands

### Get Help
```
@gemini-cli help
```

### Code Review
```
@gemini-cli /review
```

### Issue Triage
```
@gemini-cli /triage
```

---

## Natural Language Queries

### Repository Questions
```
@gemini-cli What are the main features of CachePrimitive?

@gemini-cli Explain how the workflow dispatch system works

@gemini-cli Summarize recent changes to Gemini CLI integration
```

### Search & Discovery
```
@gemini-cli List all open issues related to [topic]

@gemini-cli Find PRs that modified [file/directory]

@gemini-cli What is the status of issue #[number]?
```

### Code Analysis
```
@gemini-cli Analyze the security implications of [feature]

@gemini-cli Review [file] for performance issues

@gemini-cli Explain the architecture of [component]
```

---

## Advanced Features

### With Context7 (External Documentation)
```
@gemini-cli Using Context7, explain best practices for [library/topic]

@gemini-cli Look up the latest documentation for [library] and suggest improvements
```

### Write Operations (Requires Approval)
```
@gemini-cli Create a test file for [component]

@gemini-cli Generate documentation for [feature]

@gemini-cli Update [file] to fix [issue]
```

**Note:** Write operations post a plan and wait for `/approve` comment

---

## Expected Response Times

| Command Type | Expected Time |
|--------------|---------------|
| Help | < 30 seconds |
| Simple queries | < 1 minute |
| Analysis/Review | 1-2 minutes |
| Complex tasks | 2-5 minutes |

---

## Current Configuration

**Models in Use:**
- **Quality (default)**: `gemini-2.0-flash-thinking-exp-1219`
- **Balanced**: `gemini-1.5-pro-002`
- **Speed**: `gemini-2.0-flash-exp`

**MCP Servers:**
- ✅ GitHub (v0.20.1) - Repository operations
- ✅ Context7 - External documentation

**Permissions:**
- ✅ Read: Issues, PRs, code, comments
- ✅ Write: Comments, files, branches, PRs (with approval)
- ❌ Merge: Requires human review

---

## Quality Checklist

**Good @gemini requests:**
- ✅ Specific and clear
- ✅ Provides context when needed
- ✅ One request per comment
- ✅ Uses appropriate command (`/review`, `/triage`)

**Avoid:**
- ❌ Vague requests ("review this")
- ❌ Multiple unrelated requests
- ❌ Expecting instant responses
- ❌ Requesting unsafe operations

---

## Examples by Use Case

### PR Review
```
Issue: Need code review
Comment: @gemini-cli /review
Result: Comprehensive code analysis
```

### Documentation Question
```
Issue: How does RetryPrimitive work?
Comment: @gemini-cli Explain RetryPrimitive with usage examples
Result: Detailed explanation with code samples
```

### Bug Investigation
```
Issue: Workflow timing out
Comment: @gemini-cli Analyze issue #68 and summarize the investigation
Result: Timeline, root cause, solution
```

### Library Best Practices
```
Issue: Need FastAPI guidance
Comment: @gemini-cli Using Context7, review this FastAPI code for best practices
Result: Analysis with external documentation references
```

### File Creation
```
Issue: Need test examples
Comment: @gemini-cli Create a test file showing MockPrimitive usage
Result: Plan posted → Await approval → File created → PR opened
```

---

## Troubleshooting

### No Response
- Check [workflow runs](https://github.com/theinterneti/TTA.dev/actions)
- Verify you're OWNER/MEMBER/COLLABORATOR
- Wait 2-3 minutes before retrying

### Generic Response
- Add more context to your request
- Specify exact files/components
- Use `/review` or `/triage` commands for standard operations

### Timeout
- Large PRs may take longer
- Check workflow logs for details
- Consider breaking request into smaller parts

---

## Testing Framework

**Test Locations:**
- Issue #61 - Primary testing ground
- PR #74 - Code review testing

**Test Protocol:**
- See `docs/gemini-cli-testing-protocol.md`

**Report Issues:**
- Create issue with `gemini-cli` label
- Include workflow run link
- Describe expected vs actual behavior

---

## Resources

- **Integration Guide**: `docs/gemini-cli-integration-guide.md`
- **Capabilities**: `docs/gemini-cli-capabilities-analysis.md`
- **Optimization Plan**: `docs/gemini-cli-optimization-plan.md`
- **Testing Protocol**: `docs/gemini-cli-testing-protocol.md`

---

**Questions?** Ask in [Discussions](https://github.com/theinterneti/TTA.dev/discussions) or create an [Issue](https://github.com/theinterneti/TTA.dev/issues).

---

**Quick Start:** Just type `@gemini-cli help` in any issue or PR! 🚀
