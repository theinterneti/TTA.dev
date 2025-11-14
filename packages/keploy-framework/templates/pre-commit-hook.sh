#!/bin/bash
# Pre-commit hook for Keploy test validation
# Copy to .git/hooks/pre-commit and make executable

set -e

echo "🧪 Running Keploy tests before commit..."

# Run tests
keploy-test --quiet

if [ $? -eq 0 ]; then
    echo "✅ All Keploy tests passed"
    exit 0
else
    echo "❌ Keploy tests failed - commit blocked"
    echo "Fix failing tests or run: git commit --no-verify"
    exit 1
fi
