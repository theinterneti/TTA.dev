#!/bin/bash
# Keploy Framework - One-Command Setup Script
# Usage: ./setup-keploy.sh [project-name] [port]

set -e

PROJECT_NAME=${1:-"my-api"}
API_PORT=${2:-8000}

echo "🚀 Keploy Framework Setup"
echo "=========================="
echo "Project: $PROJECT_NAME"
echo "Port: $API_PORT"
echo ""

# Install framework
echo "📦 Installing keploy-framework..."
pip install keploy-framework

# Initialize
echo "⚙️  Initializing configuration..."
keploy-setup --name "$PROJECT_NAME" --port "$API_PORT" --command "uvicorn app:app --port $API_PORT"

# Create scripts directory
echo "📁 Creating scripts..."
mkdir -p scripts

# Download master menu template
cat > scripts/master-keploy.sh << 'EOF'
#!/bin/bash
# Master Keploy Menu - Interactive Control Panel

source "$(dirname "$0")/../templates/master-menu.sh"
EOF

chmod +x scripts/master-keploy.sh

# Setup pre-commit hook (optional)
read -p "Install pre-commit hook? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    mkdir -p .git/hooks
    cp templates/pre-commit-hook.sh .git/hooks/pre-commit
    chmod +x .git/hooks/pre-commit
    echo "✅ Pre-commit hook installed"
fi

# Setup GitHub Actions (optional)
read -p "Install GitHub Actions workflow? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    mkdir -p .github/workflows
    cp templates/github-workflow.yml .github/workflows/keploy-tests.yml
    echo "✅ GitHub Actions workflow installed"
fi

echo ""
echo "✨ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Start your API: uvicorn app:app --port $API_PORT"
echo "2. Run menu: ./scripts/master-keploy.sh"
echo "3. Choose '2' to record tests"
echo "4. Choose '3' to run tests"
