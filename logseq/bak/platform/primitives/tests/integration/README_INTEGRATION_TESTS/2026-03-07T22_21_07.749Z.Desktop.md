# OpenTelemetry Integration Tests

This directory contains integration tests for verifying that TTA.dev primitives work correctly with real OpenTelemetry backends (Jaeger, Prometheus).

## Prerequisites

- **Docker** and **Docker Compose** installed
- **Python 3.11+** with `uv` package manager
- **Network access** to pull Docker images

## Quick Start

### 1. Start OpenTelemetry Backends

```bash
# From packages/tta-dev-primitives directory
docker-compose -f docker-compose.integration.yml up -d

# Wait for services to be ready (~10 seconds)
sleep 10

# Verify services are running
docker-compose -f docker-compose.integration.yml ps
```

### 2. Run Integration Tests

```bash
# Run all integration tests
uv run pytest tests/integration/test_otel_backend_integration.py -v

# Run specific test
uv run pytest tests/integration/test_otel_backend_integration.py::test_sequential_primitive_creates_spans -v

# Run with detailed output
uv run pytest tests/integration/test_otel_backend_integration.py -v -s
```

### 3. View Observability Data

**Jaeger UI** (Distributed Tracing):
- URL: http://localhost:16686
- Service: `tta-primitives-integration-test`
- View traces, spans, and timing information

**Prometheus** (Metrics):
- URL: http://localhost:9090
- Query metrics: `tta_primitives_*`
- View percentiles, throughput, SLO

**Grafana** (Visualization):
- URL: http://localhost:3000
- Username: `admin`
- Password: `admin`
- Pre-configured datasources for Jaeger and Prometheus

### 4. Stop Services

```bash
# Stop and remove containers
docker-compose -f docker-compose.integration.yml down

# Stop and remove containers + volumes
docker-compose -f docker-compose.integration.yml down -v
```

## Architecture

### Services

| Service | Port | Purpose |
|---------|------|---------|
| **Jaeger** | 16686 | Distributed tracing UI |
| **Jaeger Collector** | 14268 | Trace ingestion (HTTP) |
| **Jaeger Collector** | 14250 | Trace ingestion (gRPC) |
| **Prometheus** | 9090 | Metrics collection and query |
| **Grafana** | 3000 | Visualization dashboard |
| **OTEL Collector** | 4317 | OTLP gRPC receiver |
| **OTEL Collector** | 4318 | OTLP HTTP receiver |

### Data Flow

```
Test Application
    ↓ (OTLP/HTTP)
OpenTelemetry Collector
    ├─→ Jaeger (traces)
    └─→ Prometheus (metrics)
```

## Test Coverage

### Primitives Tested

1. ✅ **SequentialPrimitive** - Step-level spans
2. ✅ **ParallelPrimitive** - Concurrent branch spans
3. ✅ **ConditionalPrimitive** - Branch decision spans
4. ✅ **SwitchPrimitive** - Case routing spans
5. ✅ **RetryPrimitive** - Retry attempt spans
6. ✅ **FallbackPrimitive** - Primary/fallback spans
7. ✅ **SagaPrimitive** - Forward/compensation spans

### Test Scenarios

- **Span Creation**: Verify spans are created in Jaeger
- **Span Hierarchy**: Verify parent-child relationships
- **Span Attributes**: Verify metadata is correctly set
- **Trace Propagation**: Verify context propagates across primitives
- **Composed Workflows**: Verify complex workflows create correct traces
- **Error Tracking**: Verify errors are recorded in spans
- **Metrics Export**: Verify metrics are exported to Prometheus

## Configuration

### Environment Variables

```bash
# Jaeger endpoints
export JAEGER_ENDPOINT="http://localhost:14268"
export JAEGER_QUERY_ENDPOINT="http://localhost:16686"

# Prometheus endpoint
export PROMETHEUS_ENDPOINT="http://localhost:9090"

# OTLP endpoint
export OTEL_EXPORTER_OTLP_ENDPOINT="http://localhost:4318"
```

### Custom Configuration

Edit configuration files in `tests/integration/config/`:

- `prometheus.yml` - Prometheus scrape configuration
- `grafana-datasources.yml` - Grafana datasource configuration
- `otel-collector-config.yml` - OpenTelemetry Collector configuration

## Troubleshooting

### Services Not Starting

```bash
# Check Docker logs
docker-compose -f docker-compose.integration.yml logs

# Check specific service
docker-compose -f docker-compose.integration.yml logs jaeger
docker-compose -f docker-compose.integration.yml logs prometheus
```

### Tests Skipped

If tests are skipped with "OpenTelemetry backends not available":

1. Verify services are running: `docker-compose ps`
2. Check service health:
   ```bash
   curl http://localhost:16686/api/services
   curl http://localhost:9090/-/healthy
   ```
3. Wait longer for services to start (may take 10-30 seconds)

### No Traces in Jaeger

1. Verify OTLP exporter is configured correctly
2. Check OpenTelemetry Collector logs:
   ```bash
   docker-compose -f docker-compose.integration.yml logs otel-collector
   ```
3. Verify test execution completed successfully
4. Wait a few seconds for spans to be exported (batch processing)

### No Metrics in Prometheus

1. Verify Prometheus is scraping targets:
   - Go to http://localhost:9090/targets
   - Check target status
2. Verify metrics are being exported:
   ```bash
   curl http://localhost:9464/metrics
   ```
3. Check Prometheus configuration in `tests/integration/config/prometheus.yml`

## Performance Benchmarking

### Running Performance Tests

```bash
# Run performance overhead tests
uv run pytest tests/integration/test_otel_backend_integration.py -k "performance" -v

# Run with profiling
uv run pytest tests/integration/test_otel_backend_integration.py --profile -v
```

### Expected Overhead

- **Latency**: <5% increase with instrumentation
- **Memory**: <10MB additional per workflow
- **CPU**: <2% additional during execution

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Integration Tests

on: [push, pull_request]

jobs:
  integration-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Start OpenTelemetry backends
        run: |
          cd packages/tta-dev-primitives
          docker-compose -f docker-compose.integration.yml up -d
          sleep 15

      - name: Run integration tests
        run: |
          cd packages/tta-dev-primitives
          uv run pytest tests/integration/test_otel_backend_integration.py -v

      - name: Stop backends
        if: always()
        run: |
          cd packages/tta-dev-primitives
          docker-compose -f docker-compose.integration.yml down -v
```

## References

- [OpenTelemetry Python Documentation](https://opentelemetry.io/docs/instrumentation/python/)
- [Jaeger Documentation](https://www.jaegertracing.io/docs/)
- [Prometheus Documentation](https://prometheus.io/docs/)
- [OpenTelemetry Collector Documentation](https://opentelemetry.io/docs/collector/)

## Support

For issues or questions:
1. Check existing GitHub issues
2. Review test logs and Docker logs
3. Open a new issue with:
   - Test output
   - Docker logs
   - Environment details
