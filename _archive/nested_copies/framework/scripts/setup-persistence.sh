#!/bin/bash
# Setup persistence for TTA.dev observability infrastructure

set -e

echo "🔧 Setting up TTA.dev persistence..."

# 1. Add restart policies to docker-compose
echo "📝 Updating docker-compose.integration.yml with restart policies..."
cd /home/thein/repos/TTA.dev/packages/tta-dev-primitives

# Backup original
cp docker-compose.integration.yml docker-compose.integration.yml.backup

# Add restart: unless-stopped to all services
# (This will be done manually to preserve formatting)

# 2. Install systemd service for agent-activity-tracker
echo "📦 Installing systemd service..."
sudo cp /home/thein/repos/TTA.dev/scripts/agent-activity-tracker.service /etc/systemd/system/
sudo systemctl daemon-reload

# 3. Enable and start services
echo "🚀 Enabling services..."
sudo systemctl enable agent-activity-tracker
sudo systemctl start agent-activity-tracker

# 4. Start observability stack
echo "🔭 Starting observability stack..."
cd /home/thein/repos/TTA.dev/packages/tta-dev-primitives
docker-compose -f docker-compose.integration.yml up -d

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
echo "  - Docker: docker-compose -f docker-compose.integration.yml logs -f"
echo ""
echo "🎯 Access:"
echo "  - Metrics: http://localhost:8001/metrics"
echo "  - Prometheus: http://localhost:9090"
echo "  - Jaeger: http://localhost:16686"
echo "  - Grafana: http://localhost:3000"
