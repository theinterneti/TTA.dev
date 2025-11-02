# Quick Help Needed: Gemini CLI Output Capture

**Repo:** theinterneti/TTA.dev
**Issue:** `run-gemini-cli@v0` action succeeds but `gemini_response` output is empty (0 bytes)

## What Works ✅
- Workflow triggers correctly
- Gemini CLI v0.11.3 installs
- API auth with gemini-2.5-flash (HTTP 200)
- Step completes without errors

## What Doesn't ❌
- `steps.run_gemini.outputs.gemini_response` is always empty
- No response posted to issues

**See:** `GEMINI_CLI_INTEGRATION_QUESTIONS.md` for full details

**Question:** Why is stdout empty when `gemini --yolo --prompt "text"` runs successfully in the action?
