**Therapeutic Text Adventure (TTA) - Coding Standards**

**1. Programming Language: Python**

Python is our chosen programming language due to its extensive libraries for AI, NLP, data manipulation, and graph database interaction, as well as its readability and rapid prototyping capabilities.

*   **Adherence to PEP 8:** All Python code must adhere to PEP 8, the style guide for Python code. This includes conventions for naming, indentation (4 spaces), line length (typically 79 characters), whitespace, comments, and overall code layout. Consistency in style improves readability and maintainability. **Tools like `flake8` or `pylint` should be used to automatically enforce PEP 8 compliance.**
*   **Meaningful Naming:** Variables, functions, classes, and modules should be named descriptively and consistently to clearly indicate their purpose. Avoid single-letter variable names (except for very short-lived loop counters) and use names that reflect the data they hold or the action they perform. **Names should be chosen to clearly indicate the role and responsibility within the agent architecture.**  When choosing names, think about *who* or *what* is using this variable/function/class. For example, instead of `process_data()`, maybe `process_player_input()` or `analyze_dialogue_context()`.
*   **Type Hinting:** We will extensively use Python type hints as defined in PEP 484 and subsequent related PEPs. Type hints improve code readability, help catch type-related errors during development (with tools like MyPy), and make the codebase easier for both humans and AI to understand and work with. Type hints will be used for function and method signatures, as well as variable annotations where clarity is enhanced. **Pydantic models, used extensively for data validation and schemas, rely heavily on type hints, so their consistent use is crucial.** We'll use `mypy` to *actively check* type hints.
*   **Docstrings:** All modules, classes, functions, and methods must have comprehensive docstrings that follow a consistent format (e.g., NumPy or Google style). Docstrings should explain the purpose of the component, its parameters (including types and descriptions), what it returns, and any exceptions it might raise. This documentation is crucial for understanding the codebase and can be used by documentation generation tools. **Docstrings are especially important for tools and agent logic, clearly defining their inputs, outputs, and intended behavior for other developers and for the LLM itself to understand.** Docstrings should not just describe *what* something does, but ideally *show* a quick example of *how* to use it. For functions, a simple example in the docstring demonstrating input and output is very helpful for understanding.
*   **Modularity and Reusability:** We will design our code with a strong emphasis on modularity. Functions and classes should perform single, well-defined tasks, making them easier to test, debug, and reuse across different parts of the project. This aligns with our modular design principle for the overall game architecture. **This is particularly important for tools, which are designed to be reusable across different agents and workflows.**
*   **Efficiency:** While prioritizing readability and clarity, we will also strive for efficient code, especially in performance-critical areas such as knowledge graph interactions and AI agent logic. This may involve choosing appropriate data structures and algorithms. **Performance optimization should be considered especially for Cypher queries and LLM interactions to minimize latency.** Focus on writing clear and readable code *first*. Optimize for efficiency *later*, only if you notice performance problems (like the game running slowly).
*   **Error Handling:** Robust error handling mechanisms (using `try...except` blocks) will be implemented to gracefully manage potential issues and prevent unexpected crashes. Informative error messages should be logged or returned to aid in debugging. **Error handling is crucial within tool implementations and agent logic to ensure system stability.  Structured error responses (e.g., JSON with "success" and "message" fields) are preferred for tool outputs to facilitate automated error handling in workflows.**
*   **Logging:** We will utilize Python's logging module to record important events, errors, and debugging information during the execution of the game. Proper logging helps in understanding the system's behavior and diagnosing issues. **Detailed logging, including agent roles, inputs, outputs, and tool calls, is essential for debugging complex AI agent workflows and monitoring system behavior.** Python's logging has different levels (like DEBUG, INFO, WARNING, ERROR, CRITICAL).  Use DEBUG for detailed info during development, INFO for general operation messages, WARNING for potential issues, and ERROR/CRITICAL for failures.

**2. Knowledge Graph Interaction (Neo4j and Cypher)**

Interactions with the Neo4j graph database will be a core part of TTA.

*   **Clear and Concise Cypher:** Cypher queries will be written to be clear, concise, and well-documented. The purpose of each query should be easily understandable. **Cypher queries should be optimized for performance, considering indexing and avoiding inefficient clauses like `UNWIND` where possible.  Use `PROFILE` or `EXPLAIN` to analyze query performance.**
*   **Parameterized Queries:** All Cypher queries executed from Python code must use parameterized queries to prevent Cypher injection vulnerabilities and improve query efficiency. **Always use parameterized queries and avoid string concatenation for building Cypher queries.** When using Python to query Neo4j, an example of a parameterized query is:  `query = "MATCH (n:Character {name: $name}) RETURN n";  parameters = {"name": player_name};  results = tx.run(query, parameters)` .
*   **Strategic Labeling and Relationship Definition:** We will strategically use labels for nodes and define relationships clearly with descriptive types and properties to ensure an organized and efficient knowledge graph. **Follow consistent naming conventions: CamelCase for Node Labels (e.g., `Character`, `Location`), UPPER_CASE_WITH_UNDERSCORES for Relationship Types (e.g., `LOCATED_IN`, `HAS_ITEM`), and snake_case for Properties (e.g., `character_name`, `location_description`).** Think about broad categories for node labels (e.g., `Player`, `Location`, `Character`, `Item`, `Dialogue`).  Relationship types should be descriptive verbs (e.g., `LOCATED_IN`, `HAS_ITEM`, `SPEAKS_TO`).
*   **Cypher Style Guide:** We will develop a Cypher style guide to ensure consistency in query formatting and structure. **The Cypher style guide should include examples and cover aspects like keyword capitalization (`MATCH`, `CREATE`, `RETURN` in UPPERCASE), indentation, and the use of backticks for identifiers when needed.** For instance,  'Use UPPERCASE for Cypher keywords (MATCH, CREATE, RETURN), lowercase for node labels and relationship types.  Indent clauses for readability.'

**3. AI Agent Implementation (LangChain and LangGraph)**

Our AI agents will be built and orchestrated using LangChain and LangGraph.

*   **Modular Agent Design:** Agent logic will be encapsulated within well-defined classes or functions, adhering to the principles of modularity. **Agent roles (IPA, NGA, LKA, etc.) should be implemented as distinct modules, promoting code organization and reusability.**
*   **Clear Agent Roles and Responsibilities:** Each AI agent will have clearly defined roles and responsibilities, reflected in their code and documentation. **Agent roles should be clearly documented, specifying their purpose, inputs, outputs, and interactions with other agents and tools.  Document these roles in the Developer Wiki.** For each AI agent, create a short document or section in the developer wiki that clearly states its role, responsibilities, inputs, outputs, and any specific logic it uses. This 'agent profile' helps everyone understand what each agent is supposed to do.
*   **Consistent Use of Prompt Templates:** LangChain's `PromptTemplate` will be used to create reusable and manageable prompts for our LLM. Prompts should be well-documented and version-controlled. **Prompt templates should follow a consistent structure, including sections for Metaconcepts, Agent Role/Task, Context, Available Tools, and Output Format. Store prompt templates in separate files (e.g., `prompts/agent_dialogue.txt`) for better management and version control. Treat prompt files like code.**
*   **Structured Input and Output for Tools:** Tools used by AI agents will have clearly defined input and output schemas, often using Pydantic models, to ensure seamless data exchange. **All tools must use Pydantic models to define their input and output schemas. This ensures data validation, clear documentation, and type safety.  Provide clear descriptions in Pydantic models for LLM understanding.** Provide simple Pydantic model examples for tool input/output. For example:

    ```python
    from pydantic import BaseModel

    class ToolInput(BaseModel):
        action_type: str
        target_object: str

    class ToolOutput(BaseModel):
        result_message: str
        success: bool
    ```
*   **LangGraph Workflow Definition:** LangGraph workflows will be defined clearly, visualizing the sequence of agent interactions, decision points, and state transitions. **LangGraph workflows should be defined using `StateGraph` and its associated methods for nodes and edges.  Conditional logic for workflow transitions should be implemented using Python functions that evaluate the `AgentState`. Consider visual diagrams for complex workflows. For complex LangGraph workflows, consider creating simple diagrams (even hand-drawn or using online tools) to visualize the steps and agent interactions.**
*   **State Management:** We will leverage LangGraph's state management capabilities to maintain the game state and facilitate communication between agents. Pydantic models will be used to represent the `AgentState` and ensure data integrity. **The `AgentState` should be a comprehensive Pydantic model encompassing all relevant game information (player input, parsed input, game world state, character states, conversation history, metaconcepts, memory, prompt chain, response).  Ensure strong typing and validation are enforced by Pydantic.**

**4. Version Control (Git)**

Git will be our primary version control system.

*   **Feature Branching:** We will use separate branches for feature development and bug fixes.
*   **Atomic Commits:** Each commit should be atomic and focused on a single logical change. Commit messages should be clear, concise, and follow conventional commit message formats, explaining the "why" behind the change, not just the "what". Before committing, ask yourself: 'Does this commit address a single, logical change? Is the commit message clear and explain *why* I made this change?  Does it build on previous commits in a sensible way?'
*   **Meaningful Branch Names:** Branch names should be descriptive and indicate the feature or bug fix they address. **Use prefixes like `feature/`, `bugfix/`, `refactor/` for branch names to clearly categorize them.** Branch names should be like `feature/add-player-inventory`, `bugfix/dialogue-typo`, `refactor/knowledge-graph-schema`.
*   **Regular Committing:** Commit changes frequently to maintain a detailed history and facilitate easier rollback if needed. Commit changes at least once a day, or more frequently when you complete a logical unit of work (e.g., finishing a function, implementing a feature component).  Think of committing as saving your progress regularly.
*   **Version Control Configuration:** **Ensure the `.devcontainer` folder and `docker-compose.yml` are included in version control to maintain a consistent development environment configuration across all development setups.**
*   **Prompt Template Versioning:** **Treat prompt template files as code and ensure they are under version control. Track changes to prompts as carefully as code changes.**

**5. Documentation**

Comprehensive documentation is crucial for the long-term maintainability and understanding of the project.

*   **Design Documents:** We will maintain up-to-date design documents outlining the system architecture, AI agent design, knowledge graph schema, and other key aspects of the project. Design documents should be 'living documents' - updated as the project evolves.  Review and update them regularly to reflect the current system architecture and design decisions.
*   **Code Comments:** In-code comments will be used judiciously to explain complex logic or non-obvious sections of the code. Comments should be concise and focused. Docstrings are preferred for documenting interfaces and functionality.
*   **Developer Wiki:** A developer wiki or similar platform will be used to store and share technical information, design decisions, and best practices. **The Developer Wiki will be hosted using `wikimd` and automatically generated from Markdown files in the `Documentation` folder. It will be accessible via `http://localhost:8080` when the Devcontainer is running.** Organize the developer wiki with clear sections like 'Setup Guide', 'Architecture Overview', 'Agent Design', 'Knowledge Graph Schema', 'Coding Standards', 'Troubleshooting', 'Deployment'.
*   **Tool Documentation:** **Document each tool thoroughly, including its purpose, input/output schemas (Pydantic models), example usage, and any error handling considerations. Include this documentation in the Developer Wiki.**
*   **Agent Role Documentation:** **For each agent role (IPA, NGA, LKA, etc.), create a dedicated page in the Developer Wiki outlining its responsibilities, inputs, outputs, workflows, and any specific prompting strategies used.**
*   **Prompt Template Documentation:** **For each key prompt template, document its purpose, input variables, structure, and any important considerations.  Include examples in the Developer Wiki.**
*   **Knowledge Graph Schema Documentation:** **Maintain up-to-date documentation of the knowledge graph schema in the Developer Wiki, including node labels, relationship types, properties, and naming conventions. Visual diagrams of the knowledge graph can be very helpful.**

**6. Ethical Considerations**

Given the therapeutic nature of TTA, ethical considerations are paramount.

*   **Bias Mitigation:** We will actively work to mitigate harmful stereotypes and biases in our AI agents and generated content. This will influence prompt design, data curation for potential fine-tuning, and content review processes. **Implement specific bias mitigation techniques like 'Diverse Prompt Design' (try different phrasing to avoid reinforcing stereotypes), 'Output Review' (manually review agent outputs for biases, especially initially), and 'Data Awareness' (if fine-tuning, be mindful of biases in training data). Continuously monitor and audit AI-generated content for biases. Ethical considerations are an ongoing process.**
*   **Privacy:** We are committed to protecting player privacy and handling data responsibly. Data collection will be minimized, and anonymization/pseudonymization will be used whenever possible. **Adhere to the principle of data minimization.  Ensure player data is stored locally by default.  Implement robust anonymization and pseudonymization for any data shared centrally. Obtain explicit and granular consent for data collection and sharing.**
*   **Therapeutic Responsibility:** We will clearly communicate that TTA is not a replacement for professional therapy. AI agents will be guided by metaconcepts to avoid giving direct therapeutic advice. **Include a clear disclaimer within the game (perhaps in the introduction or 'about' section) stating that TTA is *not* a substitute for professional therapy and is for entertainment/exploration purposes only.  Reinforce this message throughout player onboarding and potentially at key moments in the game. TTA is for entertainment/exploration purposes only.**
*   **Transparency:** We aim to be transparent with players about the game's mechanics, AI involvement, and data practices. **Provide clear information to players about how AI agents work, how data is used (or not used), and the game's limitations regarding therapeutic outcomes.  Make the privacy policy and terms of service easily accessible.**

**7. Testing**

While being a solo developer, thorough testing is still crucial to ensure the quality and stability of TTA.

*   **Unit Tests:** We will write unit tests to verify the functionality of individual modules, functions, and classes. **Use a testing framework like `pytest` for Python unit tests. Focus unit tests on core logic, tools, and data validation functions.** For Python unit tests, use the built-in `unittest` framework or the more user-friendly `pytest`.
*   **Integration Tests:** Integration tests will be used to ensure that different components of the system (e.g., AI agents interacting with the knowledge graph) work together correctly. **Focus integration tests on key interactions between agents and tools, and between agents and the knowledge graph.  Verify data flow and workflow execution across different components.** Focus integration tests on key interactions, like:  'AI agent correctly retrieves information from the knowledge graph', 'Player input is correctly processed by the game logic', 'Game state is updated correctly after agent actions'. Test the 'joints' of your system.
*   **Manual Testing:** Regular manual testing will be performed to evaluate gameplay, narrative flow, and the overall player experience. **Create structured manual testing scenarios and checklists to guide manual testing efforts. Focus on gameplay flow, narrative coherence, and player experience from different perspectives.** For manual testing, create checklists or scenarios to guide your testing.  Examples: 'Play through the first chapter and check for dialogue flow', 'Try different player choices and see if agents respond appropriately', 'Test edge cases like invalid inputs'.
*   **Simulation Runs:** We will conduct simulation runs to observe AI agent behavior and game dynamics under various conditions. **Use simulation runs to observe agent behavior in different game states and scenarios.  This can help identify emergent issues and refine agent logic and prompts.**

**8. Development Environment Setup**

To ensure everyone works in a consistent and easily reproducible environment, and to simplify setup, we will use a Devcontainer and supplementary Docker images.

*   **Devcontainer (for Consistent Development Environment):**
    *   **What it is:** A Devcontainer is essentially a pre-configured Docker container that acts as your development environment. It includes all the necessary tools, libraries, and settings to work on the TTA project. Think of it as a lightweight virtual machine specifically tailored for coding, but much easier to set up and manage.
    *   **Benefits:**
        *   **Consistency:**  Everyone on the project (even if it's just you now!) works in *exactly* the same environment, eliminating "it works on my machine" issues caused by different operating systems or software versions.
        *   **Simplified Setup:**  Setting up your development environment becomes incredibly easy.  You don't need to manually install Python, Neo4j drivers, AI libraries, etc., on your computer.  The Devcontainer handles all of this.
        *   **Isolation:** Your project environment is isolated from your main computer's system.  This prevents conflicts with other software or projects you might have.
    *   **How to Use:**
        *   We will provide a `.devcontainer` folder in the project's Git repository.  This folder contains configuration files that tell tools like VS Code (or other compatible editors) how to build and run the Devcontainer.
        *   Using VS Code (recommended), you simply need to open the TTA project folder. VS Code will detect the `.devcontainer` configuration and prompt you to "Reopen in Container".  Clicking this button will automatically build and start the Devcontainer.
        *   Once the Devcontainer is running, your VS Code will be connected to it.  Any code you write, run, or debug will happen *inside* the container, using the environment defined within it.
        *   *For someone non-technical:* Imagine having a dedicated "coding box" that is perfectly set up for TTA. The Devcontainer *is* that "coding box", and VS Code lets you work inside it seamlessly.

*   **Supplementary Docker Images (for Key Services):**
    *   **Neo4j:**  We will use an official Neo4j Docker image to run our knowledge graph database. This means you don't need to install Neo4j directly on your computer. The Devcontainer will be configured to easily connect to this Neo4j Docker container.
    *   **transformers-pytorch-gpu (for AI Models - if GPU is available):**  For development involving AI models, we will use a Docker image pre-configured with `transformers`, `PyTorch`, and GPU support (if your computer has a compatible NVIDIA GPU). This image ensures you have the correct versions of these libraries and simplifies GPU setup for AI development. If you don't have a GPU, a CPU-based image can be used, or the GPU image will simply utilize the CPU.
    *   **wikimd (for Developer Wiki):**  We will use a `wikimd` Docker image to serve our Documentation folder as a developer wiki. This image is a lightweight web server specifically designed to display Markdown files as a wiki.
    *   **Benefits of Supplementary Docker Images:**
        *   **Simplified Service Setup:**  Running Neo4j and the wiki (and potentially AI model environments) becomes as simple as starting Docker containers. No need for complex installations or configurations.
        *   **Version Control for Services:** Docker images ensure we are all using the same versions of Neo4j, wikimd, and AI library environments, reducing compatibility issues.
        *   **Clean Separation:**  These services run in their own isolated containers, keeping your main development environment clean and focused on the project code.
    *   **How to Use:**
        *   The `.devcontainer/docker-compose.yml` file (within the Devcontainer configuration) will define these supplementary Docker services (Neo4j, wikimd, transformers-pytorch-gpu).
        *   When you start the Devcontainer (using VS Code's "Reopen in Container"), Docker Compose will automatically start these supplementary containers as well.
        *   The Devcontainer will be configured to communicate with these services (e.g., Python code connecting to Neo4j running in its Docker container, wikimd serving the documentation).
        *   *For someone non-technical:*  Think of these Docker images as pre-packaged "appliances" for Neo4j, the wiki, and AI tools.  The Devcontainer setup makes it easy to plug in these "appliances" and use them without manual setup.

*   **Accessing the Developer Wiki (via wikimd):**
    *   Once the Devcontainer and supplementary Docker containers are running, the developer wiki will be accessible through your web browser.
    *   The URL will typically be `http://localhost:8080` (or another port specified in the `docker-compose.yml` file).
    *   This will display the Markdown files within your `Documentation` folder as a nicely formatted, searchable wiki.
    *   You can edit the Markdown files in the `Documentation` folder using VS Code within the Devcontainer, and the wiki will automatically update.
    *   This provides a central, easily accessible, and automatically updated location for all project documentation, design documents, and coding standards.

**9. Model Updates and Fine-Tuning**

To continuously improve the quality and capabilities of TTA, we will implement a strategy for model updates and fine-tuning.

*   **Regular Model Evaluation:**  We will regularly evaluate the performance of Qwen2.5 and consider integrating newer, more powerful LLMs as they become available. Evaluation will include benchmark tasks and TTA-specific tasks, assessing text quality, reasoning ability, and ethical considerations.
*   **Fine-tuning on TTA Data:** Qwen2.5 will be fine-tuned on TTA-specific datasets to optimize its performance for game-related tasks. Datasets will include high-quality examples of narrative content, character interactions, and knowledge graph data. Techniques like Reinforcement Learning and Rejection Sampling will be explored to enhance fine-tuning.
*   **Prompt Engineering Iteration:** Prompt engineering is an ongoing process. We will continuously experiment with and refine prompts to improve agent behavior, content quality, and adherence to metaconcepts. Prompt templates will be version-controlled, and changes will be carefully documented.
*   **Decoding Strategy Optimization:** We will explore and optimize different decoding strategies (e.g., temperature sampling, top-k sampling, beam search) to balance creativity, coherence, and computational cost of text generation. Dynamic adjustment of decoding parameters based on context will be considered.

By consistently adhering to these coding practices and standards, we will build a robust, maintainable, and ethically sound foundation for the Therapeutic Text Adventure project. These guidelines will evolve as the project progresses and we gain new insights.


---
**Logseq:** [[TTA.dev/Docs/Development/Codingstandards]]
