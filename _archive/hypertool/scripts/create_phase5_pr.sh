#!/bin/bash
# Phase 5 APM Integration - Git Workflow Automation
# This script executes the commit plan from GIT_COMMIT_PLAN.md

set -e  # Exit on error

echo "🚀 Phase 5 APM Integration - Git Workflow"
echo "=========================================="
echo ""

# Check we're on the right branch
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "agentic/core-architecture" ]; then
    echo "⚠️  Warning: Not on agentic/core-architecture branch (currently on $CURRENT_BRANCH)"
    echo "Continue anyway? (y/n)"
    read -r response
    if [ "$response" != "y" ]; then
        echo "Aborted."
        exit 1
    fi
fi

# Create feature branch
echo "📌 Step 1: Creating feature branch..."
git checkout -b feature/phase5-apm-integration
echo "✅ Branch created: feature/phase5-apm-integration"
echo ""

# Commit 1: Core Infrastructure
echo "📝 Commit 1/5: Core APM Infrastructure (Week 1)"
git add .hypertool/instrumentation/__init__.py \
        .hypertool/instrumentation/persona_metrics.py \
        .hypertool/instrumentation/workflow_tracing.py \
        .hypertool/instrumentation/test_instrumented_workflow.py \
        .hypertool/workflows/

git commit -m "feat(hypertool): Add core APM infrastructure with Prometheus metrics

Implement Phase 5 Week 1 deliverables:
- PersonaMetricsCollector with 6 Prometheus metrics
- WorkflowTracer with OpenTelemetry integration
- Test workflow demonstrating instrumentation
- Multi-persona workflow examples

Metrics implemented:
- persona_switches_total: Track persona transitions
- persona_duration_seconds: Time spent in each persona
- persona_tokens_used_total: Token consumption tracking
- persona_token_budget_remaining: Budget management
- workflow_stage_duration_seconds: Stage performance
- workflow_quality_gate_total: Quality gate results

Files:
- .hypertool/instrumentation/__init__.py
- .hypertool/instrumentation/persona_metrics.py (342 lines)
- .hypertool/instrumentation/workflow_tracing.py (317 lines)
- .hypertool/instrumentation/test_instrumented_workflow.py (329 lines)
- .hypertool/workflows/*.py (3 workflow files)"

echo "✅ Commit 1 complete"
echo ""

# Commit 2: Langfuse Integration
echo "📝 Commit 2/5: Langfuse LLM Observability (Week 2)"
git add .hypertool/instrumentation/langfuse_integration.py \
        .hypertool/instrumentation/observable_llm.py \
        .hypertool/instrumentation/LANGFUSE_INTEGRATION.md

git commit -m "feat(hypertool): Add Langfuse integration for LLM observability

Implement Phase 5 Week 2 deliverables:
- LangfuseIntegration class with trace/span/generation support
- ObservableLLM wrapper for automatic LLM call tracing
- Persona-as-user pattern for analytics
- Graceful degradation when Langfuse unavailable

Features:
- Automatic prompt/completion logging to Langfuse
- Token usage tracking integrated with Prometheus
- @observe_llm decorator for easy instrumentation
- Full type hints and error handling
- Environment-based configuration

Files:
- .hypertool/instrumentation/langfuse_integration.py (389 lines)
- .hypertool/instrumentation/observable_llm.py (308 lines)
- .hypertool/instrumentation/LANGFUSE_INTEGRATION.md (500+ lines)"

echo "✅ Commit 2 complete"
echo ""

# Commit 3: Dashboards & Alerts
echo "📝 Commit 3/5: Grafana Dashboards & Prometheus Alerts (Week 3)"
git add .hypertool/instrumentation/dashboards/ \
        .hypertool/instrumentation/persona_alerts.yml \
        .hypertool/instrumentation/ALERT_RUNBOOK.md

git commit -m "feat(hypertool): Add Grafana dashboards and Prometheus alerts

Implement Phase 5 Week 3 deliverables:
- 2 production-ready Grafana dashboards
- 7 Prometheus alert rules with graduated severity
- Comprehensive alert runbook documentation

Dashboards:
1. Persona Overview (5 panels):
   - Switch rate, duration heatmap, token usage, budget gauge, transitions
2. Workflow Performance (5 panels):
   - Stage duration p50/p95, success rate, failed gates, slowest stages, trends

Alerts:
- TokenBudgetExceeded (critical)
- HighQualityGateFailureRate (warning)
- ExcessivePersonaSwitching (warning)
- SlowWorkflowStage (warning)
- TokenBudgetDepletionPredicted (info)
- HypertoolMetricsNotReported (critical)
- LangfuseIntegrationFailing (warning)

Files:
- .hypertool/instrumentation/dashboards/persona_overview.json (380 lines)
- .hypertool/instrumentation/dashboards/workflow_performance.json (520 lines)
- .hypertool/instrumentation/persona_alerts.yml (280 lines)
- .hypertool/instrumentation/ALERT_RUNBOOK.md (850+ lines)"

echo "✅ Commit 3 complete"
echo ""

# Commit 4: Documentation
echo "📝 Commit 4/5: Documentation & Testing Infrastructure"
git add .hypertool/PHASE5_*.md \
        .hypertool/OBSERVABILITY_QUICK_REFERENCE.md \
        .hypertool/NEXT_SESSION_PROMPT.md \
        .hypertool/AUTOMATED_TESTING_PLAN.md \
        .hypertool/instrumentation/MANUAL_TESTING_PLAN.md \
        .hypertool/instrumentation/run_manual_tests.py \
        .hypertool/instrumentation/QUICK_TEST.md \
        .hypertool/instrumentation/BASELINE_TEST_SUCCESS.md \
        .hypertool/run_baseline_test.py

git commit -m "docs(hypertool): Add Phase 5 documentation and testing guides

Add comprehensive documentation for Phase 5 APM integration:
- Phase 5 planning and implementation summaries
- Quick reference guides for developers
- Manual testing plan with automation scripts
- Baseline test success documentation

Documentation:
- Planning documents and architecture decisions
- Week-by-week implementation summaries
- Quick reference for common tasks
- Manual testing procedures with automation

Testing:
- Manual testing plan (800+ lines)
- Automated test runner script
- Quick test guide (15 minutes)
- Baseline test success report

Files:
- .hypertool/PHASE5_*.md (6 planning/summary docs)
- .hypertool/OBSERVABILITY_QUICK_REFERENCE.md
- .hypertool/instrumentation/MANUAL_TESTING_PLAN.md
- .hypertool/instrumentation/run_manual_tests.py
- .hypertool/instrumentation/QUICK_TEST.md
- .hypertool/instrumentation/BASELINE_TEST_SUCCESS.md
- .hypertool/run_baseline_test.py"

echo "✅ Commit 4 complete"
echo ""

# Commit 5: Workflow Templates
echo "📝 Commit 5/5: Workflow Prompt Templates"
git add .augment/workflows/ \
        .cline/workflows/ \
        .github/workflows/package-release-hypertool.prompt.md

git commit -m "chore(workflows): Add multi-persona workflow prompt templates

Add prompt templates for Augment, Cline, and GitHub Copilot workflows:
- Package release workflow prompts
- Bug fix workflow prompts  
- Feature implementation workflow prompts

These templates guide LLM-based coding assistants through
multi-persona workflows with proper instrumentation.

Files:
- .augment/workflows/
- .cline/workflows/
- .github/workflows/package-release-hypertool.prompt.md"

echo "✅ Commit 5 complete"
echo ""

# Add the planning docs we just created
echo "📝 Bonus Commit: Git workflow documentation"
git add .hypertool/GIT_COMMIT_PLAN.md \
        .hypertool/PR_DESCRIPTION.md \
        .hypertool/scripts/create_phase5_pr.sh

git commit -m "chore(hypertool): Add git workflow documentation for Phase 5

Add planning documents for creating Phase 5 PR:
- Detailed commit plan with messages
- PR description template
- Automation script for executing plan

Files:
- .hypertool/GIT_COMMIT_PLAN.md
- .hypertool/PR_DESCRIPTION.md
- .hypertool/scripts/create_phase5_pr.sh"

echo "✅ Bonus commit complete"
echo ""

# Summary
echo "=========================================="
echo "✅ All commits created successfully!"
echo ""
echo "📊 Summary:"
git log --oneline -6
echo ""

# Next steps
echo "🎯 Next Steps:"
echo ""
echo "1. Review commits:"
echo "   git log --stat -6"
echo ""
echo "2. Push to GitHub:"
echo "   git push -u origin feature/phase5-apm-integration"
echo ""
echo "3. Create PR:"
echo "   gh pr create --title \"feat(hypertool): Phase 5 APM Integration - Prometheus, Langfuse, Grafana\" \\"
echo "                --body-file .hypertool/PR_DESCRIPTION.md \\"
echo "                --base agentic/core-architecture"
echo ""
echo "4. Or use GitHub CLI interactive:"
echo "   gh pr create --web"
echo ""

echo "Done! 🎉"
