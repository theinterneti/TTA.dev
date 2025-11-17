# Gemini API Troubleshooting Guide

**Status**: Performance issue SOLVED ✅ (10+ min → 54s) | API Authentication BLOCKED ❌

## Problem Summary

The @gemini-cli GitHub workflow completes successfully in ~54 seconds, but consistently fails with:
```
Error when talking to Gemini API
Full report available at: /tmp/gemini-client-error-Turn.run-sendMessageStream-[timestamp].json
```

**What we've tried** (all unsuccessful):
1. ✅ Model name changes (gemini-1.5-pro-002 → gemini-1.5-pro-latest → gemini-1.5-flash)
2. ✅ Multiple API key regenerations (GEMINI_API_KEY, GOOGLE_AI_STUDIO_API_KEY, VERTEX_API_KEY)
3. ✅ New Google Cloud Project created (604126426981)
4. ✅ GCP variables set (GOOGLE_CLOUD_PROJECT, GOOGLE_CLOUD_LOCATION)
5. ✅ Action version updated (@v0.1.14 → @v0)
6. ✅ Progressive workflow simplification (down to 2 parameters)
7. ✅ OAuth fix (GOOGLE_GENAI_USE_GCA=false)

**Current configuration** (commit 8b43d44):
```yaml
- name: 'Run Gemini CLI'
  uses: 'google-github-actions/run-gemini-cli@v0'
  with:
    gemini_api_key: '${{ secrets.GOOGLE_AI_STUDIO_API_KEY }}'
    prompt: '${{ inputs.additional_context }}'
```

## Critical Next Step: Test API Keys Directly

**You need to manually test if your API keys work outside GitHub Actions.**

### Step 1: Get Your API Keys

Your API keys are stored as GitHub secrets and cannot be accessed directly. You need to:

1. **For AI Studio Key**:
   - Go to: https://aistudio.google.com/apikey
   - Copy the API key for project 604126426981
   - This should match what's in `GOOGLE_AI_STUDIO_API_KEY` secret

2. **For Vertex AI Key**:
   - Go to: https://console.cloud.google.com/apis/credentials?project=604126426981
   - Copy the API key
   - This should match what's in `VERTEX_API_KEY` secret

### Step 2: Test AI Studio Pathway

Run this command in your terminal (replace `YOUR_KEY_HERE`):

```bash
export AI_STUDIO_KEY='YOUR_KEY_HERE'
./scripts/test-gemini-api-key.sh
```

**Expected outcomes:**

**✅ If test succeeds**:
```
✅ SUCCESS! API key works with AI Studio
Response:
Hello! How can I help you today?
```
→ **This means**: API key is valid, problem is with gemini-cli action
→ **Next steps**: File bug report OR implement direct API calls in workflow

**❌ If test fails with 400 error**:
```
❌ FAILED! API key does not work
Error response:
{
  "error": {
    "code": 400,
    "message": "API key not valid. Please pass a valid API key.",
    "status": "INVALID_ARGUMENT"
  }
}
```
→ **This means**: API key is invalid or improperly formatted
→ **Next steps**: Check API key in Google Cloud Console, verify it's enabled

**❌ If test fails with 403 error**:
```
❌ FAILED! API key does not work
Error response:
{
  "error": {
    "code": 403,
    "message": "The request is missing a valid API key.",
    "status": "PERMISSION_DENIED"
  }
}
```
→ **This means**: API key restrictions or permissions issue
→ **Next steps**: Check API key restrictions in Google Cloud Console

### Step 3: Test Vertex AI Pathway (Optional)

If you want to test the Vertex AI pathway:

```bash
export VERTEX_KEY='YOUR_VERTEX_KEY_HERE'
export GCP_PROJECT='604126426981'
export GCP_LOCATION='us-central1'
./scripts/test-gemini-api-key.sh
```

**Note**: Vertex AI may require service account authentication instead of API keys.

## Troubleshooting Based on Test Results

### Scenario A: API Key Test Succeeds ✅

**Problem**: gemini-cli GitHub Action has a bug or missing configuration

**Solutions**:

1. **File bug report with gemini-cli**:
   - Repository: https://github.com/google-github-actions/run-gemini-cli
   - Include: Test script results, workflow logs, minimal reproduction

2. **Implement direct API calls**:
   ```yaml
   - name: Call Gemini API Directly
     run: |
       response=$(curl -s -H "Content-Type: application/json" \
         -d '{
           "contents": [{
             "parts": [{"text": "${{ inputs.additional_context }}"}]
           }]
         }' \
         "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=${{ secrets.GOOGLE_AI_STUDIO_API_KEY }}")

       answer=$(echo "$response" | jq -r '.candidates[0].content.parts[0].text')

       gh issue comment ${{ github.event.issue.number }} --body "$answer"
   ```

3. **Use different action or SDK**:
   - Try alternative Gemini GitHub Actions
   - Use @google/generative-ai npm package directly

### Scenario B: API Key Test Fails (400/403) ❌

**Problem**: API key or Google Cloud configuration issue

**Checklist**:

1. **Verify API is enabled**:
   - Go to: https://console.cloud.google.com/apis/library/generativelanguage.googleapis.com?project=604126426981
   - Click "Enable" if not already enabled

2. **Check API key restrictions**:
   - Go to: https://console.cloud.google.com/apis/credentials?project=604126426981
   - Click on your API key
   - Check "API restrictions": Should allow "Generative Language API"
   - Check "Application restrictions": Should be "None" or allow GitHub Actions IPs

3. **Verify billing** (if required):
   - Go to: https://console.cloud.google.com/billing?project=604126426981
   - Ensure billing account is linked and active
   - Note: AI Studio may have free tier, Vertex AI typically requires billing

4. **Regenerate API key**:
   - Create new API key in Google Cloud Console
   - Update GitHub secret immediately
   - Test again with new key

5. **Try different project**:
   - Create new Google Cloud Project
   - Enable Generative Language API
   - Create new API key
   - Test with fresh setup

### Scenario C: Both Pathways Fail ❌

**Problem**: Fundamental configuration or account issue

**Checklist**:

1. **Verify Google account access**:
   - Can you access Google AI Studio? https://aistudio.google.com/
   - Can you access Google Cloud Console? https://console.cloud.google.com/

2. **Check API quotas**:
   - Go to: https://console.cloud.google.com/apis/api/generativelanguage.googleapis.com/quotas?project=604126426981
   - Verify you haven't exceeded free tier limits

3. **Try web interface**:
   - Go to: https://aistudio.google.com/prompts/new
   - Try sending a prompt
   - If this fails, issue is with Google account/project, not GitHub workflow

4. **Contact Google support**:
   - Issue may be with your Google Cloud account or project
   - Check for any account restrictions or verification requirements

## Implementation Plan: Two Pathways

Once API key testing confirms which pathway works, implement both:

### Pathway 1: AI Studio (Free Tier)

**Workflow**: `.github/workflows/gemini-invoke.yml` (current)

**Configuration**:
```yaml
uses: 'google-github-actions/run-gemini-cli@v0'
with:
  gemini_api_key: '${{ secrets.GOOGLE_AI_STUDIO_API_KEY }}'
  prompt: '${{ inputs.additional_context }}'
```

**Pros**: Simple, free tier, no billing required
**Cons**: Rate limits, fewer features than Vertex AI

### Pathway 2: Vertex AI (Enterprise)

**Workflow**: `.github/workflows/gemini-invoke-vertex.yml` (to be created)

**Configuration**:
```yaml
uses: 'google-github-actions/run-gemini-cli@v0'
with:
  use_vertex_ai: 'true'
  gcp_project_id: '${{ vars.GOOGLE_CLOUD_PROJECT }}'
  gcp_location: '${{ vars.GOOGLE_CLOUD_LOCATION }}'
  # May need workload identity or service account
```

**Pros**: Higher limits, enterprise features, SLAs
**Cons**: Requires billing, more complex auth

## Current Workflow Status

**Working**:
- ✅ Workflow triggers on @gemini-cli mentions
- ✅ Dispatch extracts commands correctly
- ✅ Acknowledgment posts successfully
- ✅ Execution completes in ~54 seconds
- ✅ No timeout issues

**Broken**:
- ❌ Gemini API authentication fails at runtime
- ❌ No responses posted to issues
- ❌ Error: "Error when talking to Gemini API"

## Test Workflow Runs

All runs show same error pattern:

- **19004460487**: gemini-1.5-pro-002 + full config → API error
- **19004722401**: gemini-1.5-pro-latest + regenerated key → API error
- **19005930722**: gemini-1.5-pro-latest + @v0 action → API error
- **19006015229**: gemini-1.5-flash + GCP vars → API error
- **19006030079**: gemini-1.5-flash + OAuth fix → API error
- **19006136164**: AI Studio key + GCP vars → API error
- **19006164981**: Minimal config (2 params) → API error

**Pattern**: Configuration changes have no effect on the error

## Files Modified

- `.github/workflows/gemini-invoke.yml` - Commit 8b43d44 (minimal config)
- `.github/workflows/gemini-test-minimal.yml` - Test workflow (proved MCP was issue)
- `scripts/test-gemini-api-key.sh` - Direct API testing script (NEW)

## Repository Configuration

**Secrets** (all updated recently):
- `GEMINI_API_KEY` - Original key (12 min ago)
- `GOOGLE_AI_STUDIO_API_KEY` - User provided (3 min ago)
- `VERTEX_API_KEY` - User provided (4 min ago)
- `GITHUB_PAT_KEY` - For GitHub API access

**Variables**:
- `GEMINI_MODEL` = "gemini-1.5-flash"
- `GEMINI_CLI_VERSION` = "latest"
- `GOOGLE_CLOUD_PROJECT` = "604126426981"
- `GOOGLE_CLOUD_LOCATION` = "us-central1"
- `GOOGLE_GENAI_USE_GCA` = "false"
- `GOOGLE_GENAI_USE_VERTEXAI` = "false"
- `DEBUG` = "true"

## Action Items

**IMMEDIATE** (do this now):
1. Run `./scripts/test-gemini-api-key.sh` with your API keys
2. Report results (success or error message)

**NEXT** (based on test results):
- If test succeeds → Implement direct API calls or file action bug
- If test fails → Debug Google Cloud configuration

**THEN** (after one pathway works):
- Implement both AI Studio and Vertex AI pathways
- Add error handling and retry logic
- Document usage in README

## Success Criteria

- ✅ AI Studio pathway posts responses using GOOGLE_AI_STUDIO_API_KEY
- ✅ Vertex AI pathway posts responses using VERTEX_API_KEY
- ✅ Response time under 2 minutes
- ✅ No "Error when talking to Gemini API"
- ✅ Workflow status: success with actual response

## References

- **Google AI Studio**: https://aistudio.google.com/
- **Vertex AI**: https://console.cloud.google.com/vertex-ai
- **Gemini CLI Action**: https://github.com/google-github-actions/run-gemini-cli
- **API Documentation**: https://ai.google.dev/api/rest
- **Test Issue**: #61 (TTA.dev repository)

---

**Last Updated**: November 1, 2025
**Status**: Waiting for API key test results
**Priority**: CRITICAL - Blocking all Gemini functionality
