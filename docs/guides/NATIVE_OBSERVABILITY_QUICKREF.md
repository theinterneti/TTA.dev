# Native Observability Quick Reference

**Replace Docker Desktop with Linux-native services for TTA.dev**

---

## 🚀 Quick Start (5 minutes)

### 1. Automated Installation

```bash
# Option 1: Full installation with Grafana Cloud
sudo GRAFANA_CLOUD_TOKEN="<your-token>" ./scripts/setup-native-observability.sh

# Option 2: Include local Prometheus for offline dev
sudo GRAFANA_CLOUD_TOKEN="<your-token>" \
     INSTALL_LOCAL_PROMETHEUS=true \
     ./scripts/setup-native-observability.sh

# Option 3: Full stack (Alloy + Local Prometheus + Local Grafana)
sudo GRAFANA_CLOUD_TOKEN="<your-token>" \
     INSTALL_LOCAL_PROMETHEUS=true \
     INSTALL_LOCAL_GRAFANA=true \
     ./scripts/setup-native-observability.sh
```

**Token Location:** Check `/home/thein/.env.tta-dev` for your Grafana Cloud API key.

---

## 🔧 Manual Installation (Ubuntu/Debian)

### Install Grafana Alloy

```bash
# Add Grafana repository
sudo mkdir -p /etc/apt/keyrings/
wget -q -O - https://apt.grafana.com/gpg.key | gpg --dearmor | sudo tee /etc/apt/keyrings/grafana.gpg > /dev/null
echo "deb [signed-by=/etc/apt/keyrings/grafana.gpg] https://apt.grafana.com stable main" | sudo tee /etc/apt/sources.list.d/grafana.list

# Install
sudo apt-get update
sudo apt-get install alloy

# Verify
alloy --version
```

### Configure Alloy

```bash
# Set credentials
sudo nano /etc/default/alloy
```

Add:
```bash
GRAFANA_CLOUD_TOKEN="<your-token-from-env-file>"
GRAFANA_CLOUD_STACK="theinterneti"
GRAFANA_CLOUD_REGION="prod-us-east-0"
```

```bash
# Create config
sudo nano /etc/alloy/config.alloy
```

Use the config from `docs/guides/LINUX_NATIVE_OBSERVABILITY.md` or let the script generate it.

### Start Service

```bash
sudo systemctl enable alloy
sudo systemctl start alloy
sudo systemctl status alloy
```

---

## 📊 Service Management

### Alloy Commands

```bash
# Status check
sudo systemctl status alloy

# View logs
journalctl -u alloy -f

# Restart service
sudo systemctl restart alloy

# Stop service
sudo systemctl stop alloy

# Check configuration syntax
sudo alloy fmt /etc/alloy/config.alloy
```

### Prometheus Commands (if installed locally)

```bash
# Status
sudo systemctl status prometheus

# Logs
journalctl -u prometheus -f

# Restart
sudo systemctl restart prometheus

# Access UI
open http://localhost:9090
```

### Grafana Commands (if installed locally)

```bash
# Status
sudo systemctl status grafana-server

# Restart
sudo systemctl restart grafana-server

# Access UI
open http://localhost:3000
# Default: admin/admin
```

---

## 🔍 Verification

### Check Metrics Export

```bash
# Check if your app is exporting metrics
curl http://localhost:9464/metrics

# Should show Prometheus-formatted metrics
```

### Check Alloy Health

```bash
# Alloy's own metrics
curl http://localhost:12345/metrics

# Check scrape targets
curl http://localhost:12345/metrics | grep -i scrape
```

### Check Grafana Cloud

1. Visit: https://theinterneti.grafana.net/
2. Navigate to Explore
3. Select Prometheus data source
4. Query: `{job="tta-dev-app"}`

---

## 🎯 What Gets Replaced

| Docker Service | Native Alternative | Port |
|----------------|-------------------|------|
| Prometheus | Grafana Alloy → Grafana Cloud | Scrapes :9464 |
| Grafana | Grafana Cloud (or local install) | :3000 (local) |
| Jaeger | Grafana Cloud Tempo | OTLP :4317/:4318 |
| OTLP Collector | Grafana Alloy (built-in) | :4317/:4318 |
| Pushgateway | Not needed (direct scrape) | - |

---

## 💾 Memory/Disk Usage

### Before (Docker)

```
Services: 5 containers
Memory: ~800MB
Disk: ~2GB (images)
Startup: ~30 seconds
```

### After (Native)

```
Services: 1 binary (Alloy)
Memory: ~100MB
Disk: ~50MB
Startup: ~2 seconds
```

**Savings:** ~700MB RAM, ~1.95GB disk space

---

## 🔧 Troubleshooting

### Alloy Won't Start

```bash
# Check logs
journalctl -u alloy -n 50 --no-pager

# Common issues:
# 1. Missing credentials
sudo cat /etc/default/alloy

# 2. Config syntax error
sudo alloy fmt /etc/alloy/config.alloy

# 3. Permission issues
sudo chown -R alloy:alloy /var/lib/alloy
sudo chown -R alloy:alloy /etc/alloy
```

### No Metrics in Grafana Cloud

```bash
# 1. Verify app is exporting
curl http://localhost:9464/metrics

# 2. Check Alloy is scraping
journalctl -u alloy | grep -i scrape

# 3. Check remote write
journalctl -u alloy | grep -i "remote.*write"

# 4. Verify credentials
journalctl -u alloy | grep -i "401\|403\|unauthorized"
```

### Can't Access Local Services

```bash
# Check if services are running
sudo systemctl status prometheus
sudo systemctl status grafana-server

# Check if ports are listening
sudo netstat -tulpn | grep -E '9090|3000'

# Check firewall
sudo ufw status
```

---

## 🔐 Security

### Protect Grafana Cloud Token

```bash
# Current: Environment file
# /etc/default/alloy
# Permissions: 600 (root only)

# Check permissions
ls -la /etc/default/alloy

# Should show: -rw------- 1 root root
```

### Firewall Rules

```bash
# OTLP ports (if accepting external traces)
sudo ufw allow 4317/tcp comment 'Alloy OTLP gRPC'
sudo ufw allow 4318/tcp comment 'Alloy OTLP HTTP'

# Metrics port (localhost only - no rule needed)
# Port 9464 should NOT be exposed externally
```

---

## 📚 Integration with TTA.dev

### Your Application (No Changes Needed!)

```python
from observability_integration import initialize_observability

# This stays the same
success = initialize_observability(
    service_name="tta-dev-app",
    enable_prometheus=True,
    prometheus_port=9464,  # Alloy scrapes this
    otlp_endpoint="http://localhost:4317",  # Alloy receives traces
)
```

### Environment Variables

Alloy uses environment variables from `/etc/default/alloy`:

```bash
GRAFANA_CLOUD_TOKEN  # Your API key
GRAFANA_CLOUD_STACK  # Your stack name (theinterneti)
GRAFANA_CLOUD_REGION # Your region (prod-us-east-0)
```

---

## 🚦 Migration Path

### Phase 1: Parallel (Recommended)

```bash
# Keep Docker running
docker-compose -f docker-compose.integration.yml up -d

# Install Alloy
sudo ./scripts/setup-native-observability.sh

# Compare data in Grafana Cloud vs local Prometheus
# Verify both show same metrics
```

### Phase 2: Switch

```bash
# Stop Docker
docker-compose -f docker-compose.integration.yml down

# Verify Alloy is running
sudo systemctl status alloy

# Check Grafana Cloud for data
```

### Phase 3: Cleanup

```bash
# Remove Docker images (optional)
docker rmi jaegertracing/all-in-one:1.52
docker rmi prom/prometheus:v2.48.1
docker rmi grafana/grafana:10.2.3
docker rmi otel/opentelemetry-collector-contrib:0.91.0

# Remove volumes
docker volume prune
```

---

## 📖 Configuration Files

### Key Files

```
/etc/alloy/config.alloy          # Main configuration
/etc/default/alloy               # Environment variables
/var/lib/alloy/                  # Data directory
/etc/systemd/system/alloy.service # Systemd service

Optional (if installed):
/etc/prometheus/prometheus.yml   # Prometheus config
/var/lib/prometheus/             # Prometheus data
/etc/grafana/grafana.ini         # Grafana config
```

### Backup Configuration

```bash
# Backup Alloy config
sudo cp /etc/alloy/config.alloy /etc/alloy/config.alloy.backup

# Backup environment
sudo cp /etc/default/alloy /etc/default/alloy.backup
```

---

## 🆘 Getting Help

### Check Logs

```bash
# Alloy logs (last 50 lines)
journalctl -u alloy -n 50 --no-pager

# Alloy logs (follow)
journalctl -u alloy -f

# Search for errors
journalctl -u alloy | grep -i error

# Check since boot
journalctl -u alloy -b
```

### Test Configuration

```bash
# Validate syntax
sudo alloy fmt /etc/alloy/config.alloy

# Dry-run mode (check config without starting)
sudo alloy run --dry-run /etc/alloy/config.alloy
```

### Restart Everything

```bash
# Nuclear option: restart all services
sudo systemctl restart alloy
sudo systemctl restart prometheus  # if installed
sudo systemctl restart grafana-server  # if installed

# Check status
sudo systemctl status alloy
sudo systemctl status prometheus
sudo systemctl status grafana-server
```

---

## 🔗 Resources

### Documentation

- **Full Guide:** `docs/guides/LINUX_NATIVE_OBSERVABILITY.md`
- **Alloy Docs:** https://grafana.com/docs/alloy/
- **Grafana Cloud:** https://grafana.com/docs/grafana-cloud/

### Quick Links

- **Grafana Cloud:** https://theinterneti.grafana.net/
- **Alloy Metrics:** http://localhost:12345/metrics
- **Local Prometheus:** http://localhost:9090 (if installed)
- **Local Grafana:** http://localhost:3000 (if installed)

### Common Commands

```bash
# Status check
sudo systemctl status alloy

# View logs
journalctl -u alloy -f

# Restart
sudo systemctl restart alloy

# Check app metrics
curl http://localhost:9464/metrics

# Check Alloy health
curl http://localhost:12345/metrics
```

---

## ✅ Success Checklist

- [ ] Grafana Alloy installed and running
- [ ] Configuration file created
- [ ] Credentials set in /etc/default/alloy
- [ ] Service starts on boot (enabled)
- [ ] App exports metrics on port 9464
- [ ] Metrics visible in Grafana Cloud
- [ ] OTLP receiver working (if using traces)
- [ ] Alloy service survives reboot
- [ ] Memory usage <150MB
- [ ] Docker services stopped (if migrating)

---

**Last Updated:** 2025-11-15
**Quick Start Script:** `./scripts/setup-native-observability.sh`


---
**Logseq:** [[TTA.dev/Docs/Guides/Native_observability_quickref]]
