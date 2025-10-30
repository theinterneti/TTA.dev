#!/bin/bash
# Setup GitHub Secrets for Logseq Sync Workflows
# This script adds the required secrets to TTA.dev and TTA-notes repositories

set -e

echo "🔐 GitHub Secrets Setup for Logseq Sync"
echo "========================================"
echo ""

# Check if gh CLI is installed
if ! command -v gh &> /dev/null; then
    echo "❌ GitHub CLI (gh) is not installed"
    echo ""
    echo "Install it with:"
    echo "  Ubuntu/Debian: sudo apt install gh"
    echo "  macOS: brew install gh"
    echo "  Or visit: https://cli.github.com/"
    exit 1
fi

# Check if authenticated
if ! gh auth status &> /dev/null; then
    echo "❌ Not authenticated with GitHub CLI"
    echo ""
    echo "Run: gh auth login"
    exit 1
fi

echo "✅ GitHub CLI is installed and authenticated"
echo ""

# Prompt for tokens
echo "Please paste your tokens (they will be hidden):"
echo ""
read -sp "TTA_NOTES_PAT (for TTA.dev → TTA-notes): " TTA_NOTES_PAT
echo ""
read -sp "TTA_DEV_PAT (for TTA-notes → TTA.dev): " TTA_DEV_PAT
echo ""
echo ""

# Validate tokens are not empty
if [ -z "$TTA_NOTES_PAT" ]; then
    echo "❌ TTA_NOTES_PAT cannot be empty"
    exit 1
fi

if [ -z "$TTA_DEV_PAT" ]; then
    echo "❌ TTA_DEV_PAT cannot be empty"
    exit 1
fi

# Add TTA_NOTES_PAT to TTA.dev repository
echo "📝 Adding TTA_NOTES_PAT to theinterneti/TTA.dev..."
if gh secret set TTA_NOTES_PAT --repo theinterneti/TTA.dev --body "$TTA_NOTES_PAT"; then
    echo "✅ TTA_NOTES_PAT added to TTA.dev"
else
    echo "❌ Failed to add TTA_NOTES_PAT to TTA.dev"
    exit 1
fi

echo ""

# Add TTA_DEV_PAT to TTA-notes repository
echo "📝 Adding TTA_DEV_PAT to theinterneti/TTA-notes..."
if gh secret set TTA_DEV_PAT --repo theinterneti/TTA-notes --body "$TTA_DEV_PAT"; then
    echo "✅ TTA_DEV_PAT added to TTA-notes"
else
    echo "❌ Failed to add TTA_DEV_PAT to TTA-notes"
    exit 1
fi

echo ""
echo "🎉 All secrets configured successfully!"
echo ""
echo "Next steps:"
echo "1. Deploy TTA-notes workflow"
echo "2. Push workflows to TTA.dev"
echo "3. Test the sync"
echo ""

