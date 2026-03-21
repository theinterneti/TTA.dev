#!/usr/bin/env bash
# Consolidate and clean up GitHub Actions workflows
set -euo pipefail

WORKFLOWS_DIR=".github/workflows"
ARCHIVE_DIR="${WORKFLOWS_DIR}/_archive"

echo "🧹 GitHub Actions Workflow Consolidation"
echo "========================================"

# Create archive directories
mkdir -p "${ARCHIVE_DIR}/experimental"
mkdir -p "${ARCHIVE_DIR}/duplicates"
mkdir -p "${ARCHIVE_DIR}/deprecated"
mkdir -p "${WORKFLOWS_DIR}/reusable"

# Archive experimental Gemini workflows (keep only the working one)
echo "📦 Archiving experimental workflows..."
if [ -d "${WORKFLOWS_DIR}/experimental/gemini" ]; then
    # Keep only gemini-triage.yml as the reference implementation
    find "${WORKFLOWS_DIR}/experimental/gemini" -name "*.yml" ! -name "gemini-triage.yml" -exec mv {} "${ARCHIVE_DIR}/experimental/" \;

    # If gemini-triage exists, keep it
    if [ -f "${WORKFLOWS_DIR}/experimental/gemini/gemini-triage.yml" ]; then
        mv "${WORKFLOWS_DIR}/experimental/gemini/gemini-triage.yml" "${ARCHIVE_DIR}/experimental/gemini-triage.yml.reference"
    fi

    # Remove empty experimental directory
    rmdir "${WORKFLOWS_DIR}/experimental/gemini" 2>/dev/null || true
    rmdir "${WORKFLOWS_DIR}/experimental" 2>/dev/null || true
fi

# Archive duplicate PR validation workflows (keep consolidated-pr-validation.yml)
echo "📦 Archiving duplicate PR validation workflows..."
for file in pr-validation.yml pr-validation-v2.yml agentic-pr-review.yml; do
    [ -f "${WORKFLOWS_DIR}/${file}" ] && mv "${WORKFLOWS_DIR}/${file}" "${ARCHIVE_DIR}/duplicates/"
done

# Archive duplicate merge gate workflows (keep consolidated-merge-gate.yml)
echo "📦 Archiving duplicate merge gate workflows..."
for file in merge-validation.yml merge-validation-v2.yml; do
    [ -f "${WORKFLOWS_DIR}/${file}" ] && mv "${WORKFLOWS_DIR}/${file}" "${ARCHIVE_DIR}/duplicates/"
done

# Archive duplicate quality check workflows (keep ci.yml)
echo "📦 Archiving duplicate quality workflows..."
for file in quality-check.yml test-quality-checks.yml agentic-checks.yml; do
    [ -f "${WORKFLOWS_DIR}/${file}" ] && mv "${WORKFLOWS_DIR}/${file}" "${ARCHIVE_DIR}/duplicates/"
done

# Archive duplicate test workflows (keep ci.yml which includes tests)
echo "📦 Archiving duplicate test workflows..."
for file in tests.yml tests-split.yml; do
    [ -f "${WORKFLOWS_DIR}/${file}" ] && mv "${WORKFLOWS_DIR}/${file}" "${ARCHIVE_DIR}/duplicates/"
done

# Archive meta-workflows and deprecated files
echo "📦 Archiving deprecated workflows..."
for file in workflow-comparison.yml auto-lazy-dev-setup.yml copilot-setup-steps.yml; do
    [ -f "${WORKFLOWS_DIR}/${file}" ] && mv "${WORKFLOWS_DIR}/${file}" "${ARCHIVE_DIR}/deprecated/"
done

# Move reusable workflows to dedicated directory
echo "📦 Organizing reusable workflows..."
for file in "${WORKFLOWS_DIR}"/reusable-*.yml; do
    if [ -f "$file" ]; then
        filename=$(basename "$file")
        new_name=$(echo "$filename" | sed 's/reusable-//')
        mv "$file" "${WORKFLOWS_DIR}/reusable/${new_name}"
    fi
done

# Archive duplicate AI review workflows (keep consolidated-ai-review.yml)
echo "📦 Archiving duplicate AI review workflows..."
for file in orchestration-pr-review.yml agentic-self-heal.yml; do
    [ -f "${WORKFLOWS_DIR}/${file}" ] && mv "${WORKFLOWS_DIR}/${file}" "${ARCHIVE_DIR}/duplicates/"
done

# Archive platform compatibility duplicates if consolidated version exists
if [ -f "${WORKFLOWS_DIR}/consolidated-platform-compatibility.yml" ]; then
    echo "📦 Archiving old platform compatibility workflows..."
    for file in mcp-validation.yml test-mcp-versions.yml; do
        [ -f "${WORKFLOWS_DIR}/${file}" ] && mv "${WORKFLOWS_DIR}/${file}" "${ARCHIVE_DIR}/duplicates/"
    done
fi

echo ""
echo "✅ Consolidation complete!"
echo ""
echo "📊 Final structure:"
find "${WORKFLOWS_DIR}" -name "*.yml" -o -name "*.yaml" -o -name "*.md" | grep -v "_archive" | sort

echo ""
echo "📦 Archived files:"
find "${ARCHIVE_DIR}" -type f | wc -l
echo ""
echo "🎯 Next steps:"
echo "  1. Review consolidated workflows"
echo "  2. Run: ./scripts/pin_workflow_actions.sh"
echo "  3. Run: python scripts/ci/add_strict_permissions.py"
echo "  4. Commit changes"
