# Deployment Guide

This document provides instructions for deploying the Therapeutic Text Adventure (TTA) application to various environments.

## Overview

The TTA application can be deployed in several ways:

1. **Docker Deployment**: Using Docker and Docker Compose
2. **Local Deployment**: Running directly on the host machine
3. **Cloud Deployment**: Deploying to cloud platforms

## Prerequisites

Before deploying the TTA application, ensure you have:

- Access to the TTA codebase
- Required dependencies installed
- Appropriate permissions for the deployment environment
- Access to a Neo4j database (either local or remote)
- Access to LLM services (either local or remote)

## Docker Deployment

Docker deployment is the recommended approach for most scenarios. It provides a consistent environment and simplifies dependency management.

### Step 1: Prepare the Environment

1. Install Docker and Docker Compose:
   ```bash
   # For Ubuntu
   sudo apt-get update
   sudo apt-get install docker.io docker-compose
   
   # For Windows/Mac
   # Download and install Docker Desktop from https://www.docker.com/products/docker-desktop
   ```

2. Install NVIDIA Container Toolkit (for GPU support):
   ```bash
   # For Ubuntu
   distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
   curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
   curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list
   sudo apt-get update
   sudo apt-get install -y nvidia-container-toolkit
   sudo systemctl restart docker
   ```

### Step 2: Configure the Application

1. Create a `.env` file in the `config` directory:
   ```bash
   cp config/.env.example config/.env
   ```

2. Edit the `.env` file to set the required environment variables:
   ```
   # Neo4j Database Settings
   NEO4J_URI=bolt://neo4j:7687
   NEO4J_USERNAME=neo4j
   NEO4J_PASSWORD=your-secure-password
   
   # LLM Settings
   LLM_API_BASE=http://localhost:1234/v1
   LLM_API_KEY=your-api-key
   LLM_MODEL_NAME=qwen2.5-0.5b-instruct
   
   # Other Settings
   LOG_LEVEL=INFO
   ```

3. Configure the Docker Compose file if needed:
   ```bash
   # Modify memory limits, port mappings, etc.
   nano docker/docker-compose.yml
   ```

### Step 3: Build and Start the Containers

1. Navigate to the Docker directory:
   ```bash
   cd docker
   ```

2. Build and start the containers:
   ```bash
   docker-compose up -d
   ```

3. Verify that the containers are running:
   ```bash
   docker-compose ps
   ```

### Step 4: Initialize the Database

1. Access the application container:
   ```bash
   docker-compose exec app bash
   ```

2. Run the database initialization script:
   ```bash
   python -m src.knowledge.graph_initializer
   ```

### Step 5: Access the Application

1. For a command-line interface:
   ```bash
   docker-compose exec app python -m src.main
   ```

2. For a web interface (if implemented):
   ```
   Open http://localhost:8000 in your web browser
   ```

## Local Deployment

Local deployment runs the application directly on the host machine without Docker.

### Step 1: Prepare the Environment

1. Install Python 3.10 or later:
   ```bash
   # For Ubuntu
   sudo apt-get update
   sudo apt-get install python3.10 python3.10-venv python3-pip
   ```

2. Install Neo4j:
   ```bash
   # Download and install from https://neo4j.com/download/
   ```

3. Install CUDA and cuDNN (for GPU support):
   ```bash
   # Follow NVIDIA's installation guide
   ```

### Step 2: Set Up the Project

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\\Scripts\\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file:
   ```bash
   cp config/.env.example config/.env
   ```

5. Edit the `.env` file to set the required environment variables:
   ```
   # Neo4j Database Settings
   NEO4J_URI=bolt://localhost:7687
   NEO4J_USERNAME=neo4j
   NEO4J_PASSWORD=your-secure-password
   
   # LLM Settings
   LLM_API_BASE=http://localhost:1234/v1
   LLM_API_KEY=your-api-key
   LLM_MODEL_NAME=qwen2.5-0.5b-instruct
   ```

### Step 3: Initialize the Database

1. Start Neo4j:
   ```bash
   # Start the Neo4j service according to your installation
   ```

2. Run the database initialization script:
   ```bash
   python -m src.knowledge.graph_initializer
   ```

### Step 4: Run the Application

1. Start the application:
   ```bash
   python -m src.main
   ```

## Cloud Deployment

The TTA application can be deployed to various cloud platforms. Here's a general guide for deploying to cloud environments.

### Option 1: Docker-Based Cloud Deployment

1. **Build and Push Docker Image**:
   ```bash
   # Build the Docker image
   docker build -t tta-app:latest -f docker/Dockerfile .
   
   # Tag the image for your registry
   docker tag tta-app:latest your-registry/tta-app:latest
   
   # Push the image to your registry
   docker push your-registry/tta-app:latest
   ```

2. **Deploy to Cloud Platform**:
   - **AWS ECS**: Create a task definition and service
   - **Google Cloud Run**: Deploy the container
   - **Azure Container Instances**: Create a container group

### Option 2: Kubernetes Deployment

1. **Create Kubernetes Manifests**:
   ```yaml
   # deployment.yaml
   apiVersion: apps/v1
   kind: Deployment
   metadata:
     name: tta-app
   spec:
     replicas: 1
     selector:
       matchLabels:
         app: tta-app
     template:
       metadata:
         labels:
           app: tta-app
       spec:
         containers:
         - name: tta-app
           image: your-registry/tta-app:latest
           env:
           - name: NEO4J_URI
             valueFrom:
               secretKeyRef:
                 name: tta-secrets
                 key: neo4j-uri
           - name: NEO4J_USERNAME
             valueFrom:
               secretKeyRef:
                 name: tta-secrets
                 key: neo4j-username
           - name: NEO4J_PASSWORD
             valueFrom:
               secretKeyRef:
                 name: tta-secrets
                 key: neo4j-password
           resources:
             limits:
               nvidia.com/gpu: 1
   ```

2. **Deploy to Kubernetes**:
   ```bash
   kubectl apply -f deployment.yaml
   ```

## Production Considerations

When deploying to production, consider the following:

### Security

1. **Use Strong Passwords**: Set strong passwords for Neo4j and other services
2. **Secure Environment Variables**: Use secrets management for sensitive information
3. **Network Security**: Restrict access to the application and database
4. **Regular Updates**: Keep dependencies and the application up to date

### Performance

1. **Hardware Requirements**:
   - **CPU**: 4+ cores recommended
   - **RAM**: 16+ GB recommended
   - **GPU**: NVIDIA GPU with 8+ GB VRAM recommended
   - **Storage**: 50+ GB SSD recommended

2. **Database Optimization**:
   - Configure Neo4j memory settings based on available RAM
   - Create indexes for frequently queried properties
   - Consider using Neo4j Enterprise for production deployments

3. **Model Optimization**:
   - Use quantized models for better performance
   - Configure batch sizes and other parameters based on hardware

### Monitoring and Logging

1. **Set Up Monitoring**:
   - Use Prometheus and Grafana for metrics
   - Monitor CPU, RAM, GPU, and disk usage
   - Track application-specific metrics

2. **Configure Logging**:
   - Set appropriate log levels
   - Use a centralized logging solution
   - Implement log rotation

### Backup and Recovery

1. **Database Backup**:
   - Set up regular Neo4j backups
   - Store backups in a secure location
   - Test recovery procedures

2. **Application State Backup**:
   - Back up configuration files
   - Back up model caches if needed

## Troubleshooting

### Common Deployment Issues

1. **Database Connection Issues**:
   - Verify that Neo4j is running
   - Check connection URI, username, and password
   - Ensure network connectivity between the application and database

2. **GPU Access Issues**:
   - Verify that CUDA is installed and working
   - Check NVIDIA driver compatibility
   - Ensure the container has access to the GPU

3. **Memory Issues**:
   - Increase container memory limits
   - Optimize Neo4j memory settings
   - Use smaller models or batch sizes

## Related Documentation

- [Docker Guide](./Docker_Guide.md): Detailed Docker setup instructions
- [Environment Variables Guide](./Environment_Variables_Guide.md): Environment variable configuration
- [System Architecture](../Architecture/System_Architecture.md): Overall system architecture
- [Testing Guide](./Testing_Guide.md): Testing procedures
