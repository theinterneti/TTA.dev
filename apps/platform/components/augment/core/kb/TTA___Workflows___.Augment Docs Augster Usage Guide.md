---
title: Augster Usage Guide
tags: #TTA
status: Active
repo: theinterneti/TTA
path: .augment/docs/augster-usage-guide.md
created: 2025-11-01
updated: 2025-11-01
---
# [[TTA/Workflows/Augster Usage Guide]]

This guide explains how to use the modular Augster system effectively.

## Quick Start

The Augster system is **automatically active** - no setup required! Simply interact with the AI and it will exhibit Augster behavior.

### What You Get

- **Elite-level software engineering** through systematic workflows
- **Comprehensive planning** before implementation
- **Rigorous verification** of all work
- **Autonomous problem-solving** with minimal user intervention
- **Clear, scannable communication** optimized for efficiency

## Always-Active Modules

These instruction files are automatically loaded for all interactions:

### 1. Core Identity (`augster-core-identity.instructions.md`)

**What it does:**
- Establishes "The Augster" persona
- Defines 16 personality traits (Genius, Principled, Meticulous, etc.)
- Provides glossary of key concepts (Mission, Workload, Trajectory, PAF, etc.)

**When it's active:** Always

**How to use:** No action needed - the AI will embody these traits automatically

---

### 2. Communication Style (`augster-communication.instructions.md`)

**What it does:**
- Ensures clear, scannable, efficient communication
- Applies formatting guidelines (bold text, headers, lists)
- Optimizes for time-constrained users

**When it's active:** Always (applies to user-facing output only)

**How to use:** Expect responses formatted with:
- **Bold text** for key terms and conclusions
- Clear headers for organization
- Bulleted/numbered lists for readability
- Concise paragraphs (3-5 sentences max)

---

### 3. Maxims (`augster-maxims.instructions.md`)

**What it does:**
- Enforces 13 fundamental behavioral rules
- Governs cognitive processes, code quality, and workflow

**Key maxims you'll notice:**
- **PrimedCognition**: Structured reasoning before actions
- **Autonomy**: Proactive execution without constant user queries
- **EmpiricalRigor**: No assumptions - only verified facts
- **Consistency**: Adherence to codebase conventions
- **PurityAndCleanliness**: Real-time cleanup of obsolete code

**When it's active:** Always

**How to use:** Trust the AI to follow best practices automatically

---

### 4. Protocols (`augster-protocols.instructions.md`)

**What it does:**
- Provides reusable procedures for common tasks
- Includes: DecompositionProtocol, PAFGateProtocol, ClarificationProtocol

**When you'll see them:**
- **DecompositionProtocol**: When breaking down complex tasks
- **PAFGateProtocol**: When storing architectural facts
- **ClarificationProtocol**: When AI needs essential input from you

**When it's active:** Always (invoked as needed)

---

### 5. Heuristics (`augster-heuristics.instructions.md`)

**What it does:**
- Applies SOLID principles for code design
- Uses SWOT analysis for planning
- Follows DRY, YAGNI, KISS principles

**When it's active:** Always (applied when appropriate)

**How to use:** Expect code that follows industry best practices

---

### 6. Operational Loop (`augster-operational-loop.instructions.md`)

**What it does:**
- Detects whether a Mission is in progress
- Invokes the Axiomatic Workflow when needed
- Manages task list for mission tracking

**When it's active:** Always (checked at start of each interaction)

**How to use:** The AI will automatically:
- Check task list status
- Continue existing missions or start new ones
- Manage mission lifecycle

## Workflow Template

### Axiomatic Workflow (`augster-axiomatic-workflow.prompt.md`)

**What it does:**
- Executes missions through 6 systematic stages
- Ensures comprehensive planning and verification

**The 6 stages:**
1. **Preliminary**: Distill mission, create workload, analyze pre-existing tech
2. **Planning and Research**: Resolve uncertainties, identify new technologies
3. **Trajectory Formulation**: Create detailed execution plan, register tasks
4. **Implementation**: Execute all tasks sequentially
5. **Verification**: Verify mission completion
6. **Post-Implementation**: Document suggestions, provide summary

**When it's invoked:** Automatically by operational loop for complex missions

**How to use:** Simply provide your request - the AI will follow the workflow automatically

## Usage Examples

### Example 1: Simple Request

**User:** "Explain how the authentication system works"

**Augster behavior:**
- Checks task list (empty → simple query, not a mission)
- Uses codebase-retrieval to find authentication code
- Provides clear, scannable explanation with bold key terms
- No workflow invocation needed

---

### Example 2: Complex Feature Implementation

**User:** "Implement user preferences system with Redis storage"

**Augster behavior:**
1. **Operational Loop**: Checks task list (empty → new mission)
2. **Stage 1 (Preliminary)**:
   - Distills mission: "Implement user preferences system..."
   - Creates workload with hypothetical phases
   - Analyzes pre-existing tech (finds Redis setup, etc.)
3. **Stage 2 (Planning)**:
   - Researches existing patterns
   - Identifies required technologies
4. **Stage 3 (Trajectory)**:
   - Creates detailed task breakdown
   - Registers tasks in task management system
5. **Stage 4 (Implementation)**:
   - Executes each task sequentially
   - Marks tasks complete as they finish
6. **Stage 5 (Verification)**:
   - Verifies all requirements met
   - Tests implementation
7. **Stage 6 (Post-Implementation)**:
   - Provides suggestions for future enhancements
   - Summarizes what was accomplished

---

### Example 3: Continuing Existing Mission

**User:** "Actually, use Neo4j instead of Redis for preferences"

**Augster behavior:**
- Checks task list (not empty → mission in progress)
- Applies Agility maxim (adapts to new requirement)
- Updates trajectory and tasks
- Continues implementation with new approach

## Customization

### Modifying Maxims

To add or modify maxims:

1. Edit `.augment/instructions/augster-maxims.instructions.md`
2. Add new maxim to appropriate category (Cognitive, Code Quality, Workflow)
3. Include: Mandate, Rationale (optional), Nuance (optional)
4. Save file - changes take effect immediately

**Example:**
```markdown
### MyNewMaxim
**Mandate**: Always do X when Y occurs.

**Rationale**: This ensures Z benefit.

**Nuance**: Exception applies when A condition is met.
```

### Modifying Protocols

To add or modify protocols:

1. Edit `.augment/instructions/augster-protocols.instructions.md`
2. Add new protocol with: Purpose, Guidance, OutputFormat, Example, When to Use
3. Save file - changes take effect immediately

### Modifying Workflow

To customize the workflow:

1. Edit `.augment/workflows/augster-axiomatic-workflow.prompt.md`
2. Modify stages, steps, or validation criteria
3. Maintain structure: Goal, Actions, Validation Criteria, Tools
4. Save file - changes take effect on next workflow invocation

### Creating Scoped Instructions

To create instructions that only apply to specific files:

1. Create new instruction file in `.augment/instructions/`
2. Use scoped `applyTo` pattern:
   ```yaml
   ---
   applyTo: ["src/specific-component/**/*.py"]
   priority: high
   category: component-specific
   ---
   ```
3. Write component-specific guidelines

## FAQ

### Q: How do I know if Augster is active?

**A:** Look for these signs:
- AI refers to itself as "The Augster" or "I"
- Responses use bold text for key terms
- Complex requests trigger task management
- Communication is clear and scannable
- AI exhibits proactive, autonomous behavior

### Q: Can I disable specific maxims or protocols?

**A:** Yes, but not recommended. To disable:
1. Edit the relevant instruction file
2. Comment out or remove the maxim/protocol
3. Save file

Better approach: Modify the maxim to suit your needs rather than removing it.

### Q: How do I see the task list?

**A:** The AI manages the task list automatically. To view it manually:
```bash
# The AI uses this tool internally
# You can ask: "Show me the current task list"
```

### Q: What if I want the old monolithic prompt back?

**A:** See [Migration Guide - Rollback Procedure](./augster-migration-guide.md#rollback-procedure)

### Q: Can I use Augster with other AI systems?

**A:** The modular architecture is designed for Augment Code's instruction system. For other systems:
- GitHub Copilot: May need adaptation to their instruction format
- Claude: Can use the monolithic backup as a system prompt
- Other systems: Consult their documentation for custom instructions

### Q: How do I update Augster to a new version?

**A:** Currently at v1.0.0. Future updates will be documented here with migration instructions.

### Q: Does Augster work with all programming languages?

**A:** Yes! Augster's principles (SOLID, testing, code quality) apply universally. Language-specific patterns are learned from your codebase.

### Q: Can I share my customized Augster with my team?

**A:** Yes! The modular files are part of your repository. Team members will automatically get the same Augster behavior when they use the codebase.

## Best Practices

### 1. Trust the Workflow

Let Augster follow its 6-stage workflow for complex tasks. Don't interrupt with "just do it quickly" - the workflow ensures quality.

### 2. Provide Clear Requirements

The better your initial request, the better Augster's mission distillation. Include:
- What you want accomplished
- Why it's needed
- Any constraints or preferences

### 3. Review Trajectories

When Augster presents a trajectory (detailed plan), review it before implementation begins. This is your chance to course-correct.

### 4. Use Task Management

For multi-session work, Augster's task management keeps context. Don't start fresh each time - continue the mission.

### 5. Leverage Protocols

When you need structured output or clarification, explicitly invoke protocols:
- "Use DecompositionProtocol to break this down"
- "Apply ClarificationProtocol - I need to understand X"

## Troubleshooting

See [Architecture Documentation - Troubleshooting](./augster-modular-architecture.md#troubleshooting) for common issues and solutions.

---

**Related Documentation**:
- [[TTA/Workflows/augster-modular-architecture|Architecture Documentation]]
- [[TTA/Workflows/augster-migration-guide|Migration Guide]]
- [Original Monolithic Prompt](../.augment/user_guidelines.md.backup)


---
**Logseq:** [[TTA.dev/Platform_tta_dev/Components/Augment/Core/Kb/Tta___workflows___.augment docs augster usage guide]]
