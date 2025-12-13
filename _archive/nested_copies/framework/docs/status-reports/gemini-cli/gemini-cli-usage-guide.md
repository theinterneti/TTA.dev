# Gemini CLI Usage Guide

**Quality-first AI code review and development assistance**

---

## 🎯 Quick Start

### Basic Commands

```bash
# Invoke Gemini with default quality model (thinking)
@gemini-cli Review this PR for best practices

# Get help
@gemini-cli /help

# Review code
@gemini-cli /review

# Triage an issue
@gemini-cli /triage
```

### Model Tiers

The system uses **gemini-2.0-flash-thinking-exp-1219** by default for highest quality reasoning.

**Available Tiers:**
- **thinking** (default) - Extended reasoning, shows thought process, highest quality
- **pro** - Proven quality, balanced performance
- **fast** - Quick responses for simple tasks
- **auto** - Automatically selects based on task complexity

---

## 💡 Example Use Cases

### Code Review (Default - Quality Mode)

```bash
@gemini-cli /review
```

This uses the thinking model for deep analysis showing reasoning steps.

### Complex Architectural Decision

```bash
@gemini-cli Should we refactor this module to use dependency injection?
Consider our existing patterns and the long-term maintainability.
```

Auto-detected as complex → uses thinking model.

### Documentation Lookup with Context7

```bash
@gemini-cli Using Context7, verify this FastAPI implementation follows best practices
```

Gemini will:
1. Use Context7 MCP to lookup FastAPI documentation
2. Compare your code against official patterns
3. Provide specific recommendations with references

### Quick Question (Fast Mode)

For simple queries where you want speed over extended reasoning, you can request fast mode (coming soon in dispatch enhancements).

---

## 🔧 Available Tools

Gemini has access to the following capabilities:

### GitHub Operations (18 tools)

- File management: create_or_update_file, delete_file, get_file_contents
- Branch operations: create_branch
- Pull requests: create_pull_request, list_pull_requests, search_pull_requests
- Issues: add_issue_comment, get_issue, list_issues, search_issues
- Code search: search_code, list_commits, get_commit
- Repository: fork_repository, push_files

### Context7 - Library Documentation (2 tools)

- **resolve-library-id** - Find the correct library identifier
- **get-library-docs** - Retrieve up-to-date documentation

**Example prompts that leverage Context7:**
```bash
@gemini-cli Check if this uses the latest Pydantic v2 patterns

@gemini-cli Review SQLAlchemy usage against current best practices

@gemini-cli Is this FastAPI route handler correctly structured per docs?
```

---

## 🧠 Quality Mode (Thinking Model)

The default thinking model provides:

### Extended Reasoning
Shows its thought process before providing answers:
- Analyzes the problem
- Considers alternatives
- Evaluates tradeoffs
- Reaches a conclusion

### Better for Complex Tasks
- Architectural decisions
- Security analysis
- Performance optimization
- Refactoring plans
- Complex debugging

### Higher Accuracy
- Fewer hallucinations
- More thorough analysis
- Better context understanding
- Stronger reasoning chains

---

## 📊 Model Selection Logic

When you use `@gemini-cli` without specifying a model, the system auto-selects based on keywords:

### Thinking Model (Quality)
Triggered by keywords:
- architect, design, complex, refactor
- "analyze deeply"
- Security reviews
- Performance analysis

### Pro Model (Balanced)
Triggered by keywords:
- review, analyze, explain, document
- Standard code reviews
- Documentation generation

### Fast Model (Speed)
Triggered by:
- Simple questions
- Quick triage
- Basic queries

Default: **thinking** (quality over speed)

---

## 🎨 Advanced Patterns

### Multi-Tool Usage

Gemini can chain multiple tools:

```bash
@gemini-cli
1. Search our codebase for similar authentication patterns
2. Look up the latest OAuth2 best practices using Context7
3. Review this PR's auth implementation
4. Create a security checklist as an issue
```

Gemini will:
1. Use `search_code` for internal patterns
2. Use Context7 for OAuth2 docs
3. Review the PR code
4. Use `add_issue_comment` to document findings

### Documentation-Driven Review

```bash
@gemini-cli Review this API implementation:
1. Check against FastAPI docs (use Context7)
2. Verify our internal API guidelines (search codebase)
3. Suggest improvements with references
```

### Incremental Improvements

```bash
@gemini-cli Create a branch with formatting fixes for this file
```

Gemini will:
1. Analyze the file
2. Create a new branch
3. Make targeted improvements
4. Push changes
5. Create a PR with detailed explanation

---

## 🔐 Security & Permissions

### What Gemini Can Do

✅ Read all repository files
✅ Create and update files
✅ Create branches
✅ Create pull requests
✅ Add comments to issues/PRs
✅ Search code and documentation
✅ Query external documentation (Context7)

### What Gemini Cannot Do

❌ Force push to protected branches
❌ Delete branches
❌ Modify workflow files (security constraint)
❌ Access secrets or environment variables
❌ Execute arbitrary shell commands (limited to safe read-only commands)

---

## 📈 Performance Expectations

### Thinking Model
- Response time: 30-90 seconds (shows reasoning)
- Best for: Complex analysis, architectural decisions
- Free tier: Generous limits

### Pro Model
- Response time: 20-60 seconds
- Best for: Standard code reviews
- Free tier: 1,500 requests/day

### Fast Model
- Response time: 10-30 seconds
- Best for: Quick questions, triage
- Free tier: High limits

---

## 🎓 Tips & Best Practices

### Be Specific

```bash
# ❌ Vague
@gemini-cli check this

# ✅ Specific
@gemini-cli Review the authentication logic in auth.py for security vulnerabilities,
focusing on token validation and session management
```

### Leverage Context7

```bash
# ❌ Generic
@gemini-cli Is this FastAPI code correct?

# ✅ Leverages docs
@gemini-cli Using Context7, verify this FastAPI code follows the official
dependency injection patterns and best practices
```

### Ask for Reasoning

```bash
# ✅ Shows thought process
@gemini-cli Explain your reasoning: Should we use Redis or Memcached for caching?
```

### Request Incremental Work

```bash
# ✅ Clear scope
@gemini-cli Create a PR that adds input validation to the user registration endpoint
```

### Use Multi-Step Instructions

```bash
# ✅ Structured approach
@gemini-cli
1. Analyze the performance bottleneck in this code
2. Research best practices for optimization using Context7
3. Propose 3 specific improvements with tradeoffs
4. If I approve, create a PR with the best option
```

---

## 🐛 Troubleshooting

### Gemini Doesn't Respond

**Check:**
1. Did you tag `@gemini-cli` at the start?
2. Are you an OWNER, MEMBER, or COLLABORATOR?
3. Is this a forked repository? (Not currently supported)

**View logs:**
The acknowledgment comment includes a link to workflow logs.

### Context7 Not Finding Documentation

**Try:**
1. Be specific with library names: "FastAPI" not "fast api"
2. Specify version if needed: "Pydantic v2"
3. Use official package names: "SQLAlchemy" not "sqlalchemy"

### Quality Issues

**Improve by:**
1. Providing more context in your request
2. Being specific about what you want analyzed
3. Asking for reasoning: "Explain your thought process"
4. Using the thinking model for complex tasks (default)

---

## 📚 Examples by Use Case

### Security Review

```bash
@gemini-cli Perform a security review of this authentication code:
- Check for common vulnerabilities
- Verify input validation
- Review session management
- Check for proper error handling
Provide specific CVE references where applicable.
```

### Performance Optimization

```bash
@gemini-cli This endpoint is slow under load:
1. Profile the code path
2. Look up database query optimization best practices (Context7)
3. Suggest 3 specific improvements
4. Estimate impact of each
```

### API Design Review

```bash
@gemini-cli Using Context7, review this REST API design:
1. Check against REST best practices
2. Verify FastAPI patterns
3. Review error handling
4. Suggest improvements for consistency
```

### Documentation Generation

```bash
@gemini-cli Generate comprehensive API documentation for this module:
- Include all public functions
- Add usage examples
- Document parameters and return types
- Note any edge cases or limitations
Create the docs as docs/api/module-name.md
```

### Refactoring Analysis

```bash
@gemini-cli Should we refactor this module? Consider:
1. Current complexity metrics
2. Maintainability concerns
3. Testing coverage
4. Breaking change risks
Provide a detailed analysis with recommendation.
```

---

## 🚀 Advanced Features

### Chaining Operations

```bash
@gemini-cli
1. Create a branch called 'feature/add-logging'
2. Add structured logging to all database operations
3. Update the logging configuration
4. Create a PR with detailed changelog
```

### Research Mode

```bash
@gemini-cli Research task:
1. Use Context7 to review current best practices for asyncio error handling
2. Search our codebase for existing patterns
3. Identify gaps in our current implementation
4. Write a technical design doc proposing improvements
```

### Incremental Development

```bash
@gemini-cli Let's improve error handling incrementally:

Step 1: Create a branch and add custom exception classes
Wait for my approval before continuing.

Step 2: Update the database layer to use new exceptions
Wait for my approval before continuing.

Step 3: Update API endpoints with proper error responses
Wait for my approval before continuing.

Step 4: Add tests for error scenarios
```

---

## 📞 Getting Help

### In GitHub
```bash
@gemini-cli /help
```

### Documentation
- [Integration Guide](./gemini-cli-integration-guide.md)
- [Quality Enhancements](./gemini-cli-quality-enhancements.md)
- [Capabilities Analysis](./gemini-cli-capabilities-analysis.md)

### Workflow Logs
Every interaction includes a link to detailed logs in the acknowledgment comment.

---

## 🎯 Quick Reference

| Command | Purpose | Model |
|---------|---------|-------|
| `@gemini-cli /review` | Code review | Thinking (quality) |
| `@gemini-cli /triage` | Issue triage | Auto-selected |
| `@gemini-cli [prompt]` | General task | Thinking (default) |
| `@gemini-cli /help` | Get help | Fast |

| Feature | Description |
|---------|-------------|
| **Thinking Model** | Shows reasoning, highest quality (default) |
| **Context7** | Library documentation lookup |
| **GitHub Tools** | 18 operations for file/PR/issue management |
| **Auto-selection** | Chooses model based on task complexity |

---

**Last Updated:** October 31, 2025
**Model:** gemini-2.0-flash-thinking-exp-1219 (default)
**MCP Servers:** GitHub (v0.20.1), Context7


---
**Logseq:** [[TTA.dev/_archive/Nested_copies/Framework/Docs/Status-reports/Gemini-cli/Gemini-cli-usage-guide]]
