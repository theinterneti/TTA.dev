import os
from dataclasses import dataclass, field

from tta_dev_primitives.core.base import WorkflowPrimitive
from tta_dev_primitives.core.context import WorkflowContext
from tta_dev_primitives.integrations.llm import LLMInput, LLMPrimitive

from .create_hook import CreateHookInput, CreateHookPrimitive
from .test_hook import TestHookInput, TestHookPrimitive, TestResult
from .validate_hook import ValidateHookInput, ValidateHookPrimitive, ValidationResult


@dataclass
class RefineHookInput:
    hook_name: str
    prompt: str
    max_attempts: int = 3
    test_env: dict[str, str] = field(default_factory=dict)


@dataclass
class RefinementAttempt:
    attempt_number: int
    script_content: str
    validation_result: ValidationResult | None = None
    test_result: TestResult | None = None


@dataclass
class RefineHookResult:
    success: bool
    final_script_path: str | None = None
    attempts: list[RefinementAttempt] = field(default_factory=list)
    error_message: str | None = None


class RefineHookPrimitive(WorkflowPrimitive[RefineHookInput, RefineHookResult]):
    """
    An intelligent primitive that generates, validates, tests, and refines a Cline hook script
    until it meets the specified requirements.
    """

    async def _execute(
        self,
        context: WorkflowContext,
        input_data: RefineHookInput,
    ) -> RefineHookResult:
        llm_primitive = LLMPrimitive()
        create_primitive = CreateHookPrimitive()
        validate_primitive = ValidateHookPrimitive()
        test_primitive = TestHookPrimitive()

        attempts = []
        current_prompt = input_data.prompt
        hook_path = os.path.join(
            os.path.expanduser("~/.cline/hooks"), input_data.hook_name
        )

        for i in range(input_data.max_attempts):
            attempt_num = i + 1

            # 1. Generate
            llm_result = await llm_primitive._execute(
                context, LLMInput(prompt=current_prompt)
            )
            script_content = llm_result.response

            attempt = RefinementAttempt(
                attempt_number=attempt_num, script_content=script_content
            )

            # 2. Create the hook file
            await create_primitive._execute(
                context,
                CreateHookInput(name=input_data.hook_name, content=script_content),
            )

            # 3. Validate
            validation_result = await validate_primitive._execute(
                context, ValidateHookInput(hook_path=hook_path)
            )
            attempt.validation_result = validation_result
            if not validation_result.success and validation_result.issues:
                current_prompt += f"\nAttempt {attempt_num} failed validation (shellcheck). Please fix these issues:\n{validation_result.issues}"
                attempts.append(attempt)
                continue

            # 4. Test
            test_result = await test_primitive._execute(
                context, TestHookInput(hook_path=hook_path, env=input_data.test_env)
            )
            attempt.test_result = test_result
            if test_result.exit_code != 0:
                current_prompt += f"\nAttempt {attempt_num} failed the test. Exit code: {test_result.exit_code}\nStderr:\n{test_result.stderr}\nPlease fix the script."
                attempts.append(attempt)
                continue

            # Success
            attempts.append(attempt)
            return RefineHookResult(
                success=True, final_script_path=hook_path, attempts=attempts
            )

        return RefineHookResult(
            success=False,
            attempts=attempts,
            error_message="Failed to create a working hook within the maximum number of attempts.",
        )
