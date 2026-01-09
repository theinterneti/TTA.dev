---
title: Phase 2: Testing and Integration Guide
tags: #TTA
status: Active
repo: theinterneti/TTA
path: PHASE_2_TESTING_AND_INTEGRATION_GUIDE.md
created: 2025-11-01
updated: 2025-11-01
---
# [[TTA/Workflows/Phase 2: Testing and Integration Guide]]

**Status**: Ready for Testing
**Date**: 2025-10-27
**Phase**: Phase 2 - Async OpenHands Integration

## Priority Order for Next Steps

### 1. Testing (Highest Priority) ⚡

#### Unit Tests
**File**: `tests/workflow/test_async_openhands_integration.py` ✅ Created

**Test Coverage**:
- ✅ `AsyncOpenHandsStageResult` dataclass
- ✅ `AsyncOpenHandsTestGenerationStage.submit_tasks()`
- ✅ `AsyncOpenHandsTestGenerationStage.collect_results()`
- ✅ `WorkflowOrchestrator._run_async_openhands_test_generation_stage()`
- ✅ `WorkflowOrchestrator._collect_async_openhands_results()`
- ✅ Performance measurement fields in `WorkflowResult`

**Run Tests**:
```bash
# Run async workflow tests
uv run pytest tests/workflow/test_async_openhands_integration.py -v

# Run with coverage
uv run pytest tests/workflow/test_async_openhands_integration.py \
    --cov=scripts.workflow.openhands_stage \
    --cov=scripts.workflow.spec_to_production \
    --cov-report=html

# Run all workflow tests
uv run pytest tests/workflow/ -v
```

#### Integration Tests (Recommended)
**File**: `tests/integration/test_async_workflow_integration.py` (To be created)

**Test Scenarios**:
1. **End-to-End Async Workflow**: Full workflow with mock OpenHands
2. **Parallel Execution**: Verify refactoring runs while OpenHands tasks execute
3. **Timeout Handling**: Test timeout scenarios for task collection
4. **Error Recovery**: Test circuit breaker and retry logic
5. **Performance Comparison**: Compare sync vs async execution times

**Create Integration Test**:
```bash
# Create integration test file
cat > tests/integration/test_async_workflow_integration.py << 'EOF'
"""Integration tests for async OpenHands workflow."""

import asyncio
import pytest
from pathlib import Path
from scripts.workflow.spec_to_production import WorkflowOrchestrator

@pytest.mark.integration
@pytest.mark.asyncio
async def test_async_workflow_end_to_end(tmp_path):
    """Test complete async workflow execution."""
    # Setup test component
    spec_file = tmp_path / "spec.md"
    spec_file.write_text("# Test Component\n\n## Requirements\n- Req 1")

    component_path = tmp_path / "component"
    component_path.mkdir()
    (component_path / "module.py").write_text("def func(): pass")

    # Create orchestrator
    orchestrator = WorkflowOrchestrator(
        spec_file=spec_file,
        component_name="test_component",
        target_stage="development",
        component_path=component_path,
        config={"enable_openhands_test_generation": False}  # Disable for test
    )

    # Run async workflow
    result = await orchestrator.run_async_with_parallel_openhands()

    # Verify result
    assert result is not None
    assert result.execution_mode == "async"
    assert "specification" in result.stage_timings
EOF
```

---

### 2. CLI Integration (High Priority) 🔧

#### Add Async Mode Flag

**File**: `scripts/workflow/spec_to_production.py` (Update `main()` function)

**Recommended Approach**:
```python
def main():
    """Main entry point for workflow execution."""
    parser = argparse.ArgumentParser(
        description="Run spec-to-production workflow"
    )
    parser.add_argument("--spec", required=True, help="Path to specification file")
    parser.add_argument("--component", required=True, help="Component name")
    parser.add_argument("--target", required=True,
                       choices=["development", "staging", "production"])
    parser.add_argument("--async", dest="async_mode", action="store_true",
                       help="Use async workflow with parallel OpenHands execution")
    parser.add_argument("--enable-openhands", action="store_true",
                       help="Enable OpenHands test generation")

    args = parser.parse_args()

    config = {
        "enable_openhands_test_generation": args.enable_openhands,
        "coverage_threshold": 80,
    }

    if args.async_mode:
        # Run async workflow
        result = asyncio.run(run_async_workflow(
            spec_file=Path(args.spec),
            component_name=args.component,
            target_stage=args.target,
            config=config
        ))
    else:
        # Run sync workflow (existing)
        result = run_workflow(
            spec_file=Path(args.spec),
            component_name=args.component,
            target_stage=args.target,
            config=config
        )

    # Print results...
```

**Usage Examples**:
```bash
# Sync workflow (existing)
python scripts/workflow/spec_to_production.py \
    --spec specs/my_component.md \
    --component my_component \
    --target staging

# Async workflow (new)
python scripts/workflow/spec_to_production.py \
    --spec specs/my_component.md \
    --component my_component \
    --target staging \
    --async \
    --enable-openhands
```

---

### 3. Validation (Medium Priority) ✓

#### End-to-End Validation

**Recommended Test Component**: Use a small, well-defined component

**Option 1: Create Test Component**
```bash
# Create test component
mkdir -p src/test_components/calculator
cat > src/test_components/calculator/operations.py << 'EOF'
"""Simple calculator operations for testing."""

def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b

def subtract(a: int, b: int) -> int:
    """Subtract b from a."""
    return a - b

def multiply(a: int, b: int) -> int:
    """Multiply two numbers."""
    return a * b

def divide(a: int, b: int) -> float:
    """Divide a by b."""
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b
EOF

# Create specification
cat > specs/calculator_operations.md << 'EOF'
# Calculator Operations Component

## Overview
Simple calculator operations for testing async workflow.

## Requirements
- Addition operation
- Subtraction operation
- Multiplication operation
- Division operation with zero check

## Testing Requirements
- Test all operations
- Test edge cases (division by zero)
- Achieve 80% coverage
EOF
```

**Option 2: Use Existing Small Component**
```bash
# Find small components suitable for testing
find src/ -name "*.py" -type f -exec wc -l {} + | sort -n | head -20
```

**Run Validation**:
```bash
# Test async workflow with test component
python scripts/workflow/spec_to_production.py \
    --spec specs/calculator_operations.md \
    --component calculator_operations \
    --target development \
    --async \
    --enable-openhands

# Check results
cat workflow_report_calculator_operations.json | jq '.execution_mode, .stage_timings'
```

---

### 4. Documentation Updates (Low Priority) 📝

#### Files to Update

**1. Main README** (if exists)
- Add async workflow usage examples
- Document `--async` flag
- Explain performance benefits

**2. Workflow Documentation**
```bash
# Update workflow documentation
cat >> docs/development/WORKFLOW_USAGE.md << 'EOF'

## Async Workflow Execution (Phase 2)

The async workflow enables parallel execution of independent stages while OpenHands
test generation tasks run in the background.

### Benefits
- Reduced total workflow time
- Non-blocking test generation
- Parallel stage execution
- Detailed performance metrics

### Usage
```bash
python scripts/workflow/spec_to_production.py \
    --spec specs/my_component.md \
    --component my_component \
    --target staging \
    --async \
    --enable-openhands
```

### Performance Metrics
The async workflow tracks:
- Individual stage execution times
- OpenHands task submission time
- OpenHands result collection time
- Total workflow execution time
- Parallel execution savings

See `PHASE_2_IMPLEMENTATION_SUMMARY.md` for details.
EOF
```

**3. API Documentation**
- Document `run_async_with_parallel_openhands()` method
- Document `AsyncOpenHandsTestGenerationStage` class
- Document performance measurement fields

---

### 5. Phase 3 Decision (Lowest Priority) 🤔

**Recommendation**: **Validate Phase 2 first** before proceeding to Phase 3

**Validation Checklist**:
- [ ] Unit tests passing
- [ ] Integration tests passing
- [ ] End-to-end validation successful
- [ ] Performance metrics showing improvement
- [ ] No regressions in existing functionality
- [ ] Documentation updated
- [ ] Team review completed

**Phase 3 Scope** (Optional):
- Task priority management
- Advanced scheduling
- Result caching
- Performance monitoring dashboard

**Decision Point**: After Phase 2 validation is complete, assess:
1. Is Phase 2 meeting performance goals?
2. Are there specific bottlenecks that Phase 3 would address?
3. Is the added complexity of Phase 3 justified?

---

## Quick Start Testing

### 1. Run Unit Tests
```bash
uv run pytest tests/workflow/test_async_openhands_integration.py -v
```

### 2. Create Integration Test
```bash
# Copy template from this guide
# Customize for your needs
uv run pytest tests/integration/test_async_workflow_integration.py -v
```

### 3. Validate with Test Component
```bash
# Create test component (see Option 1 above)
# Run async workflow
# Verify results
```

### 4. Compare Performance
```bash
# Run sync workflow
time python scripts/workflow/spec_to_production.py \
    --spec specs/test.md --component test --target dev

# Run async workflow
time python scripts/workflow/spec_to_production.py \
    --spec specs/test.md --component test --target dev --async
```

---

## Success Criteria

### Phase 2 Validation Complete When:
- ✅ All unit tests passing
- ✅ Integration tests passing
- ✅ End-to-end validation successful
- ✅ Performance improvement demonstrated
- ✅ No regressions in existing workflows
- ✅ Documentation complete
- ✅ CLI integration working

---

## Troubleshooting

### Tests Failing
1. Check mock setup is correct
2. Verify async/await syntax
3. Check import paths
4. Review error messages

### Integration Issues
1. Verify OpenHands SDK is available
2. Check environment variables
3. Review circuit breaker configuration
4. Check timeout settings

### Performance Issues
1. Review timing instrumentation
2. Check for blocking operations
3. Verify parallel execution
4. Monitor resource usage

---

**Next Action**: Run unit tests to validate Phase 2 implementation


---
**Logseq:** [[TTA.dev/Platform_tta_dev/Components/Augment/Core/Kb/Tta___workflows___phase 2 testing and integration guide document]]
