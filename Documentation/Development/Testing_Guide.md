# Testing Strategy

This document outlines the testing strategy for the Therapeutic Text Adventure (TTA) project. Thorough testing is crucial for ensuring the quality, reliability, and stability of the game. We employ a multi-layered approach, including:

* **Unit Tests:** Testing individual functions and classes in isolation.
* **Integration Tests:** Testing the interactions between different components (e.g., AI agents, the knowledge graph).
* **End-to-End Tests:** Testing complete game scenarios from the player's perspective.
* **User Testing:** Gathering feedback from real players.

## Testing Framework

We use the `unittest` framework for structuring and running tests. Tests are located in the `tta/tests` directory.

## Running Tests

To run all tests:

```bash
python -m unittest discover tta/tests
```

To run tests for a specific module (e.g., ipa.py):

```bash
python -m unittest tta/tests/test_ipa.py
```

## Test Organization

* Each module should have a corresponding test file (e.g., ipa.py has test_ipa.py).
* Test files should contain test classes (e.g., TestIPA) that inherit from unittest.TestCase.
* Each test method within a test class should focus on testing a specific aspect of the code.
* Test method names should be descriptive and start with test_ (e.g., test_parse_move_command, test_create_character).
* Use the setup and teardown methods to create a consistent environment.

## Types of Tests

### Unit Tests

Unit tests focus on testing individual functions and classes in isolation. They verify that each unit of code behaves as expected, given specific inputs and conditions. Examples:

* Testing the process_input function in ipa.py with various player inputs.
* Testing the create_node and get_node_by_id functions in neo4j_utils.py with different node types and properties.
* Testing individual methods of an AI agent class.

### Integration Tests

Integration tests verify that different components of the system work together correctly. Examples:

* Testing the interaction between the IPA and the NGA.
* Testing that an AI agent can correctly query and update the Neo4j knowledge graph.
* Testing that a LangGraph workflow executes as expected.

### End-to-End Tests

End-to-end tests simulate complete game scenarios from the player's perspective. They verify that the entire system works together to create the intended gameplay experience. Examples:

* Testing a complete character creation sequence.
* Testing a simple exploration scenario (e.g., moving between locations, examining objects).
* Testing a conversation with an NPC.
* Testing a combat encounter.

### User Testing

User testing involves gathering feedback from real players. This is crucial for identifying usability issues, gameplay imbalances, and areas for improvement.

## Test Coverage

We strive for high test coverage, meaning that a large percentage of the codebase is executed during testing. Tools like coverage.py can be used to measure test coverage and identify areas that need more testing.

## Continuous Integration (Future)

We plan to implement continuous integration (CI) to automatically run tests whenever code is pushed to the repository. This will help ensure that new changes don't introduce regressions.

## Writing Good Tests

* **Test-Driven Development (TDD):** Consider writing tests before writing the code. This helps clarify requirements and ensures that the code is testable.
* **Keep Tests Small and Focused:** Each test should focus on a specific aspect of the code.
* **Use Descriptive Names:** Test names should clearly indicate what is being tested.
* **Use Assertions:** Use assertion methods (e.g., assertEqual, assertTrue, assertRaises) to verify that the code behaves as expected.
* **Handle Edge Cases:** Test with a variety of inputs, including edge cases and invalid inputs.
* **Isolate Tests:** Tests should be independent of each other. One test should not affect the outcome of another test.
* **Mock External Dependencies (When Appropriate):** For unit tests, consider using mocking to isolate the code being tested from external dependencies (e.g., the Neo4j database). However, for integration tests, you should test the actual interaction with external systems.
* **Don't Over-Mock:** Avoid excessive mocking, as it can make tests brittle and less representative of real-world behavior.
* **Test for Errors:** Ensure that your code handles errors gracefully, and write tests to verify this.

This comprehensive testing strategy will help ensure the quality and reliability of the TTA project.
