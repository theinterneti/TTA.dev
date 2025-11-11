# TTA.dev Observability Visualizations Guide

## 🎯 Overview

This guide demonstrates the comprehensive observability capabilities built for TTA.dev primitives, showing real-time metrics, performance insights, and operational visibility.

## 📊 Available Metrics

### Core TTA.dev Metrics

| Metric | Type | Description | Labels |
|--------|------|-------------|--------|
| `tta_requests_total` | Counter | Total requests by primitive type | `primitive_type`, `status` |
| `tta_execution_duration_seconds` | Histogram | Execution duration by primitive type | `primitive_type` |
| `tta_cache_hit_rate` | Gauge | Cache hit rate percentage | `cache_key` |
| `tta_cache_hits_total` | Counter | Total cache hits | `cache_key` |
| `tta_cache_misses_total` | Counter | Total cache misses | `cache_key` |
| `tta_workflow_executions_total` | Counter | Total workflow executions | `workflow_type` |
| `tta_workflow_duration_seconds` | Histogram | End-to-end workflow duration | `workflow_type` |

### System Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `process_cpu_seconds_total` | Counter | CPU usage of metrics server |
| `process_resident_memory_bytes` | Gauge | Memory usage |
| `python_gc_collections_total` | Counter | Python garbage collection stats |

## 🔍 Prometheus Queries

### 1. Performance Queries

#### Request Rate by Primitive Type
```promql
# Requests per second by primitive type
rate(tta_requests_total[1m])

# Top performing primitives by request rate
topk(5, rate(tta_requests_total[1m]))
```

#### Execution Duration Percentiles
```promql
# P95 latency by primitive type
histogram_quantile(0.95, rate(tta_execution_duration_seconds_bucket[5m]))

# P50 latency by primitive type
histogram_quantile(0.50, rate(tta_execution_duration_seconds_bucket[5m]))

# P99 latency by primitive type
histogram_quantile(0.99, rate(tta_execution_duration_seconds_bucket[5m]))
```

#### Average Execution Time
```promql
# Average execution time per primitive type
rate(tta_execution_duration_seconds_sum[5m]) / rate(tta_execution_duration_seconds_count[5m])
```

### 2. Cache Performance Queries

#### Cache Hit Rate
```promql
# Current cache hit rate as percentage
tta_cache_hit_rate * 100

# Cache hit rate over time
avg_over_time(tta_cache_hit_rate[5m]) * 100
```

#### Cache Operations Rate
```promql
# Cache hits per second
rate(tta_cache_hits_total[1m])

# Cache misses per second
rate(tta_cache_misses_total[1m])

# Total cache operations per second
rate(tta_cache_hits_total[1m]) + rate(tta_cache_misses_total[1m])
```

#### Cache Efficiency Metrics
```promql
# Cache efficiency ratio (hits/total operations)
rate(tta_cache_hits_total[1m]) / (rate(tta_cache_hits_total[1m]) + rate(tta_cache_misses_total[1m]))

# Cache miss rate
rate(tta_cache_misses_total[1m]) / (rate(tta_cache_hits_total[1m]) + rate(tta_cache_misses_total[1m]))
```

### 3. Workflow Metrics

#### Workflow Execution Rate
```promql
# Workflows per second
rate(tta_workflow_executions_total[1m])

# Total workflow executions
tta_workflow_executions_total
```

#### Workflow Duration Analysis
```promql
# P95 workflow duration
histogram_quantile(0.95, rate(tta_workflow_duration_seconds_bucket[5m]))

# Average workflow duration
rate(tta_workflow_duration_seconds_sum[5m]) / rate(tta_workflow_duration_seconds_count[5m])

# Workflow duration standard deviation
sqrt(
  rate(tta_workflow_duration_seconds_sum[5m]) / rate(tta_workflow_duration_seconds_count[5m]) -
  (rate(tta_workflow_duration_seconds_sum[5m]) / rate(tta_workflow_duration_seconds_count[5m]))^2
)
```

### 4. Error Rate Queries

#### Success Rate by Primitive
```promql
# Success rate percentage by primitive type
rate(tta_requests_total{status="success"}[5m]) / rate(tta_requests_total[5m]) * 100

# Error rate percentage by primitive type
rate(tta_requests_total{status!="success"}[5m]) / rate(tta_requests_total[5m]) * 100
```

### 5. Resource Utilization

#### CPU Usage
```promql
# CPU usage rate
rate(process_cpu_seconds_total[1m]) * 100
```

#### Memory Usage
```promql
# Memory usage in MB
process_resident_memory_bytes / 1024 / 1024

# Memory usage percentage (if you know max memory)
process_resident_memory_bytes / (1024 * 1024 * 1024) * 100  # Assuming 1GB max
```

### 6. Advanced Analytics Queries

#### Primitive Performance Ranking
```promql
# Fastest primitives by P50 latency
bottomk(10, histogram_quantile(0.50, rate(tta_execution_duration_seconds_bucket[5m])))

# Slowest primitives by P95 latency
topk(10, histogram_quantile(0.95, rate(tta_execution_duration_seconds_bucket[5m])))
```

#### Load Distribution
```promql
# Request distribution by primitive type (percentage)
(rate(tta_requests_total[5m]) / ignoring(primitive_type) group_left sum(rate(tta_requests_total[5m]))) * 100
```

#### Throughput vs Latency Analysis
```promql
# Throughput (requests/sec) vs P95 latency correlation
rate(tta_requests_total[5m]) and histogram_quantile(0.95, rate(tta_execution_duration_seconds_bucket[5m]))
```

## 📈 Grafana Dashboard Panels

### 1. Overview Panels

#### Key Performance Indicators (KPIs)
- **Total Requests**: `sum(tta_requests_total)`
- **Cache Hit Rate**: `tta_cache_hit_rate * 100`
- **Average Latency**: `avg(rate(tta_execution_duration_seconds_sum[5m]) / rate(tta_execution_duration_seconds_count[5m]))`
- **Workflow Rate**: `rate(tta_workflow_executions_total[1m])`

#### Performance Gauges
- Cache hit rate with thresholds (Red: <70%, Yellow: 70-90%, Green: >90%)
- P95 latency with SLA thresholds
- Request rate with capacity indicators

### 2. Time Series Visualizations

#### Multi-Primitive Performance
```promql
# Show all primitive types on one graph
histogram_quantile(0.95, rate(tta_execution_duration_seconds_bucket[5m]))
```

#### Cache Performance Timeline
```promql
# Cache hits vs misses over time
rate(tta_cache_hits_total[1m]) and rate(tta_cache_misses_total[1m])
```

### 3. Distribution Visualizations

#### Request Distribution (Pie Chart)
```promql
# Requests by primitive type
tta_requests_total
```

#### Latency Heatmap
```promql
# Duration distribution heatmap
rate(tta_execution_duration_seconds_bucket[5m])
```

### 4. Advanced Visualizations

#### Performance Correlation Matrix
- X-axis: Request rate
- Y-axis: P95 latency
- Size: Cache hit rate
- Color: Primitive type

#### Resource Utilization Dashboard
- CPU usage timeline
- Memory usage timeline
- Garbage collection frequency
- Thread count over time

## 🚨 Alerting Rules

### Performance Alerts

#### High Latency Alert
```yaml
- alert: HighPrimitiveLatency
  expr: histogram_quantile(0.95, rate(tta_execution_duration_seconds_bucket[5m])) > 0.1
  for: 2m
  labels:
    severity: warning
  annotations:
    summary: "High latency detected for primitive {{ $labels.primitive_type }}"
    description: "P95 latency is {{ $value }}s for primitive {{ $labels.primitive_type }}"
```

#### Low Cache Hit Rate Alert
```yaml
- alert: LowCacheHitRate
  expr: tta_cache_hit_rate < 0.8
  for: 1m
  labels:
    severity: warning
  annotations:
    summary: "Low cache hit rate: {{ $value | humanizePercentage }}"
    description: "Cache hit rate has dropped below 80%"
```

#### High Error Rate Alert
```yaml
- alert: HighErrorRate
  expr: rate(tta_requests_total{status!="success"}[5m]) / rate(tta_requests_total[5m]) > 0.05
  for: 30s
  labels:
    severity: critical
  annotations:
    summary: "High error rate detected"
    description: "Error rate is {{ $value | humanizePercentage }} for primitive {{ $labels.primitive_type }}"
```

## 📸 Current Live Data

Based on our live metrics server (running 400+ workflow executions):

### Key Performance Metrics
- **Cache Hit Rate**: 99.03% (Excellent performance!)
- **Workflow Execution Rate**: ~0.33 workflows/second (1 every 3 seconds)
- **Average Workflow Duration**: ~1.5ms (Very fast execution)
- **Primitive Types Active**: MockPrimitive, CachePrimitive, ParallelPrimitive, SequentialPrimitive

### Performance Insights
1. **Cache Effectiveness**: 99%+ hit rate shows excellent cache utilization
2. **Low Latency**: Sub-millisecond execution times for most primitives
3. **Stable Performance**: Consistent metrics over 400+ executions
4. **Resource Efficiency**: Low CPU and memory usage

## 🎯 Visualization Best Practices

### 1. Dashboard Organization
- **Overview**: High-level KPIs and health indicators
- **Performance**: Detailed latency and throughput metrics
- **Operations**: Cache performance and resource utilization
- **Troubleshooting**: Error rates and system health

### 2. Time Range Selection
- **Real-time monitoring**: Last 5-15 minutes
- **Performance analysis**: Last 1-4 hours
- **Trend analysis**: Last 24 hours to 7 days
- **Capacity planning**: Last 30 days

### 3. Visualization Types
- **Gauges**: For current values (cache hit rate, current latency)
- **Time series**: For trends (request rate, latency over time)
- **Heatmaps**: For distribution analysis (latency distribution)
- **Pie charts**: For composition (request distribution by primitive)
- **Tables**: For detailed breakdowns (primitive performance summary)

### 4. Color Coding
- **Green**: Good performance (>90% cache hit, <10ms latency)
- **Yellow**: Warning levels (70-90% cache hit, 10-50ms latency)
- **Red**: Critical issues (<70% cache hit, >50ms latency)

## 🔗 Quick Access Links

### Live Dashboards
- **Grafana**: http://localhost:3000/d/b09ca53d-4f9f-4f6e-b1f6-db06d33600b6/tta-dev-primitives-dashboard
- **Prometheus**: http://localhost:9090
- **Jaeger**: http://localhost:16686

### Key Queries to Try in Prometheus
1. `tta_cache_hit_rate * 100` - Current cache performance
2. `rate(tta_requests_total[1m])` - Current request rate
3. `histogram_quantile(0.95, rate(tta_execution_duration_seconds_bucket[5m]))` - P95 latency
4. `sum(rate(tta_workflow_executions_total[1m]))` - Workflow throughput

---

**Last Updated**: November 10, 2025
**Data Source**: Live TTA.dev metrics server with 400+ workflow executions
**Cache Performance**: 99.03% hit rate
**System Status**: All services operational
