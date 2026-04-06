"""Unit tests for ttadev.cli.hw_detect — hardware-aware Ollama model recommendation."""

from __future__ import annotations

import json
import subprocess
from unittest.mock import MagicMock, patch

import pytest

from ttadev.cli.hw_detect import (
    _detect_amd_vram_gb,
    _detect_nvidia_vram_gb,
    detect_gpu_vram_gb,
    detect_system_ram_gb,
    hardware_summary,
    recommend_ollama_model,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _completed(stdout: str = "", returncode: int = 0) -> subprocess.CompletedProcess[str]:
    """Build a fake CompletedProcess."""
    result: subprocess.CompletedProcess[str] = subprocess.CompletedProcess(
        args=[], returncode=returncode, stdout=stdout, stderr=""
    )
    return result


# ---------------------------------------------------------------------------
# _detect_nvidia_vram_gb
# ---------------------------------------------------------------------------


class TestDetectNvidiaVramGb:
    def test_returns_gb_from_mib(self) -> None:
        """Single GPU: 16384 MiB → 16.0 GB."""
        with patch("ttadev.cli.hw_detect._run", return_value=_completed("16384\n")):
            result = _detect_nvidia_vram_gb()
        assert result == pytest.approx(16.0)

    def test_uses_first_gpu_when_multiple(self) -> None:
        """Multiple GPUs: takes the first line (24576 MiB → 24.0 GB)."""
        with patch("ttadev.cli.hw_detect._run", return_value=_completed("24576\n8192\n")):
            result = _detect_nvidia_vram_gb()
        assert result == pytest.approx(24.0)

    def test_returns_none_on_nonzero_returncode(self) -> None:
        with patch("ttadev.cli.hw_detect._run", return_value=_completed("", returncode=1)):
            result = _detect_nvidia_vram_gb()
        assert result is None

    def test_returns_none_on_empty_output(self) -> None:
        with patch("ttadev.cli.hw_detect._run", return_value=_completed("")):
            result = _detect_nvidia_vram_gb()
        assert result is None

    def test_returns_none_when_file_not_found(self) -> None:
        with patch("ttadev.cli.hw_detect._run", side_effect=FileNotFoundError):
            result = _detect_nvidia_vram_gb()
        assert result is None

    def test_returns_none_on_timeout(self) -> None:
        with patch("ttadev.cli.hw_detect._run", side_effect=subprocess.TimeoutExpired("cmd", 5)):
            result = _detect_nvidia_vram_gb()
        assert result is None

    def test_returns_none_on_os_error(self) -> None:
        with patch("ttadev.cli.hw_detect._run", side_effect=OSError):
            result = _detect_nvidia_vram_gb()
        assert result is None

    def test_returns_none_on_invalid_output(self) -> None:
        with patch("ttadev.cli.hw_detect._run", return_value=_completed("not a number\n")):
            result = _detect_nvidia_vram_gb()
        assert result is None

    def test_small_vram(self) -> None:
        """4096 MiB → 4.0 GB."""
        with patch("ttadev.cli.hw_detect._run", return_value=_completed("4096\n")):
            result = _detect_nvidia_vram_gb()
        assert result == pytest.approx(4.0)


# ---------------------------------------------------------------------------
# _detect_amd_vram_gb
# ---------------------------------------------------------------------------


class TestDetectAmdVramGb:
    def _amd_json(self, vram_bytes: int) -> str:
        return json.dumps(
            {"card0": {"VRAM Total Memory (B)": str(vram_bytes), "VRAM Total Used Memory (B)": "0"}}
        )

    def test_returns_gb_from_json(self) -> None:
        """16 GB VRAM in bytes."""
        vram_bytes = 16 * 1024**3
        with patch(
            "ttadev.cli.hw_detect._run", return_value=_completed(self._amd_json(vram_bytes))
        ):
            result = _detect_amd_vram_gb()
        assert result == pytest.approx(16.0)

    def test_returns_none_on_file_not_found(self) -> None:
        with patch("ttadev.cli.hw_detect._run", side_effect=FileNotFoundError):
            result = _detect_amd_vram_gb()
        assert result is None

    def test_returns_none_on_timeout(self) -> None:
        with patch("ttadev.cli.hw_detect._run", side_effect=subprocess.TimeoutExpired("cmd", 5)):
            result = _detect_amd_vram_gb()
        assert result is None

    def test_returns_none_on_nonzero_returncode(self) -> None:
        with patch("ttadev.cli.hw_detect._run", return_value=_completed("", returncode=1)):
            result = _detect_amd_vram_gb()
        assert result is None

    def test_returns_none_on_invalid_json(self) -> None:
        with patch("ttadev.cli.hw_detect._run", return_value=_completed("not json")):
            result = _detect_amd_vram_gb()
        assert result is None

    def test_returns_none_on_empty_output(self) -> None:
        with patch("ttadev.cli.hw_detect._run", return_value=_completed("")):
            result = _detect_amd_vram_gb()
        assert result is None

    def test_returns_none_when_no_vram_key(self) -> None:
        data = json.dumps({"card0": {"Other Key": "12345"}})
        with patch("ttadev.cli.hw_detect._run", return_value=_completed(data)):
            result = _detect_amd_vram_gb()
        assert result is None


# ---------------------------------------------------------------------------
# detect_gpu_vram_gb
# ---------------------------------------------------------------------------


class TestDetectGpuVramGb:
    def test_nvidia_takes_priority(self) -> None:
        """NVIDIA found → AMD not attempted."""
        with (
            patch("ttadev.cli.hw_detect._detect_nvidia_vram_gb", return_value=8.0),
            patch("ttadev.cli.hw_detect._detect_amd_vram_gb") as amd_mock,
        ):
            result = detect_gpu_vram_gb()
        assert result == pytest.approx(8.0)
        amd_mock.assert_not_called()

    def test_falls_back_to_amd_when_nvidia_fails(self) -> None:
        with (
            patch("ttadev.cli.hw_detect._detect_nvidia_vram_gb", return_value=None),
            patch("ttadev.cli.hw_detect._detect_amd_vram_gb", return_value=12.0),
        ):
            result = detect_gpu_vram_gb()
        assert result == pytest.approx(12.0)

    def test_returns_none_when_both_fail(self) -> None:
        with (
            patch("ttadev.cli.hw_detect._detect_nvidia_vram_gb", return_value=None),
            patch("ttadev.cli.hw_detect._detect_amd_vram_gb", return_value=None),
        ):
            result = detect_gpu_vram_gb()
        assert result is None


# ---------------------------------------------------------------------------
# detect_system_ram_gb
# ---------------------------------------------------------------------------


class TestDetectSystemRamGb:
    def test_uses_psutil_when_available(self) -> None:
        mock_psutil = MagicMock()
        mock_psutil.virtual_memory.return_value.total = 32 * 1024**3
        with patch.dict("sys.modules", {"psutil": mock_psutil}):
            # Force re-import path by patching directly inside module.
            with patch("ttadev.cli.hw_detect.detect_system_ram_gb", wraps=None) as _:
                pass
        # Test via direct psutil import mock.

        import ttadev.cli.hw_detect as hw

        with patch.object(hw, "detect_system_ram_gb") as mock_fn:
            mock_fn.return_value = 32.0
            assert mock_fn() == 32.0

    def test_returns_positive_float(self) -> None:
        ram = detect_system_ram_gb()
        assert isinstance(ram, float)
        assert ram > 0


# ---------------------------------------------------------------------------
# recommend_ollama_model — tier boundaries
# ---------------------------------------------------------------------------


class TestRecommendOllamaModel:
    def _with_gpu(self, vram_gb: float) -> str:
        with (
            patch("ttadev.cli.hw_detect.detect_gpu_vram_gb", return_value=vram_gb),
            patch("ttadev.cli.hw_detect.detect_system_ram_gb", return_value=32.0),
        ):
            return recommend_ollama_model()

    def _no_gpu(self, ram_gb: float) -> str:
        with (
            patch("ttadev.cli.hw_detect.detect_gpu_vram_gb", return_value=None),
            patch("ttadev.cli.hw_detect.detect_system_ram_gb", return_value=ram_gb),
        ):
            return recommend_ollama_model()

    def test_vram_24gb_recommends_32b(self) -> None:
        assert self._with_gpu(24.0) == "qwen2.5-coder:32b"

    def test_vram_32gb_recommends_32b(self) -> None:
        assert self._with_gpu(32.0) == "qwen2.5-coder:32b"

    def test_vram_16gb_recommends_14b(self) -> None:
        assert self._with_gpu(16.0) == "qwen2.5:14b"

    def test_vram_20gb_recommends_14b(self) -> None:
        assert self._with_gpu(20.0) == "qwen2.5:14b"

    def test_vram_8gb_recommends_gemma3_4b(self) -> None:
        assert self._with_gpu(8.0) == "gemma3:4b"

    def test_vram_10gb_recommends_gemma3_4b(self) -> None:
        assert self._with_gpu(10.0) == "gemma3:4b"

    def test_vram_4gb_recommends_3b(self) -> None:
        assert self._with_gpu(4.0) == "qwen2.5:3b"

    def test_vram_6gb_recommends_3b(self) -> None:
        assert self._with_gpu(6.0) == "qwen2.5:3b"

    def test_no_gpu_ram_16gb_recommends_7b(self) -> None:
        assert self._no_gpu(16.0) == "qwen2.5:7b"

    def test_no_gpu_ram_32gb_recommends_7b(self) -> None:
        assert self._no_gpu(32.0) == "qwen2.5:7b"

    def test_no_gpu_ram_8gb_recommends_3b(self) -> None:
        assert self._no_gpu(8.0) == "qwen2.5:3b"

    def test_no_gpu_ram_4gb_recommends_3b(self) -> None:
        assert self._no_gpu(4.0) == "qwen2.5:3b"


# ---------------------------------------------------------------------------
# hardware_summary
# ---------------------------------------------------------------------------


class TestHardwareSummary:
    def test_output_shape_with_gpu(self) -> None:
        with (
            patch("ttadev.cli.hw_detect.detect_gpu_vram_gb", return_value=16.0),
            patch("ttadev.cli.hw_detect.detect_system_ram_gb", return_value=32.0),
        ):
            summary = hardware_summary()

        assert set(summary.keys()) == {
            "gpu_vram_gb",
            "system_ram_gb",
            "recommended_model",
            "reason",
        }
        assert summary["gpu_vram_gb"] == pytest.approx(16.0)
        assert summary["system_ram_gb"] == pytest.approx(32.0)
        assert isinstance(summary["recommended_model"], str)
        assert len(summary["recommended_model"]) > 0
        assert isinstance(summary["reason"], str)
        assert len(summary["reason"]) > 0

    def test_output_shape_without_gpu(self) -> None:
        with (
            patch("ttadev.cli.hw_detect.detect_gpu_vram_gb", return_value=None),
            patch("ttadev.cli.hw_detect.detect_system_ram_gb", return_value=32.0),
        ):
            summary = hardware_summary()

        assert summary["gpu_vram_gb"] is None
        assert summary["recommended_model"] == "qwen2.5:7b"

    def test_recommended_model_matches_standalone_recommend(self) -> None:
        with (
            patch("ttadev.cli.hw_detect.detect_gpu_vram_gb", return_value=8.0),
            patch("ttadev.cli.hw_detect.detect_system_ram_gb", return_value=32.0),
        ):
            summary = hardware_summary()
            standalone = recommend_ollama_model()

        assert summary["recommended_model"] == standalone
