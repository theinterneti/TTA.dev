---
description: 'Review code for TTA.dev standards and primitive usage'
agent: 'agent'
---

# Code Review

Review ${file} for TTA.dev standards compliance.

## Review Checklist

### Primitive Usage
- [ ] No manual retry loops (use `RetryPrimitive`)
- [ ] No `asyncio.wait_for` (use `TimeoutPrimitive`)
- [ ] No manual cache dicts (use `CachePrimitive`)
- [ ] Workflows composed with `>>` and `|` operators

### Python Standards
- [ ] Type hints on all functions (`str | None` not `Optional[str]`)
- [ ] Google-style docstrings on public functions
- [ ] Imports ordered: stdlib, third-party, local
- [ ] No `pip` references (use `uv`)

### Error Handling
- [ ] Custom exceptions inherit from TTA base classes
- [ ] Error messages include context
- [ ] No bare `except:` clauses

### Testing
- [ ] Tests use `MockPrimitive`
- [ ] Tests use `@pytest.mark.asyncio`
- [ ] Coverage for success, failure, edge cases

### Security
- [ ] No secrets in code
- [ ] URL validation uses `urlparse()`
- [ ] Input validation present

## Common Issues

| Issue | Fix |
|-------|-----|
| `Optional[str]` | `str \| None` |
| `Dict[str, Any]` | `dict[str, Any]` |
| `pip install` | `uv add` |
| Manual retry loop | `RetryPrimitive` |
| `asyncio.wait_for` | `TimeoutPrimitive` |

## Output Format

```markdown
## Review Summary

**File:** ${file}
**Status:** ✅ Approved / ⚠️ Changes Requested

### Issues Found

1. **[Category]** Description
   - Location: line X
   - Fix: Suggested solution

### Suggestions

- Optional improvements
```


---
**Logseq:** [[TTA.dev/.github/Prompts/Code-review.prompt]]
