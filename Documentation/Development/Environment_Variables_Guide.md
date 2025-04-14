# Environment Variables Guide

This document provides a comprehensive guide to the environment variables used in the Therapeutic Text Adventure (TTA) project.

## Overview

Environment variables are used to configure the TTA application without modifying the code. They control database connections, model selection, logging, and other aspects of the application's behavior.

## Configuration File

Environment variables are typically stored in a `.env` file in the `config` directory. This file is loaded when the application starts.

Example `.env` file:

```
# Neo4j Database Settings
NEO4J_URI=bolt://neo4j:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=password

# LLM Settings
LLM_API_BASE=http://localhost:1234/v1
LLM_API_KEY=not-needed
LLM_MODEL_NAME=qwen2.5-0.5b-instruct

# Model Cache
MODEL_CACHE_DIR=/app/.model_cache

# Logging
LOG_LEVEL=INFO
```

## Required Environment Variables

These environment variables are required for the application to function properly:

### Neo4j Database Settings

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `NEO4J_URI` | URI for connecting to the Neo4j database | `bolt://localhost:7687` | `bolt://neo4j:7687` |
| `NEO4J_USERNAME` | Username for the Neo4j database | `neo4j` | `neo4j` |
| `NEO4J_PASSWORD` | Password for the Neo4j database | None | `password` |

### LLM Settings

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `LLM_API_BASE` | Base URL for the LLM API | `http://localhost:1234/v1` | `http://localhost:1234/v1` |
| `LLM_API_KEY` | API key for the LLM service | `not-needed` | `not-needed` |
| `LLM_MODEL_NAME` | Name of the LLM model to use | `qwen2.5-0.5b-instruct` | `qwen2.5-0.5b-instruct` |

## Optional Environment Variables

These environment variables are optional and have sensible defaults:

### Model Cache

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `MODEL_CACHE_DIR` | Directory for caching models | `./.model_cache` | `/app/.model_cache` |
| `TRANSFORMERS_CACHE` | Directory for caching Hugging Face models | `~/.cache/huggingface` | `/app/.cache/huggingface` |

### Logging

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `LOG_LEVEL` | Logging level | `INFO` | `DEBUG` |
| `LOG_FILE` | Log file path | None (logs to console) | `/app/logs/tta.log` |

### Performance

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `BATCH_SIZE` | Batch size for model inference | `1` | `4` |
| `MAX_TOKENS` | Maximum number of tokens to generate | `512` | `1024` |
| `TEMPERATURE` | Temperature for text generation | `0.7` | `0.8` |

### Feature Flags

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `ENABLE_DYNAMIC_TOOLS` | Enable dynamic tool generation | `true` | `true` |
| `ENABLE_THERAPEUTIC_TOOLS` | Enable therapeutic tools | `true` | `true` |
| `ENABLE_AGENTIC_RAG` | Enable agentic RAG | `true` | `true` |

## Environment-Specific Variables

### Development Environment

For development, you might want to use these settings:

```
LOG_LEVEL=DEBUG
NEO4J_URI=bolt://localhost:7687
LLM_API_BASE=http://localhost:1234/v1
```

### Production Environment

For production, consider these settings:

```
LOG_LEVEL=INFO
LOG_FILE=/var/log/tta/tta.log
NEO4J_URI=bolt://neo4j.production:7687
NEO4J_PASSWORD=strong-password
```

## Docker Environment Variables

When using Docker, environment variables can be set in the `docker-compose.yml` file:

```yaml
environment:
  - PYTHONPATH=/app
  - VIRTUAL_ENV=/app/.venv
  - PATH=/app/.venv/bin:$PATH
  - NVIDIA_VISIBLE_DEVICES=all
  - NEO4J_URI=bolt://neo4j:7687
  - NEO4J_USERNAME=neo4j
  - NEO4J_PASSWORD=${NEO4J_PASSWORD:-password}
  - MODEL_CACHE_DIR=/app/.model_cache
```

## Loading Environment Variables

The TTA application loads environment variables using the `dotenv` package:

```python
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Access environment variables
neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
neo4j_username = os.getenv("NEO4J_USERNAME", "neo4j")
neo4j_password = os.getenv("NEO4J_PASSWORD")
```

## Environment Variable Validation

The TTA application validates environment variables using Pydantic:

```python
from pydantic import BaseSettings, Field

class Settings(BaseSettings):
    # Neo4j settings
    neo4j_uri: str = Field("bolt://localhost:7687", env="NEO4J_URI")
    neo4j_username: str = Field("neo4j", env="NEO4J_USERNAME")
    neo4j_password: str = Field(..., env="NEO4J_PASSWORD")
    
    # LLM settings
    llm_api_base: str = Field("http://localhost:1234/v1", env="LLM_API_BASE")
    llm_api_key: str = Field("not-needed", env="LLM_API_KEY")
    llm_model_name: str = Field("qwen2.5-0.5b-instruct", env="LLM_MODEL_NAME")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Load settings
settings = Settings()
```

## Troubleshooting

### Missing Environment Variables

If the application fails to start with an error about missing environment variables:

1. Check that the `.env` file exists in the correct location
2. Verify that the required environment variables are set
3. Ensure that the `.env` file is being loaded correctly

### Connection Issues

If the application cannot connect to Neo4j or other services:

1. Check that the URIs in the environment variables are correct
2. Verify that the services are running and accessible
3. Ensure that the credentials are correct

## Related Documentation

- [Docker Guide](./Docker_Guide.md): Docker setup and configuration
- [Installation Guide](../Overview.md#installation): General installation instructions
- [System Architecture](../Architecture/System_Architecture.md): Overall system architecture
