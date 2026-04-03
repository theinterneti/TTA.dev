"""Hardware detection for local-first model routing.

Detects CPU cores, system RAM, and GPU presence/VRAM so the router can skip
Ollama model recommendations that won't fit in available memory.

Supported GPU backends
----------------------
- **CUDA** (NVIDIA) — via ``nvidia-smi``
- **ROCm** (AMD)   — via ``rocm-smi``
- **Metal** (Apple) — via ``system_profiler`` (returns unified memory)
- **CPU only**     — falls back gracefully when no GPU tooling is found

Usage
-----
::

    from ttadev.primitives.llm.hardware_detector import HardwareDetector

    hw = HardwareDetector()
    profile = hw.detect()
    print(profile.summary())

    # Filter an Ollama model list to only viable models:
    viable = hw.filter_ollama_models(["llama3.2:1b", "qwen3:14b", "llama3.3:70b"])
    # On a 4 GB VRAM machine → ["llama3.2:1b"]

CLI
---
::

    uv run python -m ttadev.primitives.llm.hardware_detector
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from typing import Any

import structlog

try:
    import psutil

    _PSUTIL_AVAILABLE = True
except ImportError:  # pragma: no cover
    _PSUTIL_AVAILABLE = False

logger = structlog.get_logger("tta_dev.hardware_detector")

# ---------------------------------------------------------------------------
# Model parameter-count heuristics (Ollama default Q4_K_M quantization)
# VRAM estimate: params_B * 0.56 GB  (empirical Q4_K_M rule of thumb)
# We also allow CPU-RAM fallback: Ollama can offload layers to system RAM,
# but at drastically reduced speed. We mark GPU-only models as "slow" on CPU.
# ---------------------------------------------------------------------------

#: Bytes-per-parameter for each quantization level (approximate)
_QUANT_BPP: dict[str, float] = {
    "q2": 0.28,
    "q3": 0.42,
    "q4": 0.56,
    "q5": 0.70,
    "q6": 0.84,
    "q8": 1.10,
    "fp16": 2.0,
    "fp32": 4.0,
}

#: Known param counts for popular models where the name is ambiguous (latest/default)
_KNOWN_PARAM_GB: dict[str, float] = {
    # phi series (Microsoft)
    "phi4": 14.0,
    "phi4-mini": 3.8,
    "phi3": 3.8,
    "phi3.5": 3.8,
    # deepseek
    "deepseek-r1": 7.0,  # distill variant most common via Ollama
    "deepseek-coder-v2": 16.0,
    # gemma
    "gemma3": 9.0,
    "gemma2": 9.0,
    "gemma": 7.0,
    # mistral
    "mistral": 7.0,
    "mistral-nemo": 12.0,
    # codellama
    "codellama": 7.0,
    # wizardcoder
    "wizardcoder": 7.0,
    # starcoder
    "starcoder2": 7.0,
    # llava (vision)
    "llava": 7.0,
    # general small models
    "tinyllama": 1.1,
    "smollm2": 1.7,
}

#: Regex to extract parameter count from model ID  (e.g. "qwen3:14b" → 14.0)
_PARAM_RE = re.compile(r"[:\-_](\d+(?:\.\d+)?)b\b", re.IGNORECASE)


def _estimate_params_b(model_id: str) -> float | None:
    """Return estimated parameter count (billions) from a model ID string."""
    # e.g. "qwen3:14b", "llama3.2:1b", "phi4:latest"
    m = _PARAM_RE.search(model_id.lower())
    if m:
        return float(m.group(1))
    # Try known-name lookup (strip tag)
    base = model_id.split(":")[0].lower()
    for known, params in _KNOWN_PARAM_GB.items():
        if base == known or base.startswith(known + "-") or base.endswith("-" + known):
            return params
    return None


def _vram_needed_gb(params_b: float, quantization: str = "q4") -> float:
    """Estimate VRAM needed (GB) for *params_b* billion parameters."""
    bpp = _QUANT_BPP.get(quantization.lower(), _QUANT_BPP["q4"])
    # Add ~15% for KV-cache and framework overhead
    return params_b * bpp * 1.15


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class GPUInfo:
    """A single GPU's identity and memory capacity."""

    name: str
    vram_mb: int
    backend: str  # "cuda" | "rocm" | "metal"

    @property
    def vram_gb(self) -> float:
        """VRAM in gigabytes."""
        return self.vram_mb / 1024


@dataclass(frozen=True)
class HardwareProfile:
    """Full hardware snapshot for the current machine."""

    cpu_cores: int
    ram_mb: int
    gpus: list[GPUInfo] = field(default_factory=list)

    @property
    def ram_gb(self) -> float:
        return self.ram_mb / 1024

    @property
    def total_vram_mb(self) -> int:
        return sum(g.vram_mb for g in self.gpus)

    @property
    def total_vram_gb(self) -> float:
        return self.total_vram_mb / 1024

    @property
    def max_vram_mb(self) -> int:
        """Largest single GPU's VRAM (relevant for non-NVLink setups)."""
        return max((g.vram_mb for g in self.gpus), default=0)

    @property
    def backend(self) -> str:
        """Dominant compute backend: "cuda", "rocm", "metal", or "cpu"."""
        return self.gpus[0].backend if self.gpus else "cpu"

    def can_run(self, model_id: str, quantization: str = "q4") -> bool:
        """Return True if this hardware can run *model_id* in Ollama.

        Uses GPU VRAM when available; falls back to system RAM (CPU-only,
        slower but functional for small/medium models).

        Args:
            model_id: Ollama model identifier (e.g. ``"qwen3:14b"``).
            quantization: Quantization level assumed.  Defaults to ``"q4"``
                which matches Ollama's default Q4_K_M.

        Returns:
            ``True`` when estimated VRAM/RAM requirement is met.
        """
        params = _estimate_params_b(model_id)
        if params is None:
            # Unknown model — be optimistic; Ollama will tell the user if it fails
            logger.debug("hardware_detector: unknown params for %s, assuming runnable", model_id)
            return True

        needed_gb = _vram_needed_gb(params, quantization)

        # Prefer GPU if available and sufficient
        if self.total_vram_gb >= needed_gb:
            return True

        # CPU-only fallback: allow if system RAM comfortably covers it (with OS headroom)
        available_ram_gb = self.ram_gb * 0.6  # keep 40% headroom for OS + swap
        return available_ram_gb >= needed_gb

    def max_params_b(self, quantization: str = "q4") -> float:
        """Largest model (in billions of params) this hardware can run.

        Considers both VRAM and system RAM.
        """
        bpp = _QUANT_BPP.get(quantization.lower(), _QUANT_BPP["q4"])
        overhead = 1.15  # KV-cache + framework

        gpu_max = self.total_vram_gb / (bpp * overhead) if self.total_vram_gb > 0 else 0.0
        ram_max = (self.ram_gb * 0.6) / (bpp * overhead)
        return max(gpu_max, ram_max)

    def summary(self) -> str:
        """Human-readable one-liner for display/logging."""
        gpu_part = (
            ", ".join(f"{g.name} {g.vram_gb:.0f}GB {g.backend.upper()}" for g in self.gpus)
            or "no GPU"
        )
        return (
            f"{self.cpu_cores} CPU cores | "
            f"{self.ram_gb:.0f} GB RAM | "
            f"{gpu_part} | "
            f"max ~{self.max_params_b():.0f}B params (Q4)"
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialisable representation for MCP / CLI output."""
        return {
            "cpu_cores": self.cpu_cores,
            "ram_gb": round(self.ram_gb, 1),
            "gpus": [
                {
                    "name": g.name,
                    "vram_gb": round(g.vram_gb, 1),
                    "backend": g.backend,
                }
                for g in self.gpus
            ],
            "backend": self.backend,
            "total_vram_gb": round(self.total_vram_gb, 1),
            "max_params_b_q4": round(self.max_params_b("q4"), 1),
            "max_params_b_q8": round(self.max_params_b("q8"), 1),
        }


# ---------------------------------------------------------------------------
# Detector
# ---------------------------------------------------------------------------


class HardwareDetector:
    """Detects local hardware and advises which Ollama models can run.

    Results are cached for the lifetime of the instance (hardware doesn't
    change during a session).  Call :meth:`detect` to force a re-read.
    """

    def __init__(self) -> None:
        self._cached: HardwareProfile | None = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def detect(self, *, force: bool = False) -> HardwareProfile:
        """Detect and return the current hardware profile.

        Args:
            force: Bypass the instance cache and re-probe hardware.

        Returns:
            A :class:`HardwareProfile` describing CPU, RAM, and GPUs.
        """
        if self._cached is not None and not force:
            return self._cached

        cpu_cores = self._detect_cpu_cores()
        ram_mb = self._detect_ram_mb()
        gpus = self._detect_gpus()

        self._cached = HardwareProfile(cpu_cores=cpu_cores, ram_mb=ram_mb, gpus=gpus)
        logger.info("hardware_detector: %s", self._cached.summary())
        return self._cached

    def filter_ollama_models(
        self,
        model_ids: list[str],
        quantization: str = "q4",
    ) -> list[str]:
        """Return only those *model_ids* that fit in available memory.

        Args:
            model_ids: Candidate Ollama model IDs to filter.
            quantization: Assumed quantization level.  Defaults to ``"q4"``.

        Returns:
            Subset of *model_ids* that the current hardware can run, in the
            same order as the input list.
        """
        profile = self.detect()
        return [mid for mid in model_ids if profile.can_run(mid, quantization)]

    def recommend_size_tag(self) -> str:
        """Return the largest recommended model size tag for this hardware.

        Useful for building Ollama pull commands or choosing between
        ``phi4:latest`` (14B) and ``phi4-mini`` (3.8B).

        Returns:
            One of ``"1b"``, ``"3b"``, ``"7b"``, ``"14b"``, ``"32b"``, ``"70b"``.
        """
        max_b = self.detect().max_params_b("q4")
        for threshold, tag in [
            (60.0, "70b"),
            (25.0, "32b"),
            (10.0, "14b"),
            (5.0, "7b"),
            (2.5, "3b"),
        ]:
            if max_b >= threshold:
                return tag
        return "1b"

    # ------------------------------------------------------------------
    # Private detection helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _detect_cpu_cores() -> int:
        if _PSUTIL_AVAILABLE:
            return psutil.cpu_count(logical=False) or psutil.cpu_count() or 1
        try:
            import os

            return os.cpu_count() or 1
        except Exception:
            return 1

    @staticmethod
    def _detect_ram_mb() -> int:
        if _PSUTIL_AVAILABLE:
            return int(psutil.virtual_memory().total / 1024 / 1024)
        # Fallback: read /proc/meminfo on Linux
        try:
            with open("/proc/meminfo") as f:
                for line in f:
                    if line.startswith("MemTotal:"):
                        kb = int(line.split()[1])
                        return kb // 1024
        except Exception:
            pass
        return 8192  # conservative default

    @staticmethod
    def _detect_gpus() -> list[GPUInfo]:
        """Try each GPU backend in priority order: CUDA → ROCm → Metal."""
        gpus = HardwareDetector._probe_nvidia()
        if gpus:
            return gpus
        gpus = HardwareDetector._probe_rocm()
        if gpus:
            return gpus
        gpus = HardwareDetector._probe_metal()
        return gpus

    @staticmethod
    def _run(cmd: list[str], timeout: int = 5) -> str | None:
        """Run a subprocess and return stdout, or None on failure."""
        if not shutil.which(cmd[0]):
            return None
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            return result.stdout if result.returncode == 0 else None
        except Exception:
            return None

    @staticmethod
    def _probe_nvidia() -> list[GPUInfo]:
        out = HardwareDetector._run(
            ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"]
        )
        if not out:
            return []
        gpus: list[GPUInfo] = []
        for line in out.strip().splitlines():
            parts = [p.strip() for p in line.split(",")]
            if len(parts) < 2:
                continue
            try:
                vram_mb = int(parts[1])
            except ValueError:
                continue
            gpus.append(GPUInfo(name=parts[0], vram_mb=vram_mb, backend="cuda"))
        return gpus

    @staticmethod
    def _probe_rocm() -> list[GPUInfo]:
        # rocm-smi --showmeminfo vram returns lines like:
        #   GPU[0]   : VRAM Total Memory (B): 8589934592
        out = HardwareDetector._run(["rocm-smi", "--showmeminfo", "vram"])
        if not out:
            return []
        gpus: list[GPUInfo] = []
        name_re = re.compile(r"GPU\[(\d+)\]")
        # Try to get GPU name separately
        gpu_indices: list[int] = []
        for line in out.splitlines():
            m = name_re.search(line)
            if m and "Total Memory" in line:
                idx = int(m.group(1))
                try:
                    bytes_val = int(line.split(":")[-1].strip())
                    vram_mb = bytes_val // (1024 * 1024)
                    gpu_indices.append(idx)
                    gpus.append(GPUInfo(name=f"AMD GPU {idx}", vram_mb=vram_mb, backend="rocm"))
                except ValueError:
                    pass
        return gpus

    @staticmethod
    def _probe_metal() -> list[GPUInfo]:
        """Detect Apple Silicon / Metal GPU via system_profiler."""
        if sys.platform != "darwin":
            return []
        out = HardwareDetector._run(["system_profiler", "SPDisplaysDataType"], timeout=10)
        if not out:
            return []

        # Apple Silicon uses unified memory — report total RAM as effective VRAM
        # system_profiler reports "VRAM (Total): 16 GB" for discrete GPUs
        # For M-series, we fall back to RAM
        gpus: list[GPUInfo] = []
        vram_re = re.compile(r"VRAM.*?:\s*(\d+)\s*(MB|GB)", re.IGNORECASE)
        chip_re = re.compile(r"Chipset Model:\s*(.+)")
        name = "Apple GPU"
        for line in out.splitlines():
            cm = chip_re.search(line)
            if cm:
                name = cm.group(1).strip()
            vm = vram_re.search(line)
            if vm:
                amount = int(vm.group(1))
                unit = vm.group(2).upper()
                vram_mb = amount * 1024 if unit == "GB" else amount
                gpus.append(GPUInfo(name=name, vram_mb=vram_mb, backend="metal"))
                name = "Apple GPU"  # reset for next GPU

        if not gpus and _PSUTIL_AVAILABLE:
            # Apple Silicon unified memory — treat system RAM as shared VRAM
            ram_mb = int(psutil.virtual_memory().total / 1024 / 1024)
            gpus.append(GPUInfo(name=name or "Apple Silicon", vram_mb=ram_mb, backend="metal"))

        return gpus


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

#: Shared detector instance; safe to import and use directly.
detector = HardwareDetector()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _cli_main() -> None:  # pragma: no cover
    import json

    hw = HardwareDetector()
    profile = hw.detect()
    print(profile.summary())
    print()

    data = profile.to_dict()
    data["recommend_size_tag"] = hw.recommend_size_tag()

    # Show which common Ollama models are runnable
    candidates = [
        "tinyllama:latest",
        "llama3.2:1b",
        "llama3.2:3b",
        "phi4-mini:latest",
        "qwen3:4b",
        "qwen2.5:7b",
        "phi4:latest",
        "qwen3:14b",
        "qwen3:32b",
        "llama3.3:70b",
        "qwen3:235b-a22b",
    ]
    viable = hw.filter_ollama_models(candidates)
    not_viable = [m for m in candidates if m not in viable]

    data["viable_models"] = viable
    data["not_viable_models"] = not_viable

    print("✅ Viable Ollama models:")
    for m in viable:
        print(f"   {m}")
    if not_viable:
        print("❌ Too large for available memory:")
        for m in not_viable:
            print(f"   {m}")

    print()
    print(json.dumps(data, indent=2))


if __name__ == "__main__":
    _cli_main()
