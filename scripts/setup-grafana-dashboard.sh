#!/bin/bash

# Script to import TTA.dev dashboard into Grafana
# This script creates comprehensive visualizations for TTA.dev primitives

set -e

GRAFANA_URL="http://localhost:3000"
GRAFANA_USER="admin"
GRAFANA_PASS="admin"
DASHBOARD_FILE="grafana/dashboards/tta-primitives-dashboard.json"

echo "🎨 Setting up TTA.dev Grafana Dashboard..."

# Check if Grafana is accessible
if ! curl -s "$GRAFANA_URL/api/health" > /dev/null; then
    echo "❌ Grafana is not accessible at $GRAFANA_URL"
    echo "Make sure the observability stack is running:"
    echo "docker ps | grep tta-grafana"
    exit 1
fi

echo "✅ Grafana is accessible"

# Check if Prometheus data source exists, if not create it
echo "🔧 Setting up Prometheus data source..."
curl -s -X POST \
  -H "Content-Type: application/json" \
  -u "$GRAFANA_USER:$GRAFANA_PASS" \
  "$GRAFANA_URL/api/datasources" \
  -d '{
    "name": "Prometheus",
    "type": "prometheus",
    "url": "http://tta-prometheus:9090",
    "access": "proxy",
    "isDefault": true
  }' || echo "Data source may already exist"

echo "✅ Prometheus data source configured"

# Import the dashboard
echo "📊 Importing TTA.dev Primitives Dashboard..."
if [ -f "$DASHBOARD_FILE" ]; then
    curl -s -X POST \
      -H "Content-Type: application/json" \
      -u "$GRAFANA_USER:$GRAFANA_PASS" \
      "$GRAFANA_URL/api/dashboards/db" \
      -d @"$DASHBOARD_FILE"

    if [ $? -eq 0 ]; then
        echo "✅ Dashboard imported successfully!"
        echo ""
        echo "🎯 Access your TTA.dev dashboard at:"
        echo "   $GRAFANA_URL/d/tta-primitives/tta-dev-primitives-dashboard"
        echo ""
        echo "👤 Login credentials:"
        echo "   Username: admin"
        echo "   Password: admin"
        echo ""
        echo "📈 The dashboard includes:"
        echo "   • Workflow execution rate"
        echo "   • Cache hit rate gauge"
        echo "   • Primitive execution duration (p95, p50)"
        echo "   • Request rate by primitive type"
        echo "   • Cache operations timeline"
        echo "   • Request distribution pie chart"
        echo "   • Workflow duration heatmap"
        echo "   • Key metrics summary table"
    else
        echo "❌ Failed to import dashboard"
        exit 1
    fi
else
    echo "❌ Dashboard file not found: $DASHBOARD_FILE"
    exit 1
fi

echo ""
echo "🚀 Dashboard setup complete! Your TTA.dev observability is fully visible."
