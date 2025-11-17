# Augster System - Modular Architecture

**Status**: ✅ **MIGRATED** to modular architecture (2025-10-26)

The AugsterSystemPrompt has been refactored from a monolithic user guideline into a modular collection of instruction files for improved maintainability and clarity.

## Quick Start

The Augster identity and behavior system is now **automatically active** through the following instruction files:

### Core Instructions (Always Active)

All files are located in `.augment/instructions/` and automatically loaded via `applyTo: "**/*"`:

1. **augster-core-identity.instructions.md** - Identity, personality, purpose, key concepts
2. **augster-communication.instructions.md** - Communication style and formatting
3. **augster-maxims.instructions.md** - 13 fundamental behavioral maxims
4. **augster-protocols.instructions.md** - Reusable procedures (Decomposition, PAFGate, Clarification)
5. **augster-heuristics.instructions.md** - SOLID, SWOT, and other frameworks
6. **augster-operational-loop.instructions.md** - Mission detection and workflow invocation

### Workflow Template

- **augster-axiomatic-workflow.prompt.md** (`.augment/workflows/`) - 6-stage workflow for mission execution

## Documentation

For detailed information, see:

- **[Architecture Documentation](./docs/augster-modular-architecture.md)** - Component breakdown, triggering conditions, troubleshooting
- **[Migration Guide](./docs/augster-migration-guide.md)** - Behavioral equivalence, rollback procedure
- **[Usage Guide](./docs/augster-usage-guide.md)** - How to use and customize the modular system

## Original Monolithic Prompt

The original monolithic AugsterSystemPrompt has been preserved at:
- **`.augment/user_guidelines.md.backup`**

To restore the original monolithic version, see the [Migration Guide](./docs/augster-migration-guide.md#rollback-procedure).

## What Changed?

### Before (Monolithic)
- Single 104-line XML-based user guideline
- All components in one file
- Difficult to maintain and update

### After (Modular)
- 7 focused instruction files
- 1 workflow template
- Clear separation of concerns
- Easier to maintain and extend

## Behavioral Equivalence

The modular architecture is designed to maintain **100% behavioral equivalence** with the original monolithic prompt. All components have been preserved:

- ✅ Identity and personality traits
- ✅ Communication style
- ✅ All 13 maxims
- ✅ All 3 protocols
- ✅ SOLID and SWOT heuristics
- ✅ 6-stage Axiomatic Workflow
- ✅ Operational loop logic

## Need Help?

- **Troubleshooting**: See [Architecture Documentation](./docs/augster-modular-architecture.md#troubleshooting)
- **Customization**: See [Usage Guide](./docs/augster-usage-guide.md#customization)
- **Rollback**: See [Migration Guide](./docs/augster-migration-guide.md#rollback-procedure)

---

**Version**: 1.0.0
**Migration Date**: 2025-10-26
**Source**: Discord Augment Community
