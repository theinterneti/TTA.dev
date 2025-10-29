# Workflow Profiles - Execution Modes for AI Agents

**Purpose**: Define different workflow execution modes for varying contexts - from rapid prototyping to rigorous production development.

**Last Updated**: 2025-10-28
**Status**: Active

---

## Overview

AI agents can operate in different modes depending on the task context. These workflow profiles define the level of rigor, validation, and process adherence required.

## Profile Levels

### 1. Rapid Mode (`rapid`)

**Use Case**: Rapid prototyping, exploration, proof-of-concept

**Characteristics**:
- Minimal validation
- Skip extensive documentation
- Fast iteration
- Accept higher risk
- Streamlined stages

**Stages**: Understand → Implement → Quick Test

**Example Tasks**:
- Testing an idea quickly
- Creating throwaway prototypes
- Exploratory coding

**Quality Gates**: Minimal (syntax only)

---

### 2. Standard Mode (`standard`) ⭐ **DEFAULT**

**Use Case**: Regular development, feature implementation

**Characteristics**:
- Balanced rigor
- Standard documentation
- Normal iteration speed
- Moderate risk acceptance
- Core stages with selective depth

**Stages**: Understand → Decompose → Plan → Implement → Validate

**Example Tasks**:
- Feature implementation
- Bug fixes
- Routine development

**Quality Gates**: Standard (format, lint, basic tests)

---

### 3. Augster-Rigorous Mode (`augster-rigorous`)

**Use Case**: Production-critical work, architectural decisions, safety-critical features

**Characteristics**:
- Maximum rigor
- Comprehensive documentation
- Thorough validation
- Minimal risk tolerance
- Full 6-stage workflow

**Stages**: Understand → Decompose → Plan → Implement → Validate → Reflect

**Example Tasks**:
- Architectural changes
- Production releases
- Security-critical features
- Therapeutic safety features (for TTA)

**Quality Gates**: Comprehensive (format, lint, type-check, tests, coverage, documentation)

---

## Workflow Stage Mapping

### Rapid Mode (3 Stages)

1. **Understand** (Quick)
   - Minimal context gathering
   - Basic requirements
   - No memory loading

2. **Implement** (Fast)
   - Direct implementation
   - Skip decomposition
   - Minimal planning

3. **Quick Test** (Basic)
   - Syntax check only
   - Manual testing
   - No automated tests required

### Standard Mode (5 Stages)

1. **Understand** (Normal)
   - Standard context gathering
   - Load recent memories
   - Review relevant PAFs

2. **Decompose** (Light)
   - Break down into components
   - Identify dependencies
   - Estimate complexity

3. **Plan** (Standard)
   - Create implementation plan
   - Identify risks
   - Select approach

4. **Implement** (Normal)
   - Follow plan
   - Write tests alongside
   - Document as needed

5. **Validate** (Standard)
   - Run linters and formatters
   - Run tests
   - Basic quality gates

### Augster-Rigorous Mode (6 Stages)

1. **Understand** (Deep)
   - Comprehensive context gathering
   - Load all relevant memories
   - Review all applicable PAFs
   - Consult PAFCORE for constraints
   - Load workflow context from similar tasks

2. **Decompose** (Thorough)
   - Complete task decomposition
   - Identify all dependencies
   - Risk assessment
   - SWOT analysis
   - Complexity estimation

3. **Plan** (Detailed)
   - Detailed implementation plan
   - Test strategy
   - Documentation strategy
   - Rollback plan
   - PAF compliance check

4. **Implement** (Careful)
   - Follow plan strictly
   - Test-driven development
   - Comprehensive documentation
   - Code review checkpoints
   - Continuous PAF validation

5. **Validate** (Comprehensive)
   - All quality gates
   - Full test suite
   - Coverage requirements
   - Type checking
   - Security scan
   - Documentation review

6. **Reflect** (Learning)
   - Capture learnings
   - Update memories
   - Document patterns
   - Identify improvements
   - Update PAFs if needed

---

## Memory Layer Integration

Each workflow mode uses different memory layers:

### Rapid Mode
- **Session Context**: Current execution only
- **Cache Memory**: Not used
- **Deep Memory**: Not loaded
- **PAF Store**: Not validated

### Standard Mode
- **Session Context**: Current execution + recent history
- **Cache Memory**: Last hour (if available)
- **Deep Memory**: Top 5 relevant memories
- **PAF Store**: Validate against active PAFs

### Augster-Rigorous Mode
- **Session Context**: Full session history + grouped sessions
- **Cache Memory**: Last 24 hours
- **Deep Memory**: Top 20 relevant memories (all categories)
- **PAF Store**: Validate against all PAFs + propose new ones

---

## Switching Modes

### Automatic Mode Detection

The system can automatically select mode based on:

- **File patterns**: `*.test.py` → Standard, `src/core/*` → Augster-Rigorous
- **Task keywords**: "prototype" → Rapid, "production" → Augster-Rigorous
- **Component maturity**: Development → Rapid, Staging → Standard, Production → Augster-Rigorous

### Manual Mode Selection

```bash
# Via environment variable
export WORKFLOW_MODE="augster-rigorous"

# Via CLI flag
ai-agent --workflow-mode rapid task.md

# Via inline directive
# workflow-mode: augster-rigorous
```

### In Code

```python
from tta_dev_primitives import WorkflowContext

context = WorkflowContext(
    workflow_id="feature-xyz",
    session_id="session-123",
    workflow_mode="augster-rigorous"  # Explicit mode
)
```

---

## Quality Gates by Mode

### Rapid Mode
- ✅ Syntax valid (ruff format)
- ⏭️ Skip linting
- ⏭️ Skip type checking
- ⏭️ Skip tests

### Standard Mode (Default)
- ✅ Format valid (ruff format)
- ✅ Lint passing (ruff check)
- ✅ Basic type hints present
- ✅ Unit tests passing
- ⏭️ Skip coverage check

### Augster-Rigorous Mode
- ✅ Format valid (ruff format)
- ✅ Lint passing (ruff check)
- ✅ Type checking passing (pyright)
- ✅ All tests passing
- ✅ Coverage ≥70% (PAF-QUAL-001)
- ✅ File size ≤800 lines (PAF-QUAL-004)
- ✅ Documentation complete
- ✅ Security scan passing

---

## Examples

### Rapid Mode Example

```python
# Quick test of an idea
def rapid_prototype():
    """Quick test - no extensive validation needed."""
    # Implement quickly
    result = do_something()
    print(result)  # Manual validation
    return result
```

### Standard Mode Example

```python
# Regular feature implementation
def standard_feature(data: dict) -> Result:
    """Standard feature with normal quality gates.

    Args:
        data: Input data dictionary

    Returns:
        Result object with processed data
    """
    # Proper implementation
    processed = process_data(data)
    return Result(processed)

def test_standard_feature():
    """Test for standard feature."""
    result = standard_feature({"key": "value"})
    assert result.is_valid
```

### Augster-Rigorous Mode Example

```python
# Production-critical implementation
class ProductionFeature:
    """Production-critical feature with full rigor.

    This class handles [critical functionality] and requires:
    - Comprehensive testing
    - Full type coverage
    - Security validation
    - PAF compliance

    Attributes:
        config: Configuration object
        validator: Security validator

    Examples:
        >>> feature = ProductionFeature(config)
        >>> result = feature.execute(data)
        >>> assert result.is_secure
    """

    def __init__(self, config: Config) -> None:
        """Initialize with validated configuration.

        Args:
            config: Validated configuration object

        Raises:
            ValidationError: If config violates PAFs
        """
        # Validate against PAFs
        paf_primitive = PAFMemoryPrimitive()
        # ... comprehensive validation

    def execute(self, data: SecureData) -> SecureResult:
        """Execute feature with full validation.

        Args:
            data: Validated and sanitized input

        Returns:
            Validated result with audit trail

        Raises:
            SecurityError: If security constraints violated
            ValidationError: If PAF constraints violated
        """
        # Comprehensive implementation
        # with security checks, logging, etc.
        pass

# Comprehensive test suite
class TestProductionFeature:
    """Comprehensive tests for production feature."""

    def test_normal_case(self): ...
    def test_edge_cases(self): ...
    def test_error_cases(self): ...
    def test_security_constraints(self): ...
    def test_paf_compliance(self): ...
    # ... 70%+ coverage
```

---

## References

- **PAF System**: `.universal-instructions/paf/PAFCORE.md`
- **Augster Workflow**: `.universal-instructions/augster-specific/workflows/axiomatic-workflow.md`
- **Memory System**: `docs/guides/SESSION_MEMORY_INTEGRATION_PLAN.md`
- **Quality Gates**: `scripts/validate-quality-gates.sh`

---

**Current Default**: `standard` mode
**Override**: Set `WORKFLOW_MODE` environment variable or `workflow_mode` in WorkflowContext
