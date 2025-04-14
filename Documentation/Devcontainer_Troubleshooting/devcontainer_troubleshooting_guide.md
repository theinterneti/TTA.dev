# Devcontainer Troubleshooting Guide

This guide provides solutions for common issues that may arise when using the devcontainer for development.

> **Note**: The devcontainer setup for tta.dev is now integrated with the main TTA devcontainer environment. This guide provides an overview of tta.dev-specific troubleshooting, but for detailed information about the devcontainer setup, please refer to the main TTA documentation:
>
> - [Devcontainer Setup Guide](../../../docs/devcontainer/setup.md)
> - [Devcontainer Troubleshooting Guide](../../../docs/devcontainer/troubleshooting.md)

## Common Issues

### Container Fails to Start

**Symptoms:**
- VS Code shows "Failed to start container"
- Error message about port conflicts

**Solutions:**
1. Check if another container is using the same ports:
   ```bash
   docker ps
   ```
2. Stop conflicting containers or change the port mapping in `docker-compose.yml`
3. Try restarting Docker:
   ```bash
   sudo systemctl restart docker
   ```

### Python Environment Issues

**Symptoms:**
- "Python interpreter not found"
- Import errors for installed packages

**Solutions:**
1. Verify the Python path in `.devcontainer/devcontainer.json`:
   ```json
   "python.defaultInterpreterPath": "/app/.venv/bin/python"
   ```
2. Rebuild the container to reinstall dependencies:
   ```bash
   ./scripts/orchestrate.sh build dev
   ```
3. Check if the virtual environment is activated:
   ```bash
   echo $VIRTUAL_ENV
   ```

## CodeCarbon Issues

### Missing Emissions Data

If emissions data is not being generated:

1. Check if the output directory exists:
   ```bash
   ./scripts/orchestrate.sh exec app ls -la /app/logs/codecarbon
   ```

2. Verify that CodeCarbon is installed:
   ```bash
   ./scripts/orchestrate.sh exec app pip list | grep codecarbon
   ```

3. Check the CodeCarbon log level:
   ```bash
   ./scripts/orchestrate.sh exec app env | grep CODECARBON
   ```

### Inaccurate Measurements

If measurements seem inaccurate:

1. Increase the measurement interval in `.codecarbon/config.json`:
   ```json
   {
     "measure_power_secs": 30
   }
   ```

2. Use a different tracking mode:
   ```json
   {
     "tracking_mode": "machine"
   }
   ```

3. Check if hardware power monitoring is available:
   ```bash
   ./scripts/orchestrate.sh exec app python -c "from codecarbon.core.cpu import IntelPowerGadget; print(IntelPowerGadget.is_available())"
   ```

## Additional Resources

- [VS Code Remote Development](https://code.visualstudio.com/docs/remote/remote-overview)
- [Docker Documentation](https://docs.docker.com/)
- [NVIDIA Container Toolkit Documentation](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/overview.html)
- [CodeCarbon Documentation](https://codecarbon.io/docs)
