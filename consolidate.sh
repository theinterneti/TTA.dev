#!/bin/bash
set -e

echo "=== TTA.dev Repository Consolidation ==="

# Remove old attempt
rm -rf tta_dev/

# Create new unified structure
echo "Creating unified structure..."
mkdir -p tta-dev/{primitives,observability,core,agents,integrations,skills,ui}
mkdir -p tta-dev/agents/{context,coordination}
mkdir -p tta-dev/observability/apm
mkdir -p tta-dev/ui/{vscode,web}

# Move core packages
echo "Moving core packages..."
if [ -d "packages/tta-primitives/src/tta_dev_primitives" ]; then
    cp -r packages/tta-primitives/src/tta_dev_primitives/* tta-dev/primitives/
fi

if [ -d "packages/tta-observability/src" ]; then
    cp -r packages/tta-observability/src/* tta-dev/observability/
fi

if [ -d "packages/tta-core/src" ]; then
    cp -r packages/tta-core/src/* tta-dev/core/
fi

# Consolidate platform
echo "Consolidating platform..."
if [ -d "platform/agent-context" ]; then
    cp -r platform/agent-context/* tta-dev/agents/context/
fi

if [ -d "platform/agent-coordination" ]; then
    cp -r platform/agent-coordination/* tta-dev/agents/coordination/
fi

if [ -d "platform/apm" ]; then
    cp -r platform/apm/* tta-dev/observability/apm/
fi

if [ -d "platform/integrations" ]; then
    cp -r platform/integrations/* tta-dev/integrations/
fi

if [ -d "platform/skills" ]; then
    cp -r platform/skills/* tta-dev/skills/
fi

# Consolidate UI
echo "Consolidating UI..."
if [ -d "apps/observability-vscode" ]; then
    cp -r apps/observability-vscode/* tta-dev/ui/vscode/
fi

if [ -d "apps/streamlit-mvp" ]; then
    cp -r apps/streamlit-mvp/* tta-dev/ui/web/
fi

# Archive and review items
echo "Archiving non-essential items..."
mkdir -p local/{archive,review}

if [ -d "apps/n8n" ]; then
    mv apps/n8n local/archive/ 2>/dev/null || true
fi

if [ -d "packages/python-pathway" ]; then
    mv packages/python-pathway local/review/ 2>/dev/null || true
fi

if [ -d "platform/dolt" ]; then
    mv platform/dolt local/review/ 2>/dev/null || true
fi

if [ -d "apps/platform" ]; then
    mv apps/platform local/review/ 2>/dev/null || true
fi

echo "✅ Consolidation complete!"
echo "Review tta-dev/ structure and local/review/ before proceeding."
