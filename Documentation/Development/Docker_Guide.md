# Docker Setup Guide

This document provides detailed instructions for setting up and using Docker with the Therapeutic Text Adventure (TTA) project.

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
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Create and activate virtual environment
RUN python -m venv /app/.venv

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Install development tools
RUN pip install --no-cache-dir \
    black \
    isort \
    mypy \
    pytest \
    pytest-asyncio

# Verify CUDA availability
RUN python -c "import torch; print('CUDA available:', torch.cuda.is_available())"
```

This Dockerfile:
- Uses the Hugging Face Transformers image with PyTorch and GPU support
- Sets environment variables for Python and the virtual environment
- Installs system dependencies
- Creates a Python virtual environment
- Installs Python dependencies from requirements.txt
- Installs development tools
- Verifies CUDA availability

## Using Docker Compose

### Starting the Services

To start the Docker services:

```bash
cd tta.prototype/docker
docker-compose up -d
```

This will start both the Neo4j and TTA application services in detached mode.

### Accessing the Services

- **Neo4j Browser**: Open http://localhost:7474 in your web browser
- **TTA Application**: Access the container with `docker-compose exec app bash`

### Stopping the Services

To stop the Docker services:

```bash
docker-compose down
```

To stop the services and remove the volumes:

```bash
docker-compose down -v
```

## Environment Variables

The TTA application uses environment variables for configuration. These are loaded from the `../config/.env` file. Here are the key environment variables:

- `NEO4J_PASSWORD`: Password for the Neo4j database (default: "password")
- `NEO4J_URI`: URI for connecting to the Neo4j database (default: "bolt://neo4j:7687")
- `NEO4J_USERNAME`: Username for the Neo4j database (default: "neo4j")
- `MODEL_CACHE_DIR`: Directory for caching models (default: "/app/.model_cache")
- `LLM_API_BASE`: Base URL for the LLM API
- `LLM_API_KEY`: API key for the LLM service
- `LLM_MODEL_NAME`: Name of the LLM model to use

## Troubleshooting

### GPU Access Issues

If you encounter issues with GPU access:

1. Verify that the NVIDIA Container Toolkit is installed:
   ```bash
   nvidia-smi
   ```

2. Check that Docker can access the GPU:
   ```bash
   docker run --gpus all nvidia/cuda:11.0-base nvidia-smi
   ```

3. Ensure that the `deploy` section in `docker-compose.yml` is correctly configured.

### Neo4j Connection Issues

If the TTA application cannot connect to Neo4j:

1. Verify that the Neo4j container is running:
   ```bash
   docker ps | grep neo4j
   ```

2. Check the Neo4j logs:
   ```bash
   docker-compose logs neo4j
   ```

3. Ensure that the environment variables for Neo4j connection are correctly set.

## Related Documentation

- [System Architecture](../Architecture/System_Architecture.md): Overview of the TTA system architecture
- [Knowledge Graph](../Architecture/Knowledge_Graph.md): Details about the Neo4j knowledge graph
- [Installation Guide](../Overview.md#installation): General installation instructions
- [Environment Variables Guide](./Environment_Variables_Guide.md): Detailed information about environment variables
