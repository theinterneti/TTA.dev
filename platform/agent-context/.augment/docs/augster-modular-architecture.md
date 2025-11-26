---
title: "Augster Modular Architecture"
version: "1.0.0"
last_updated: "2025-10-26"
status: "Active"
---
# Augster Modular Architecture

This document describes the modular refactoring of the AugsterSystemPrompt from a monolithic user guideline into a collection of focused, maintainable instruction files.

## Overview

The Augster identity and behavior system has been decomposed from a single 104-line XML-based user guideline into **7 instruction files** and **1 workflow template**, organized by functional concern.

### Design Principles

1. **Separation of Concerns**: Each file addresses a distinct aspect of Augster behavior
2. **Always-Active Core**: Identity, communication, maxims, protocols, heuristics, and operational loop are always active
3. **Workflow-Based Execution**: Complex multi-stage workflow is invoked as needed
4. **Maintainability**: Smaller, focused files are easier to update and understand
5. **Compatibility**: Works with Augment Code's instruction loading system

## Component Map

### Monolithic → Modular Breakdown

| Original Section | New File | Type | Lines | Priority |
|-----------------|----------|------|-------|----------|
| `<Glossary>` | `augster-core-identity.instructions.md` | Instruction | ~100 | High |
| `<YourIdentity>` | `augster-core-identity.instructions.md` | Instruction | ~100 | High |
| `<YourPurpose>` | `augster-core-identity.instructions.md` | Instruction | ~100 | High |
| `<YourCommunicationStyle>` | `augster-communication.instructions.md` | Instruction | ~150 | High |
| `<YourMaxims>` | `augster-maxims.instructions.md` | Instruction | ~180 | High |
| `<YourFavouriteHeuristics>` | `augster-heuristics.instructions.md` | Instruction | ~120 | Medium |
| `<PredefinedProtocols>` | `augster-protocols.instructions.md` | Instruction | ~200 | High |
| `<AxiomaticWorkflow>` | `augster-axiomatic-workflow.prompt.md` | Workflow | ~500 | N/A |
| `<OperationalLoop>` | `augster-operational-loop.instructions.md` | Instruction | ~120 | High |

### File Locations

```
.augment/
├── instructions/
│   ├── augster-core-identity.instructions.md       # Identity, personality, purpose, glossary
│   ├── augster-communication.instructions.md       # Communication style and formatting
│   ├── augster-maxims.instructions.md              # 13 fundamental behavioral maxims
│   ├── augster-protocols.instructions.md           # Decomposition, PAFGate, Clarification
│   ├── augster-heuristics.instructions.md          # SOLID, SWOT, other heuristics
│   └── augster-operational-loop.instructions.md    # Mission detection and workflow invocation
├── workflows/
│   └── augster-axiomatic-workflow.prompt.md        # 6-stage workflow template
└── docs/
    ├── augster-modular-architecture.md             # This file
    ├── augster-migration-guide.md                  # Migration instructions
    └── augster-usage-guide.md                      # Usage documentation
```

## Triggering Conditions

### Always-Active Instructions

These instructions are **automatically loaded** for all files via `applyTo: "**/*"`:

1. **augster-core-identity.instructions.md**
   - Defines who you are (The Augster)
   - Establishes personality traits
   - Provides key concept glossary
   - **When**: Always active

2. **augster-communication.instructions.md**
   - Governs user-facing communication
   - Formatting guidelines
   - **When**: Always active (applies to external output only)

3. **augster-maxims.instructions.md**
   - 13 fundamental behavioral rules
   - Cognitive, code quality, and workflow maxims
   - **When**: Always active

4. **augster-protocols.instructions.md**
   - Reusable procedures (Decomposition, PAFGate, Clarification)
   - **When**: Always active (invoked as needed)

5. **augster-heuristics.instructions.md**
   - SOLID, SWOT, and other frameworks
   - **When**: Always active (applied when appropriate)

6. **augster-operational-loop.instructions.md**
   - Meta-level mission detection
   - Workflow invocation logic
   - **When**: Always active (checked at start of each interaction)

### Workflow Template

**augster-axiomatic-workflow.prompt.md**
- **Type**: Workflow template (not auto-loaded)
- **When**: Invoked by operational loop when executing a Mission
- **How**: Referenced by operational loop instruction
- **Stages**: 6 stages (Preliminary, Planning, Trajectory, Implementation, Verification, Post-Implementation)

## Usage Examples

### Example 1: Starting a New Mission

**User Request**: "Implement user authentication with JWT tokens"

**System Behavior**:
1. **Operational Loop** checks task list (empty → new Mission)
2. **Core Identity** establishes Augster persona
3. **Maxims** guide behavior (PrimedCognition, EmpiricalRigor, etc.)
4. **Protocols** used for planning (DecompositionProtocol)
5. **Workflow** invoked to execute 6-stage process
6. **Communication** formats output for user

### Example 2: Continuing Existing Mission

**User Request**: "Actually, use OAuth2 instead of JWT"

**System Behavior**:
1. **Operational Loop** checks task list (not empty → continue Mission)
2. **Agility Maxim** adapts strategy to new requirement
3. **Workflow** resumes from current stage
4. **Communication** explains changes clearly

### Example 3: Storing Architectural Facts

**Discovery**: "This project uses FastAPI 0.104.0"

**System Behavior**:
1. **StrategicMemory Maxim** triggers PAF evaluation
2. **PAFGateProtocol** validates (permanent, architectural, verifiable → YES)
3. **Remember tool** stores: "Web Framework: FastAPI 0.104.0"

## Integration with Existing Systems

### Augment Code Integration

The modular architecture integrates seamlessly with Augment's existing systems:

- **Instruction Loading**: Via `conversation_manager.load_instructions()`
- **Pattern Matching**: Uses `applyTo` glob patterns
- **Importance Scoring**: Global instructions = 0.9, scoped = 0.8
- **Memory System**: PAFs stored via `remember` tool
- **Task Management**: Integrated with `add_tasks`, `update_tasks`, `reorganize_tasklist`

### Coexistence with TTA Instructions

The Augster instructions **complement** existing TTA instructions:

- **No Conflicts**: Augster heuristics reference `global.instructions.md`
- **Additive Behavior**: Augster adds meta-level orchestration
- **Shared Principles**: Both emphasize SOLID, testing, code quality

## Troubleshooting

### Issue: Instructions Not Loading

**Symptoms**: Augster behavior not observed

**Solutions**:
1. Verify files exist in `.augment/instructions/`
2. Check YAML frontmatter syntax
3. Confirm `applyTo: "**/*"` pattern
4. Review `conversation_manager.py` logs

### Issue: Workflow Not Executing

**Symptoms**: Operational loop doesn't invoke workflow

**Solutions**:
1. Check task list status via `view_tasklist`
2. Verify operational loop instruction is loaded
3. Ensure workflow file exists in `.augment/workflows/`
4. Review workflow invocation logic

### Issue: Behavioral Differences from Monolithic

**Symptoms**: Behavior differs from original AugsterSystemPrompt

**Solutions**:
1. Compare modular files against `.augment/user_guidelines.md.backup`
2. Check for missing maxims or protocols
3. Verify all 13 maxims are present in `augster-maxims.instructions.md`
4. Ensure operational loop logic matches original

### Issue: PAFs Not Being Stored

**Symptoms**: Architectural facts not remembered

**Solutions**:
1. Verify `StrategicMemory` maxim is in `augster-maxims.instructions.md`
2. Check `PAFGateProtocol` in `augster-protocols.instructions.md`
3. Ensure `remember` tool is available
4. Review PAF validation logic

## Maintenance Guidelines

### Adding New Maxims

1. Edit `augster-maxims.instructions.md`
2. Add to appropriate category (Cognitive, Code Quality, Workflow)
3. Include: Mandate, Rationale (if applicable), Nuance (if applicable)
4. Update count in verification checklist

### Modifying Protocols

1. Edit `augster-protocols.instructions.md`
2. Preserve exact output format specifications
3. Update examples if behavior changes
4. Test protocol invocation

### Updating Workflow

1. Edit `augster-axiomatic-workflow.prompt.md`
2. Maintain 6-stage structure
3. Update validation criteria if needed
4. Test workflow execution end-to-end

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-10-26 | Initial modular refactoring from monolithic prompt |

---

**Related Documentation**:
- [Migration Guide](./augster-migration-guide.md)
- [Usage Guide](./augster-usage-guide.md)
- [Original Monolithic Prompt](../.augment/user_guidelines.md.backup)
