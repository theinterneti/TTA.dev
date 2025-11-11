#!/bin/bash

# TTA.dev Observability Status Check
# Shows current status of observability infrastructure

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
DOCKER_COMPOSE_FILE="$ROOT_DIR/packages/tta-dev-primitives/docker-compose.integration.yml"

echo "🔍 TTA.dev Observability Status"
echo "================================"

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not available"
    echo "   Install Docker to use observability features"
    exit 0
fi

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo "❌ Docker is not running"
    echo "   Start Docker to use observability features"
    exit 0
fi

echo "✅ Docker is available and running"

# Check if services are running
RUNNING_SERVICES=$(docker compose -f "$DOCKER_COMPOSE_FILE" ps -q 2>/dev/null | wc -l)

if [ "$RUNNING_SERVICES" -eq 0 ]; then
    echo "❌ Observability services are not running"
    echo ""
    echo "🚀 To start observability services:"
    echo "   ./scripts/setup-observability.sh"
    echo ""
    exit 0
fi

echo "✅ Observability services are running ($RUNNING_SERVICES containers)"
echo ""

# Check individual services
echo "🔍 Service Health Check:"

# Check Prometheus
PROMETHEUS_STATUS="❌"
if curl -s -o /dev/null -w "%{http_code}" http://localhost:9090 | grep -q "200\|302"; then
    PROMETHEUS_STATUS="✅"
fi
echo "   Prometheus ($PROMETHEUS_STATUS): http://localhost:9090"

# Check Jaeger
JAEGER_STATUS="❌"
if curl -s -o /dev/null -w "%{http_code}" http://localhost:16686 | grep -q "200"; then
    JAEGER_STATUS="✅"
fi
echo "   Jaeger ($JAEGER_STATUS): http://localhost:16686"

# Check Grafana
GRAFANA_STATUS="❌"
if curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 | grep -q "200\|302"; then
    GRAFANA_STATUS="✅"
fi
echo "   Grafana ($GRAFANA_STATUS): http://localhost:3000 (admin/admin)"

# Check OpenTelemetry Collector
OTEL_STATUS="❌"
if curl -s -o /dev/null -w "%{http_code}" http://localhost:13133/health | grep -q "200"; then
    OTEL_STATUS="✅"
fi
echo "   OTEL Collector ($OTEL_STATUS): http://localhost:4317 (gRPC), http://localhost:4318 (HTTP)"

# Check Pushgateway
PUSHGATEWAY_STATUS="❌"
if curl -s -o /dev/null -w "%{http_code}" http://localhost:9091 | grep -q "200"; then
    PUSHGATEWAY_STATUS="✅"
fi
echo "   Pushgateway ($PUSHGATEWAY_STATUS): http://localhost:9091"

echo ""

# Show running containers
echo "📦 Running Containers:"
docker compose -f "$DOCKER_COMPOSE_FILE" ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "🎯 Next Steps:"
echo "   • Run demo: uv run python packages/tta-dev-primitives/examples/observability_demo.py"
echo "   • View traces: http://localhost:16686"
echo "   • Check metrics: http://localhost:9090"
echo "   • See dashboards: http://localhost:3000"
echo ""
