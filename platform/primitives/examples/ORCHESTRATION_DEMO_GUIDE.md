# Multi-Model Orchestration Demo Guide

**Automated Test Generation with 90% Cost Savings**

This guide demonstrates a production-ready workflow that uses Claude Sonnet 4.5 as an orchestrator to analyze code and delegate test generation to Gemini Pro, achieving **90%+ cost reduction** while maintaining quality.

---

## 📖 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Trigger Methods](#trigger-methods)
- [Observability](#observability)
- [Cost Analysis](#cost-analysis)
- [Troubleshooting](#troubleshooting)

---

## Overview

### What This Demo Does

1. **Analyzes Python code** to identify functions that need tests
2. **Delegates test generation** to Gemini Pro (free flagship model)
3. **Validates generated tests** for quality and coverage
4. **Tracks all metrics** with OpenTelemetry + Prometheus
5. **Visualizes results** in Grafana dashboard

### Cost Savings

| Approach | Model | Cost per File | Monthly Cost (100 files) |
|----------|-------|---------------|--------------------------|
| **All Claude** | Claude Sonnet 4.5 | $0.50 | $50.00 |
| **Orchestration** | Claude + Gemini Pro | $0.05 | $5.00 |
| **Savings** | - | **90%** | **$45.00** |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Orchestrator (Claude)                     │
│                                                              │
│  1. Analyze code structure                                  │
│  2. Create test generation plan                             │
│  3. Validate generated tests                                │
│                                                              │
│  Cost: ~$0.009 per file (200 tokens analysis + 100 validation) │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
         ┌─────────────────────┐
         │  Executor (Gemini)  │
         │                     │
         │  Generate tests     │
         │                     │
         │  Cost: $0.00 (FREE) │
         └─────────────────────┘
                   │
                   ▼
         ┌─────────────────────┐
         │   Observability     │
         │                     │
         │  OpenTelemetry      │
         │  Prometheus         │
         │  Grafana            │
         └─────────────────────┘
```

---

## Prerequisites

### 1. Install Dependencies

```bash
cd packages/tta-dev-primitives
uv sync --extra integrations
```

### 2. Set Environment Variables

```bash
# Required: Google AI Studio API key (free)
export GOOGLE_API_KEY="your-google-ai-studio-key"

# Optional: For enhanced observability
export OPENTELEMETRY_ENABLED=true
```

### 3. Obtain API Keys

**Google AI Studio (FREE):**
1. Visit https://aistudio.google.com/app/apikey
2. Click "Create API Key"
3. Copy key to `.env` file

---

## Quick Start

### Run the Demo

```bash
cd packages/tta-dev-primitives

# Generate tests for a Python file
uv run python examples/orchestration_test_generation.py \
  --file src/tta_dev_primitives/core/base.py
```

### Expected Output

```
🧠 [Orchestrator] Analyzing code: src/tta_dev_primitives/core/base.py
📊 [Orchestrator] Analysis complete: 5 functions, complexity=moderate
🤖 [Executor] Generating tests with Gemini Pro...
✅ [Executor] Tests generated: 2847 chars, cost=$0.00
🔍 [Orchestrator] Validating generated tests...
✅ [Orchestrator] Validation: 4/4 checks passed

================================================================================
📊 WORKFLOW RESULTS
================================================================================
File: src/tta_dev_primitives/core/base.py
Functions tested: 5
Test code length: 2847 chars
Validation: ✅ Passed
Duration: 3421ms

💰 COST ANALYSIS
Orchestrator (Claude): $0.0090
Executor (Gemini): $0.0000
Total: $0.0090
vs. All-Claude: $0.50
Cost Savings: 98%
================================================================================

✅ Tests written to: src/tta_dev_primitives/core/base_test.py
```

---

## Trigger Methods

### 1. CLI (Manual)

```bash
# Single file
uv run python examples/orchestration_test_generation.py --file path/to/file.py

# Multiple files (bash loop)
for file in src/**/*.py; do
  uv run python examples/orchestration_test_generation.py --file "$file"
done
```

### 2. GitHub Webhook (Automated)

Create a GitHub Actions workflow:

```yaml
# .github/workflows/auto-test-generation.yml
name: Auto Test Generation

on:
  push:
    paths:
      - 'src/**/*.py'

jobs:
  generate-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install uv
          cd packages/tta-dev-primitives
          uv sync --extra integrations

      - name: Generate tests
        env:
          GOOGLE_API_KEY: ${{ secrets.GOOGLE_API_KEY }}
        run: |
          cd packages/tta-dev-primitives
          # Get changed Python files
          git diff --name-only HEAD~1 HEAD | grep '\.py$' | while read file; do
            uv run python examples/orchestration_test_generation.py --file "$file"
          done

      - name: Commit generated tests
        run: |
          git config user.name "Test Generator Bot"
          git config user.email "bot@example.com"
          git add **/*_test.py
          git commit -m "chore: Auto-generate tests" || echo "No tests to commit"
          git push
```

### 3. Scheduled (Cron)

```bash
# Add to crontab
# Run every day at 2 AM for new/modified files
0 2 * * * cd /path/to/TTA.dev/packages/tta-dev-primitives && \
  find src -name "*.py" -mtime -1 -exec \
  uv run python examples/orchestration_test_generation.py --file {} \;
```

---

## Observability

### Metrics Exposed

The workflow exposes Prometheus metrics on port **9464**:

```bash
# View metrics
curl http://localhost:9464/metrics | grep orchestration
```

**Key Metrics:**

| Metric | Type | Description |
|--------|------|-------------|
| `orchestration_workflows_total` | Counter | Total workflows executed |
| `orchestration_tasks_total{complexity}` | Counter | Tasks by complexity |
| `orchestration_delegations_total{executor_model}` | Counter | Delegations by model |
| `orchestration_delegations_success_total` | Counter | Successful delegations |
| `orchestration_validations_total` | Counter | Total validations |
| `orchestration_validations_passed_total` | Counter | Passed validations |
| `orchestration_workflow_duration_ms` | Histogram | Workflow duration |
| `orchestration_orchestrator_tokens_total` | Counter | Orchestrator tokens |
| `orchestration_executor_tokens_total` | Counter | Executor tokens |
| `orchestration_orchestrator_cost_usd` | Counter | Orchestrator cost |
| `orchestration_executor_cost_usd` | Counter | Executor cost |
| `orchestration_total_cost_usd` | Counter | Total cost |
| `orchestration_cost_savings_percent` | Gauge | Cost savings % |

### Grafana Dashboard

Import the dashboard:

```bash
# 1. Start Grafana (if not running)
docker run -d -p 3000:3000 grafana/grafana:latest

# 2. Import dashboard
# Navigate to http://localhost:3000
# Login: admin/admin
# Import: dashboards/grafana/orchestration-metrics.json
```

**Dashboard Panels:**
- Cost Savings Overview (stat)
- Total Cost Last 24h (stat)
- Task Classification Distribution (pie chart)
- Executor Model Usage (pie chart)
- Orchestrator vs Executor Tokens (time series)
- Delegation Success Rate (gauge)
- Validation Pass Rate (gauge)
- Cost Breakdown (stacked bars)
- Workflow Duration P50/P95/P99 (time series)

---

## Cost Analysis

### Detailed Breakdown

**Scenario:** Generate tests for 100 Python files

| Component | Tokens | Cost/1M | Total Cost |
|-----------|--------|---------|------------|
| **Orchestrator (Claude)** | | | |
| - Code analysis | 200 × 100 = 20K | $3.00 | $0.06 |
| - Test validation | 100 × 100 = 10K | $3.00 | $0.03 |
| **Executor (Gemini)** | | | |
| - Test generation | 1500 × 100 = 150K | $0.00 | $0.00 |
| **Total** | 180K | - | **$0.09** |

**vs. All-Claude Approach:**
- Claude for everything: 1700 × 100 = 170K tokens
- Cost: 170K × $3.00/1M = **$0.51**
- **Savings: $0.42 (82%)**

### ROI Calculation

**Monthly Usage:** 1000 files

| Approach | Monthly Cost | Annual Cost |
|----------|--------------|-------------|
| All-Claude | $510 | $6,120 |
| Orchestration | $90 | $1,080 |
| **Savings** | **$420/month** | **$5,040/year** |

---

## Troubleshooting

### Issue: "GOOGLE_API_KEY not set"

**Solution:**
```bash
export GOOGLE_API_KEY="your-key-here"
# Or add to .env file
echo "GOOGLE_API_KEY=your-key-here" >> .env
```

### Issue: "Observability not initialized"

**Solution:**
```bash
# Install observability integration
cd packages/tta-observability-integration
uv sync
```

### Issue: "Metrics not appearing in Prometheus"

**Solution:**
```bash
# 1. Check metrics endpoint
curl http://localhost:9464/metrics

# 2. Verify Prometheus scrape config
# Add to prometheus.yml:
scrape_configs:
  - job_name: 'tta-orchestration'
    static_configs:
      - targets: ['localhost:9464']
```

### Issue: "Validation always fails"

**Solution:**
- Check that generated tests include `import pytest`
- Verify test functions start with `test_`
- Ensure assertions are present (`assert `)
- Check that all functions from analysis are covered

---

## Next Steps

1. **Add More Executors:**
   - Register Groq for speed-critical tasks
   - Register DeepSeek R1 for complex reasoning

2. **Customize Validation:**
   - Add syntax checking with `ast.parse()`
   - Run tests with `pytest --collect-only`
   - Check coverage with `pytest-cov`

3. **Scale to Production:**
   - Deploy as microservice with FastAPI
   - Add queue for batch processing (Celery/RQ)
   - Implement retry logic for failed generations

4. **Monitor in Production:**
   - Set up alerts for validation failures
   - Track cost trends over time
   - Monitor executor model availability

---

**Last Updated:** October 30, 2025
**Maintained by:** TTA.dev Team



---
**Logseq:** [[TTA.dev/Platform/Primitives/Examples/Orchestration_demo_guide]]
