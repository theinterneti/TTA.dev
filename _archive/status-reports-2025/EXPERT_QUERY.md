# ✅ SOLVED: Gemini CLI Output Capture

**Repo:** theinterneti/TTA.dev
**Issue:** `run-gemini-cli@v0` action succeeded but produced empty output (0 bytes)

## Root Cause

Default `--prompt` mode doesn't produce reliable stdout in CI/CD environments.

## Solution

Use `--output-format json` flag for structured, parseable output:

```bash
# ❌ What we were doing (unreliable)
gemini --yolo --prompt "text"

# ✅ Correct approach (reliable)
gemini --yolo --prompt "text" --output-format json
```

## Implementation

Updated workflow to:

1. Install Gemini CLI directly (not via action wrapper)
2. Run with `--output-format json`
3. Parse JSON with `jq` to extract response text
4. Save to GitHub output properly

**Status:** Ready for testing in Issue #61

**See:** `GEMINI_CLI_INTEGRATION_QUESTIONS.md` for complete journey


---
**Logseq:** [[TTA.dev/_archive/Status-reports-2025/Expert_query]]
