#!/bin/bash
# Fix n8n workflow imports by adding required 'active' field and re-importing cleanly

set -e

echo "🔧 Fixing n8n workflow imports..."
echo ""

# Backup original files
echo "📦 Creating backups..."
mkdir -p workflows/backup
cp -f workflows/*.json workflows/backup/ 2>/dev/null || true
cp -f n8n_*.json workflows/backup/ 2>/dev/null || true

# Function to add 'active' field to JSON if missing
fix_workflow_json() {
    local file=$1
    local temp_file="${file}.tmp"

    echo "  Checking: $(basename "$file")"

    # Check if 'active' field already exists
    if grep -q '"active"' "$file"; then
        echo "    ✓ Already has 'active' field"
        return 0
    fi

    # Add 'active': false after the opening brace
    # This uses Python for reliable JSON manipulation
    python3 -c "
import json
import sys

with open('$file', 'r') as f:
    data = json.load(f)

# Add 'active' field if not present
if 'active' not in data:
    data['active'] = False

with open('$temp_file', 'w') as f:
    json.dump(data, f, indent=2)
    f.write('\n')
" || {
        echo "    ✗ Failed to parse JSON"
        return 1
    }

    # Replace original file
    mv "$temp_file" "$file"
    echo "    ✓ Added 'active': false"
}

# Fix all workflow JSONs
echo ""
echo "🔨 Fixing workflow files..."

# Fix workflows in workflows/ directory
for workflow in workflows/n8n_*.json; do
    if [ -f "$workflow" ]; then
        fix_workflow_json "$workflow"
    fi
done

# Fix workflows in root directory
for workflow in n8n_*.json; do
    if [ -f "$workflow" ]; then
        fix_workflow_json "$workflow"
    fi
done

echo ""
echo "✅ All workflow files fixed!"
echo ""

# Check if n8n is running
if ! lsof -Pi :5678 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️  n8n is not running. Please start n8n first:"
    echo "   ./start-n8n.sh"
    exit 1
fi

echo "🔄 Re-importing workflows..."
echo ""

# Function to import workflow
import_workflow() {
    local file=$1
    local name=$(basename "$file")

    echo "  Importing: $name"

    if npx n8n import:workflow --input "$file" 2>&1 | grep -q "Successfully imported"; then
        echo "    ✓ Imported successfully"
    else
        echo "    ⚠️  Import may have warnings (check n8n UI)"
    fi
}

# Import workflows from workflows/ directory
for workflow in workflows/n8n_*.json; do
    if [ -f "$workflow" ]; then
        import_workflow "$workflow"
    fi
done

# Import workflows from root directory
for workflow in n8n_git_automation_workflow.json n8n_github_health_dashboard.json; do
    if [ -f "$workflow" ]; then
        import_workflow "$workflow"
    fi
done

echo ""
echo "✅ Import complete!"
echo ""
echo "📋 Next steps:"
echo "   1. Open n8n at http://localhost:5678"
echo "   2. Verify workflows appear in the UI"
echo "   3. Check node configurations (especially LangChain/Gemini nodes)"
echo "   4. Test a safe workflow (without git commits/pushes)"
echo ""
echo "💾 Backups saved in workflows/backup/"
echo ""
