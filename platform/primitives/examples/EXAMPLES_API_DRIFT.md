# Example Files - API Drift Notice

**Status:** Many example files in this directory have **API drift** and will not pass Pyright type checking.

## Issue

These examples were written for an earlier version of the TTA.dev primitives API and have not been updated to match the current API signatures.

### Common Issues

1. **CachePrimitive**: Uses `ttl=` and `max_size=` instead of `ttl_seconds=` and requires `primitive=` and `cache_key_fn=` parameters
2. **RouterPrimitive**: Uses `default_route=` instead of requiring `router_fn=` parameter
3. **RetryPrimitive**: Uses `max_attempts=`, `backoff_factor=` instead of correct parameter names
4. **ConditionalPrimitive**: Uses `if_true=`, `if_false=` instead of `then_primitive=`, `else_primitive=`
5. **LambdaPrimitive**: Used in ParallelPrimitive but type doesn't match WorkflowPrimitive requirement

## Files Affected

### High Priority (20+ errors)

- `real_world_workflows.py` - 20 errors

### Medium Priority (15+ errors)

- `orchestration_pr_review.py` - 17 errors
- `orchestration_doc_generation.py` - 17 errors
- `orchestration_test_generation.py` - 16 errors

### Lower Priority (10+ errors)

- `cost_optimization.py` - 10 errors
- `free_flagship_models.py` - errors
- `observability_demo.py` - errors
- `speckit_validation_gate_example.py` - 8 errors

## Action Required

These examples need to be updated to match the current API or removed. Until then:

**⚠️ DO NOT USE THESE EXAMPLES AS REFERENCE** - They will not work with the current API.

**✅ USE THESE INSTEAD:**

- Phase 3 examples in `examples/` (validated, type-safe)
- Package README examples
- Test files in `tests/` directory

## Resolution Plan

1. **Short term:** Mark examples as broken (this file)
2. **Medium term:** Fix high-priority examples (real_world_workflows.py, orchestration_*.py)
3. **Long term:** Update all examples or create new validated examples

## Tracking

See GitHub issue: [TODO: Create issue]

Last updated: November 5, 2025
