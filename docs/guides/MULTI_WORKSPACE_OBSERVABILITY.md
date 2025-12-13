# Multi-Workspace Observability Configuration

**Managing observability across multiple TTA.dev workspace clones**

**Last Updated:** 2025-11-15

---

## 🎯 Overview

You have multiple TTA.dev workspace clones on the same machine:
- `/home/thein/repos/TTA.dev` (main)
- `/home/thein/repos/TTA.dev-cline`
- `/home/thein/repos/TTA.dev-copilot`
- `/home/thein/repos/TTA.dev-augment`

**Key Insight:** Grafana Alloy is installed **globally** (system-wide), so you install it **once** and all workspaces share the same observability infrastructure.

---

## 📦 Installation Scope

### Global Components (Install Once Per Machine)

```
System-Wide Installation:
├── /usr/bin/alloy                    # Alloy binary
├── /etc/alloy/config.alloy           # Configuration
├── /etc/default/alloy                # Environment variables
├── /var/lib/alloy/                   # Data directory
└── /etc/systemd/system/alloy.service # Systemd service

Optional:
├── /usr/local/bin/prometheus         # Prometheus binary
├── /etc/prometheus/prometheus.yml    # Prometheus config
├── /usr/sbin/grafana-server          # Grafana binary
└── /etc/grafana/grafana.ini          # Grafana config
```

**Action Required:** Install **once** using the script:

```bash
cd /home/thein/repos/TTA.dev  # Any workspace
sudo GRAFANA_CLOUD_TOKEN="<token>" ./scripts/setup-native-observability.sh
```

### Per-Workspace Components (No Installation Needed)

Each workspace has its own:
- Application code (Python packages)
- Prometheus metrics exporter (port 9464 by default)
- OTLP trace exporter (port 4317/4318)

**Action Required:** Copy the documentation and scripts to other workspaces (optional):

```bash
# From main workspace
cd /home/thein/repos/TTA.dev

# Copy to other workspaces
cp -r docs/guides/LINUX_NATIVE_OBSERVABILITY.md \
      docs/guides/NATIVE_OBSERVABILITY_QUICKREF.md \
      docs/guides/DOCKER_FREE_OBSERVABILITY_MIGRATION.md \
      /home/thein/repos/TTA.dev-cline/docs/guides/

cp scripts/setup-native-observability.sh \
   /home/thein/repos/TTA.dev-cline/scripts/

# Repeat for TTA.dev-copilot and TTA.dev-augment
```

---

## 🔍 How It Works

### Single Alloy Instance Serves All Workspaces

```
┌─────────────────────────────────────────────────────────┐
│  System-Wide Grafana Alloy Service (Port 12345)        │
│  ├─ Scrapes metrics from all apps                      │
│  ├─ Collects systemd logs                              │
│  ├─ Receives OTLP traces                               │
│  └─ Ships everything to Grafana Cloud                  │
└────────────┬────────────────────────────────────────────┘
             │
             ├──► TTA.dev (main)           :9464
             ├──► TTA.dev-cline            :9465 (different port)
             ├──► TTA.dev-copilot          :9466 (different port)
             └──► TTA.dev-augment          :9467 (different port)
```

### Port Allocation Strategy

Since all workspaces share the same Alloy instance, **each workspace must use a different port** to avoid conflicts.

**Recommended Port Allocation:**

| Workspace | Prometheus Port | OTLP gRPC | OTLP HTTP | Notes |
|-----------|-----------------|-----------|-----------|-------|
| TTA.dev (main) | 9464 | 4317 | 4318 | Default |
| TTA.dev-cline | 9465 | 4417 | 4418 | +100 from default |
| TTA.dev-copilot | 9466 | 4517 | 4518 | +200 from default |
| TTA.dev-augment | 9467 | 4617 | 4618 | +300 from default |

---

## ⚙️ Configuration

### Step 1: Update Alloy Configuration (One Time)

Edit `/etc/alloy/config.alloy` to scrape from all workspaces:

```bash
sudo nano /etc/alloy/config.alloy
```

**Update the scrape configuration:**

```alloy
// Prometheus metrics scraping from all TTA.dev workspaces
prometheus.scrape "tta_main" {
  targets = [{
    __address__ = "localhost:9464",
    workspace = "main",
  }]
  forward_to = [prometheus.remote_write.grafana_cloud.receiver]
  scrape_interval = "15s"
}

prometheus.scrape "tta_cline" {
  targets = [{
    __address__ = "localhost:9465",
    workspace = "cline",
  }]
  forward_to = [prometheus.remote_write.grafana_cloud.receiver]
  scrape_interval = "15s"
}

prometheus.scrape "tta_copilot" {
  targets = [{
    __address__ = "localhost:9466",
    workspace = "copilot",
  }]
  forward_to = [prometheus.remote_write.grafana_cloud.receiver]
  scrape_interval = "15s"
}

prometheus.scrape "tta_augment" {
  targets = [{
    __address__ = "localhost:9467",
    workspace = "augment",
  }]
  forward_to = [prometheus.remote_write.grafana_cloud.receiver]
  scrape_interval = "15s"
}

// Rest of config stays the same...
prometheus.remote_write "grafana_cloud" {
  endpoint {
    url = "https://prometheus-" + env("GRAFANA_CLOUD_REGION") + ".grafana.net/api/prom/push"
    basic_auth {
      username = env("GRAFANA_CLOUD_STACK")
      password = env("GRAFANA_CLOUD_TOKEN")
    }
  }
}

// OTLP receiver (shared by all workspaces)
otelcol.receiver.otlp "default" {
  grpc {
    endpoint = "0.0.0.0:4317"  // Main workspace
  }
  http {
    endpoint = "0.0.0.0:4318"  // Main workspace
  }
  output {
    traces = [otelcol.exporter.otlp.grafana_cloud.input]
  }
}

// Additional OTLP receivers for other workspaces
otelcol.receiver.otlp "cline" {
  grpc {
    endpoint = "0.0.0.0:4417"
  }
  http {
    endpoint = "0.0.0.0:4418"
  }
  output {
    traces = [otelcol.exporter.otlp.grafana_cloud.input]
  }
}

otelcol.receiver.otlp "copilot" {
  grpc {
    endpoint = "0.0.0.0:4517"
  }
  http {
    endpoint = "0.0.0.0:4518"
  }
  output {
    traces = [otelcol.exporter.otlp.grafana_cloud.input]
  }
}

otelcol.receiver.otlp "augment" {
  grpc {
    endpoint = "0.0.0.0:4617"
  }
  http {
    endpoint = "0.0.0.0:4618"
  }
  output {
    traces = [otelcol.exporter.otlp.grafana_cloud.input]
  }
}

// Auth and exporter (shared)
otelcol.auth.basic "grafana_cloud" {
  username = env("GRAFANA_CLOUD_STACK")
  password = env("GRAFANA_CLOUD_TOKEN")
}

otelcol.exporter.otlp "grafana_cloud" {
  client {
    endpoint = "tempo-" + env("GRAFANA_CLOUD_REGION") + ".grafana.net:443"
    auth = otelcol.auth.basic.grafana_cloud.handler
  }
}

// Logs (shared - uses journald)
loki.source.journal "system_logs" {
  max_age = "24h"
  forward_to = [loki.write.grafana_cloud.receiver]
  labels = {
    job = "systemd-journal",
    host = env("HOSTNAME"),
  }
}

loki.write "grafana_cloud" {
  endpoint {
    url = "https://logs-" + env("GRAFANA_CLOUD_REGION") + ".grafana.net/loki/api/v1/push"
    basic_auth {
      username = env("GRAFANA_CLOUD_STACK")
      password = env("GRAFANA_CLOUD_TOKEN")
    }
  }
}
```

**Restart Alloy after configuration changes:**

```bash
sudo systemctl restart alloy
sudo systemctl status alloy
```

### Step 2: Configure Each Workspace Application

Update each workspace to use its assigned port.

#### TTA.dev (Main) - Port 9464 (Default)

```python
# No changes needed - uses default port
from observability_integration import initialize_observability

success = initialize_observability(
    service_name="tta-dev-main",
    enable_prometheus=True,
    prometheus_port=9464,
    otlp_endpoint="http://localhost:4317",
)
```

#### TTA.dev-cline - Port 9465

```python
from observability_integration import initialize_observability

success = initialize_observability(
    service_name="tta-dev-cline",
    enable_prometheus=True,
    prometheus_port=9465,  # Different port
    otlp_endpoint="http://localhost:4417",  # Different port
)
```

#### TTA.dev-copilot - Port 9466

```python
from observability_integration import initialize_observability

success = initialize_observability(
    service_name="tta-dev-copilot",
    enable_prometheus=True,
    prometheus_port=9466,  # Different port
    otlp_endpoint="http://localhost:4517",  # Different port
)
```

#### TTA.dev-augment - Port 9467

```python
from observability_integration import initialize_observability

success = initialize_observability(
    service_name="tta-dev-augment",
    enable_prometheus=True,
    prometheus_port=9467,  # Different port
    otlp_endpoint="http://localhost:4617",  # Different port
)
```

---

## 🎯 Simplified Alternative (Recommended)

If managing multiple ports is too complex, use **service name labels** instead:

### Single Port, Different Labels

**Keep all workspaces on port 9464**, but differentiate them by **service name**:

```python
# TTA.dev (main)
initialize_observability(
    service_name="tta-dev-main",  # Unique name
    prometheus_port=9464,
)

# TTA.dev-cline
initialize_observability(
    service_name="tta-dev-cline",  # Unique name
    prometheus_port=9464,
)

# TTA.dev-copilot
initialize_observability(
    service_name="tta-dev-copilot",  # Unique name
    prometheus_port=9464,
)

# TTA.dev-augment
initialize_observability(
    service_name="tta-dev-augment",  # Unique name
    prometheus_port=9464,
)
```

**Constraint:** Only **one workspace can run at a time** (port conflict).

**Alloy Configuration (Simple):**

```alloy
prometheus.scrape "tta_app" {
  targets = [{
    __address__ = "localhost:9464",
  }]
  forward_to = [prometheus.remote_write.grafana_cloud.receiver]
  scrape_interval = "15s"
}

// Rest of config as before...
```

**Benefits:**
- ✅ No configuration changes needed
- ✅ No port management
- ✅ Simple Alloy config

**Trade-off:**
- ❌ Can only run one workspace at a time
- ✅ But this matches typical development workflow

---

## 📊 Querying in Grafana Cloud

### Filter by Workspace

**Using service names:**

```promql
# All metrics from main workspace
{service_name="tta-dev-main"}

# Metrics from cline workspace
{service_name="tta-dev-cline"}

# Compare across workspaces
rate(primitive_execution_duration_seconds_sum{service_name=~"tta-dev-.*"}[5m])
```

**Using workspace labels (if using multi-port setup):**

```promql
# Main workspace
{workspace="main"}

# Cline workspace
{workspace="cline"}

# All workspaces
{workspace=~".*"}
```

---

## 🔧 Firewall Configuration (If Needed)

If using multiple OTLP ports:

```bash
# Allow OTLP receivers
sudo ufw allow 4317/tcp comment 'Alloy OTLP main'
sudo ufw allow 4318/tcp comment 'Alloy OTLP main HTTP'
sudo ufw allow 4417/tcp comment 'Alloy OTLP cline'
sudo ufw allow 4418/tcp comment 'Alloy OTLP cline HTTP'
sudo ufw allow 4517/tcp comment 'Alloy OTLP copilot'
sudo ufw allow 4518/tcp comment 'Alloy OTLP copilot HTTP'
sudo ufw allow 4617/tcp comment 'Alloy OTLP augment'
sudo ufw allow 4618/tcp comment 'Alloy OTLP augment HTTP'
```

---

## 🚀 Quick Setup Summary

### One-Time Global Installation

```bash
# Run once per machine
cd /home/thein/repos/TTA.dev
TOKEN=$(grep GRAFANA_CLOUD_API_KEY ~/.env.tta-dev | cut -d= -f2)
sudo GRAFANA_CLOUD_TOKEN="$TOKEN" ./scripts/setup-native-observability.sh
```

### Per-Workspace Configuration (Choose One)

**Option A: Simple (Recommended) - Same Port, Different Service Names**

1. All workspaces use port 9464
2. Each has unique `service_name`
3. Only run one workspace at a time
4. No Alloy config changes needed

**Option B: Advanced - Different Ports**

1. Assign different ports to each workspace
2. Update Alloy config to scrape all ports
3. Run multiple workspaces simultaneously
4. More complex but more flexible

---

## ✅ Verification

### Check Alloy Sees All Workspaces

```bash
# View Alloy metrics
curl http://localhost:12345/metrics | grep scrape_samples

# Should show metrics being scraped from configured targets
```

### Check Grafana Cloud

1. Visit: https://theinterneti.grafana.net/
2. Explore → Prometheus
3. Query: `{service_name=~"tta-dev-.*"}`
4. Should see metrics from all workspaces

---

## 🎓 Best Practices

### Development Workflow

**Recommended:** Use the **simple approach** (same port, different service names):
- ✅ Easy to set up
- ✅ No port management
- ✅ Matches typical workflow (one workspace at a time)
- ✅ Easy to query in Grafana Cloud

**Advanced:** Use **multi-port setup** only if you:
- Need to run multiple workspaces simultaneously
- Are testing cross-workspace integrations
- Have specific debugging requirements

### Service Naming Convention

Use clear, consistent service names:

```python
# Good
service_name="tta-dev-main"
service_name="tta-dev-cline"
service_name="tta-dev-copilot"

# Bad
service_name="app"
service_name="test"
service_name="my-service"
```

### Grafana Cloud Queries

Create saved queries for each workspace:

```promql
# Main workspace overview
rate(primitive_execution_duration_seconds_sum{service_name="tta-dev-main"}[5m])

# Cline workspace errors
increase(primitive_execution_errors_total{service_name="tta-dev-cline"}[1h])

# Cross-workspace comparison
sum by (service_name) (rate(http_requests_total[5m]))
```

---

## 🆘 Troubleshooting

### Port Already in Use

```bash
# Find what's using a port
sudo lsof -i :9464

# Kill the process if needed
sudo kill -9 <PID>

# Or change port in your app configuration
```

### Metrics Not Appearing for Workspace

```bash
# 1. Check app is exporting
curl http://localhost:9464/metrics  # or 9465, 9466, etc.

# 2. Check Alloy is scraping
journalctl -u alloy | grep -i scrape

# 3. Verify Alloy config
sudo alloy fmt /etc/alloy/config.alloy

# 4. Restart Alloy
sudo systemctl restart alloy
```

### Multiple Workspaces Conflict

If you see port conflicts:
1. Check which workspace is running: `ps aux | grep python`
2. Stop the conflicting workspace
3. Or use different ports (Option B)

---

## 📝 Summary

### Global Installation (Once Per Machine)

- ✅ Install Grafana Alloy once
- ✅ Configure with Grafana Cloud credentials
- ✅ All workspaces share same Alloy instance

### Per-Workspace Setup

**Simple (Recommended):**
- ✅ Same port (9464)
- ✅ Unique service names
- ✅ One workspace at a time

**Advanced:**
- ✅ Different ports per workspace
- ✅ Run multiple simultaneously
- ⚠️ More complex configuration

### Documentation Files to Copy

```bash
# Copy these to other workspaces (optional)
docs/guides/LINUX_NATIVE_OBSERVABILITY.md
docs/guides/NATIVE_OBSERVABILITY_QUICKREF.md
docs/guides/MULTI_WORKSPACE_OBSERVABILITY.md
scripts/setup-native-observability.sh
```

---

**Last Updated:** 2025-11-15
**Status:** Production-Ready
**Recommendation:** Use simple approach (same port, different service names) for most cases


---
**Logseq:** [[TTA.dev/Docs/Guides/Multi_workspace_observability]]
