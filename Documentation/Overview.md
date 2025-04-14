# Therapeutic Text Adventure (TTA)

Welcome to the documentation for the Therapeutic Text Adventure (TTA) project!

TTA is an AI-driven text adventure game designed to provide a personalized and potentially therapeutic experience for players. The game leverages a knowledge graph, large language models (LLMs), and a robust agent architecture to create a dynamic and engaging world.

This documentation provides a comprehensive overview of the project, including:

* **Architecture:** An overview of the system's design and key components. See [System Architecture](./Architecture/System_Architecture.md).
* **AI Agents:** Detailed descriptions of the AI agents and their roles. See [AI Agents](./Architecture/AI_Agents.md).
* **Knowledge Graph:** The schema and conventions for the Neo4j knowledge graph. See [Knowledge Graph](./Architecture/Knowledge_Graph.md).
* **Dynamic Tool System:** Information about the dynamic tool system. See [Dynamic Tool System](./Architecture/Dynamic_Tool_System.md).
* **Models:** Documentation about the AI models used in the project. See [Models Guide](./Models/Models_Guide.md).

## Getting Started

To get started with TTA development, you'll need to:

1. **Set up the development environment:** See the [Docker Guide](./Development/Docker_Guide.md) for instructions on setting up Docker and the development environment.
2. **Install the required dependencies:** Use Poetry to install the project's dependencies (see `pyproject.toml` and the [Docker Guide](./Development/Docker_Guide.md)).
3. **Configure the environment variables:** Create a `.env` file and set the necessary environment variables. See the [Environment Variables Guide](./Development/Environment_Variables_Guide.md) for details.
4. **Run the game:** Execute the `main.py` script to start the game. See the [Deployment Guide](./Development/Deployment_Guide.md) for more information.

## Contributing

Contributions to the TTA project are welcome! Please see the `CONTRIBUTING.md` file (not yet created) for guidelines on how to contribute.

## License

This project is licensed under the MIT License - see the `LICENSE` file (not yet created) for details.

## Technology Stack

* **Neo4j:** Graph database for storing the knowledge graph. See [Knowledge Graph](./Architecture/Knowledge_Graph.md).
* **Python:** Primary programming language.
* **LangChain:** Framework for building LLM applications. See [AI Libraries Integration Plan](./Integration/AI_Libraries_Integration_Plan.md).
* **LangGraph:** Framework for orchestrating AI agent workflows. See [AI Libraries Integration Plan](./Integration/AI_Libraries_Integration_Plan.md#4-langgraph).
* **Qwen2.5:** Large Language Model (hosted locally using LM Studio). See [Models Guide](./Models/Models_Guide.md).
* **Pydantic:** Data validation and schema definition.
* **Guidance:** Library for controlling LLM output. See [AI Libraries Integration Plan](./Integration/AI_Libraries_Integration_Plan.md#2-guidance).
* **spaCy:** Natural Language Processing library.
* **TensorFlow:** Machine Learning library.
* **FastAPI:** (Potentially) For creating a web interface.

## Installation

1. **Clone the repository:**
   ```bash
   git clone <repository_url>
   cd <repository_directory>
   ```

2. **Set up the development environment:**
   * It is highly recommended to use Docker for development. See the [Docker Guide](./Development/Docker_Guide.md) for detailed instructions.
   * If you are *not* using Docker, you will need to manually install the dependencies using Poetry:
     ```bash
     poetry install
     ```

3. **Configure environment variables:**
   * Create a `.env` file in the project root.
   * Add the necessary environment variables. See the [Environment Variables Guide](./Development/Environment_Variables_Guide.md) for a complete list of required and optional variables.
   * **Important:** The `.env` file should *never* be committed to version control. It contains sensitive information (like API keys).

4. **Run the game:**
   ```bash
   # Using Docker
   docker-compose up -d
   docker-compose exec app python -m src.main

   # Using Poetry directly
   poetry run python -m src.main
   ```

   See the [Deployment Guide](./Development/Deployment_Guide.md) for more detailed instructions on running the application in different environments.
