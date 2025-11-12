#!/bin/bash
# Import TTA.dev Observability Dashboard to Grafana

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DASHBOARD_FILE="$SCRIPT_DIR/../configs/grafana/dashboards/tta_agent_observability.json"
GRAFANA_URL="${GRAFANA_URL:-http://localhost:3000}"
GRAFANA_USER="${GRAFANA_USER:-admin}"
GRAFANA_PASS="${GRAFANA_PASS:-admin}"

echo "🔧 TTA.dev Grafana Dashboard Importer"
echo "======================================"
echo ""

# Check if observability stack is running
echo "📊 Checking observability stack status..."
if ! curl -s http://localhost:9090/-/healthy > /dev/null 2>&1; then
    echo "❌ Prometheus is not running on http://localhost:9090"
    echo "   Run: ./scripts/setup-observability.sh"
    exit 1
fi

if ! curl -s http://localhost:3000/api/health > /dev/null 2>&1; then
    echo "❌ Grafana is not running on http://localhost:3000"
    echo "   Run: ./scripts/setup-observability.sh"
    exit 1
fi

echo "✅ Prometheus running on http://localhost:9090"
echo "✅ Grafana running on http://localhost:3000"
echo ""

# Check if dashboard file exists
if [ ! -f "$DASHBOARD_FILE" ]; then
    echo "❌ Dashboard file not found: $DASHBOARD_FILE"
    exit 1
fi

echo "📁 Found dashboard: $DASHBOARD_FILE"
echo ""

# Import dashboard via API
echo "📤 Importing dashboard to Grafana..."

# Wrap dashboard JSON in required API format
IMPORT_PAYLOAD=$(jq -n \
    --slurpfile dashboard "$DASHBOARD_FILE" \
    '{
        dashboard: $dashboard[0],
        overwrite: true,
        inputs: [],
        folderId: 0
    }')

RESPONSE=$(curl -s -X POST \
    -H "Content-Type: application/json" \
    -u "$GRAFANA_USER:$GRAFANA_PASS" \
    -d "$IMPORT_PAYLOAD" \
    "$GRAFANA_URL/api/dashboards/db")

# Check response
if echo "$RESPONSE" | jq -e '.status == "success"' > /dev/null 2>&1; then
    DASHBOARD_URL=$(echo "$RESPONSE" | jq -r '.url')
    DASHBOARD_UID=$(echo "$RESPONSE" | jq -r '.uid')

    echo "✅ Dashboard imported successfully!"
    echo ""
    echo "📊 Dashboard Details:"
    echo "   - UID: $DASHBOARD_UID"
    echo "   - URL: $GRAFANA_URL$DASHBOARD_URL"
    echo ""
    echo "🎯 Next Steps:"
    echo "   1. Open: $GRAFANA_URL$DASHBOARD_URL"
    echo "   2. Generate test data:"
    echo "      PYTHONPATH=\$PWD/packages uv run python packages/tta-dev-primitives/examples/test_semantic_tracing.py"
    echo "      PYTHONPATH=\$PWD/packages uv run python packages/tta-dev-primitives/examples/test_core_metrics.py"
    echo "   3. Refresh dashboard to see metrics populate"
    echo ""
    echo "📚 Documentation: docs/observability/PHASE3_DASHBOARDS_COMPLETE.md"
else
    echo "❌ Failed to import dashboard"
    echo ""
    echo "Response:"
    echo "$RESPONSE" | jq '.'
    echo ""
    echo "💡 Troubleshooting:"
    echo "   1. Check Grafana credentials (default: admin/admin)"
    echo "   2. Verify Grafana API is accessible"
    echo "   3. Check dashboard JSON syntax"
    exit 1
fi
