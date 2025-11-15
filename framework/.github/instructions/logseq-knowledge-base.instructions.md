---
description: Logseq knowledge base and TODO management for all agents
applyTo: '**'
---

# Logseq Knowledge Base Instructions

**ALL agents working on TTA.dev MUST use the Logseq system for TODOs, documentation, and knowledge management.**

## 🎯 Core Requirements

### 1. TODO Management

**Location:** `logseq/journals/YYYY_MM_DD.md`

**When to Add TODOs:**
- Creating new implementation work
- Identifying missing tests
- Planning documentation updates
- Noting technical debt
- Tracking learning materials needed

**Tag Convention:**

```markdown
# Development Work
- TODO Implement feature X #dev-todo
  type:: implementation
  priority:: high
  package:: tta-dev-primitives
  related:: [[TTA Primitives]]

# User/Agent Learning
- TODO Create flashcards for primitives #user-todo
  type:: learning
  audience:: intermediate-users
  time-estimate:: 30 minutes
```

### 2. Daily Journal Updates

**When working on TTA.dev:**

1. **Start of Session:** Check today's journal for relevant TODOs
2. **During Work:** Add new TODOs as they arise
3. **After Completing Task:** Mark as DONE
4. **End of Session:** Update status of in-progress items

**Format:**

```markdown
## [[2025-10-31]] Session Notes

### Work Completed
- DONE Added metrics to CachePrimitive #dev-todo
  completed:: [[2025-10-31]]

### In Progress
- DOING Writing integration tests #dev-todo
  status:: in-progress

### Blocked
- TODO Deploy to staging #dev-todo
  blocked:: true
  blocker:: Waiting for infrastructure approval

### New TODOs
- TODO Document new API endpoints #dev-todo
  type:: documentation
  priority:: medium
```

### 3. Properties to Use

#### Development TODOs (#dev-todo)

**Required:**
- `type::` - implementation | testing | documentation | infrastructure | mcp-integration | examples
- `priority::` - high | medium | low
- `package::` - Package name if package-specific

**Optional:**
- `related::` - [[Page Reference]]
- `issue::` - #123 (GitHub issue number)
- `blocked::` - true | false
- `blocker::` - Description of what's blocking
- `status::` - not-started | in-progress | blocked | waiting
- `due::` - [[2025-11-01]]
- `assigned::` - @username
- `estimate::` - Time estimate (e.g., "2 hours")

#### User/Agent TODOs (#user-todo)

**Required:**
- `type::` - learning | documentation | milestone
- `audience::` - new-users | intermediate-users | advanced-users | expert-users | all-users

**Optional:**
- `related::` - [[Page Reference]]
- `difficulty::` - beginner | intermediate | advanced | expert
- `time-estimate::` - Estimated completion time
- `prerequisite::` - [[Other Task]]

### 4. Linking Context

**Always link related Logseq pages:**

```markdown
- TODO Add caching examples #dev-todo
  related:: [[TTA Primitives/CachePrimitive]]
  related:: [[TTA.dev/Examples]]
  package:: tta-dev-primitives
```

**Create new pages when needed:**
- Features: `[[TTA Primitives/NewFeature]]`
- Architecture: `[[TTA.dev/Architecture/ComponentName]]`
- Guides: `[[TTA.dev/Guides/TopicName]]`

### 5. Using TODO Queries

**Check dashboards before starting work:**

```markdown
# View your relevant TODOs
{{query (and (task TODO) [[#dev-todo]] (property priority high))}}

# Check blocked items
{{query (and (task TODO) (property blocked true))}}

# See what's in progress
{{query (task DOING)}}
```

**See:** `logseq/pages/TODO Management System.md` for complete query reference.

## 📚 Documentation in Logseq

### When to Create Logseq Pages

1. **Architecture Decisions:** Create `[[TTA.dev/Architecture/DecisionName]]`
2. **Feature Documentation:** Create `[[TTA Primitives/PrimitiveName]]`
3. **Learning Materials:** Create guides, flashcards, whiteboards
4. **Investigation Notes:** Document research and decisions

### Page Naming Convention

```
[[TTA.dev/Category/PageName]]
[[TTA Primitives/PrimitiveName]]
[[TTA Observability/Component]]
[[Learning/TopicName]]
```

### Flashcards for Learning

**Create flashcards for key concepts:**

```markdown
## Understanding RetryPrimitive #card

**Q:** What's the purpose of RetryPrimitive?

**A:** Automatically retries failed operations with configurable backoff strategies (constant, linear, exponential) and jitter support.

```

**See:** `logseq/pages/Learning TTA Primitives.md` for examples.

### Whiteboards for Architecture

**Create whiteboards for visual documentation:**

```markdown
# Whiteboard - New Feature Architecture

[[Create whiteboard in Logseq]]

## Components
- Layer 1: User Application
- Layer 2: Primitives
- Layer 3: Observability
```

**See:** `logseq/pages/Whiteboard - TTA.dev Architecture Overview.md` for template.

## 🔄 Workflows

### Feature Implementation Workflow

1. **Plan in Journal:**
   ```markdown
   - TODO Implement CachePrimitive enhancements #dev-todo
     type:: implementation
     priority:: high
     package:: tta-dev-primitives
   ```

2. **Create Feature Page:**
   - Create `[[TTA Primitives/CachePrimitive Enhancements]]`
   - Document design decisions
   - Link to related primitives

3. **During Implementation:**
   - Update TODO status to DOING
   - Add sub-tasks as needed
   - Document blockers

4. **After Completion:**
   - Mark TODO as DONE
   - Create user learning tasks if needed
   - Update architecture diagrams

### Documentation Workflow

1. **Identify Documentation Need:**
   ```markdown
   - TODO Document RouterPrimitive usage patterns #dev-todo
     type:: documentation
     priority:: medium
     related:: [[TTA Primitives/RouterPrimitive]]
   ```

2. **Create/Update Pages:**
   - Update `[[TTA Primitives/RouterPrimitive]]`
   - Add code examples
   - Create flashcards for learning

3. **Add User Learning Path:**
   ```markdown
   - TODO Create flashcards for router patterns #user-todo
     type:: learning
     audience:: intermediate-users
     related:: [[Learning TTA Primitives]]
   ```

### Bug Fix Workflow

1. **Log the Bug:**
   ```markdown
   - TODO Fix CachePrimitive TTL edge case #dev-todo
     type:: implementation
     priority:: high
     issue:: #234
     related:: [[TTA Primitives/CachePrimitive]]
   ```

2. **Document Investigation:**
   - Create `[[Investigations/Cache TTL Issue]]`
   - Document findings
   - Link to GitHub issue

3. **Track Testing:**
   ```markdown
   - TODO Add test coverage for TTL edge cases #dev-todo
     type:: testing
     priority:: high
     related:: [[TTA Primitives/CachePrimitive]]
   ```

## 🎓 Learning Path Integration

### For New Features

**Always create user learning tasks:**

```markdown
# After implementing new primitive
- TODO Create examples for NewPrimitive #user-todo
  type:: documentation
  audience:: all-users
  related:: [[TTA Primitives/NewPrimitive]]

- TODO Create flashcards for NewPrimitive #user-todo
  type:: learning
  audience:: intermediate-users
  related:: [[Learning TTA Primitives]]

- TODO Update architecture diagram #user-todo
  type:: documentation
  audience:: advanced-users
```

### For Documentation Updates

**Link to learning materials:**

```markdown
- TODO Update PRIMITIVES_CATALOG.md #dev-todo
  type:: documentation
  related:: [[TTA Primitives]]
  user-impact:: Creates learning opportunity for new patterns
```

## 📊 Status Tracking

### Check Before Commits

**Review these queries before committing:**

1. **Your in-progress items:**
   ```markdown
   {{query (task DOING)}}
   ```

2. **High-priority TODOs:**
   ```markdown
   {{query (and (task TODO) (property priority high))}}
   ```

3. **Blocked items to document:**
   ```markdown
   {{query (and (task TODO) (property blocked true))}}
   ```

### Weekly Review (Recommended)

**Every Monday, review:**

1. Completed tasks from last week
2. In-progress items
3. Blocked items needing attention
4. New priorities for this week

**Use:** `logseq/pages/TODO Management System.md` dashboards.

## 🚫 Anti-Patterns

### ❌ DON'T

- Create TODOs in code comments without logging in Logseq
- Skip property assignment (especially `type::` and `priority::`)
- Forget to mark completed tasks as DONE
- Create TODOs without linking related pages
- Mix dev and user TODOs without proper tags

### ✅ DO

- Always add TODOs to today's journal
- Use proper tags (#dev-todo vs #user-todo)
- Set all required properties
- Link to related Logseq pages
- Update status regularly
- Document blockers clearly
- Create learning tasks for user-facing changes

## 🔗 Resources

### Documentation

- **System Overview:** `logseq/pages/TODO Management System.md`
- **Advanced Features:** `logseq/ADVANCED_FEATURES.md`
- **Quick Reference:** `logseq/QUICK_REFERENCE_FEATURES.md`
- **Feature Summary:** `logseq/FEATURES_SUMMARY.md`

### Examples

- **Flashcards:** `logseq/pages/Learning TTA Primitives.md`
- **Whiteboard:** `logseq/pages/Whiteboard - TTA.dev Architecture Overview.md`
- **Journal Template:** `logseq/journals/2025_10_31.md`

### Configuration

- **Logseq Config:** `logseq/logseq/config.edn`
- **Features Enabled:** Journals, flashcards, whiteboards, queries

## 💡 Pro Tips

### For Efficiency

1. **Use Templates:** Copy TODO structure from existing items
2. **Batch Updates:** Update multiple TODOs during daily review
3. **Query Shortcuts:** Save frequent queries as page templates
4. **Link Liberally:** Over-link rather than under-link
5. **Tag Consistently:** Always use #dev-todo or #user-todo

### For Quality

1. **Be Specific:** "Add tests" → "Add integration tests for CachePrimitive TTL edge cases"
2. **Set Deadlines:** Use `due::` for time-sensitive items
3. **Document Context:** Use `related::` to provide background
4. **Track Dependencies:** Use `prerequisite::` for ordered tasks
5. **Celebrate Wins:** Review completed tasks weekly

### For Collaboration

1. **Use Assignments:** Set `assigned::` for team work
2. **Document Blockers:** Clear `blocker::` descriptions help coordination
3. **Link Issues:** Use `issue::` to connect GitHub and Logseq
4. **Share Context:** Create detailed investigation pages
5. **Update Status:** Keep TODO status current for team visibility

---

**Last Updated:** October 31, 2025
**Applies To:** All agents working on TTA.dev
**Priority:** High - Required for all work
