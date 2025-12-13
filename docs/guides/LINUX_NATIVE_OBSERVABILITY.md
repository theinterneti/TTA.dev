# Linux-Native Observability Stack Guide

**Migrating from Docker Desktop to Native Linux Services**

**Last Updated:** 2025-11-15
**Status:** Production-Ready Alternative

---

## Overview

This guide provides a complete migration path from Docker-based observability services to native Linux installations. You already have Grafana Cloud configured (https://theinterneti.grafana.net/), so this focuses on local development/testing infrastructure.

### Why Linux-Native?

- ✅ **Reliability**: No Docker Desktop dependency issues on Windows/WSL
- ✅ **Performance**: Native processes avoid container overhead
- ✅ **Simplicity**: Standard systemd service management
- ✅ **Resource Efficiency**: Lower memory/CPU usage
- ✅ **Hybrid Model**: Local dev + Grafana Cloud for production

---

## Architecture

### Current Docker-Based Setup

```yaml
# docker-compose.integration.yml
services:
  - jaeger (port 16686)
  - prometheus (port 9090)
  - grafana (port 3000)
  - otel-collector (port 4317/4318)
  - pushgateway (port 9091)
```

### New Linux-Native Setup

```
┌─────────────────────────────────────────────┐
│  TTA.dev Application                        │
│  └─ Exports Prometheus metrics (port 9464) │
└─────────────┬───────────────────────────────┘
              │
              ↓
┌─────────────────────────────────────────────┐
│  Grafana Alloy (Native Linux Service)       │
│  ├─ Collects metrics from app              │
│  ├─ Collects logs (journald)               │
│  ├─ Collects traces (OTLP)                 │
│  └─ Ships to Grafana Cloud                 │
└─────────────┬───────────────────────────────┘
              │
              ↓
┌─────────────────────────────────────────────┐
│  Grafana Cloud                              │
│  └─ https://theinterneti.grafana.net/      │
└─────────────────────────────────────────────┘

Optional Local Services (for offline dev):
  - Prometheus (native binary)
  - Local Grafana (native binary)
```

---

## Component Selection

### Recommended Stack

| Component | Solution | Why |
|-----------|----------|-----|
| **Agent** | Grafana Alloy | Single unified agent (replaces Prometheus, OTel Collector, etc.) |
| **Metrics** | Grafana Cloud + Optional local Prometheus | Hybrid approach |
| **Logs** | Grafana Cloud (via Alloy) | Native journald integration |
| **Traces** | Grafana Cloud Tempo | OTLP support built-in |
| **Visualization** | Grafana Cloud + Optional local Grafana | Development flexibility |

### Why Grafana Alloy?

**Grafana Alloy** is the modern unified agent that replaces:
- Prometheus Agent
- Grafana Agent
- OpenTelemetry Collector
- Promtail (Loki agent)

**Benefits:**
- ✅ Single binary for all telemetry (metrics, logs, traces)
- ✅ Native Linux packages (apt/dnf/zypper)
- ✅ Systemd service management
- ✅ Built-in Grafana Cloud integration
- ✅ Low resource usage (~50MB RAM)
- ✅ Configuration-as-code (Alloy syntax)

---

## Installation Guide

### Step 1: Install Grafana Alloy (Ubuntu/Debian)

```bash
# Install GPG for key management
sudo apt install gpg

# Add Grafana APT repository
sudo mkdir -p /etc/apt/keyrings/
wget -q -O - https://apt.grafana.com/gpg.key | gpg --dearmor | sudo tee /etc/apt/keyrings/grafana.gpg > /dev/null
echo "deb [signed-by=/etc/apt/keyrings/grafana.gpg] https://apt.grafana.com stable main" | sudo tee /etc/apt/sources.list.d/grafana.list

# Update and install Alloy
sudo apt-get update
sudo apt-get install alloy

# Verify installation
alloy --version
```

**For RHEL/Fedora:**
```bash
# Add Grafana YUM repository
wget -q -O gpg.key https://rpm.grafana.com/gpg.key
sudo rpm --import gpg.key
echo -e '[grafana]\nname=grafana\nbaseurl=https://rpm.grafana.com\nrepo_gpgcheck=1\nenabled=1\ngpgcheck=1\ngpgkey=https://rpm.grafana.com/gpg.key\nsslverify=1\nsslcacert=/etc/pki/tls/certs/ca-bundle.crt' | sudo tee /etc/yum.repos.d/grafana.repo

# Install Alloy
sudo dnf install alloy
```

### Step 2: Configure Grafana Cloud Credentials

Your service account token is in `/home/thein/.env.tta-dev`. We'll reference it securely.

```bash
# Create environment file for Alloy
sudo nano /etc/default/alloy
```

Add:
```bash
# Grafana Cloud Configuration
GRAFANA_CLOUD_TOKEN="<your-token-from-env-file>"
GRAFANA_CLOUD_STACK="theinterneti"
GRAFANA_CLOUD_REGION="prod-us-east-0"  # Check your actual region
```

### Step 3: Configure Alloy

Create Alloy configuration file:

```bash
sudo nano /etc/alloy/config.alloy
```

**Basic Configuration (Metrics + Logs + Traces):**

```alloy
// Prometheus metrics scraping
prometheus.scrape "tta_app" {
  targets = [{
    __address__ = "localhost:9464",
  }]
  forward_to = [prometheus.remote_write.grafana_cloud.receiver]
  scrape_interval = "15s"
}

// Remote write to Grafana Cloud
prometheus.remote_write "grafana_cloud" {
  endpoint {
    url = "https://prometheus-prod-us-east-0.grafana.net/api/prom/push"
    basic_auth {
      username = env("GRAFANA_CLOUD_STACK")
      password = env("GRAFANA_CLOUD_TOKEN")
    }
  }
}

// Systemd journal logs
loki.source.journal "system_logs" {
  max_age = "24h"
  forward_to = [loki.write.grafana_cloud.receiver]

  // Filter for TTA.dev application logs
  labels = {
    job = "tta-dev",
  }
}

// Loki logs to Grafana Cloud
loki.write "grafana_cloud" {
  endpoint {
    url = "https://logs-prod-us-east-0.grafana.net/loki/api/v1/push"
    basic_auth {
      username = env("GRAFANA_CLOUD_STACK")
      password = env("GRAFANA_CLOUD_TOKEN")
    }
  }
}

// OTLP receiver for traces
otelcol.receiver.otlp "default" {
  grpc {
    endpoint = "0.0.0.0:4317"
  }
  http {
    endpoint = "0.0.0.0:4318"
  }

  output {
    traces = [otelcol.exporter.otlp.grafana_cloud.input]
  }
}

// Traces to Grafana Cloud Tempo
otelcol.exporter.otlp "grafana_cloud" {
  client {
    endpoint = "tempo-prod-us-east-0.grafana.net:443"
    auth = otelcol.auth.basic.grafana_cloud.handler
  }
}

// Basic auth for Tempo
otelcol.auth.basic "grafana_cloud" {
  username = env("GRAFANA_CLOUD_STACK")
  password = env("GRAFANA_CLOUD_TOKEN")
}
```

### Step 4: Enable and Start Alloy Service

```bash
# Enable Alloy to start on boot
sudo systemctl enable alloy

# Start Alloy service
sudo systemctl start alloy

# Check status
sudo systemctl status alloy

# View logs
journalctl -u alloy -f
```

### Step 5: Verify Configuration

```bash
# Check if Alloy is running
sudo systemctl status alloy

# Test configuration syntax
alloy fmt /etc/alloy/config.alloy

# View metrics being collected
curl http://localhost:12345/metrics  # Alloy's own metrics
```

---

## Optional: Local Prometheus (For Offline Development)

If you need local Prometheus for testing when offline:

### Install Prometheus Binary

```bash
# Download latest Prometheus
cd /tmp
wget https://github.com/prometheus/prometheus/releases/download/v2.48.1/prometheus-2.48.1.linux-amd64.tar.gz
tar xvfz prometheus-*.tar.gz
cd prometheus-*

# Install binaries
sudo cp prometheus /usr/local/bin/
sudo cp promtool /usr/local/bin/

# Create user
sudo useradd --no-create-home --shell /bin/false prometheus

# Create directories
sudo mkdir -p /etc/prometheus /var/lib/prometheus
sudo chown -R prometheus:prometheus /etc/prometheus /var/lib/prometheus
```

### Configure Prometheus

```bash
sudo nano /etc/prometheus/prometheus.yml
```

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'tta-dev-app'
    static_configs:
      - targets: ['localhost:9464']
    scrape_interval: 15s
```

### Create Systemd Service

```bash
sudo nano /etc/systemd/system/prometheus.service
```

```ini
[Unit]
Description=Prometheus Monitoring System
Documentation=https://prometheus.io/docs/
Wants=network-online.target
After=network-online.target

[Service]
User=prometheus
Group=prometheus
Type=simple
ExecStart=/usr/local/bin/prometheus \
  --config.file=/etc/prometheus/prometheus.yml \
  --storage.tsdb.path=/var/lib/prometheus/ \
  --web.console.libraries=/usr/share/prometheus/console_libraries \
  --web.console.templates=/usr/share/prometheus/consoles

[Install]
WantedBy=multi-user.target
```

### Start Prometheus

```bash
sudo systemctl daemon-reload
sudo systemctl enable prometheus
sudo systemctl start prometheus
sudo systemctl status prometheus

# Access UI
open http://localhost:9090
```

---

## Optional: Local Grafana (For Offline Visualization)

### Install Grafana

```bash
# Add Grafana repository (already done for Alloy)
sudo apt-get install grafana

# Enable and start
sudo systemctl enable grafana-server
sudo systemctl start grafana-server

# Access UI
open http://localhost:3000
# Default credentials: admin/admin
```

### Configure Data Sources

1. **Grafana Cloud** (primary):
   - Add Prometheus data source pointing to Grafana Cloud
   - Add Loki data source pointing to Grafana Cloud
   - Add Tempo data source pointing to Grafana Cloud

2. **Local Prometheus** (fallback):
   - Add Prometheus data source: `http://localhost:9090`

---

## Integration with TTA.dev

### Update Observability Initialization

Your application code stays the same! The key is that your app exports Prometheus metrics on port 9464, which Alloy will scrape.

**No changes needed in your Python code:**

```python
from observability_integration import initialize_observability

# This still works - exports metrics on port 9464
success = initialize_observability(
    service_name="tta-dev-app",
    enable_prometheus=True,
    prometheus_port=9464,
)
```

### Update OTLP Endpoint (if using traces)

If your app sends traces via OTLP, update to use Alloy:

```python
from observability_integration import initialize_observability

success = initialize_observability(
    service_name="tta-dev-app",
    enable_prometheus=True,
    prometheus_port=9464,
    otlp_endpoint="http://localhost:4317",  # Alloy's OTLP receiver
)
```

---

## Migration Strategy

### Phase 1: Parallel Running (Recommended)

Run both Docker and native services simultaneously:

1. Keep Docker Compose running (existing setup)
2. Install and configure Alloy
3. Point Alloy to Grafana Cloud
4. Verify data flowing to Grafana Cloud
5. Compare Docker metrics vs Alloy metrics
6. Once confident, stop Docker services

### Phase 2: Switch to Native

```bash
# Stop Docker services
docker-compose -f docker-compose.integration.yml down

# Ensure Alloy is running
sudo systemctl status alloy

# Verify metrics in Grafana Cloud
# https://theinterneti.grafana.net/
```

### Phase 3: Cleanup (Optional)

```bash
# Remove Docker images (frees ~2GB)
docker rmi jaegertracing/all-in-one:1.52
docker rmi prom/prometheus:v2.48.1
docker rmi grafana/grafana:10.2.3
docker rmi otel/opentelemetry-collector-contrib:0.91.0
docker rmi prom/pushgateway:v1.6.2

# Remove Docker volumes
docker volume rm tta-dev-primitives_prometheus-data
docker volume rm tta-dev-primitives_grafana-data
```

---

## Troubleshooting

### Alloy Not Starting

```bash
# Check service status
sudo systemctl status alloy

# View detailed logs
journalctl -u alloy -n 50 --no-pager

# Test configuration
sudo alloy fmt /etc/alloy/config.alloy
```

### Metrics Not Appearing in Grafana Cloud

```bash
# Check if app is exporting metrics
curl http://localhost:9464/metrics

# Check Alloy scrape targets
curl http://localhost:12345/metrics | grep scrape

# Verify Grafana Cloud credentials
sudo systemctl status alloy
journalctl -u alloy | grep -i error
```

### Permission Issues

```bash
# Ensure proper ownership
sudo chown -R alloy:alloy /var/lib/alloy
sudo chown -R alloy:alloy /etc/alloy

# Check SELinux (if applicable)
sudo setenforce 0  # Temporarily disable for testing
```

---

## Performance Comparison

### Docker Compose Stack

```
Memory: ~800MB (all containers)
CPU: 2-5% idle
Disk: ~2GB (images)
Startup: ~30 seconds
```

### Native Linux Services

```
Memory: ~100MB (Alloy only)
CPU: <1% idle
Disk: ~50MB (binary)
Startup: ~2 seconds
```

**Savings:** ~700MB RAM, ~1.95GB disk

---

## Security Considerations

### Token Storage

Your Grafana Cloud token is sensitive. Current best practices:

```bash
# Option 1: Environment file (current)
# /etc/default/alloy
GRAFANA_CLOUD_TOKEN="<token>"

# Option 2: Systemd credentials (more secure)
sudo systemd-creds encrypt --name=grafana-token - /etc/credstore/grafana-token.cred
# Update systemd service to use LoadCredential=

# Option 3: Secrets manager
# Use systemd-creds or external secrets manager
```

### Firewall Rules

```bash
# Allow Alloy OTLP receiver (if needed)
sudo ufw allow 4317/tcp comment 'Alloy OTLP gRPC'
sudo ufw allow 4318/tcp comment 'Alloy OTLP HTTP'

# Prometheus app metrics (localhost only)
# No firewall rule needed - localhost only
```

---

## Monitoring the Monitor

Alloy exposes its own metrics:

```bash
# View Alloy's health
curl http://localhost:12345/metrics

# Key metrics to watch:
# - alloy_build_info
# - alloy_component_evaluation_seconds
# - prometheus_remote_storage_samples_total
```

---

## Alternative: Podman (Docker-Compatible)

If you still want container-like workflow without Docker Desktop:

```bash
# Install Podman (Docker alternative)
sudo apt-get install podman

# Use same docker-compose syntax
alias docker=podman
alias docker-compose=podman-compose

# Run your docker-compose.yml
podman-compose -f docker-compose.integration.yml up -d
```

**Benefits:**
- ✅ Rootless containers (more secure)
- ✅ Docker-compatible API
- ✅ No daemon required
- ✅ Native Linux integration
- ✅ systemd service generation

---

## Recommended Setup

### For Your Use Case (Grafana Cloud + Local Dev)

**Production/Cloud:**
- Grafana Alloy (native Linux service)
- Ships all telemetry to Grafana Cloud
- Lightweight, reliable, always running

**Local Development (optional):**
- Local Prometheus (native binary) for offline testing
- Local Grafana (native binary) for dashboard development
- Use Grafana Cloud as primary, local as fallback

**Configuration:**

```alloy
// /etc/alloy/config.alloy

// Ship to Grafana Cloud (primary)
prometheus.scrape "tta_app" {
  targets = [{
    __address__ = "localhost:9464",
  }]
  forward_to = [
    prometheus.remote_write.grafana_cloud.receiver,
    prometheus.remote_write.local.receiver,  // Also send to local
  ]
}

// Grafana Cloud
prometheus.remote_write "grafana_cloud" {
  endpoint {
    url = "https://prometheus-prod-us-east-0.grafana.net/api/prom/push"
    basic_auth {
      username = env("GRAFANA_CLOUD_STACK")
      password = env("GRAFANA_CLOUD_TOKEN")
    }
  }
}

// Local Prometheus (fallback)
prometheus.remote_write "local" {
  endpoint {
    url = "http://localhost:9090/api/v1/write"
  }
}
```

---

## Next Steps

### Immediate Actions

1. ✅ Install Grafana Alloy
2. ✅ Configure with Grafana Cloud credentials
3. ✅ Start Alloy service
4. ✅ Verify metrics flowing to Grafana Cloud
5. ✅ Update TTA.dev documentation

### Documentation Updates

Create these additional guides:

1. `docs/guides/GRAFANA_CLOUD_SETUP.md` - Grafana Cloud configuration
2. `docs/guides/ALLOY_CONFIGURATION.md` - Advanced Alloy config
3. Update `AGENTS.md` - Remove Docker Desktop dependency notes

### Testing Checklist

- [ ] Metrics visible in Grafana Cloud
- [ ] Logs flowing from journald
- [ ] Traces being captured (if using OTLP)
- [ ] Alloy service survives reboot
- [ ] Performance acceptable (<100MB RAM)

---

## Resources

### Official Documentation

- **Grafana Alloy:** https://grafana.com/docs/alloy/
- **Grafana Cloud:** https://grafana.com/docs/grafana-cloud/
- **Prometheus:** https://prometheus.io/docs/
- **OpenTelemetry:** https://opentelemetry.io/docs/

### TTA.dev Documentation

- [Observability Architecture](../architecture/OBSERVABILITY_ARCHITECTURE.md)
- [Observability Integration](../integration/observability-integration.md)
- [Production Deployment](../../PRODUCTION_DEPLOYMENT_GUIDE.md)

### Quick References

- **Alloy Configuration Syntax:** https://grafana.com/docs/alloy/latest/reference/
- **Grafana Cloud Regions:** https://grafana.com/docs/grafana-cloud/account-management/regional-availability/
- **Systemd Service Management:** `man systemd.service`

---

**Last Updated:** 2025-11-15
**Author:** TTA.dev Team
**Status:** Production-Ready



---
**Logseq:** [[TTA.dev/Docs/Guides/Linux_native_observability]]
