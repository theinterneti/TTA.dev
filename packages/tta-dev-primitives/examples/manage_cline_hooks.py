import asyncio

from tta_dev_primitives.core.context import WorkflowContext

from tta_dev_primitives.hooks import (
    CreateHookInput,
    CreateHookPrimitive,
    ListHooksPrimitive,
    RefineHookInput,
    RefineHookPrimitive,
    TestHookInput,
    TestHookPrimitive,
    ValidateHookInput,
    ValidateHookPrimitive,
)


async def main():
    """
    This example demonstrates a complete workflow for managing Cline hooks
    using the new primitives.
    """
    ctx = WorkflowContext(correlation_id="cline-hook-management-example")

    # 1. List existing hooks
    print("--- Listing Existing Hooks ---")
    list_primitive = ListHooksPrimitive()
    existing_hooks = await list_primitive._execute(ctx)
    if existing_hooks:
        for hook in existing_hooks:
            print(f"- Found hook: {hook.name} (Permissions: {hook.permissions})")
    else:
        print("No existing hooks found.")
    print("-" * 20)

    # 2. Create a new, simple hook
    print("\n--- Creating a New Hook ---")
    create_primitive = CreateHookPrimitive()
    hook_content = "#!/bin/bash\n\necho 'Hello from a TTA.dev-managed hook!'"
    create_input = CreateHookInput(name="hello-hook.sh", content=hook_content)
    hook_path = await create_primitive._execute(ctx, create_input)
    print(f"Successfully created hook at: {hook_path}")
    print("-" * 20)

    # 3. Validate the new hook
    print("\n--- Validating the New Hook ---")
    validate_primitive = ValidateHookPrimitive()
    validate_input = ValidateHookInput(hook_path=hook_path)
    validation_result = await validate_primitive._execute(ctx, validate_input)
    if validation_result.success:
        print("Hook validation successful (shellcheck passed).")
    else:
        print("Hook validation failed:")
        for issue in validation_result.issues:
            print(f"- L{issue.line}: {issue.message} (Code: SC{issue.code})")
    print("-" * 20)

    # 4. Test the new hook
    print("\n--- Testing the New Hook ---")
    test_primitive = TestHookPrimitive()
    test_input = TestHookInput(hook_path=hook_path)
    test_result = await test_primitive._execute(ctx, test_input)
    if test_result.exit_code == 0:
        print("Hook test successful!")
        print(f"Stdout: {test_result.stdout.strip()}")
    else:
        print("Hook test failed.")
        print(f"Exit Code: {test_result.exit_code}")
        print(f"Stderr: {test_result.stderr.strip()}")
    print("-" * 20)

    # 5. Use the intelligent RefineHookPrimitive to create a more complex hook
    print("\n--- Using RefineHookPrimitive for an Intelligent Hook ---")
    refine_primitive = RefineHookPrimitive()
    refine_input = RefineHookInput(
        hook_name="intelligent-hook.sh",
        prompt="Create a shell script that prints the value of the CLINE_USER_MESSAGE environment variable. If the variable is not set, it should print an error message to stderr and exit with code 1.",
        test_env={"CLINE_USER_MESSAGE": "This is a test message."},
    )
    refine_result = await refine_primitive._execute(ctx, refine_input)
    if refine_result.success:
        print("Successfully created and refined the intelligent hook!")
        print(f"Final script at: {refine_result.final_script_path}")
        print("--- Final Script Content ---")
        with open(refine_result.final_script_path) as f:
            print(f.read())
        print("--------------------------")
    else:
        print("Failed to refine the intelligent hook.")
        print(f"Error: {refine_result.error_message}")
    print("-" * 20)


if __name__ == "__main__":
    asyncio.run(main())
