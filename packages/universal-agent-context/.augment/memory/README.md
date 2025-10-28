# AI Memory System

**Purpose**: Capture and preserve learnings, patterns, and decisions to improve AI agent effectiveness and prevent repeated mistakes.

## Overview

The memory system provides a structured way to document:
- **Implementation Failures**: Failed approaches, bugs, and mistakes to avoid
- **Successful Patterns**: Proven solutions, best practices, and effective techniques
- **Architectural Decisions**: Design choices, technology selections, and strategic directions

These memories are automatically loaded into AI agent context during development sessions, providing relevant historical knowledge to inform current work.

## Directory Structure

```
.augment/memory/
├── README.md                           # This file
├── templates/
│   └── memory.template.md              # Template for creating new memories
├── implementation-failures/            # Failed approaches and mistakes
│   └── *.memory.md
├── successful-patterns/                # Proven solutions and best practices
│   └── *.memory.md
└── architectural-decisions/            # Design decisions and rationale
    └── *.memory.md
```

## Memory Categories

### Implementation Failures

**Purpose**: Document failed approaches, bugs, and mistakes to prevent repetition

**When to Create**:
- After encountering a significant bug or error
- When an approach fails after substantial effort
- When discovering a common pitfall or anti-pattern
- After debugging a complex issue

**What to Include**:
- Detailed description of the problem and symptoms
- Root cause analysis
- Failed approaches attempted
- Successful resolution (if found)
- Lessons learned and preventive measures

**Example Scenarios**:
- Test runner import errors requiring specific environment setup
- Pre-commit hook failures due to legacy code issues
- Database connection timeouts requiring configuration changes
- Circular dependency issues in module imports

### Successful Patterns

**Purpose**: Document proven solutions, best practices, and effective techniques

**When to Create**:
- After successfully solving a complex problem
- When discovering an effective pattern or technique
- After implementing a reusable solution
- When establishing a new best practice

**What to Include**:
- Description of the pattern or solution
- Context where it applies
- Implementation details with code examples
- Benefits and trade-offs
- When to use and when not to use

**Example Scenarios**:
- Template-driven development for consistency
- Test-first approach catching edge cases early
- Incremental validation preventing rework
- Effective use of fixtures and markers in pytest

### Architectural Decisions

**Purpose**: Document design choices, technology selections, and strategic directions

**When to Create**:
- After making a significant architectural decision
- When selecting technologies or frameworks
- When establishing project-wide standards
- When defining component boundaries or interfaces

**What to Include**:
- The decision made
- Context and constraints
- Alternatives considered
- Rationale for the chosen approach
- Expected impact and trade-offs
- Success criteria

**Example Scenarios**:
- Choosing LangGraph for workflow orchestration
- Adopting component maturity workflow
- Selecting Redis for state management
- Implementing file-based instruction system

## Memory File Format

All memory files follow this structure:

```markdown
---
category: implementation-failures | successful-patterns | architectural-decisions
date: YYYY-MM-DD
component: <component-name>
severity: critical | high | medium | low
tags: [tag1, tag2, tag3]
---
# [Memory Title]

Brief one-line summary of the learning or decision.

## Context
[When, where, who, what]

## Problem / Opportunity / Decision
[Detailed description]

## Root Cause / Rationale
[Deep analysis]

## Solution / Pattern / Decision
[Detailed description with examples]

## Lesson Learned
[Key takeaways]

## Applicability
[When to apply, when not to apply]

## Related Memories
[Links to related memories]

## References
[Links to commits, issues, docs]
```

### YAML Frontmatter Fields

- **category**: One of `implementation-failures`, `successful-patterns`, `architectural-decisions`
- **date**: Date the memory was created (YYYY-MM-DD)
- **component**: Component or area affected (e.g., `agent-orchestration`, `player-experience`, `global`)
- **severity**: Impact level (`critical`, `high`, `medium`, `low`)
- **tags**: Keywords for searching and filtering (e.g., `[testing, pytest, fixtures]`)

## Creating a New Memory

### Step 1: Choose Category

Determine which category best fits your memory:
- **Implementation Failures**: Did something fail or go wrong?
- **Successful Patterns**: Did you discover an effective solution?
- **Architectural Decisions**: Did you make a design choice?

### Step 2: Copy Template

```bash
cp .augment/memory/templates/memory.template.md \
   .augment/memory/<category>/<descriptive-name>-YYYY-MM-DD.memory.md
```

### Step 3: Fill in YAML Frontmatter

Update the frontmatter with accurate metadata:
- Set the correct `category`
- Use today's date for `date`
- Specify the affected `component`
- Assess the `severity` honestly
- Add relevant `tags` for searchability

### Step 4: Document Thoroughly

Follow the template structure:
- **Context**: Provide enough background for someone unfamiliar with the situation
- **Problem/Opportunity/Decision**: Be specific and detailed
- **Root Cause/Rationale**: Dig deep, don't just describe symptoms
- **Solution/Pattern/Decision**: Include code examples and configuration
- **Lesson Learned**: Extract actionable insights
- **Applicability**: Help future readers know when to apply this learning

### Step 5: Review and Refine

Before saving:
- Ensure YAML frontmatter is valid
- Check that all sections are complete
- Verify code examples are accurate
- Add links to related memories and references
- Proofread for clarity and completeness

## Memory Capture Checklist

Use this checklist when creating a memory:

- [ ] Category selected appropriately
- [ ] YAML frontmatter complete and valid
- [ ] Title is clear and descriptive
- [ ] One-line summary captures the essence
- [ ] Context section provides sufficient background
- [ ] Problem/opportunity/decision is detailed
- [ ] Root cause/rationale is thorough
- [ ] Solution/pattern/decision includes examples
- [ ] Lesson learned is actionable
- [ ] Applicability guidelines are clear
- [ ] Related memories linked (if any)
- [ ] References added (commits, issues, docs)
- [ ] Status and review dates set

## Memory Review Process

### Regular Review

Memories should be reviewed periodically to ensure they remain relevant:

- **Active**: Memory is current and applicable
- **Deprecated**: Memory is outdated but kept for historical reference
- **Superseded**: Memory has been replaced by a newer, better approach

### Review Schedule

- **Critical/High Severity**: Review every 3 months
- **Medium Severity**: Review every 6 months
- **Low Severity**: Review annually

### Review Checklist

- [ ] Is the memory still relevant?
- [ ] Has the solution/pattern/decision changed?
- [ ] Are there newer, better approaches?
- [ ] Should the memory be deprecated or superseded?
- [ ] Are the examples still accurate?
- [ ] Should related memories be linked?

## Integration with AI Context Manager

The memory system integrates with the AI context manager to automatically load relevant memories during development sessions.

### How It Works

1. **Session Start**: AI agent initializes a new development session
2. **Context Loading**: Context manager loads instructions and memories
3. **Memory Matching**: Memories are matched based on:
   - Current component being worked on
   - Tags matching the task
   - Category relevance to the work
4. **Importance Scoring**: Memories are scored by:
   - Severity (critical > high > medium > low)
   - Recency (newer > older)
   - Relevance (exact match > partial match)
5. **Context Injection**: Top-scoring memories are injected into agent context

### Memory Matching Algorithm

Memories are matched using these criteria:

1. **Component Match**: Exact match on component name (highest priority)
2. **Tag Match**: Any tag matches current task tags
3. **Category Match**: Category is relevant to current work type
4. **Recency**: More recent memories score higher
5. **Severity**: Higher severity memories score higher

### Importance Scoring

Memories are scored on a scale of 0.0 to 1.0:

- **Critical + Exact Component Match**: 1.0
- **High + Exact Component Match**: 0.9
- **Medium + Exact Component Match**: 0.8
- **Low + Exact Component Match**: 0.7
- **Tag Match Only**: 0.5-0.7 (based on severity)
- **Category Match Only**: 0.3-0.5 (based on severity)

## Best Practices

### Writing Effective Memories

1. **Be Specific**: Vague memories are not useful. Include concrete details, examples, and context.
2. **Be Thorough**: Future readers may not have your context. Provide enough information to understand the situation.
3. **Be Actionable**: Extract clear lessons and guidelines that can be applied in the future.
4. **Be Honest**: Document failures and mistakes openly. They are valuable learning opportunities.
5. **Be Concise**: While thorough, avoid unnecessary verbosity. Focus on key information.

### Organizing Memories

1. **Use Descriptive Names**: File names should clearly indicate the content (e.g., `pytest-import-error-resolution-2025-10-22.memory.md`)
2. **Tag Generously**: Add all relevant tags to improve searchability
3. **Link Related Memories**: Create a web of knowledge by linking related memories
4. **Update Status**: Keep status and review dates current

### Maintaining the Memory System

1. **Regular Reviews**: Schedule periodic reviews to keep memories current
2. **Deprecate Outdated Memories**: Mark obsolete memories as deprecated rather than deleting them
3. **Consolidate Duplicates**: If multiple memories cover the same topic, consolidate them
4. **Extract Patterns**: If you notice recurring themes, consider creating a pattern memory

## Examples

### Example: Implementation Failure

**File**: `.augment/memory/implementation-failures/pytest-import-error-2025-10-22.memory.md`

**Scenario**: Test runner import errors when using `uvx pytest` instead of project's configured test environment

**Key Learning**: Always use project's configured test environment (`uv run pytest`) rather than isolated tool execution (`uvx pytest`) to ensure correct module imports and dependencies

### Example: Successful Pattern

**File**: `.augment/memory/successful-patterns/template-driven-development-2025-10-22.memory.md`

**Scenario**: Using `.instructions.md` template ensured consistency across all instruction files

**Key Learning**: Template-driven development prevents inconsistencies and ensures all required sections are included

### Example: Architectural Decision

**File**: `.augment/memory/architectural-decisions/file-based-instruction-system-2025-10-22.memory.md`

**Scenario**: Decision to implement file-based instruction system rather than database-backed system

**Key Learning**: File-based system provides version control, easy editing, and no additional infrastructure dependencies

## Troubleshooting

### Memory Not Loading

**Symptom**: Memory file exists but is not loaded into agent context

**Possible Causes**:
1. YAML frontmatter is malformed
2. Component name doesn't match current work
3. Tags don't match current task
4. Memory is marked as deprecated

**Solutions**:
1. Validate YAML frontmatter syntax
2. Check component name matches exactly
3. Add more relevant tags
4. Ensure status is "Active"

### Memory Validation Errors

**Symptom**: Memory file fails validation

**Possible Causes**:
1. Missing required YAML fields
2. Invalid category value
3. Malformed date format
4. Missing required sections

**Solutions**:
1. Ensure all required YAML fields are present
2. Use only valid category values
3. Use YYYY-MM-DD date format
4. Include all required sections from template

## Related Documentation

- **Context Manager**: `.augment/context/README.md` - How memories are loaded into context
- **Instructions System**: `.augment/instructions/` - Complementary guidance system
- **Memory Template**: `.augment/memory/templates/memory.template.md` - Template for creating memories
- **Memory Capture Instructions**: `.augment/instructions/memory-capture.instructions.md` - Detailed guidelines for AI agents

---

**Last Updated**: 2025-10-22
**Version**: 1.0
**Status**: Active
