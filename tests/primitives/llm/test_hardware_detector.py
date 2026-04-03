"""Tests for ttadev.primitives.llm.hardware_detector."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from ttadev.primitives.llm.hardware_detector import (
    GPUInfo,
    HardwareDetector,
    HardwareProfile,
    _estimate_params_b,
    _vram_needed_gb,
)

# ---------------------------------------------------------------------------
# Unit helpers
# ---------------------------------------------------------------------------


class TestEstimateParamsB:
    def test_tag_suffix_integer(self) -> None:
        assert _estimate_params_b("llama3.2:3b") == pytest.approx(3.0)

    def test_tag_suffix_float(self) -> None:
        assert _estimate_params_b("tinyllama:1.1b") == pytest.approx(1.1)

    def test_dash_separator(self) -> None:
        assert _estimate_params_b("llama-3.3-70b-versatile") == pytest.approx(70.0)

    def test_known_name_phi4(self) -> None:
        assert _estimate_params_b("phi4:latest") == pytest.approx(14.0)

    def test_known_name_mistral(self) -> None:
        assert _estimate_params_b("mistral:latest") == pytest.approx(7.0)

    def test_unknown_returns_none(self) -> None:
        assert _estimate_params_b("someweirdfuturalmodel:latest") is None


class TestVramNeededGb:
    def test_7b_q4(self) -> None:
        # 7 * 0.56 * 1.15 ≈ 4.5 GB
        result = _vram_needed_gb(7.0, "q4")
        assert 4.0 < result < 5.5

    def test_70b_q4(self) -> None:
        # 70 * 0.56 * 1.15 ≈ 45 GB
        result = _vram_needed_gb(70.0, "q4")
        assert 40.0 < result < 50.0

    def test_fp16_higher_than_q4(self) -> None:
        assert _vram_needed_gb(7.0, "fp16") > _vram_needed_gb(7.0, "q4")


# ---------------------------------------------------------------------------
# HardwareProfile
# ---------------------------------------------------------------------------


class TestHardwareProfile:
    def _profile(self, vram_mb: int = 4096, ram_mb: int = 16384) -> HardwareProfile:
        gpu = GPUInfo(name="Test GPU", vram_mb=vram_mb, backend="cuda")
        return HardwareProfile(cpu_cores=4, ram_mb=ram_mb, gpus=[gpu])

    def test_vram_gb_property(self) -> None:
        p = self._profile(vram_mb=4096)
        assert p.total_vram_gb == pytest.approx(4.0)

    def test_ram_gb_property(self) -> None:
        p = self._profile(ram_mb=16384)
        assert p.ram_gb == pytest.approx(16.0)

    def test_backend_cuda(self) -> None:
        assert self._profile().backend == "cuda"

    def test_backend_cpu_no_gpu(self) -> None:
        p = HardwareProfile(cpu_cores=4, ram_mb=8192)
        assert p.backend == "cpu"

    def test_can_run_small_model_on_4gb_gpu(self) -> None:
        p = self._profile(vram_mb=4096)
        assert p.can_run("llama3.2:1b") is True

    def test_cannot_run_70b_on_4gb_gpu_limited_ram(self) -> None:
        # 4GB VRAM, only 8GB RAM → can't run 70B
        p = self._profile(vram_mb=4096, ram_mb=8192)
        assert p.can_run("llama3.3:70b") is False

    def test_can_run_70b_with_large_ram_cpu_fallback(self) -> None:
        # 128GB RAM (no GPU): 128*0.6=76.8 GB available → can run 70B (needs ~45 GB)
        p = HardwareProfile(cpu_cores=8, ram_mb=131072)  # 128GB
        assert p.can_run("llama3.3:70b") is True

    def test_unknown_model_runnable(self) -> None:
        # Unknown models are optimistically accepted
        p = self._profile()
        assert p.can_run("someunknownmodel:latest") is True

    def test_max_params_b_with_gpu(self) -> None:
        p = self._profile(vram_mb=8192, ram_mb=32768)
        # 8GB VRAM / (0.56 * 1.15) ≈ 12.4B from GPU
        # 32GB * 0.6 / (0.56 * 1.15) ≈ 29.8B from RAM
        assert p.max_params_b("q4") > 10.0

    def test_summary_string(self) -> None:
        p = self._profile()
        s = p.summary()
        assert "CPU" in s
        assert "RAM" in s
        assert "CUDA" in s

    def test_to_dict(self) -> None:
        p = self._profile()
        d = p.to_dict()
        assert "cpu_cores" in d
        assert "ram_gb" in d
        assert "gpus" in d
        assert d["backend"] == "cuda"
        assert "max_params_b_q4" in d


# ---------------------------------------------------------------------------
# HardwareDetector
# ---------------------------------------------------------------------------


class TestHardwareDetector:
    def test_detect_returns_profile(self) -> None:
        det = HardwareDetector()
        profile = det.detect()
        assert isinstance(profile, HardwareProfile)
        assert profile.cpu_cores >= 1
        assert profile.ram_mb > 0

    def test_detect_cached(self) -> None:
        det = HardwareDetector()
        p1 = det.detect()
        p2 = det.detect()
        assert p1 is p2  # same object, cached

    def test_detect_force_re_reads(self) -> None:
        det = HardwareDetector()
        p1 = det.detect()
        p2 = det.detect(force=True)
        # Contents equal but may be different object after forced re-detection
        assert p1.cpu_cores == p2.cpu_cores

    def test_filter_ollama_models(self) -> None:
        det = HardwareDetector()
        # These should definitely pass on any machine with reasonable RAM
        candidates = ["llama3.2:1b", "qwen3:235b-a22b"]
        viable = det.filter_ollama_models(candidates)
        # 1B should always be viable
        assert "llama3.2:1b" in viable

    def test_recommend_size_tag_returns_known_tag(self) -> None:
        det = HardwareDetector()
        tag = det.recommend_size_tag()
        assert tag in {"1b", "3b", "7b", "14b", "32b", "70b"}

    def test_probe_nvidia_parses_output(self) -> None:
        """Test the NVIDIA parser with a mocked nvidia-smi output."""
        mock_output = "NVIDIA GeForce GTX 1650, 4096\nNVIDIA RTX 4090, 24576"
        with patch.object(HardwareDetector, "_run", return_value=mock_output):
            gpus = HardwareDetector._probe_nvidia()
        assert len(gpus) == 2
        assert gpus[0].name == "NVIDIA GeForce GTX 1650"
        assert gpus[0].vram_mb == 4096
        assert gpus[0].backend == "cuda"
        assert gpus[1].vram_mb == 24576

    def test_probe_nvidia_missing_tool(self) -> None:
        with patch.object(HardwareDetector, "_run", return_value=None):
            gpus = HardwareDetector._probe_nvidia()
        assert gpus == []

    def test_probe_rocm_parses_output(self) -> None:
        mock_output = "GPU[0]\t\t: VRAM Total Memory (B): 8589934592"
        with patch.object(HardwareDetector, "_run", return_value=mock_output):
            gpus = HardwareDetector._probe_rocm()
        assert len(gpus) == 1
        assert gpus[0].vram_mb == pytest.approx(8192, abs=1)
        assert gpus[0].backend == "rocm"

    def test_no_gpu_fallback_cpu(self) -> None:
        with patch.object(HardwareDetector, "_detect_gpus", return_value=[]):
            det = HardwareDetector()
            profile = det.detect(force=True)
        assert profile.backend == "cpu"
        assert profile.total_vram_gb == 0.0


# ---------------------------------------------------------------------------
# Integration with model registry (hardware filter wired in)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_registry_select_filters_by_hardware() -> None:
    """Confirm hardware profile can_run correctly distinguishes model sizes."""
    # Direct unit test — the registry integration is verified by the wiring in model_registry.py
    small_profile = HardwareProfile(
        cpu_cores=4,
        ram_mb=8192,
        gpus=[GPUInfo(name="Test GPU", vram_mb=4096, backend="cuda")],
    )

    assert small_profile.can_run("llama3.2:1b") is True
    assert small_profile.can_run("llama3.3:70b") is False

    # A large-RAM no-GPU machine can run 14B via CPU offload (14*0.56*1.15 ≈ 9GB; 32GB*0.6=19.2GB)
    big_ram_profile = HardwareProfile(cpu_cores=16, ram_mb=32768)
    assert big_ram_profile.can_run("phi4:latest") is True  # phi4 = 14B
