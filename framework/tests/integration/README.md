# MCP Integration Tests

This directory contains integration tests for the MCP servers.

## Overview

The integration tests verify that the MCP servers can be started and used correctly. They test:

1. Importing the MCP servers
2. Starting the MCP servers
3. Connecting to the MCP servers
4. Sending requests to the MCP servers
5. Receiving responses from the MCP servers

## Running the Tests

### Basic Import Test

To run a basic test that verifies the MCP servers can be imported:

```bash
python3 tests/integration/test_mcp_imports.py
```

### Server Instantiation Test

To run a test that verifies the MCP servers can be instantiated:

```bash
python3 tests/integration/test_mcp_server_instantiation.py
```

### Simple MCP Test

To run a simple test that starts the MCP servers and connects to them:

```bash
python3 tests/integration/simple_mcp_test.py
```

### Full Integration Tests

To run the full integration tests:

```bash
python3 tests/integration/run_integration_tests.py
```

You can also run the tests with verbose output:

```bash
python3 tests/integration/run_integration_tests.py --verbose
```

Or run specific tests:

```bash
python3 tests/integration/run_integration_tests.py --test servers
python3 tests/integration/run_integration_tests.py --test assistant
```

## Test Files

- `test_mcp_imports.py`: Tests that the MCP servers can be imported
- `test_mcp_server_instantiation.py`: Tests that the MCP servers can be instantiated
- `simple_mcp_test.py`: Simple test that starts the MCP servers and connects to them
- `test_mcp_servers.py`: Tests for the MCP servers
- `test_ai_assistant_integration.py`: Tests for the AI assistant integration with the MCP servers
- `run_integration_tests.py`: Script to run the integration tests
- `run_mcp_servers.py`: Script to run the MCP servers manually

## Notes

- The tests require the FastMCP package to be installed
- The tests use the example MCP servers in the `examples/mcp` directory
- The tests start the servers on ports 8001 and 8002 by default

## Known Issues

- The server connection tests may fail due to timeouts when running the servers in a subprocess
- The server instantiation tests work correctly, confirming that the MCP servers can be imported and instantiated
- For full integration testing, it's recommended to run the servers manually in separate terminals

## Running Servers Manually

To run the servers manually for testing, use the `run_mcp_servers.py` script:

```bash
# Run the Knowledge Resource server
python3 tests/integration/run_mcp_servers.py --server knowledge

# Run the Agent Tool server
python3 tests/integration/run_mcp_servers.py --server agent

# Run both servers (in separate terminals)
python3 tests/integration/run_mcp_servers.py --server knowledge
python3 tests/integration/run_mcp_servers.py --server agent
```

You can also specify the port and transport:

```bash
python3 tests/integration/run_mcp_servers.py --server knowledge --port 8002 --transport sse
```
