#!/bin/bash

# TTA.dev Professional Observability Setup
# Sets up production-grade monitoring, alerting, and visualization

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
COMPOSE_FILE="docker-compose.professional.yml"
PROJECT_NAME="tta-observability"

# Banner
echo -e "${BLUE}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                TTA.dev Professional Observability           ║"
echo "║              Production-Grade Monitoring Stack              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Function to print status
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."

    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi

    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi

    # Check if compose file exists
    if [[ ! -f "$COMPOSE_FILE" ]]; then
        print_error "Docker Compose file '$COMPOSE_FILE' not found."
        exit 1
    fi

    print_status "Prerequisites check passed ✓"
}

# Create necessary directories
create_directories() {
    print_status "Creating configuration directories..."

    mkdir -p config/prometheus/rules
    mkdir -p config/alertmanager
    mkdir -p config/grafana/{datasources,dashboards}
    mkdir -p config/otel-collector
    mkdir -p logs

    print_status "Directories created ✓"
}

# Validate configuration files
validate_configs() {
    print_status "Validating configuration files..."

    # Check Prometheus config
    if [[ ! -f "config/prometheus/prometheus.yml" ]]; then
        print_error "Prometheus configuration file missing: config/prometheus/prometheus.yml"
        exit 1
    fi

    # Check recording rules
    if [[ ! -f "config/prometheus/rules/recording_rules.yml" ]]; then
        print_error "Recording rules missing: config/prometheus/rules/recording_rules.yml"
        exit 1
    fi

    # Check alerting rules
    if [[ ! -f "config/prometheus/rules/alerting_rules.yml" ]]; then
        print_error "Alerting rules missing: config/prometheus/rules/alerting_rules.yml"
        exit 1
    fi

    # Check AlertManager config
    if [[ ! -f "config/alertmanager/alertmanager.yml" ]]; then
        print_error "AlertManager configuration missing: config/alertmanager/alertmanager.yml"
        exit 1
    fi

    # Check Grafana configs
    if [[ ! -f "config/grafana/datasources/datasources.yml" ]]; then
        print_error "Grafana datasources config missing: config/grafana/datasources/datasources.yml"
        exit 1
    fi

    print_status "Configuration validation passed ✓"
}

# Setup monitoring stack
setup_stack() {
    print_status "Setting up professional observability stack..."

    # Stop any existing containers
    print_status "Stopping existing containers..."
    docker-compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" down --remove-orphans || true

    # Pull latest images
    print_status "Pulling latest container images..."
    docker-compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" pull

    # Start the stack
    print_status "Starting observability stack..."
    docker-compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" up -d

    print_status "Stack deployment initiated ✓"
}

# Wait for services to be healthy
wait_for_services() {
    print_status "Waiting for services to become healthy..."

    local services=("prometheus" "alertmanager" "grafana" "jaeger" "otel-collector" "pushgateway")
    local max_attempts=30
    local attempt=1

    for service in "${services[@]}"; do
        print_status "Checking $service..."

        while [[ $attempt -le $max_attempts ]]; do
            if docker-compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" ps --services --filter "status=running" | grep -q "$service"; then
                if docker inspect "tta-$service" --format='{{ .State.Health.Status }}' 2>/dev/null | grep -q "healthy\|starting" || \
                   [[ "$(docker inspect "tta-$service" --format='{{ .State.Status }}' 2>/dev/null)" == "running" ]]; then
                    print_status "$service is healthy ✓"
                    break
                fi
            fi

            if [[ $attempt -eq $max_attempts ]]; then
                print_warning "$service is not healthy after $max_attempts attempts"
                docker-compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" logs "$service" | tail -10
            fi

            echo -n "."
            sleep 2
            ((attempt++))
        done
        attempt=1
    done
}

# Verify endpoints
verify_endpoints() {
    print_status "Verifying service endpoints..."

    local endpoints=(
        "http://localhost:9090/-/healthy|Prometheus Health Check"
        "http://localhost:9093/-/healthy|AlertManager Health Check"
        "http://localhost:3000/api/health|Grafana Health Check"
        "http://localhost:16686/api/services|Jaeger Services API"
        "http://localhost:13133/|OpenTelemetry Collector Health"
        "http://localhost:9091/-/healthy|Pushgateway Health Check"
    )

    for endpoint_info in "${endpoints[@]}"; do
        IFS='|' read -r endpoint description <<< "$endpoint_info"

        print_status "Checking $description..."

        if curl -s -f "$endpoint" >/dev/null 2>&1; then
            print_status "$description ✓"
        else
            print_warning "$description is not responding (this may be normal during startup)"
        fi
    done
}

# Print access information
print_access_info() {
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                   🎉 Setup Complete! 🎉                     ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"

    echo -e "${GREEN}Professional Observability Stack is now running!${NC}"
    echo ""
    echo -e "${BLUE}📊 Service Access URLs:${NC}"
    echo "  • Prometheus:     http://localhost:9090"
    echo "  • AlertManager:   http://localhost:9093"
    echo "  • Grafana:        http://localhost:3000 (admin/admin)"
    echo "  • Jaeger UI:      http://localhost:16686"
    echo "  • Pushgateway:    http://localhost:9091"
    echo ""
    echo -e "${BLUE}📈 Professional Dashboards:${NC}"
    echo "  • Executive Dashboard:    http://localhost:3000/d/tta-executive"
    echo "  • Platform Health:        http://localhost:3000/d/tta-platform-health"
    echo "  • Developer Dashboard:    http://localhost:3000/d/tta-developer"
    echo ""
    echo -e "${BLUE}🚨 Alerting:${NC}"
    echo "  • Active Alerts:          http://localhost:9093/#/alerts"
    echo "  • Alert Configuration:    config/alertmanager/alertmanager.yml"
    echo "  • Recording Rules:        config/prometheus/rules/recording_rules.yml"
    echo "  • Alerting Rules:         config/prometheus/rules/alerting_rules.yml"
    echo ""
    echo -e "${BLUE}🔧 Management Commands:${NC}"
    echo "  • View logs:              docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME logs -f [service]"
    echo "  • Stop stack:             docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME down"
    echo "  • Restart service:        docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME restart [service]"
    echo "  • View status:            docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME ps"
    echo ""
    echo -e "${YELLOW}📝 Next Steps:${NC}"
    echo "  1. Configure email settings in config/alertmanager/alertmanager.yml"
    echo "  2. Set up Slack webhooks for critical alerts"
    echo "  3. Customize dashboards for your specific metrics"
    echo "  4. Review and adjust alert thresholds"
    echo "  5. Run: uv run python examples/observability_demo.py to generate test data"
    echo ""
    echo -e "${GREEN}Happy Monitoring! 🚀${NC}"
}

# Main execution
main() {
    check_prerequisites
    create_directories
    validate_configs
    setup_stack

    # Wait a moment for containers to initialize
    sleep 5

    wait_for_services
    verify_endpoints
    print_access_info
}

# Error handling
trap 'print_error "Setup failed! Check the logs above for details."' ERR

# Run main function
main "$@"
