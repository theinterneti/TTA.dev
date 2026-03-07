---
type: "always_apply"
description: "Maintain code modularity by enforcing file size limits and SOLID principles"
---

# File Size and Modularity Rule

**For AI Agent Use Only** - Enforce file size limits to maintain code quality, testability, and adherence to SOLID principles.

## Rule Priority

**MEDIUM** - Apply during code review, refactoring, and new feature development

## File Size Thresholds

### Soft Limit: 300-400 Lines
**Trigger:** File approaching 300-400 lines

**Action:** Consider splitting if:
- File contains multiple responsibilities
- Natural boundaries exist (e.g., multiple classes, distinct feature groups)
- Testing is becoming difficult
- Code review is challenging

**Rationale:** Files in this range are still manageable but may benefit from refactoring for clarity.

### Hard Limit: 1,000 Lines
**Trigger:** File exceeds 1,000 lines

**Action:** **MUST** split file - this is a component maturity blocker

**Rationale:** Files exceeding 1,000 lines violate Single Responsibility Principle and become:
- Unmaintainable (difficult to understand and modify)
- Untestable (too many code paths, complex dependencies)
- Architectural debt (blocks component promotion to staging/production)

**Reference:** `docs/component-maturity-assessment-2025-10-22.md` - "Maximum 1,000 lines per component"

### Statement Limit: 500 Statements
**Trigger:** File exceeds 500 executable statements

**Action:** Consider splitting even if line count is below threshold

**Rationale:** High statement count indicates complexity regardless of line count (comments, whitespace).

**Reference:** `docs/component-maturity-assessment-2025-10-22.md` - "Maximum 500 statements per component"

## Rationale

### SOLID Principles

**Single Responsibility Principle (SRP):**
- Each file should have one reason to change
- Large files typically violate SRP by handling multiple concerns
- Splitting files enforces clear separation of responsibilities

**Open-Closed Principle (OCP):**
- Smaller files are easier to extend without modification
- Clear boundaries enable extension through composition

**Interface Segregation Principle (ISP):**
- Smaller files naturally lead to focused interfaces
- Clients depend only on what they need

**Reference:** `src/agent_orchestration/PHASE1_ARCHITECTURE.md` - Layered architecture with SOLID principles

### Maintainability

**Code Understanding:**
- Developers can hold ~400 lines in working memory
- Files beyond this require scrolling, context switching
- Smaller files enable faster comprehension

**Code Review:**
- Reviewers can thoroughly review ~300-400 lines
- Larger files lead to superficial reviews, missed issues

**Testing:**
- Smaller files have fewer code paths
- Easier to achieve high test coverage
- Simpler to write focused unit tests

### Component Maturity

**Promotion Blockers:**
- Files >1,000 lines block staging promotion
- Component maturity workflow requires refactoring before advancement
- Technical debt compounds exponentially with file size

**Reference:** `docs/development/COMPONENT_MATURITY_WORKFLOW.md` - Quality gates for promotion

## When to Split Files

### Trigger Conditions

1. **File exceeds 1,000 lines** - MANDATORY split
2. **File exceeds 500 statements** - MANDATORY split
3. **File approaching 300-400 lines AND:**
   - Contains multiple classes
   - Handles multiple features/concerns
   - Has low cohesion (unrelated functions)
   - Testing is difficult
   - Code review is challenging

### Signs of Poor Cohesion

- Multiple import groups (different domains)
- Functions/classes that don't interact
- Distinct feature groups (e.g., CRUD + validation + reporting)
- Mixed abstraction levels (high-level orchestration + low-level utilities)

### Natural Split Boundaries

- **Multiple classes** → One class per file
- **Feature groups** → One feature per file
- **Layers** → Separate business logic, data access, presentation
- **Utilities** → Group related utilities, split by domain

## How to Split Files

### Step-by-Step Process

1. **Identify Responsibilities**
   - List all distinct responsibilities in the file
   - Group related functions/classes
   - Identify dependencies between groups

2. **Design New Structure**
   - Create one file per responsibility
   - Define clear interfaces between files
   - Plan import structure (avoid circular dependencies)

3. **Create New Files**
   - Extract each responsibility to its own file
   - Maintain clear naming conventions
   - Preserve docstrings and comments

4. **Update Imports**
   - Update all files that import from the original file
   - Use `codebase-retrieval` to find all import sites
   - Verify no circular dependencies introduced

5. **Create Backward Compatibility Shim (Optional)**
   - Keep original file as re-export shim
   - Gradually migrate callers to new files
   - Deprecate and remove shim after migration

6. **Update Tests**
   - Split tests to match new file structure
   - Ensure test coverage is maintained
   - Run full test suite to verify no regressions

7. **Update Documentation**
   - Update component README
   - Update architecture diagrams
   - Document migration path if using shim

**Reference:** `src/agent_orchestration/PHASE1_ARCHITECTURE.md` - Example of splitting 3,529-line file into 4 focused components

## Examples

### Example 1: Multiple Classes

**Before (450 lines):**
```python
# src/components/user_management.py

class UserValidator:
    """Validates user input."""
    # 150 lines

class UserRepository:
    """Handles user data persistence."""
    # 150 lines

class UserService:
    """Business logic for user operations."""
    # 150 lines
```

**After:**
```python
# src/components/user_management/validator.py
class UserValidator:
    """Validates user input."""
    # 150 lines

# src/components/user_management/repository.py
class UserRepository:
    """Handles user data persistence."""
    # 150 lines

# src/components/user_management/service.py
class UserService:
    """Business logic for user operations."""
    # 150 lines

# src/components/user_management/__init__.py
from .validator import UserValidator
from .repository import UserRepository
from .service import UserService

__all__ = ["UserValidator", "UserRepository", "UserService"]
```

### Example 2: Feature Groups

**Before (600 lines):**
```python
# src/components/api_handlers.py

# Authentication handlers (200 lines)
async def login_handler(): ...
async def logout_handler(): ...
async def refresh_token_handler(): ...

# User CRUD handlers (200 lines)
async def create_user_handler(): ...
async def get_user_handler(): ...
async def update_user_handler(): ...

# Admin handlers (200 lines)
async def admin_dashboard_handler(): ...
async def admin_users_handler(): ...
async def admin_settings_handler(): ...
```

**After:**
```python
# src/components/api/auth_handlers.py
async def login_handler(): ...
async def logout_handler(): ...
async def refresh_token_handler(): ...

# src/components/api/user_handlers.py
async def create_user_handler(): ...
async def get_user_handler(): ...
async def update_user_handler(): ...

# src/components/api/admin_handlers.py
async def admin_dashboard_handler(): ...
async def admin_users_handler(): ...
async def admin_settings_handler(): ...
```

### Example 3: Layered Architecture

**Before (800 lines):**
```python
# src/components/payment_processing.py

# Data models (100 lines)
class Payment(BaseModel): ...
class Transaction(BaseModel): ...

# Repository layer (200 lines)
class PaymentRepository: ...

# Business logic (300 lines)
class PaymentService: ...

# API handlers (200 lines)
async def process_payment_handler(): ...
async def refund_payment_handler(): ...
```

**After:**
```python
# src/components/payment/models.py
class Payment(BaseModel): ...
class Transaction(BaseModel): ...

# src/components/payment/repository.py
class PaymentRepository: ...

# src/components/payment/service.py
class PaymentService: ...

# src/components/payment/handlers.py
async def process_payment_handler(): ...
async def refund_payment_handler(): ...
```

## Exceptions

### When NOT to Split

1. **Generated Code**
   - Auto-generated files (e.g., protobuf, GraphQL schemas)
   - Migration files
   - Lock files

2. **Data Files**
   - Configuration files (YAML, JSON)
   - Test fixtures
   - Seed data

3. **Single Cohesive Class**
   - Large class with high cohesion (all methods closely related)
   - Consider splitting class first before accepting large file
   - Document rationale if keeping large file

4. **Framework Constraints**
   - Framework requires specific file structure
   - Single-file deployment requirements
   - Document constraint and plan for future refactoring

### Handling Exceptions

- **Document rationale** in file header comment
- **Add TODO** with issue number for future refactoring
- **Track as technical debt** in component maturity tracking
- **Plan migration path** for when constraint is removed

## Integration with Component Maturity Workflow

### Development → Staging Promotion

**Blocker:** Files >1,000 lines or >500 statements

**Resolution:**
1. Identify files exceeding thresholds
2. Create refactoring plan (see "How to Split Files")
3. Execute refactoring
4. Verify tests pass and coverage maintained
5. Update component MATURITY.md
6. Proceed with promotion

**Reference:** `docs/development/COMPONENT_MATURITY_WORKFLOW.md` - Exit criteria for staging promotion

### Continuous Monitoring

**Pre-commit Hooks:**
- Consider adding file size checks to pre-commit hooks
- Warn on files approaching thresholds
- Block commits for files exceeding hard limits

**Component Maturity Tracking:**
- Track file sizes in component MATURITY.md
- Include in promotion criteria checklists
- Monitor trends (files growing over time)

## Related Documentation

- **Component Maturity:** `docs/component-maturity-assessment-2025-10-22.md` - File size limits and rationale
- **Maturity Workflow:** `docs/development/COMPONENT_MATURITY_WORKFLOW.md` - Promotion criteria
- **Architecture Example:** `src/agent_orchestration/PHASE1_ARCHITECTURE.md` - Splitting large files with SOLID principles
- **Monorepo Structure:** `docs/architecture/monorepo-restructuring-summary.md` - Package organization

## Summary

**Soft limit:** 300-400 lines - Consider splitting for clarity and maintainability

**Hard limit:** 1,000 lines or 500 statements - MUST split (component maturity blocker)

**Rationale:** SOLID principles, maintainability, testability, component maturity

**Process:** Identify responsibilities → Design structure → Extract files → Update imports → Update tests → Update docs

**Exceptions:** Generated code, data files, framework constraints (document rationale)

---

**Status:** Active (Enforced via Component Maturity Workflow)
**Last Updated:** 2025-10-22
**Related Rules:** `integrated-workflow.md`, `use-serena-tools.md`


---
**Logseq:** [[TTA.dev/Platform_tta_dev/Components/Augment/Core/Rules/Avoid-long-files]]
