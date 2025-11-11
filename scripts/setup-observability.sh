#!/bin/bash

# TTA.dev Observability Setup Script
# Ensures observability infrastructure is running whenever working with TTA.dev

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
DOCKER_COMPOSE_FILE="$ROOT_DIR/packages/tta-dev-primitives/docker-compose.integration.yml"

echo "🔍 TTA.dev Observability Setup"
echo "================================"

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker to use observability features."
    echo "   You can still use TTA.dev without observability."
    exit 0
fi

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo "❌ Docker is not running. Please start Docker to use observability features."
    echo "   You can still use TTA.dev without observability."
    exit 0
fi

# Check if Docker Compose file exists
if [ ! -f "$DOCKER_COMPOSE_FILE" ]; then
    echo "❌ Docker Compose file not found at: $DOCKER_COMPOSE_FILE"
    exit 1
fi

echo "✅ Docker is available and running"

# Check if services are already running
RUNNING_SERVICES=$(docker compose -f "$DOCKER_COMPOSE_FILE" ps -q 2>/dev/null | wc -l)

if [ "$RUNNING_SERVICES" -gt 0 ]; then
    echo "✅ Observability services are already running"
    echo ""
    echo "📊 Access your observability stack:"
    echo "   Prometheus:  http://localhost:9090"
    echo "   Jaeger:      http://localhost:16686"
    echo "   Grafana:     http://localhost:3000 (admin/admin)"
    echo ""
else
    echo "🚀 Starting observability services..."

    # Start services in detached mode
    if docker compose -f "$DOCKER_COMPOSE_FILE" up -d; then
        echo "✅ Observability services started successfully!"
        echo ""
        echo "⏳ Waiting for services to be ready..."
        sleep 10

        # Verify services are responding
        echo ""
        echo "🔍 Checking service health..."

        # Check Prometheus
        if curl -s -o /dev/null -w "%{http_code}" http://localhost:9090 | grep -q "200\|302"; then
            echo "✅ Prometheus: http://localhost:9090"
        else
            echo "⚠️  Prometheus: Starting up... (may take a moment)"
        fi

        # Check Jaeger
        if curl -s -o /dev/null -w "%{http_code}" http://localhost:16686 | grep -q "200"; then
            echo "✅ Jaeger: http://localhost:16686"
        else
            echo "⚠️  Jaeger: Starting up... (may take a moment)"
        fi

        # Check Grafana
        if curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 | grep -q "200\|302"; then
            echo "✅ Grafana: http://localhost:3000 (admin/admin)"
        else
            echo "⚠️  Grafana: Starting up... (may take a moment)"
        fi

        echo ""
        echo "🎯 Try the observability demo:"
        echo "   uv run python packages/tta-dev-primitives/examples/observability_demo.py"
        echo ""

    else
        echo "❌ Failed to start observability services"
        echo "   You can still use TTA.dev without observability."
        exit 1
    fi
fi

echo "✨ Observability setup complete!"
