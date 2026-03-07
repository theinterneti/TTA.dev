# LangFuse Observability Consolidation

## Overview

This document tracks the consolidation of two separate LangFuse implementations into a unified observability solution for TTA.dev.

## Problem

We had two competing LangFuse implementations:
1. `platform/apm/langfuse/` - Dedicated APM package with `@observe` decorator support
2. `platform/observability/src/observability_integration/langfuse_integration.py` - Embedded LLM tracking

This caused:
- Confusion about which to use
- Duplicated code
- Inconsistent tracing patterns
- Maintenance overhead

## Solution

**Primary Implementation:** `platform/apm/langfuse/`

This package becomes the canonical LangFuse integration because it:
- Uses native `@observe` decorator for automatic tracing
- Provides `instrument()` method for primitive wrapping
- Handles parent/child trace relationships automatically
- Includes comprehensive error tracking
- Supports async flush operations

**Migration Path:**

1. Import from unified location:
   ```python
   from tta_apm_langfuse import LangFuseIntegration
   ```

2. Initialize once per application:
   ```python
   import os
   from tta_apm_langfuse import LangFuseIntegration
   
   apm = LangFuseIntegration(
       public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
       secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
       host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com"),
       enabled=True
   )
   ```

3. Instrument primitives:
   ```python
   workflow = apm.instrument(my_primitive, trace_name="custom-name")
   result = await workflow.execute(data, context)
   ```

4. Manual LLM generation tracking:
   ```python
   apm.create_generation(
       name="gpt4-call",
       model="gpt-4",
       input_data=prompt,
       output_data=response,
       metadata={"tokens": 150, "cost_usd": 0.003}
   )
   ```

## Deprecation Timeline

- **Immediate:** `platform/observability/src/observability_integration/langfuse_integration.py` marked deprecated
- **Week 1:** Update all internal code to use `tta_apm_langfuse`
- **Week 2:** Add deprecation warnings to old module
- **Month 1:** Remove deprecated module

## Benefits

- Single source of truth for LangFuse integration
- Consistent tracing across all primitives
- Better maintainability
- Clearer documentation
- Reduced code duplication

## Implementation Status

- [x] Identify duplicate implementations
- [x] Choose primary implementation
- [x] Document consolidation plan
- [ ] Update primitives to use unified integration
- [x] Add deprecation warnings
- [x] Update documentation
- [ ] Remove deprecated code
