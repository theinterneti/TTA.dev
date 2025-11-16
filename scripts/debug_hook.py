import asyncio
from tta_dev_primitives.core.context import WorkflowContext
from tta_dev_primitives.hooks import TestHookPrimitive, TestHookInput

async def main():
    """
    This script uses the TestHookPrimitive to debug the post-message.sh hook.
    """
    ctx = WorkflowContext(correlation_id="cline-hook-debugging")
    
    print("--- Testing the post-message.sh Hook ---")
    test_primitive = TestHookPrimitive()
    
    # We need to simulate the environment the hook expects.
    # Let's provide a user message via an environment variable.
    test_env = {"CLINE_USER_MESSAGE": "Let's add the MCP from github.com/serena/serena-mcp"}
    
    test_input = TestHookInput(
        hook_path=".cline/hooks/post-message.sh",
        test_env=test_env
    )
    
    test_result = await test_primitive._execute(ctx, test_input)
    
    if test_result.exit_code == 0:
        print("Hook test successful!")
        print(f"Stdout: {test_result.stdout.strip()}")
        print(f"Stderr: {test_result.stderr.strip()}")
    else:
        print("Hook test failed.")
        print(f"Exit Code: {test_result.exit_code}")
        print(f"Stdout: {test_result.stdout.strip()}")
        print(f"Stderr: {test_result.stderr.strip()}")
    print("-" * 20)

if __name__ == "__main__":
    asyncio.run(main())
