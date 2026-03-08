"""Analysis configuration for TTA.dev CLI and MCP Server.

Provides user-friendly YAML/TOML/JSON configuration for analysis settings,
enabling customization of confidence thresholds, output formats, auto-fix,
and transformation rules.

Configuration Search Order:
1. Command-line arguments (highest priority)
2. .ttadevrc.yaml / .ttadevrc.yml / .ttadevrc.toml / .ttadevrc.json
3. pyproject.toml [tool.tta-dev] section
4. Default values (lowest priority)

Example .ttadevrc.yaml:
    analysis:
      min_confidence: 0.5
      output_format: table
      show_templates: false
      show_line_numbers: true
      quiet: false

    transform:
      auto_fix: false
      suggest_diff: true
      backup_files: true
      confirm_changes: true

    patterns:
      ignore:
        - "test_*.py"
        - "*_test.py"
        - "__pycache__/**"
      custom_rules: []

    primitives:
      preferred:
        - RetryPrimitive
        - CachePrimitive
      disabled: []

    mcp:
      host: "127.0.0.1"
      port: 5000
      enable_unsafe_tools: false
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)

# Try to import tomllib (Python 3.11+) or fall back to tomli
try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib  # type: ignore[import-not-found]
    except ImportError:
        tomllib = None  # type: ignore[assignment]


class AnalysisSettings(BaseModel):
    """Configuration for code analysis."""

    min_confidence: float = Field(
        default=0.3,
        description="Minimum confidence threshold for recommendations (0.0 to 1.0)",
        ge=0.0,
        le=1.0,
    )
    output_format: str = Field(
        default="table",
        description="Output format: table, json, brief",
    )
    show_templates: bool = Field(
        default=False,
        description="Show code templates for recommendations",
    )
    show_line_numbers: bool = Field(
        default=False,
        description="Show line numbers for detected patterns",
    )
    quiet: bool = Field(
        default=False,
        description="Suppress debug logs (cleaner output for agents)",
    )
    max_recommendations: int = Field(
        default=10,
        description="Maximum number of recommendations to show",
        ge=1,
        le=50,
    )

    @field_validator("output_format")
    @classmethod
    def validate_output_format(cls, v: str) -> str:
        """Validate output_format is a valid option."""
        valid_formats = {"table", "json", "brief", "markdown"}
        if v not in valid_formats:
            raise ValueError(f"Invalid output_format: {v}. Must be one of: {valid_formats}")
        return v


class TransformSettings(BaseModel):
    """Configuration for code transformations."""

    auto_fix: bool = Field(
        default=False,
        description="Automatically apply recommended transformations",
    )
    suggest_diff: bool = Field(
        default=False,
        description="Show suggested code transformations as diffs",
    )
    backup_files: bool = Field(
        default=True,
        description="Create .bak backup before modifying files",
    )
    confirm_changes: bool = Field(
        default=True,
        description="Require confirmation before applying changes",
    )
    preferred_primitive: str | None = Field(
        default=None,
        description="Preferred primitive to apply when auto-fixing",
    )


class PatternSettings(BaseModel):
    """Configuration for pattern detection."""

    ignore: list[str] = Field(
        default_factory=lambda: [
            "test_*.py",
            "*_test.py",
            "conftest.py",
            "__pycache__/**",
            ".git/**",
            ".venv/**",
            "*.pyc",
        ],
        description="Glob patterns for files to ignore",
    )
    custom_rules: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Custom detection rules (advanced)",
    )
    enabled_detectors: list[str] = Field(
        default_factory=lambda: [
            "retry_loop",
            "timeout",
            "cache_pattern",
            "fallback",
            "gather",
            "router_pattern",
        ],
        description="List of enabled AST detectors",
    )


class PrimitiveSettings(BaseModel):
    """Configuration for primitive recommendations."""

    preferred: list[str] = Field(
        default_factory=list,
        description="Preferred primitives (ranked higher in suggestions)",
    )
    disabled: list[str] = Field(
        default_factory=list,
        description="Primitives to exclude from recommendations",
    )
    import_style: str = Field(
        default="specific",
        description="Import style: 'specific' (from x import Y) or 'module' (import x)",
    )

    @field_validator("import_style")
    @classmethod
    def validate_import_style(cls, v: str) -> str:
        """Validate import_style is valid."""
        valid_styles = {"specific", "module"}
        if v not in valid_styles:
            raise ValueError(f"Invalid import_style: {v}. Must be one of: {valid_styles}")
        return v


class MCPSettings(BaseModel):
    """Configuration for MCP server."""

    host: str = Field(
        default="127.0.0.1",
        description="Host to bind the MCP server to",
    )
    port: int = Field(
        default=5000,
        description="Port for the MCP server",
        ge=1,
        le=65535,
    )
    enable_unsafe_tools: bool = Field(
        default=False,
        description="Enable tools that modify files (security risk)",
    )
    log_requests: bool = Field(
        default=False,
        description="Log all MCP requests (verbose)",
    )


class BenchmarkSettings(BaseModel):
    """Configuration for benchmarking."""

    iterations: int = Field(
        default=100,
        description="Number of iterations for benchmarks",
        ge=1,
    )
    warmup: int = Field(
        default=5,
        description="Number of warmup iterations",
        ge=0,
    )
    output_dir: str = Field(
        default="benchmark_results",
        description="Directory for benchmark output files",
    )


class TTAConfig(BaseModel):
    """Complete TTA.dev configuration."""

    version: str = Field(
        default="1.0",
        description="Configuration version",
    )
    analysis: AnalysisSettings = Field(
        default_factory=AnalysisSettings,
        description="Code analysis settings",
    )
    transform: TransformSettings = Field(
        default_factory=TransformSettings,
        description="Code transformation settings",
    )
    patterns: PatternSettings = Field(
        default_factory=PatternSettings,
        description="Pattern detection settings",
    )
    primitives: PrimitiveSettings = Field(
        default_factory=PrimitiveSettings,
        description="Primitive recommendation settings",
    )
    mcp: MCPSettings = Field(
        default_factory=MCPSettings,
        description="MCP server settings",
    )
    benchmark: BenchmarkSettings = Field(
        default_factory=BenchmarkSettings,
        description="Benchmarking settings",
    )


# Configuration file names in search order
CONFIG_FILE_NAMES = [
    ".ttadevrc.yaml",
    ".ttadevrc.yml",
    ".ttadevrc.toml",
    ".ttadevrc.json",
    ".ttadevrc",  # YAML by default
]


def find_config_file(start_dir: Path | None = None) -> Path | None:
    """Find the configuration file by walking up from start_dir.

    Args:
        start_dir: Directory to start searching from (defaults to cwd)

    Returns:
        Path to config file if found, None otherwise
    """
    if start_dir is None:
        start_dir = Path.cwd()

    current = start_dir.resolve()

    # Walk up the directory tree
    while current != current.parent:
        # Check for config files
        for name in CONFIG_FILE_NAMES:
            config_path = current / name
            if config_path.exists():
                logger.debug("Found config file: %s", config_path)
                return config_path

        # Check pyproject.toml for [tool.tta-dev] section
        pyproject = current / "pyproject.toml"
        if pyproject.exists():
            if _has_tta_dev_section(pyproject):
                logger.debug("Found config in pyproject.toml: %s", pyproject)
                return pyproject

        current = current.parent

    # Check home directory
    home = Path.home()
    for name in CONFIG_FILE_NAMES:
        config_path = home / name
        if config_path.exists():
            logger.debug("Found config file in home: %s", config_path)
            return config_path

    return None


def _has_tta_dev_section(pyproject_path: Path) -> bool:
    """Check if pyproject.toml has a [tool.tta-dev] section."""
    if tomllib is None:
        return False

    try:
        with open(pyproject_path, "rb") as f:
            data = tomllib.load(f)
        return "tta-dev" in data.get("tool", {})
    except Exception:
        return False


def _load_yaml(path: Path) -> dict[str, Any]:
    """Load YAML configuration file."""
    with open(path) as f:
        return yaml.safe_load(f) or {}


def _load_toml(path: Path) -> dict[str, Any]:
    """Load TOML configuration file."""
    if tomllib is None:
        raise ImportError("TOML support requires Python 3.11+ or 'tomli' package")

    with open(path, "rb") as f:
        data = tomllib.load(f)

    # If it's pyproject.toml, extract [tool.tta-dev] section
    if path.name == "pyproject.toml":
        return data.get("tool", {}).get("tta-dev", {})

    return data


def _load_json(path: Path) -> dict[str, Any]:
    """Load JSON configuration file."""
    import json

    with open(path) as f:
        return json.load(f)


def load_config(
    config_path: Path | str | None = None,
    start_dir: Path | None = None,
) -> TTAConfig:
    """Load configuration from file.

    Args:
        config_path: Explicit path to config file (overrides search)
        start_dir: Directory to start searching from

    Returns:
        TTAConfig instance with loaded settings

    Raises:
        FileNotFoundError: If explicit config_path doesn't exist
        ValueError: If config file has invalid format
    """
    # Use explicit path if provided
    if config_path is not None:
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")
    else:
        # Search for config file
        path = find_config_file(start_dir)
        if path is None:
            logger.debug("No config file found, using defaults")
            return TTAConfig()

    # Load based on file extension
    suffix = path.suffix.lower()
    name = path.name.lower()

    try:
        if suffix in {".yaml", ".yml"} or name == ".ttadevrc":
            data = _load_yaml(path)
        elif suffix == ".toml":
            data = _load_toml(path)
        elif suffix == ".json":
            data = _load_json(path)
        else:
            # Try YAML by default
            data = _load_yaml(path)

        logger.info("Loaded config from: %s", path)
        return TTAConfig(**data)

    except Exception as e:
        logger.warning("Error loading config from %s: %s", path, e)
        raise ValueError(f"Invalid config file {path}: {e}") from e


def save_config(
    config: TTAConfig,
    path: Path | str,
    format: str = "yaml",
) -> None:
    """Save configuration to file.

    Args:
        config: Configuration to save
        path: Path to save to
        format: Output format (yaml, json, toml)
    """
    path = Path(path)

    # Convert to dict (exclude defaults for cleaner output)
    data = config.model_dump(exclude_defaults=True)

    if format == "yaml":
        with open(path, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)
    elif format == "json":
        import json

        with open(path, "w") as f:
            json.dump(data, f, indent=2)
    elif format == "toml":
        # TOML writing requires additional library
        try:
            import toml

            with open(path, "w") as f:
                toml.dump(data, f)
        except ImportError:
            raise ImportError("TOML writing requires 'toml' package") from None
    else:
        raise ValueError(f"Unsupported format: {format}")

    logger.info("Saved config to: %s", path)


def generate_default_config(format: str = "yaml") -> str:
    """Generate default configuration as string.

    Args:
        format: Output format (yaml, json)

    Returns:
        Configuration string
    """
    config = TTAConfig()

    # Get full config with all defaults shown
    data = config.model_dump()

    if format == "yaml":
        return yaml.dump(data, default_flow_style=False, sort_keys=False)
    elif format == "json":
        import json

        return json.dumps(data, indent=2)
    else:
        raise ValueError(f"Unsupported format: {format}")


def merge_cli_options(
    config: TTAConfig,
    **cli_options: Any,
) -> TTAConfig:
    """Merge CLI options into configuration.

    CLI options take precedence over config file values.

    Args:
        config: Base configuration
        **cli_options: CLI option overrides

    Returns:
        New TTAConfig with merged values
    """
    # Map CLI option names to config paths
    cli_to_config = {
        "min_confidence": ("analysis", "min_confidence"),
        "output": ("analysis", "output_format"),
        "templates": ("analysis", "show_templates"),
        "show_templates": ("analysis", "show_templates"),
        "quiet": ("analysis", "quiet"),
        "lines": ("analysis", "show_line_numbers"),
        "show_lines": ("analysis", "show_line_numbers"),
        "apply": ("transform", "auto_fix"),
        "suggest_diff": ("transform", "suggest_diff"),
        "apply_primitive": ("transform", "preferred_primitive"),
        "host": ("mcp", "host"),
        "port": ("mcp", "port"),
        "iterations": ("benchmark", "iterations"),
    }

    # Create a copy of the config data
    data = config.model_dump()

    # Apply CLI overrides
    for cli_name, value in cli_options.items():
        if value is None:
            continue

        if cli_name in cli_to_config:
            section, key = cli_to_config[cli_name]
            data[section][key] = value

    return TTAConfig(**data)


# Module-level cached config
_cached_config: TTAConfig | None = None
_cached_config_path: Path | None = None


def get_config(reload: bool = False) -> TTAConfig:
    """Get the current configuration (cached).

    Args:
        reload: Force reload from disk

    Returns:
        Current TTAConfig
    """
    global _cached_config, _cached_config_path

    if _cached_config is None or reload:
        _cached_config = load_config()
        _cached_config_path = find_config_file()

    return _cached_config


def get_config_path() -> Path | None:
    """Get the path to the loaded config file."""
    global _cached_config_path

    if _cached_config_path is None:
        _cached_config_path = find_config_file()

    return _cached_config_path
