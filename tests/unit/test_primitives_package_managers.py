"""Unit tests for ttadev/primitives/package_managers/ (uv and pnpm).

All subprocess calls are mocked — no real uv or pnpm binary is invoked.
Tests verify command construction, output parsing, and flag handling.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ttadev.primitives.core.base import WorkflowContext
from ttadev.primitives.package_managers.base import (
    PackageManagerOutput,
)
from ttadev.primitives.package_managers.pnpm import (
    PnpmAddInput,
    PnpmAddPrimitive,
    PnpmInstallInput,
    PnpmInstallPrimitive,
    PnpmRemoveInput,
    PnpmRemovePrimitive,
    PnpmRunInput,
    PnpmRunPrimitive,
    PnpmUpdateInput,
    PnpmUpdatePrimitive,
)
from ttadev.primitives.package_managers.uv import (
    UvAddInput,
    UvAddPrimitive,
    UvLockInput,
    UvLockPrimitive,
    UvRemoveInput,
    UvRemovePrimitive,
    UvRunInput,
    UvRunPrimitive,
    UvSyncInput,
    UvSyncPrimitive,
    UvTreeInput,
    UvTreePrimitive,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _mock_proc(stdout: bytes = b"ok", stderr: bytes = b"", returncode: int = 0) -> MagicMock:
    """Return an asyncio Process mock with the given output."""
    proc = MagicMock()
    proc.communicate = AsyncMock(return_value=(stdout, stderr))
    proc.returncode = returncode
    return proc


def _ctx() -> WorkflowContext:
    return WorkflowContext(workflow_id="test-pkg-mgr")


EXEC = "asyncio.create_subprocess_exec"


# ---------------------------------------------------------------------------
# PackageManagerOutput model
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestPackageManagerOutput:
    def test_default_command_field(self) -> None:
        out = PackageManagerOutput(
            success=True, stdout="", stderr="", return_code=0, execution_time=0.1, command="uv sync"
        )
        assert out.command == "uv sync"

    def test_failure_flag(self) -> None:
        out = PackageManagerOutput(
            success=False, stdout="", stderr="err", return_code=1, execution_time=0.0, command="x"
        )
        assert out.success is False


# ---------------------------------------------------------------------------
# UvSyncPrimitive
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestUvSyncPrimitive:
    async def test_success_path(self) -> None:
        with patch(EXEC, return_value=_mock_proc(b"Synced", b"", 0)) as mock:
            result = await UvSyncPrimitive().execute(UvSyncInput(), _ctx())
        assert result.success is True
        assert "uv" in mock.call_args.args[0]
        assert "sync" in mock.call_args.args

    async def test_failure_path(self) -> None:
        with patch(EXEC, return_value=_mock_proc(b"", b"err", 1)):
            result = await UvSyncPrimitive().execute(UvSyncInput(), _ctx())
        assert result.success is False
        assert result.return_code == 1

    async def test_all_extras_flag(self) -> None:
        with patch(EXEC, return_value=_mock_proc()) as mock:
            await UvSyncPrimitive().execute(UvSyncInput(all_extras=True), _ctx())
        assert "--all-extras" in mock.call_args.args

    async def test_frozen_flag(self) -> None:
        with patch(EXEC, return_value=_mock_proc()) as mock:
            await UvSyncPrimitive().execute(UvSyncInput(frozen=True), _ctx())
        assert "--frozen" in mock.call_args.args

    async def test_no_dev_flag(self) -> None:
        with patch(EXEC, return_value=_mock_proc()) as mock:
            await UvSyncPrimitive().execute(UvSyncInput(no_dev=True), _ctx())
        assert "--no-dev" in mock.call_args.args

    async def test_stdout_captured(self) -> None:
        with patch(EXEC, return_value=_mock_proc(b"output text")):
            result = await UvSyncPrimitive().execute(UvSyncInput(), _ctx())
        assert result.stdout == "output text"

    async def test_working_dir_forwarded(self) -> None:
        with patch(EXEC, return_value=_mock_proc()) as mock:
            await UvSyncPrimitive(working_dir="/tmp").execute(UvSyncInput(), _ctx())
        assert mock.call_args.kwargs.get("cwd") == "/tmp"


# ---------------------------------------------------------------------------
# UvAddPrimitive
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestUvAddPrimitive:
    async def test_packages_in_command(self) -> None:
        with patch(EXEC, return_value=_mock_proc()) as mock:
            await UvAddPrimitive().execute(UvAddInput(packages=["requests"]), _ctx())
        assert "requests" in mock.call_args.args

    async def test_dev_flag(self) -> None:
        with patch(EXEC, return_value=_mock_proc()) as mock:
            await UvAddPrimitive().execute(UvAddInput(packages=["pytest"], dev=True), _ctx())
        assert "--dev" in mock.call_args.args

    async def test_group_flag(self) -> None:
        with patch(EXEC, return_value=_mock_proc()) as mock:
            await UvAddPrimitive().execute(UvAddInput(packages=["x"], group="lint"), _ctx())
        args = mock.call_args.args
        assert "--group" in args
        assert "lint" in args

    async def test_packages_added_field_on_success(self) -> None:
        with patch(EXEC, return_value=_mock_proc(returncode=0)):
            result = await UvAddPrimitive().execute(UvAddInput(packages=["requests"]), _ctx())
        assert result.packages_added == ["requests"]

    async def test_packages_added_empty_on_failure(self) -> None:
        with patch(EXEC, return_value=_mock_proc(returncode=1)):
            result = await UvAddPrimitive().execute(UvAddInput(packages=["bad"]), _ctx())
        assert result.packages_added == []

    async def test_success_true_on_rc_zero(self) -> None:
        with patch(EXEC, return_value=_mock_proc(returncode=0)):
            result = await UvAddPrimitive().execute(UvAddInput(packages=["x"]), _ctx())
        assert result.success is True


# ---------------------------------------------------------------------------
# UvRemovePrimitive
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestUvRemovePrimitive:
    async def test_packages_in_command(self) -> None:
        with patch(EXEC, return_value=_mock_proc()) as mock:
            await UvRemovePrimitive().execute(UvRemoveInput(packages=["requests"]), _ctx())
        assert "requests" in mock.call_args.args

    async def test_packages_removed_on_success(self) -> None:
        with patch(EXEC, return_value=_mock_proc(returncode=0)):
            result = await UvRemovePrimitive().execute(UvRemoveInput(packages=["x"]), _ctx())
        assert result.packages_removed == ["x"]

    async def test_packages_removed_empty_on_failure(self) -> None:
        with patch(EXEC, return_value=_mock_proc(returncode=1)):
            result = await UvRemovePrimitive().execute(UvRemoveInput(packages=["x"]), _ctx())
        assert result.packages_removed == []


# ---------------------------------------------------------------------------
# UvRunPrimitive
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestUvRunPrimitive:
    async def test_command_in_args(self) -> None:
        with patch(EXEC, return_value=_mock_proc()) as mock:
            await UvRunPrimitive().execute(UvRunInput(command="pytest"), _ctx())
        assert "pytest" in mock.call_args.args

    async def test_extra_args_forwarded(self) -> None:
        with patch(EXEC, return_value=_mock_proc()) as mock:
            await UvRunPrimitive().execute(UvRunInput(command="pytest", args=["-v"]), _ctx())
        assert "-v" in mock.call_args.args

    async def test_success_on_rc_zero(self) -> None:
        with patch(EXEC, return_value=_mock_proc(returncode=0)):
            result = await UvRunPrimitive().execute(UvRunInput(command="pytest"), _ctx())
        assert result.success is True


# ---------------------------------------------------------------------------
# UvLockPrimitive
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestUvLockPrimitive:
    async def test_basic_command(self) -> None:
        with patch(EXEC, return_value=_mock_proc()) as mock:
            await UvLockPrimitive().execute(UvLockInput(), _ctx())
        assert "lock" in mock.call_args.args

    async def test_upgrade_flag(self) -> None:
        with patch(EXEC, return_value=_mock_proc()) as mock:
            await UvLockPrimitive().execute(UvLockInput(upgrade=True), _ctx())
        assert "--upgrade" in mock.call_args.args

    async def test_no_upgrade_flag_by_default(self) -> None:
        with patch(EXEC, return_value=_mock_proc()) as mock:
            await UvLockPrimitive().execute(UvLockInput(), _ctx())
        assert "--upgrade" not in mock.call_args.args


# ---------------------------------------------------------------------------
# UvTreePrimitive
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestUvTreePrimitive:
    async def test_basic_command(self) -> None:
        with patch(EXEC, return_value=_mock_proc()) as mock:
            await UvTreePrimitive().execute(UvTreeInput(), _ctx())
        assert "tree" in mock.call_args.args

    async def test_package_filter(self) -> None:
        with patch(EXEC, return_value=_mock_proc()) as mock:
            await UvTreePrimitive().execute(UvTreeInput(package="requests"), _ctx())
        args = mock.call_args.args
        assert "--package" in args
        assert "requests" in args

    async def test_depth_flag(self) -> None:
        with patch(EXEC, return_value=_mock_proc()) as mock:
            await UvTreePrimitive().execute(UvTreeInput(depth=2), _ctx())
        args = mock.call_args.args
        assert "--depth" in args
        assert "2" in args

    async def test_depth_zero_included(self) -> None:
        """depth=0 is valid and must appear in the command (not be silently dropped)."""
        with patch(EXEC, return_value=_mock_proc()) as mock:
            await UvTreePrimitive().execute(UvTreeInput(depth=0), _ctx())
        assert "--depth" in mock.call_args.args

    async def test_no_package_flag_by_default(self) -> None:
        with patch(EXEC, return_value=_mock_proc()) as mock:
            await UvTreePrimitive().execute(UvTreeInput(), _ctx())
        assert "--package" not in mock.call_args.args


# ---------------------------------------------------------------------------
# PnpmInstallPrimitive
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestPnpmInstallPrimitive:
    async def test_basic_install_command(self) -> None:
        with patch(EXEC, return_value=_mock_proc()) as mock:
            await PnpmInstallPrimitive().execute(PnpmInstallInput(), _ctx())
        assert "install" in mock.call_args.args

    async def test_frozen_lockfile_flag(self) -> None:
        with patch(EXEC, return_value=_mock_proc()) as mock:
            await PnpmInstallPrimitive().execute(PnpmInstallInput(frozen_lockfile=True), _ctx())
        assert "--frozen-lockfile" in mock.call_args.args

    async def test_prefer_offline_flag(self) -> None:
        with patch(EXEC, return_value=_mock_proc()) as mock:
            await PnpmInstallPrimitive().execute(PnpmInstallInput(prefer_offline=True), _ctx())
        assert "--prefer-offline" in mock.call_args.args

    async def test_success_on_rc_zero(self) -> None:
        with patch(EXEC, return_value=_mock_proc(returncode=0)):
            result = await PnpmInstallPrimitive().execute(PnpmInstallInput(), _ctx())
        assert result.success is True

    async def test_failure_on_nonzero_rc(self) -> None:
        with patch(EXEC, return_value=_mock_proc(returncode=1)):
            result = await PnpmInstallPrimitive().execute(PnpmInstallInput(), _ctx())
        assert result.success is False


# ---------------------------------------------------------------------------
# PnpmAddPrimitive
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestPnpmAddPrimitive:
    async def test_packages_in_command(self) -> None:
        with patch(EXEC, return_value=_mock_proc()) as mock:
            await PnpmAddPrimitive().execute(PnpmAddInput(packages=["lodash"]), _ctx())
        assert "lodash" in mock.call_args.args

    async def test_dev_flag(self) -> None:
        with patch(EXEC, return_value=_mock_proc()) as mock:
            await PnpmAddPrimitive().execute(PnpmAddInput(packages=["x"], dev=True), _ctx())
        assert "--save-dev" in mock.call_args.args

    async def test_save_exact_flag(self) -> None:
        with patch(EXEC, return_value=_mock_proc()) as mock:
            await PnpmAddPrimitive().execute(PnpmAddInput(packages=["x"], save_exact=True), _ctx())
        assert "--save-exact" in mock.call_args.args

    async def test_packages_added_on_success(self) -> None:
        with patch(EXEC, return_value=_mock_proc(returncode=0)):
            result = await PnpmAddPrimitive().execute(PnpmAddInput(packages=["lodash"]), _ctx())
        assert result.packages_added == ["lodash"]

    async def test_packages_added_empty_on_failure(self) -> None:
        with patch(EXEC, return_value=_mock_proc(returncode=1)):
            result = await PnpmAddPrimitive().execute(PnpmAddInput(packages=["bad"]), _ctx())
        assert result.packages_added == []


# ---------------------------------------------------------------------------
# PnpmRemovePrimitive
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestPnpmRemovePrimitive:
    async def test_packages_in_command(self) -> None:
        with patch(EXEC, return_value=_mock_proc()) as mock:
            await PnpmRemovePrimitive().execute(PnpmRemoveInput(packages=["lodash"]), _ctx())
        assert "lodash" in mock.call_args.args

    async def test_success_on_rc_zero(self) -> None:
        with patch(EXEC, return_value=_mock_proc(returncode=0)):
            result = await PnpmRemovePrimitive().execute(PnpmRemoveInput(packages=["x"]), _ctx())
        assert result.success is True

    async def test_failure_on_nonzero_rc(self) -> None:
        with patch(EXEC, return_value=_mock_proc(returncode=1)):
            result = await PnpmRemovePrimitive().execute(PnpmRemoveInput(packages=["x"]), _ctx())
        assert result.success is False


# ---------------------------------------------------------------------------
# PnpmRunPrimitive
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestPnpmRunPrimitive:
    async def test_script_in_command(self) -> None:
        with patch(EXEC, return_value=_mock_proc()) as mock:
            await PnpmRunPrimitive().execute(PnpmRunInput(script="build"), _ctx())
        assert "build" in mock.call_args.args

    async def test_extra_args_forwarded(self) -> None:
        with patch(EXEC, return_value=_mock_proc()) as mock:
            await PnpmRunPrimitive().execute(PnpmRunInput(script="test", args=["--watch"]), _ctx())
        assert "--watch" in mock.call_args.args

    async def test_success_on_rc_zero(self) -> None:
        with patch(EXEC, return_value=_mock_proc(returncode=0)):
            result = await PnpmRunPrimitive().execute(PnpmRunInput(script="lint"), _ctx())
        assert result.success is True


# ---------------------------------------------------------------------------
# PnpmUpdatePrimitive
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestPnpmUpdatePrimitive:
    async def test_basic_update_command(self) -> None:
        with patch(EXEC, return_value=_mock_proc()) as mock:
            await PnpmUpdatePrimitive().execute(PnpmUpdateInput(), _ctx())
        assert "update" in mock.call_args.args

    async def test_specific_packages(self) -> None:
        with patch(EXEC, return_value=_mock_proc()) as mock:
            await PnpmUpdatePrimitive().execute(PnpmUpdateInput(packages=["lodash"]), _ctx())
        assert "lodash" in mock.call_args.args

    async def test_latest_flag(self) -> None:
        with patch(EXEC, return_value=_mock_proc()) as mock:
            await PnpmUpdatePrimitive().execute(PnpmUpdateInput(latest=True), _ctx())
        assert "--latest" in mock.call_args.args

    async def test_no_latest_flag_by_default(self) -> None:
        with patch(EXEC, return_value=_mock_proc()) as mock:
            await PnpmUpdatePrimitive().execute(PnpmUpdateInput(), _ctx())
        assert "--latest" not in mock.call_args.args

    async def test_success_on_rc_zero(self) -> None:
        with patch(EXEC, return_value=_mock_proc(returncode=0)):
            result = await PnpmUpdatePrimitive().execute(PnpmUpdateInput(), _ctx())
        assert result.success is True
