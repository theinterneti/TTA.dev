# AI Agent Observability in CI

This directory contains scripts and configurations for immutable logging and observability of AI agent decisions in GitHub Actions.

## Overview

When AI agents make decisions in our CI pipeline (test triage, code fixes, documentation updates), we need:

1. **Immutable audit logs** - Every decision is logged with structured metadata
2. **OpenTelemetry integration** - All operations are traced via OTEL
3. **Artifact archival** - Decision logs are uploaded as GitHub Actions artifacts

## Scripts

### `ai_decision_logger.py`

Logs AI agent decisions with immutable audit trail.

**Usage:**
```bash
python scripts/ci/ai_decision_logger.py \
  --agent-name "test-triage-agent" \
  --action "Propose fix for test_retry_primitive" \
  --confidence 0.85 \
  --rationale "Root cause: RetryPrimitive max_attempts parameter removed" \
  --metadata '{"pr_number": 123, "test_name": "test_retry"}'
```

**Output:**
Creates a JSON file in `ci-ai-decisions/` with structure:
```json
{
  "trace_id": "uuid-v4",
  "timestamp": "2026-03-07T20:00:00.000Z",
  "agent_name": "test-triage-agent",
  "agent_version": "1.0.0",
  "proposed_action": "Propose fix for test_retry_primitive",
  "confidence_score": 0.85,
  "rationale": "Root cause analysis...",
  "ci_context": {
    "github_run_id": "12345",
    "github_sha": "abc123",
    "github_workflow": "CI"
  },
  "metadata": {},
  "otel_trace_parent": "00-trace-id-span-id-01"
}
```

### `setup_otel.py`

Configures OpenTelemetry environment variables for CI runners.

**Usage:**
```bash
# In GitHub Actions or local environment
eval $(python scripts/ci/setup_otel.py)

# Verify configuration
echo $OTEL_SERVICE_NAME  # tta-ci-runner
echo $TRACEPARENT        # W3C trace context
```

**Environment Variables Set:**
- `OTEL_SERVICE_NAME=tta-ci-runner`
- `OTEL_EXPORTER_OTLP_ENDPOINT` (defaults to localhost:4318)
- `OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf`
- `OTEL_TRACES_EXPORTER=otlp`
- `OTEL_METRICS_EXPORTER=otlp`
- `OTEL_LOGS_EXPORTER=otlp`
- `OTEL_RESOURCE_ATTRIBUTES` (service metadata + CI context)

## Workflow Integration

### Agentic Workflows

Add to `.github/workflows/*.md` agentic workflows:

```markdown
## Initialization (Run First!)

Before any analysis, configure observability:
\`\`\`bash
# Setup OpenTelemetry environment
eval $(python scripts/ci/setup_otel.py)
echo "✅ OTEL configured with trace: $TRACEPARENT"
\`\`\`

## Log Decisions

Before taking action:
\`\`\`bash
python scripts/ci/ai_decision_logger.py \
  --agent-name "your-agent-name" \
  --action "Description of action" \
  --confidence 0.0-1.0 \
  --rationale "Why you're doing this" \
  --metadata '{"key": "value"}'
\`\`\`
```

### Upload Artifacts

Use the reusable workflow to upload decision logs:

```yaml
jobs:
  your-job:
    steps:
      # ... your steps that create ci-ai-decisions/ logs ...
  
  upload-decisions:
    needs: your-job
    uses: ./.github/workflows/upload-ai-decisions.yml
    with:
      workflow_name: ${{ github.workflow }}
```

## Local Development

Test the logging system locally:

```bash
# Configure OTEL
eval $(python scripts/ci/setup_otel.py)

# Log a decision
python scripts/ci/ai_decision_logger.py \
  --agent-name "local-test" \
  --action "Testing logging" \
  --confidence 1.0 \
  --rationale "Development testing"

# Verify log created
ls -la ci-ai-decisions/
cat ci-ai-decisions/*.json | jq .
```

## Ingestion by Observability UI

The `tta-observability-ui` dashboard ingests these artifacts:

1. GitHub Actions uploads artifacts to artifact storage
2. Observability backend polls for new artifacts
3. JSON logs are parsed and indexed
4. Metrics, traces, and decision timelines are generated

## Security

- **Immutable**: Logs are write-once, cannot be modified
- **Traceable**: Every log includes W3C trace context for correlation
- **Auditable**: All AI decisions are visible in GitHub Actions artifacts
- **Retention**: Artifacts retained for 90 days

## Guidelines

**When to log:**
- Before opening PRs
- Before modifying code
- Before making infrastructure changes
- When confidence score changes significantly

**What NOT to log:**
- Secrets or credentials
- Large file contents (use hashes)
- Personal information

**Confidence Thresholds:**
- `>= 0.9`: High confidence, proceed automatically
- `0.7-0.9`: Moderate confidence, create Draft PR
- `< 0.7`: Low confidence, explain but don't act

## Examples

### Test Triage Agent
```bash
python scripts/ci/ai_decision_logger.py \
  --agent-name "test-triage" \
  --action "Fix flaky test_circuit_breaker_transitions" \
  --confidence 0.92 \
  --rationale "Test uses time.sleep instead of MockPrimitive, causing timing issues" \
  --metadata '{"pr_number": 208, "test_file": "test_circuit_breaker.py"}'
```

### Documentation Sync Agent
```bash
python scripts/ci/ai_decision_logger.py \
  --agent-name "docs-sync" \
  --action "Update README.md RetryPrimitive examples" \
  --confidence 0.95 \
  --rationale "RetryStrategy replaced max_attempts parameter" \
  --metadata '{"commit_sha": "abc123", "files": ["README.md", "PRIMITIVES_CATALOG.md"]}'
```

## Troubleshooting

**No TRACEPARENT set:**
```bash
# Ensure setup_otel.py is sourced, not executed
eval $(python scripts/ci/setup_otel.py)  # ✅
python scripts/ci/setup_otel.py          # ❌ (won't export to shell)
```

**Artifacts not uploading:**
- Check `ci-ai-decisions/` directory exists and has .json files
- Verify workflow has `contents: read` permission
- Check GitHub Actions artifact retention settings

**JSON parse errors:**
- Ensure `--metadata` is valid JSON string
- Use single quotes around JSON: `'{"key": "value"}'`
- Escape special characters in bash

## Related Documentation

- [OTEL Integration](../../platform/observability/README.md)
- [Agentic Workflows](../.github/workflows/README.md)
- [TTA Observability Primitives](../../PRIMITIVES_CATALOG.md#observability)
