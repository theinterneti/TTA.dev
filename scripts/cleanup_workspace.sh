#!/bin/bash
# TTA.dev Workspace Cleanup Script
# Organizes repository for optimal agentic usage

set -e  # Exit on error

REPO_ROOT="/home/thein/repos/TTA.dev"
cd "$REPO_ROOT"

echo "🧹 TTA.dev Workspace Cleanup Started"
echo "======================================"

# Create directory structure
echo "📁 Creating directory structure..."
mkdir -p docs/status-reports
mkdir -p docs/guides/quick-actions
mkdir -p docs/development/git
mkdir -p docs/troubleshooting
mkdir -p .vscode/workspaces
mkdir -p _archive/historical

# Move Status Reports & Summaries to docs/status-reports/
echo "📊 Moving status reports..."
mv -f MIGRATION_FINAL.md docs/status-reports/ 2>/dev/null || true
mv -f MIGRATION_SUMMARY.md docs/status-reports/ 2>/dev/null || true
mv -f SETUP_TEST_RESULTS.md docs/status-reports/ 2>/dev/null || true
mv -f VALIDATION_RESULTS.md docs/status-reports/ 2>/dev/null || true
mv -f WORKFLOW_REBASE_COMPLETE.md docs/status-reports/ 2>/dev/null || true
mv -f BRANCH_ORGANIZATION_COMPLETE.md docs/status-reports/ 2>/dev/null || true
mv -f ZSH_ENVIRONMENT_IMPLEMENTATION_COMPLETE.md docs/status-reports/ 2>/dev/null || true
mv -f LAZY_DEV_FINAL_SUMMARY.md docs/status-reports/ 2>/dev/null || true
mv -f PACKAGE_INVESTIGATION_SUMMARY.md docs/status-reports/ 2>/dev/null || true

# Move Guides to docs/guides/
echo "📚 Moving guides..."
mv -f PRODUCTION_DEPLOYMENT_GUIDE.md docs/guides/ 2>/dev/null || true
mv -f CLINE_INTEGRATION_GUIDE.md docs/guides/ 2>/dev/null || true
mv -f AI_CODER_WORKSPACES_GUIDE.md docs/guides/ 2>/dev/null || true
mv -f GITHUB_WORKFLOWS_EXPERT_GUIDE.md docs/guides/ 2>/dev/null || true
mv -f LAZY_DEV_QUICKREF.md docs/guides/ 2>/dev/null || true
mv -f ZSH_QUICK_START_CARD.md docs/guides/ 2>/dev/null || true

# Move Quick Actions to docs/guides/quick-actions/
echo "⚡ Moving quick action guides..."
mv -f GITHUB_WORKFLOWS_QUICK_ACTIONS.md docs/guides/quick-actions/ 2>/dev/null || true
mv -f RELEASE_QUICK_ACTIONS.md docs/guides/quick-actions/ 2>/dev/null || true

# Move Git/Worktree docs to docs/development/git/
echo "🌳 Moving git documentation..."
mv -f GIT_CLEANUP_PLAN.md docs/development/git/ 2>/dev/null || true
mv -f GIT_MANAGEMENT_SUMMARY.md docs/development/git/ 2>/dev/null || true
mv -f GIT_QUICKREF.md docs/development/git/ 2>/dev/null || true
mv -f GIT_STRUCTURE_DIAGRAM.txt docs/development/git/ 2>/dev/null || true
mv -f GIT_WORKTREE_BRANCH_ANALYSIS.md docs/development/git/ 2>/dev/null || true
mv -f GIT_WORKTREE_SUMMARY.md docs/development/git/ 2>/dev/null || true
mv -f WORKTREE_COORDINATION_ARCHITECTURE.md docs/development/git/ 2>/dev/null || true
mv -f WORKTREE_COORDINATION_PROTOCOL.md docs/development/git/ 2>/dev/null || true
mv -f WORKTREE_COORDINATION_QUICKSTART.md docs/development/git/ 2>/dev/null || true
mv -f WORKTREE_COORDINATION_SUMMARY.md docs/development/git/ 2>/dev/null || true
mv -f COPILOT_WORKTREE_INVESTIGATION.md docs/development/git/ 2>/dev/null || true

# Move Architecture Analysis to docs/architecture/
echo "🏗️ Moving architecture docs..."
mv -f PACKAGE_INVESTIGATION_ANALYSIS.md docs/architecture/ 2>/dev/null || true
mv -f REPOSITORY_STRUCTURE.md docs/architecture/ 2>/dev/null || true
mv -f BRANCH_ORGANIZATION_PLAN.md docs/architecture/ 2>/dev/null || true

# Move Troubleshooting to docs/troubleshooting/
echo "🔧 Moving troubleshooting docs..."
mv -f GEMINI_AUTH_ISSUE_DIAGNOSIS.md docs/troubleshooting/ 2>/dev/null || true
mv -f kb-broken-links-analysis.txt docs/troubleshooting/ 2>/dev/null || true
mv -f kb-real-broken-links.txt docs/troubleshooting/ 2>/dev/null || true

# Archive historical/one-time files
echo "📦 Archiving historical files..."
mv -f phases_2_3_complete_setup.md _archive/historical/ 2>/dev/null || true
mv -f verification_results.json _archive/historical/ 2>/dev/null || true
mv -f todos_current.csv _archive/historical/ 2>/dev/null || true
mv -f PRIMITIVES_CATALOG.md.corrupted.bak _archive/historical/ 2>/dev/null || true
mv -f simulation_final.txt _archive/historical/ 2>/dev/null || true
mv -f simulation_output.txt _archive/historical/ 2>/dev/null || true
mv -f long_term_proof_output.txt _archive/historical/ 2>/dev/null || true

# Move workspace files to .vscode/workspaces/
echo "💼 Organizing workspace files..."
mv -f augment.code-workspace .vscode/workspaces/ 2>/dev/null || true
mv -f augment-worktree.code-workspace .vscode/workspaces/ 2>/dev/null || true
mv -f cline.code-workspace .vscode/workspaces/ 2>/dev/null || true
mv -f cline-worktree.code-workspace .vscode/workspaces/ 2>/dev/null || true
mv -f github-copilot.code-workspace .vscode/workspaces/ 2>/dev/null || true
mv -f copilot-worktree.code-workspace .vscode/workspaces/ 2>/dev/null || true

# Move test files to tests/ if they exist
echo "🧪 Moving test files..."
mv -f test_observability.py tests/ 2>/dev/null || true
mv -f test_real_workflow.py tests/ 2>/dev/null || true

# Remove temporary/generated files
echo "🗑️ Removing temporary and generated files..."
rm -rf __pycache__/ 2>/dev/null || true
rm -rf .pytest_cache/ 2>/dev/null || true
rm -rf .ruff_cache/ 2>/dev/null || true
rm -rf htmlcov/ 2>/dev/null || true
rm -rf verification_test_*/ 2>/dev/null || true
rm -rf auto_learning_demo/ 2>/dev/null || true
rm -rf production_adaptive_demo/ 2>/dev/null || true
rm -f *.log 2>/dev/null || true
rm -f *_output.log 2>/dev/null || true
rm -f cache_primitive_*.log 2>/dev/null || true
rm -f retry_primitive_*.log 2>/dev/null || true
rm -f test_results.log 2>/dev/null || true
rm -f tta_traces.db 2>/dev/null || true
rm -f n8n.log 2>/dev/null || true

echo ""
echo "✅ Workspace cleanup complete!"
echo ""
echo "📊 Summary:"
echo "  - Status reports moved to docs/status-reports/"
echo "  - Guides moved to docs/guides/"
echo "  - Git docs moved to docs/development/git/"
echo "  - Architecture docs moved to docs/architecture/"
echo "  - Troubleshooting docs moved to docs/troubleshooting/"
echo "  - Workspace files moved to .vscode/workspaces/"
echo "  - Historical files archived to _archive/historical/"
echo "  - Temporary/generated files removed"
echo ""
echo "📝 Next steps:"
echo "  1. Review WORKSPACE_CLEANUP_PLAN.md for details"
echo "  2. Update .gitignore if needed"
echo "  3. Validate all documentation links"
echo "  4. Create WORKSPACE_ORGANIZATION.md guide"
