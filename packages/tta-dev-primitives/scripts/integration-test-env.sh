#!/usr/bin/env bash
#
# Integration Test Environment Manager
#
# Manages Docker Compose environment for OpenTelemetry integration tests.
#
# Usage:
#   ./scripts/integration-test-env.sh start    # Start services
#   ./scripts/integration-test-env.sh stop     # Stop services
#   ./scripts/integration-test-env.sh restart  # Restart services
#   ./scripts/integration-test-env.sh status   # Check service status
#   ./scripts/integration-test-env.sh logs     # View logs
#   ./scripts/integration-test-env.sh test     # Run integration tests
#   ./scripts/integration-test-env.sh clean    # Stop and remove volumes

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
COMPOSE_FILE="$PROJECT_DIR/docker-compose.integration.yml"

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
}

start_services() {
    log_info "Starting OpenTelemetry integration test environment..."
    
    cd "$PROJECT_DIR"
    docker-compose -f "$COMPOSE_FILE" up -d
    
    log_info "Waiting for services to be ready..."
    sleep 10
    
    # Check service health
    check_service_health
    
    log_success "Services started successfully!"
    log_info "Access points:"
    echo "  - Jaeger UI:    http://localhost:16686"
    echo "  - Prometheus:   http://localhost:9090"
    echo "  - Grafana:      http://localhost:3000 (admin/admin)"
    echo "  - OTLP HTTP:    http://localhost:4318"
    echo "  - OTLP gRPC:    http://localhost:4317"
}

stop_services() {
    log_info "Stopping OpenTelemetry integration test environment..."
    
    cd "$PROJECT_DIR"
    docker-compose -f "$COMPOSE_FILE" stop
    
    log_success "Services stopped successfully!"
}

restart_services() {
    log_info "Restarting OpenTelemetry integration test environment..."
    
    stop_services
    sleep 2
    start_services
}

check_status() {
    log_info "Checking service status..."
    
    cd "$PROJECT_DIR"
    docker-compose -f "$COMPOSE_FILE" ps
}

view_logs() {
    log_info "Viewing service logs (Ctrl+C to exit)..."
    
    cd "$PROJECT_DIR"
    docker-compose -f "$COMPOSE_FILE" logs -f
}

check_service_health() {
    local max_attempts=30
    local attempt=0
    
    log_info "Checking Jaeger health..."
    while [ $attempt -lt $max_attempts ]; do
        if curl -s http://localhost:16686/api/services > /dev/null 2>&1; then
            log_success "Jaeger is healthy"
            break
        fi
        attempt=$((attempt + 1))
        sleep 1
    done
    
    if [ $attempt -eq $max_attempts ]; then
        log_warning "Jaeger health check timed out"
    fi
    
    attempt=0
    log_info "Checking Prometheus health..."
    while [ $attempt -lt $max_attempts ]; do
        if curl -s http://localhost:9090/-/healthy > /dev/null 2>&1; then
            log_success "Prometheus is healthy"
            break
        fi
        attempt=$((attempt + 1))
        sleep 1
    done
    
    if [ $attempt -eq $max_attempts ]; then
        log_warning "Prometheus health check timed out"
    fi
}

run_tests() {
    log_info "Running integration tests..."
    
    cd "$PROJECT_DIR"
    
    # Check if services are running
    if ! docker-compose -f "$COMPOSE_FILE" ps | grep -q "Up"; then
        log_warning "Services are not running. Starting them now..."
        start_services
    fi
    
    # Run tests
    log_info "Executing pytest..."
    uv run pytest tests/integration/test_otel_backend_integration.py -v
    
    if [ $? -eq 0 ]; then
        log_success "All integration tests passed!"
    else
        log_error "Some integration tests failed!"
        exit 1
    fi
}

clean_environment() {
    log_info "Cleaning up OpenTelemetry integration test environment..."
    
    cd "$PROJECT_DIR"
    docker-compose -f "$COMPOSE_FILE" down -v
    
    log_success "Environment cleaned successfully!"
}

show_help() {
    cat << EOF
Integration Test Environment Manager

Usage: $0 <command>

Commands:
    start       Start OpenTelemetry services (Jaeger, Prometheus, Grafana, OTEL Collector)
    stop        Stop all services
    restart     Restart all services
    status      Show service status
    logs        View service logs (follow mode)
    test        Run integration tests
    clean       Stop services and remove volumes
    help        Show this help message

Examples:
    $0 start                    # Start all services
    $0 test                     # Run integration tests
    $0 logs                     # View logs
    $0 clean                    # Clean up everything

Service URLs:
    Jaeger UI:      http://localhost:16686
    Prometheus:     http://localhost:9090
    Grafana:        http://localhost:3000 (admin/admin)
    OTLP HTTP:      http://localhost:4318
    OTLP gRPC:      http://localhost:4317

EOF
}

# Main
main() {
    check_docker
    
    case "${1:-help}" in
        start)
            start_services
            ;;
        stop)
            stop_services
            ;;
        restart)
            restart_services
            ;;
        status)
            check_status
            ;;
        logs)
            view_logs
            ;;
        test)
            run_tests
            ;;
        clean)
            clean_environment
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            log_error "Unknown command: $1"
            show_help
            exit 1
            ;;
    esac
}

main "$@"

