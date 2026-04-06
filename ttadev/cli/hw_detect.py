"""Hardware-aware Ollama model recommendation.

Detects GPU VRAM (NVIDIA or AMD) and system RAM, then recommends the best
Ollama model the hardware can handle.
"""

from __future__ import annotations

import json
import subprocess

# ---------------------------------------------------------------------------
# VRAM → model tier mapping
# ---------------------------------------------------------------------------

#: Ordered list of (vram_threshold_gb, model_name, reason).  Checked highest
#: VRAM first so the first matching entry wins.
_GPU_TIERS: list[tuple[float, str, str]] = [
    (24.0, "qwen2.5-coder:32b", "GPU VRAM ≥ 24 GB supports 32B parameter models efficiently."),
    (16.0, "qwen2.5:14b", "GPU VRAM ≥ 16 GB supports 14B parameter models efficiently."),
    (8.0, "gemma3:4b", "GPU VRAM ≥ 8 GB supports 4B parameter models efficiently."),
    (4.0, "qwen2.5:3b", "GPU VRAM ≥ 4 GB supports 3B parameter models efficiently."),
]

#: RAM-only (no GPU) tiers.
_CPU_TIERS: list[tuple[float, str, str]] = [
    (
        16.0,
        "qwen2.5:7b",
        "No GPU detected; RAM ≥ 16 GB is sufficient for CPU inference of 7B models.",
    ),
    (
        0.0,
        "qwen2.5:3b",
        "No GPU detected; 3B model recommended for systems with less than 16 GB RAM.",
    ),
]


# ---------------------------------------------------------------------------
# GPU detection helpers
# ---------------------------------------------------------------------------


def _run(args: list[str], timeout: int = 5) -> subprocess.CompletedProcess[str]:
    """Run a subprocess safely, never raising on failure.

    Args:
        args: Command and arguments.
        timeout: Maximum seconds to wait.

    Returns:
        CompletedProcess result (returncode may be non-zero).
    """
    return subprocess.run(
        args,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


def _detect_nvidia_vram_gb() -> float | None:
    """Try to detect NVIDIA GPU VRAM via nvidia-smi.

    Returns:
        VRAM in GB, or ``None`` if nvidia-smi is unavailable or fails.
    """
    try:
        result = _run(["nvidia-smi", "--query-gpu=memory.total", "--format=csv,noheader,nounits"])
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return None

    if result.returncode != 0 or not result.stdout.strip():
        return None

    # nvidia-smi returns one line per GPU in MiB; take the first GPU.
    first_line = result.stdout.strip().splitlines()[0].strip()
    try:
        mib = float(first_line)
        return mib / 1024.0
    except ValueError:
        return None


def _detect_amd_vram_gb() -> float | None:
    """Try to detect AMD GPU VRAM via rocm-smi.

    Returns:
        VRAM in GB, or ``None`` if rocm-smi is unavailable or fails.
    """
    try:
        result = _run(["rocm-smi", "--showmeminfo", "vram", "--json"])
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return None

    if result.returncode != 0 or not result.stdout.strip():
        return None

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        return None

    # rocm-smi JSON structure: {card_id: {"VRAM Total Memory (B)": "..."}}
    # Sum across all cards and return the maximum single-GPU VRAM.
    max_vram_bytes = 0
    for card_data in data.values():
        if not isinstance(card_data, dict):
            continue
        for key, value in card_data.items():
            key_lower = key.lower()
            if "vram" in key_lower and "total" in key_lower and "used" not in key_lower:
                try:
                    max_vram_bytes = max(max_vram_bytes, int(value))
                except (ValueError, TypeError):
                    pass

    if max_vram_bytes > 0:
        return max_vram_bytes / (1024**3)

    return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def detect_gpu_vram_gb() -> float | None:
    """Detect GPU VRAM in GB.

    Tries NVIDIA first (via ``nvidia-smi``), then AMD (via ``rocm-smi``).
    Returns ``None`` if no GPU is detected or both tools fail.

    Returns:
        VRAM in GB as a float, or ``None`` if no GPU is available.
    """
    vram = _detect_nvidia_vram_gb()
    if vram is not None:
        return vram
    return _detect_amd_vram_gb()


def detect_system_ram_gb() -> float:
    """Detect total system RAM in GB.

    Uses ``psutil`` when available, falls back to reading ``/proc/meminfo``
    on Linux, and returns 8.0 GB as a conservative default when all methods
    fail.

    Returns:
        Total system RAM in GB.
    """
    try:
        import psutil  # type: ignore[import-untyped]

        return psutil.virtual_memory().total / (1024**3)
    except ImportError:
        pass

    # Fallback: parse /proc/meminfo on Linux.
    try:
        with open("/proc/meminfo") as f:
            for line in f:
                if line.startswith("MemTotal:"):
                    kb = int(line.split()[1])
                    return kb / (1024**2)
    except OSError:
        pass

    # Conservative default.
    return 8.0


def recommend_ollama_model() -> str:
    """Recommend the best Ollama model for the current hardware.

    Returns:
        Ollama model identifier string (without ``ollama/`` prefix),
        e.g. ``"qwen2.5:14b"``.
    """
    vram_gb = detect_gpu_vram_gb()
    if vram_gb is not None:
        for threshold, model, _ in _GPU_TIERS:
            if vram_gb >= threshold:
                return model
        # Less than 4 GB VRAM — fall back to CPU tiers.

    ram_gb = detect_system_ram_gb()
    for threshold, model, _ in _CPU_TIERS:
        if ram_gb >= threshold:
            return model

    return _CPU_TIERS[-1][1]


def _get_recommendation_reason(vram_gb: float | None, ram_gb: float) -> str:
    """Return a human-readable reason for the recommendation.

    Args:
        vram_gb: Detected GPU VRAM in GB, or ``None``.
        ram_gb: Detected system RAM in GB.

    Returns:
        Reason string.
    """
    if vram_gb is not None:
        for threshold, _, reason in _GPU_TIERS:
            if vram_gb >= threshold:
                return reason
    for threshold, _, reason in _CPU_TIERS:
        if ram_gb >= threshold:
            return reason
    return _CPU_TIERS[-1][2]


def hardware_summary() -> dict[str, object]:
    """Return a summary of detected hardware and the recommended Ollama model.

    Returns:
        Dictionary with keys:

        - ``gpu_vram_gb`` (``float | None``): Detected GPU VRAM in GB, or
          ``None`` if no GPU detected.
        - ``system_ram_gb`` (``float``): Total system RAM in GB.
        - ``recommended_model`` (``str``): Recommended Ollama model string.
        - ``reason`` (``str``): Human-readable justification.
    """
    vram_gb = detect_gpu_vram_gb()
    ram_gb = detect_system_ram_gb()
    model = recommend_ollama_model()
    reason = _get_recommendation_reason(vram_gb, ram_gb)

    return {
        "gpu_vram_gb": vram_gb,
        "system_ram_gb": ram_gb,
        "recommended_model": model,
        "reason": reason,
    }
