#!/bin/bash
# Validate n8n workflows and node availability

set -e

echo "🔍 Validating n8n Workflows and Nodes..."
echo ""

# Check if n8n is running
if ! lsof -Pi :5678 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "❌ n8n is not running. Please start n8n first."
    exit 1
fi

echo "✅ n8n is running on port 5678"
echo ""

# Export current node types
echo "📦 Exporting available node types..."
npx n8n export:nodes --output /tmp/n8n-current-nodes.json 2>/dev/null
echo "✓ Exported to /tmp/n8n-current-nodes.json"
echo ""

# Check for LangChain nodes
echo "🔎 Checking for LangChain nodes..."
if grep -q "langchain" /tmp/n8n-current-nodes.json 2>/dev/null; then
    echo "✅ LangChain nodes found:"
    grep -o '"@n8n/n8n-nodes-langchain[^"]*"' /tmp/n8n-current-nodes.json | sort | uniq | head -5
else
    echo "⚠️  No LangChain nodes detected"
fi
echo ""

# Check for Gemini-related nodes
echo "🤖 Checking for Gemini/Google nodes..."
if grep -qi "gemini\|google.*ai" /tmp/n8n-current-nodes.json 2>/dev/null; then
    echo "✅ Gemini-related nodes found:"
    grep -oi '"[^"]*gemini[^"]*"\|"[^"]*google.*ai[^"]*"' /tmp/n8n-current-nodes.json | sort | uniq | head -5
else
    echo "⚠️  No Gemini-specific nodes detected"
fi
echo ""

# List imported workflows
echo "📋 Listing imported workflows..."
npx n8n export:workflow --all --output /tmp 2>/dev/null && {
    echo "✅ Workflows exported to /tmp/"
    ls -1 /tmp/My_workflow_*.json 2>/dev/null | wc -l | xargs echo "   Total workflows:"
} || {
    echo "⚠️  Could not export workflows"
}
echo ""

# Check workflow files for unrecognized node types
echo "🔍 Checking for unrecognized node types in workflow files..."
unrecognized=0

check_workflow() {
    local file=$1
    local name=$(basename "$file")

    # Extract all node types from the workflow
    node_types=$(python3 -c "
import json
import sys

try:
    with open('$file') as f:
        data = json.load(f)

    types = set()
    if 'nodes' in data:
        for node in data['nodes']:
            if 'type' in node:
                types.add(node['type'])

    for t in sorted(types):
        print(t)
except Exception as e:
    print(f'Error: {e}', file=sys.stderr)
" 2>&1)

    # Check if any types are not in the available nodes
    for node_type in $node_types; do
        if ! grep -q "\"$node_type\"" /tmp/n8n-current-nodes.json 2>/dev/null; then
            echo "  ⚠️  $name: Unrecognized node type: $node_type"
            ((unrecognized++))
        fi
    done
}

# Check all workflow files
for workflow in workflows/n8n_*.json n8n_git_automation_workflow.json n8n_github_health_dashboard.json; do
    if [ -f "$workflow" ]; then
        check_workflow "$workflow"
    fi
done

if [ $unrecognized -eq 0 ]; then
    echo "✅ All node types recognized!"
else
    echo "⚠️  Found $unrecognized unrecognized node type(s)"
fi
echo ""

# Summary
echo "📊 Validation Summary:"
echo "   ✅ n8n running: Yes"
echo "   ✅ Workflows imported: $(ls -1 workflows/n8n_*.json 2>/dev/null | wc -l) from workflows/"
echo "   ✅ Workflows imported: $(ls -1 n8n_*.json 2>/dev/null | grep -v node_modules | wc -l) from root"
echo "   ✅ LangChain nodes: $(grep -c "langchain" /tmp/n8n-current-nodes.json 2>/dev/null || echo 0) available"
echo ""
echo "🎯 Next Steps:"
echo "   1. Open n8n UI: http://localhost:5678"
echo "   2. Browse workflows to verify they appear"
echo "   3. Open a workflow and check node configurations"
echo "   4. Test a safe workflow (e.g., one without git operations)"
echo ""
