# --- Base Image ---
# Use a specific Python version. 'slim' variant is smaller, good for production.
FROM python:3.11-slim as base

# Set working directory inside the container.  All subsequent commands are relative to this.
WORKDIR /app

# --- Install System Dependencies (if needed) ---
# If your Python libraries or application requires system-level dependencies
# (like specific libraries, tools, etc.), install them here using 'apt-get'.
# For example, if you needed 'libpq-dev' for psycopg2 (PostgreSQL):
# RUN apt-get update && apt-get install -y --no-install-recommends libpq-dev
#
# For this AI project, we might not need any system dependencies initially.
# If you find errors later related to missing system libraries, you can add them here.
# For now, we'll skip this section.
#
# Example of installing system packages (uncomment if needed):
# RUN apt-get update && apt-get install -y --no-install-recommends some-system-package another-package


# --- Copy Requirements File and Install Python Dependencies ---
# Copy only the requirements.txt file first to leverage Docker's caching.
# This means if only application code changes, Docker can reuse the cached dependency installation layer,
# making builds much faster.
COPY requirements.txt /app/

# Install Python dependencies from requirements.txt.
# --no-cache-dir: Prevents pip from caching downloaded packages, reduces image size.
# -r requirements.txt: Tells pip to install packages listed in requirements.txt.
RUN pip install --no-cache-dir -r requirements.txt


# --- Copy Application Code ---
# Copy the rest of your application code into the container.
# IMPORTANT: Make sure you have a '.dockerignore' file to exclude unnecessary files
# (like .git folders, __pycache__, etc.) to keep the image size small and build fast.
COPY . /app/


# --- Expose Ports ---
# Expose the ports that your application and services will use.
# 8501:  Likely for Streamlit (if you are using it)
# 1234:  Default port for LM Studio
# 7687:  Default Bolt port for Neo4j (though Neo4j should ideally be in a separate container)
EXPOSE 8501 1234 7687


# --- Create a Non-Root User for Security ---
# Create a new user named 'appuser' with a home directory.
RUN useradd -m appuser

# Switch to the 'appuser' user for running the application.
# Running as a non-root user is a security best practice.
USER appuser


# --- Command to Run the Application ---
# Define the command to execute when the container starts.
# Assumes your main Python script is in 'src/main.py'.
# Adjust the path if your main script is located elsewhere.
CMD ["python", "src/main.py"]

# --- IMPORTANT REMINDERS ---
# 1. ENVIRONMENT VARIABLES:
#    - DO NOT hardcode API keys, passwords, or sensitive configuration directly in this Dockerfile.
#    - Pass environment variables at runtime using Docker Compose, 'docker run -e', or your container orchestration system.
#    - Use a '.env' file (and load it in your Python code with 'python-dotenv' as you are already doing) for local development.
#
# 2. .dockerignore FILE:
#    - Create a '.dockerignore' file in the same directory as your Dockerfile.
#    - Add patterns for files and directories you don't want to include in the Docker image
#      (e.g., .git/, __pycache__/, *.pyc, .env, node_modules/, etc.).
#    - This significantly reduces image size and build time.
#
# 3. PRODUCTION vs. DEVELOPMENT:
#    - This Dockerfile is suitable for both development and production.
#    - For development, you'll typically use it with VS Code Dev Containers, which mounts your source code.
#    - For production, you'll build the image and deploy it.
#
# 4. ADJUST CMD:
#    - Ensure the 'CMD' instruction correctly points to your main Python application file.