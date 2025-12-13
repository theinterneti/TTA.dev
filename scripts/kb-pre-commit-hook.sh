#!/bin/bash
# KB Maintenance Pre-commit Hook
# Place in TTA.dev/.git/hooks/pre-commit or run via pre-commit framework

set -e

# Only run on changes to platform/, scripts/, docs/
CHANGED_FILES=$(git diff --cached --name-only --diff-filter=ACM | grep -E "^(platform|scripts|docs)/" || true)

if [ -z "$CHANGED_FILES" ]; then
    exit 0
fi

echo "🗄️  KB Pre-commit Hook: Detected changes in tracked directories"

# Check if TTA-notes repo exists
TTA_NOTES="${HOME}/repos/TTA-notes"
if [ ! -d "$TTA_NOTES" ]; then
    echo "⚠️  TTA-notes repo not found at $TTA_NOTES, skipping KB sync"
    exit 0
fi

# Run lightweight validation only (full sync is expensive)
echo "   Running KB validation..."
python3 "$TTA_NOTES/scripts/kb_maintenance.py" --validate-only 2>/dev/null || true

echo "✅ KB validation complete"
echo "💡 Tip: Run 'python3 ~/repos/TTA-notes/scripts/kb_maintenance.py' for full sync"
