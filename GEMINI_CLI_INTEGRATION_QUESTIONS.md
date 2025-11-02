# Gemini CLI GitHub Actions Integration - Expert Questions

**Date:** November 1, 2025  
**Repository:** theinterneti/TTA.dev  
**Context:** Attempting to integrate `@google-github-actions/run-gemini-cli@v0` for async AI assistance in GitHub issues/PRs

---

## Executive Summary

We've successfully solved **performance issues** (10+ minutes → 54 seconds) and **API authentication errors** (updated from deprecated `gemini-1.5-flash` to `gemini-2.5-flash`), but we're now facing a **critical output capture issue**: the Gemini CLI action executes successfully but produces **zero-length responses**.

### Current Status

- ✅ **Workflow Triggers**: Working perfectly
- ✅ **API Authentication**: All keys valid, correct model configured
- ✅ **Gemini CLI Installation**: v0.11.3 installs successfully
- ✅ **Execution**: Completes without errors (~40s)
- ❌ **Output Capture**: `gemini_response` output is always empty (0 bytes)
- ❌ **Bot Response**: No Gemini responses posted to issues

---

## What We've Implemented

### Workflow Architecture

```
User mentions @gemini-cli in issue
    ↓
gemini-dispatch.yml (extracts command, routes)
    ↓
gemini-invoke.yml (executes Gemini CLI)
    ↓
google-github-actions/run-gemini-cli@v0
    ↓
Posts response to issue (NOT WORKING)
```

### Configuration Files

**`.github/workflows/gemini-invoke.yml`** (Simplified version without MCP):

```yaml
name: '▶️ Gemini Invoke'

on:
  workflow_call:
    inputs:
      additional_context:
        type: 'string'
        description: 'Any additional context from the request'
        required: false
      issue_number:
        type: 'number'
        description: 'The issue or PR number to comment on'
        required: false
      is_pull_request:
        type: 'boolean'
        description: 'Whether this is a pull request'
        required: false
        default: false

jobs:
  invoke:
    runs-on: 'ubuntu-latest'
    permissions:
      contents: 'read'
      id-token: 'write'
      issues: 'write'
      pull-requests: 'write'
    steps:
      - name: 'Run Gemini CLI'
        id: 'run_gemini'
        uses: 'google-github-actions/run-gemini-cli@v0'
        with:
          gemini_api_key: '${{ secrets.GOOGLE_AI_STUDIO_API_KEY }}'
          gemini_model: 'gemini-2.5-flash'
          prompt: '${{ inputs.additional_context }}'

      - name: 'Post Gemini Response'
        if: always()
        uses: 'actions/github-script@v7'
        with:
          github-token: '${{ github.token }}'
          script: |
            const response = `${{ steps.run_gemini.outputs.gemini_response }}`;
            const issueNumber = ${{ inputs.issue_number || 0 }};
            
            console.log('DEBUG: Response length:', response.length);
            console.log('DEBUG: Response preview:', response.substring(0, 100));
            console.log('DEBUG: Issue number:', issueNumber);
            
            if (!response || response.trim() === '') {
              console.log('No response from Gemini, skipping comment');
              return;
            }
            
            if (!issueNumber) {
              console.log('No issue number provided, skipping comment');
              return;
            }

            await github.rest.issues.createComment({
              owner: context.repo.owner,
              repo: context.repo.repo,
              issue_number: issueNumber,
              body: `**Gemini Response:**\n\n${response}`
            });
```

**`.github/workflows/gemini-dispatch.yml`** (Excerpt):

```yaml
invoke:
  needs: 'dispatch'
  if: |-
    ${{ needs.dispatch.outputs.command == 'invoke' }}
  uses: './.github/workflows/gemini-invoke.yml'
  permissions:
    contents: 'read'
    id-token: 'write'
    issues: 'write'
    pull-requests: 'write'
  with:
    additional_context: '${{ needs.dispatch.outputs.additional_context }}'
    issue_number: '${{ github.event.issue.number || github.event.pull_request.number }}'
    is_pull_request: '${{ github.event.pull_request != null }}'
  secrets: 'inherit'
```

### Repository Configuration

**Secrets:**
- `GOOGLE_AI_STUDIO_API_KEY`: Verified working (✅ HTTP 200 responses)
- `VERTEX_API_KEY`: Present but not used
- `GEMINI_API_KEY`: Legacy, also works

**Variables:**
- `GEMINI_MODEL`: `gemini-2.5-flash` (updated from deprecated `gemini-1.5-flash`)
- `GEMINI_CLI_VERSION`: `latest`
- `DEBUG`: `false`
- `GOOGLE_GENAI_USE_GCA`: `false`
- `GOOGLE_GENAI_USE_VERTEXAI`: `false`

---

## Problems Solved

### Problem 1: Performance (10+ Minutes) ✅ SOLVED

**Symptom:** Initial workflows took 10+ minutes to execute

**Root Cause:** MCP server Docker initialization added 9+ minutes overhead

**Solution:** Removed MCP server configuration from `gemini-invoke.yml` for basic queries

**Result:** Execution time reduced to ~40-54 seconds ✅

**Evidence:**
- Run with MCP: 10+ minutes
- Run without MCP: 54 seconds
- Current runs: ~40 seconds consistently

### Problem 2: API Authentication Errors ✅ SOLVED

**Symptom:** "Error when talking to Gemini API" in all workflow runs

**Root Cause:** Model `gemini-1.5-flash` no longer exists in Gemini API (HTTP 404)

**Investigation Steps:**
1. Created `test-gemini-keys.yml` workflow to test API keys directly
2. Tested multiple API keys with `curl` commands
3. Discovered all API keys work perfectly
4. Created `list-gemini-models.yml` workflow to enumerate available models
5. Found that Gemini 1.5 series has been deprecated

**Solution:** Updated to `gemini-2.5-flash` (current available model)

**Result:** 
- API calls return HTTP 200 ✅
- Gemini responds correctly: "That's great to hear! You are indeed interacting with a model from the Gemini family..."
- No more API errors ✅

**Available Models Confirmed:**
- ✅ `gemini-2.5-flash` (currently using)
- ✅ `gemini-2.5-pro`
- ✅ `gemini-2.0-flash`
- ✅ `gemini-2.0-flash-exp`
- ❌ `gemini-1.5-flash` (deprecated, causes 404)
- ❌ `gemini-1.5-pro` (deprecated, causes 404)

---

## Current Problem: Empty Response Output ❌

### Symptom

The `run-gemini-cli@v0` action:
- ✅ Installs Gemini CLI v0.11.3 successfully
- ✅ Executes without errors (step conclusion: "success")
- ✅ Completes in ~40 seconds
- ❌ Produces zero-length `gemini_response` output
- ❌ No response posted to GitHub issues

### Debug Output from Workflow Logs

```
DEBUG: Response length: 0
DEBUG: Response preview: 
DEBUG: Issue number: 61
No response from Gemini, skipping comment
```

### Evidence from Action Logs

```
2025-11-02T03:36:51.1165539Z echo "gemini_response<<EOF" >> "${GITHUB_OUTPUT}"
2025-11-02T03:36:51.1165860Z cat "${TEMP_STDOUT}" >> "${GITHUB_OUTPUT}"
2025-11-02T03:36:51.1166132Z echo "EOF" >> "${GITHUB_OUTPUT}"
```

The action script **is** trying to capture output from `TEMP_STDOUT`, but that file appears to be empty.

### Gemini CLI Execution Command

From the action's bash script:

```bash
if [[ "${DEBUG}" = true ]]; then
  if ! { gemini --yolo --prompt "${PROMPT}" 2> >(tee "${TEMP_STDERR}" >&2) | tee "${TEMP_STDOUT}"; }; then
    FAILED=true
  fi
else
  if ! gemini --yolo --prompt "${PROMPT}" 2> "${TEMP_STDERR}" 1> "${TEMP_STDOUT}"; then
    FAILED=true
  fi
fi
```

**Our Configuration:**
- `DEBUG`: `false` (so using the second branch)
- `PROMPT`: Successfully passed (e.g., "Describe TTA.dev in one concise sentence.")
- `FAILED`: Remains `false` (command doesn't fail)

---

## Investigation Steps Taken

### 1. Direct API Testing ✅

Created workflow to test Gemini API directly with `curl`:

```bash
curl -s "https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent?key=${API_KEY}" \
  -H 'Content-Type: application/json' \
  -d '{"contents":[{"parts":[{"text":"Are you gemini-2.5-flash?"}]}]}'
```

**Result:** HTTP 200, full response received ✅

### 2. Model Enumeration ✅

Listed all available models:

```bash
curl -s "https://generativelanguage.googleapis.com/v1/models?key=${API_KEY}" | jq -r '.models[].name'
```

**Result:** 20+ Gemini 2.x models listed, confirmed no 1.5 models ✅

### 3. Workflow Configuration Testing ✅

Tested multiple configurations:
- Minimal workflow (no MCP)
- With/without debug mode
- Different API key configurations
- Various model names

**Result:** Performance and authentication solved, but output still empty ❌

### 4. Output Capture Debugging ✅

Added extensive logging to `Post Gemini Response` step:

```javascript
console.log('DEBUG: Response length:', response.length);
console.log('DEBUG: Response preview:', response.substring(0, 100));
console.log('DEBUG: Issue number:', issueNumber);
```

**Result:** Confirmed response is empty (length: 0) ❌

### 5. Context Propagation Fix ✅

Initially, `context.payload.issue` was undefined in reusable workflows. Fixed by:
- Adding `issue_number` and `is_pull_request` inputs to `gemini-invoke.yml`
- Passing values from `gemini-dispatch.yml`

**Result:** Issue number now correctly passed (61), but response still empty ❌

---

## Questions for the Experts

### Question 1: CLI Command Syntax

**Is the `--yolo --prompt` syntax correct for Gemini CLI v0.11.3?**

The action runs:
```bash
gemini --yolo --prompt "Describe TTA.dev in one concise sentence."
```

- Is `--yolo` a valid flag? (We don't see it documented)
- Is `--prompt` the correct way to pass input in non-interactive mode?
- Should we be using `--input` or stdin instead?

### Question 2: Output Capture Method

**How should we capture Gemini CLI output in GitHub Actions?**

Current approach:
```bash
gemini --yolo --prompt "${PROMPT}" 2> "${TEMP_STDERR}" 1> "${TEMP_STDOUT}"
cat "${TEMP_STDOUT}" >> "${GITHUB_OUTPUT}"
```

Questions:
- Does Gemini CLI write responses to stdout?
- Could responses be going to stderr instead?
- Is there a different output file we should check?
- Does Gemini CLI require a TTY even with `--yolo`?

### Question 3: Action Version & Configuration

**Are we using the correct version of the action?**

We're using: `google-github-actions/run-gemini-cli@v0`

- Is `@v0` the correct/latest tag?
- Should we use a specific version like `@v0.1.0`?
- Are there known issues with output capture in this version?

### Question 4: Model Compatibility

**Is `gemini-2.5-flash` compatible with Gemini CLI v0.11.3?**

- Gemini CLI installs: v0.11.3
- Model configured: `gemini-2.5-flash`
- API endpoint: `generativelanguage.googleapis.com/v1`

Could there be a version mismatch where:
- The CLI was built for Gemini 1.5 models?
- Gemini 2.5 requires a newer CLI version?
- The CLI doesn't recognize Gemini 2.5 models?

### Question 5: Debug Mode

**Should we enable debug mode to see execution details?**

Current: `DEBUG: false`

Questions:
- What does debug mode reveal that could help diagnose this?
- Will it show the actual Gemini CLI execution and response?
- Are there performance/security implications to enabling it permanently?

### Question 6: Alternative Approaches

**Are there better patterns for async Gemini CLI integration?**

Alternatives we've considered:
1. **Direct API calls**: Skip CLI entirely, use REST API directly
2. **Custom action**: Write our own action with better logging
3. **Polling pattern**: Store results in artifacts, poll for completion
4. **Webhook pattern**: Have Gemini CLI post results to a webhook

Which approach is recommended for production use?

### Question 7: MCP Server Integration

**When/how should we integrate the MCP server?**

We removed MCP to solve performance issues, but we may need it for:
- GitHub API access (file reading, PR analysis)
- Repository context
- Tool usage

Questions:
- Is MCP required for basic Q&A or only for tool usage?
- Can we selectively enable MCP for certain commands?
- What's the recommended way to balance performance vs functionality?

### Question 8: Minimal Reproduction

**Can you help us create a minimal reproduction case?**

We'd like to test:
```yaml
- uses: 'google-github-actions/run-gemini-cli@v0'
  with:
    gemini_api_key: '${{ secrets.GOOGLE_AI_STUDIO_API_KEY }}'
    gemini_model: 'gemini-2.5-flash'
    prompt: 'Hello, are you working?'
```

And verify:
- Does this produce output?
- What should we see in the logs?
- How should we access the response?

---

## Test Workflows Available

We've created several test workflows that you can examine:

1. **`gemini-invoke.yml`**: Main workflow (currently not producing output)
   - Run: https://github.com/theinterneti/TTA.dev/actions/runs/19006773168

2. **`test-gemini-keys.yml`**: Direct API testing (✅ works)
   - Run: https://github.com/theinterneti/TTA.dev/actions/runs/19006396989

3. **`list-gemini-models.yml`**: Model enumeration (✅ works)
   - Run: https://github.com/theinterneti/TTA.dev/actions/runs/19006380851

4. **`gemini-dispatch.yml`**: Routing workflow (✅ works)
   - Run: https://github.com/theinterneti/TTA.dev/actions/runs/19006773168

---

## Environment Details

### GitHub Actions Runner
- OS: `ubuntu-latest`
- Shell: `/usr/bin/bash --noprofile --norc -e -o pipefail`

### Gemini CLI
- Version: `0.11.3` (installed via npm)
- Source: `@google/gemini-cli@latest`
- Installation: Successful (verified with `gemini --version`)

### API Configuration
- Endpoint: `https://generativelanguage.googleapis.com/v1`
- Authentication: AI Studio API Key (working ✅)
- Model: `gemini-2.5-flash` (confirmed available ✅)

### Workflow Context
- Trigger: `issue_comment.created`
- Event: User mentions `@gemini-cli <question>`
- Dispatch: Via reusable workflow call
- Permissions: `issues: write`, `contents: read`

---

## What We Need

### Immediate Help

1. **Root cause identification**: Why is `gemini_response` output always empty?
2. **Correct CLI syntax**: Proper command structure for non-interactive execution
3. **Output access pattern**: How to reliably capture Gemini CLI responses

### Documentation Requests

1. **GitHub Actions integration guide**: Step-by-step for async workflows
2. **Output handling**: How `run-gemini-cli@v0` action sets outputs
3. **Troubleshooting guide**: Common issues and solutions
4. **Model compatibility matrix**: Which CLI versions work with which models

### Example/Template

An official working example of:
- Trigger on issue comment
- Execute Gemini CLI
- Capture response
- Post back to issue

Even a minimal "hello world" example would help us identify what we're doing wrong.

---

## Success Criteria

We'll know we've succeeded when:

1. ✅ Workflow triggers on `@gemini-cli` mentions (WORKING)
2. ✅ Executes in < 2 minutes (WORKING - 40s)
3. ✅ Gemini CLI runs without errors (WORKING)
4. ❌ **`gemini_response` output contains actual content** (NOT WORKING)
5. ❌ **Response posted as comment to issue** (NOT WORKING)

We're 60% there! Just need help with output capture.

---

## Repository Access

- **Repository**: https://github.com/theinterneti/TTA.dev
- **Test Issue**: https://github.com/theinterneti/TTA.dev/issues/61
- **Workflows**: `.github/workflows/gemini-*.yml`
- **Documentation**: `docs/integration/gemini-cli-github-actions.md`

We're happy to provide:
- Direct repository access
- Additional workflow runs for testing
- Any other information needed

---

## Thank You

We appreciate any guidance you can provide! We've put significant effort into debugging this and we're confident we're close to a solution. The integration has huge potential for our AI development toolkit, and we'd love to make it work reliably.

**Contact:** Issues/PRs in https://github.com/theinterneti/TTA.dev or via GitHub discussions.

---

**Last Updated:** November 1, 2025  
**Status:** Awaiting expert guidance  
**Priority:** High - Blocks production deployment
