#!/bin/bash
# Setup persistence for TTA.dev observability infrastructure

set -e

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "🔧 Setting up TTA.dev persistence..."

# 1. Ensure restart policies are set
echo "📝 docker-compose.yml already includes restart: unless-stopped policies..."
cd "$REPO_ROOT"

# 2. Install systemd service for agent-activity-tracker
echo "📦 Installing systemd service..."
sudo cp "$REPO_ROOT/scripts/agent-activity-tracker.service" /etc/systemd/system/
sudo systemctl daemon-reload

# 3. Enable and start services
echo "🚀 Enabling services..."
sudo systemctl enable agent-activity-tracker
sudo systemctl start agent-activity-tracker

# 4. Start observability stack
echo "🔭 Starting observability stack..."
cd "$REPO_ROOT"
docker compose --profile observability up -d

# 5. Verify
echo ""
echo "✅ Persistence setup complete!"
echo ""
echo "📊 Status:"
echo "  - Agent tracker: $(sudo systemctl is-active agent-activity-tracker)"
echo "  - Docker containers: $(docker ps --format '{{.Names}}' | grep -E '(jaeger|prometheus|grafana)' | wc -l) running"
echo ""
echo "🔍 View logs:"
echo "  - Agent tracker: sudo journalctl -u agent-activity-tracker -f"
echo "  - Docker: docker compose --profile observability logs -f"
echo ""
echo "🎯 Access:"
echo "  - Metrics: http://localhost:8001/metrics"
echo "  - Prometheus: http://localhost:9090"
echo "  - Jaeger: http://localhost:16686"
echo "  - Grafana: http://localhost:3000"
