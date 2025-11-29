# Gemini CLI Performance Investigation

**Date**: October 30, 2025  
**Status**: 🔍 In Progress  
**Related Issues**: #59, #61  
**Workflow Run**: [#18953391176](https://github.com/theinterneti/TTA.dev/actions/runs/18953391176)

---

## Executive Summary

Investigation into why a simple `@gemini-cli help` command is taking 35+ minutes to execute in GitHub Actions, when production implementations (Karl Stoney's Autotrader system) complete complex PR reviews in 3-5 minutes.

**Key Finding**: The GitHub Action is correctly configured with `--yolo` flag for headless execution. The performance issue is **NOT** caused by waiting for approval prompts.

---

## Timeline

| Time (UTC) | Event | Duration |
|------------|-------|----------|
| 19:56:31 | User posted `@gemini-cli help` in issue #59 | - |
| 19:56:34 | Workflow triggered | 3 seconds |
| 19:56:41 | Acknowledgment posted | 10 seconds |
| 19:56:46 | Gemini CLI execution started | - |
| 20:32:00+ | **Still executing** | **35+ minutes** |

---

## Root Cause Analysis

### ✅ What We Ruled Out

1. **Approval Prompt Theory** - ❌ RULED OUT
   - GitHub Action uses `--yolo` flag (line 283 of `action.yml`)
   - This automatically accepts all tool executions
   - Equivalent to `tools.autoAccept: true` in settings

2. **Missing Settings** - ❌ NOT THE CAUSE (for GitHub Actions)
   - Local `.gemini/settings.json` was missing critical settings
   - **BUT** GitHub Actions workflow passes settings via `settings` input
   - The `--yolo` CLI flag overrides settings anyway

### 🔍 Possible Causes (Under Investigation)

1. **Network/API Issues**
   - Slow connection to Gemini API
   - API rate limiting or throttling
   - Geographic latency (GitHub Actions runners vs API endpoints)

2. **Model Selection**
   - Default model may be slower than expected
   - No explicit model pinned in workflow
   - Karl Stoney uses `gemini-2.5-pro` (slower model but faster results!)

3. **GitHub MCP Server Overhead**
   - Docker container startup time
   - Image pull time (using `ghcr.io/github/github-mcp-server:v0.18.0`)
   - Communication overhead between Gemini CLI and MCP server

4. **Resource Constraints**
   - GitHub Actions runner limitations (CPU, memory, network)
   - Concurrent workflow limits
   - Runner queue delays

5. **Workflow Configuration**
   - Missing optimizations
   - No timeout set (could run indefinitely)
   - Debug logging disabled (can't see what's happening)

---

## Configuration Comparison

### TTA.dev vs Karl Stoney's Production

| Aspect | TTA.dev | Karl Stoney (Production) |
|--------|---------|--------------------------|
| **Platform** | GitHub Actions | Kubernetes Jobs |
| **Model** | Not explicitly set (defaults to `gemini-2.0-flash-exp`) | `gemini-2.5-pro` |
| **Execution** | Synchronous (waits for completion) | Asynchronous (fire-and-forget) |
| **Timeout** | ❌ None (before fix) | ✅ Set (reasonable limits) |
| **Debug Logging** | ❌ Disabled | ✅ Enabled (for troubleshooting) |
| **MCP Server** | Docker-based (pull on every run) | Pre-configured in cluster |
| **Scale** | Single repository | 50 PRs/day across multiple repos |
| **Performance** | 35+ minutes (abnormal) | 3-5 minutes (normal) |

---

## Optimizations Applied

### 1. ✅ Updated `.gemini/settings.json` (Local Development)

**File**: `.gemini/settings.json`  
**Commit**: TBD

Added critical settings for headless execution:

```json
{
  "general": {
    "disableAutoUpdate": true
  },
  "ui": {
    "hideTips": true,
    "hideFooter": true
  },
  "tools": {
    "autoAccept": true
  },
  "security": {
    "folderTrust": {
      "featureEnabled": false,
      "enabled": true
    }
  }
}
```

**Impact**: Improves local development experience, but doesn't affect GitHub Actions performance.

### 2. ✅ Updated `gemini-invoke.yml` (GitHub Actions)

**File**: `.github/workflows/gemini-invoke.yml`  
**Commit**: TBD

**Changes**:

1. **Added timeout** (line 22):
   ```yaml
   timeout-minutes: 15  # Prevent runaway executions
   ```

2. **Added headless settings** to `settings` input (lines 65-133):
   ```json
   {
     "general": {
       "disableAutoUpdate": true
     },
     "ui": {
       "hideTips": true,
       "hideFooter": true
     },
     "tools": {
       "autoAccept": true
     },
     "security": {
       "folderTrust": {
         "featureEnabled": false,
         "enabled": true
       }
     }
   }
   ```

**Impact**: 
- Prevents workflows from running indefinitely
- Ensures headless execution settings are explicit
- Reduces output noise and update checks

---

## Next Steps

### Immediate Actions

1. **Wait for current run to complete or timeout**
   - Run #18953391176 is still in progress
   - Will provide logs once complete
   - Expected to timeout at 15-minute mark (new setting)

2. **Analyze workflow logs**
   - Check for slow operations
   - Identify bottlenecks
   - Look for retry/timeout messages

3. **Test with optimized configuration**
   - Trigger new `@gemini-cli help` command
   - Compare execution time with previous run
   - Verify timeout works correctly

### Further Optimizations (If Needed)

1. **Pin Gemini model explicitly**
   ```yaml
   gemini_model: 'gemini-2.0-flash-exp'  # Or gemini-2.5-pro
   ```

2. **Enable debug logging**
   ```yaml
   gemini_debug: true
   ```

3. **Pre-pull GitHub MCP Server image**
   - Add step to pull Docker image before running Gemini CLI
   - Reduces startup time

4. **Consider alternative MCP server deployment**
   - Use pre-built binary instead of Docker
   - Host MCP server separately (like Karl's Kubernetes setup)

5. **Add performance monitoring**
   - Track execution time per step
   - Log API response times
   - Monitor resource usage

---

## References

### External Resources

- **Karl Stoney's Blog**: [Building a PR Review Agent](https://karlstoney.com/building-a-pr-review-agent/) (October 8, 2025)
- **Gemini CLI Docs**: [Configuration](https://github.com/google-gemini/gemini-cli/blob/main/docs/cli/configuration.md)
- **GitHub Action Source**: [action.yml](https://github.com/google-github-actions/run-gemini-cli/blob/main/action.yml)

### Internal Resources

- **Issue #59**: Test: Gemini CLI GitHub Integration
- **Issue #61**: ✅ Gemini CLI GitHub Actions Integration - Success Report
- **Documentation**: `docs/integration/gemini-cli-github-actions.md`

---

## Lessons Learned

1. **Always check the source code** - The `--yolo` flag was in the action all along
2. **Production benchmarks are invaluable** - Karl's blog provided critical performance baseline
3. **Settings can be redundant** - CLI flags override settings files
4. **Timeouts are essential** - Prevent runaway executions in CI/CD
5. **Debug logging is critical** - Can't troubleshoot what you can't see

---

**Last Updated**: October 30, 2025 20:32 UTC  
**Status**: Awaiting workflow completion for log analysis

