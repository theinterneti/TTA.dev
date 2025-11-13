#!/bin/bash

# This script refactors the TTA.dev repository to align with its new core purpose:
# exclusively containing the framework for building AI agents.
# Product-related code, internal tooling, and deprecated files will be moved
# to temporary directories for later inspection and relocation.

# --- 1. Create temporary and new framework directories ---
echo "Creating temporary directories for product-related and deprecated files..."
mkdir -p _TTA_PRODUCT_TO_BE_MOVED
mkdir -p _DEPRECATED
echo "Creating the main framework directory..."
mkdir -p framework

# --- 2. Move core framework files to the 'framework' directory first ---
# This prevents them from being moved with the wildcard *.md command later.
echo "Moving essential framework markdown files..."
mv README.md framework/
mv CONTRIBUTING.md framework/
mv LICENSE framework/
mv ROADMAP.md framework/
mv AGENTS.md framework/
mv GETTING_STARTED.md framework/
mv MCP_SERVERS.md framework/
mv PRIMITIVES_CATALOG.md framework/
mv CHANGELOG.md framework/


# --- 3. Move Product-related materials to _TTA_PRODUCT_TO_BE_MOVED ---
echo "Moving product-related materials, reports, and agent configurations..."

# Move all remaining markdown files (mostly status reports)
echo "Moving remaining markdown files (product-related or temporary)..."
mv *.md _TTA_PRODUCT_TO_BE_MOVED/ 2>/dev/null

# Move agent-specific configurations and internal tooling
echo "Moving agent-specific configurations..."
mv .ace _TTA_PRODUCT_TO_BE_MOVED/ 2>/dev/null
mv .augment _TTA_PRODUCT_TO_BE_MOVED/ 2>/dev/null
mv .cline _TTA_PRODUCT_TO_BE_MOVED/ 2>/dev/null
mv .cursor _TTA_PRODUCT_TO_BE_MOVED/ 2>/dev/null
mv .gemini _TTA_PRODUCT_TO_BE_MOVED/ 2>/dev/null
mv .tta _TTA_PRODUCT_TO_BE_MOVED/ 2>/dev/null
mv .universal-instructions _TTA_PRODUCT_TO_BE_MOVED/ 2>/dev/null

# Move product-specific directories
echo "Moving product-specific directories..."
mv apps _TTA_PRODUCT_TO_BE_MOVED/ 2>/dev/null
mv data _TTA_PRODUCT_TO_BE_MOVED/ 2>/dev/null
mv datasets _TTA_PRODUCT_TO_BE_MOVED/ 2>/dev/null
mv experiments _TTA_PRODUCT_TO_BE_MOVED/ 2>/dev/null
mv local _TTA_PRODUCT_TO_BE_MOVED/ 2>/dev/null
mv output _TTA_PRODUCT_TO_BE_MOVED/ 2>/dev/null
mv tta-agent-coordination _TTA_PRODUCT_TO_BE_MOVED/ 2>/dev/null
mv tta_secrets _TTA_PRODUCT_TO_BE_MOVED/ 2>/dev/null
mv workflows _TTA_PRODUCT_TO_BE_MOVED/ 2>/dev/null
mv production_adaptive_demo _TTA_PRODUCT_TO_BE_MOVED/ 2>/dev/null
mv verification_test_1 _TTA_PRODUCT_TO_BE_MOVED/ 2>/dev/null
mv verification_test_2 _TTA_PRODUCT_TO_BE_MOVED/ 2>/dev/null
mv verification_test_3 _TTA_PRODUCT_TO_BE_MOVED/ 2>/dev/null
mv verification_test_4 _TTA_PRODUCT_TO_BE_MOVED/ 2>/dev/null
mv verification_test_5 _TTA_PRODUCT_TO_BE_MOVED/ 2>/dev/null


# Move product-related files
echo "Moving product-related files..."
mv augment.code-workspace _TTA_PRODUCT_TO_BE_MOVED/ 2>/dev/null
mv CLINE_INTEGRATION_GAP_ANAL _TTA_PRODUCT_TO_BE_MOVED/ 2>/dev/null
mv github-copilot.code-workspace _TTA_PRODUCT_TO_BE_MOVED/ 2>/dev/null
mv phases_2_3_complete_setup.md _TTA_PRODUCT_TO_BE_MOVED/ 2>/dev/null
mv tasks_github.json _TTA_PRODUCT_TO_BE_MOVED/ 2>/dev/null
mv tta_self_assessment_plan.md _TTA_PRODUCT_TO_BE_MOVED/ 2>/dev/null
mv tta_self_assessment_todo.md _TTA_PRODUCT_TO_BE_MOVED/ 2>/dev/null
mv self_assessment_workflow.py _TTA_PRODUCT_TO_BE_MOVED/ 2>/dev/null
mv setup_n8n_github_dashboard.sh _TTA_PRODUCT_TO_BE_MOVED/ 2>/dev/null
mv simulation_final.txt _TTA_PRODUCT_TO_BE_MOVED/ 2>/dev/null
mv simulation_output.txt _TTA_PRODUCT_TO_BE_MOVED/ 2>/dev/null
mv test_generation_playbook.json _TTA_PRODUCT_TO_BE_MOVED/ 2>/dev/null
mv test_llm_playbook.json _TTA_PRODUCT_TO_BE_MOVED/ 2>/dev/null
mv todo_list.md _TTA_PRODUCT_TO_BE_MOVED/ 2>/dev/null
mv todos_current.csv _TTA_PRODUCT_TO_BE_MOVED/ 2>/dev/null
mv validate_templates.py _TTA_PRODUCT_TO_BE_MOVED/ 2>/dev/null
mv verification_results.json _TTA_PRODUCT_TO_BE_MOVED/ 2>/dev/null
mv workspace_planning_todo.md _TTA_PRODUCT_TO_BE_MOVED/ 2>/dev/null
mv workspace_qa_todo.md _TTA_PRODUCT_TO_BE_MOVED/ 2>/dev/null
mv ace_advanced_playbook.json _TTA_PRODUCT_TO_BE_MOVED/ 2>/dev/null
mv ace_demo_playbook.json _TTA_PRODUCT_TO_BE_MOVED/ 2>/dev/null
mv phase3_refinement_playbook.json _TTA_PRODUCT_TO_BE_MOVED/ 2>/dev/null
mv retry_primitive_tests_playbook_phase3.json _TTA_PRODUCT_TO_BE_MOVED/ 2>/dev/null
mv retry_primitive_tests_playbook_phase4.json _TTA_PRODUCT_TO_BE_MOVED/ 2>/dev/null
mv robust_n8n_setup.py _TTA_PRODUCT_TO_BE_MOVED/ 2>/dev/null
mv robust_n8n_setup_fixed.py _TTA_PRODUCT_TO_BE_MOVED/ 2>/dev/null


# --- 4. Move Deprecated/Orphaned files to _DEPRECATED ---
echo "Moving deprecated and orphaned files to _DEPRECATED..."

# Directories
mv archive _DEPRECATED/ 2>/dev/null
mv auto_learning_demo _DEPRECATED/ 2>/dev/null
mv custom _DEPRECATED/ 2>/dev/null

# Files
mv apm.yml _DEPRECATED/ 2>/dev/null
mv migration_output.txt _DEPRECATED/ 2>/dev/null
mv pytest_results.txt _DEPRECATED/ 2>/dev/null
mv PRIMITIVES_CATALOG.md.corrupted.bak _DEPRECATED/ 2>/dev/null
mv test_todos.csv _DEPRECATED/ 2>/dev/null
mv todo_scan_results.txt _DEPRECATED/ 2>/dev/null
mv todos.csv _DEPRECATED/ 2>/dev/null

# --- 5. Move remaining Framework-related items into the 'framework' directory ---
echo "Moving core framework components into the 'framework' directory..."

# Root-level framework files
mv .clinerules framework/ 2>/dev/null
mv .env.example framework/ 2>/dev/null
mv .env.template framework/ 2>/dev/null
mv .gitignore framework/ 2>/dev/null
mv .ruffignore framework/ 2>/dev/null
mv cline.code-workspace framework/ 2>/dev/null
mv codecov.yml framework/ 2>/dev/null
mv e2b.Dockerfile.debug-minimal framework/ 2>/dev/null
mv package-lock.json framework/ 2>/dev/null
mv package.json framework/ 2>/dev/null
mv pyproject.toml framework/ 2>/dev/null
mv uv.lock framework/ 2>/dev/null
mv pyrightconfig.json framework/ 2>/dev/null


# Core framework directories
mv .devcontainer framework/ 2>/dev/null
mv .github framework/ 2>/dev/null
mv .vscode framework/ 2>/dev/null
mv docs framework/ 2>/dev/null
mv examples framework/ 2>/dev/null
mv logseq framework/ 2>/dev/null
mv monitoring framework/ 2>/dev/null
mv packages framework/ 2>/dev/null
mv scripts framework/ 2>/dev/null
mv tests framework/ 2>/dev/null

echo "Repository refactoring complete."
echo "Product-related files are in _TTA_PRODUCT_TO_BE_MOVED/"
echo "Deprecated files are in _DEPRECATED/"
echo "Framework files are now organized under the 'framework/' directory."
