# TTA Development Guide

This guide provides detailed information for developers working on the Therapeutic Text Adventure (TTA) project.

## 🚀 Getting Started

This guide provides instructions for setting up the development environment and contributing to the Therapeutic Text Adventure (TTA) project.

### Prerequisites

- Python 3.9+
- Neo4j 4.4+
- Git
- [Docker](https://www.docker.com/products/docker-desktop/) (for devcontainer)
- [VS Code](https://code.visualstudio.com/) with the [Remote - Containers](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) extension (for devcontainer)
- [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html) for GPU support (optional but recommended)

### Installation Options

#### Using the Devcontainer (Recommended)

The TTA project uses VS Code's devcontainer feature to provide a consistent development environment. This approach ensures that all developers have the same dependencies, tools, and configuration.

1. Clone the repository:
   ```bash
   git clone https://github.com/your-organization/tta.git
   cd tta
   ```

2. Open the project in VS Code:
   ```bash
   code .
   ```

3. When prompted, click "Reopen in Container" or use the command palette (F1) and select "Remote-Containers: Reopen in Container".

4. VS Code will build the Docker image and start the containers. This may take a few minutes the first time.

5. Once the container is running, the project will be fully set up with all dependencies installed and services running.

#### Container Services

The devcontainer includes three services:

1. **Neo4j Database (neo4j)**
   - Accessible at http://localhost:7474 (browser interface)
   - Bolt connection at bolt://localhost:7687
   - Default credentials: neo4j/password (configurable in .env)

2. **Ollama LLM Service (ollama)**
   - Accessible at http://localhost:11434
   - Provides an alternative to Hugging Face for local LLM hosting

3. **Python Application (app)**
   - Main development environment
   - CUDA-enabled for GPU acceleration
   - All Python dependencies pre-installed

#### Manual Setup

If you prefer not to use the devcontainer, you can set up the development environment manually:

1. Clone the repository:
   ```bash
   git clone https://github.com/your-organization/tta.git
   cd tta
   ```

2. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment variables in `.env`:
   ```
   # Neo4j Configuration
   NEO4J_URI=bolt://localhost:7687
   NEO4J_USERNAME=neo4j
   NEO4J_PASSWORD=your_password

   # LLM Configuration
   LLM_API_BASE=http://localhost:1234/v1
   TOOLS_MODEL=qwen2.5-0.5b
   NARRATIVE_MODEL=gemma-3-1b-it
   TOOLS_TEMPERATURE=0.2
   NARRATIVE_TEMPERATURE=0.7
   ```

5. Start Neo4j database

6. Start LM Studio and load the required models:
   - Qwen2.5-0.5b for tool selection (faster, more deterministic)
   - Gemma-3-1b-it for narrative generation (more creative)

## 📂 Project Structure

```
tta/
├── .env                    # Environment variables
├── .gitignore              # Git ignore file
├── README.md               # Project overview
├── Documentation/          # Project documentation
│   ├── Architecture/       # Architecture documentation
│   ├── Development/        # Development guides
│   ├── Guides/             # User guides
│   ├── Integration/        # Integration documentation
│   ├── Models/             # Model documentation
│   ├── PLANNING.md         # Project planning
│   └── TASK.md             # Task tracking
├── src/                    # Source code
│   ├── __init__.py
│   ├── agent_memory.py     # Agent memory system
│   ├── agentic_rag.py      # Agentic RAG implementation
│   ├── dynamic_agents.py   # Dynamic agent system
│   ├── dynamic_game.py     # Game state management
│   ├── dynamic_langgraph.py # LangGraph integration
│   ├── dynamic_tools.py    # Dynamic tool system
│   ├── kg_tools.py         # Knowledge graph utilities
│   ├── langgraph_engine.py # LangGraph engine
│   ├── llm_client.py       # LLM client
│   ├── llm_config_hybrid.py # Hybrid LLM configuration
│   ├── main_dynamic.py     # Main game loop
│   ├── neo4j_manager.py    # Neo4j database integration
│   ├── prompts.py          # System prompts
│   └── tool_selector.py    # Tool selection
├── tests/                  # Test code
│   ├── __init__.py
│   ├── test_agents.py      # Agent tests
│   ├── test_dynamic_tools.py # Dynamic tool tests
│   ├── test_kg_tools.py    # Knowledge graph tests
│   ├── test_langgraph.py   # LangGraph tests
│   └── test_neo4j.py       # Neo4j tests
└── examples/               # Example code
    ├── ai_libraries_demo.py # AI libraries demo
    └── hybrid_model_example.py # Hybrid model example
```

## 🧪 Development Workflow

### 1. Check TASK.md

Before starting work, check `Documentation/TASK.md` for current tasks. If your task isn't listed, add it with a brief description and today's date.

### 2. Create a Feature Branch

Create a branch for your feature or bug fix:

```bash
git checkout -b feature/your-feature-name
```

### 3. Write Tests

Write tests for your feature before implementation:

```bash
# Create a test file
touch tests/test_your_feature.py

# Run tests
python -m pytest tests/test_your_feature.py -v
```

### 4. Implement Your Feature

Implement your feature following the project's coding standards:

- Follow PEP8
- Use type hints
- Format with `black`
- Write docstrings for all functions and classes

### 5. Run Tests

Run the tests to ensure your feature works correctly:

```bash
python -m pytest
```

### 6. Update Documentation

Update the documentation to reflect your changes:

- Update README.md if necessary
- Add or update documentation in the Documentation directory
- Update docstrings in your code

### 7. Commit Your Changes

Commit your changes with a descriptive message:

```bash
git add .
git commit -m "Add feature: your feature description"
```

### 8. Mark Task as Completed

Mark your task as completed in `Documentation/TASK.md`.

## 📝 Coding Standards

### Python Style Guide

- Follow PEP8 guidelines
- Use type hints for all functions and methods
- Format code with `black`
- Maximum line length of 88 characters

### Documentation

- Use Google-style docstrings:
  ```python
  def example_function(param1: str, param2: int) -> bool:
      """
      Brief description of the function.

      Args:
          param1: Description of param1
          param2: Description of param2

      Returns:
          Description of return value
      """
      # Function implementation
  ```

- Add inline comments for complex logic:
  ```python
  # Reason: This complex logic is needed because...
  complex_logic_here()
  ```

### Testing

- Write unit tests for all new features
- Include at least:
  - 1 test for expected use
  - 1 edge case
  - 1 failure case
- Use pytest fixtures for common setup

### File Organization

- Keep files under 500 lines
- Organize code into modules by feature or responsibility
- Use clear, consistent imports (prefer relative imports within packages)

## 🔧 Common Tasks

### Running the Game

```bash
# Traditional approach
python -m src.main

# LangGraph approach
python -m src.main_langgraph

# Dynamic tools with LangGraph approach (recommended)
python -m src.main_dynamic
```

### Running Tests

```bash
# Run all tests
python -m pytest

# Run specific test file
python -m pytest tests/test_specific_file.py

# Run tests with coverage
python -m pytest --cov=src
```

### Updating Dependencies

```bash
# Update requirements.txt
pip freeze > requirements.txt
```

### Working with Neo4j

```bash
# Start Neo4j (if using Docker)
docker-compose up -d neo4j

# Reset the database
python -m src.populate_graph
```

## 🐛 Troubleshooting

### Common Issues

1. **Neo4j Connection Issues**
   - Check that Neo4j is running
   - Verify connection details in `.env`
   - Ensure Neo4j has enough memory
   - Try connecting directly with the Neo4j browser

2. **LLM API Issues**
   - Check that LM Studio is running
   - Verify API base URL in `.env`
   - Ensure models are loaded in LM Studio

3. **Import Errors**
   - Check that you're running from the project root
   - Verify virtual environment is activated
   - Check for missing dependencies

4. **GPU not detected**
   - Ensure NVIDIA drivers are installed
   - Verify NVIDIA Container Toolkit is properly set up
   - Check `nvidia-smi` works on the host

5. **Model loading errors**
   - Check internet connection for downloading models
   - Verify sufficient disk space for model cache
   - Try a smaller model or increase quantization

### Getting Help

If you encounter issues not covered here:

1. Check the project documentation
2. Look for similar issues in the issue tracker
3. Ask for help in the project chat
4. Create a new issue with detailed information

## 🔄 Continuous Integration

The project uses GitHub Actions for continuous integration:

- Linting with flake8
- Type checking with mypy
- Testing with pytest
- Code coverage with pytest-cov

Make sure your code passes all CI checks before submitting a pull request.

## 📚 Additional Resources

- [Python Documentation](https://docs.python.org/3/)
- [Neo4j Documentation](https://neo4j.com/docs/)
- [LangChain Documentation](https://python.langchain.com/docs/get_started/introduction)
- [LangGraph Documentation](https://python.langchain.com/docs/langgraph)
- [Transformers Documentation](https://huggingface.co/docs/transformers/index)


---
**Logseq:** [[TTA.dev/Docs/Development/Development_guide]]
