# Gemini Workflow Authentication Issue - Diagnosis & Fix

**Date:** November 17, 2025
**Issue:** Gemini workflows failing with Google Cloud credentials error

---

## 🔍 Root Cause

The Gemini CLI is attempting to export telemetry to Google Cloud Platform, which requires **Google Cloud credentials** (not just the Gemini API key).

### Error Message
```
Error: Could not load the default credentials. Browse to https://cloud.google.com/docs/authentication/getting-started for more information.
```

### Stack Trace Location
```
PeriodicExportingMetricReader: metrics export failed
/usr/local/lib/node_modules/@google/gemini-cli/node_modules/@google-cloud/logging/build/src/v2/logging_service_v2_client.js:265
```

---

## 📊 What's Happening

The workflow configuration in `.github/workflows/experimental/gemini/gemini-triage.yml` (and likely others) has:

```yaml
settings: |-
  {
    "telemetry": {
      "enabled": ${{ vars.GOOGLE_CLOUD_PROJECT != '' }},  # ← Evaluates to TRUE if project var exists
      "target": "gcp"  # ← Tries to send telemetry to Google Cloud
    }
  }
```

**Authentication attempted:**
- `gcp_workload_identity_provider`: `${{ vars.GCP_WIF_PROVIDER }}`
- `gcp_service_account`: `${{ vars.SERVICE_ACCOUNT_EMAIL }}`
- `gcp_project_id`: `${{ vars.GOOGLE_CLOUD_PROJECT }}`

**Problem:** These Google Cloud variables are likely set (or partially set), which enables telemetry, but the Workload Identity Federation (WIF) authentication isn't properly configured or the service account doesn't have the right permissions.

---

## 🎯 Two Authentication Paths

The Gemini CLI can work in two modes:

### Option A: Direct API Key (Simpler)
- Uses `GEMINI_API_KEY` secret
- No Google Cloud project needed
- **No telemetry to GCP**
- ✅ Perfect for experimental workflows

### Option B: Google Cloud + Workload Identity (Complex)
- Uses Workload Identity Federation
- Requires GCP project setup
- Requires service account with permissions
- Enables telemetry export to GCP
- ❌ Not necessary for basic Gemini usage

**You're currently in a hybrid state:** API key is set, but GCP telemetry is enabled, causing auth failures.

---

## ✅ Solution Options

### Option 1: Disable GCP Telemetry (Recommended for Experimental)

Update ALL Gemini workflow files to disable GCP telemetry:

**Files to update:**
- `.github/workflows/experimental/gemini/gemini-triage.yml`
- `.github/workflows/experimental/gemini/gemini-dispatch.yml`
- `.github/workflows/experimental/gemini/gemini-review.yml`
- `.github/workflows/experimental/gemini/gemini-invoke-advanced.yml`
- Any other workflows using `run-gemini-cli`

**Change:**
```yaml
settings: |-
  {
    "model": {
      "maxSessionTurns": 25
    },
    "telemetry": {
      "enabled": false,  # ← Force disable
      "target": "gcp"
    },
    "tools": {
      "core": [
        "run_shell_command(echo)"
      ]
    }
  }
```

**Or remove GCP-specific inputs:**
```yaml
- name: 'Run Gemini CLI'
  uses: 'google-github-actions/run-gemini-cli@v0.1.14'
  with:
    # Remove these lines:
    # gcp_location: '${{ vars.GOOGLE_CLOUD_LOCATION }}'
    # gcp_project_id: '${{ vars.GOOGLE_CLOUD_PROJECT }}'
    # gcp_service_account: '${{ vars.SERVICE_ACCOUNT_EMAIL }}'
    # gcp_workload_identity_provider: '${{ vars.GCP_WIF_PROVIDER }}'
    
    # Keep these:
    gemini_api_key: '${{ secrets.GEMINI_API_KEY }}'
    gemini_model: '${{ vars.GEMINI_MODEL }}'
    # ... other non-GCP settings
    
    settings: |-
      {
        "telemetry": {
          "enabled": false  # ← Disable telemetry
        }
      }
```

### Option 2: Properly Configure Google Cloud (If Needed)

If you actually want GCP telemetry:

1. **Set up Workload Identity Federation:**
   - Create GCP project
   - Configure Workload Identity Pool
   - Create service account with permissions
   - Grant GitHub Actions access

2. **Configure repository variables:**
   ```
   GOOGLE_CLOUD_PROJECT=your-project-id
   GOOGLE_CLOUD_LOCATION=us-central1
   GCP_WIF_PROVIDER=projects/PROJECT_NUM/locations/global/workloadIdentityPools/POOL_ID/providers/PROVIDER_ID
   SERVICE_ACCOUNT_EMAIL=github-actions@PROJECT_ID.iam.gserviceaccount.com
   ```

3. **Add required permissions:**
   - `roles/logging.logWriter`
   - `roles/cloudtrace.agent`
   - `roles/monitoring.metricWriter`

**This is complex and likely overkill for experimental workflows!**

### Option 3: Use Environment Variable Override

Set repository variable to disable GCP features:
```
GOOGLE_GENAI_USE_VERTEXAI=false
GOOGLE_CLOUD_PROJECT=""  # ← Empty string disables telemetry check
```

---

## 🚀 Quick Fix Implementation

### Step 1: Update Main Gemini Workflow

Let me create a patch for `gemini-triage.yml`:

**File:** `.github/workflows/experimental/gemini/gemini-triage.yml`

**Find (around line 63-82):**
```yaml
        with:
          gcp_location: '${{ vars.GOOGLE_CLOUD_LOCATION }}'
          gcp_project_id: '${{ vars.GOOGLE_CLOUD_PROJECT }}'
          gcp_service_account: '${{ vars.SERVICE_ACCOUNT_EMAIL }}'
          gcp_workload_identity_provider: '${{ vars.GCP_WIF_PROVIDER }}'
          gemini_api_key: '${{ secrets.GEMINI_API_KEY }}'
          gemini_cli_version: '${{ vars.GEMINI_CLI_VERSION }}'
          gemini_debug: '${{ fromJSON(vars.DEBUG || vars.ACTIONS_STEP_DEBUG || false) }}'
          gemini_model: '${{ vars.GEMINI_MODEL }}'
          google_api_key: '${{ secrets.GOOGLE_API_KEY }}'
          use_gemini_code_assist: '${{ vars.GOOGLE_GENAI_USE_GCA }}'
          use_vertex_ai: '${{ vars.GOOGLE_GENAI_USE_VERTEXAI }}'
          settings: |-
            {
              "model": {
                "maxSessionTurns": 25
              },
              "telemetry": {
                "enabled": ${{ vars.GOOGLE_CLOUD_PROJECT != '' }},
                "target": "gcp"
              },
```

**Replace with:**
```yaml
        with:
          # Removed GCP-specific authentication (not needed for experimental workflows)
          # gcp_location: '${{ vars.GOOGLE_CLOUD_LOCATION }}'
          # gcp_project_id: '${{ vars.GOOGLE_CLOUD_PROJECT }}'
          # gcp_service_account: '${{ vars.SERVICE_ACCOUNT_EMAIL }}'
          # gcp_workload_identity_provider: '${{ vars.GCP_WIF_PROVIDER }}'
          
          gemini_api_key: '${{ secrets.GEMINI_API_KEY }}'
          gemini_cli_version: '${{ vars.GEMINI_CLI_VERSION || 'latest' }}'
          gemini_debug: '${{ fromJSON(vars.DEBUG || vars.ACTIONS_STEP_DEBUG || false) }}'
          gemini_model: '${{ vars.GEMINI_MODEL || 'gemini-2.5-flash' }}'
          # Removed use_vertex_ai (requires GCP auth)
          # use_vertex_ai: '${{ vars.GOOGLE_GENAI_USE_VERTEXAI }}'
          settings: |-
            {
              "model": {
                "maxSessionTurns": 25
              },
              "telemetry": {
                "enabled": false
              },
```

### Step 2: Verify Required Secrets

Check that these are set in repository settings:
- `GEMINI_API_KEY` ✅ (Should already exist)

Optional variables (with defaults):
- `GEMINI_CLI_VERSION` (default: 'latest')
- `GEMINI_MODEL` (default: 'gemini-2.5-flash')

---

## 📝 Affected Workflows

All workflows in `.github/workflows/experimental/gemini/` likely have this issue:

1. ✅ `gemini-dispatch.yml`
2. ✅ `gemini-triage.yml`
3. ✅ `gemini-review.yml`
4. ✅ `gemini-invoke-advanced.yml`
5. ✅ `gemini-invoke.yml`
6. ✅ `test-gemini-api-key.yml`
7. ✅ `test-gemini-cli-no-mcp.yml`
8. ✅ `test-gemini-keys.yml`
9. ✅ `list-gemini-models.yml`
10. ✅ `gemini-test-minimal.yml`

**Action needed:** Apply the same fix to all workflows that use `google-github-actions/run-gemini-cli`.

---

## ✅ Verification Steps

After fixing:

1. **Push changes to experimental branch**
2. **Trigger a workflow** (create/comment on test issue)
3. **Check workflow logs** for:
   - ✅ No "Could not load default credentials" error
   - ✅ Gemini CLI executes successfully
   - ✅ Response is generated

---

## 📖 Related Documentation

- **Gemini CLI GitHub Action:** https://github.com/google-github-actions/run-gemini-cli
- **Workload Identity Federation:** https://cloud.google.com/iam/docs/workload-identity-federation
- **Gemini API Authentication:** https://ai.google.dev/gemini-api/docs/api-key

---

## 💡 Recommendations

**For experimental workflows:**
1. ✅ **Disable GCP telemetry** (use Option 1)
2. ✅ **Use API key authentication** (simplest)
3. ✅ **Remove GCP-specific inputs** from workflows
4. ✅ **Set sensible defaults** for missing variables

**For production workflows (future):**
1. Consider if GCP telemetry is actually needed
2. If yes, properly set up Workload Identity Federation
3. If no, keep using simple API key auth

---

**Status:** Ready to implement fix
**Impact:** All 10 Gemini workflows affected
**Estimated fix time:** 15-30 minutes
**Testing:** Can test immediately after merge
