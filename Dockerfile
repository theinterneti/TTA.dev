# syntax=docker/dockerfile:1

# --- Base Image ---
FROM python:3.11-slim as base

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# --- Builder Stage ---
FROM base as builder

# Copy requirements file
COPY requirements.txt ./

# Install Python dependencies
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir streamlit>=1.30.0

# Copy application source code
COPY . .

# Make setup.sh executable
RUN chmod +x setup.sh

# --- Final Stage ---
FROM base as final

# Copy installed dependencies from builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application source code
COPY . .

# Make setup.sh executable
RUN chmod +x setup.sh

# Expose application ports
EXPOSE 8501 1234 7687

# Create necessary directories
RUN mkdir -p /app/data /app/logs

# Set non-root user for security
RUN useradd -ms /bin/bash appuser
RUN chown -R appuser:appuser /app
USER appuser

# Command to run the application
CMD ["./setup.sh"]