#!/bin/bash
set -e

echo "🧪 Testing GitHub Actions Workflow Rebuild"
echo "==========================================="
echo ""

# Test 1: Validate YAML syntax
echo "📝 Test 1: Validating YAML syntax..."
for workflow in .github/workflows/pr-validation.yml .github/workflows/merge-validation.yml; do
    echo "  Checking $workflow..."
    python3 -c "import yaml; yaml.safe_load(open('$workflow'))" && echo "  ✅ Valid YAML" || echo "  ❌ Invalid YAML"
done
echo ""

# Test 2: Validate composite action
echo "📝 Test 2: Validating composite action..."
composite_action=".github/actions/setup-tta-env/action.yml"
if [ -f "$composite_action" ]; then
    echo "  Checking $composite_action..."
    python3 -c "import yaml; yaml.safe_load(open('$composite_action'))" && echo "  ✅ Valid YAML" || echo "  ❌ Invalid YAML"
else
    echo "  ❌ Composite action not found at $composite_action"
fi
echo ""

# Test 3: Check for required keys in workflows
echo "📝 Test 3: Checking workflow structure..."
for workflow in .github/workflows/pr-validation.yml .github/workflows/merge-validation.yml; do
    echo "  Analyzing $workflow..."
    python3 -c "
import yaml
with open('$workflow') as f:
    w = yaml.safe_load(f)
    # 'on' becomes True in Python YAML
    required = ['name', 'jobs']
    has_trigger = True in w or 'on' in w
    missing = [k for k in required if k not in w]
    if missing:
        print(f'  ❌ Missing keys: {missing}')
    elif not has_trigger:
        print(f'  ❌ Missing trigger (on:)')
    else:
        print(f'  ✅ Has all required keys')
        print(f'  ℹ️  Jobs: {list(w[\"jobs\"].keys())}')
"
done
echo ""

# Test 4: Verify composite action is referenced correctly
echo "📝 Test 4: Verifying composite action references..."
grep -r "setup-tta-env" .github/workflows/pr-validation.yml .github/workflows/merge-validation.yml && \
    echo "  ✅ Composite action referenced" || \
    echo "  ❌ Composite action not referenced"
echo ""

# Test 5: Check concurrency groups
echo "📝 Test 5: Checking concurrency configuration..."
for workflow in .github/workflows/pr-validation.yml .github/workflows/merge-validation.yml; do
    echo "  Checking $workflow..."
    if grep -q "concurrency:" "$workflow"; then
        echo "  ✅ Has concurrency control"
    else
        echo "  ⚠️  No concurrency control"
    fi
done
echo ""

echo "✅ All validation tests complete!"
echo ""
echo "Next steps:"
echo "1. Push these changes to a test branch"
echo "2. Create a test PR to validate pr-validation.yml"
echo "3. Merge to main to validate merge-validation.yml"
echo "4. Monitor GitHub Actions UI for execution"
