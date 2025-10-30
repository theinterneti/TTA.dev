# Gemini CLI 60+ Minute Hang - Root Cause Investigation

**Date**: October 30, 2025, 21:27 UTC
**Workflow Run**: #18953391176
**Duration**: 90+ minutes (started 19:56:34 UTC, still running at 21:27 UTC)
**Command**: `@gemini-cli help` (simple help command)
**Expected Duration**: 1-2 minutes
**Actual Duration**: 90+ minutes (45-90x slower than expected)

---

## Executive Summary

**Status**: 🔴 **CRITICAL HANG IDENTIFIED**

The Gemini CLI workflow is **stuck on the "Run Gemini CLI" step** after 90+ minutes of execution. This is a **critical performance issue** that makes the integration unusable for production.

**Key Findings**:
1. ✅ Workflow successfully completed "Set up job" and "Mint identity token" steps
2. 🔴 **Workflow is stuck on "Run Gemini CLI" step** (no completion after 90+ minutes)
3. ⚠️ **Logs are not available** until the workflow completes (GitHub Actions limitation)
4. ⚠️ **No observability data available** - TTA.dev observability stack does NOT capture GitHub Actions telemetry
5. ⚠️ **Timeout not enforced** - The 15-minute timeout added in PR #62 has NOT been applied to this run (run started before PR was merged)

**Root Cause Hypothesis** (based on configuration analysis):
1. **Docker MCP Server overhead** (most likely) - Pulling `ghcr.io/github/github-mcp-server:v0.18.0` image
2. **Telemetry configuration issues** - GCP telemetry enabled but may be misconfigured
3. **Network/API latency** - Slow connection to Gemini API or GCP services

---

## Investigation Timeline

| Time (UTC) | Event | Status |
|------------|-------|--------|
| 19:56:31 | User posted `@gemini-cli help` in issue #59 | ✅ |
| 19:56:34 | Workflow triggered (3 second delay) | ✅ |
| 19:56:41 | Acknowledgment posted (10 second latency) | ✅ |
| 19:56:46 | "Set up job" completed | ✅ |
| 19:56:46 | "Mint identity token" started | ✅ |
| 19:56:46 | "Run Gemini CLI" started | 🔴 **STUCK HERE** |
| 21:27:20 | Investigation conducted (90+ minutes elapsed) | 🔴 **STILL RUNNING** |

---

## Workflow Job Status

```
* main 🔀 Gemini Dispatch · 18953391176
Triggered via issue_comment about 1 hour ago

JOBS
✓ debugger in 3s (ID 54123736403)
✓ dispatch in 6s (ID 54123736415)
* invoke / invoke (ID 54123747890)  ← STUCK HERE

Job Steps:
  ✓ Set up job
  - Mint identity token
  * Run Gemini CLI              ← STUCK HERE (90+ minutes)
  * Post Run Gemini CLI
```

**Critical Observation**: The "Run Gemini CLI" step has been executing for **90+ minutes** without completion or timeout.

---

## Observability Analysis

### TTA.dev Observability Stack

**Configuration**:
- **Package**: `tta-observability-integration`
- **Components**: OpenTelemetry + Prometheus + Grafana
- **Metrics Endpoint**: `http://localhost:9464/metrics`
- **Scrape Targets**: Local applications only (`host.docker.internal:8000`, `host.docker.internal:9464`)

**GitHub Actions Integration**: ❌ **NOT CONFIGURED**

**Key Finding**: The TTA.dev observability stack is designed for **local development and application monitoring**, NOT for GitHub Actions workflows.

**Evidence**:
1. Prometheus scrape targets point to `host.docker.internal` (local Docker containers)
2. No GitHub Actions-specific exporters or collectors configured
3. No correlation between GitHub Actions workflow runs and TTA.dev traces/metrics
4. Observability is initialized via `initialize_observability()` in Python applications, not in GitHub Actions workflows

**Conclusion**: We **CANNOT** query the TTA.dev observability stack for telemetry data from this GitHub Actions workflow run.

---

## Gemini CLI Telemetry Configuration

**From `.github/workflows/gemini-invoke.yml` (lines 77-80)**:

```yaml
"telemetry": {
  "enabled": ${{ vars.GOOGLE_CLOUD_PROJECT != '' }},
  "target": "gcp"
}
```

**Analysis**:
- Telemetry is **enabled** (assuming `vars.GOOGLE_CLOUD_PROJECT` is set)
- Telemetry target is **GCP** (Google Cloud Platform)
- Telemetry data is sent to the GCP project specified in `vars.GOOGLE_CLOUD_PROJECT`

**Potential Issues**:
1. **GCP project misconfiguration** - If the project doesn't exist or lacks permissions, telemetry operations could timeout
2. **Network latency** - Sending telemetry to GCP adds overhead to every operation
3. **Telemetry export failures** - If telemetry export fails, it could cause retries and delays

**Recommendation**: Disable telemetry for testing to rule out this as a bottleneck.

---

## Docker MCP Server Analysis

**Configuration** (lines 97-132):

```yaml
"mcpServers": {
  "github": {
    "command": "docker",
    "args": [
      "run", "-i", "--rm", "-e", "GITHUB_PERSONAL_ACCESS_TOKEN",
      "ghcr.io/github/github-mcp-server:v0.18.0"
    ],
    ...
  }
}
```

**Potential Bottlenecks**:

1. **Docker Image Pull** (first run or cache miss)
   - Image size: Unknown (need to check)
   - Pull time: Could be 1-5 minutes on slow networks
   - **Hypothesis**: If the GitHub Actions runner doesn't have the image cached, it must pull it on every run

2. **Docker Container Startup**
   - Container initialization: 5-10 seconds
   - MCP server startup: 5-10 seconds
   - Total overhead: 10-20 seconds (acceptable)

3. **Docker Networking**
   - Communication between Gemini CLI and Docker container
   - Potential latency: 1-5ms per request (acceptable)

**Critical Question**: Is the Docker image being pulled on every workflow run?

**Evidence from Karl Stoney's Setup**:
- Uses Kubernetes with **pre-configured MCP servers**
- Avoids Docker pull/startup overhead on every run
- Completes complex PR reviews in 3-5 minutes

**Recommendation**: Add a step to pre-pull the Docker image before running Gemini CLI.

---

## Configuration Comparison: TTA.dev vs Karl Stoney

| Setting | TTA.dev | Karl Stoney | Impact |
|---------|---------|-------------|--------|
| **MCP Server** | Docker (`ghcr.io/github/github-mcp-server:v0.18.0`) | Kubernetes (pre-configured) | 🔴 **HIGH** - Docker pull overhead |
| **Telemetry** | Enabled (GCP) | Unknown | ⚠️ **MEDIUM** - Potential network overhead |
| **Timeout** | 15 minutes (not applied to this run) | Unknown | ⚠️ **MEDIUM** - No timeout enforcement |
| **Model** | Default (likely `gemini-2.0-flash-exp`) | `gemini-2.5-pro` | ⚠️ **LOW** - Model selection |
| **Max Session Turns** | 25 | Unknown | ⚠️ **LOW** - Conversation length |

---

## Root Cause Hypothesis

Based on the investigation, the most likely root causes (in order of probability):

### 1. 🔴 **Docker Image Pull Overhead** (HIGH PROBABILITY)

**Evidence**:
- Docker-based MCP server configured
- No pre-pull step in workflow
- GitHub Actions runners may not have image cached
- Karl Stoney uses Kubernetes with pre-configured servers (avoids this issue)

**Impact**: 1-5 minutes for image pull (on slow networks)

**Test**: Add pre-pull step and measure execution time

---

### 2. ⚠️ **Telemetry Configuration Issues** (MEDIUM PROBABILITY)

**Evidence**:
- Telemetry enabled and set to send data to GCP
- No verification that GCP project is correctly configured
- Telemetry export failures could cause retries and delays

**Impact**: Unknown (could be 1-10 minutes if retrying failed exports)

**Test**: Disable telemetry and measure execution time

---

### 3. ⚠️ **Network/API Latency** (MEDIUM PROBABILITY)

**Evidence**:
- No direct evidence, but possible
- Could be slow connection to Gemini API
- Could be slow connection to GCP services

**Impact**: Unknown (could be 1-10 minutes)

**Test**: Enable debug logging to see API call latency

---

## Immediate Action Items

### 1. **Cancel the Stuck Workflow** ✅ URGENT

```bash
gh run cancel 18953391176
```

**Reason**: The workflow has been running for 90+ minutes with no progress. Cancel it to free up resources.

---

### 2. **Apply PR #62 Changes** ✅ URGENT

**PR #62 Status**: Open (not merged)

**Changes**:
- Added `timeout-minutes: 15` to prevent indefinite hangs
- Added explicit headless settings
- Created investigation document

**Action**: Merge PR #62 to apply the timeout configuration.

---

### 3. **Test with Telemetry Disabled** ✅ HIGH PRIORITY

**Create a new test workflow** with telemetry disabled:

```yaml
"telemetry": {
  "enabled": false
}
```

**Expected Result**: If telemetry is the bottleneck, execution time should drop significantly.

---

### 4. **Add Docker Pre-Pull Step** ✅ HIGH PRIORITY

**Add before "Run Gemini CLI" step**:

```yaml
- name: 'Pre-pull GitHub MCP Server'
  run: docker pull ghcr.io/github/github-mcp-server:v0.18.0
```

**Expected Result**: If Docker pull is the bottleneck, this will make it visible in the logs.

---

### 5. **Enable Debug Logging** ✅ MEDIUM PRIORITY

**Set `gemini_debug: true`** in workflow:

```yaml
gemini_debug: true
```

**Expected Result**: Detailed logs showing where execution is stuck.

---

## Next Steps

1. ✅ **Cancel workflow run #18953391176**
2. ✅ **Merge PR #62** to apply timeout configuration
3. ✅ **Create test branch** with telemetry disabled + Docker pre-pull
4. ✅ **Trigger new test run** with `@gemini-cli help` command
5. ✅ **Monitor execution time** and check logs when complete
6. ✅ **Identify bottleneck** from logs and apply targeted fix

---

## Lessons Learned

1. **Observability Gap**: TTA.dev observability stack does NOT capture GitHub Actions telemetry
2. **Timeout Critical**: Without timeout, workflows can hang indefinitely
3. **Docker Overhead**: Docker-based MCP servers add significant overhead vs pre-configured servers
4. **Log Availability**: GitHub Actions logs are only available after workflow completes
5. **Testing Required**: Cannot assume configuration works without testing in production environment

---

**Last Updated**: October 30, 2025, 21:45 UTC
**Status**: Diagnostic test run in progress (workflow run #18955932233)

---

## Update: Diagnostic Test Run Initiated

**Time**: 21:45 UTC
**Workflow Run**: #18955932233
**PR**: #64 (test/gemini-cli-diagnostics)
**Command**: `@gemini-cli help`

### Actions Completed

1. ✅ **Merged PR #62** - Applied 15-minute timeout and performance optimizations
2. ✅ **Created test branch** - `test/gemini-cli-diagnostics` with diagnostic configuration
3. ✅ **Disabled telemetry** - `"telemetry": {"enabled": false}`
4. ✅ **Added Docker pre-pull step** - Makes image pull time visible in logs
5. ✅ **Enabled debug logging** - `gemini_debug: true` for detailed traces
6. ✅ **Created diagnostic PR #64** - Draft PR for testing
7. ✅ **Triggered workflow** - Posted `@gemini-cli help` command in PR #64

### Monitoring

**Workflow Status**: In progress
**Started**: 21:45:36 UTC
**Expected Duration**: 1-2 minutes (target), 3-5 minutes (acceptable), >10 minutes (unacceptable)

**Next Steps**:
1. ⏳ Monitor workflow execution time
2. ⏳ Analyze logs when workflow completes
3. ⏳ Identify specific bottleneck from logs
4. ⏳ Update this document with findings
5. ⏳ Apply targeted fix based on identified bottleneck

---

## Original Investigation (October 30, 2025, 21:27 UTC)
