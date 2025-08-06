#!/usr/bin/env python3
"""
Simple test for MCP servers.

This script tests the MCP servers by starting them and sending a simple request.
"""

import sys
import os
import subprocess
import time
import requests

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Add the examples directory to the Python path
examples_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'examples')
sys.path.append(examples_path)

# Test constants
KNOWLEDGE_SERVER_PORT = 8002
AGENT_TOOL_SERVER_PORT = 8001

def start_knowledge_server():
    """Start the Knowledge Resource server."""
    print("Starting Knowledge Resource server...")

    # Create a script file to run the server
    script_path = os.path.join(os.getcwd(), "run_knowledge_server.py")
    with open(script_path, "w") as f:
        f.write(f"""
#!/usr/bin/env python3
import sys
sys.path.append('{examples_path}')
from examples.mcp.knowledge_resource_server import mcp
print('Server object created')
mcp.settings.port = {KNOWLEDGE_SERVER_PORT}
print(f'Port set to {KNOWLEDGE_SERVER_PORT}')
print('Starting server...')
mcp.run('sse')
""")

    # Make the script executable
    os.chmod(script_path, 0o755)

    # Run the script
    print(f"Running script: {script_path}")
    process = subprocess.Popen(
        ["python3", script_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    # Wait for the server to be ready by polling the endpoint
    print("Waiting for server to start...")
    start_time = time.time()
    timeout = 15  # seconds
    while True:
        try:
            response = requests.get(f"http://localhost:{KNOWLEDGE_SERVER_PORT}/sse", timeout=1)
            if response.status_code == 200:
                print("Server is ready!")
                break
        except Exception:
            pass
        if time.time() - start_time > timeout:
            print("Server did not start within timeout period.")
            break
        time.sleep(0.5)

    # Check if the process is still running
    if process.poll() is not None:
        print(f"Server process exited with code {process.returncode}")
        stdout, stderr = process.communicate()
        print(f"Server stdout: {stdout}")
        print(f"Server stderr: {stderr}")
        return None

    return process

def start_agent_tool_server():
    """Start the Agent Tool server."""
    print("Starting Agent Tool server...")

    # Create a script file to run the server
    script_path = os.path.join(os.getcwd(), "run_agent_tool_server.py")
    with open(script_path, "w") as f:
        f.write(f"""
#!/usr/bin/env python3
import sys
sys.path.append('{examples_path}')
from examples.mcp.agent_tool_server import mcp
print('Server object created')
mcp.settings.port = {AGENT_TOOL_SERVER_PORT}
print(f'Port set to {AGENT_TOOL_SERVER_PORT}')
print('Starting server...')
mcp.run('sse')
""")

    # Make the script executable
    os.chmod(script_path, 0o755)

    # Run the script
    print(f"Running script: {script_path}")
    process = subprocess.Popen(
        ["python3", script_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    # Give the server a moment to start
    print("Waiting for server to start...")
    time.sleep(5)  # Increased wait time

    # Check if the process is still running
    if process.poll() is not None:
        print(f"Server process exited with code {process.returncode}")
        stdout, stderr = process.communicate()
        print(f"Server stdout: {stdout}")
        print(f"Server stderr: {stderr}")
        return None

    return process

def test_knowledge_server():
    """Test the Knowledge Resource server."""
    script_path = os.path.join(os.getcwd(), "run_knowledge_server.py")

    try:
        # Start the server
        process = start_knowledge_server()

        # If the server failed to start, return False
        if process is None:
            return False

        try:
            # Test the server
            print("Testing Knowledge Resource server...")
            try:
                print(f"Connecting to http://localhost:{KNOWLEDGE_SERVER_PORT}/sse")
                response = requests.get(f"http://localhost:{KNOWLEDGE_SERVER_PORT}/sse", timeout=10)  # Increased timeout

                if response.status_code == 200:
                    print("Knowledge Resource server is running!")
                    return True
                else:
                    print(f"Knowledge Resource server returned status code {response.status_code}")
                    return False
            except requests.exceptions.ConnectionError as e:
                print(f"Could not connect to Knowledge Resource server: {e}")
                return False
            except requests.exceptions.Timeout:
                print("Connection to Knowledge Resource server timed out")
                return False
        finally:
            # Print any server output
            try:
                stdout, stderr = process.communicate(timeout=0.1)
                print(f"Server stdout: {stdout}")
                print(f"Server stderr: {stderr}")
            except subprocess.TimeoutExpired:
                # Server is still running, which is expected
                print("Server is still running (as expected)")

            # Kill the server
            print("Terminating server...")
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                print("Server did not terminate, killing it...")
                process.kill()
                process.wait()
    finally:
        # Clean up the script file
        if os.path.exists(script_path):
            print(f"Removing script file: {script_path}")
            os.remove(script_path)

def test_agent_tool_server():
    """Test the Agent Tool server."""
    script_path = os.path.join(os.getcwd(), "run_agent_tool_server.py")

    try:
        # Start the server
        process = start_agent_tool_server()

        # If the server failed to start, return False
        if process is None:
            return False

        try:
            # Test the server
            print("Testing Agent Tool server...")
            try:
                print(f"Connecting to http://localhost:{AGENT_TOOL_SERVER_PORT}/sse")
                response = requests.get(f"http://localhost:{AGENT_TOOL_SERVER_PORT}/sse", timeout=10)  # Increased timeout

                if response.status_code == 200:
                    print("Agent Tool server is running!")
                    return True
                else:
                    print(f"Agent Tool server returned status code {response.status_code}")
                    return False
            except requests.exceptions.ConnectionError as e:
                print(f"Could not connect to Agent Tool server: {e}")
                return False
            except requests.exceptions.Timeout:
                print("Connection to Agent Tool server timed out")
                return False
        finally:
            # Print any server output
            try:
                stdout, stderr = process.communicate(timeout=0.1)
                print(f"Server stdout: {stdout}")
                print(f"Server stderr: {stderr}")
            except subprocess.TimeoutExpired:
                # Server is still running, which is expected
                print("Server is still running (as expected)")

            # Kill the server
            print("Terminating server...")
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                print("Server did not terminate, killing it...")
                process.kill()
                process.wait()
    finally:
        # Clean up the script file
        if os.path.exists(script_path):
            print(f"Removing script file: {script_path}")
            os.remove(script_path)

def main():
    """Main entry point."""
    # Test the Knowledge Resource server
    knowledge_server_success = test_knowledge_server()

    # Test the Agent Tool server
    agent_tool_server_success = test_agent_tool_server()

    # Print the results
    print("\nResults:")
    print(f"Knowledge Resource server: {'SUCCESS' if knowledge_server_success else 'FAILURE'}")
    print(f"Agent Tool server: {'SUCCESS' if agent_tool_server_success else 'FAILURE'}")

    # Return success if both tests passed
    return 0 if knowledge_server_success and agent_tool_server_success else 1

if __name__ == "__main__":
    sys.exit(main())
