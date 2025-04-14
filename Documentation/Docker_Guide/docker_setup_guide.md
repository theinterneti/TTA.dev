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