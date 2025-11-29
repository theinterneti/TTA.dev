#!/usr/bin/env bash
# Wrapper script to run the configuration generator from the correct directory

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$WORKSPACE_ROOT/packages/tta-dev-primitives"

echo "🔧 Generating AI assistant configurations..."
echo "📂 Workspace: $WORKSPACE_ROOT"
echo ""

uv run python "$WORKSPACE_ROOT/scripts/config/generate_assistant_configs.py" \
    --workspace "$WORKSPACE_ROOT" \
    "$@"
