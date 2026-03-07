#!/usr/bin/env bash
# Pin GitHub Actions to commit SHAs for security
# Usage: bash scripts/pin_actions.sh

set -euo pipefail

WORKFLOW_DIR=".github/workflows"
TEMP_FILE=$(mktemp)

echo "🔒 Pinning GitHub Actions to commit SHAs..."

# Find all actions/@version patterns in workflow files
grep -rn "uses:.*@v[0-9]" "$WORKFLOW_DIR" || true > "$TEMP_FILE"

if [ ! -s "$TEMP_FILE" ]; then
    echo "✅ All actions already pinned to SHAs"
    rm "$TEMP_FILE"
    exit 0
fi

echo "⚠️  Found unpinned actions:"
cat "$TEMP_FILE"
echo ""
echo "🔧 To pin these actions, use: gh api repos/{owner}/{repo}/commits/{branch} --jq .sha"
echo "   Example: actions/checkout@v4 → actions/checkout@<SHA>"
echo ""
echo "📖 See: https://docs.github.com/en/actions/security-guides/security-hardening-for-github-actions#using-third-party-actions"

rm "$TEMP_FILE"
exit 1
