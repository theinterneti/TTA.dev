Therapeutic Text Adventure (TTA) - Testing Strategy Document

Version: 1.0
Date: 2024-07-26

Purpose: This document defines the comprehensive testing strategy for the Therapeutic Text Adventure (TTA) project. It outlines the various testing levels, methodologies, tools, and processes that will be employed throughout the Software Development Life Cycle (SDLC) to ensure the application meets quality standards, functional requirements, performance benchmarks, and ethical guidelines. This strategy aims to identify and mitigate risks early, ensure system stability, and deliver a high-quality, reliable, and engaging experience for players.

1. Guiding Principles:

Early and Continuous Testing: Integrate testing activities into all phases of the development lifecycle, starting from the initial prototype.

Layered Testing Approach: Employ multiple levels of testing (Unit, Integration, End-to-End, Manual) to target different aspects of the system and catch various types of defects.

Automation Focus: Automate repetitive tests (Unit, Integration, parts of E2E) to ensure consistency, efficiency, and rapid feedback, crucial for a solo developer or small team.

Risk-Based Prioritization: Focus testing efforts on high-risk areas, critical functionalities, complex interactions (AI agents, knowledge graph, state management), and core gameplay loops.

Reproducibility: Design tests to be reproducible, with controlled environments and predictable test data setups.

Ethical Testing: Ensure testing procedures, especially those involving AI generation or simulated player data, adhere to the project's ethical guidelines, avoid generating harmful content, and respect privacy.

Iterative Refinement: Continuously review and refine the testing strategy based on project progress, feedback, and identified issues.

2. Testing Levels:

2.1. Unit Testing:

Purpose: To verify the correctness of individual, isolated components (functions, classes, methods) in the codebase.

Scope: Smallest testable parts of the software (e.g., Pydantic model validation, individual tool functions, helper utilities, specific agent logic modules).

Methodology: White-box testing performed by the developer. Dependencies (LLM APIs, Neo4j database, other agents/modules) will be mocked or stubbed to ensure isolation.

Tools: pytest, unittest.mock (or pytest-mock).

Examples:

Testing a Pydantic model correctly validates input data.

Testing a query_knowledge_graph tool function correctly formats a Cypher query (mocking the actual DB call).

Testing a helper function for calculating distances or parsing specific text formats.

Testing a specific logic branch within an agent's processing function (mocking inputs and dependencies).

2.2. Integration Testing:

Purpose: To verify the interaction and communication between different components or modules of the system.

Scope: Testing interactions between:

AI Agents (e.g., IPA output feeding into NGA).

Agent and Tools (e.g., NGA calling query_knowledge_graph).

Application layer and Neo4j database (testing Cypher query execution and data retrieval/storage).

LangGraph workflow transitions (conditional edges, state updates).

Python code and LLM API (limited, controlled tests or mocked responses).

Methodology: Testing interfaces and data flow between integrated units. May involve a dedicated test Neo4j database instance populated with specific test data. LLM calls may be mocked or directed to a test endpoint if available, or limited actual calls with controlled inputs.

Tools: pytest, test Neo4j database, potentially docker-compose for setting up test environment, mocked LLM responses.

Examples:

Testing that the IPA correctly parses input and the subsequent agent (e.g., NGA) receives the expected structured data via LangGraph state.

Testing that an agent's call to query_knowledge_graph successfully executes against the test Neo4j instance and returns the expected data format.

Testing a LangGraph conditional edge correctly routes the workflow based on mocked agent output.

2.3. End-to-End (E2E) Testing:

Purpose: To validate the complete flow of the application from the user's perspective, simulating real user scenarios.

Scope: Testing entire features or user journeys, involving multiple components interacting together (UI -> IPA -> LangGraph -> Agents -> Tools -> Neo4j -> LLM -> UI).

Methodology: Black-box or gray-box testing. Simulating player commands and verifying the final output and system state changes. Requires a fully integrated environment (test Neo4j DB, connection to LLM). Automation is possible for core scenarios but challenging for complex, AI-driven narratives.

Tools: pytest (for scripting scenarios), potentially UI automation tools if a graphical interface is developed later, manual testing plans.

Examples:

Simulating the full "Genesis Sequence" from player input to universe creation confirmation.

Simulating a player entering a location, examining an object, talking to an NPC, and verifying the text output and state changes in Neo4j.

Testing the core gameplay loop with a sequence of commands ("look", "go north", "examine table", "talk to guard").

2.4. Manual / Exploratory Testing:

Purpose: To uncover issues related to usability, user experience, narrative coherence, edge cases, and unexpected AI behavior that automated tests might miss.

Scope: Ad-hoc testing of the application, exploring different paths, trying unusual inputs, evaluating the "feel" and flow of the game.

Methodology: Performed by the developer (and later, testers) interacting directly with the application. Focuses on creativity, intuition, and exploring the boundaries of the system. Essential for evaluating the subjective quality of the narrative and therapeutic elements.

Tools: The running application, note-taking tools, bug tracking system.

Examples:

Trying intentionally vague or nonsensical commands to see how the IPA and NGA respond.

Following a narrative thread for an extended period to check for consistency and engagement.

Evaluating the subtlety and appropriateness of therapeutic prompts.

Testing the user interface (even command-line) for clarity and ease of use.
3. Testing Tools and Frameworks:

Core Framework: pytest (for unit, integration, and potentially E2E test scripting)

Mocking: unittest.mock or pytest-mock

Code Coverage: pytest-cov

CI/CD: GitHub Actions

Database: Dedicated Neo4j test instance (local or cloud)

Performance: Neo4j Browser (PROFILE/EXPLAIN), Python timeit/cProfile.

Bug Tracking: GitHub Issues

4. Test Case Management:

Format: Tests written using pytest conventions. Test functions should be clearly named (e.g., test_ipa_parses_move_command_correctly). Use Arrange-Act-Assert pattern.

Location: Test files stored in a dedicated tests/ directory, mirroring the main application structure.

Tracking: Test execution results tracked via CI/CD system (GitHub Actions). Bug reports tracked in GitHub Issues.

5. Test Data Management:

Test Database: A separate Neo4j database instance will be used exclusively for testing.

Data Generation: Python scripts will be created and maintained under version control to populate the test database with controlled, representative data (nodes, relationships) needed for specific test scenarios.

Data Reset: Test setup routines (pytest fixtures) will ensure the test database is in a known, clean state before each test run or suite (e.g., deleting existing data and running population scripts).

Anonymization: No production player data will be used for testing. If structures mimic sensitive data (e.g., psychological_profile), ensure test data is synthetic and anonymized.

Versioning: Test data generation scripts will be versioned alongside the application code in Git.

6. Automation Strategy (CI/CD):

Platform: GitHub Actions.

Workflows: Define workflows (.github/workflows/testing.yml) to automate testing.

Triggers: Automatically run unit and integration tests on every push and pull request to main development branches (e.g., main, develop).

Steps:

Checkout code.

Set up Python environment.

Install dependencies (pip install -r requirements.txt).

(Optional) Set up test Neo4j instance (e.g., using Docker within the Action).

Run pytest with coverage reporting.

Upload coverage reports (e.g., to Codecov).

Reporting: Pass/fail status visible directly in GitHub Actions UI and pull requests.

7. Performance Testing:

Metrics:

Latency: LLM API call time, Neo4j query execution time, LangGraph node execution time.

Resource Usage: CPU and Memory utilization (especially for local LLM/DB setup).

Methodology:

Baseline: Measure performance under normal conditions periodically.

Targeted Profiling: Use Neo4j PROFILE/EXPLAIN and Python profiling tools to investigate slow components identified during manual testing or based on complexity.

Focus: Prioritize testing the performance of frequently used agents (IPA, NGA) and complex KG queries (LKA).

---
**Logseq:** [[TTA.dev/_archive/Legacy-tta-game/Testingstrategy]]
