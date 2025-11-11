#!/bin/bash
set -e

echo "🏗️ Setting up TTA.dev Product Building Environment..."

# Update package manager
sudo apt-get update

# Install additional development tools
sudo apt-get install -y \
    postgresql-client \
    redis-tools \
    htop \
    tree \
    jq \
    curl \
    wget \
    vim \
    git-lfs

# Install UV package manager (latest version)
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"

# Add UV to PATH for current session
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc

# Install Python dependencies
echo "📦 Installing Python dependencies..."
uv sync --all-extras

# Setup pre-commit hooks
echo "🔧 Setting up pre-commit hooks..."
uv run pre-commit install || echo "⚠️ Pre-commit setup skipped (not configured)"

# Create ACE directory structure
echo "🧠 Setting up ACE knowledge capture system..."
mkdir -p .ace/knowledge-base/{development-patterns,integration-learnings,performance-insights,quality-strategies}
mkdir -p .ace/patterns/{workflow-templates,testing-strategies,deployment-patterns}
mkdir -p .ace/learnings/{daily-insights,milestone-reviews,retrospectives}
mkdir -p .ace/templates/{project-structure,tooling-configs,quality-gates}

# Create ACE initialization script
cat > .ace/init-session.py << 'EOF'
#!/usr/bin/env python3
"""Initialize ACE learning session"""

import json
import datetime
from pathlib import Path

def init_ace_session():
    """Initialize new ACE learning session."""
    session_data = {
        "session_id": f"session_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "start_time": datetime.datetime.now().isoformat(),
        "focus_area": "TTA Development",
        "learning_objectives": [
            "Capture development patterns",
            "Document integration insights",
            "Record quality strategies",
            "Preserve performance optimizations"
        ],
        "captured_patterns": [],
        "integration_learnings": [],
        "quality_insights": [],
        "performance_notes": []
    }

    session_file = Path('.ace/learnings/daily-insights') / f"{datetime.date.today()}_session.json"
    session_file.parent.mkdir(parents=True, exist_ok=True)

    with open(session_file, 'w') as f:
        json.dump(session_data, f, indent=2)

    print(f"🧠 ACE session initialized: {session_file}")
    return session_file

if __name__ == "__main__":
    init_ace_session()
EOF

chmod +x .ace/init-session.py

# Create development environment file
cat > .env.development << 'EOF'
# TTA.dev Product Building Environment
TTA_DEV_MODE=true
ACE_ENABLED=true
LOG_LEVEL=DEBUG

# Database URLs (for local development)
DATABASE_URL=postgresql://tta_dev:tta_dev@localhost:5432/tta_dev
REDIS_URL=redis://localhost:6379/0

# Observability
PROMETHEUS_URL=http://localhost:9090
GRAFANA_URL=http://localhost:3000

# TTA Rebuild specific
TTA_NARRATIVE_ENGINE_DEBUG=true
TTA_THERAPEUTIC_MODE=development
EOF

# Setup development compose file
cat > docker-compose.dev.yml << 'EOF'
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: tta_dev
      POSTGRES_USER: tta_dev
      POSTGRES_PASSWORD: tta_dev
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana

volumes:
  postgres_data:
  redis_data:
  prometheus_data:
  grafana_data:
EOF

# Create monitoring directory and basic config
mkdir -p monitoring
cat > monitoring/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'tta-dev'
    static_configs:
      - targets: ['host.docker.internal:8000']

  - job_name: 'tta-rebuild'
    static_configs:
      - targets: ['host.docker.internal:8001']
EOF

# Start observability stack (if Docker is available)
if command -v docker-compose &> /dev/null; then
    echo "🚀 Starting observability stack..."
    docker-compose -f docker-compose.dev.yml up -d postgres redis prometheus grafana
else
    echo "⚠️ Docker not available - observability stack not started"
fi

# Run initial tests to verify setup
echo "🧪 Running verification tests..."
uv run python -c "import sys; print(f'✅ Python {sys.version}')"
uv run python -c "import tta_dev_primitives; print('✅ TTA.dev primitives importable')"

# Initialize first ACE session
echo "🧠 Initializing first ACE session..."
python .ace/init-session.py

# Create helpful aliases
cat >> ~/.bashrc << 'EOF'

# TTA.dev Development Aliases
alias tta-test='uv run pytest -v'
alias tta-lint='uv run ruff check . --fix'
alias tta-format='uv run ruff format .'
alias tta-typecheck='uvx pyright packages/'
alias tta-dev='uv run python -m tta_rebuild.main'
alias ace-session='python .ace/init-session.py'
alias ace-capture='python .ace/capture-session.py'

# Quick navigation
alias tt='cd packages/tta-rebuild'
alias tp='cd packages/tta-dev-primitives'
alias docs='cd docs'
alias ace='cd .ace'
EOF

echo ""
echo "✅ TTA.dev Product Building Environment Setup Complete!"
echo ""
echo "🚀 Environment Ready:"
echo "  📊 Observability: http://localhost:9090 (Prometheus), http://localhost:3000 (Grafana)"
echo "  🗄️  Database: postgresql://tta_dev:tta_dev@localhost:5432/tta_dev"
echo "  🔗 Redis: redis://localhost:6379/0"
echo "  🔍 TTA Development: packages/tta-rebuild/"
echo "  🧠 ACE System: .ace/"
echo ""
echo "📝 Quick Commands:"
echo "  tta-test     - Run all tests"
echo "  tta-dev      - Start TTA development server"
echo "  ace-session  - Initialize new ACE learning session"
echo "  tt           - Navigate to TTA rebuild"
echo ""
echo "🎯 Next Steps:"
echo "  1. Run 'tta-test' to verify everything works"
echo "  2. Run 'ace-session' to start capturing development lessons"
echo "  3. Begin TTA development in packages/tta-rebuild/"
echo ""
