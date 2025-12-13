# TTA.dev Persistence Setup

This document explains what persists across sessions and how to set up automatic startup for the TTA.dev observability infrastructure.

## What Persists Automatically ✅

1. **Git Post-Commit Hook** - Already installed at `.git/hooks/post-commit`
   - Runs automatically on every commit
   - Pushes metrics to Pushgateway
   - Survives reboots and new terminals

2. **Configuration Files**
   - `prometheus.yml` - Scrape configurations
   - `docker-compose.integration.yml` - Infrastructure setup
   - All scripts in `/scripts` directory

## What Needs Setup 🔧

### Option 1: Manual Startup (Quick)

Run these commands each time you open a new session:

```bash
# Start observability stack
cd /home/thein/repos/TTA.dev/packages/tta-dev-primitives
docker-compose -f docker-compose.integration.yml up -d

# Start agent activity tracker
cd /home/thein/repos/TTA.dev
uv run python scripts/agent-activity-tracker-tta.py --workspace /home/thein/repos/TTA.dev --port 8001 &
```

### Option 2: Automatic Startup (Recommended)

Run the setup script once to configure systemd and Docker restart policies:

```bash
# Run setup (requires sudo for systemd)
/home/thein/repos/TTA.dev/scripts/setup-persistence.sh
```

This will:
- ✅ Add `restart: unless-stopped` to all Docker services
- ✅ Install systemd service for agent-activity-tracker
- ✅ Enable automatic startup on boot
- ✅ Start everything immediately

## What Gets Installed

### 1. Systemd Service

**File:** `/etc/systemd/system/agent-activity-tracker.service`

**Purpose:** Runs agent-activity-tracker-tta.py as a system service

**Commands:**
```bash
# Start service
sudo systemctl start agent-activity-tracker

# Stop service
sudo systemctl stop agent-activity-tracker

# View status
sudo systemctl status agent-activity-tracker

# View logs
sudo journalctl -u agent-activity-tracker -f

# Enable on boot
sudo systemctl enable agent-activity-tracker

# Disable on boot
sudo systemctl disable agent-activity-tracker
```

### 2. Docker Restart Policies

**File:** `docker-compose.integration.yml`

**Added:** `restart: unless-stopped` to all services:
- Jaeger (traces)
- Prometheus (metrics)
- Grafana (visualization)
- OpenTelemetry Collector
- Pushgateway (git hooks)

**Behavior:**
- Containers restart automatically if they crash
- Containers start automatically on system boot
- Containers stay stopped if manually stopped

## Verification

After running setup, verify everything is working:

```bash
# Check systemd service
sudo systemctl status agent-activity-tracker

# Check Docker containers
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Check metrics endpoint
curl http://localhost:8001/metrics | grep copilot_

# Check Prometheus targets
curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | {job: .labels.job, health: .health}'
```

Expected output:
```
✅ agent-activity-tracker.service - active (running)
✅ 5 Docker containers running
✅ Metrics available on port 8001
✅ Prometheus scraping both agent-activity-tracker and pushgateway
```

## Access Points

After setup, these services are always available:

| Service | URL | Purpose |
|---------|-----|---------|
| Agent Metrics | http://localhost:8001/metrics | File system activity metrics |
| Prometheus | http://localhost:9090 | Metrics database and queries |
| Jaeger UI | http://localhost:16686 | Distributed traces visualization |
| Grafana | http://localhost:3000 | Dashboards (admin/admin) |
| Pushgateway | http://localhost:9091 | Git hook metrics |

## Logs

View logs from different components:

```bash
# Agent activity tracker (systemd)
sudo journalctl -u agent-activity-tracker -f

# Docker containers
cd /home/thein/repos/TTA.dev/packages/tta-dev-primitives
docker-compose -f docker-compose.integration.yml logs -f

# Specific container
docker logs -f tta-prometheus
docker logs -f tta-jaeger
docker logs -f tta-grafana
```

## Troubleshooting

### Agent tracker not starting

```bash
# Check service status
sudo systemctl status agent-activity-tracker

# View recent logs
sudo journalctl -u agent-activity-tracker -n 50

# Restart service
sudo systemctl restart agent-activity-tracker
```

### Docker containers not starting

```bash
# Check container status
docker ps -a

# View logs
docker-compose -f docker-compose.integration.yml logs

# Restart everything
docker-compose -f docker-compose.integration.yml restart
```

### Metrics not appearing

```bash
# Check if agent tracker is running
ps aux | grep agent-activity-tracker

# Check metrics endpoint
curl http://localhost:8001/metrics

# Check Prometheus targets
curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | select(.labels.job=="agent-activity-tracker")'
```

## Uninstall

To remove the automatic startup:

```bash
# Stop and disable systemd service
sudo systemctl stop agent-activity-tracker
sudo systemctl disable agent-activity-tracker
sudo rm /etc/systemd/system/agent-activity-tracker.service
sudo systemctl daemon-reload

# Stop Docker containers (remove restart policies manually from docker-compose.yml first)
cd /home/thein/repos/TTA.dev/packages/tta-dev-primitives
docker-compose -f docker-compose.integration.yml down
```

## Notes

- **Systemd service** runs as your user (`thein`) with your environment
- **Docker containers** run as root but are managed by Docker daemon
- **Logs** are written to `/var/log/tta-agent-tracker.log` for systemd service
- **Git hook** always persists (installed in `.git/hooks/`)
- **Restart policy** `unless-stopped` means containers start on boot unless you manually stopped them

---

**Created:** November 2, 2025
**Author:** TTA.dev Team
**Purpose:** Persistence and automatic startup documentation


---
**Logseq:** [[TTA.dev/Scripts/Persistence_setup]]
