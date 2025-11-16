import asyncio
import os
import stat
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from tta_dev_primitives.core.context import WorkflowContext
from tta_dev_primitives.integrations.llm import LLMResult

from tta_dev_primitives.hooks import (
    CreateHookInput,
    CreateHookPrimitive,
    HookInfo,
    ListHooksPrimitive,
    RefineHookInput,
    RefineHookPrimitive,
    TestHookInput,
    TestHookPrimitive,
    ValidateHookInput,
    ValidateHookPrimitive,
)

pytestmark = pytest.mark.asyncio


@pytest.fixture
def mock_context() -> WorkflowContext:
    """Provides a mock WorkflowContext."""
    return WorkflowContext(correlation_id="test-123")


@pytest.fixture
def hooks_dir(tmp_path: Path) -> Path:
    """Creates a temporary hooks directory."""
    hooks_path = tmp_path / ".cline" / "hooks"
    hooks_path.mkdir(parents=True, exist_ok=True)
    return hooks_path


class TestListHooksPrimitive:
    async def test_list_hooks_successfully(
        self, mock_context: WorkflowContext, hooks_dir: Path
    ):
        # Arrange
        primitive = ListHooksPrimitive()
        hook_path = hooks_dir / "my-hook.sh"
        hook_path.touch()
        os.chmod(hook_path, stat.S_IRWXU)

        non_exec_path = hooks_dir / "not-a-hook.txt"
        non_exec_path.touch()

        with patch("pathlib.Path.home", return_value=hooks_dir.parent.parent):
            # Act
            result = await primitive._execute(mock_context)

            # Assert
            assert len(result) == 1
            assert isinstance(result[0], HookInfo)
            assert result[0].name == "my-hook.sh"

    async def test_list_hooks_no_dir(
        self, mock_context: WorkflowContext, tmp_path: Path
    ):
        # Arrange
        primitive = ListHooksPrimitive()
        with patch("pathlib.Path.home", return_value=tmp_path):
            # Act
            result = await primitive._execute(mock_context)

            # Assert
            assert result == []


class TestCreateHookPrimitive:
    async def test_create_hook(self, mock_context: WorkflowContext, hooks_dir: Path):
        # Arrange
        primitive = CreateHookPrimitive()
        input_data = CreateHookInput(
            name="new-hook.sh", content="#!/bin/bash\necho 'Hello'"
        )

        with patch("pathlib.Path.home", return_value=hooks_dir.parent.parent):
            # Act
            result_path = await primitive._execute(mock_context, input_data)

            # Assert
            hook_path = Path(result_path)
            assert hook_path.exists()
            assert hook_path.read_text() == "#!/bin/bash\necho 'Hello'"
            assert os.access(hook_path, os.X_OK)


class TestValidateHookPrimitive:
    @patch("tta_dev_primitives.hooks.validate_hook.which")
    @patch("asyncio.create_subprocess_exec")
    async def test_validate_hook_success(
        self, mock_exec: AsyncMock, mock_which: MagicMock, mock_context: WorkflowContext
    ):
        # Arrange
        mock_which.return_value = "/usr/bin/shellcheck"
        mock_proc = AsyncMock()
        mock_proc.communicate.return_value = (b"[]", b"")
        mock_proc.returncode = 0
        mock_exec.return_value = mock_proc

        primitive = ValidateHookPrimitive()
        input_data = ValidateHookInput(hook_path="/path/to/hook.sh")

        # Act
        result = await primitive._execute(mock_context, input_data)

        # Assert
        assert result.success
        assert result.issues == []

    @patch("tta_dev_primitives.hooks.validate_hook.which", return_value=None)
    async def test_shellcheck_not_found(
        self, mock_which: MagicMock, mock_context: WorkflowContext
    ):
        # Arrange
        primitive = ValidateHookPrimitive()
        input_data = ValidateHookInput(hook_path="/path/to/hook.sh")

        # Act
        result = await primitive._execute(mock_context, input_data)

        # Assert
        assert not result.success
        assert "shellcheck is not installed" in result.error_message


class TestTestHookPrimitive:
    @patch("asyncio.create_subprocess_exec")
    async def test_hook_execution_success(
        self, mock_exec: AsyncMock, mock_context: WorkflowContext
    ):
        # Arrange
        mock_proc = AsyncMock()
        mock_proc.communicate.return_value = (b"output", b"")
        mock_proc.returncode = 0
        mock_exec.return_value = mock_proc

        primitive = TestHookPrimitive()
        input_data = TestHookInput(hook_path="/path/to/hook.sh")

        # Act
        result = await primitive._execute(mock_context, input_data)

        # Assert
        assert result.exit_code == 0
        assert result.stdout == "output"
        assert not result.timed_out

    @patch("asyncio.create_subprocess_exec")
    async def test_hook_execution_timeout(
        self, mock_exec: AsyncMock, mock_context: WorkflowContext
    ):
        # Arrange
        mock_exec.side_effect = asyncio.TimeoutError
        primitive = TestHookPrimitive()
        input_data = TestHookInput(hook_path="/path/to/hook.sh", timeout=0.1)

        # Act
        result = await primitive._execute(mock_context, input_data)

        # Assert
        assert result.timed_out
        assert result.exit_code == -1


class TestRefineHookPrimitive:
    @patch("tta_dev_primitives.hooks.refine_hook.LLMPrimitive")
    @patch("tta_dev_primitives.hooks.refine_hook.CreateHookPrimitive")
    @patch("tta_dev_primitives.hooks.refine_hook.ValidateHookPrimitive")
    @patch("tta_dev_primitives.hooks.refine_hook.TestHookPrimitive")
    async def test_refine_hook_succeeds_first_try(
        self,
        mock_test: MagicMock,
        mock_validate: MagicMock,
        mock_create: MagicMock,
        mock_llm: MagicMock,
        mock_context: WorkflowContext,
        hooks_dir: Path,
    ):
        # Arrange
        mock_llm.return_value._execute = AsyncMock(
            return_value=LLMResult(response="#!/bin/bash\necho 'Success'")
        )
        mock_create.return_value._execute = AsyncMock()
        mock_validate.return_value._execute = AsyncMock(
            return_value=MagicMock(success=True)
        )
        mock_test.return_value._execute = AsyncMock(return_value=MagicMock(exit_code=0))

        primitive = RefineHookPrimitive()
        input_data = RefineHookInput(
            hook_name="test-hook.sh", prompt="Create a success hook"
        )

        with patch("pathlib.Path.home", return_value=hooks_dir.parent.parent):
            # Act
            result = await primitive._execute(mock_context, input_data)

            # Assert
            assert result.success
            assert len(result.attempts) == 1
            assert result.final_script_path is not None
