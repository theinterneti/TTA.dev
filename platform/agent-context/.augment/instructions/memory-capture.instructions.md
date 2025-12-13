---
applyTo: ["**/*"]
priority: high
category: global
---
# Memory Capture Workflow

Guidelines for AI agents on when and how to capture learnings, patterns, and decisions in the memory system.

## Architecture Principles

Core principles for memory capture:

- **Capture Early**: Document learnings as soon as they occur, while context is fresh
- **Be Specific**: Vague memories are not useful; include concrete details and examples
- **Be Actionable**: Extract clear lessons that can be applied in future work
- **Be Honest**: Document failures openly; they are valuable learning opportunities
- **Link Context**: Connect memories to related memories, commits, and documentation

## Memory Categories

The memory system has three categories, each serving a distinct purpose:

### Implementation Failures

**Purpose**: Document failed approaches, bugs, and mistakes to prevent repetition

**When to Capture**:
- After encountering a significant bug or error that took >30 minutes to resolve
- When an approach fails after substantial effort (>2 hours)
- When discovering a common pitfall or anti-pattern
- After debugging a complex issue with non-obvious root cause
- When a quality gate fails unexpectedly

**What to Include**:
- Detailed description of the problem and observable symptoms
- Root cause analysis (not just symptoms)
- Failed approaches attempted before finding solution
- Successful resolution with code examples
- Lessons learned and preventive measures
- When to watch for this issue in the future

**Severity Guidelines**:
- **Critical**: System-breaking issues, data loss, security vulnerabilities
- **High**: Significant development blockers, major bugs affecting multiple components
- **Medium**: Moderate issues affecting single component, workarounds available
- **Low**: Minor issues, cosmetic problems, documentation gaps

### Successful Patterns

**Purpose**: Document proven solutions, best practices, and effective techniques

**When to Capture**:
- After successfully solving a complex problem (>2 hours effort)
- When discovering an effective pattern or technique worth reusing
- After implementing a reusable solution or abstraction
- When establishing a new best practice or convention
- After completing a task significantly faster than expected

**What to Include**:
- Description of the pattern or solution
- Context where it applies (and where it doesn't)
- Implementation details with complete code examples
- Benefits and trade-offs
- When to use and when NOT to use
- Related patterns and alternatives

**Severity Guidelines**:
- **Critical**: Patterns preventing critical failures or enabling core functionality
- **High**: Patterns significantly improving development velocity or code quality
- **Medium**: Useful patterns with moderate impact
- **Low**: Nice-to-have patterns, minor optimizations

### Architectural Decisions

**Purpose**: Document design choices, technology selections, and strategic directions

**When to Capture**:
- After making a significant architectural decision affecting multiple components
- When selecting technologies, frameworks, or libraries
- When establishing project-wide standards or conventions
- When defining component boundaries or interfaces
- When making trade-offs between competing approaches

**What to Include**:
- The decision made (clear, specific statement)
- Context and constraints that influenced the decision
- Alternatives considered with pros/cons
- Rationale for the chosen approach
- Expected impact and trade-offs
- Success criteria for validating the decision

**Severity Guidelines**:
- **Critical**: Decisions affecting core architecture, data models, or security
- **High**: Decisions affecting multiple components or long-term maintainability
- **Medium**: Decisions affecting single component or short-term development
- **Low**: Minor decisions, easily reversible choices

## Memory Capture Checklist

Use this checklist when creating a memory:

### Pre-Capture
- [ ] Determine if this learning is worth capturing (>30 min impact or reusable)
- [ ] Choose appropriate category (implementation-failures, successful-patterns, architectural-decisions)
- [ ] Assess severity honestly (critical, high, medium, low)
- [ ] Identify affected component(s)
- [ ] Gather relevant tags for searchability

### During Capture
- [ ] Copy memory template to appropriate category directory
- [ ] Use descriptive file name: `<topic>-YYYY-MM-DD.memory.md`
- [ ] Fill in YAML frontmatter completely and accurately
- [ ] Write clear, descriptive title
- [ ] Provide one-line summary capturing the essence
- [ ] Document context thoroughly (when, where, who, what)
- [ ] Describe problem/opportunity/decision in detail
- [ ] Analyze root cause/rationale deeply
- [ ] Document solution/pattern/decision with code examples
- [ ] Extract actionable lessons learned
- [ ] Define applicability guidelines clearly
- [ ] Link related memories (if any)
- [ ] Add references (commits, issues, docs)

### Post-Capture
- [ ] Validate YAML frontmatter syntax
- [ ] Verify all required sections are complete
- [ ] Proofread for clarity and accuracy
- [ ] Test code examples for correctness
- [ ] Set status and review dates
- [ ] Commit memory file with descriptive message

## Common Patterns

### Pattern 1: Capture After Resolution

**When to use**: After successfully resolving a significant issue

**Example**:
```markdown
---
category: implementation-failures
date: 2025-10-22
component: agent-orchestration
severity: high
tags: [pytest, imports, test-environment]
---
# Pytest Import Error Resolution

Test runner import errors when using `uvx pytest` instead of project's configured test environment.

## Context
[Full context of the issue]

## Problem
[Detailed problem description]

## Root Cause
Always use project's configured test environment (`uv run pytest`) rather than isolated tool execution.

## Solution
[Solution with examples]

## Lesson Learned
**Key Takeaway**: Always use project's configured test environment to ensure correct module imports.
```

**Benefits**: Captures learning while context is fresh, prevents future repetition

### Pattern 2: Capture During Implementation

**When to use**: When discovering an effective pattern worth documenting

**Example**:
```markdown
---
category: successful-patterns
date: 2025-10-22
component: global
severity: high
tags: [development-workflow, templates, consistency]
---
# Template-Driven Development

Using templates ensures consistency across similar files and prevents missing required sections.

## Context
[When this pattern was discovered]

## Opportunity
[Why this pattern is valuable]

## Pattern
[Detailed pattern description with examples]

## Lesson Learned
**Key Takeaway**: Template-driven development prevents inconsistencies and ensures completeness.
```

**Benefits**: Documents patterns as they emerge, builds knowledge base incrementally

### Pattern 3: Capture Before Major Decision

**When to use**: Before committing to a significant architectural decision

**Example**:
```markdown
---
category: architectural-decisions
date: 2025-10-22
component: global
severity: critical
tags: [architecture, infrastructure, ai-agents]
---
# File-Based Instruction System

Decision to implement file-based instruction system rather than database-backed system.

## Context
[Decision context and constraints]

## Alternatives Considered
[List of alternatives with pros/cons]

## Decision
[Clear statement of decision made]

## Rationale
[Detailed reasoning]

## Expected Impact
[Anticipated outcomes and trade-offs]
```

**Benefits**: Documents decision rationale for future reference, enables informed review

## Error Handling

Memory capture should handle these scenarios:

- **Malformed YAML**: Validate frontmatter before saving
- **Missing Sections**: Ensure all required sections are present
- **Invalid Category**: Use only valid category values
- **Duplicate Memories**: Check for existing memories on same topic
- **Outdated Memories**: Mark superseded memories as deprecated

## Code Style

Memory file naming and formatting:

- **File Names**: `<descriptive-topic>-YYYY-MM-DD.memory.md`
- **Title Format**: Clear, specific, action-oriented
- **Section Headers**: Use consistent markdown heading levels
- **Code Blocks**: Always specify language for syntax highlighting
- **Links**: Use relative paths for internal links

## Integration Points

Memory system integrates with:

- **Context Manager**: Memories automatically loaded into AI agent context
- **Quality Gates**: Memory validation ensures well-formed files
- **Git**: All memories version-controlled with code
- **Documentation**: Memories complement formal documentation

## Quality Gates

Memory files must meet these criteria:

- **YAML Validation**: Frontmatter must be valid YAML
- **Required Fields**: All required frontmatter fields present
- **Valid Category**: Category must be one of three valid values
- **Date Format**: Date must be YYYY-MM-DD format
- **Required Sections**: All template sections present
- **Code Examples**: Code blocks must be syntactically valid

## Examples

### Example 1: Implementation Failure

**Context**: Test runner fails with import errors

**Implementation**:
```markdown
---
category: implementation-failures
date: 2025-10-22
component: agent-orchestration
severity: high
tags: [pytest, imports, test-environment]
---
# Pytest Import Error - Use Project Test Environment

Test runner import errors when using `uvx pytest` instead of `uv run pytest`.

## Root Cause
`uvx pytest` runs in isolated environment without project dependencies.

## Solution
Always use `uv run pytest` to ensure correct module imports.

## Lesson Learned
**Key Takeaway**: Use project's configured test environment, not isolated tools.
```

**Explanation**: Documents specific failure with clear resolution and actionable lesson

### Example 2: Successful Pattern

**Context**: Template-driven development ensures consistency

**Implementation**:
```markdown
---
category: successful-patterns
date: 2025-10-22
component: global
severity: high
tags: [development-workflow, templates, consistency]
---
# Template-Driven Development for Consistency

Using templates for similar files ensures consistency and completeness.

## Pattern
1. Create template with all required sections
2. Copy template for each new file
3. Fill in template sections systematically
4. Validate against template structure

## Benefits
- Prevents missing required sections
- Ensures consistent format
- Reduces cognitive load
- Enables automated validation

## Lesson Learned
**Key Takeaway**: Templates prevent inconsistencies and ensure completeness.
```

**Explanation**: Documents reusable pattern with clear benefits and application guidelines

## Anti-Patterns

Common mistakes to avoid when capturing memories:

### Anti-Pattern 1: Vague Memories

**Problem**: Memory lacks specific details, making it unusable

**Example**:
```markdown
# Something Failed

There was an error with tests. Fixed it somehow.
```

**Solution**: Provide specific details, root cause, and clear resolution

```markdown
# Pytest Import Error - Use Project Test Environment

Test runner import errors when using `uvx pytest` instead of `uv run pytest`.

## Root Cause
`uvx pytest` runs in isolated environment without project dependencies.

## Solution
Always use `uv run pytest` to ensure correct module imports and dependencies.
```

### Anti-Pattern 2: Missing Context

**Problem**: Memory doesn't explain when/where/why it applies

**Example**:
```markdown
# Use Templates

Templates are good. Use them.
```

**Solution**: Provide context, rationale, and applicability guidelines

```markdown
# Template-Driven Development for Consistency

## Context
When creating multiple similar files (instructions, memories, configs).

## Rationale
Templates ensure consistency and prevent missing required sections.

## Applicability
**When to Apply**: Creating files with standard structure
**When NOT to Apply**: One-off files, highly variable content
```

## References

- **Memory System README**: `.augment/memory/README.md`
- **Memory Template**: `.augment/memory/templates/memory.template.md`
- **Context Manager**: `.augment/context/conversation_manager.py`
- **Session Guide**: `docs/development/agentic-primitives-session-guide.md`

---

**Last Updated**: 2025-10-22
**Maintainer**: TTA Development Team


---
**Logseq:** [[TTA.dev/Platform/Agent-context/.augment/Instructions/Memory-capture.instructions]]
