# Use a specific Python version (adjust as needed)
FROM python:3.11

# Set environment variables to enable LangSmith (optional, but good for debugging)
ENV LANGCHAIN_TRACING_V2=true
ENV LANGCHAIN_ENDPOINT="https://api.smith.langchain.com"
ENV LANGCHAIN_API_KEY=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
ENV LANGCHAIN_PROJECT=react-agent 
ENV LANGSMITH_API_KEY=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

ENV openai_api_base=http://172.31.16.1:1234/v1,
ENV model="qwen2.5-7b-instruct"

ENV NEO4J_PASSWORD=11111111  

ENV TAVILY_API_KEY=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

ENV PYTHONUNBUFFERED=1
ENV POETRY_VERSION=1.7.1

# Install Poetry
RUN pip install --no-cache-dir poetry

# Copy project files (make sure .dockerignore excludes unnecessary files)
WORKDIR /app
COPY pyproject.toml poetry.lock /app/

# Install dependencies using Poetry
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

# Copy the application code
COPY . /app/

# Expose any necessary ports (e.g., for a Streamlit app)
#8501 for Streamlit, 1234 for LM Studio, 7687 for LM Studio
EXPOSE 8501
EXPOSE 1234
EXPOSE 7687
# You can add other setup steps here (e.g., installing system packages)

# Set a non-root user (good practice)
RUN useradd -m vscode
USER vscode

# No CMD or ENTRYPOINT here - VS Code handles the command to run
CMD ["poetry", "run", "python", "app/tta/main.py"]