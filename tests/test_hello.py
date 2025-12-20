import subprocess
import sys


def test_hello_world():
    """Verify that hello.py prints 'Hello World' to stdout."""
    # Run the hello.py script as a subprocess
    process = subprocess.run(
        [sys.executable, "hello.py"], capture_output=True, text=True, check=True
    )

    # Assert that the output is 'Hello World\n'
    assert process.stdout == "Hello World\n"
    assert process.stderr == ""
