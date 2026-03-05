#!/bin/bash
# Verify TTA.dev observability persistence and set up if needed
# This script is idempotent - safe to run multiple times

set -e

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🔍 TTA.dev Observability Persistence Check"
echo ""

# Track what needs setup
NEEDS_SYSTEMD=false
NEEDS_DOCKER_START=false
ALL_GOOD=true

# 1. Check systemd service
echo -n "Checking systemd service... "
if systemctl is-active --quiet agent-activity-tracker 2>/dev/null; then
    echo -e "${GREEN}✅ Running${NC}"
elif systemctl is-enabled --quiet agent-activity-tracker 2>/dev/null; then
    echo -e "${YELLOW}⚠️  Installed but not running${NC}"
    echo "   Run: sudo systemctl start agent-activity-tracker"
    ALL_GOOD=false
elif [ -f "/etc/systemd/system/agent-activity-tracker.service" ]; then
    echo -e "${YELLOW}⚠️  Installed but not enabled${NC}"
    echo "   Run: sudo systemctl enable --now agent-activity-tracker"
    ALL_GOOD=false
else
    echo -e "${RED}❌ Not installed${NC}"
    NEEDS_SYSTEMD=true
    ALL_GOOD=false
fi

# 2. Check Docker containers
echo -n "Checking Docker containers... "
RUNNING_CONTAINERS=$(docker ps --format '{{.Names}}' | grep -E '^tta-' | wc -l)
if [ "$RUNNING_CONTAINERS" -ge 5 ]; then
    echo -e "${GREEN}✅ Running ($RUNNING_CONTAINERS containers)${NC}"
else
    echo -e "${RED}❌ Not running (expected 5, found $RUNNING_CONTAINERS)${NC}"
    NEEDS_DOCKER_START=true
    ALL_GOOD=false
fi

# 3. Check restart policies
echo -n "Checking Docker restart policies... "
if grep -q "restart: unless-stopped" "$REPO_ROOT/docker-compose.yml"; then
    echo -e "${GREEN}✅ Configured${NC}"
else
    echo -e "${RED}❌ Not configured${NC}"
    echo "   Note: docker-compose.yml needs restart policies"
    ALL_GOOD=false
fi

# 4. Check git hook
echo -n "Checking git post-commit hook... "
if [ -x "$REPO_ROOT/.git/hooks/post-commit" ]; then
    echo -e "${GREEN}✅ Installed${NC}"
else
    echo -e "${YELLOW}⚠️  Not found or not executable${NC}"
    ALL_GOOD=false
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Provide guidance based on findings
if [ "$ALL_GOOD" = true ]; then
    echo -e "${GREEN}✅ All systems operational!${NC}"
    echo ""
    echo "📊 Access your observability stack:"
    echo "   • Metrics:     http://localhost:8001/metrics"
    echo "   • Prometheus:  http://localhost:9090"
    echo "   • Jaeger:      http://localhost:16686"
    echo "   • Grafana:     http://localhost:3000 (admin/admin)"
    echo "   • Pushgateway: http://localhost:9091"
    echo ""
    exit 0
fi

echo -e "${YELLOW}⚠️  Setup required${NC}"
echo ""

# Offer to fix issues
if [ "$NEEDS_SYSTEMD" = true ] || [ "$NEEDS_DOCKER_START" = true ]; then
    echo "Options:"
    echo ""

    if [ "$NEEDS_SYSTEMD" = true ]; then
        echo "1. Run full setup (installs systemd service - requires sudo):"
        echo "   ./scripts/setup-persistence.sh"
        echo ""
    fi

    if [ "$NEEDS_DOCKER_START" = true ]; then
        echo "2. Start Docker containers only:"
        echo "   docker compose --profile observability up -d"
        echo ""
    fi

    echo "3. View detailed documentation:"
    echo "   cat scripts/PERSISTENCE_SETUP.md"
    echo ""
fi

# Ask if user wants auto-fix
if [ -t 0 ]; then  # Check if stdin is a terminal (interactive)
    echo -n "Would you like to run setup now? (y/N): "
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        echo ""
        echo "🚀 Running setup..."
        exec ./scripts/setup-persistence.sh
    fi
fi

exit 1
