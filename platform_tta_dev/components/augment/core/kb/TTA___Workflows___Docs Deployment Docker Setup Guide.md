---
title: Docker Setup Guide
tags: #TTA
status: Active
repo: theinterneti/TTA
path: docs/deployment/docker_setup_guide.md
created: 2025-11-01
updated: 2025-11-01
---
# [[TTA/Workflows/Docker Setup Guide]]

This document provides detailed instructions for setting up and using Docker with the Therapeutic Text Adventure (TTA) project.

> **Note**: The Docker setup for tta.dev is now integrated with the main TTA Docker environment. This guide provides an overview of the tta.dev-specific configuration, but for detailed information about the Docker setup, please refer to the main TTA documentation:
>
> - [[TTA/Workflows/README|Docker Overview]]
> - [[TTA/Workflows/orchestration|Docker Orchestration Guide]]
> - [[TTA/Workflows/README|Docker Environment Configurations]]
> - [[TTA/Workflows/codecarbon|CodeCarbon Integration]]

## Overview

The TTA project uses Docker to create a consistent development and deployment environment. The Docker setup includes:

- A Neo4j database container for the knowledge graph
- A Python application container with GPU support for running the TTA application
- Volume mounts for persistent data storage

## Prerequisites

Before you begin, ensure you have the following installed:

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)
- [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html) (for GPU support)

## Docker Compose Configuration

The project uses a `docker-compose.yml` file to define and run the multi-container Docker application. Here's a breakdown of the services:

### Neo4j Service

```yaml
neo4j:
  image: neo4j:5.13.0
  container_name: tta-neo4j
  ports:
    - "7474:7474"  # HTTP browser interface
    - "7687:7687"  # Bolt port
  volumes:
    - neo4j-data:/data
    - ./neo4j/conf:/conf
    - ./neo4j/logs:/logs
    - ./neo4j/plugins:/plugins
  environment:
    NEO4J_AUTH: neo4j/${NEO4J_PASSWORD:-password}
    NEO4J_PLUGINS: "apoc"
    NEO4J_dbms_security_procedures_unrestricted: apoc.*
    NEO4J_server_memory_heap_initial__size: 512m
    NEO4J_server_memory_heap_max__size: 2G
    NEO4J_server_memory_pagecache_size: 1G
  restart: unless-stopped
```

This service:
- Uses Neo4j version 5.13.0
- Exposes ports 7474 (browser interface) and 7687 (Bolt protocol)
- Mounts volumes for data persistence, configuration, logs, and plugins
- Sets environment variables for authentication, plugins, and memory allocation

### TTA Application Service

```yaml
app:
  build:
    context: .
    dockerfile: Dockerfile
  container_name: tta-app
  volumes:
    - .:/app:delegated
    - venv-data:/app/.venv
    - huggingface-cache:/root/.cache/huggingface
    - model-cache:/app/.model_cache
  env_file:
    - ../config/.env
  environment:
    - PYTHONPATH=/app
    - VIRTUAL_ENV=/app/.venv
    - PATH=/app/.venv/bin:$PATH
    - NVIDIA_VISIBLE_DEVICES=all
    - NEO4J_URI=bolt://neo4j:7687
    - NEO4J_USERNAME=neo4j
    - NEO4J_PASSWORD=${NEO4J_PASSWORD:-password}
    - MODEL_CACHE_DIR=/app/.model_cache
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: all
            capabilities: [gpu]
  depends_on:
    - neo4j
  stdin_open: true
  tty: true
```

This service:
- Builds from the Dockerfile in the current directory
- Mounts volumes for code, virtual environment, Hugging Face cache, and model cache
- Loads environment variables from a .env file
- Sets environment variables for Python, Neo4j connection, and model cache
- Configures GPU access using NVIDIA Container Toolkit
- Depends on the Neo4j service
- Enables interactive terminal access

### Volumes

```yaml
volumes:
  neo4j-data:
  venv-data:
  huggingface-cache:
  model-cache:
```

These volumes provide persistent storage for:
- Neo4j database data
- Python virtual environment
- Hugging Face model cache
- TTA model cache

## Orchestration Script

The TTA project now includes an orchestration script for managing Docker containers:

```bash
# Start development environment
./scripts/orchestrate.sh start dev

# Start production environment
./scripts/orchestrate.sh start prod

# Start with Jupyter notebook
./scripts/orchestrate.sh start jupyter

# Check container status
./scripts/orchestrate.sh status

# View container logs
./scripts/orchestrate.sh logs app

# Execute command in container
./scripts/orchestrate.sh exec app bash

# Stop containers
./scripts/orchestrate.sh stop

# Restart containers
./scripts/orchestrate.sh restart

# Build containers
./scripts/orchestrate.sh build
```

## CodeCarbon Integration

The project now includes [CodeCarbon](https://codecarbon.io/) for tracking energy usage and CO2 emissions during development and production.

### Basic Usage

```python
from codecarbon import EmissionsTracker

# Track emissions for a specific function
tracker = EmissionsTracker(project_name="TTA")
tracker.start()
# Your code here
emissions = tracker.stop()
print(f"Emissions: {emissions} kg CO2eq")
```

### Using as a Decorator

```python
from codecarbon import track_emissions

@track_emissions(project_name="TTA")
def my_function():
    # Your code here
    pass
```

### Viewing Emissions Data

Emissions data is saved to the `/app/logs/codecarbon` directory. You can view it with:

```bash
./scripts/orchestrate.sh exec app cat /app/logs/codecarbon/emissions.csv
```

For more information about CodeCarbon, see the [[TTA/Workflows/codecarbon|CodeCarbon Integration Guide]].

## Dockerfile

The Dockerfile defines how the TTA application container is built:

```dockerfile
# Use Hugging Face's Transformers image as base
FROM huggingface/transformers-pytorch-gpu:latest

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEBIAN_FRONTEND=noninteractive \
    VIRTUAL_ENV=/app/.venv \
    PATH=/app/.venv/bin:$PATH \
    PYTHONPATH=/app

# Install additional system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    python3-venv \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Create and activate virtual environment
RUN python3 -m venv /app/.venv

# Install Python dependencies
COPY requirements.txt .
RUN /app/.venv/bin/pip install --no-cache-dir --upgrade pip setuptools wheel && \
    /app/.venv/bin/pip install --no-cache-dir -r requirements.txt

# Install development tools
RUN /app/.venv/bin/pip install --no-cache-dir \
    black \
    isort \
    mypy \
    pytest \
    pytest-asyncio \
    codecarbon>=2.8.0

# Verify CUDA availability
RUN /app/.venv/bin/python -c "import torch; print('CUDA available:', torch.cuda.is_available())"
```

## Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Neo4j Docker Documentation](https://neo4j.com/docs/operations-manual/current/docker/)
- [CodeCarbon Documentation](https://codecarbon.io/docs)


---
**Logseq:** [[TTA.dev/Platform_tta_dev/Components/Augment/Core/Kb/Tta___workflows___docs deployment docker setup guide]]
