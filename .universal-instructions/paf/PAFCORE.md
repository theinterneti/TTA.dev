# Permanent Architectural Facts (PAF) - Core Registry

**Purpose**: Store atomic, immutable architectural constraints and decisions that form the permanent foundation of the TTA.dev project.

**Last Updated**: 2025-10-28
**Status**: Active
**Validation**: Required before modification

---

## What are PAFs?

Permanent Architectural Facts (PAFs) are:

- **Atomic**: Single, indivisible facts
- **Immutable**: Once established, they don't change (only deprecate and replace)
- **Verifiable**: Can be confirmed by inspection or testing
- **Architectural**: Define system structure, not implementation details

## PAF Categories

### 1. Technology Stack

#### Core Languages
- **LANG-001**: Primary language is Python 3.12+
- **LANG-002**: Package management via `uv`
- **LANG-003**: Type checking via `pyright`
- **LANG-004**: Code formatting via `ruff`

### 2. Package Structure

#### Workspace Organization
- **PKG-001**: Monorepo structure using workspace pattern
- **PKG-002**: Packages located in `packages/` directory
- **PKG-003**: Each package has independent `pyproject.toml`
- **PKG-004**: Shared dependencies managed at workspace root

### 3. Code Quality

#### Testing Requirements
- **QUAL-001**: Minimum 70% test coverage for production code
- **QUAL-002**: All public APIs must have docstrings
- **QUAL-003**: Type hints required for all function signatures

#### File Organization
- **QUAL-004**: Maximum file size 800 lines (production maturity)
- **QUAL-005**: One class per file for component implementations
- **QUAL-006**: SOLID principles enforced

### 4. Agent Behavior

#### Instruction System
- **AGENT-001**: Universal instructions in `.universal-instructions/`
- **AGENT-002**: YAML frontmatter required for all instruction files
- **AGENT-003**: Auto-generation system via primitives
- **AGENT-004**: Hub pattern: AGENTS.md, CLAUDE.md at repository root

### 5. Development Workflow

#### Git Conventions
- **GIT-001**: Conventional commits enforced (feat, fix, docs, etc.)
- **GIT-002**: Feature branches follow `feat/*`, `fix/*` pattern
- **GIT-003**: Main branch protected, requires PR

#### Quality Gates
- **QA-001**: All code must pass `ruff format` and `ruff check`
- **QA-002**: Type checking via `pyright` must pass
- **QA-003**: Tests must pass before merge

### 6. Architecture Patterns

#### Primitives Pattern
- **ARCH-001**: Primitives inherit from `WorkflowPrimitive[I, O]`
- **ARCH-002**: Composition via `>>` and `|` operators
- **ARCH-003**: WorkflowContext threading for observability
- **ARCH-004**: Result types wrap outputs with metadata

#### Session Management
- **ARCH-005**: Session state uses `AIConversationContextManager`
- **ARCH-006**: Memory system uses `.memory.md` files with YAML frontmatter
- **ARCH-007**: Four-layer memory hierarchy: Session → Cache → Deep → PAF

### 7. Documentation

#### Standards
- **DOC-001**: All packages require README.md with examples
- **DOC-002**: Architecture decisions documented in `.memory.md` files
- **DOC-003**: API documentation auto-generated from docstrings

---

## PAF Validation Rules

### Adding a New PAF

1. **Verify it's truly permanent** - Will this constraint last 12+ months?
2. **Verify it's atomic** - Can it be stated in one clear sentence?
3. **Verify it's verifiable** - Can we test/prove this fact?
4. **Verify it's architectural** - Does it define system structure?

### PAF Lifecycle

```
PROPOSED → REVIEW → ACTIVE → [DEPRECATED] → REPLACED
```

- **PROPOSED**: New PAF under consideration
- **REVIEW**: Team review in progress
- **ACTIVE**: Enforced and validated
- **DEPRECATED**: Still in code but being phased out
- **REPLACED**: Superseded by new PAF (reference included)

### Deprecating a PAF

When a PAF must change:

1. Create new PAF with different ID
2. Mark old PAF as **DEPRECATED** with reason
3. Reference new PAF in deprecation notice
4. Update all implementations
5. After 1 release cycle, mark as **REPLACED**

Example:
```markdown
- **LANG-001**: ~~Primary language is Python 3.10+~~ **DEPRECATED**
  - Reason: Python 3.12 required for new features
  - Replaced by: LANG-001-v2
  - Date: 2025-10-28
```

---

## Usage in Code

### PAF Primitive (Auto-loaded)

The `PAFMemoryPrimitive` automatically loads and validates PAFs:

```python
from tta_dev_primitives import PAFMemoryPrimitive

paf_primitive = PAFMemoryPrimitive()

# Validate against PAF
result = await paf_primitive.validate_against_paf(
    category="LANG",
    fact_id="001",
    actual_value="Python 3.12.0"
)

if result.is_valid:
    print("✅ Complies with PAF-LANG-001")
else:
    print(f"❌ Violates PAF-LANG-001: {result.reason}")
```

### PAF in Workflows

PAFs are automatically checked during:

- Package initialization
- Quality gate validation
- Pre-commit hooks
- CI/CD pipelines

---

## PAF Registry Index

Total Active PAFs: 22

By Category:
- Technology Stack: 4
- Package Structure: 4
- Code Quality: 6
- Agent Behavior: 4
- Development Workflow: 6
- Architecture Patterns: 7
- Documentation: 3

---

## References

- **Augster PAFGateProtocol**: `.universal-instructions/augster-specific/protocols.md`
- **Memory System**: `docs/guides/SESSION_MEMORY_INTEGRATION_PLAN.md`
- **Quality Gates**: `scripts/validate-quality-gates.sh`

---

**Note**: This is a living document. Propose new PAFs via PR with justification and team review.
