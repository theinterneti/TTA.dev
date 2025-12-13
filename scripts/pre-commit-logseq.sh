#!/bin/bash
# Pre-commit hook to sync Logseq graph

echo " Syncing Logseq graph..."
python3 platform/kb-automation/src/tta_kb_automation/tools/logseq_graph_sync.py "$@"

# Check if files were modified
MODIFIED_FILES=$(git diff --name-only "$@")
if [ -n "$MODIFIED_FILES" ]; then
    echo "⚠️  Logseq Graph Agent modified some files (injected citations)."
    echo "Please stage these changes and commit again:"
    echo "$MODIFIED_FILES"
    exit 1
fi
