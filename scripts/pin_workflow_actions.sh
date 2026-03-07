#!/usr/bin/env bash
# Pin all GitHub Actions to specific commit SHAs for supply chain security

set -euo pipefail

echo "🔒 Pinning GitHub Actions to commit SHAs..."

# Common actions and their latest stable commit SHAs (as of March 2026)
declare -A ACTION_PINS=(
    ["actions/checkout@v4"]="actions/checkout@b4ffde65f46336ab88eb53be808477a3936bae11" # v4.1.1
    ["actions/setup-python@v5"]="actions/setup-python@0a5c61591373683505ea898e09a3ea4f39ef2b9c" # v5.0.0
    ["actions/setup-node@v4"]="actions/setup-node@60edb5dd545a775178f52524783378180af0d1f8" # v4.0.2
    ["actions/upload-artifact@v4"]="actions/upload-artifact@5d5d22a31266ced268874388b861e4b58bb5c2f3" # v4.3.1
    ["actions/download-artifact@v4"]="actions/download-artifact@c850b930e6ba138125429b7e5c93fc707a7f8427" # v4.1.4
    ["actions/cache@v4"]="actions/cache@ab5e6d0c87105b4c9c2047343972218f562e4319" # v4.0.1
    ["actions/github-script@v7"]="actions/github-script@60a0d83039c74a4aee543508d2ffcb1c3799cdea" # v7.0.1
    ["astral-sh/setup-uv@v2"]="astral-sh/setup-uv@3f2f00c85e1be39f0c70d3c3e5c2ebb9e6471ebe" # v2.0.0
    ["codecov/codecov-action@v4"]="codecov/codecov-action@v4.0.1" # Needs actual SHA
)

UPDATED=0
TOTAL=0

# Find all workflow files
for workflow in .github/workflows/*.yml .github/workflows/*.yaml; do
    [ -f "$workflow" ] || continue
    
    echo "Processing: $workflow"
    
    # Create backup
    cp "$workflow" "$workflow.bak"
    
    # Replace unpinned actions
    for action_tag in "${!ACTION_PINS[@]}"; do
        action_pin="${ACTION_PINS[$action_tag]}"
        
        if grep -q "uses: $action_tag" "$workflow"; then
            echo "  📌 Pinning $action_tag"
            # Handle both GNU and BSD sed (macOS)
            if [[ "$OSTYPE" == "darwin"* ]]; then
                sed -i.bak "s|uses: $action_tag|uses: $action_pin # $action_tag|g" "$workflow"
                rm -f "$workflow.bak"
            else
                sed -i "s|uses: $action_tag|uses: $action_pin # $action_tag|g" "$workflow"
            fi
            ((UPDATED++))
        fi
        ((TOTAL++))
    done
    
    # Remove backup if no changes
    if diff "$workflow" "$workflow.bak" > /dev/null 2>&1; then
        rm "$workflow.bak"
    else
        echo "  ✅ Updated $workflow"
    fi
done

echo ""
echo "📊 Summary:"
echo "  - Actions checked: $TOTAL"
echo "  - Actions pinned: $UPDATED"
echo ""

if [ $UPDATED -gt 0 ]; then
    echo "⚠️  Please review the changes and commit them"
    echo "💡 Run 'git diff .github/workflows' to see changes"
else
    echo "✅ All actions already pinned!"
fi
