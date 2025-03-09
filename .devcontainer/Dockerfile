# --- Multi-Stage Build: Builder Stage (for Dependencies) ---
    FROM python:3.11-slim as builder

    # Set the working directory in the container
    WORKDIR /app/build
    
    # Copy only requirements file for caching - IMPORTANT for build speed!
    COPY requirements.txt .
    
    # Install system dependencies
    RUN apt-get update && apt-get install -y --no-install-recommends \
        python3-pip \
        git \
        sudo \
        curl \
        && rm -rf /var/lib/apt/lists/*
    
    # Install Python dependencies
    RUN pip install --no-cache-dir -r requirements.txt
    
    # Copy application code
    COPY . /app
    
    # --- Final Image: Runtime Stage ---
    FROM python:3.11-slim as final
    
    # Copy dependencies from builder stage
    COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
    COPY --from=builder /usr/local/bin /usr/local/bin
    
    # Expose the ports that your application and services will use.
    EXPOSE 8501 1234 7687
    
    # Create a Non-Root User for Security
    RUN useradd -m appuser && usermod -aG sudo appuser
    USER appuser
    
    # Command to Run the Application
    CMD ["python", "/app/src/main.py"]
    
