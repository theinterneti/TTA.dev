"""Configuration management for TTA.dev primitives.

This module provides configuration loading and validation for:
- Orchestration settings (multi-model workflows)
- Analysis settings (CLI and MCP server)
- Transform settings (auto-fix, diffs)
- Pattern detection settings

Configuration files are loaded from (in priority order):
1. Explicit --config path
2. .ttadevrc.yaml / .ttadevrc.yml / .ttadevrc.toml / .ttadevrc.json
3. pyproject.toml [tool.tta-dev] section
4. Default values
"""

from tta_dev_primitives.config.analysis_config import (
    AnalysisSettings,
    BenchmarkSettings,
    MCPSettings,
    PatternSettings,
    PrimitiveSettings,
    TransformSettings,
    TTAConfig,
    find_config_file,
    generate_default_config,
    get_config,
    get_config_path,
    load_config,
    merge_cli_options,
    save_config,
)
from tta_dev_primitives.config.orchestration_config import (
    ExecutorConfig,
    FallbackStrategy,
    OrchestrationConfig,
    OrchestratorConfig,
    load_orchestration_config,
)

__all__ = [
    # Analysis config
    "TTAConfig",
    "AnalysisSettings",
    "TransformSettings",
    "PatternSettings",
    "PrimitiveSettings",
    "MCPSettings",
    "BenchmarkSettings",
    "load_config",
    "save_config",
    "find_config_file",
    "get_config",
    "get_config_path",
    "generate_default_config",
    "merge_cli_options",
    # Orchestration config
    "OrchestrationConfig",
    "OrchestratorConfig",
    "ExecutorConfig",
    "FallbackStrategy",
    "load_orchestration_config",
]
