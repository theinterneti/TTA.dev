# E2B Validation Examples

This directory contains validation scripts created during E2B template debugging (November 7, 2025).

## Working Examples ✅

- `test_template_comparison.py` - Compares default vs ML template performance
- `test_direct_sdk.py` - Direct E2B SDK validation (bypasses primitive)
- `test_primitive_integration.py` - Tests CodeExecutionPrimitive with ML template

## Usage

```bash
# Test basic E2B functionality
uv run python examples/e2b-validation/test_template_comparison.py

# Test E2B SDK directly
uv run python examples/e2b-validation/test_direct_sdk.py

# Test primitive integration (will fail with ML template currently)
uv run python examples/e2b-validation/test_primitive_integration.py
```

## Results Summary

- **Default Template**: ✅ Works perfectly (~0.6s execution)
- **ML Template**: ❌ Sandbox creates but interpreter fails (port 49999 not open)

See `E2B_INVESTIGATION_REPORT.md` for full analysis.
