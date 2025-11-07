# TODO Guidelines for TTA.dev

**Purpose**: Define when to use code TODOs vs. Logseq TODOs  
**Audience**: All contributors (developers, agents, maintainers)  
**Status**: ✅ Active  
**Last Updated**: 2025-10-31

---

## 🎯 Quick Decision Framework

### Use **Code TODO** (inline comment) when:

✅ **Providing context** for future developers  
✅ **Documenting limitations** of current implementation  
✅ **Explaining non-obvious behavior** or edge cases  
✅ **Marking optimization opportunities** (low priority)  
✅ **Noting assumptions** or constraints  
✅ **Temporary debugging** notes (remove before merge)

### Use **Logseq TODO** when:

✅ **Tracking actual work items** requiring completion  
✅ **Managing feature development** across sprints  
✅ **Coordinating work** across team members  
✅ **Linking to documentation** or KB pages  
✅ **Requiring priority/status tracking**  
✅ **Blocking other work** or dependencies  
✅ **Needs effort estimation** or time tracking

---

## 📝 Code TODO Examples

### ✅ Good Code TODOs (Keep as inline comments)

#### 1. Providing Context

```python
# TODO: This could be optimized with caching, but current performance is acceptable
# for the expected load (< 1000 requests/sec). Revisit if load increases.
def process_request(request: Request) -> Response:
    ...
```

**Why**: Explains decision, provides context for future optimization.

---

#### 2. Documenting Limitations

```python
# Note: Only primitive.X spans have correlation_id tags, not internal sequential.step_X spans
# This is intentional to reduce span volume and focus on user-facing operations.
def create_span(name: str, context: WorkflowContext) -> Span:
    ...
```

**Why**: Documents known limitation and reasoning.

---

#### 3. Explaining Non-Obvious Behavior

```python
# TODO: ConditionalPrimitive doesn't extend InstrumentedPrimitive because it delegates
# to child primitives which already have instrumentation. Adding another layer would
# create duplicate spans.
class ConditionalPrimitive(WorkflowPrimitive[T, U]):
    ...
```

**Why**: Explains architectural decision to prevent confusion.

---

#### 4. Marking Optimization Opportunities

```python
# TODO: This linear search could be replaced with a hash map for O(1) lookup,
# but current list size is < 10 items so performance impact is negligible.
def find_item(items: list[Item], key: str) -> Item | None:
    for item in items:
        if item.key == key:
            return item
    return None
```

**Why**: Notes optimization opportunity without creating work item.

---

#### 5. Noting Assumptions

```python
# Note: Assumes input is already validated by upstream primitive.
# If used standalone, add validation here.
def transform_data(data: dict[str, Any]) -> dict[str, Any]:
    ...
```

**Why**: Documents assumption for future maintainers.

---

### ❌ Bad Code TODOs (Should be Logseq TODOs)

#### 1. Actual Work Items

```python
# TODO: Implement retry logic with exponential backoff
def api_call(url: str) -> Response:
    return requests.get(url)  # No retry!
```

**Why**: This is actual work that needs tracking. Should be Logseq TODO.

**Better**:
```markdown
- TODO Implement retry logic for API calls #dev-todo
  type:: implementation
  priority:: high
  package:: tta-dev-primitives
  related:: [[TTA.dev/Primitives/RetryPrimitive]]
  file:: src/api_client.py:42
```

---

#### 2. Feature Requests

```python
# TODO: Add support for GraphQL queries
class APIClient:
    def rest_call(self, endpoint: str) -> dict:
        ...
```

**Why**: Feature request needs prioritization and tracking. Should be Logseq TODO.

---

#### 3. Bug Fixes

```python
# TODO: Fix race condition in cache invalidation
def invalidate_cache(key: str) -> None:
    ...
```

**Why**: Bug fix needs tracking and testing. Should be Logseq TODO with issue link.

---

## 📋 Logseq TODO Examples

### ✅ Good Logseq TODOs

#### 1. Feature Development

```markdown
- TODO Implement GoogleGeminiPrimitive for free tier access #dev-todo
  type:: implementation
  priority:: critical
  package:: tta-dev-primitives
  related:: [[TTA.dev/Primitives/GoogleGeminiPrimitive]], [[TTA.dev/LLM Providers/Google Gemini]]
  issue:: https://github.com/theinterneti/TTA.dev/issues/75
  notes:: Google AI Studio provides free access to Gemini Pro
  estimated-effort:: 1 week
  dependencies:: Verify Google AI Studio API key works
  blocked:: false
```

**Why**: Complex feature requiring tracking, prioritization, and coordination.

---

#### 2. Bug Fix with Investigation

```markdown
- TODO Fix CachePrimitive TTL edge case #dev-todo
  type:: implementation
  priority:: high
  package:: tta-dev-primitives
  related:: [[TTA.dev/Primitives/CachePrimitive]]
  issue:: https://github.com/theinterneti/TTA.dev/issues/123
  notes:: Cache entries expire 1 second early due to rounding error
  estimated-effort:: 2 days
  dependencies:: None
  blocked:: false
  investigation:: [[2025-10-31]] - Root cause: time.time() vs datetime.now()
```

**Why**: Bug requires investigation, testing, and verification.

---

#### 3. Documentation Work

```markdown
- TODO Update PRIMITIVES_CATALOG.md with new primitives #dev-todo
  type:: documentation
  priority:: high
  package:: infrastructure
  related:: [[TTA.dev/Primitives]], [[PRIMITIVES_CATALOG]]
  notes:: RouterPrimitive, CachePrimitive, TimeoutPrimitive added but not documented
  estimated-effort:: 1 day
  dependencies:: None
  blocked:: false
```

**Why**: Documentation work needs tracking to ensure completion.

---

#### 4. Learning/Onboarding Tasks

```markdown
- TODO Create flashcards for router patterns #user-todo
  type:: learning
  audience:: intermediate-users
  difficulty:: intermediate
  related:: [[TTA.dev/Primitives/RouterPrimitive]], [[TTA.dev/Learning]]
  notes:: Help users learn LLM routing strategies
  estimated-effort:: 1 week
  time-estimate:: 20 minutes per pattern
```

**Why**: User-facing work requiring effort estimation and tracking.

---

## 🔄 Migration Process

### When You Find a Code TODO That Should Be in Logseq:

1. **Assess Priority**:
   - P0 (Critical): Migrate immediately
   - P1 (High): Migrate this week
   - P2 (Medium): Migrate this sprint
   - P3 (Low): Keep as code comment or delete

2. **Create Logseq TODO**:
   - Add to today's journal (`logseq/journals/YYYY_MM_DD.md`)
   - Use proper tag (`#dev-todo` or `#user-todo`)
   - Add all required properties
   - Link to related KB pages

3. **Update Code Comment**:
   - Replace with reference to Logseq TODO
   - Or remove if redundant

**Example**:

**Before**:
```python
# TODO: Implement retry logic with exponential backoff
def api_call(url: str) -> Response:
    return requests.get(url)
```

**After**:
```python
# See Logseq TODO: [[2025-10-31]] - Implement retry logic
# Tracked in: logseq/journals/2025_10_31.md
def api_call(url: str) -> Response:
    return requests.get(url)
```

**Logseq**:
```markdown
- TODO Implement retry logic for API calls #dev-todo
  type:: implementation
  priority:: high
  package:: tta-dev-primitives
  related:: [[TTA.dev/Primitives/RetryPrimitive]]
  file:: src/api_client.py:42
```

---

## 🚫 Anti-Patterns

### ❌ Don't Do This:

1. **Duplicate TODOs** in both code and Logseq
   - Choose one location based on guidelines

2. **Vague TODOs** without context
   ```python
   # TODO: Fix this
   ```
   - Always explain what needs fixing and why

3. **Stale TODOs** that are no longer relevant
   - Delete or update regularly

4. **TODOs without priority** in Logseq
   - Always set priority for dev-todo items

5. **TODOs without related pages** in Logseq
   - Always link to relevant KB pages

---

## ✅ Best Practices

### For Code TODOs:

1. **Be Specific**: Explain what, why, and when
2. **Add Context**: Help future developers understand
3. **Keep Short**: If explanation is long, use Logseq
4. **Review Regularly**: Delete stale TODOs during code reviews
5. **Link to Logseq**: If work is tracked elsewhere

### For Logseq TODOs:

1. **Use Templates**: Copy structure from existing TODOs
2. **Add All Properties**: Don't skip required fields
3. **Link Generously**: Connect to related KB pages
4. **Update Status**: Keep TODO/DOING/DONE current
5. **Add Notes**: Document decisions and blockers

---

## 📊 Metrics & Monitoring

### Code TODO Metrics:

- **Total code TODOs**: Track in codebase scan
- **Age of TODOs**: Identify stale items
- **TODO density**: TODOs per 1000 lines of code
- **Target**: < 5 TODOs per 1000 lines

### Logseq TODO Metrics:

- **Total TODOs**: Track in validation script
- **Compliance rate**: Must be 100%
- **Completion rate**: Track DONE vs. TODO
- **Average age**: Time from creation to completion

**Run Metrics**:
```bash
# Scan codebase TODOs
uv run python scripts/scan-codebase-todos.py --json

# Validate Logseq TODOs
uv run python scripts/validate-todos.py --json
```

---

## 🔗 Related Documentation

- **TODO Management System**: [`logseq/pages/TODO Management System.md`](../logseq/pages/TODO%20Management%20System.md)
- **Codebase TODO Analysis**: [`CODEBASE_TODO_ANALYSIS_2025_10_31.md`](../CODEBASE_TODO_ANALYSIS_2025_10_31.md)
- **Migration Plan**: [`CODEBASE_TODO_MIGRATION_PLAN.md`](../CODEBASE_TODO_MIGRATION_PLAN.md)
- **Contributing Guide**: [`CONTRIBUTING.md`](../CONTRIBUTING.md)

---

## 📞 Questions?

If you're unsure whether a TODO should be in code or Logseq:

1. **Ask yourself**: "Does this need tracking and prioritization?"
   - Yes → Logseq TODO
   - No → Code TODO

2. **Check examples** in this document

3. **When in doubt**: Create Logseq TODO (easier to delete than to lose track)

---

**Status**: ✅ Active  
**Owner**: TTA.dev Team  
**Review**: Quarterly  
**Last Updated**: 2025-10-31

