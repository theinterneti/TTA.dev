# PAF (Permanent Architectural Facts) Guidelines

## What is a PAF?

A **PAF (Permanent Architectural Fact)** is a non-negotiable architectural decision or constraint that applies to the entire project. PAFs are recorded in `PAFCORE.md` and validated programmatically via `PAFMemoryPrimitive`.

## What Qualifies as a PAF?

A fact is a PAF if it meets ALL of these criteria:

1. **Permanent**: Will remain true for foreseeable future of the project
2. **Architectural**: Affects system design, not implementation details
3. **Verifiable**: Can be objectively confirmed programmatically
4. **Non-negotiable**: Changing it would require major refactoring

## PAF Categories

### 1. Technology Stack (LANG-*)

Language choices, runtime requirements, and core dependencies.

**Examples**:
- `LANG-001`: Primary language is Python 3.12+
- `LANG-002`: Package management via `uv` (never use pip directly)
- `LANG-003`: Type hints required for all public functions

**Anti-Examples** ❌:
- "Prefer FastAPI for web services" (preference, not requirement)
- "Use snake_case for variables" (code style, not architecture)

### 2. Package Management (PKG-*)

Dependency management, package structure, and installation requirements.

**Examples**:
- `PKG-001`: Use `pyproject.toml` for dependency management
- `PKG-002`: Production dependencies via `[project.dependencies]`
- `PKG-003`: Development dependencies via `[project.optional-dependencies]`

### 3. Code Quality (QUAL-*)

Quality standards, testing requirements, and code maturity expectations.

**Examples**:
- `QUAL-001`: Minimum 80% test coverage for production code
- `QUAL-002`: All public APIs must have docstrings
- `QUAL-003`: Type safety enforced via pyright
- `QUAL-004`: Maximum file size 800 lines (production maturity)

### 4. Agent Behavior (AGENT-*)

AI agent behavior patterns and interaction protocols.

**Examples**:
- `AGENT-001`: Primitives-first composition architecture
- `AGENT-002`: Sequential composition via `>>` operator
- `AGENT-003`: Parallel composition via `|` operator

### 5. Version Control (GIT-*)

Git workflow, branching strategy, commit conventions.

**Examples**:
- `GIT-001`: Feature branches named `feat/descriptive-name`
- `GIT-002`: Conventional commits (feat/fix/docs/refactor)
- `GIT-003`: No direct commits to main branch

### 6. Testing (QA-*)

Testing frameworks, test structure, quality assurance processes.

**Examples**:
- `QA-001`: Test framework is pytest
- `QA-002`: Async tests use `@pytest.mark.asyncio`
- `QA-003`: Mock external dependencies in tests

### 7. Architecture (ARCH-*)

System architecture patterns and design principles.

**Examples**:
- `ARCH-001`: WorkflowContext for state passing
- `ARCH-002`: Observability via structured logging
- `ARCH-003`: Error handling via Result types (not exceptions)

### 8. Documentation (DOC-*)

Documentation standards and requirements.

**Examples**:
- `DOC-001`: All packages have README.md
- `DOC-002`: Public APIs documented with examples
- `DOC-003`: Architectural decisions recorded as PAFs

## Anti-Patterns: What is NOT a PAF?

❌ **Don't record as PAF**:

### 1. Implementation Details
- "Use X variable name" (too specific)
- "Function should be 20 lines max" (code style)
- "Import statements alphabetically" (formatting)

### 2. Temporary Decisions
- "Use X for now until we evaluate Y" (temporary)
- "Placeholder implementation" (transient)
- "Quick hack for demo" (not permanent)

### 3. Preferences
- "I prefer X style" (subjective)
- "X looks cleaner than Y" (aesthetic)
- "Team likes X better" (preference)

### 4. Project-Specific
- "This feature uses Redis" (feature-specific, not project-wide)
- "Dashboard component uses Chart.js" (component-level)
- "API returns JSON" (endpoint-specific)

✅ **DO record as PAF**:
- "All features must support Redis as cache backend" (architectural)
- "UI components use React" (technology choice)
- "APIs follow REST conventions" (architectural pattern)

## Creating PAFs

### 1. Identify Need

PAFs emerge from:
- Major architectural decisions
- Technology stack selections
- Quality standard agreements
- Repeated violations of unwritten rules

### 2. Validate Criteria

Before creating a PAF, ask:
- Is this permanent? (Will it change in 6 months?)
- Is this architectural? (Does it affect system design?)
- Is this verifiable? (Can we programmatically check it?)
- Is this non-negotiable? (Is changing it a major refactor?)

If all YES → Create PAF  
If any NO → Don't create PAF

### 3. Add to PAFCORE.md

```markdown
### Category Name

#### Subcategory

- **CATEGORY-###**: Description of the fact
  - Rationale: Why this decision was made
  - Verification: How to programmatically validate
  - Examples: Code showing compliance
```

### 4. Create Validation Method

```python
from tta_dev_primitives import PAFMemoryPrimitive

paf = PAFMemoryPrimitive()

# Custom validation
def validate_custom_rule(value, paf):
    # Your validation logic
    return value meets paf constraint

result = paf.validate_against_paf("CATEGORY-###", value, validate_custom_rule)
```

## Using PAFs in Code

### Validation Methods

```python
from tta_dev_primitives import PAFMemoryPrimitive

paf = PAFMemoryPrimitive()

# Validate test coverage
result = paf.validate_test_coverage(85.0)
if not result.is_valid:
    print(f"❌ Coverage violation: {result.reason}")

# Validate Python version
result = paf.validate_python_version("3.12.1")
if not result.is_valid:
    print(f"❌ Python version violation: {result.reason}")

# Validate dependency presence
result = paf.validate_dependency("pydantic>=2.0.0")
if not result.is_valid:
    print(f"❌ Dependency violation: {result.reason}")

# Validate file size
result = paf.validate_file_size("my_module.py", 750)
if not result.is_valid:
    print(f"❌ File size violation: {result.reason}")
```

### Querying PAFs

```python
from tta_dev_primitives import PAFMemoryPrimitive

paf = PAFMemoryPrimitive()

# Get specific PAF
fact = paf.get_paf("LANG-001")
print(f"{fact.full_id}: {fact.description}")

# Get all PAFs in category
lang_pafs = paf.get_pafs_by_category("LANG")
for fact in lang_pafs:
    print(f"  - {fact.description}")

# Get all active PAFs
active = paf.get_active_pafs()
print(f"Total active PAFs: {len(active)}")

# Get all validations available
validations = paf.get_all_validations()
for validation_name in validations:
    print(f"  - {validation_name}()")
```

### Via Memory Workflow

```python
from tta_dev_primitives import MemoryWorkflowPrimitive

memory = MemoryWorkflowPrimitive()

# Validate through unified interface
result = await memory.validate_paf("test-coverage", 85.0)

# Get PAFs by category
pafs = await memory.get_active_pafs(category="QUAL")
```

## PAF Lifecycle

### Active PAFs

PAFs that are currently enforced. These are stored in the main sections of PAFCORE.md and loaded into memory.

### Deprecated PAFs

When a PAF is superseded, mark it as deprecated but keep it in PAFCORE.md for historical reference:

```markdown
## Deprecated PAFs

### Historical Technology Decisions

- **LANG-001**: ~~Primary language is Python 3.10+~~ **DEPRECATED**
  - Reason: Updated to Python 3.12+ for performance and typing improvements
  - Replaced by: LANG-001-v2
  - Deprecated: 2025-08-15
```

Deprecated PAFs are NOT loaded into memory (they don't affect validation).

## Best Practices

1. **Start Minimal**: Don't over-create PAFs. Only record truly permanent decisions.

2. **Validate Regularly**: Run PAF validations in CI/CD pipeline

   ```yaml
   - name: Validate PAF Compliance
     run: |
       uv run python scripts/validate_pafs.py
   ```

3. **Document Rationale**: Always include why the decision was made

4. **Review Annually**: Review PAFs yearly to ensure they're still valid

5. **Version When Changing**: If a PAF must change, deprecate old and create new with version suffix

6. **Team Agreement**: PAFs should be team decisions, not individual preferences

7. **Programmatic Validation**: If you can't write code to validate it, it's probably not a PAF

## Examples from TTA.dev

### Good PAFs ✅

```python
# LANG-001: Python 3.12+ - Verifiable via sys.version_info
result = paf.validate_python_version("3.12.1")

# QUAL-001: 80% test coverage - Verifiable via pytest-cov
result = paf.validate_test_coverage(85.0)

# PKG-001: Use uv - Verifiable by checking pyproject.toml
result = paf.validate_dependency("uv")
```

### Bad PAFs ❌

```python
# ❌ Too specific, not architectural
"Use variable name 'df' for DataFrames"

# ❌ Preference, not verifiable
"Code should look clean"

# ❌ Temporary, not permanent
"Use placeholder API until real one is ready"

# ❌ Feature-specific, not project-wide
"Login page uses email validation"
```

## Troubleshooting

### PAF Validation Failing

1. Check if PAF exists: `paf.get_paf("CATEGORY-###")`
2. Verify PAFCORE.md syntax is correct
3. Ensure PAF is not deprecated
4. Check validation method matches PAF type

### PAFCORE.md Not Found

1. Verify file exists at `.universal-instructions/paf/PAFCORE.md`
2. Check current working directory
3. Use explicit path: `PAFMemoryPrimitive(paf_core_path="/path/to/PAFCORE.md")`

### Custom Validation Not Working

1. Ensure validator function signature is correct: `(value, paf) -> bool`
2. Check that PAF ID matches exactly
3. Verify PAF is active (not deprecated)
